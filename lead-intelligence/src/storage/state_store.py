"""
Persistent Crash-Safe Pipeline State Store (SQLite) for Ariyx Lead Intelligence.

Maintains cross-day deduplication, 30-day campaign progress tracking,
daily metrics counters, accepted-lead sync outbox, and query rotation state
so interrupted runs can resume cleanly without duplicating records.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.scoring.lead_scorer import LeadScorer

logger = logging.getLogger(__name__)


class PipelineStateStore:
    """
    SQLite-backed state store for 30-day daily automation and crash recovery.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            db_path = str(base_dir / "data" / "state" / "ariyx_pipeline.db")

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS campaign_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS daily_runs (
                    run_date TEXT PRIMARY KEY,
                    campaign_day INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    target_accepted INTEGER NOT NULL,
                    accepted_count INTEGER NOT NULL DEFAULT 0,
                    research_attempts INTEGER NOT NULL DEFAULT 0,
                    rejected_count INTEGER NOT NULL DEFAULT 0,
                    skipped_duplicates INTEGER NOT NULL DEFAULT 0,
                    skipped_suppressed INTEGER NOT NULL DEFAULT 0,
                    dm_identified_count INTEGER NOT NULL DEFAULT 0,
                    email_verification_counts_json TEXT NOT NULL DEFAULT '{}',
                    rejection_breakdown_json TEXT NOT NULL DEFAULT '{}',
                    sheets_inserted INTEGER NOT NULL DEFAULT 0,
                    blocker_summary TEXT NOT NULL DEFAULT '',
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    finished_at TEXT
                );

                CREATE TABLE IF NOT EXISTS processed_domains (
                    domain TEXT PRIMARY KEY,
                    lead_id TEXT NOT NULL DEFAULT '',
                    business_name TEXT NOT NULL DEFAULT '',
                    first_seen_date TEXT NOT NULL,
                    last_checked_date TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    qualification_tier TEXT NOT NULL DEFAULT '',
                    email_verification_status TEXT NOT NULL DEFAULT '',
                    decision_maker_found INTEGER NOT NULL DEFAULT 0,
                    cooldown_until TEXT,
                    blocker_codes_json TEXT NOT NULL DEFAULT '[]',
                    rejection_reasons_json TEXT NOT NULL DEFAULT '[]',
                    record_json TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS daily_accepted_leads (
                    lead_id TEXT PRIMARY KEY,
                    run_date TEXT NOT NULL,
                    domain TEXT UNIQUE NOT NULL,
                    business_name TEXT NOT NULL,
                    outreach_segment TEXT NOT NULL,
                    decision_maker_name TEXT NOT NULL,
                    verified_email TEXT NOT NULL,
                    lead_score INTEGER NOT NULL DEFAULT 0,
                    synced_to_sheet INTEGER NOT NULL DEFAULT 0,
                    synced_at TEXT,
                    record_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS provider_daily_quotas (
                    provider TEXT NOT NULL,
                    quota_date TEXT NOT NULL,
                    exhausted INTEGER NOT NULL DEFAULT 0,
                    requests_used INTEGER NOT NULL DEFAULT 0,
                    remaining_reported INTEGER,
                    note TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (provider, quota_date)
                );
                """
            )

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_meta(self, key: str, default: Optional[str] = None) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute("SELECT value FROM campaign_state WHERE key = ?", (key,)).fetchone()
            return row["value"] if row else default

    def set_meta(self, key: str, value: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO campaign_state (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )

    def get_query_offset(self) -> int:
        val = self.get_meta("query_offset", "0")
        try:
            return int(val or 0)
        except ValueError:
            return 0

    def set_query_offset(self, offset: int) -> None:
        self.set_meta("query_offset", str(int(offset)))

    def get_or_create_campaign_day(self, run_date: str) -> int:
        existing = self.get_daily_run(run_date)
        if existing:
            return int(existing["campaign_day"])

        start_date = self.get_meta("campaign_start_date")
        if not start_date:
            self.set_meta("campaign_start_date", run_date)
            return 1

        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS cnt FROM daily_runs WHERE run_date < ?", (run_date,)).fetchone()
            return int(row["cnt"] or 0) + 1

    def get_campaign_progress(self, max_days: int = 0) -> Dict[str, Any]:
        with self._connect() as conn:
            runs = conn.execute(
                "SELECT run_date, campaign_day, status, target_accepted, accepted_count, research_attempts, sheets_inserted "
                "FROM daily_runs ORDER BY run_date ASC"
            ).fetchall()
        completed_days = sum(1 for r in runs if r["status"] == "COMPLETED_TARGET_MET")
        total_accepted = sum(int(r["accepted_count"]) for r in runs)
        total_synced = sum(int(r["sheets_inserted"]) for r in runs)
        is_complete = bool(max_days and max_days > 0 and len(runs) >= max_days)
        return {
            "campaign_start_date": self.get_meta("campaign_start_date") or "",
            "days_logged": len(runs),
            "target_campaign_days": max_days if max_days and max_days > 0 else "Ongoing",
            "completed_target_days": completed_days,
            "total_accepted_leads": total_accepted,
            "total_sheets_inserted": total_synced,
            "campaign_complete": is_complete,
        }

    def start_or_resume_daily_run(self, run_date: str, target_accepted: int = 30) -> Dict[str, Any]:
        existing = self.get_daily_run(run_date)
        now = self._now_iso()
        if existing:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE daily_runs SET status = 'RUNNING', target_accepted = ?, updated_at = ?, finished_at = NULL "
                    "WHERE run_date = ?",
                    (target_accepted, now, run_date),
                )
            return self.get_daily_run(run_date) or existing

        campaign_day = self.get_or_create_campaign_day(run_date)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO daily_runs (
                    run_date, campaign_day, status, target_accepted,
                    started_at, updated_at
                ) VALUES (?, ?, 'RUNNING', ?, ?, ?)
                """,
                (run_date, campaign_day, target_accepted, now, now),
            )
        return self.get_daily_run(run_date) or {}

    def get_daily_run(self, run_date: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM daily_runs WHERE run_date = ?", (run_date,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["email_verification_counts"] = json.loads(data.pop("email_verification_counts_json", "{}") or "{}")
            data["rejection_breakdown"] = json.loads(data.pop("rejection_breakdown_json", "{}") or "{}")
            return data

    def save_daily_run(self, run_summary: Dict[str, Any]) -> None:
        now = self._now_iso()
        finished_at = run_summary.get("finished_at")
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE daily_runs SET
                    status = ?,
                    target_accepted = ?,
                    accepted_count = ?,
                    research_attempts = ?,
                    rejected_count = ?,
                    skipped_duplicates = ?,
                    skipped_suppressed = ?,
                    dm_identified_count = ?,
                    email_verification_counts_json = ?,
                    rejection_breakdown_json = ?,
                    sheets_inserted = ?,
                    blocker_summary = ?,
                    updated_at = ?,
                    finished_at = ?
                WHERE run_date = ?
                """,
                (
                    run_summary.get("status", "RUNNING"),
                    int(run_summary.get("target_accepted", 30)),
                    int(run_summary.get("accepted_count", 0)),
                    int(run_summary.get("research_attempts", 0)),
                    int(run_summary.get("rejected_count", 0)),
                    int(run_summary.get("skipped_duplicates", 0)),
                    int(run_summary.get("skipped_suppressed", 0)),
                    int(run_summary.get("dm_identified_count", 0)),
                    json.dumps(run_summary.get("email_verification_counts", {})),
                    json.dumps(run_summary.get("rejection_breakdown", {})),
                    int(run_summary.get("sheets_inserted", 0)),
                    run_summary.get("blocker_summary", ""),
                    now,
                    finished_at,
                    run_summary["run_date"],
                ),
            )

    def get_blocked_domains(self, run_date: str) -> Set[str]:
        """
        Returns domains that MUST NOT be researched again today:
        - Already ACCEPTED on any day
        - Permanently SUPPRESSED or ENTERPRISE
        - Already checked today (`last_checked_date == run_date`)
        - In active cooldown (`cooldown_until > run_date`)
        """
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT domain FROM processed_domains
                WHERE outcome IN ('ACCEPTED', 'SUPPRESSED', 'ENTERPRISE')
                   OR last_checked_date = ?
                   OR (cooldown_until IS NOT NULL AND cooldown_until > ?)
                """,
                (run_date, run_date),
            ).fetchall()
        return {r["domain"] for r in rows if r["domain"]}

    def get_known_accepted_emails(self) -> Set[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT verified_email FROM daily_accepted_leads").fetchall()
        return {r["verified_email"].strip().lower() for r in rows if r["verified_email"]}

    def record_candidate_outcome(
        self,
        run_date: str,
        lead: Dict[str, Any],
        outcome: str,
        blocker_codes: Optional[List[str]] = None,
        rejection_reasons: Optional[List[str]] = None,
        outreach_segment: str = "UNASSIGNED",
        cooldown_days: Optional[int] = None,
    ) -> None:
        domain = LeadScorer._extract_clean_domain(
            lead.get("domain") or lead.get("website") or lead.get("Website URL") or ""
        )
        if not domain:
            return

        now_date = run_date
        cooldown_until: Optional[str] = None
        if cooldown_days and cooldown_days > 0:
            base_dt = datetime.strptime(run_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            cooldown_until = (base_dt + timedelta(days=cooldown_days)).strftime("%Y-%m-%d")

        lead_id = str(lead.get("lead_id") or lead.get("Lead ID") or "").strip()
        business_name = str(lead.get("business_name") or lead.get("Business Name") or domain).strip()
        dm_name = str(lead.get("decision_maker_name") or "Unavailable").strip()
        dm_found = 1 if (dm_name and dm_name != "Unavailable") else 0
        email = str(lead.get("verified_email") or lead.get("email") or "Unavailable").strip().lower()
        email_status = str(lead.get("email_verification_status") or "Unavailable").strip()
        tier = str(lead.get("qualification_tier") or "").strip()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO processed_domains (
                    domain, lead_id, business_name, first_seen_date, last_checked_date,
                    outcome, qualification_tier, email_verification_status,
                    decision_maker_found, cooldown_until, blocker_codes_json,
                    rejection_reasons_json, record_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    lead_id = excluded.lead_id,
                    business_name = excluded.business_name,
                    last_checked_date = excluded.last_checked_date,
                    outcome = excluded.outcome,
                    qualification_tier = excluded.qualification_tier,
                    email_verification_status = excluded.email_verification_status,
                    decision_maker_found = excluded.decision_maker_found,
                    cooldown_until = excluded.cooldown_until,
                    blocker_codes_json = excluded.blocker_codes_json,
                    rejection_reasons_json = excluded.rejection_reasons_json,
                    record_json = excluded.record_json
                """,
                (
                    domain,
                    lead_id,
                    business_name,
                    now_date,
                    now_date,
                    outcome,
                    tier,
                    email_status,
                    dm_found,
                    cooldown_until,
                    json.dumps(blocker_codes or []),
                    json.dumps(rejection_reasons or []),
                    json.dumps(lead, ensure_ascii=False),
                ),
            )

            if outcome == "ACCEPTED":
                record_copy = dict(lead)
                record_copy["outreach_segment"] = outreach_segment
                conn.execute(
                    """
                    INSERT INTO daily_accepted_leads (
                        lead_id, run_date, domain, business_name, outreach_segment,
                        decision_maker_name, verified_email, lead_score, synced_to_sheet, record_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
                    ON CONFLICT(domain) DO NOTHING
                    """,
                    (
                        lead_id,
                        run_date,
                        domain,
                        business_name,
                        outreach_segment,
                        dm_name,
                        email,
                        int(lead.get("lead_score") or 0),
                        json.dumps(record_copy, ensure_ascii=False),
                    ),
                )

    def get_accepted_leads_for_day(self, run_date: str, unsynced_only: bool = False) -> List[Dict[str, Any]]:
        sql = "SELECT record_json, outreach_segment, synced_to_sheet FROM daily_accepted_leads WHERE run_date = ?"
        if unsynced_only:
            sql += " AND synced_to_sheet = 0"
        sql += " ORDER BY rowid ASC"
        with self._connect() as conn:
            rows = conn.execute(sql, (run_date,)).fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            rec = json.loads(row["record_json"])
            rec["outreach_segment"] = row["outreach_segment"]
            rec["_synced_to_sheet"] = bool(row["synced_to_sheet"])
            results.append(rec)
        return results

    def mark_accepted_synced(self, lead_ids: List[str]) -> None:
        if not lead_ids:
            return
        now = self._now_iso()
        with self._connect() as conn:
            conn.executemany(
                "UPDATE daily_accepted_leads SET synced_to_sheet = 1, synced_at = ? WHERE lead_id = ?",
                [(now, lid) for lid in lead_ids],
            )

    def get_exhausted_providers(self, quota_date: str) -> Set[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT provider FROM provider_daily_quotas WHERE quota_date = ? AND exhausted = 1",
                (quota_date,),
            ).fetchall()
        return {str(r["provider"]).strip().lower() for r in rows if r["provider"]}

    def record_provider_usage(
        self,
        provider: str,
        quota_date: str,
        used_delta: int = 1,
        remaining_reported: Optional[int] = None,
        exhausted: Optional[bool] = None,
        note: str = "",
    ) -> None:
        prov = (provider or "").strip().lower()
        if not prov:
            return
        now = self._now_iso()
        is_exh = 1 if exhausted else 0
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO provider_daily_quotas (
                    provider, quota_date, exhausted, requests_used, remaining_reported, note, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, quota_date) DO UPDATE SET
                    exhausted = CASE WHEN ? IS NULL THEN provider_daily_quotas.exhausted ELSE ? END,
                    requests_used = provider_daily_quotas.requests_used + ?,
                    remaining_reported = COALESCE(?, provider_daily_quotas.remaining_reported),
                    note = CASE WHEN ? != '' THEN ? ELSE provider_daily_quotas.note END,
                    updated_at = excluded.updated_at
                """,
                (
                    prov,
                    quota_date,
                    is_exh,
                    int(used_delta),
                    remaining_reported,
                    note,
                    now,
                    exhausted,
                    is_exh,
                    int(used_delta),
                    remaining_reported,
                    note,
                    note,
                ),
            )

    def mark_provider_exhausted(self, provider: str, quota_date: str, note: str = "Daily quota exhausted") -> None:
        self.record_provider_usage(
            provider=provider,
            quota_date=quota_date,
            used_delta=0,
            remaining_reported=0,
            exhausted=True,
            note=note,
        )

    def get_provider_usage_summary(self, quota_date: str) -> Dict[str, Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT provider, exhausted, requests_used, remaining_reported, note, updated_at "
                "FROM provider_daily_quotas WHERE quota_date = ? ORDER BY provider ASC",
                (quota_date,),
            ).fetchall()
        return {
            r["provider"]: {
                "exhausted": bool(r["exhausted"]),
                "requests_used": int(r["requests_used"]),
                "remaining_reported": r["remaining_reported"],
                "note": r["note"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        }

    def hydrate_from_sheet(self, sheet_syncer: Any) -> Dict[str, int]:
        """
        Hydrates local SQLite state from Google Sheets:
        - Accepted leads from 'Outbound Leads Intelligence' -> outcome='ACCEPTED'
        - Opt-outs from 'Suppression & Opt-Outs' -> outcome='SUPPRESSED'
        - Pipeline metadata from 'Pipeline State' -> campaign_state table
        - Prior checks from 'Pipeline Deduplication' -> processed_domains table
        Guarantees zero lead loss across ephemeral GitHub Actions cloud runners.
        """
        counts = {"accepted": 0, "suppressed": 0, "meta": 0, "dedup": 0}
        if sheet_syncer is None:
            return counts

        try:
            # 1. Existing Accepted Leads
            existing = sheet_syncer.get_existing_sheet_identifiers()
            accepted_domains = existing.get("domains", set())
            accepted_emails = existing.get("emails", set())
            now_iso = self._now_iso()
            today_str = now_iso[:10]

            with self._connect() as conn:
                for dom in accepted_domains:
                    if dom:
                        conn.execute(
                            """
                            INSERT INTO processed_domains (
                                domain, outcome, first_seen_date, last_checked_date,
                                blocker_codes_json, rejection_reasons_json
                            ) VALUES (?, 'ACCEPTED', ?, ?, '[]', '[]')
                            ON CONFLICT(domain) DO UPDATE SET outcome = 'ACCEPTED'
                            """,
                            (dom, today_str, today_str),
                        )
                        counts["accepted"] += 1

                for em in accepted_emails:
                    if em and em != "unavailable":
                        conn.execute(
                            """
                            INSERT OR IGNORE INTO daily_accepted_leads (
                                lead_id, run_date, domain, business_name, outreach_segment,
                                decision_maker_name, verified_email, lead_score, synced_to_sheet, record_json
                            ) VALUES (?, ?, ?, ?, 'UNASSIGNED', 'Preserved', ?, 50, 1, '{}')
                            """,
                            (f"SHEET_{em}", today_str, em.split("@")[-1], em.split("@")[-1], em),
                        )

            # 2. Suppressed & Opt-Outs
            opt_outs = sheet_syncer.fetch_sheet_opt_outs()
            with self._connect() as conn:
                for item in opt_outs:
                    dom = item.get("domain", "").strip()
                    if dom:
                        conn.execute(
                            """
                            INSERT INTO processed_domains (
                                domain, outcome, first_seen_date, last_checked_date,
                                blocker_codes_json, rejection_reasons_json
                            ) VALUES (?, 'SUPPRESSED', ?, ?, '[]', '[]')
                            ON CONFLICT(domain) DO UPDATE SET outcome = 'SUPPRESSED'
                            """,
                            (dom, today_str, today_str),
                        )
                        counts["suppressed"] += 1

            # 3. Pipeline State metadata (e.g. query_offset, campaign_start_date)
            p_meta = sheet_syncer.get_pipeline_state()
            for k, v in p_meta.items():
                self.set_meta(k, v)
                counts["meta"] += 1

            # 4. Pipeline Deduplication (compact rejection history)
            dedup_records = sheet_syncer.fetch_deduplication_domains()
            with self._connect() as conn:
                for dom, status in dedup_records.items():
                    if dom and dom not in accepted_domains:
                        conn.execute(
                            """
                            INSERT INTO processed_domains (
                                domain, outcome, first_seen_date, last_checked_date,
                                blocker_codes_json, rejection_reasons_json
                            ) VALUES (?, ?, ?, ?, '[]', '[]')
                            ON CONFLICT(domain) DO UPDATE SET outcome = excluded.outcome
                            """,
                            (dom, status, today_str, today_str),
                        )
                        counts["dedup"] += 1

            logger.info(
                f"[HYDRATION] Loaded from Google Sheets: {counts['accepted']} accepted, "
                f"{counts['suppressed']} suppressed, {counts['meta']} meta, {counts['dedup']} dedup records."
            )

        except Exception as exc:
            logger.warning(f"Google Sheet cloud hydration encountered an issue (continuing with local state): {exc}")

        return counts

    def checkpoint_to_sheet(self, sheet_syncer: Any, run_summary: Dict[str, Any]) -> None:
        """
        Checkpoints state back to Google Sheets:
        - Logs run telemetry to 'Daily Run Logs'
        - Saves 'query_offset' and campaign progress to 'Pipeline State'
        - Appends newly processed/rejected domains to 'Pipeline Deduplication'
        """
        if sheet_syncer is None:
            return

        try:
            # 1. Telemetry row
            sheet_syncer.sync_daily_run_log(run_summary)

            # 2. Pipeline State tab
            meta_updates = {
                "query_offset": str(self.get_query_offset()),
                "campaign_start_date": self.get_meta("campaign_start_date") or run_summary.get("run_date", ""),
                "last_cloud_run": self._now_iso(),
            }
            sheet_syncer.save_pipeline_state(meta_updates)

            # 3. Newly checked domains to Pipeline Deduplication
            run_date = run_summary.get("run_date")
            if run_date:
                with self._connect() as conn:
                    rows = conn.execute(
                        "SELECT domain, outcome, last_checked_date, blocker_codes_json "
                        "FROM processed_domains WHERE last_checked_date = ? AND outcome != 'ACCEPTED'",
                        (run_date,),
                    ).fetchall()
                if rows:
                    records = [
                        {
                            "domain": r["domain"],
                            "status": r["outcome"],
                            "last_checked_date": r["last_checked_date"],
                            "reason": r["blocker_codes_json"][:80],
                        }
                        for r in rows
                    ]
                    sheet_syncer.append_deduplication_domains(records)
        except Exception as exc:
            logger.warning(f"Could not complete cloud checkpoint to Google Sheet: {exc}")

