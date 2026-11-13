"""
Email Verification Module
Implements the strict verification taxonomy:
1. Provider-Verified (authorized verification provider API or free-tier HTTPS API)
2. SMTP-Verified (direct RCPT TO 250 OK AND non-catch-all confirmed by 5xx on random probe)
3. Publicly Listed (Unverified) (MX resolved, but mailbox not verified due to port 25 block / deferral)
4. Catch-All / Risky (server accepts random non-existent mailboxes)
5. Verification Inconclusive (DNS timeout / transient DNS failure / API unknown result)
6. Invalid (syntax, disposable, placeholder/telemetry, NXDOMAIN/NO_MX, or 5xx/API rejection)
7. Unavailable (no email found)

Supports a zero-cost HTTPS verification waterfall across legitimate recurring free tiers
(QuickEmailVerification, Verifalia, Reoon Power Mode, ZeroBounce) plus optional Reacher,
with automatic quota-exhaustion failover and zero credit-card / subscription requirements.

Strict Rule: Never guarantee deliverability based on an email check and never
claim an email is verified when checks are inconclusive, catch-all, or port 25 is blocked.
"""

import datetime
import logging
import os
import re
import smtplib
import socket
import time
import zlib
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import dns.resolver
import requests

logger = logging.getLogger(__name__)

# Basic RFC 5322 compliant regex for standard email syntax
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
)

# Known disposable / temporary email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "sharklasers.com", "trashmail.com", "yopmail.com", "throwawaymail.com"
}

# Known placeholder / template addresses
PLACEHOLDER_EMAILS = {
    "name@email.com", "you@company.com", "user@example.com", "test@test.com",
    "info@example.com", "email@example.com", "yourname@domain.com", "name@domain.com",
    "first.last@company.com", "sample@email.com", "john.doe@example.com", "contact@example.com"
}

# Monitoring, telemetry, and error-reporting service domain patterns
MONITORING_DOMAIN_PATTERNS = [
    re.compile(r"sentry\.io$", re.I),
    re.compile(r"bugsnag\.com$", re.I),
    re.compile(r"datadog\.com$", re.I),
    re.compile(r"rollbar\.com$", re.I),
    re.compile(r"loggly\.com$", re.I),
    re.compile(r"w3\.org$", re.I),
]

NON_COMMERCIAL_PREFIXES = {
    "noreply", "no-reply", "donotreply", "do-not-reply",
    "privacy", "dpo", "gdpr", "abuse", "postmaster", "hostmaster", "webmaster",
    "careers", "jobs", "hr", "legal", "compliance", "press", "media", "mailer-daemon",
}

STRICTLY_VERIFIED_STATUSES = {"Provider-Verified", "SMTP-Verified"}

DEFAULT_WATERFALL_ORDER = [
    "quickemailverification",
    "verifalia",
    "reoon",
    "zerobounce",
    "self_hosted_reacher",
]

PROVIDER_ALIASES = {
    "qev": "quickemailverification",
    "quickemailverification": "quickemailverification",
    "verifalia": "verifalia",
    "reoon": "reoon",
    "zerobounce": "zerobounce",
    "zb": "zerobounce",
    "reacher": "self_hosted_reacher",
    "self_hosted_reacher": "self_hosted_reacher",
}


def _read_env_defaults(env_path: Optional[str] = None) -> Dict[str, str]:
    target = Path(env_path) if env_path else (Path(__file__).resolve().parent.parent.parent / ".env")
    values: Dict[str, str] = {}
    if not target.exists() or not target.is_file():
        return values
    try:
        for raw_line in target.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            if key.startswith("export "):
                key = key[7:].strip()
            val = val.strip()
            if len(val) >= 2 and ((val[0] == '"' and val[-1] == '"') or (val[0] == "'" and val[-1] == "'")):
                val = val[1:-1].strip()
            if key and val:
                values[key] = val
    except OSError:
        pass
    return values


