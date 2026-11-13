"""
Unit tests for Deduplicator and Suppression lists.
"""

import pytest
from src.storage.deduplicator import Deduplicator


@pytest.fixture
def deduplicator(tmp_path):
    supp_file = tmp_path / "suppression.json"
    supp_file.write_text('{"domains": ["blocked.com"], "emails": ["do-not-contact@agency.com"], "company_names": ["Blacklisted Corp"], "opt_outs": []}', encoding="utf-8")
    return Deduplicator(suppression_path=str(supp_file))


def test_domain_normalization(deduplicator):
    assert deduplicator.normalize_domain("https://www.AgencyAlpha.co.uk/services/") == "agencyalpha.co.uk"
    assert deduplicator.normalize_domain("http://marketing-pro.com:8080/home") == "marketing-pro.com"
    assert deduplicator.normalize_domain("WWW.SUB.DOMAIN.COM") == "sub.domain.com"


def test_suppression_check(deduplicator):
    is_supp, reason = deduplicator.is_suppressed("https://www.blocked.com/about")
    assert is_supp is True
    assert "blocked.com" in reason

    is_supp_email, reason_email = deduplicator.is_suppressed("clean.com", email="do-not-contact@agency.com")
    assert is_supp_email is True

    is_supp_clean, _ = deduplicator.is_suppressed("good-agency.com", email="hello@good-agency.com")
    assert is_supp_clean is False


def test_duplicate_registration(deduplicator):
    domain = "newagency.com"
    email = "contact@newagency.com"

    is_dup, _ = deduplicator.is_duplicate(domain, email)
    assert is_dup is False

    deduplicator.register(domain, email)

    is_dup_again, dup_reason = deduplicator.is_duplicate(domain, email)
    assert is_dup_again is True
    assert "already processed" in dup_reason
