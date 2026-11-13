"""
Unit and Integration Tests for LeadScorer, Qualification Categorization,
Triple-Lock Tier 1 Rules, Compliance Separation, and Batch Reclassification.
"""

import json
from pathlib import Path

import pytest

from reclassify_batch import reclassify_leads
from run_batch import LeadIntelligenceEngine
from src.compliance.compliance_checker import ComplianceChecker
from src.scoring.lead_scorer import (
    LeadScorer,
    TIER_1_HOT,
    TIER_2_WARM,
    TIER_3_LOW,
    TIER_ENTERPRISE,
    TIER_EXCLUDED,
    TIER_LOW_PRIORITY,
    TIER_NEEDS_RESEARCH,
)
from src.storage.sheet_schema import validate_lead_record


@pytest.fixture
def scorer():
    return LeadScorer()


def test_weights_distribution(scorer):
    """Verifies that max sub-weights sum exactly to 100 points."""
    max_scores = scorer.weights.get("max_scores", {})
    total = sum(max_scores.values())
    assert total == 100
    assert max_scores["business_and_industry_fit"] == 25
    assert max_scores["decision_maker_identification"] == 25
    assert max_scores["evidence_of_potential_problems"] == 35
    assert max_scores["contact_quality_and_reachability"] == 15


def test_triple_lock_tier1_qualified(scorer):
    """
    Tier 1 qualified lead:
    Score >= 75 AND Confirmed DM AND Target Fit AND Problem Evidence >= 12.
    """
    lead_data = {
        "industry": "Marketing agencies",
        "country": "US",
        "employee_count": 15,
        "dm_tier": "tier_1",
        "decision_maker_name": "Sarah Jenkins",
        "decision_maker_title": "Founder & CEO",
        "signal_score": 25,
        "potential_buying_signals": [
            {"signal_type": "STATIC_FORM_NO_CALENDAR", "points": 12, "source_url": "https://example.com/contact"}
        ],
        "email_verification_status": "Provider-Verified",
        "phone_status": "Public Business Phone"
    }

    result = scorer.score_lead(lead_data)
    assert result["total_score"] >= 75
    assert result["triple_lock_status"]["all_passed"] is True
    assert result["qualification_tier"] == TIER_1_HOT


def test_triple_lock_high_score_missing_dm_capped_at_tier2(scorer):
    """
    A high numerical score (>= 75) without a verified decision-maker
    MUST NOT be Tier 1. It must be capped at Tier 2 - Warm.
    """
    lead_data = {
        "industry": "Marketing agencies",
        "country": "UK",
        "employee_count": 20,
        "dm_tier": "tier_4",
        "decision_maker_name": "Unavailable",
        "decision_maker_title": "Unavailable",
        "signal_score": 35,
        "potential_buying_signals": [
            {"signal_type": "STATIC_FORM_NO_CALENDAR", "points": 12},
            {"signal_type": "MANUAL_FOLLOWUP_FRICTION", "points": 10},
            {"signal_type": "DISCONNECTED_FORM_STACK", "points": 8},
            {"signal_type": "NO_CONVERSATIONAL_WIDGET", "points": 5}
        ],
        "email_verification_status": "Provider-Verified",
        "phone_status": "Public Business Phone"
    }

    result = scorer.score_lead(lead_data)
    assert result["triple_lock_status"]["confirmed_decision_maker"] is False
    assert result["triple_lock_status"]["all_passed"] is False
    assert result["qualification_tier"] == TIER_2_WARM
    assert "Triple-Lock failed on: Unconfirmed Decision-Maker" in result["tier_rationale"]


def test_triple_lock_missing_problem_evidence_capped_at_tier2(scorer):
    """
    A lead with a verified Founder but NO observed problem evidence (<12 pts)
    MUST NOT be Tier 1. It must be capped at Tier 2 - Warm.
    """
    lead_data = {
        "industry": "Consulting firms",
        "country": "US",
        "employee_count": 10,
        "dm_tier": "tier_1",
        "decision_maker_name": "Marcus Vance",
        "decision_maker_title": "Managing Partner",
        "signal_score": 10,
        "potential_buying_signals": [
            {"signal_type": "MANUAL_FOLLOWUP_FRICTION", "points": 10}
        ],
        "email_verification_status": "Provider-Verified",
        "phone_status": "Public Business Phone"
    }

    result = scorer.score_lead(lead_data)
    assert result["triple_lock_status"]["credible_problem_evidence"] is False
    assert result["qualification_tier"] == TIER_2_WARM
    assert "Triple-Lock failed on: Insufficient Problem Evidence (<12 pts)" in result["tier_rationale"]


