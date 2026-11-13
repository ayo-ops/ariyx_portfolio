"""
Strict Daily Acceptance Evaluator for Ariyx Lead Intelligence System.

Enforces all 9 mandatory criteria before a prospect may count towards the
30/day target or enter the main outreach Google Sheet ('Outbound Leads Intelligence'):

1. Real, active B2B business in approved target markets (SMB scale by default; enterprise backlog kept separate).
2. Relevant industry that can realistically benefit from Ariyx CRM / automation / lead management / AI.
3. Relevant decision-maker identified with name, position, source URL, and evidence.
4. Credible evidence of a potential business need Ariyx can solve (>= 12 signal pts with evidence & source URL).
5. Business website and identity checked (HTTP research COMPLETED, non-blocked, valid description).
6. Business email passed validation (SMTP-Verified or Provider-Verified, OR MX-checked
   Publicly Listed (Unverified) when allow_unverified_public_emails=True;
   NEVER Invalid, Unavailable, Verification Inconclusive, or Catch-All / Risky).
7. Not already in local database/history, main Google Sheet, or suppression list.
8. Compliance status independently evaluated and not RESTRICTED, OPT_OUT_RECORDED, or ELIGIBILITY_NOT_ESTABLISHED.
9. Never fabricates data or lowers thresholds; returns transparent blocking codes on rejection.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from src.compliance.compliance_checker import ComplianceChecker
from src.scoring.lead_scorer import (
    BOT_BLOCK_PAGE_MARKERS,
    DISPOSABLE_OR_PLACEHOLDER_DOMAINS,
    EXCLUDED_PLATFORM_DOMAINS,
    NON_B2B_ENTITY_TYPES,
    TARGET_INDUSTRIES,
    TIER_ENTERPRISE,
    TIER_EXCLUDED,
    TIER_LOW_PRIORITY,
    TIER_NEEDS_RESEARCH,
    LeadScorer,
)
from src.verification.email_verifier import STRICTLY_VERIFIED_STATUSES

APPROVED_INDUSTRY_KEYWORDS = (
    "marketing",
    "digital agency",
    "seo",
    "advertising",
    "ppc",
    "branding",
    "creative agency",
    "web design",
    "pr agency",
    "public relations",
    "consulting",
    "consultancy",
    "advisory",
    "coaching",
    "financial advisor",
    "accounting",
    "recruitment",
    "staffing",
    "b2b services",
)

NON_COMMERCIAL_EMAIL_PREFIXES = {
    "noreply",
    "no-reply",
    "donotreply",
    "do-not-reply",
    "privacy",
    "dpo",
    "gdpr",
    "abuse",
    "postmaster",
    "hostmaster",
    "webmaster",
    "careers",
    "jobs",
    "hr",
    "legal",
    "compliance",
    "press",
    "media",
    "mailer-daemon",
}

COUNTRY_ALIASES = {
    "US": "US",
    "USA": "US",
    "UNITED STATES": "US",
    "AMERICA": "US",
    "UK": "UK",
    "GB": "UK",
    "UNITED KINGDOM": "UK",
    "ENGLAND": "UK",
    "SCOTLAND": "UK",
    "WALES": "UK",
    "CA": "CA",
    "CANADA": "CA",
    "AU": "AU",
    "AUSTRALIA": "AU",
}

BAD_NAME_TOKENS = {
    "unavailable",
    "unknown",
    "none",
    "admin",
    "team",
    "our team",
    "leadership",
    "about us",
    "contact us",
    "digital marketing",
    "marketing agency",
    "management consulting",
}

NON_PERSON_NAME_WORDS = {
    "view", "bio", "bios", "message", "founder", "founders", "owner", "owners", "ceo", "coo", "cto",
    "cfo", "director", "directors", "partner", "partners", "partnership", "president", "principal",
    "executive", "leadership", "team", "our", "your", "the", "from", "for", "with", "and", "talk",
    "speak", "meet", "ask", "call", "contact", "about", "read", "more", "learn", "get", "touch",
    "program", "programmes", "advertising", "marketing", "digital", "agency",
    "ecommerce", "e-commerce", "hearing", "aid", "business", "businesses", "company", "services",
    "solutions", "media", "consulting", "consultancy", "group", "ltd", "llc", "inc", "corp",
    "microsoft", "google", "meta", "shopify", "hubspot", "wordpress", "certified", "award",
    "winner", "winning", "case", "study", "studies", "client", "clients", "customer", "customers",
    "stories", "story", "news", "insights", "blog", "inspired", "card", "right", "what", "how",
    "why", "who", "we", "are", "best", "top", "uk", "usa", "london", "manchester", "birmingham",
    "bristol", "edinburgh", "brighton", "leeds",
}


@dataclass
class AcceptanceDecision:
    accepted: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    blocker_codes: List[str] = field(default_factory=list)
    blocking_reasons: List[str] = field(default_factory=list)
    outreach_segment: str = "UNASSIGNED"
    primary_blocker: str = ""


def normalize_market_country(country: Optional[str]) -> str:
    raw = (country or "").strip().upper()
    return COUNTRY_ALIASES.get(raw, raw)


def assign_outreach_segment(lead: Dict[str, Any]) -> str:
    """
    Deterministically classifies an accepted prospect into an email campaign segment
    using observed industry, buying signals, and decision-maker tier.
    """
    industry = str(lead.get("industry") or "").strip().lower()
    is_agency = any(
        k in industry
        for k in ("marketing", "seo", "advertising", "branding", "digital", "creative", "pr ", "public relations")
    )
    is_consulting = any(
        k in industry for k in ("consulting", "consultancy", "advisory", "coach", "accounting", "financial")
    )

    signals = lead.get("potential_buying_signals") or []
    signal_types = {
        str(s.get("signal_type") or "").upper()
        for s in signals
        if isinstance(s, dict)
    }

    if is_agency:
        if "STATIC_FORM_NO_CALENDAR" in signal_types or "MANUAL_FOLLOWUP_FRICTION" in signal_types:
            return "AGENCY_SPEED_TO_LEAD"
        if "DISCONNECTED_FORM_STACK" in signal_types or "NO_CONVERSATIONAL_WIDGET" in signal_types:
            return "AGENCY_CONVERSATIONAL_AI"
        return "AGENCY_GENERAL_AUTOMATION"

    if is_consulting:
        if "STATIC_FORM_NO_CALENDAR" in signal_types or "MANUAL_FOLLOWUP_FRICTION" in signal_types:
            return "CONSULTING_PIPELINE_AUTOMATION"
        return "CONSULTING_EXECUTIVE_OUTBOUND"

    return "B2B_SERVICE_FOUNDER_DIRECT"


class AcceptanceEvaluator:
    """
    Enforces strict daily acceptance rules (all 9 criteria must pass simultaneously).
    """

    def __init__(
        self,
        approved_markets: Optional[Set[str]] = None,
        min_signal_score: int = 12,
        exclude_enterprise: bool = True,
        allow_tier_3: bool = False,
        allow_unverified_public_emails: bool = True,
    ):
        self.approved_markets = {normalize_market_country(c) for c in (approved_markets or {"US", "UK", "CA", "AU"})}
        self.min_signal_score = int(min_signal_score)
        self.exclude_enterprise = exclude_enterprise
        self.allow_tier_3 = allow_tier_3
        self.allow_unverified_public_emails = allow_unverified_public_emails

    def evaluate(
        self,
        lead: Dict[str, Any],
        known_domains: Optional[Set[str]] = None,
        known_emails: Optional[Set[str]] = None,
        known_lead_ids: Optional[Set[str]] = None,
    ) -> AcceptanceDecision:
        checks: Dict[str, bool] = {}
        blocker_codes: List[str] = []
        blocking_reasons: List[str] = []

        lead_id = str(lead.get("lead_id") or lead.get("Lead ID") or "").strip()
        domain = LeadScorer._extract_clean_domain(
            lead.get("domain") or lead.get("website") or lead.get("Website URL") or ""
        )
        country_raw = str(lead.get("country") or "").strip()
        market = normalize_market_country(country_raw)
        industry = str(lead.get("industry") or lead.get("Industry & Sub-niche") or "").strip()
        research_status = str(lead.get("research_status") or "").strip()
        page_title = str(lead.get("page_title") or "").strip()
        business_name = str(lead.get("business_name") or lead.get("Business Name") or "").strip()
        description = str(lead.get("business_description") or lead.get("Business Description") or "").strip()

        dm_name = str(lead.get("decision_maker_name") or lead.get("Decision-Maker Full Name") or "").strip()
        dm_title = str(lead.get("decision_maker_title") or lead.get("Job Title") or "").strip()
        dm_tier = str(lead.get("decision_maker_tier") or lead.get("dm_tier") or "tier_4").strip().lower()
        dm_source_url = str(lead.get("decision_maker_source_url") or "").strip()
        dm_evidence = str(lead.get("decision_maker_evidence") or "").strip()

        email = str(lead.get("verified_email") or lead.get("Public Business Email") or lead.get("email") or "").strip().lower()
        email_status = str(lead.get("email_verification_status") or lead.get("Email Verification Status") or "Unavailable").strip()

        signal_score = int(lead.get("signal_score") or 0)
        signals = lead.get("potential_buying_signals") or []
        fit_hypothesis = str(lead.get("fit_hypothesis") or lead.get("Ariyx Fit Hypothesis") or "").strip()

        emp_raw = lead.get("estimated_employees") or lead.get("employee_count")
        emp_count = LeadScorer._parse_employee_count(emp_raw)
        qual_tier = str(lead.get("qualification_tier") or lead.get("Qualification Tier") or "").strip()
        comp_status = str(lead.get("compliance_status") or lead.get("Compliance Status") or "").strip().upper()

        # 1. Website & Identity Checked
        site_checked_ok = (
            research_status.upper().startswith("COMPLETED")
            and bool(domain)
            and LeadScorer._is_valid_hostname(domain)
            and not LeadScorer._domain_matches_set(domain, EXCLUDED_PLATFORM_DOMAINS)
            and not LeadScorer._domain_matches_set(domain, DISPOSABLE_OR_PLACEHOLDER_DOMAINS)
            and bool(business_name)
            and business_name.lower() != "unavailable"
            and bool(description)
            and description != "Public description unavailable."
            and not any(m in page_title.lower() for m in BOT_BLOCK_PAGE_MARKERS)
        )
        checks["website_identity_checked"] = site_checked_ok
        if not site_checked_ok:
            blocker_codes.append("WEBSITE_UNCHECKED_OR_INVALID")
            blocking_reasons.append(f"Website/identity incomplete or blocked ({research_status or 'missing audit'}).")

        # 2. Active B2B Business in Approved Target Market & SMB Scope
        entity_type = str(lead.get("entity_type") or "").strip().lower()
        is_directory = any(
            kw in (description.lower() + " " + page_title.lower())
            for kw in ("directory of", "comprehensive directory", "find the best uk digital marketing agencies", "list of marketing agencies", "compare agencies", "find top-rated")
        )
        is_b2b = (lead.get("is_b2b") is not False) and (entity_type not in NON_B2B_ENTITY_TYPES) and not is_directory
        in_market = bool(market and market in self.approved_markets)
        is_enterprise = (qual_tier == TIER_ENTERPRISE) or bool(emp_count and emp_count > 250)
        smb_ok = not (self.exclude_enterprise and is_enterprise)

        market_b2b_ok = is_b2b and in_market and smb_ok
        checks["active_b2b_target_market"] = market_b2b_ok
        if is_directory:
            blocker_codes.append("AGGREGATOR_DIRECTORY_EXCLUDED")
            blocking_reasons.append("Entity appears to be a directory / aggregator listing other agencies rather than an eligible service provider.")
        elif not is_b2b:
            blocker_codes.append("NON_B2B_ENTITY")
            blocking_reasons.append("Entity does not appear to be an eligible B2B business.")
        if not in_market:
            blocker_codes.append("OUT_OF_TARGET_MARKET")
            blocking_reasons.append(f"Country '{country_raw or 'Unknown'}' is outside approved target markets ({sorted(self.approved_markets)}).")
        if self.exclude_enterprise and is_enterprise:
            blocker_codes.append("ENTERPRISE_BACKLOG_EXCLUDED")
            blocking_reasons.append("Enterprise account (>250 staff) belongs to separate backlog, not daily SMB outreach sheet.")

        # 3. Industry Fit
        ind_lower = industry.lower()
        industry_ok = bool(ind_lower) and (
            any(tgt in ind_lower for tgt in TARGET_INDUSTRIES)
            or any(kw in ind_lower for kw in APPROVED_INDUSTRY_KEYWORDS)
        )
        checks["industry_fit"] = industry_ok
        if not industry_ok:
            blocker_codes.append("INDUSTRY_OUT_OF_SCOPE")
            blocking_reasons.append(f"Industry '{industry or 'Unspecified'}' lacks clear Ariyx CRM/automation fit.")

        # 4. Relevant Decision-Maker Identified With Evidence
        dm_name_clean = re.sub(r"\s+", " ", dm_name).strip()
        dm_tokens = [t for t in re.split(r"\s+", dm_name_clean) if t]
        has_bad_token = any(re.sub(r"[^a-z]", "", t.lower()) in NON_PERSON_NAME_WORDS for t in dm_tokens)
        has_bad_symbol = any(ch in "@/:;|()[]{}>—–•\"'“”!?*#+=\\<>" for ch in dm_name_clean)
        dm_name_valid = (
            bool(dm_name_clean)
            and dm_name_clean.lower() not in BAD_NAME_TOKENS
            and len(dm_tokens) >= 2
            and not any(ch.isdigit() for ch in dm_name_clean)
            and not has_bad_token
            and not has_bad_symbol
        )
        dm_title_valid = bool(dm_title) and dm_title.lower() not in ("unavailable", "unknown", "none")
        dm_tier_valid = dm_tier in ("tier_1", "tier_2", "tier_3")
        dm_evidence_valid = dm_source_url.lower().startswith("http") and bool(dm_evidence) and dm_evidence.lower() != "unavailable"

        dm_ok = dm_name_valid and dm_title_valid and dm_tier_valid and dm_evidence_valid
        checks["decision_maker_verified"] = dm_ok
        if not dm_ok:
            blocker_codes.append("MISSING_VERIFIED_DECISION_MAKER")
            blocking_reasons.append(
                f"Decision-maker evidence incomplete (name='{dm_name or 'Unavailable'}', title='{dm_title or 'Unavailable'}', tier='{dm_tier}')."
            )

        # 5. Credible Evidence of Solvable Business Need
        evidenced_signals = [
            s for s in signals
            if isinstance(s, dict)
            and str(s.get("evidence") or "").strip()
            and str(s.get("source_url") or "").strip().lower().startswith("http")
        ]
        problem_ok = (
            signal_score >= self.min_signal_score
            and len(evidenced_signals) >= 1
            and bool(fit_hypothesis)
            and fit_hypothesis != "Unavailable"
            and "Insufficient public website data" not in fit_hypothesis
        )
        checks["problem_evidence_present"] = problem_ok
        if not problem_ok:
            blocker_codes.append("INSUFFICIENT_PROBLEM_EVIDENCE")
            blocking_reasons.append(
                f"Credible buying-signal evidence missing or below {self.min_signal_score} pts (signal_score={signal_score}, evidenced={len(evidenced_signals)})."
            )

        # 6. Email Status Check (Strict Zero-Guessing Rule)
        local_part = email.split("@")[0] if "@" in email else ""
        is_consumer = ComplianceChecker.is_consumer_email(email) if email else True
        is_non_commercial_alias = local_part in NON_COMMERCIAL_EMAIL_PREFIXES
        allowed_statuses = (
            STRICTLY_VERIFIED_STATUSES | {"Publicly Listed (Unverified)"}
            if self.allow_unverified_public_emails
            else STRICTLY_VERIFIED_STATUSES
        )
        status_allowed = email_status in allowed_statuses

        email_ok = (
            bool(email)
            and email != "unavailable"
            and "@" in email
            and not is_consumer
            and not is_non_commercial_alias
            and status_allowed
        )
        checks["email_verified_strict"] = email_ok
        if not email_ok:
            if not email or email == "unavailable":
                blocker_codes.append("EMAIL_UNAVAILABLE")
                blocking_reasons.append("No public corporate email discovered.")
            elif is_consumer:
                blocker_codes.append("CONSUMER_WEBMAIL_REJECTED")
                blocking_reasons.append(f"Consumer webmail address '{email}' cannot enter B2B outbound pipeline.")
            elif is_non_commercial_alias:
                blocker_codes.append("NON_COMMERCIAL_EMAIL_ALIAS")
                blocking_reasons.append(f"Non-commercial alias '{email}' is unsuitable for B2B outreach.")
            else:
                expected_msg = (
                    "SMTP-Verified, Provider-Verified, or MX-checked Publicly Listed (Unverified)"
                    if self.allow_unverified_public_emails
                    else "SMTP-Verified or Provider-Verified"
                )
                blocker_codes.append(f"EMAIL_NOT_VERIFIED:{email_status.upper().replace(' ', '_')}")
                blocking_reasons.append(
                    f"Email '{email}' failed verification gate (status='{email_status}'; requires {expected_msg})."
                )

        # 7. Not Already in Database / Sheet / Suppression
        dup_flag = bool(lead.get("is_duplicate"))
        supp_flag = bool(lead.get("is_suppressed")) or comp_status == "OPT_OUT_RECORDED"
        in_known_domains = bool(known_domains and domain and domain in known_domains)
        in_known_emails = bool(known_emails and email and email in known_emails)
        in_known_ids = bool(known_lead_ids and lead_id and lead_id in known_lead_ids)

        not_dup_supp = not (dup_flag or supp_flag or in_known_domains or in_known_emails or in_known_ids)
        checks["not_duplicate_or_suppressed"] = not_dup_supp
        if supp_flag:
            blocker_codes.append("SUPPRESSED_OR_OPT_OUT")
            blocking_reasons.append("Domain or contact is suppressed / opted out.")
        elif dup_flag or in_known_domains or in_known_emails or in_known_ids:
            blocker_codes.append("DUPLICATE_EXISTING_RECORD")
            blocking_reasons.append(f"Prospect already exists in local history or Google Sheets ({domain}).")

        # 8. Compliance Reviewed & Not Prohibited/Restricted
        compliance_ok = comp_status == "REVIEW_REQUIRED"
        checks["compliance_reviewed"] = compliance_ok
        if not compliance_ok:
            blocker_codes.append(f"COMPLIANCE_BLOCKED:{comp_status or 'MISSING'}")
            blocking_reasons.append(
                f"Compliance status '{comp_status or 'MISSING'}' cannot enter daily outreach queue (requires REVIEW_REQUIRED manual-review status)."
            )

        # 9. Sales Tier Integrity (Never admit Excluded / Needs Further Research / Enterprise / Low-Priority)
        disallowed_tiers = {TIER_EXCLUDED, TIER_NEEDS_RESEARCH, TIER_ENTERPRISE, TIER_LOW_PRIORITY}
        if not self.allow_tier_3:
            # With all above passing, typical minimum score is 59+, but explicitly guard Low-Priority/Excluded/Incomplete
            pass
        tier_ok = bool(qual_tier) and qual_tier not in disallowed_tiers
        checks["qualification_tier_eligible"] = tier_ok
        if not tier_ok:
            blocker_codes.append("INELIGIBLE_QUALIFICATION_TIER")
            blocking_reasons.append(f"Qualification tier '{qual_tier or 'None'}' is not eligible for main outreach list.")

        accepted = all(checks.values())
        segment = assign_outreach_segment(lead) if accepted else "UNASSIGNED"
        primary_blocker = blocker_codes[0] if blocker_codes else ""

        return AcceptanceDecision(
            accepted=accepted,
            checks=checks,
            blocker_codes=blocker_codes,
            blocking_reasons=blocking_reasons,
            outreach_segment=segment,
            primary_blocker=primary_blocker,
        )

    def evaluate_pre_email(
        self,
        lead_partial: Dict[str, Any],
        known_domains: Optional[Set[str]] = None,
        known_emails: Optional[Set[str]] = None,
        known_lead_ids: Optional[Set[str]] = None,
    ) -> AcceptanceDecision:
        """
        Pre-verification cost-saving gate used before consuming limited free HTTPS
        email verification credits. Checks every non-email acceptance criterion plus
        confirming a non-consumer, non-role corporate candidate email exists.
        """
        probe = dict(lead_partial)
        probe["email_verification_status"] = "Provider-Verified"
        if not probe.get("qualification_tier"):
            probe["qualification_tier"] = "Tier 2 - Warm"
        return self.evaluate(
            probe,
            known_domains=known_domains,
            known_emails=known_emails,
            known_lead_ids=known_lead_ids,
        )
