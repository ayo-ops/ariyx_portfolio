"""
Unit tests for EmailVerifier and PhoneVerifier.
Tests the 5 email verification labels and E.164 phone normalization.
Verifies that deliverability is NEVER guaranteed based on SMTP.
"""

import pytest
from src.verification.email_verifier import EmailVerifier
from src.verification.phone_verifier import PhoneVerifier


@pytest.fixture
def email_verifier():
    return EmailVerifier()


@pytest.fixture
def phone_verifier():
    return PhoneVerifier()


def test_email_unavailable(email_verifier):
    res = email_verifier.verify(None)
    assert res["verification_status"] == "Unavailable"
    assert res["deliverability_guaranteed"] is False

    res_empty = email_verifier.verify("")
    assert res_empty["verification_status"] == "Unavailable"


def test_email_invalid_syntax(email_verifier):
    res = email_verifier.verify("not-an-email")
    assert res["verification_status"] == "Invalid"
    assert "syntax" in res["verification_notes"].lower()
    assert res["deliverability_guaranteed"] is False


def test_email_disposable_domain(email_verifier):
    res = email_verifier.verify("ceo@mailinator.com")
    assert res["verification_status"] == "Invalid"
    assert "disposable" in res["verification_notes"].lower()


def test_email_provider_verified(email_verifier):
    res = email_verifier.verify("founder@agency.com", source_is_provider_verified=True)
    assert res["verification_status"] == "Provider-Verified"
    assert res["deliverability_guaranteed"] is False  # Never guaranteed!


def test_placeholder_and_monitoring_emails_invalid(email_verifier):
    """Placeholder emails and telemetry endpoints must be classified as Invalid."""
    for ph in ["name@email.com", "you@company.com", "user@example.com", "token@o12345.ingest.sentry.io"]:
        res = email_verifier.verify(ph)
        assert res["verification_status"] == "Invalid"
        assert res["deliverability_guaranteed"] is False


def test_dns_timeout_classified_as_verification_inconclusive(email_verifier, monkeypatch):
    """DNS timeout must NOT be classified as Invalid. It must be Verification Inconclusive."""
    monkeypatch.setattr(email_verifier, "_resolve_mx", lambda dom: ([], "TIMEOUT"))
    res = email_verifier.verify("contact@examplefirm.com")
    assert res["verification_status"] == "Verification Inconclusive"
    assert "inconclusive" in res["verification_notes"].lower() or "timed out" in res["verification_notes"].lower()
    assert res["deliverability_guaranteed"] is False


def test_deliverability_is_never_guaranteed(email_verifier):
    """Deliverability must ALWAYS be False regardless of checks."""
    for email in ["test@gmail.com", "info@company.co.uk", "bad@invalid"]:
        res = email_verifier.verify(email)
        assert res["deliverability_guaranteed"] is False


def test_smtp_verified_non_catch_all(email_verifier, monkeypatch):
    """When SMTP returns 250 on target AND 550 on random probe, status becomes SMTP-Verified."""
    monkeypatch.setattr(email_verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))
    monkeypatch.setattr(
        email_verifier,
        "_probe_smtp",
        lambda email, dom, mx: ("VALID_MAILBOX", False, "SMTP 250 OK on candidate mailbox.", False),
    )
    res = email_verifier.verify("founder@agency.com")
    assert res["verification_status"] == "SMTP-Verified"
    assert EmailVerifier.is_strictly_verified(res["verification_status"]) is True
    assert res["is_catch_all"] is False
    assert res["deliverability_guaranteed"] is False


def test_smtp_catch_all_and_blocked_not_accepted(email_verifier, monkeypatch):
    """Catch-all and port-25-blocked checks must never be labeled verified."""
    monkeypatch.setattr(email_verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))

    monkeypatch.setattr(
        email_verifier,
        "_probe_smtp",
        lambda email, dom, mx: ("CATCH_ALL", True, "Catch-All server detected.", False),
    )
    res_ca = email_verifier.verify("info@catchall.com")
    assert res_ca["verification_status"] == "Catch-All / Risky"
    assert EmailVerifier.is_strictly_verified(res_ca["verification_status"]) is False

    monkeypatch.setattr(
        email_verifier,
        "_probe_smtp",
        lambda email, dom, mx: ("UNVERIFIED", None, "Direct SMTP port 25 check unreachable/blocked.", True),
    )
    res_blk = email_verifier.verify("info@blocked25.com")
    assert res_blk["verification_status"] == "Publicly Listed (Unverified)"
    assert res_blk["smtp_port_25_blocked"] is True
    assert EmailVerifier.is_strictly_verified(res_blk["verification_status"]) is False