def test_tier_3_low_classification(scorer):
    """Completed SMB records scoring 40-59 remain Tier 3 - Low."""
    lead_data = {
        "domain": "solidagency.com",
        "website": "https://solidagency.com",
        "industry": "Marketing agencies",
        "country": "US",
        "employee_count": "50-100 (Estimate)",
        "dm_tier": "tier_4",
        "decision_maker_name": "Unavailable",
        "signal_score": 17,
        "potential_buying_signals": [{"signal_type": "STATIC_FORM_NO_CALENDAR", "points": 12}],
        "email_verification_status": "Publicly Listed (Unverified)",
        "phone_status": "Public Business Phone",
        "research_status": "COMPLETED",
    }

    result = scorer.score_lead(lead_data)
    assert 40 <= result["total_score"] <= 59
    assert result["qualification_tier"] == TIER_3_LOW


def test_low_scoring_smb_retained_as_low_priority_prospect(scorer):
    """
    Valid SMB records scoring < 40 with completed research MUST NOT be disqualified;
    they are retained as 'Low-Priority Prospect' for review and manual enrichment.
    """
    lead_data = {
        "domain": "directiveconsulting.com",
        "website": "https://directiveconsulting.com/",
        "industry": "Marketing agencies",
        "country": "US",
        "estimated_employees": "50-100 (Estimate)",
        "dm_tier": "tier_4",
        "decision_maker_name": "Unavailable",
        "signal_score": 5,
        "potential_buying_signals": [{"signal_type": "NO_CONVERSATIONAL_WIDGET", "points": 5}],
        "email_verification_status": "Unavailable",
        "phone_status": "Public Business Phone",
        "research_status": "COMPLETED",
        "page_title": "B2B Marketing Agency - Directive",
        "business_description": "B2B marketing agency.",
        "evidence_urls": ["https://directiveconsulting.com/"],
    }

    result = scorer.score_lead(lead_data)
    assert result["total_score"] == 31
    assert result["qualification_tier"] == TIER_LOW_PRIORITY
    assert "retained" in result["tier_rationale"].lower()


def test_enterprise_prospect_over_250_employees(scorer):
    """
    Companies > 250 employees with completed research MUST be classified separately
    as 'Enterprise Prospect' rather than discarded, while retaining honest diagnostics
    and keeping Triple-Lock all_passed False.
    """
    lead_data = {
        "domain": "bigagency.com",
        "website": "https://bigagency.com",
        "industry": "Marketing agencies",
        "country": "UK",
        "estimated_employees": "1000+ (Confirmed)",
        "employee_status": "Confirmed",
        "employee_source_url": "https://bigagency.com/about",
        "dm_tier": "tier_2",
        "decision_maker_name": "Rachelle Risner",
        "decision_maker_title": "Managing Director",
        "signal_score": 15,
        "potential_buying_signals": [
            {"signal_type": "STATIC_FORM_NO_CALENDAR", "points": 12, "source_url": "https://bigagency.com/contact"}
        ],
        "email_verification_status": "Unavailable",
        "phone_status": "Unavailable",
        "research_status": "COMPLETED",
    }

    result = scorer.score_lead(lead_data)
    assert result["total_score"] == 55  # 20 fit + 20 dm + 15 signals + 0 contact
    assert result["qualification_tier"] == TIER_ENTERPRISE
    assert result["triple_lock_status"]["confirmed_decision_maker"] is True
    assert result["triple_lock_status"]["credible_problem_evidence"] is True
    assert result["triple_lock_status"]["strong_business_fit"] is False
    assert result["triple_lock_status"]["all_passed"] is False
    assert "Enterprise prospect" in result["tier_rationale"]


def test_insufficient_research_classified_as_needs_further_research(scorer):
    """
    Failed site fetches, bot challenge pages, and empty scrapes classify as
    'Needs Further Research' rather than being disqualified for a low score.
    """
    failed_fetch = {
        "domain": "ignitedigital.com",
        "website": "https://ignitedigital.com",
        "industry": "Marketing agencies",
        "country": "US",
        "estimated_employees": "10-25 (Estimate)",
        "signal_score": 0,
        "research_status": "FAILED: Connection Failed / Host Unreachable",
        "business_description": "Public description unavailable.",
        "evidence_urls": [],
    }
    res1 = scorer.score_lead(failed_fetch)
    assert res1["total_score"] == 25
    assert res1["qualification_tier"] == TIER_NEEDS_RESEARCH
    assert res1["triple_lock_status"]["all_passed"] is False

    bot_blocked = {
        "domain": "blockedsite.com",
        "website": "https://blockedsite.com",
        "industry": "Marketing agencies",
        "country": "US",
        "estimated_employees": "25-50 (Estimate)",
        "signal_score": 0,
        "research_status": "COMPLETED",
        "page_title": "Just a moment...",
        "business_description": "Public description unavailable.",
        "evidence_urls": [],
    }
    res2 = scorer.score_lead(bot_blocked)
    assert res2["qualification_tier"] == TIER_NEEDS_RESEARCH


