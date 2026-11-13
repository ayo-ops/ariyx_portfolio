"""
Unit tests for ComplianceChecker.
Enforces cautious compliance statuses: REVIEW_REQUIRED, RESTRICTED, ELIGIBILITY_NOT_ESTABLISHED, OPT_OUT_RECORDED.
Verifies that public email listing is NOT treated as consent.
"""

import pytest
from src.compliance.compliance_checker import ComplianceChecker


@pytest.fixture
def compliance():
    return ComplianceChecker()


def test_us_compliance_status(compliance):
    """US commercial outreach defaults to REVIEW_REQUIRED under CAN-SPAM."""
    eval_res = compliance.evaluate(country="US", email="sarah@agencyalpha.com")
    assert eval_res["compliance_status"] == "REVIEW_REQUIRED"
    assert "CAN-SPAM" in eval_res["framework"]
    assert any("Public email availability is NOT marketing consent" in note for note in eval_res["review_notes"])


def test_uk_compliance_status(compliance):
    """UK corporate B2B defaults to REVIEW_REQUIRED under PECR/UK GDPR."""
    eval_res = compliance.evaluate(country="UK", email="alex@consultinggroup.co.uk")
    assert eval_res["compliance_status"] == "REVIEW_REQUIRED"
    assert "PECR" in eval_res["framework"]
    assert any("corporate subscriber" in note.lower() for note in eval_res["review_notes"])


def test_germany_strict_restriction(compliance):
    """Germany strictly restricts cold B2B email under UWG §7 -> RESTRICTED."""
    eval_res = compliance.evaluate(country="DE", email="kontakt@agentur.de")
    assert eval_res["compliance_status"] == "RESTRICTED"
    assert "UWG" in eval_res["framework"]
    assert eval_res["risk_tier"] == "HIGH_RISK"


def test_consumer_webmail_restricted(compliance):
    """Consumer webmail (e.g. Gmail) cannot be contacted under B2B legitimate interest -> RESTRICTED."""
    eval_res = compliance.evaluate(country="US", email="businessowner123@gmail.com")
    assert eval_res["compliance_status"] == "RESTRICTED"
    assert eval_res["risk_tier"] == "HIGH_RISK"
    assert any("consumer webmail" in note.lower() for note in eval_res["review_notes"])


def test_unknown_country_eligibility_not_established(compliance):
    """Missing or unverified country defaults to ELIGIBILITY_NOT_ESTABLISHED."""
    eval_res = compliance.evaluate(country="", email="contact@mysterious.com")
    assert eval_res["compliance_status"] == "ELIGIBILITY_NOT_ESTABLISHED"
    assert eval_res["risk_tier"] == "UNKNOWN"


def test_suppressed_lead_opt_out_recorded(compliance):
    """Suppressed leads are marked OPT_OUT_RECORDED and PROHIBITED."""
    eval_res = compliance.evaluate(country="US", email="optout@domain.com", is_suppressed=True, suppression_reason="Unsubscribed")
    assert eval_res["compliance_status"] == "OPT_OUT_RECORDED"
    assert eval_res["risk_tier"] == "PROHIBITED"
