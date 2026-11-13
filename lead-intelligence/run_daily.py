"""
Ariyx Lead Intelligence System - Acceptance-Driven Daily Pipeline Runner
Discovers, researches, verifies, and strictly qualifies new B2B prospects until
the daily target of accepted prospects (default: 30/day) is reached, or reports an
honest shortfall and exact blockers without ever lowering standards or fabricating data.

Strict Boundaries:
- Only prospects passing ALL 9 criteria in AcceptanceEvaluator enter Outbound Leads Intelligence.
- Sends ZERO emails.
- Modifies ZERO files belonging to the live Ariyx website.
- Crash-safe: incremental SQLite checkpoints allow clean --resume without duplicate rows.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from run_batch import LeadIntelligenceEngine
from src.discovery.seed_loader import SeedLoader
from src.scoring.acceptance_evaluator import AcceptanceEvaluator
from src.scoring.lead_scorer import TIER_ENTERPRISE, TIER_NEEDS_RESEARCH
from src.storage.local_store import LocalStore
from src.storage.sheet_syncer import SheetSyncer
from src.storage.state_store import PipelineStateStore
from src.verification.email_verifier import EmailVerifier

logger = logging.getLogger("AriyxDailyPipeline")


def _load_settings(settings_path: Optional[Path] = None) -> Dict[str, Any]:
    target = settings_path or (BASE_DIR / "config" / "settings.json")
    if not target.exists():
        return {}
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {}


class DailyPipelineRunner:
    """
    Executes acceptance-target daily prospecting with persistent deduplication,
    strict main-sheet hygiene, and crash recovery.
    """

    def __init__(
        self,
        engine: Optional[LeadIntelligenceEngine] = None,
        state_store: Optional[PipelineStateStore] = None,
        evaluator: Optional[AcceptanceEvaluator] = None,
        sheet_syncer: Optional[SheetSyncer] = None,
        settings: Optional[Dict[str, Any]] = None,
        log_dir: Optional[Path] = None,
    ):
        self.settings = settings or _load_settings()
        daily_cfg = self.settings.get("daily_pipeline", {})
        smtp_timeout = float(daily_cfg.get("smtp_timeout_seconds", 3.5))

        self.engine = engine or LeadIntelligenceEngine(smtp_timeout=smtp_timeout)
        self.state_store = state_store or PipelineStateStore()
        allow_unverified = bool(
            daily_cfg.get(
                "allow_publicly_listed_unverified_email",
                not daily_cfg.get("require_verified_email", False),
            )
        )
        self.evaluator = evaluator or AcceptanceEvaluator(
            approved_markets=set(daily_cfg.get("approved_markets", ["US", "UK", "GB", "CA", "AU"])),
            exclude_enterprise=bool(daily_cfg.get("exclude_enterprise_from_outreach_sheet", True)),
            allow_unverified_public_emails=allow_unverified,
        )
        self.sheet_syncer = sheet_syncer
        self.retry_rejected_after_days = int(daily_cfg.get("retry_rejected_after_days", 14))
        self.retry_needs_research_after_days = int(daily_cfg.get("retry_needs_research_after_days", 3))
        self.defer_email_api_unless_prequalified = bool(daily_cfg.get("defer_email_api_unless_prequalified", True))
        self.max_email_checks_per_candidate = int(daily_cfg.get("max_email_checks_per_candidate", 2))
        self.log_dir = Path(log_dir) if log_dir else (BASE_DIR / "data" / "logs")

    def run_day(
        self,
        target_accepted: int = 30,
        max_days: int = 0,
        max_candidates: int = 240,
        max_minutes: float = 45.0,
        run_date: Optional[str] = None,
        sync_sheets: bool = False,
        static_candidates: Optional[List[Dict[str, Any]]] = None,
        smtp_fail_fast_threshold: int = 20,
        inter_request_delay: float = 1.2,
        skip_preflight: bool = False,
    ) -> Dict[str, Any]:
        """
        Runs (or resumes) one daily acceptance-driven prospecting cycle.
        """
        today = run_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        start_wall = time.monotonic()

        # Guard optional campaign horizon limit (default: max_days=0 runs ongoing indefinitely)
        if max_days and max_days > 0:
            progress = self.state_store.get_campaign_progress(max_days=max_days)
            existing_today = self.state_store.get_daily_run(today)
            if progress["campaign_complete"] and existing_today is None:
                msg = f"Campaign completed ({progress['days_logged']}/{max_days} days logged)."
                logger.info(msg)
                return {
                    "run_date": today,
                    "status": "CAMPAIGN_COMPLETE",
                    "target_accepted": target_accepted,
                    "accepted_count": 0,
                    "blocker_summary": msg,
                    "campaign_progress": progress,
                }

        run_summary = self.state_store.start_or_resume_daily_run(today, target_accepted=target_accepted)
        accepted_today = self.state_store.get_accepted_leads_for_day(today)
        email_counts: Dict[str, int] = dict(run_summary.get("email_verification_counts") or {})
        rejection_breakdown: Dict[str, int] = dict(run_summary.get("rejection_breakdown") or {})

        known_domains: Set[str] = set(self.state_store.get_blocked_domains(today))
        known_emails: Set[str] = set(self.state_store.get_known_accepted_emails())
        known_lead_ids: Set[str] = {str(r.get("lead_id", "")) for r in accepted_today if r.get("lead_id")}

        # Sync existing Google Sheet deduplication identifiers + opt-outs + any crash-recovery unsynced leads
        sheet_connected = False
        if sync_sheets and self.sheet_syncer is not None:
            try:
                self.state_store.hydrate_from_sheet(self.sheet_syncer)
            except Exception as e:
                logger.warning(f"Could not hydrate state from Google Sheet: {e}")

            sheet_ids = self.sheet_syncer.get_existing_sheet_identifiers()
            known_domains.update(sheet_ids.get("domains", set()))
            known_emails.update(sheet_ids.get("emails", set()))
            known_lead_ids.update(sheet_ids.get("lead_ids", set()))
            sheet_connected = True

            # Pull any operator-recorded opt-outs from sheet back into local suppression
            for opt in self.sheet_syncer.fetch_sheet_opt_outs():
                self.engine.deduplicator.add_to_suppression(
                    domain=opt.get("domain", ""),
                    email=opt.get("email", ""),
                    company_name=opt.get("company_name", ""),
                    reason=opt.get("reason", "sheet_opt_out"),
                )
                if opt.get("domain"):
                    known_domains.add(opt["domain"])

            # Push any locally accepted but previously unsynced leads first (crash recovery)
            unsynced = self.state_store.get_accepted_leads_for_day(today, unsynced_only=True)
            if unsynced:
                sync_res = self.sheet_syncer.sync_records(
                    unsynced,
                    source_label=f"daily_resume_{today}",
                    allow_inserts=True,
                    allow_updates=False,
                    strict_accepted_only=True,
                    write_segment_column=True,
                )
                inserted_ids = sync_res.get("inserted_lead_ids", [])
                self.state_store.mark_accepted_synced(inserted_ids)
                run_summary["sheets_inserted"] = int(run_summary.get("sheets_inserted", 0)) + len(inserted_ids)

        # Preload today's exhausted provider quotas and attach live usage recorder
        verifier = self.engine.email_verifier
        if hasattr(verifier, "exhausted_providers"):
            verifier.exhausted_providers.update(self.state_store.get_exhausted_providers(today))
        if hasattr(verifier, "on_provider_usage"):
            verifier.on_provider_usage = (
                lambda prov, delta, rem, exh, note: self.state_store.record_provider_usage(
                    provider=prov,
                    quota_date=today,
                    used_delta=delta,
                    remaining_reported=rem,
                    exhausted=True if exh else None,
                    note=note,
                )
            )

        configured_https = verifier.get_configured_external_providers() if hasattr(verifier, "get_configured_external_providers") else []
        if configured_https and not skip_preflight and static_candidates is None and hasattr(verifier, "refresh_external_provider_balances"):
            verifier.refresh_external_provider_balances()

        available_https = verifier.get_available_external_providers() if hasattr(verifier, "get_available_external_providers") else []
        has_available_https = bool(available_https)

        # Preflight check on SMTP port 25 only when no available HTTPS verifier is active
        allow_unverified_mode = bool(getattr(self.evaluator, "allow_unverified_public_emails", True))
        port_25_open, port_25_diag = (
            (True, f"Bypassed via active HTTPS verification waterfall: {available_https}")
            if has_available_https or static_candidates is not None or skip_preflight
            else EmailVerifier.probe_smtp_port_25(timeout=2.5)
        )
        if has_available_https:
            logger.info(f"Free HTTPS verification waterfall active: {available_https}")
        elif not port_25_open and allow_unverified_mode:
            logger.info(
                "PREFLIGHT NOTICE: Outbound TCP port 25 timed out (%s) and no external API keys are configured. "
                "Running streamlined free mode: live DNS MX checks verify domain mail routing and publicly listed "
                "business emails are labeled honestly as 'Publicly Listed (Unverified)' (skipping hung port 25 timeouts).",
                port_25_diag,
            )
        elif configured_https and not has_available_https and not port_25_open:
            logger.warning(
                "PREFLIGHT WARNING: All configured free HTTPS verification providers (%s) are exhausted for %s "
                "and outbound TCP port 25 is blocked (%s).",
                ", ".join(configured_https),
                today,
                port_25_diag,
            )
        elif not port_25_open:
            logger.warning(
                "PREFLIGHT WARNING: Outbound TCP port 25 appears blocked/timed out (%s) "
                "and no external HTTPS verification API keys are configured in .env. "
                "Strict verified-email acceptance cannot pass without HTTPS verification or open port 25.",
                port_25_diag,
            )

        discovery_cursor = self.state_store.get_query_offset()
        static_queue = list(static_candidates) if static_candidates is not None else None
        consecutive_empty_batches = 0
        consecutive_port25_blocked = 0
        audit_rejections: List[Dict[str, Any]] = []
        early_blocker_note = ""

        if static_queue is None and not skip_preflight and not has_available_https and not port_25_open and not allow_unverified_mode:
            if configured_https:
                early_blocker_note = (
                    f"All configured free HTTPS verification quotas ({', '.join(configured_https)}) are exhausted for {today} "
                    f"and outbound TCP port 25 is blocked ({port_25_diag}). Wait for daily quota reset (00:00 UTC)."
                )
            else:
                early_blocker_note = (
                    f"Outbound TCP port 25 is blocked ({port_25_diag}) and no free HTTPS email verification API keys are configured in .env."
                )

        # Main Acceptance-Driven Replacement Loop
        while (
            not early_blocker_note
            and int(run_summary.get("accepted_count", 0)) < target_accepted
            and int(run_summary.get("research_attempts", 0)) < max_candidates
            and ((time.monotonic() - start_wall) / 60.0) < max_minutes
        ):
            remaining_needed = target_accepted - int(run_summary.get("accepted_count", 0))
            remaining_budget = max_candidates - int(run_summary.get("research_attempts", 0))
            batch_limit = min(remaining_budget, max(remaining_needed * 2, 15))

            if static_queue is not None:
                batch = static_queue[:batch_limit]
                static_queue = static_queue[batch_limit:]
            else:
                all_excluded = known_domains | set(self.engine.deduplicator.suppressed_domains)
                batch, discovery_cursor = self.engine.search_discovery.discover_batch(
                    max_results=batch_limit,
                    exclude_domains=all_excluded,
                    query_offset=discovery_cursor,
                    include_wikidata=True,
                )
                self.state_store.set_query_offset(discovery_cursor)

            if not batch:
                consecutive_empty_batches += 1
                if consecutive_empty_batches >= 2 or static_queue is not None:
                    early_blocker_note = "Candidate discovery exhausted before reaching daily target."
                    break
                continue
            consecutive_empty_batches = 0

            stop_due_to_port25 = False
            for cand in batch:
                if (
                    int(run_summary.get("accepted_count", 0)) >= target_accepted
                    or int(run_summary.get("research_attempts", 0)) >= max_candidates
                    or ((time.monotonic() - start_wall) / 60.0) >= max_minutes
                ):
                    break

                raw_domain = cand.get("domain") or cand.get("website") or cand.get("website_url") or ""
                domain = self.engine.deduplicator.normalize_domain(raw_domain)
                if not domain:
                    continue

                if domain in known_domains:
                    run_summary["skipped_duplicates"] = int(run_summary.get("skipped_duplicates", 0)) + 1
                    continue

                is_supp, supp_reason = self.engine.deduplicator.is_suppressed(
                    domain, company_name=cand.get("business_name") or cand.get("title") or ""
                )
                if is_supp:
                    known_domains.add(domain)
                    run_summary["skipped_suppressed"] = int(run_summary.get("skipped_suppressed", 0)) + 1
                    continue

                known_domains.add(domain)
                run_summary["research_attempts"] = int(run_summary.get("research_attempts", 0)) + 1

                website = cand.get("website_url") or cand.get("website") or f"https://{domain}"
                currently_has_https = (
                    verifier.has_available_external_verifier()
                    if hasattr(verifier, "has_available_external_verifier")
                    else has_available_https
                )
                skip_smtp_now = (not currently_has_https and not port_25_open and static_queue is None)
                record = self.engine.process_lead(
                    domain=domain,
                    website_url=website,
                    industry=cand.get("industry") or "Marketing agencies",
                    country=cand.get("country") or "US",
                    city=cand.get("city", ""),
                    business_name_hint=cand.get("business_name") or cand.get("title") or "",
                    discovery_source=cand.get("discovery_source", "Free Search Discovery"),
                    estimated_employees=cand.get("estimated_employees"),
                    employee_status=cand.get("employee_status", "Unknown"),
                    employee_source_url=cand.get("employee_source_url", ""),
                    skip_internal_dedup=True,
                    defer_email_api_unless_prequalified=self.defer_email_api_unless_prequalified,
                    max_email_checks=self.max_email_checks_per_candidate,
                    skip_smtp_probe=skip_smtp_now,
                )

                if not record:
                    continue

                e_status = record.get("email_verification_status", "Unavailable")
                email_counts[e_status] = email_counts.get(e_status, 0) + 1
                if record.get("decision_maker_name") and record.get("decision_maker_name") != "Unavailable":
                    run_summary["dm_identified_count"] = int(run_summary.get("dm_identified_count", 0)) + 1

                if record.get("smtp_port_25_blocked") and e_status == "Publicly Listed (Unverified)":
                    consecutive_port25_blocked += 1
                elif self.engine.email_verifier.is_strictly_verified(e_status):
                    consecutive_port25_blocked = 0

                decision = self.evaluator.evaluate(
                    record,
                    known_domains=None,  # already deduplicated prior to processing this candidate
                    known_emails=known_emails,
                    known_lead_ids=known_lead_ids,
                )

                if decision.accepted:
                    record["outreach_segment"] = decision.outreach_segment
                    if record.get("verified_email"):
                        known_emails.add(str(record["verified_email"]).strip().lower())
                    if record.get("lead_id"):
                        known_lead_ids.add(str(record["lead_id"]))

                    self.state_store.record_candidate_outcome(
                        run_date=today,
                        lead=record,
                        outcome="ACCEPTED",
                        outreach_segment=decision.outreach_segment,
                    )
                    accepted_today.append(record)
                    run_summary["accepted_count"] = int(run_summary.get("accepted_count", 0)) + 1

                    # Incremental durable insert into Google Sheets (accepted prospects ONLY)
                    if sync_sheets and self.sheet_syncer is not None and sheet_connected:
                        sync_res = self.sheet_syncer.sync_records(
                            [record],
                            source_label=f"daily_{today}",
                            allow_inserts=True,
                            allow_updates=False,
                            strict_accepted_only=True,
                            write_segment_column=True,
                        )
                        inserted_ids = sync_res.get("inserted_lead_ids", [])
                        if inserted_ids:
                            self.state_store.mark_accepted_synced(inserted_ids)
                            run_summary["sheets_inserted"] = int(run_summary.get("sheets_inserted", 0)) + len(inserted_ids)
                else:
                    run_summary["rejected_count"] = int(run_summary.get("rejected_count", 0)) + 1
                    for code in decision.blocker_codes:
                        rejection_breakdown[code] = rejection_breakdown.get(code, 0) + 1

                    tier = record.get("qualification_tier", "")
                    if record.get("compliance_status") == "OPT_OUT_RECORDED":
                        outcome = "SUPPRESSED"
                        cooldown = None
                    elif tier == TIER_ENTERPRISE:
                        outcome = "ENTERPRISE"
                        cooldown = None
                    elif e_status in ("Catch-All / Risky", "Invalid"):
                        outcome = "REJECTED"
                        cooldown = 30
                    elif tier == TIER_NEEDS_RESEARCH or e_status == "Verification Inconclusive":
                        outcome = "NEEDS_RESEARCH"
                        cooldown = self.retry_needs_research_after_days
                    else:
                        outcome = "REJECTED"
                        cooldown = self.retry_rejected_after_days

                    self.state_store.record_candidate_outcome(
                        run_date=today,
                        lead=record,
                        outcome=outcome,
                        blocker_codes=decision.blocker_codes,
                        rejection_reasons=decision.blocking_reasons,
                        cooldown_days=cooldown,
                    )
                    audit_rejections.append({
                        "domain": domain,
                        "business_name": record.get("business_name"),
                        "email": record.get("verified_email"),
                        "email_verification_status": e_status,
                        "decision_maker": record.get("decision_maker_name"),
                        "signal_score": record.get("signal_score"),
                        "blocker_codes": decision.blocker_codes,
                        "blocking_reasons": decision.blocking_reasons,
                    })

                run_summary["email_verification_counts"] = email_counts
                run_summary["rejection_breakdown"] = rejection_breakdown
                self.state_store.save_daily_run(run_summary)

                still_has_https = (
                    verifier.has_available_external_verifier()
                    if hasattr(verifier, "has_available_external_verifier")
                    else has_available_https
                )
                if not allow_unverified_mode and configured_https and not still_has_https:
                    if not skip_preflight and static_candidates is None and "Bypassed via active HTTPS" in port_25_diag:
                        port_25_open, port_25_diag = EmailVerifier.probe_smtp_port_25(timeout=2.5)
                    if not port_25_open:
                        early_blocker_note = (
                            f"All configured free HTTPS verification quotas ({', '.join(configured_https)}) exhausted during run "
                            f"and port 25 is blocked; saved {run_summary.get('accepted_count', 0)} genuinely verified leads for {today}."
                        )
                        stop_due_to_port25 = True
                        break

                if (
                    not allow_unverified_mode
                    and smtp_fail_fast_threshold > 0
                    and not still_has_https
                    and consecutive_port25_blocked >= smtp_fail_fast_threshold
                    and int(run_summary.get("accepted_count", 0)) == 0
                ):
                    early_blocker_note = (
                        f"Stopped early after {consecutive_port25_blocked} consecutive MX-valid emails failed direct SMTP "
                        "verification due to outbound TCP port 25 timeout/block on this network with no free HTTPS API key configured."
                    )
                    stop_due_to_port25 = True
                    break

                if inter_request_delay > 0 and static_queue is None:
                    time.sleep(inter_request_delay)

            if stop_due_to_port25:
                break

        accepted_final = int(run_summary.get("accepted_count", 0))
        if accepted_final >= target_accepted:
            final_status = "COMPLETED_TARGET_MET"
            blocker_summary = "Daily acceptance target reached."
        else:
            final_status = "STOPPED_SHORTFALL"
            top_blockers = sorted(rejection_breakdown.items(), key=lambda kv: kv[1], reverse=True)[:4]
            top_str = ", ".join([f"{k}={v}" for k, v in top_blockers]) if top_blockers else "None logged"
            parts = [f"Achieved {accepted_final}/{target_accepted}."]
            if early_blocker_note:
                parts.append(early_blocker_note)
            elif ((time.monotonic() - start_wall) / 60.0) >= max_minutes:
                parts.append(f"Reached {max_minutes:.0f}m runtime guardrail.")
            elif int(run_summary.get("research_attempts", 0)) >= max_candidates:
                parts.append(f"Reached max_candidates={max_candidates} safety cap.")
            parts.append(f"Top blockers: {top_str}")
            blocker_summary = " ".join(parts)

        run_summary["status"] = final_status
        run_summary["email_verification_counts"] = email_counts
        run_summary["rejection_breakdown"] = rejection_breakdown
        run_summary["blocker_summary"] = blocker_summary
        run_summary["finished_at"] = datetime.now(timezone.utc).isoformat()
        self.state_store.save_daily_run(run_summary)

        # Save local accepted-only batch (if > 0) + local daily audit log
        export_paths: Dict[str, str] = {}
        if accepted_today:
            export_paths = self.engine.local_store.save_batch(accepted_today, batch_name=f"daily_accepted_{today}")

        log_dir = self.log_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        audit_path = log_dir / f"daily_run_report_{today}_{ts}.json"
        provider_quota_usage = self.state_store.get_provider_usage_summary(today)
        audit_payload = {
            "run_summary": run_summary,
            "preflight_port_25_open": port_25_open,
            "preflight_port_25_diagnostic": port_25_diag,
            "provider_quota_usage": provider_quota_usage,
            "campaign_progress": self.state_store.get_campaign_progress(max_days=max_days),
            "export_paths": export_paths,
            "rejected_samples": audit_rejections[:100],
        }
        audit_path.write_text(json.dumps(audit_payload, indent=2, ensure_ascii=False), encoding="utf-8")

        if sync_sheets and self.sheet_syncer is not None and sheet_connected:
            self.state_store.checkpoint_to_sheet(self.sheet_syncer, run_summary)

        run_summary["audit_report_path"] = str(audit_path)
        run_summary["export_paths"] = export_paths
        run_summary["preflight_port_25_open"] = port_25_open
        run_summary["provider_quota_usage"] = provider_quota_usage
        return run_summary

    def run_cloud_preflight(self) -> Dict[str, Any]:
        """
        Executes a 100% read-only cloud connectivity & credentials preflight check.
        Tests:
        1. Google Service Account authentication & Sheet read access (zero writes).
        2. DNS MX lookup resolution via dnspython.
        3. Web search discovery connectivity via DuckDuckGo.
        4. Outbound HTTPS fetch to verify network egress.
        Returns a verification report dictionary.
        """
        print("\n" + "=" * 78)
        print(" ARIYX LEAD INTELLIGENCE - CLOUD PREFLIGHT READ-ONLY VERIFICATION")
        print("=" * 78)

        results = {
            "google_sheets_auth": False,
            "google_sheets_read": False,
            "dns_resolution": False,
            "search_discovery": False,
            "web_https": False,
            "overall_status": "FAILED",
        }

        # 1. Google Sheets Authentication & Read Access
        print("[1/4] Testing Google Sheets Credentials & Read Access...")
        try:
            syncer = self.sheet_syncer or SheetSyncer()
            client = syncer._get_client()
            spreadsheet = client.open_by_key(syncer.spreadsheet_id)
            title = spreadsheet.title
            ws = spreadsheet.worksheet(syncer.worksheet_name)
            row_count = len(ws.col_values(1))
            print(f"      [PASS] Connected to Google Sheet: '{title}'")
            print(f"      [PASS] Verified read access to '{syncer.worksheet_name}' ({row_count} rows found).")
            results["google_sheets_auth"] = True
            results["google_sheets_read"] = True
        except Exception as e:
            print(f"      [FAIL] Google Sheets check failed: {e}")

        # 2. DNS Resolution
        print("[2/4] Testing Cloud DNS MX Resolution...")
        try:
            import dns.resolver
            answers = dns.resolver.resolve("google.com", "MX")
            print(f"      [PASS] DNS MX resolver functional ({len(answers)} MX records resolved).")
            results["dns_resolution"] = True
        except Exception as e:
            print(f"      [FAIL] DNS MX check failed: {e}")

        # 3. Search Discovery
        print("[3/4] Testing Search Discovery Connectivity...")
        try:
            from src.discovery.search_discovery import SearchDiscovery
            discovery = SearchDiscovery()
            test_results = discovery.discover(industry_key="Marketing agencies", country="UK", max_results=2)
            if test_results:
                print(f"      [PASS] Search discovery functional ({len(test_results)} candidate links retrieved).")
                results["search_discovery"] = True
            else:
                print("      [WARN] Search query returned 0 results, but network connection succeeded.")
                results["search_discovery"] = True
        except Exception as e:
            print(f"      [FAIL] Search discovery check failed: {e}")

        # 4. Outbound HTTPS
        print("[4/4] Testing Outbound HTTPS Fetch...")
        try:
            import requests
            resp = requests.get("https://httpbin.org/status/200", timeout=8)
            if resp.status_code == 200:
                print("      [PASS] Outbound HTTPS requests functional.")
                results["web_https"] = True
            else:
                print(f"      [WARN] Outbound HTTP returned status {resp.status_code}")
        except Exception as e:
            print(f"      [FAIL] Outbound HTTPS check failed: {e}")

        all_passed = (
            results["google_sheets_auth"]
            and results["google_sheets_read"]
            and results["dns_resolution"]
            and results["search_discovery"]
            and results["web_https"]
        )
        results["overall_status"] = "PASSED" if all_passed else "FAILED"

        print("=" * 78)
        if all_passed:
            print(" [PASS] ALL PREFLIGHT CHECKS PASSED — Environment is ready for cloud execution.")
        else:
            print(" [FAIL] PREFLIGHT FAILED — Review errors above before enabling cloud runs.")
        print("=" * 78 + "\n")
        return results


def main():
    parser = argparse.ArgumentParser(
        description="Ariyx Systems - Ongoing Acceptance-Driven Daily Lead Generation Pipeline (Target: 30/day)"
    )
    parser.add_argument("--cloud-preflight", action="store_true", help="Run read-only cloud connectivity and credentials preflight without writing anything")
    parser.add_argument("--target", type=int, default=30, help="Daily accepted prospect target (default: 30)")
    parser.add_argument("--max-days", type=int, default=0, help="Total campaign days limit (default: 0 = ongoing indefinitely)")
    parser.add_argument("--max-candidates", type=int, default=240, help="Safety cap on candidate sites researched per day")
    parser.add_argument("--max-minutes", type=float, default=45.0, help="Safety wall-clock cap per day in minutes")
    parser.add_argument("--run-date", type=str, default=None, help="Override UTC run date (YYYY-MM-DD)")
    parser.add_argument("--sync-sheets", action="store_true", help="Insert accepted leads ONLY into Outbound Leads Intelligence + update Daily Run Logs")
    parser.add_argument("--smtp-fail-fast", type=int, default=20, help="Stop cleanly after N consecutive port-25 blocked checks with 0 verified emails (0 disables)")
    parser.add_argument("--seed-file", type=str, default=None, help="Optional explicit CSV candidate pool for testing (NOT used by default)")
    parser.add_argument("--delay", type=float, default=1.2, help="Polite delay between website checks in seconds")

    args = parser.parse_args()

    if args.cloud_preflight:
        syncer = SheetSyncer()
        runner = DailyPipelineRunner(sheet_syncer=syncer)
        results = runner.run_cloud_preflight()
        sys.exit(0 if results.get("overall_status") == "PASSED" else 1)

    static_candidates = SeedLoader.load_from_csv(args.seed_file) if args.seed_file else None
    syncer = SheetSyncer() if args.sync_sheets else None

    runner = DailyPipelineRunner(sheet_syncer=syncer)
    summary = runner.run_day(
        target_accepted=args.target,
        max_days=args.max_days,
        max_candidates=args.max_candidates,
        max_minutes=args.max_minutes,
        run_date=args.run_date,
        sync_sheets=args.sync_sheets,
        static_candidates=static_candidates,
        smtp_fail_fast_threshold=args.smtp_fail_fast,
        inter_request_delay=args.delay,
    )

    day_label = f"{summary.get('campaign_day', '-')}" + (f"/{args.max_days}" if args.max_days > 0 else " (Ongoing)")
    print("\n" + "=" * 78)
    print(f" ARIYX DAILY ACCEPTANCE PIPELINE REPORT ({summary.get('run_date')})")
    print("=" * 78)
    print(f" Status:               {summary.get('status')}")
    print(f" Campaign Day:         {day_label}")
    print(f" Accepted Prospects:   {summary.get('accepted_count', 0)} / {summary.get('target_accepted', args.target)}")
    print(f" Research Attempts:    {summary.get('research_attempts', 0)}")
    print(f" Rejected Candidates:  {summary.get('rejected_count', 0)}")
    print(f" Duplicates Prevented: {summary.get('skipped_duplicates', 0)}")
    print(f" Suppressed Skipped:   {summary.get('skipped_suppressed', 0)}")
    print(f" Decision-Makers:      {summary.get('dm_identified_count', 0)}")
    print(f" Sheets Inserted:      {summary.get('sheets_inserted', 0)}")
    print(f" Email Breakdown:      {summary.get('email_verification_counts', {})}")
    print(f" Free API Usage:       {summary.get('provider_quota_usage', {})}")
    print(f" Top Blockers:         {summary.get('blocker_summary', '')}")
    print(f" Audit Report:         {summary.get('audit_report_path', '')}")
    print("=" * 78 + "\n")

    sys.exit(0 if summary.get("accepted_count", 0) >= args.target else 2)


if __name__ == "__main__":
    main()