def test_phone_normalization_us(phone_verifier):
    res = phone_verifier.verify("212-555-0199", default_country="US", source_url="https://agency.com/contact")
    assert res["is_valid"] is True
    assert res["formatted_phone"] == "+12125550199"
    assert res["status"] == "Public Business Phone"


def test_phone_normalization_uk(phone_verifier):
    res = phone_verifier.verify("020 7946 0912", default_country="UK", source_url="https://agency.co.uk/contact")
    assert res["is_valid"] is True
    assert res["formatted_phone"] == "+442079460912"
    assert res["status"] == "Public Business Phone"


def test_phone_unavailable(phone_verifier):
    res = phone_verifier.verify("")
    assert res["status"] == "Unavailable"
    assert res["formatted_phone"] == ""


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict, headers: dict = None):
        self.status_code = status_code
        self._payload = payload
        self.headers = headers or {}

    def json(self):
        return self._payload


def test_quickemailverification_outcomes(monkeypatch):
    verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["quickemailverification"],
        provider_configs={"quickemailverification": {"api_key": "qev-test-key"}},
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))

    # 1. Valid non-catch-all
    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, params=None, timeout=None: _FakeResponse(
            200,
            {"result": "valid", "reason": "accepted_email", "accept_all": False, "disposable": False},
            headers={"X-QEV-Remaining-Credits": "99"},
        ),
    )
    res_ok = verifier.verify("sarah@agency.com")
    assert res_ok["verification_status"] == "Provider-Verified"
    assert res_ok["verification_provider"] == "quickemailverification"
    assert res_ok["is_catch_all"] is False
    assert verifier.provider_usage["quickemailverification"]["remaining_reported"] == 99
    assert verifier.provider_usage["quickemailverification"]["requests_used"] == 1

    # 2. Catch-all must NEVER become Provider-Verified
    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, params=None, timeout=None: _FakeResponse(
            200,
            {"result": "valid", "reason": "accept_all", "accept_all": True, "disposable": False},
            headers={"X-QEV-Remaining-Credits": "98"},
        ),
    )
    res_ca = verifier.verify("sarah@catchall.com")
    assert res_ca["verification_status"] == "Catch-All / Risky"
    assert res_ca["is_catch_all"] is True
    assert verifier.provider_usage["quickemailverification"]["requests_used"] == 2

    # 3. Unknown is inconclusive and spends 0 local used count
    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, params=None, timeout=None: _FakeResponse(
            200,
            {"result": "unknown", "reason": "timeout", "accept_all": False, "disposable": False},
        ),
    )
    res_unk = verifier.verify("sarah@slow.com")
    assert res_unk["verification_status"] == "Verification Inconclusive"
    assert verifier.provider_usage["quickemailverification"]["requests_used"] == 2

    # 4. Non-commercial prefix must not pass as Provider-Verified
    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, params=None, timeout=None: _FakeResponse(
            200,
            {"result": "valid", "reason": "accepted_email", "accept_all": False, "disposable": False},
        ),
    )
    res_nr = verifier.verify("noreply@agency.com")
    assert res_nr["verification_status"] == "Publicly Listed (Unverified)"


