"""
Integration and Unit Tests for Strict Acceptance Gate, 30/Day Acceptance-Target Loop,
Crash Recovery, Main-Sheet Hygiene, Discovery Exclusion, and Multi-Page Enrichment.
All tests run 100% offline.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from run_batch import LeadIntelligenceEngine
from run_daily import DailyPipelineRunner
from src.discovery.search_discovery import SearchDiscovery
from src.enrichment.buying_signals import BuyingSignalAuditor
from src.scoring.acceptance_evaluator import AcceptanceEvaluator
from src.scoring.lead_scorer import (
    TIER_1_HOT,
    TIER_2_WARM,
    TIER_ENTERPRISE,
    TIER_NEEDS_RESEARCH,
)
from src.storage.deduplicator import Deduplicator
from src.storage.local_store import LocalStore
from src.storage.sheet_schema import ALL_COLUMNS, DAILY_RUN_LOG_COLUMNS
from src.storage.sheet_syncer import SheetSyncer
from src.storage.state_store import PipelineStateStore


class MockTab:
    def __init__(self, title: str, initial_rows: List[List[Any]] = None):
        self.title = title
        self.rows: List[List[Any]] = [list(r) for r in initial_rows] if initial_rows else []
        self.row_count = 1000
        self.update_calls: List[Dict[str, Any]] = []
        self.append_calls: List[Dict[str, Any]] = []

    def get_all_values(self) -> List[List[str]]:
        return [[str(c) for c in r] for r in self.rows]

    def row_values(self, idx: int) -> List[str]:
        if 1 <= idx <= len(self.rows):
            return [str(c) for c in self.rows[idx - 1]]
        return []

    def col_values(self, col_idx: int) -> List[str]:
        return [str(r[col_idx - 1]) if len(r) >= col_idx else "" for r in self.rows]

    def update(self, range_name: str, values: List[List[Any]], **kwargs):
        self.update_calls.append({"range_name": range_name, "values": values, "kwargs": kwargs})
        import re

        if range_name == "A1:AA1":
            if not self.rows:
                self.rows.append(list(values[0]))
            else:
                self.rows[0][:27] = list(values[0][:27])
            return

        if range_name == "AB1:AG1":
            if not self.rows:
                self.rows.append([""] * 27 + list(values[0]))
            else:
                while len(self.rows[0]) < 33:
                    self.rows[0].append("")
                self.rows[0][27:33] = list(values[0][:6])
            return

        m_ab = re.match(r"^AB(\d+):AB(\d+)$", range_name)
        if m_ab:
            row_idx = int(m_ab.group(1)) - 1
            if row_idx < len(self.rows):
                while len(self.rows[row_idx]) < 28:
                    self.rows[row_idx].append("")
                self.rows[row_idx][27] = values[0][0]
            return

        m_log = re.match(r"^A(\d+):N(\d+)$", range_name)
        if m_log and self.title == "Daily Run Logs":
            row_idx = int(m_log.group(1)) - 1
            while len(self.rows) <= row_idx:
                self.rows.append([])
            self.rows[row_idx] = list(values[0])
            return

    def append_rows(self, values: List[List[Any]], **kwargs):
        self.append_calls.append({"values": values, "kwargs": kwargs})
        for r in values:
            self.rows.append(list(r))

    def append_row(self, values: List[Any], **kwargs):
        self.rows.append(list(values))


class MockSpreadsheet:
    def __init__(self, tabs: List[MockTab]):
        self._tabs = {t.title: t for t in tabs}

    def worksheets(self) -> List[MockTab]:
        return list(self._tabs.values())

    def worksheet(self, name: str) -> MockTab:
        if name in self._tabs:
            return self._tabs[name]
        raise Exception(f"Worksheet {name} not found")

    def add_worksheet(self, title: str, rows: int = 100, cols: int = 20) -> MockTab:
        tab = MockTab(title)
        self._tabs[title] = tab
        return tab


class MockClient:
    def __init__(self, spreadsheet: MockSpreadsheet):
        self.spreadsheet = spreadsheet

    def open_by_key(self, key: str) -> MockSpreadsheet:
        return self.spreadsheet


def _make_lead(
    idx: int,
    *,
    email_status: str = "SMTP-Verified",
    email: str = "",
    dm_name: str = "Sarah Jenkins",
    dm_title: str = "Founder & CEO",
    dm_tier: str = "tier_1",
    signal_score: int = 17,
    research_status: str = "COMPLETED",
    country: str = "US",
    industry: str = "Marketing agencies",
    estimated_employees: str = "15-30 (Estimate)",
    qualification_tier: str = TIER_1_HOT,
    compliance_status: str = "REVIEW_REQUIRED",
) -> Dict[str, Any]:
    domain = f"agency{idx}.com"
    resolved_email = email or f"sarah@{domain}"
    signals = (
        [
            {
                "signal_type": "STATIC_FORM_NO_CALENDAR",
                "points": 12,
                "description": "Potential buying signal.",
                "evidence": f"<form> on https://{domain}/contact",
                "source_url": f"https://{domain}/contact",
            },
            {
                "signal_type": "NO_CONVERSATIONAL_WIDGET",
                "points": 5,
                "description": "Potential buying signal.",
                "evidence": "No chat widget found.",
                "source_url": f"https://{domain}/contact",
            },
        ]
        if signal_score >= 12
        else []
    )
    return {
        "lead_id": f"ARI-{country[:2]}-{idx:04d}",
        "date_researched": "2026-11-11",
        "business_name": f"Agency {idx} LLC",
        "page_title": f"Agency {idx} | B2B Growth",
        "website": f"https://{domain}",
        "domain": domain,
        "industry": industry,
        "country": country,
        "city": "Austin",
        "decision_maker_name": dm_name,
        "decision_maker_title": dm_title,
        "decision_maker_tier": dm_tier,
        "decision_maker_evidence": f"Found executive card on https://{domain}/team",
        "decision_maker_source_url": f"https://{domain}/team",
        "decision_maker_linkedin": "Unavailable",
        "company_linkedin": "Unavailable",
        "verified_email": resolved_email,
        "email_verification_status": email_status,
        "email_verification_notes": "Checked cleanly.",
        "smtp_port_25_blocked": email_status == "Publicly Listed (Unverified)",
        "formatted_phone": "+15125550100",
        "phone_status": "Public Business Phone",
        "estimated_employees": estimated_employees,
        "employee_status": "Estimate",
        "employee_source_url": "",
        "business_description": "B2B digital agency.",
        "potential_buying_signals": signals,
        "signal_score": signal_score,
        "fit_hypothesis": f"Ariyx Systems Fit Hypothesis for https://{domain}/contact",
        "evidence_urls": [f"https://{domain}/contact"] if signals else [],
        "lead_score": 86 if email_status in ("SMTP-Verified", "Provider-Verified") else 82,
        "qualification_tier": qualification_tier,
        "compliance_status": compliance_status,
        "campaign_status": "Ready for Manual Review",
        "research_status": research_status,
    }


def test_acceptance_evaluator_strict_checks():
    # Default streamlined evaluator admits MX-confirmed Publicly Listed (Unverified) corporate emails
    # while keeping business, DM, signal, compliance, catch-all, invalid, and unavailable strict.
    evaluator = AcceptanceEvaluator()
    strict_evaluator = AcceptanceEvaluator(allow_unverified_public_emails=False)

    # 1. Valid SMB verified prospect -> Accepted
    good = _make_lead(1, email_status="SMTP-Verified")
    dec = evaluator.evaluate(good)
    assert dec.accepted is True
    assert dec.outreach_segment == "AGENCY_SPEED_TO_LEAD"
    assert dec.blocker_codes == []

    # Publicly Listed (Unverified) corporate email allowed in streamlined mode, blocked in strict verified-only mode
    unver_lead = _make_lead(1, email_status="Publicly Listed (Unverified)")
    assert evaluator.evaluate(unver_lead).accepted is True
    assert strict_evaluator.evaluate(unver_lead).accepted is False

    # 2. High score (82) with inconclusive / catch-all / invalid / unavailable email -> ALWAYS Rejected
    for bad_status in ["Verification Inconclusive", "Catch-All / Risky", "Invalid", "Unavailable"]:
        rec = _make_lead(2, email_status=bad_status)
        d = evaluator.evaluate(rec)
        assert d.accepted is False
        assert any("EMAIL" in c for c in d.blocker_codes)

    # 3. Consumer webmail & privacy/noreply alias -> Rejected even if SMTP-Verified
    gmail_rec = _make_lead(3, email="owner@gmail.com", email_status="SMTP-Verified")
    assert evaluator.evaluate(gmail_rec).accepted is False

    noreply_rec = _make_lead(4, email="noreply@agency4.com", email_status="SMTP-Verified")
    assert evaluator.evaluate(noreply_rec).accepted is False

    # 4. Missing DM -> Rejected
    no_dm = _make_lead(5, dm_name="Unavailable", dm_title="Unavailable", dm_tier="tier_4")
    assert evaluator.evaluate(no_dm).accepted is False

    # 5. Enterprise backlog (> 250 staff) -> Rejected from daily outreach sheet
    ent = _make_lead(6, estimated_employees="400+ (Confirmed)", qualification_tier=TIER_ENTERPRISE)
    d_ent = evaluator.evaluate(ent)
    assert d_ent.accepted is False
    assert "ENTERPRISE_BACKLOG_EXCLUDED" in d_ent.blocker_codes

    # 6. Restricted / Opt-out / Outside market -> Rejected
    de_lead = _make_lead(7, country="DE", compliance_status="RESTRICTED")
    assert evaluator.evaluate(de_lead).accepted is False

    opt_out = _make_lead(8, compliance_status="OPT_OUT_RECORDED")
    assert evaluator.evaluate(opt_out).accepted is False

    # 7. Duplicate domain -> Rejected
    dup_dec = evaluator.evaluate(_make_lead(9), known_domains={"agency9.com"})
    assert dup_dec.accepted is False
    assert "DUPLICATE_EXISTING_RECORD" in dup_dec.blocker_codes


def test_real_30_company_export_blocked_under_strict_sheet_gate():
    """
    Ensures unqualified records from the historical 30-company batch cannot enter the main outreach sheet:
    - Under strict_verified evaluator: all 30 are blocked because none were SMTP/API verified.
    - Under streamlined default evaluator: only genuinely qualified SMBs with DM + >=12 signals + valid
      Publicly Listed (Unverified) corporate email pass; enterprise/missing-DM/weak-signal/missing-email fail.
    """
    export_path = BASE_DIR / "data" / "exports" / "mixed_services_uk_us_reclassified_20261111_103825.json"
    if not export_path.exists():
        pytest.skip("Reclassified batch JSON not present.")

    from src.storage.sheet_schema import load_export_file

    leads = load_export_file(export_path)
    syncer = SheetSyncer(load_env=False)
    strict_plan = syncer.evaluate_batch(
        leads,
        [],
        strict_accepted_only=True,
        acceptance_evaluator=AcceptanceEvaluator(allow_unverified_public_emails=False),
    )
    assert strict_plan.summary["rejected_unaccepted"] == 30
    assert strict_plan.summary["case_2_inserts"] == 0

    streamlined_plan = syncer.dry_run(export_path, strict_accepted_only=True)
    # Most of the 30-company batch still fails qualification (enterprise, missing DM, low signals, missing email)
    assert streamlined_plan.summary["rejected_unaccepted"] >= 20
    assert any(a.domain == "builtvisible.com" for a in streamlined_plan.actions)


def test_daily_pipeline_loops_and_replaces_until_30_accepted(tmp_path):
    """
    Simulates discovering 45 companies where 15 fail (catch-all, invalid, missing DM,
    enterprise, failed HTTP) and 30 pass (using honest Publicly Listed (Unverified) & verified statuses)
    -> reaches 30/30 and syncs ONLY 30 into Outbound Leads Intelligence.
    """
    state_store = PipelineStateStore(db_path=str(tmp_path / "pipeline.db"))
    supp_path = tmp_path / "suppression.json"
    supp_path.write_text('{"domains": ["blocked-agency.com"], "emails": [], "company_names": ["Blacklisted Holdings"], "opt_outs": []}', encoding="utf-8")

    # Build curated mock outcome map across 47 candidates
    mock_records: Dict[str, Dict[str, Any]] = {}
    candidates: List[Dict[str, Any]] = [
        {"domain": "blocked-agency.com", "website_url": "https://blocked-agency.com", "country": "US", "industry": "Marketing agencies"},
        {"domain": "suppressed-co.com", "website_url": "https://suppressed-co.com", "business_name": "Blacklisted Holdings", "country": "US", "industry": "Marketing agencies"},
    ]

    # 15 candidates that MUST be rejected + replaced
    for i in range(1, 16):
        dom = f"reject{i}.com"
        candidates.append({"domain": dom, "website_url": f"https://{dom}", "country": "US", "industry": "Marketing agencies"})
        if i <= 4:
            rec = _make_lead(100 + i, email_status="Invalid")
        elif i <= 7:
            rec = _make_lead(100 + i, email_status="Catch-All / Risky")
        elif i <= 10:
            rec = _make_lead(100 + i, dm_name="Unavailable", dm_title="Unavailable", dm_tier="tier_4")
        elif i <= 12:
            rec = _make_lead(100 + i, qualification_tier=TIER_ENTERPRISE, estimated_employees="500+")
        else:
            rec = _make_lead(100 + i, research_status="FAILED: HTTP 403", qualification_tier=TIER_NEEDS_RESEARCH)
        rec["domain"] = dom
        rec["website"] = f"https://{dom}"
        rec["verified_email"] = f"founder@{dom}"
        mock_records[dom] = rec

    # 32 candidates that pass (target 30 -> must stop right at 30!)
    for i in range(1, 33):
        dom = f"pass{i}.com"
        candidates.append({"domain": dom, "website_url": f"https://{dom}", "country": "US" if i % 2 == 0 else "UK", "industry": "Consulting firms" if i % 3 == 0 else "Marketing agencies"})
        rec = _make_lead(
            200 + i,
            email_status="Publicly Listed (Unverified)" if i % 2 == 1 else "SMTP-Verified",
            country="US" if i % 2 == 0 else "UK",
            industry="Consulting firms" if i % 3 == 0 else "Marketing agencies",
            qualification_tier=TIER_1_HOT if i % 2 == 0 else TIER_2_WARM,
        )
        rec["domain"] = dom
        rec["website"] = f"https://{dom}"
        rec["verified_email"] = f"sarah@{dom}"
        mock_records[dom] = rec

    class FakeDiscovery:
        def __init__(self, pool):
            self.pool = list(pool)

        def discover_batch(self, max_results=20, exclude_domains=None, query_offset=0, include_wikidata=True):
            excl = set(exclude_domains or set())
            out = []
            for item in self.pool:
                if item["domain"] not in excl:
                    out.append(item)
                if len(out) >= 12:  # Force multiple iterative replacement batches!
                    break
            return out, query_offset + 1

    class FakeEngine:
        def __init__(self):
            self.deduplicator = Deduplicator(suppression_path=str(supp_path))
            self.email_verifier = LeadIntelligenceEngine(load_env=False).email_verifier
            self.local_store = LocalStore(exports_dir=str(tmp_path / "exports"))
            self.search_discovery = FakeDiscovery(candidates)

        def process_lead(self, domain, **kwargs):
            return dict(mock_records[domain])

    main_tab = MockTab("Outbound Leads Intelligence", [list(ALL_COLUMNS)])
    logs_tab = MockTab("Daily Run Logs", [list(DAILY_RUN_LOG_COLUMNS)])
    supp_tab = MockTab("Suppression & Opt-Outs")
    spreadsheet = MockSpreadsheet([main_tab, logs_tab, supp_tab])

    syncer = SheetSyncer(
        credentials_path="unused.json",
        spreadsheet_id="test-sheet-id",
        client=MockClient(spreadsheet),
        worksheet=main_tab,
        load_env=False,
    )

    runner = DailyPipelineRunner(
        engine=FakeEngine(),
        state_store=state_store,
        sheet_syncer=syncer,
        log_dir=tmp_path / "logs",
    )

    summary = runner.run_day(
        target_accepted=30,
        max_days=30,
        max_candidates=100,
        run_date="2026-11-11",
        sync_sheets=True,
        smtp_fail_fast_threshold=0,
        inter_request_delay=0.0,
        skip_preflight=True,
    )

    assert summary["status"] == "COMPLETED_TARGET_MET"
    assert summary["accepted_count"] == 30
    assert summary["research_attempts"] == 45  # 15 rejected + 30 accepted (suppressed blocked prior to fetch)
    assert summary["rejected_count"] == 15
    assert summary["skipped_suppressed"] == 1
    assert summary["sheets_inserted"] == 30

    # Strictly 1 header row + 30 accepted rows in Outbound Leads Intelligence (zero rejected rows!)
    assert len(main_tab.rows) == 31
    inserted_domains = {r[3].replace("https://", "") for r in main_tab.rows[1:]}
    assert len(inserted_domains) == 30
    assert not any(d.startswith("reject") for d in inserted_domains)
    assert "blocked-agency.com" not in inserted_domains

    # Operator Cols V-AA untouched except V initialized to Ready for Manual Review; Col AB segment populated
    assert main_tab.rows[1][21] == "Ready for Manual Review"
    assert main_tab.rows[1][27] in ("AGENCY_SPEED_TO_LEAD", "CONSULTING_PIPELINE_AUTOMATION")

    # Daily Run Logs tab synced with today's completed target row
    assert len(logs_tab.rows) == 2
    assert logs_tab.rows[1][0] == "2026-11-11"
    assert logs_tab.rows[1][2] == "COMPLETED_TARGET_MET"
    assert logs_tab.rows[1][4] == 30


def test_crash_recovery_resume_and_honest_shortfall(tmp_path):
    """
    Verifies:
    1. Crash recovery syncs previously accepted-but-unsynced leads without duplicating sheet rows.
    2. When discovery pool only yields 12 accepted leads, runner stops cleanly with STOPPED_SHORTFALL (never fabricates/lowers bar).
    """
    state_store = PipelineStateStore(db_path=str(tmp_path / "resume.db"))
    supp_path = tmp_path / "suppression.json"
    supp_path.write_text('{"domains": [], "emails": [], "company_names": [], "opt_outs": []}', encoding="utf-8")

    # Simulate pre-crash state on Day 1: 5 leads accepted, 3 already synced, 2 unsynced in SQLite
    state_store.start_or_resume_daily_run("2026-11-11", target_accepted=30)
    pre_leads = []
    for i in range(1, 6):
        rec = _make_lead(i, email_status="SMTP-Verified")
        state_store.record_candidate_outcome(
            "2026-11-11", rec, outcome="ACCEPTED", outreach_segment="AGENCY_SPEED_TO_LEAD"
        )
        pre_leads.append(rec)
    state_store.mark_accepted_synced([l["lead_id"] for l in pre_leads[:3]])
    state_store.save_daily_run({
        "run_date": "2026-11-11",
        "status": "RUNNING",
        "target_accepted": 30,
        "accepted_count": 5,
        "research_attempts": 8,
        "rejected_count": 3,
        "sheets_inserted": 3,
    })

    # Pre-seed MockTab with the 3 already-synced leads
    from src.storage.sheet_schema import format_insert_row
    initial_sheet_rows = [list(ALL_COLUMNS)] + [format_insert_row(r) for r in pre_leads[:3]]
    main_tab = MockTab("Outbound Leads Intelligence", initial_sheet_rows)
    logs_tab = MockTab("Daily Run Logs", [list(DAILY_RUN_LOG_COLUMNS)])
    spreadsheet = MockSpreadsheet([main_tab, logs_tab])
    syncer = SheetSyncer(
        credentials_path="unused.json",
        spreadsheet_id="test-sheet-id",
        client=MockClient(spreadsheet),
        worksheet=main_tab,
        load_env=False,
    )

    # Supply only 7 additional valid + 4 invalid leads before pool exhausts (total accepted = 5 + 7 = 12)
    extra_records: Dict[str, Dict[str, Any]] = {}
    pool: List[Dict[str, Any]] = []
    # Include a duplicate already on day 1 to confirm no repeat
    pool.append({"domain": "agency1.com", "website_url": "https://agency1.com"})
    for i in range(6, 13):
        rec = _make_lead(i, email_status="SMTP-Verified")
        extra_records[rec["domain"]] = rec
        pool.append({"domain": rec["domain"], "website_url": rec["website"]})
    for i in range(50, 54):
        rec = _make_lead(i, email_status="Invalid" if i % 2 == 0 else "Catch-All / Risky")
        extra_records[rec["domain"]] = rec
        pool.append({"domain": rec["domain"], "website_url": rec["website"]})

    class SmallEngine:
        def __init__(self):
            self.deduplicator = Deduplicator(suppression_path=str(supp_path))
            self.email_verifier = LeadIntelligenceEngine(load_env=False).email_verifier
            self.local_store = LocalStore(exports_dir=str(tmp_path / "exports"))
            self.search_discovery = SearchDiscovery()
            self.search_discovery.discover_batch = lambda **kw: (
                [c for c in pool if c["domain"] not in (kw.get("exclude_domains") or set())],
                1,
            )

        def process_lead(self, domain, **kwargs):
            return dict(extra_records[domain])

    runner = DailyPipelineRunner(
        engine=SmallEngine(),
        state_store=state_store,
        sheet_syncer=syncer,
        log_dir=tmp_path / "logs",
    )
    summary = runner.run_day(
        target_accepted=30,
        run_date="2026-11-11",
        sync_sheets=True,
        smtp_fail_fast_threshold=0,
        inter_request_delay=0.0,
        skip_preflight=True,
    )

    assert summary["status"] == "STOPPED_SHORTFALL"
    assert summary["accepted_count"] == 12  # 5 resumed + 7 newly accepted
    assert summary["sheets_inserted"] == 12  # 3 prior + 2 crash-recovered + 7 newly accepted (NO duplicates!)
    assert len(main_tab.rows) == 13  # 1 header + 12 accepted rows
    assert "Achieved 12/30" in summary["blocker_summary"]


def test_multipage_signal_audit_and_ranked_email_extraction():
    auditor = BuyingSignalAuditor()
    homepage_html = "<html><body><form><input name='email'></form></body></html>"
    contact_html = "<html><body><iframe src='https://calendly.com/team/call'></iframe></body></html>"

    # Cross-page detection sees Calendly on /contact and avoids false STATIC_FORM_NO_CALENDAR signal
    merged = auditor.audit_pages([
        (contact_html, "https://agency.com/contact", True),
        (homepage_html, "https://agency.com", False),
    ])
    types = [s["signal_type"] for s in merged["signals"]]
    assert "STATIC_FORM_NO_CALENDAR" not in types

    # Ranked email extraction ignores privacy/noreply/sentry and picks DM email over info@
    pages = [
        (
            '<a href="mailto:privacy@agency.com">Privacy</a>'
            '<a href="mailto:info@agency.com">Info</a>'
            '<a href="mailto:sarah@agency.com">Sarah Jenkins</a>'
            '<span>noreply@agency.com</span>',
            "https://agency.com/contact",
        )
    ]
    ranked = LeadIntelligenceEngine._extract_ranked_email_candidates(
        pages_with_urls=pages,
        target_domain="agency.com",
        dm_name="Sarah Jenkins",
    )
    emails = [e for e, _ in ranked]
    assert "privacy@agency.com" not in emails
    assert "noreply@agency.com" not in emails
    assert emails[0] == "sarah@agency.com"


def test_provider_quota_persistence_and_midrun_exhaustion_shortfall(tmp_path, monkeypatch):
    """
    Verifies SQLite quota persistence:
    - 2 accepted leads succeed via mocked QuickEmailVerification HTTPS API and sync cleanly.
    - Lead 3 triggers HTTP 402 quota exhaustion -> fallback port 25 probe fails -> stops cleanly
      with STOPPED_SHORTFALL, saves the 2 accepted leads, and records exhaustion in SQLite.
    - Resuming same day refuses pre-exhausted provider immediately with 0 HTTPS retries.
    """
    from src.verification.email_verifier import EmailVerifier

    class _FakeResp:
        def __init__(self, code, payload, headers=None):
            self.status_code = code
            self._payload = payload
            self.headers = headers or {}

        def json(self):
            return self._payload

    state_store = PipelineStateStore(db_path=str(tmp_path / "quota.db"))
    supp_path = tmp_path / "suppression.json"
    supp_path.write_text('{"domains": [], "emails": [], "company_names": [], "opt_outs": []}', encoding="utf-8")

    verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["quickemailverification"],
        provider_configs={"quickemailverification": {"api_key": "qev-key"}},
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: ([f"mx.{dom}"], None))
    monkeypatch.setattr(verifier, "_probe_smtp", lambda e, d, mx: ("UNVERIFIED", None, "Port 25 blocked.", True))
    monkeypatch.setattr(EmailVerifier, "probe_smtp_port_25", staticmethod(lambda timeout=3.0: (False, "TimeoutError: timed out")))

    http_calls = {"count": 0}

    def fake_qev_get(url, params=None, timeout=None):
        http_calls["count"] += 1
        if http_calls["count"] <= 2:
            return _FakeResp(
                200,
                {"result": "valid", "reason": "accepted_email", "accept_all": False, "disposable": False},
                headers={"X-QEV-Remaining-Credits": str(2 - http_calls["count"])},
            )
        return _FakeResp(402, {"message": "Quota exhausted"})

    monkeypatch.setattr(verifier.http_session, "get", fake_qev_get)

    pool = [{"domain": f"agency{i}.com", "website_url": f"https://agency{i}.com"} for i in range(1, 6)]

    class QuotaEngine:
        def __init__(self):
            self.deduplicator = Deduplicator(suppression_path=str(supp_path))
            self.email_verifier = verifier
            self.local_store = LocalStore(exports_dir=str(tmp_path / "exports"))
            self.search_discovery = SearchDiscovery()
            self.search_discovery.discover_batch = lambda **kw: (
                [c for c in pool if c["domain"] not in (kw.get("exclude_domains") or set())],
                1,
            )

        def process_lead(self, domain, **kwargs):
            idx = int(domain.replace("agency", "").replace(".com", ""))
            rec = _make_lead(idx, email_status="Unavailable")
            v_res = self.email_verifier.verify(rec["verified_email"])
            rec["email_verification_status"] = v_res["verification_status"]
            rec["smtp_port_25_blocked"] = v_res["smtp_port_25_blocked"]
            return rec

    main_tab = MockTab("Outbound Leads Intelligence", [list(ALL_COLUMNS)])
    logs_tab = MockTab("Daily Run Logs", [list(DAILY_RUN_LOG_COLUMNS)])
    spreadsheet = MockSpreadsheet([main_tab, logs_tab])
    syncer = SheetSyncer(
        credentials_path="unused.json",
        spreadsheet_id="test-sheet-id",
        client=MockClient(spreadsheet),
        worksheet=main_tab,
        load_env=False,
    )

    runner = DailyPipelineRunner(
        engine=QuotaEngine(),
        state_store=state_store,
        evaluator=AcceptanceEvaluator(allow_unverified_public_emails=False),
        sheet_syncer=syncer,
        log_dir=tmp_path / "logs",
    )
    summary1 = runner.run_day(
        target_accepted=30,
        run_date="2026-11-11",
        sync_sheets=True,
        smtp_fail_fast_threshold=0,
        inter_request_delay=0.0,
        skip_preflight=False,
    )

    assert summary1["status"] == "STOPPED_SHORTFALL"
    assert summary1["accepted_count"] == 2
    assert summary1["sheets_inserted"] == 2
    assert len(main_tab.rows) == 3  # Header + 2 strictly verified rows (lead 3 rejected & NOT in sheet)
    assert "exhausted" in summary1["blocker_summary"].lower()
    assert summary1["provider_quota_usage"]["quickemailverification"]["exhausted"] is True
    assert "quickemailverification" in state_store.get_exhausted_providers("2026-11-11")

    # Resuming on the same UTC date with a fresh EmailVerifier preloads exhausted status & does 0 HTTP retries
    fresh_verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["quickemailverification"],
        provider_configs={"quickemailverification": {"api_key": "qev-key"}},
    )
    monkeypatch.setattr(
        fresh_verifier.http_session,
        "get",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("Exhausted provider must NOT be called on resume")),
    )

    class ResumeEngine(QuotaEngine):
        def __init__(self):
            super().__init__()
            self.email_verifier = fresh_verifier

    runner2 = DailyPipelineRunner(
        engine=ResumeEngine(),
        state_store=state_store,
        evaluator=AcceptanceEvaluator(allow_unverified_public_emails=False),
        sheet_syncer=syncer,
        log_dir=tmp_path / "logs",
    )
    summary2 = runner2.run_day(
        target_accepted=30,
        run_date="2026-11-11",
        sync_sheets=True,
        inter_request_delay=0.0,
        skip_preflight=False,
    )
    assert summary2["accepted_count"] == 2
    assert "exhausted" in summary2["blocker_summary"].lower()


def test_pre_api_credit_conservation_and_catchall_shortcircuit(monkeypatch):
    """
    Confirms limited free verification credits are conserved at every stage:
    1. Missing DM / weak signal candidate with 2 emails makes 0 external API calls.
    2. Pre-qualified candidate whose 1st email is Catch-All short-circuits immediately (1 API call, NOT 2).
    3. Pre-qualified candidate whose 1st email is Invalid checks email #2 -> accepts Provider-Verified (2 calls).
    """
    engine = LeadIntelligenceEngine(load_env=False)

    html_no_dm = """
    <html>
      <head><title>Ghost Agency | Marketing</title><meta name="description" content="B2B agency"></head>
      <body>
        <form><input type="email" /></form>
        <a href="mailto:hello@ghostagency.com">Email Us</a>
        <a href="mailto:info@ghostagency.com">Info</a>
      </body>
    </html>
    """
    html_qualified = """
    <html>
      <head><title>Spark Growth | B2B Marketing Agency</title><meta name="description" content="B2B growth agency"></head>
      <body>
        <h2>Our Leadership</h2>
        <div class="team-card"><h3>Sarah Jenkins</h3><p>Founder &amp; CEO</p></div>
        <form><input type="email" /><button>Submit</button></form>
        <a href="mailto:sarah@sparkgrowth.com">Sarah</a>
        <a href="mailto:info@sparkgrowth.com">Info</a>
      </body>
    </html>
    """

    ext_calls: List[str] = []

    def fake_verify(email, source_is_provider_verified=False, source_url="", allow_external_provider=True, skip_smtp_probe=False):
        if not email:
            return {"email": "", "verification_status": "Unavailable", "smtp_port_25_blocked": False, "verification_notes": "", "verification_provider": ""}
        if allow_external_provider:
            ext_calls.append(email)
            if "catchall" in email:
                return {"email": email, "verification_status": "Catch-All / Risky", "smtp_port_25_blocked": False, "verification_notes": "Catch-all", "verification_provider": "quickemailverification"}
            if email.startswith("sarah@invalidfirst"):
                return {"email": email, "verification_status": "Invalid", "smtp_port_25_blocked": False, "verification_notes": "Mailbox unknown", "verification_provider": "quickemailverification"}
            return {"email": email, "verification_status": "Provider-Verified", "smtp_port_25_blocked": False, "verification_notes": "Verified", "verification_provider": "quickemailverification"}
        return {"email": email, "verification_status": "Publicly Listed (Unverified)", "smtp_port_25_blocked": False, "verification_notes": "Skipped prequal", "verification_provider": "skipped_prequalification"}

    monkeypatch.setattr(engine.email_verifier, "verify", fake_verify)

    # Case 1: Missing DM -> 0 external calls
    monkeypatch.setattr(engine, "_fetch_html", lambda url: (html_no_dm if url == "https://ghostagency.com" else "", url, None))
    rec1 = engine.process_lead(
        domain="ghostagency.com",
        website_url="https://ghostagency.com",
        industry="Marketing agencies",
        country="US",
        skip_internal_dedup=True,
        defer_email_api_unless_prequalified=True,
    )
    assert len(ext_calls) == 0
    assert rec1["email_verification_status"] == "Publicly Listed (Unverified)"

    # Case 2: Qualified DM + Catch-all on email #1 -> stops after 1st API call (NOT 2!)
    html_catchall = html_qualified.replace("sparkgrowth.com", "catchallco.com")
    monkeypatch.setattr(engine, "_fetch_html", lambda url: (html_catchall if url == "https://catchallco.com" else "", url, None))
    rec2 = engine.process_lead(
        domain="catchallco.com",
        website_url="https://catchallco.com",
        industry="Marketing agencies",
        country="US",
        skip_internal_dedup=True,
        defer_email_api_unless_prequalified=True,
        max_email_checks=2,
    )
    assert len(ext_calls) == 1
    assert rec2["email_verification_status"] == "Catch-All / Risky"

    # Case 3: Qualified DM + Invalid on email #1 -> falls through cleanly to email #2 (Provider-Verified)
    ext_calls.clear()
    html_invalid_first = html_qualified.replace("sparkgrowth.com", "invalidfirst.com")
    monkeypatch.setattr(engine, "_fetch_html", lambda url: (html_invalid_first if url == "https://invalidfirst.com" else "", url, None))
    rec3 = engine.process_lead(
        domain="invalidfirst.com",
        website_url="https://invalidfirst.com",
        industry="Marketing agencies",
        country="US",
        skip_internal_dedup=True,
        defer_email_api_unless_prequalified=True,
        max_email_checks=2,
    )
    assert len(ext_calls) == 2
    assert rec3["verified_email"] == "info@invalidfirst.com"
    assert rec3["email_verification_status"] == "Provider-Verified"


def test_expanded_30day_query_bank_and_wikidata_pagination(monkeypatch):
    from src.discovery.search_discovery import EXPANDED_QUERY_BANK

    assert len(EXPANDED_QUERY_BANK) >= 120
    countries = {q["country"] for q in EXPANDED_QUERY_BANK}
    assert {"US", "UK", "CA", "AU"}.issubset(countries)
    queries = [q["q"] for q in EXPANDED_QUERY_BANK]
    assert len(queries) == len(set(queries))

    sd = SearchDiscovery(delay_seconds=0.0)
    captured = {}
    monkeypatch.setattr(sd, "_search_duckduckgo_html", lambda **kw: [])

    def fake_wiki(limit=40, offset=0):
        captured["offset"] = offset
        return [{"domain": "paginatedagency.co.uk", "website_url": "https://paginatedagency.co.uk", "country": "UK", "industry": "Marketing agencies", "discovery_source": "Wikidata"}]

    monkeypatch.setattr(sd, "_discover_wikidata_agencies", fake_wiki)
    results, next_cur = sd.discover_batch(max_results=10, query_offset=5, include_wikidata=True)
    assert captured["offset"] == 75
    assert len(results) == 1
    assert next_cur > 5