def test_bridgespan_edge_case_failed_research_overrides_enterprise_size(scorer):
    """
    If a >250 employee company has a failed website audit (e.g., The Bridgespan Group),
    Needs Further Research takes precedence while preserving its confirmed sizing context.
    """
    bridgespan = {
        "domain": "bridgespan.org",
        "website": "https://bridgespan.org",
        "industry": "Consulting firms",
        "country": "US",
        "estimated_employees": "400+ (Confirmed)",
        "employee_status": "Confirmed",
        "employee_source_url": "https://www.bridgespan.org/about-us/overview",
        "signal_score": 0,
        "decision_maker_name": "Unavailable",
        "research_status": "FAILED: Connection Failed / Host Unreachable",
        "business_description": "Public description unavailable.",
        "evidence_urls": [],
    }

    result = scorer.score_lead(bridgespan)
    assert result["total_score"] == 20
    assert result["qualification_tier"] == TIER_NEEDS_RESEARCH
    assert "400+ (Confirmed)" in result["tier_rationale"]
    assert "bridgespan.org/about-us/overview" in result["tier_rationale"]
    assert result["triple_lock_status"]["all_passed"] is False


def test_excluded_only_for_genuinely_ineligible_records(scorer):
    """
    Only suppressed/opted-out records, duplicates, invalid/missing domains,
    aggregator platforms, placeholders, or non-B2B entities are classified as Excluded.
    """
    base = {
        "industry": "Marketing agencies",
        "country": "US",
        "estimated_employees": "25-50 (Estimate)",
        "research_status": "COMPLETED",
        "signal_score": 25,
    }

    suppressed = {**base, "domain": "optedout.com", "is_suppressed": True}
    assert scorer.score_lead(suppressed)["qualification_tier"] == TIER_EXCLUDED

    opt_out_comp = {**base, "domain": "optedout2.com", "compliance_status": "OPT_OUT_RECORDED"}
    assert scorer.score_lead(opt_out_comp)["qualification_tier"] == TIER_EXCLUDED

    duplicate = {**base, "domain": "dup.com", "is_duplicate": True}
    assert scorer.score_lead(duplicate)["qualification_tier"] == TIER_EXCLUDED

    invalid_dom = {**base, "domain": "not_a_valid_domain", "website": "not_a_valid_domain"}
    assert scorer.score_lead(invalid_dom)["qualification_tier"] == TIER_EXCLUDED

    empty_dom = {**base, "domain": "", "website": ""}
    assert scorer.score_lead(empty_dom)["qualification_tier"] == TIER_EXCLUDED

    directory_dom = {**base, "domain": "uk.linkedin.com", "website": "https://uk.linkedin.com/company/test"}
    assert scorer.score_lead(directory_dom)["qualification_tier"] == TIER_EXCLUDED

    placeholder_dom = {**base, "domain": "example.com", "website": "https://example.com"}
    assert scorer.score_lead(placeholder_dom)["qualification_tier"] == TIER_EXCLUDED

    non_b2b = {**base, "domain": "hobbyblog.org", "website": "https://hobbyblog.org", "entity_type": "personal"}
    assert scorer.score_lead(non_b2b)["qualification_tier"] == TIER_EXCLUDED


def test_compliance_strictly_separate_from_qualification(scorer):
    """
    Verifies two-way separation:
    1. A Tier 1 - Hot high-scoring lead remains restricted/review-required under ComplianceChecker.
    2. A RESTRICTED compliance status (e.g. Germany UWG §7 or consumer webmail) does NOT alter
       sales tiering in LeadScorer or grant outreach eligibility.
    """
    compliance = ComplianceChecker()

    german_agency = {
        "domain": "agentur-berlin.de",
        "website": "https://agentur-berlin.de",
        "industry": "Marketing agencies",
        "country": "DE",
        "employee_count": 20,
        "dm_tier": "tier_1",
        "decision_maker_name": "Lukas Weber",
        "decision_maker_title": "Founder & CEO",
        "signal_score": 25,
        "potential_buying_signals": [{"signal_type": "STATIC_FORM_NO_CALENDAR", "points": 12}],
        "email_verification_status": "Provider-Verified",
        "phone_status": "Public Business Phone",
        "research_status": "COMPLETED",
        "compliance_status": "RESTRICTED",
    }

    comp_eval = compliance.evaluate(country="DE", email="lukas@agentur-berlin.de")
    assert comp_eval["compliance_status"] == "RESTRICTED"

    score_res = scorer.score_lead(german_agency)
    # Scores well on B2B fit/signals/DM, never automatically excluded just for DE jurisdiction,
    # and never alters compliance_status from RESTRICTED.
    assert score_res["qualification_tier"] in (TIER_2_WARM, TIER_1_HOT)
    assert comp_eval["compliance_status"] == "RESTRICTED"

    # Even a Top UK Tier 1 lead remains REVIEW_REQUIRED in ComplianceChecker
    uk_comp = compliance.evaluate(country="UK", email="founder@builtvisible.com")
    assert uk_comp["compliance_status"] == "REVIEW_REQUIRED"