def test_verifalia_sync_polling_and_catchall(monkeypatch):
    import src.verification.email_verifier as ev_mod

    monkeypatch.setattr(ev_mod.time, "sleep", lambda s: None)
    verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["verifalia"],
        provider_configs={"verifalia": {"username": "u", "password": "p"}},
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))

    # 1. Synchronous 200 Deliverable
    monkeypatch.setattr(
        verifier.http_session,
        "post",
        lambda url, params=None, auth=None, json=None, timeout=None: _FakeResponse(
            200,
            {
                "overview": {"status": "Completed"},
                "entries": {"data": [{"classification": "Deliverable", "status": "Success", "isDisposableEmailAddress": False}]},
            },
        ),
    )
    res_ok = verifier.verify("founder@agency.com")
    assert res_ok["verification_status"] == "Provider-Verified"
    assert res_ok["verification_provider"] == "verifalia"

    # 2. HTTP 202 polling returning Catch-All (Risky)
    monkeypatch.setattr(
        verifier.http_session,
        "post",
        lambda url, params=None, auth=None, json=None, timeout=None: _FakeResponse(
            202,
            {"overview": {"id": "job-123", "status": "InProgress"}},
            headers={"Location": "https://api.verifalia.com/v2.6/email-validations/job-123"},
        ),
    )
    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, auth=None, timeout=None: _FakeResponse(
            200,
            {
                "overview": {"id": "job-123", "status": "Completed"},
                "entries": {"data": [{"classification": "Risky", "status": "ServerIsCatchAll", "isDisposableEmailAddress": False}]},
            },
        ),
    )
    res_ca = verifier.verify("info@catchall.co.uk")
    assert res_ca["verification_status"] == "Catch-All / Risky"
    assert res_ca["is_catch_all"] is True


def test_reoon_power_mode_role_account_and_balance(monkeypatch):
    verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["reoon"],
        provider_configs={"reoon": {"api_key": "reoon-key"}},
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))

    captured_params = []

    def fake_get(url, params=None, timeout=None):
        if "check-account-balance" in url:
            return _FakeResponse(200, {"remaining_daily_credits": 0, "remaining_instant_credits": 0})
        captured_params.append(dict(params or {}))
        email = params["email"]
        if email.startswith("hello@"):
            return _FakeResponse(
                200,
                {"status": "role_account", "is_deliverable": True, "is_catch_all": False, "is_disposable": False},
            )
        if email.startswith("noreply@"):
            return _FakeResponse(
                200,
                {"status": "role_account", "is_deliverable": True, "is_catch_all": False, "is_disposable": False},
            )
        return _FakeResponse(
            200,
            {"status": "safe", "is_deliverable": True, "is_catch_all": False, "is_disposable": False},
        )

    monkeypatch.setattr(verifier.http_session, "get", fake_get)

    res_dm = verifier.verify("sarah@agency.com")
    assert res_dm["verification_status"] == "Provider-Verified"
    assert captured_params[-1]["mode"] == "power"

    res_role_ok = verifier.verify("hello@agency.com")
    assert res_role_ok["verification_status"] == "Provider-Verified"

    res_noreply = verifier.verify("noreply@agency.com")
    assert res_noreply["verification_status"] == "Publicly Listed (Unverified)"

    bal = verifier.refresh_external_provider_balances()
    assert bal["reoon"]["exhausted"] is True
    assert "reoon" in verifier.exhausted_providers


def test_zerobounce_outcomes(monkeypatch):
    verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["zerobounce"],
        provider_configs={"zerobounce": {"api_key": "zb-key"}},
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))

    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, params=None, timeout=None: _FakeResponse(200, {"status": "valid", "sub_status": "", "catchall_domain": False}),
    )
    assert verifier.verify("sarah@agency.com")["verification_status"] == "Provider-Verified"

    monkeypatch.setattr(
        verifier.http_session,
        "get",
        lambda url, params=None, timeout=None: _FakeResponse(200, {"status": "catch-all", "sub_status": "accept_all", "catchall_domain": True}),
    )
    assert verifier.verify("sarah@ca.com")["verification_status"] == "Catch-All / Risky"