class EmailVerifier:
    """
    Validates emails through syntax, DNS MX resolution, a multi-provider HTTPS
    free-tier verification waterfall, and guarded direct SMTP fallback.
    """

    def __init__(
        self,
        dns_timeout: float = 6.0,
        smtp_timeout: float = 3.5,
        provider_name: Optional[str] = None,
        provider_url: Optional[str] = None,
        provider_api_key: Optional[str] = None,
        load_env: bool = False,
        env_path: Optional[str] = None,
        waterfall_order: Optional[List[str]] = None,
        provider_configs: Optional[Dict[str, Dict[str, str]]] = None,
        on_provider_usage: Optional[Callable[[str, int, Optional[int], bool, str], None]] = None,
    ):
        self.dns_timeout = dns_timeout
        self.smtp_timeout = smtp_timeout
        self._env_values = _read_env_defaults(env_path) if load_env else {}
        self.on_provider_usage = on_provider_usage

        def _cfg(key: str, default: str = "") -> str:
            return (os.getenv(key) or self._env_values.get(key) or default).strip()

        raw_prov = (provider_name or (_cfg("EMAIL_VERIFIER_PROVIDER") if load_env else "")).strip().lower()
        self.provider_name = PROVIDER_ALIASES.get(raw_prov, raw_prov)
        self.provider_url = (provider_url or (_cfg("EMAIL_VERIFIER_API_URL") if load_env else "")).strip()
        self.provider_api_key = (provider_api_key or (_cfg("EMAIL_VERIFIER_API_KEY") if load_env else "")).strip()

        self.provider_configs: Dict[str, Dict[str, str]] = {}
        if provider_configs:
            for pname, pcfg in provider_configs.items():
                norm_p = PROVIDER_ALIASES.get(pname.strip().lower(), pname.strip().lower())
                self.provider_configs[norm_p] = dict(pcfg)
        elif load_env:
            qev_key = _cfg("QUICKEMAILVERIFICATION_API_KEY")
            if qev_key:
                self.provider_configs["quickemailverification"] = {"api_key": qev_key}

            verif_user = _cfg("VERIFALIA_USERNAME")
            verif_pass = _cfg("VERIFALIA_PASSWORD")
            if verif_user and verif_pass:
                self.provider_configs["verifalia"] = {"username": verif_user, "password": verif_pass}

            reoon_key = _cfg("REOON_API_KEY")
            if reoon_key:
                self.provider_configs["reoon"] = {"api_key": reoon_key}

            zb_key = _cfg("ZEROBOUNCE_API_KEY")
            if zb_key:
                self.provider_configs["zerobounce"] = {"api_key": zb_key}

            if self.provider_name == "self_hosted_reacher" and self.provider_url:
                self.provider_configs["self_hosted_reacher"] = {
                    "api_url": self.provider_url,
                    "api_key": self.provider_api_key,
                }
            elif self.provider_name in ("quickemailverification", "reoon", "zerobounce") and self.provider_name not in self.provider_configs and self.provider_api_key:
                self.provider_configs[self.provider_name] = {"api_key": self.provider_api_key}
        elif self.provider_name and (self.provider_api_key or self.provider_url):
            self.provider_configs[self.provider_name] = {
                "api_key": self.provider_api_key,
                "api_url": self.provider_url,
            }

        env_wf = _cfg("EMAIL_VERIFIER_WATERFALL") if load_env else ""
        if waterfall_order:
            raw_order = [PROVIDER_ALIASES.get(p.strip().lower(), p.strip().lower()) for p in waterfall_order if p.strip()]
        elif env_wf:
            raw_order = [PROVIDER_ALIASES.get(p.strip().lower(), p.strip().lower()) for p in env_wf.split(",") if p.strip()]
        else:
            raw_order = list(DEFAULT_WATERFALL_ORDER)

        if self.provider_name and self.provider_name in self.provider_configs:
            raw_order = [self.provider_name] + [p for p in raw_order if p != self.provider_name]
        self.waterfall_order: List[str] = raw_order

        self.exhausted_providers: Set[str] = set()
        self.provider_usage: Dict[str, Dict[str, Any]] = {}
        self.http_session = requests.Session()

        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = dns_timeout
        try:
            self.resolver.nameservers = ["8.8.8.8", "1.1.1.1", "8.8.4.4"]
        except Exception:
            pass

    @staticmethod
    def is_strictly_verified(status: Optional[str]) -> bool:
        return bool(status and status.strip() in STRICTLY_VERIFIED_STATUSES)

    @staticmethod
    def probe_smtp_port_25(host: str = "gmail-smtp-in.l.google.com", timeout: float = 3.0) -> Tuple[bool, str]:
        """Fast connectivity preflight check for outbound TCP port 25."""
        try:
            with socket.create_connection((host, 25), timeout=timeout) as sock:
                banner = sock.recv(256).decode("utf-8", errors="replace").strip()
            # If banner does not start with 220 or indicates DNSBL / temporary rejection, port 25 is unusable
            banner_lower = banner.lower()
            if not banner.startswith("220") or any(b in banner_lower for b in ("421", "550", "554", "dnsbl", "blocklist", "not available", "denied")):
                return False, f"SMTP Port 25 unusable / DNSBL blocked ({banner})"
            return True, banner or "SMTP Port 25 TCP connection established."
        except Exception as exc:
            return False, f"{type(exc).__name__}: {exc}"

    def get_configured_external_providers(self) -> List[str]:
        return [p for p in self.waterfall_order if p in self.provider_configs]

    def get_available_external_providers(self) -> List[str]:
        return [p for p in self.get_configured_external_providers() if p not in self.exhausted_providers]

    def has_configured_external_verifier(self) -> bool:
        return bool(self.get_configured_external_providers())

    def has_available_external_verifier(self) -> bool:
        return bool(self.get_available_external_providers())

    def refresh_external_provider_balances(self) -> Dict[str, Dict[str, Any]]:
        """
        Probes zero-credit balance endpoints where supported (e.g. Reoon) before research
        so depleted daily quotas are marked exhausted immediately.
        """
        summary: Dict[str, Dict[str, Any]] = {}
        if "reoon" in self.provider_configs and "reoon" not in self.exhausted_providers:
            api_key = self.provider_configs["reoon"].get("api_key", "")
            if api_key:
                try:
                    resp = self.http_session.get(
                        "https://emailverifier.reoon.com/api/v1/check-account-balance/",
                        params={"key": api_key},
                        timeout=8.0,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        daily = int(data.get("remaining_daily_credits") or 0)
                        instant = int(data.get("remaining_instant_credits") or 0)
                        total = daily + instant
                        is_exh = total <= 0
                        summary["reoon"] = {
                            "remaining_daily": daily,
                            "remaining_instant": instant,
                            "total_remaining": total,
                            "exhausted": is_exh,
                        }
                        if is_exh:
                            self._record_provider_event("reoon", 0, 0, True, "0 credits remaining on balance precheck.")
                except Exception as exc:
                    logger.debug(f"Reoon balance check notice: {exc}")
        return summary

    def verify(
        self,
        email: Optional[str],
        source_is_provider_verified: bool = False,
        source_url: str = "",
        allow_external_provider: bool = True,
        skip_smtp_probe: bool = False,
    ) -> Dict[str, Any]:
        """
        Runs the verification waterfall and returns standardized status and notes.
        """
        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # 1. Unavailable check
        if not email or not email.strip():
            return {
                "email": "",
                "verification_status": "Unavailable",
                "mx_found": False,
                "mx_hosts": [],
                "is_catch_all": None,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "",
                "verification_notes": "No email address discovered from public sources.",
                "source_url": source_url,
                "verified_at": timestamp,
            }

        cleaned_email = email.strip().lower()

        # 2. Syntax validation
        if not EMAIL_REGEX.match(cleaned_email):
            return {
                "email": cleaned_email,
                "verification_status": "Invalid",
                "mx_found": False,
                "mx_hosts": [],
                "is_catch_all": None,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "local_syntax",
                "verification_notes": "Failed RFC 5322 syntax validation.",
                "source_url": source_url,
                "verified_at": timestamp,
            }

        local_part, domain = cleaned_email.split("@", 1)

        # 3. Disposable domain check
        if domain in DISPOSABLE_DOMAINS:
            return {
                "email": cleaned_email,
                "verification_status": "Invalid",
                "mx_found": False,
                "mx_hosts": [],
                "is_catch_all": None,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "local_disposable_filter",
                "verification_notes": "Disposable/temporary email service detected.",
                "source_url": source_url,
                "verified_at": timestamp,
            }

        # 4. Form template placeholder or telemetry/error token check
        if (
            cleaned_email in PLACEHOLDER_EMAILS
            or any(p.search(domain) for p in MONITORING_DOMAIN_PATTERNS)
            or domain in ("example.com", "example.org", "example.net")
        ):
            return {
                "email": cleaned_email,
                "verification_status": "Invalid",
                "mx_found": False,
                "mx_hosts": [],
                "is_catch_all": None,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "local_placeholder_filter",
                "verification_notes": "Form template placeholder or third-party monitoring/telemetry address detected.",
                "source_url": source_url,
                "verified_at": timestamp,
            }

        # 5. If already confirmed via an authorized B2B Provider API
        if source_is_provider_verified:
            return {
                "email": cleaned_email,
                "verification_status": "Provider-Verified",
                "mx_found": True,
                "mx_hosts": [],
                "is_catch_all": False,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "pre_verified_source",
                "verification_notes": "Verified by licensed data provider API. Deliverability not guaranteed.",
                "source_url": source_url,
                "verified_at": timestamp,
            }

        # 6. DNS MX Record Resolution (100% free local check prior to any HTTPS API credit use)
        mx_hosts, dns_error = self._resolve_mx(domain)

        if dns_error in ("TIMEOUT", "DNS_ERROR"):
            return {
                "email": cleaned_email,
                "verification_status": "Verification Inconclusive",
                "mx_found": None,
                "mx_hosts": [],
                "is_catch_all": None,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "local_dns",
                "verification_notes": f"DNS resolution timed out or encountered network error ({dns_error}). Verification could not be definitively completed.",
                "source_url": source_url,
                "verified_at": timestamp,
            }
        elif dns_error in ("NXDOMAIN", "NO_MX") or not mx_hosts:
            return {
                "email": cleaned_email,
                "verification_status": "Invalid",
                "mx_found": False,
                "mx_hosts": [],
                "is_catch_all": None,
                "smtp_port_25_blocked": False,
                "deliverability_guaranteed": False,
                "verification_provider": "local_dns",
                "verification_notes": f"Definitive invalid domain: '{domain}' does not exist or has no active mail exchanger (MX) configured.",
                "source_url": source_url,
                "verified_at": timestamp,
            }

        # 7. HTTPS Provider Waterfall (if enabled & configured with non-exhausted providers)
        if allow_external_provider and self.has_available_external_verifier():
            ext_res = self._verify_via_configured_provider(
                cleaned_email=cleaned_email,
                local_part=local_part,
                mx_hosts=mx_hosts,
                source_url=source_url,
                timestamp=timestamp,
            )
            if ext_res is not None:
                return ext_res

        # If caller intentionally skipped external API OR preflight proved SMTP port 25 unavailable without HTTPS API
        if not allow_external_provider or skip_smtp_probe:
            note_msg = (
                "External API verification skipped because candidate failed pre-API DM/signal/market gate."
                if not allow_external_provider
                else "DNS MX records confirmed active; direct SMTP port 25 probe skipped (port 25 blocked on current network) and no external verification API configured. Accurately labeled Publicly Listed (Unverified)."
            )
            return {
                "email": cleaned_email,
                "verification_status": "Publicly Listed (Unverified)",
                "mx_found": True,
                "mx_hosts": mx_hosts[:3],
                "is_catch_all": None,
                "smtp_port_25_blocked": bool(skip_smtp_probe),
                "deliverability_guaranteed": False,
                "verification_provider": "local_dns_mx" if skip_smtp_probe else "skipped_prequalification",
                "verification_notes": note_msg,
                "source_url": source_url,
                "verified_at": timestamp,
            }

        # 8. Direct SMTP Mailbox Check & Catch-all Probe across up to top 2 MX hosts
        smtp_result = "UNVERIFIED"
        is_catch_all: Optional[bool] = None
        notes = ""
        port_25_blocked = False

        for mx_host in mx_hosts[:2]:
            smtp_result, is_catch_all, notes, port_25_blocked = self._probe_smtp(cleaned_email, domain, mx_host)
            if smtp_result in ("VALID_MAILBOX", "INVALID", "CATCH_ALL"):
                break

        if smtp_result == "INVALID":
            status = "Invalid"
        elif smtp_result == "CATCH_ALL" or is_catch_all is True:
            status = "Catch-All / Risky"
        elif smtp_result == "VALID_MAILBOX" and is_catch_all is False:
            status = "SMTP-Verified"
            notes += " (Non-catch-all mailbox handshake confirmed; deliverability still not guaranteed against upstream spam filters)."
        else:
            status = "Publicly Listed (Unverified)"

        return {
            "email": cleaned_email,
            "verification_status": status,
            "mx_found": True,
            "mx_hosts": mx_hosts[:3],
            "is_catch_all": is_catch_all,
            "smtp_port_25_blocked": port_25_blocked,
            "deliverability_guaranteed": False,
            "verification_provider": "direct_smtp",
            "verification_notes": notes,
            "source_url": source_url,
            "verified_at": timestamp,
        }

    def _record_provider_event(
        self,
        provider: str,
        used_delta: int,
        remaining: Optional[int],
        exhausted: bool,
        note: str,
    ) -> None:
        entry = self.provider_usage.setdefault(
            provider, {"requests_used": 0, "remaining_reported": None, "exhausted": False, "last_note": ""}
        )
        entry["requests_used"] += int(used_delta)
        if remaining is not None:
            entry["remaining_reported"] = int(remaining)
        if exhausted:
            entry["exhausted"] = True
            self.exhausted_providers.add(provider)
        if note:
            entry["last_note"] = note
        if self.on_provider_usage:
            try:
                self.on_provider_usage(provider, int(used_delta), remaining, exhausted, note)
            except Exception:
                pass

    def _verify_via_configured_provider(
        self,
        cleaned_email: str,
        local_part: str = "",
        mx_hosts: Optional[List[str]] = None,
        source_url: str = "",
        timestamp: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Executes configured HTTPS verification providers in priority waterfall order,
        failing over cleanly when a free daily quota is exhausted.
        """
        mx_list = (mx_hosts or [])[:3]
        local = local_part or cleaned_email.split("@")[0].lower()

        for prov in self.get_available_external_providers():
            cfg = self.provider_configs.get(prov, {})
            if prov == "quickemailverification":
                res = self._verify_quickemailverification(cleaned_email, local, cfg, mx_list, source_url, timestamp)
            elif prov == "verifalia":
                res = self._verify_verifalia(cleaned_email, local, cfg, mx_list, source_url, timestamp)
            elif prov == "reoon":
                res = self._verify_reoon(cleaned_email, local, cfg, mx_list, source_url, timestamp)
            elif prov == "zerobounce":
                res = self._verify_zerobounce(cleaned_email, local, cfg, mx_list, source_url, timestamp)
            elif prov == "self_hosted_reacher":
                res = self._verify_self_hosted_reacher(cleaned_email, cfg, mx_list, source_url, timestamp)
            else:
                res = None

            if res is not None:
                return res

        return None

    def _build_provider_result(
        self,
        cleaned_email: str,
        status: str,
        is_catch_all: Optional[bool],
        mx_hosts: List[str],
        provider: str,
        notes: str,
        source_url: str,
        timestamp: str,
    ) -> Dict[str, Any]:
        return {
            "email": cleaned_email,
            "verification_status": status,
            "mx_found": True,
            "mx_hosts": mx_hosts,
            "is_catch_all": is_catch_all,
            "smtp_port_25_blocked": False,
            "deliverability_guaranteed": False,
            "verification_provider": provider,
            "verification_notes": notes,
            "source_url": source_url,
            "verified_at": timestamp,
        }

    def _verify_quickemailverification(
        self,
        cleaned_email: str,
        local_part: str,
        cfg: Dict[str, str],
        mx_hosts: List[str],
        source_url: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        api_key = cfg.get("api_key", "")
        if not api_key:
            return None

        for attempt in range(2):
            try:
                resp = self.http_session.get(
                    "https://api.quickemailverification.com/v1/verify",
                    params={"email": cleaned_email, "apikey": api_key},
                    timeout=18.0,
                )
                rem_hdr = resp.headers.get("X-QEV-Remaining-Credits")
                remaining: Optional[int] = int(rem_hdr) if (rem_hdr is not None and str(rem_hdr).lstrip("-").isdigit()) else None

                if resp.status_code == 402:
                    self._record_provider_event("quickemailverification", 0, 0, True, "HTTP 402 daily free quota exhausted.")
                    return None
                if resp.status_code == 429:
                    if attempt == 0:
                        time.sleep(2.0)
                        continue
                    logger.warning("QuickEmailVerification rate-limited (HTTP 429); trying next provider.")
                    return None
                if resp.status_code in (401, 403):
                    self._record_provider_event("quickemailverification", 0, None, True, f"HTTP {resp.status_code} invalid/unauthorized API key.")
                    return None
                if resp.status_code != 200:
                    return None

                data = resp.json()
                result = str(data.get("result") or "").strip().lower()
                reason = str(data.get("reason") or "").strip().lower()
                accept_all = bool(data.get("accept_all"))
                disposable = bool(data.get("disposable"))

                if disposable or result == "invalid":
                    status = "Invalid"
                    is_catch_all = accept_all
                elif accept_all or reason == "accept_all":
                    status = "Catch-All / Risky"
                    is_catch_all = True
                elif result == "valid" and not accept_all and not disposable and local_part not in NON_COMMERCIAL_PREFIXES:
                    status = "Provider-Verified"
                    is_catch_all = False
                elif result == "unknown":
                    status = "Verification Inconclusive"
                    is_catch_all = None
                else:
                    status = "Publicly Listed (Unverified)"
                    is_catch_all = accept_all

                used = 0 if result == "unknown" else 1
                exhausted_after = remaining is not None and remaining <= 0
                self._record_provider_event(
                    "quickemailverification",
                    used,
                    remaining,
                    exhausted_after,
                    f"result={result}, reason={reason}, accept_all={accept_all}",
                )
                return self._build_provider_result(
                    cleaned_email=cleaned_email,
                    status=status,
                    is_catch_all=is_catch_all,
                    mx_hosts=mx_hosts,
                    provider="quickemailverification",
                    notes=f"QuickEmailVerification HTTPS check: result={result}, reason={reason}, accept_all={accept_all}.",
                    source_url=source_url,
                    timestamp=timestamp,
                )
            except Exception as exc:
                logger.debug(f"QuickEmailVerification API notice: {exc}")
                return None
        return None

    def _verify_verifalia(
        self,
        cleaned_email: str,
        local_part: str,
        cfg: Dict[str, str],
        mx_hosts: List[str],
        source_url: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        username = cfg.get("username", "")
        password = cfg.get("password", "")
        if not username or not password:
            return None

        try:
            resp = self.http_session.post(
                "https://api.verifalia.com/v2.6/email-validations",
                params={"waitTime": 30000},
                auth=(username, password),
                json={"entries": [{"inputData": cleaned_email, "quality": "Standard"}]},
                timeout=35.0,
            )
            if resp.status_code == 402:
                self._record_provider_event("verifalia", 0, 0, True, "HTTP 402 Verifalia daily free quota (25/day) exhausted.")
                return None
            if resp.status_code in (401, 403):
                self._record_provider_event("verifalia", 0, None, True, f"HTTP {resp.status_code} invalid Verifalia credentials.")
                return None

            data: Dict[str, Any] = resp.json() if resp.status_code in (200, 202) else {}
            if resp.status_code == 202:
                loc = resp.headers.get("Location") or ""
                job_id = (data.get("overview") or {}).get("id", "")
                poll_url = loc if loc.startswith("http") else (f"https://api.verifalia.com/v2.6/email-validations/{job_id}" if job_id else "")
                for _ in range(3):
                    if not poll_url:
                        break
                    time.sleep(2.0)
                    p_resp = self.http_session.get(poll_url, auth=(username, password), timeout=15.0)
                    if p_resp.status_code == 200:
                        data = p_resp.json()
                        if (data.get("overview") or {}).get("status") == "Completed":
                            break
            elif resp.status_code != 200:
                return None

            entries = (data.get("entries") or {}).get("data") or []
            if not entries:
                return None
            entry = entries[0]
            classification = str(entry.get("classification") or "").strip().lower()
            sub_status = str(entry.get("status") or "").strip()
            disposable = bool(entry.get("isDisposableEmailAddress"))
            is_catch_all_flag = "catchall" in sub_status.lower()

            if disposable or classification == "undeliverable":
                status = "Invalid"
                is_catch_all = is_catch_all_flag
            elif classification == "risky" or is_catch_all_flag:
                status = "Catch-All / Risky"
                is_catch_all = True
            elif classification == "deliverable" and not is_catch_all_flag and local_part not in NON_COMMERCIAL_PREFIXES:
                status = "Provider-Verified"
                is_catch_all = False
            elif classification == "unknown":
                status = "Verification Inconclusive"
                is_catch_all = None
            else:
                status = "Publicly Listed (Unverified)"
                is_catch_all = None

            self._record_provider_event("verifalia", 1, None, False, f"classification={classification}, status={sub_status}")
            return self._build_provider_result(
                cleaned_email=cleaned_email,
                status=status,
                is_catch_all=is_catch_all,
                mx_hosts=mx_hosts,
                provider="verifalia",
                notes=f"Verifalia Standard check: classification={classification}, status={sub_status}.",
                source_url=source_url,
                timestamp=timestamp,
            )
        except Exception as exc:
            logger.debug(f"Verifalia API notice: {exc}")
            return None

    def _verify_reoon(
        self,
        cleaned_email: str,
        local_part: str,
        cfg: Dict[str, str],
        mx_hosts: List[str],
        source_url: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        api_key = cfg.get("api_key", "")
        if not api_key:
            return None

        try:
            resp = self.http_session.get(
                "https://emailverifier.reoon.com/api/v1/verify",
                params={"email": cleaned_email, "key": api_key, "mode": "power"},
                timeout=65.0,
            )
            if resp.status_code in (402, 403):
                self._record_provider_event("reoon", 0, 0, True, f"HTTP {resp.status_code} Reoon quota/auth limit reached.")
                return None
            if resp.status_code == 429:
                logger.warning("Reoon API rate-limited (HTTP 429); trying next provider.")
                return None
            if resp.status_code != 200:
                return None

            data = resp.json()
            reoon_status = str(data.get("status") or "").strip().lower()
            if reoon_status == "error":
                msg = str(data.get("message") or data.get("detail") or data.get("reason") or "Reoon API error").lower()
                if any(k in msg for k in ("credit", "limit", "insufficient", "exhausted", "balance")):
                    self._record_provider_event("reoon", 0, 0, True, msg)
                return None

            is_catch_all = bool(data.get("is_catch_all"))
            is_deliverable = data.get("is_deliverable")
            is_disposable = bool(data.get("is_disposable"))
            is_disabled = bool(data.get("is_disabled"))
            is_spamtrap = bool(data.get("is_spamtrap"))

            if is_disposable or is_disabled or is_spamtrap or reoon_status in ("invalid", "disposable", "disabled", "spamtrap", "inbox_full") or is_deliverable is False:
                status = "Invalid"
            elif reoon_status == "catch_all" or is_catch_all:
                status = "Catch-All / Risky"
                is_catch_all = True
            elif (
                reoon_status in ("safe", "role_account")
                and is_deliverable is True
                and not is_catch_all
                and local_part not in NON_COMMERCIAL_PREFIXES
            ):
                status = "Provider-Verified"
            elif reoon_status == "unknown":
                status = "Verification Inconclusive"
                is_catch_all = None
            else:
                status = "Publicly Listed (Unverified)"

            used = 0 if reoon_status == "unknown" else 1
            self._record_provider_event("reoon", used, None, False, f"status={reoon_status}, catch_all={is_catch_all}")
            return self._build_provider_result(
                cleaned_email=cleaned_email,
                status=status,
                is_catch_all=is_catch_all,
                mx_hosts=mx_hosts,
                provider="reoon",
                notes=f"Reoon Power Mode check: status={reoon_status}, deliverable={is_deliverable}, catch_all={is_catch_all}.",
                source_url=source_url,
                timestamp=timestamp,
            )
        except Exception as exc:
            logger.debug(f"Reoon API notice: {exc}")
            return None

    def _verify_zerobounce(
        self,
        cleaned_email: str,
        local_part: str,
        cfg: Dict[str, str],
        mx_hosts: List[str],
        source_url: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        api_key = cfg.get("api_key", "")
        if not api_key:
            return None

        try:
            resp = self.http_session.get(
                "https://api.zerobounce.net/v2/validate",
                params={"api_key": api_key, "email": cleaned_email},
                timeout=20.0,
            )
            if resp.status_code in (402, 403):
                self._record_provider_event("zerobounce", 0, 0, True, f"HTTP {resp.status_code} ZeroBounce quota/auth exhausted.")
                return None
            if resp.status_code != 200:
                return None

            data = resp.json()
            if data.get("error"):
                err_l = str(data["error"]).lower()
                if any(k in err_l for k in ("credit", "out of", "insufficient", "limit")):
                    self._record_provider_event("zerobounce", 0, 0, True, err_l)
                return None

            zb_status = str(data.get("status") or "").strip().lower()
            sub_status = str(data.get("sub_status") or "").strip().lower()
            is_ca = bool(data.get("catchall_domain")) or zb_status == "catch-all"

            if zb_status in ("invalid", "spamtrap", "abuse", "do_not_mail"):
                status = "Invalid"
            elif is_ca:
                status = "Catch-All / Risky"
            elif zb_status == "valid" and local_part not in NON_COMMERCIAL_PREFIXES:
                status = "Provider-Verified"
                is_ca = False
            elif zb_status == "unknown":
                status = "Verification Inconclusive"
                is_ca = None
            else:
                status = "Publicly Listed (Unverified)"

            used = 0 if zb_status == "unknown" else 1
            self._record_provider_event("zerobounce", used, None, False, f"status={zb_status}, sub={sub_status}")
            return self._build_provider_result(
                cleaned_email=cleaned_email,
                status=status,
                is_catch_all=is_ca,
                mx_hosts=mx_hosts,
                provider="zerobounce",
                notes=f"ZeroBounce check: status={zb_status}, sub_status={sub_status}.",
                source_url=source_url,
                timestamp=timestamp,
            )
        except Exception as exc:
            logger.debug(f"ZeroBounce API notice: {exc}")
            return None

    def _verify_self_hosted_reacher(
        self,
        cleaned_email: str,
        cfg: Dict[str, str],
        mx_hosts: List[str],
        source_url: str,
        timestamp: str,
    ) -> Optional[Dict[str, Any]]:
        api_url = cfg.get("api_url") or self.provider_url
        if not api_url:
            return None

        headers = {"Content-Type": "application/json"}
        api_key = cfg.get("api_key") or self.provider_api_key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            resp = self.http_session.post(
                api_url,
                json={"to_email": cleaned_email},
                headers=headers,
                timeout=max(5.0, self.smtp_timeout * 2),
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            reachable = str(data.get("is_reachable", "")).lower()
            smtp_obj = data.get("smtp") or {}
            is_catch_all = smtp_obj.get("is_catch_all")
            is_deliverable = smtp_obj.get("is_deliverable")

            if reachable == "invalid" or is_deliverable is False:
                status = "Invalid"
            elif is_catch_all is True or reachable == "risky":
                status = "Catch-All / Risky"
            elif reachable == "safe" and is_deliverable is True and is_catch_all is False:
                status = "Provider-Verified"
            else:
                status = "Publicly Listed (Unverified)"

            self._record_provider_event("self_hosted_reacher", 1, None, False, f"is_reachable={reachable}")
            return self._build_provider_result(
                cleaned_email=cleaned_email,
                status=status,
                is_catch_all=is_catch_all,
                mx_hosts=mx_hosts,
                provider="self_hosted_reacher",
                notes=f"Checked via self_hosted_reacher: is_reachable={reachable}.",
                source_url=source_url,
                timestamp=timestamp,
            )
        except Exception as exc:
            logger.debug(f"Configured Reacher fallback triggered: {exc}")
            return None

    def _resolve_mx(self, domain: str) -> tuple[List[str], Optional[str]]:
        """
        Resolves MX records for a domain.
        Returns: (mx_hosts_list, error_type)
        """
        try:
            answers = self.resolver.resolve(domain, "MX")
            sorted_answers = sorted(answers, key=lambda r: r.preference)
            hosts = [str(r.exchange).rstrip(".") for r in sorted_answers if str(r.exchange).strip() != "."]
            if hosts:
                return hosts, None
            return [], "NO_MX"
        except dns.resolver.NXDOMAIN:
            return [], "NXDOMAIN"
        except dns.resolver.NoAnswer:
            return [], "NO_MX"
        except dns.resolver.Timeout:
            return [], "TIMEOUT"
        except Exception as e:
            logger.debug(f"MX resolution failed for {domain}: {e}")
            return [], "DNS_ERROR"

    def _probe_smtp(self, email: str, domain: str, mx_host: str) -> tuple[str, Optional[bool], str, bool]:
        """
        Attempts a non-intrusive SMTP handshake (EHLO/HELO, MAIL FROM, RCPT TO).
        Tests target mailbox first, then a random address on the domain ONLY if the
        target mailbox returned 250 OK, to confirm the domain is NOT catch-all.
        Returns: (smtp_result, is_catch_all, notes, port_25_blocked)
        """
        try:
            server = smtplib.SMTP(timeout=self.smtp_timeout)
            server.connect(mx_host, 25)
            code_ehlo, _ = server.ehlo("verify.ariyxresearch.com")
            if code_ehlo < 200 or code_ehlo >= 400:
                server.helo("verify.ariyxresearch.com")
            server.mail("probe@verify.ariyxresearch.com")

            # 1. Check candidate mailbox first
            code_candidate, _ = server.rcpt(email)
            if code_candidate in (550, 551, 552, 553, 554):
                try:
                    server.quit()
                except Exception:
                    pass
                return "INVALID", False, f"SMTP rejection ({code_candidate}): Mailbox does not exist.", False

            if not (200 <= code_candidate < 300):
                try:
                    server.quit()
                except Exception:
                    pass
                return "UNVERIFIED", None, f"SMTP returned deferred/non-250 code {code_candidate}.", False

            # 2. Target returned 250; verify NOT a catch-all domain using deterministic random local-part
            probe_token = f"{zlib.crc32(domain.encode('utf-8')) & 0xFFFFFFFF:08x}"
            random_probe = f"ariyx_nonexistent_{probe_token}@{domain}"
            code_random, _ = server.rcpt(random_probe)
            try:
                server.quit()
            except Exception:
                pass

            if 200 <= code_random < 300:
                return "CATCH_ALL", True, "Domain accepts all incoming mailboxes (Catch-All server detected).", False

            if 500 <= code_random < 600:
                return (
                    "VALID_MAILBOX",
                    False,
                    f"SMTP 250 OK on candidate mailbox and {code_random} rejection on nonexistent probe on {mx_host}.",
                    False,
                )

            return (
                "UNVERIFIED",
                None,
                f"Candidate accepted ({code_candidate}), but catch-all verification probe returned inconclusive code {code_random}.",
                False,
            )

        except (socket.timeout, TimeoutError, smtplib.SMTPConnectError, OSError) as e:
            return (
                "UNVERIFIED",
                None,
                f"Direct SMTP port 25 check unreachable/blocked ({type(e).__name__}). Classified based on DNS MX existence.",
                True,
            )
        except smtplib.SMTPServerDisconnected as e:
            return (
                "UNVERIFIED",
                None,
                f"Remote MX closed SMTP session during probe ({type(e).__name__}). Classified as Publicly Listed (Unverified).",
                False,
            )
        except Exception as e:
            return "UNVERIFIED", None, f"SMTP check incomplete: {type(e).__name__}: {e}", False