def test_suppressed_record_builder_populates_excluded_and_validates():
    """Suppressed records from LeadIntelligenceEngine carry valid Excluded schema fields."""
    rec = LeadIntelligenceEngine._build_suppressed_record(
        lead_id="ARI-US-SUP001",
        domain="suppressed.com",
        url="https://suppressed.com",
        country="US",
        industry="Marketing agencies",
        reason="Domain on suppression list.",
    )
    assert rec["lead_score"] == 0
    assert rec["qualification_tier"] == TIER_EXCLUDED
    assert rec["compliance_status"] == "OPT_OUT_RECORDED"
    assert rec["campaign_status"] == "Suppressed"

    is_valid, errs = validate_lead_record(rec)
    assert is_valid, f"Suppressed record failed sheet schema validation: {errs}"


def test_reclassify_actual_30_company_batch_preserves_all_records_and_scores():
    """
    Runs offline reclassification on the real 30-company export and verifies:
    - All 30 companies, 0-100 scores, evidence, research details, and compliance statuses are preserved.
    - No record receives automatic outreach eligibility (Campaign Status remains Ready for Manual Review).
    - Expected tier counts match the approved proposal.
    """
    base_dir = Path(__file__).resolve().parent.parent
    export_path = base_dir / "data" / "exports" / "mixed_services_uk_us_20261109_193531.json"
    with open(export_path, "r", encoding="utf-8") as f:
        original_leads = json.load(f)

    assert len(original_leads) == 30

    reclassified, tier_counts = reclassify_leads(original_leads)
    assert len(reclassified) == 30

    scorer = LeadScorer()
    for orig, upd in zip(original_leads, reclassified):
        assert upd["lead_id"] == orig["lead_id"]
        assert upd["business_name"] == orig["business_name"]
        assert upd["lead_score"] == orig["lead_score"]
        assert upd["compliance_status"] == orig["compliance_status"]
        assert upd["campaign_status"] == "Ready for Manual Review"
        assert upd["research_status"] == orig["research_status"]
        assert upd["potential_buying_signals"] == orig["potential_buying_signals"]
        assert upd["evidence_urls"] == orig["evidence_urls"]
        assert upd["decision_maker_name"] == orig["decision_maker_name"]
        assert upd["verified_email"] == orig["verified_email"]
        assert upd["formatted_phone"] == orig["formatted_phone"]

        # Confirm exact score formula stability
        recomputed = scorer.score_lead(upd)
        assert recomputed["total_score"] == orig["lead_score"]

        valid, errs = validate_lead_record(upd)
        assert valid, f"Reclassified lead {upd['lead_id']} failed schema validation: {errs}"

    assert tier_counts == {
        TIER_NEEDS_RESEARCH: 3,
        TIER_LOW_PRIORITY: 5,
        TIER_ENTERPRISE: 8,
        TIER_2_WARM: 6,
        TIER_3_LOW: 7,
        TIER_1_HOT: 1,
    }

    # Explicit checks on key boundary companies
    by_id = {r["lead_id"]: r for r in reclassified}
    assert by_id["ARI-UK-38A564"]["qualification_tier"] == TIER_1_HOT         # Builtvisible (86)
    assert by_id["ARI-US-F9808E"]["qualification_tier"] == TIER_NEEDS_RESEARCH  # Bridgespan Group (400+, failed fetch)
    assert "400+ (Confirmed)" in by_id["ARI-US-F9808E"]["tier_rationale"]
    assert by_id["ARI-UK-DACECE"]["qualification_tier"] == TIER_ENTERPRISE      # Brainlabs (1000+)
    assert by_id["ARI-UK-DACECE"]["triple_lock_status"]["confirmed_decision_maker"] is True
    assert by_id["ARI-UK-67731C"]["qualification_tier"] == TIER_LOW_PRIORITY    # Hallam Internet (39)