def test_multi_provider_waterfall_failover_and_honest_exhaustion(monkeypatch):
    verifier = EmailVerifier(
        load_env=False,
        waterfall_order=["quickemailverification", "verifalia", "reoon"],
        provider_configs={
            "quickemailverification": {"api_key": "qev-key"},
            "verifalia": {"username": "v-user", "password": "v-pass"},
            "reoon": {"api_key": "reoon-key"},
        },
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: (["mx1.agency.com"], None))
    monkeypatch.setattr(
        verifier,
        "_probe_smtp",
        lambda email, dom, mx: ("UNVERIFIED", None, "Direct SMTP port 25 blocked.", True),
    )

    reoon_calls = {"count": 0}

    def fake_get(url, params=None, timeout=None):
        if "quickemailverification.com" in url:
            return _FakeResponse(402, {"message": "Insufficient credits"})
        if "reoon.com" in url:
            reoon_calls["count"] += 1
            if reoon_calls["count"] == 1:
                return _FakeResponse(200, {"status": "safe", "is_deliverable": True, "is_catch_all": False})
            return _FakeResponse(200, {"status": "error", "message": "Insufficient daily credits"})
        raise AssertionError(f"Unexpected GET URL: {url}")

    def fake_post(url, params=None, auth=None, json=None, timeout=None):
        if "verifalia.com" in url:
            return _FakeResponse(402, {"title": "Payment Required"})
        raise AssertionError(f"Unexpected POST URL: {url}")

    monkeypatch.setattr(verifier.http_session, "get", fake_get)
    monkeypatch.setattr(verifier.http_session, "post", fake_post)

    # Call 1: QEV 402 -> Verifalia 402 -> Reoon succeeds seamlessly
    res1 = verifier.verify("founder@agency.com")
    assert res1["verification_status"] == "Provider-Verified"
    assert res1["verification_provider"] == "reoon"
    assert {"quickemailverification", "verifalia"}.issubset(verifier.exhausted_providers)
    assert verifier.has_available_external_verifier() is True

    # Call 2: Reoon reports insufficient credits -> falls back to direct SMTP (blocked) -> NEVER marks verified
    res2 = verifier.verify("ceo@otheragency.com")
    assert res2["verification_status"] == "Publicly Listed (Unverified)"
    assert res2["smtp_port_25_blocked"] is True
    assert EmailVerifier.is_strictly_verified(res2["verification_status"]) is False
    assert verifier.has_available_external_verifier() is False


def test_env_loading_for_free_https_providers(monkeypatch, tmp_path):
    for key in (
        "EMAIL_VERIFIER_PROVIDER",
        "EMAIL_VERIFIER_API_URL",
        "EMAIL_VERIFIER_API_KEY",
        "EMAIL_VERIFIER_WATERFALL",
        "QUICKEMAILVERIFICATION_API_KEY",
        "VERIFALIA_USERNAME",
        "VERIFALIA_PASSWORD",
        "REOON_API_KEY",
        "ZEROBOUNCE_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "EMAIL_VERIFIER_WATERFALL=verifalia,quickemailverification,reoon\n"
        "QUICKEMAILVERIFICATION_API_KEY=qev-123\n"
        "VERIFALIA_USERNAME=ver-u\n"
        "VERIFALIA_PASSWORD=ver-p\n"
        "REOON_API_KEY=reoon-789\n",
        encoding="utf-8",
    )

    verifier = EmailVerifier(load_env=True, env_path=str(env_file))
    assert verifier.get_configured_external_providers() == ["verifalia", "quickemailverification", "reoon"]
    assert verifier.provider_configs["verifalia"]["username"] == "ver-u"
    assert verifier.provider_configs["reoon"]["api_key"] == "reoon-789"

    # Generic EMAIL_VERIFIER_PROVIDER fallback also supported
    env_generic = tmp_path / ".env_generic"
    env_generic.write_text("EMAIL_VERIFIER_PROVIDER=reoon\nEMAIL_VERIFIER_API_KEY=gen-reoon\n", encoding="utf-8")
    v_gen = EmailVerifier(load_env=True, env_path=str(env_generic))
    assert v_gen.get_configured_external_providers() == ["reoon"]
    assert v_gen.provider_configs["reoon"]["api_key"] == "gen-reoon"


def test_skip_smtp_probe_validates_dns_mx_without_hanging(monkeypatch):
    verifier = EmailVerifier(load_env=False)
    monkeypatch.setattr(
        verifier,
        "_probe_smtp",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("SMTP probe must be skipped when skip_smtp_probe=True")),
    )
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: (["aspmx.l.google.com"], None))
    res = verifier.verify("founder@agency.com", skip_smtp_probe=True)
    assert res["verification_status"] == "Publicly Listed (Unverified)"
    assert res["mx_found"] is True
    assert res["mx_hosts"] == ["aspmx.l.google.com"]
    assert res["smtp_port_25_blocked"] is True
    assert res["deliverability_guaranteed"] is False

    # Missing MX domain still gets marked Invalid even when skip_smtp_probe=True
    monkeypatch.setattr(verifier, "_resolve_mx", lambda dom: ([], "NXDOMAIN"))
    res_bad = verifier.verify("founder@nonexistent-agency.invalid", skip_smtp_probe=True)
    assert res_bad["verification_status"] == "Invalid"
