"""
Lead Qualification and Scoring Module
Calculates the 0-100 score based on approved weights:
- Business and industry fit: 25 points
- Decision-maker identification: 25 points
- Evidence of a potential problem Ariyx Systems can solve: 35 points
- Contact quality and reachability: 15 points

Qualification Classification Precedence:
1. Excluded: Genuinely invalid, duplicate, suppressed/opt-out, or ineligible non-B2B records.
2. Needs Further Research: Incomplete/failed website audit or bot-blocked public content.
3. Enterprise Prospect: Valid companies exceeding 250 employees with completed research.
4. Core SMB Priority Tiers (<= 250 employees):
   - Tier 1 - Hot: Score >= 75 AND Triple-Lock satisfied.
   - Tier 2 - Warm: Score >= 60 (or >= 75 capped due to missing Triple-Lock).
   - Tier 3 - Low: Score 40-59.
   - Low-Priority Prospect: Score < 40 (retained for manual review/enrichment).

Note: Sales qualification is strictly independent from regulatory Compliance Status.
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Standardized Qualification Tier Categories (Column T)
TIER_1_HOT = "Tier 1 - Hot"
TIER_2_WARM = "Tier 2 - Warm"
TIER_3_LOW = "Tier 3 - Low"
TIER_LOW_PRIORITY = "Low-Priority Prospect"
TIER_ENTERPRISE = "Enterprise Prospect"
TIER_NEEDS_RESEARCH = "Needs Further Research"
TIER_EXCLUDED = "Excluded"

TARGET_INDUSTRIES = {
    "marketing agencies", "marketing agency", "digital marketing", "seo agency",
    "advertising agency", "consulting firms", "consulting firm", "management consulting",
    "business consulting", "financial coaches", "fitness coaching", "online coaches"
}

TARGET_COUNTRIES = {"US", "UK", "CA", "AU", "EU", "GB"}

EXCLUDED_PLATFORM_DOMAINS: Set[str] = {
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "wikipedia.org", "clutch.co", "yelp.com", "upwork.com",
    "fiverr.com", "glassdoor.com", "indeed.com", "medium.com", "forbes.com"
}

DISPOSABLE_OR_PLACEHOLDER_DOMAINS: Set[str] = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com",
    "sharklasers.com", "trashmail.com", "yopmail.com", "throwawaymail.com",
    "example.com", "example.org", "example.net", "test.com", "localhost"
}

BOT_BLOCK_PAGE_MARKERS = (
    "just a moment",
    "attention required",
    "access denied",
    "verify you are human",
    "are you a robot",
    "ddos-guard",
    "403 forbidden",
)

NON_B2B_ENTITY_TYPES: Set[str] = {
    "consumer", "personal", "individual_blog", "government", "non_b2b_consumer"
}

HOSTNAME_REGEX = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+$"
)


class LeadScorer:
    """
    Evaluates enriched prospect records against Ariyx Systems qualification benchmarks.
    """

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            config_path = str(base_dir / "config" / "scoring_weights.json")

        self.config_path = Path(config_path)
        self.weights = self._load_weights()

    def _load_weights(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            logger.warning(f"Weights file not found at {self.config_path}. Using standard defaults.")
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load weights: {e}")
            return {}

    def score_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates sub-scores, total score, triple-lock criteria, and final qualification tier.

        Evaluation precedence:
        1. Excluded (genuinely invalid, duplicate, suppressed, or non-B2B ineligible records)
        2. Needs Further Research (failed/incomplete website audit or blocked page content)
        3. Enterprise Prospect (> 250 employees with completed research)
        4. Core SMB priority tiers (Tier 1 - Hot, Tier 2 - Warm, Tier 3 - Low, Low-Priority Prospect)
        """
        # 1. Business & Industry Fit (Max 25 pts)
        fit_score, fit_details = self._calculate_business_fit(lead_data)

        # 2. Decision-Maker Identification (Max 25 pts)
        dm_score, dm_details = self._calculate_dm_score(lead_data)

        # 3. Evidence of Potential Problems (Max 35 pts)
        problem_score, problem_details = self._calculate_problem_evidence(lead_data)

        # 4. Contact Quality & Reachability (Max 15 pts)
        contact_score, contact_details = self._calculate_contact_quality(lead_data)

        total_score = fit_score + dm_score + problem_score + contact_score

        # 5. Parse company sizing context (retained for Enterprise / Needs Further Research notes)
        emp_raw = lead_data.get("employee_count") or lead_data.get("estimated_employees")
        emp_count = self._parse_employee_count(emp_raw)
        emp_status = lead_data.get("employee_status", "Estimate")
        emp_source = lead_data.get("employee_source_url", "")
        is_enterprise = bool(emp_count and emp_count > 250)

        # 6. Evaluate diagnostic Triple-Lock indicators honestly
        lock_dm, lock_fit, lock_problem = self._evaluate_triple_lock(
            lead_data=lead_data,
            dm_score=dm_score,
            fit_score=fit_score,
            problem_score=problem_score,
            is_enterprise=is_enterprise,
        )

        # Precedence 1: Genuine Exclusion Check
        is_excluded, excl_reason = self._check_exclusion(lead_data)
        if is_excluded:
            return {
                "total_score": total_score,
                "qualification_tier": TIER_EXCLUDED,
                "tier_rationale": f"Excluded: {excl_reason}",
                "sub_scores": {
                    "business_and_industry_fit": fit_score,
                    "decision_maker_identification": dm_score,
                    "evidence_of_potential_problems": problem_score,
                    "contact_quality_and_reachability": contact_score
                },
                "triple_lock_status": {
                    "confirmed_decision_maker": False,
                    "strong_business_fit": False,
                    "credible_problem_evidence": False,
                    "all_passed": False
                },
                "score_breakdown": {
                    "fit_details": fit_details,
                    "dm_details": dm_details,
                    "problem_details": problem_details,
                    "contact_details": contact_details
                }
            }

        # Precedence 2: Research Sufficiency Check (takes priority over enterprise sizing)
        has_sufficient_research, research_gap = self._check_research_sufficiency(lead_data, problem_score)
        if not has_sufficient_research:
            if is_enterprise:
                size_label = str(emp_raw).strip() if emp_raw else f"{emp_count}+ ({emp_status})"
                source_note = f" (Source: {emp_source})" if emp_source else ""
                tier_rationale = (
                    f"Needs further research: {research_gap} "
                    f"Known enterprise sizing retained: {size_label}{source_note}."
                )
            else:
                tier_rationale = (
                    f"Needs further research: {research_gap} "
                    "Retained in pipeline for manual audit or retry."
                )

            return {
                "total_score": total_score,
                "qualification_tier": TIER_NEEDS_RESEARCH,
                "tier_rationale": tier_rationale,
                "sub_scores": {
                    "business_and_industry_fit": fit_score,
                    "decision_maker_identification": dm_score,
                    "evidence_of_potential_problems": problem_score,
                    "contact_quality_and_reachability": contact_score
                },
                "triple_lock_status": {
                    "confirmed_decision_maker": lock_dm,
                    "strong_business_fit": lock_fit,
                    "credible_problem_evidence": lock_problem,
                    "all_passed": False
                },
                "score_breakdown": {
                    "fit_details": fit_details,
                    "dm_details": dm_details,
                    "problem_details": problem_details,
                    "contact_details": contact_details
                }
            }

        # Precedence 3: Enterprise Prospect Track (> 250 employees with completed research)
        if is_enterprise:
            size_label = str(emp_raw).strip() if emp_raw else f"{emp_count}+"
            source_note = f" (Source: {emp_source})" if emp_source else ""
            status_note = emp_status.lower() if isinstance(emp_status, str) else "estimate"
            size_phrase = size_label if status_note in size_label.lower() else f"{status_note} {size_label}"
            return {
                "total_score": total_score,
                "qualification_tier": TIER_ENTERPRISE,
                "tier_rationale": (
                    f"Enterprise prospect: Business has {size_phrase} employees "
                    f"(exceeds 250 SMB threshold){source_note}. Retained on dedicated enterprise track "
                    f"with audit score ({total_score}/100)."
                ),
                "sub_scores": {
                    "business_and_industry_fit": fit_score,
                    "decision_maker_identification": dm_score,
                    "evidence_of_potential_problems": problem_score,
                    "contact_quality_and_reachability": contact_score
                },
                "triple_lock_status": {
                    "confirmed_decision_maker": lock_dm,
                    "strong_business_fit": False,
                    "credible_problem_evidence": lock_problem,
                    "all_passed": False
                },
                "score_breakdown": {
                    "fit_details": fit_details,
                    "dm_details": dm_details,
                    "problem_details": problem_details,
                    "contact_details": contact_details
                }
            }

        # Precedence 4: Core SMB Qualification Tiers
        all_locks_passed = lock_dm and lock_fit and lock_problem

        min_problem = (
            self.weights.get("tier_requirements", {})
            .get("tier_1_hot", {})
            .get("triple_lock_mandatory", {})
            .get("min_problem_evidence_score", 12)
        )

        if total_score >= 75 and all_locks_passed:
            tier = TIER_1_HOT
            tier_rationale = "Satisfies all Triple-Lock criteria: Confirmed Decision-Maker, Strong Business Fit, and Credible Problem Evidence."
        elif total_score >= 60:
            tier = TIER_2_WARM
            if total_score >= 75 and not all_locks_passed:
                failed_locks = []
                if not lock_dm:
                    failed_locks.append("Unconfirmed Decision-Maker")
                if not lock_fit:
                    failed_locks.append("Weak Business/Geo Fit")
                if not lock_problem:
                    failed_locks.append(f"Insufficient Problem Evidence (<{min_problem} pts)")
                tier_rationale = (
                    f"High numerical score ({total_score}/100) but capped at Tier 2 because "
                    f"Triple-Lock failed on: {', '.join(failed_locks)}."
                )
            else:
                tier_rationale = "Solid prospect meeting baseline qualification criteria."
        elif total_score >= 40:
            tier = TIER_3_LOW
            tier_rationale = "Moderate fit or limited public operational data; backlog status."
        else:
            tier = TIER_LOW_PRIORITY
            tier_rationale = (
                f"Low-priority prospect (Score {total_score}/100, below 40 baseline). "
                "Valid SMB record with completed audit; retained for manual review and deeper enrichment."
            )

        return {
            "total_score": total_score,
            "qualification_tier": tier,
            "tier_rationale": tier_rationale,
            "sub_scores": {
                "business_and_industry_fit": fit_score,
                "decision_maker_identification": dm_score,
                "evidence_of_potential_problems": problem_score,
                "contact_quality_and_reachability": contact_score
            },
            "triple_lock_status": {
                "confirmed_decision_maker": lock_dm,
                "strong_business_fit": lock_fit,
                "credible_problem_evidence": lock_problem,
                "all_passed": all_locks_passed
            },
            "score_breakdown": {
                "fit_details": fit_details,
                "dm_details": dm_details,
                "problem_details": problem_details,
                "contact_details": contact_details
            }
        }

    @staticmethod
    def _extract_clean_domain(url_or_domain: Any) -> str:
        """Extracts and normalizes lowercase domain host from a domain or URL string."""
        if not url_or_domain:
            return ""
        raw = str(url_or_domain).strip().lower()
        if not raw or raw.startswith(("mailto:", "tel:", "javascript:")):
            return ""
        if not (raw.startswith("http://") or raw.startswith("https://")):
            raw = f"http://{raw}"
        try:
            parsed = urlparse(raw)
            host = parsed.netloc or parsed.path.split("/")[0]
            if ":" in host:
                host = host.split(":")[0]
            if host.startswith("www."):
                host = host[4:]
            return host.strip()
        except Exception:
            return ""

    @staticmethod
    def _is_valid_hostname(hostname: str) -> bool:
        """Checks basic DNS hostname structure with valid multi-character alphabetic TLD."""
        if not hostname or not HOSTNAME_REGEX.match(hostname):
            return False
        tld = hostname.rsplit(".", 1)[-1]
        return len(tld) >= 2 and tld.isalpha()

    @staticmethod
    def _domain_matches_set(hostname: str, domain_set: Set[str]) -> bool:
        """Matches exact root domain or subdomains (e.g., uk.linkedin.com -> linkedin.com)."""
        return any(hostname == d or hostname.endswith(f".{d}") for d in domain_set)

    def _check_exclusion(self, lead_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Determines whether a record is genuinely invalid, duplicate, suppressed/opted-out,
        or ineligible (and should be excluded from pipeline review).
        Never conflates regulatory RESTRICTED status (e.g., jurisdiction/consent rules)
        with sales exclusion.
        """
        if lead_data.get("is_suppressed"):
            reason = lead_data.get("suppression_reason") or "Prospect or domain is registered on the suppression list."
            return True, str(reason)

        comp_status = str(lead_data.get("compliance_status") or "").strip().upper()
        if comp_status == "OPT_OUT_RECORDED":
            return True, "Prospect opt-out / suppression recorded (OPT_OUT_RECORDED)."

        camp_status = str(lead_data.get("campaign_status") or "").strip().lower()
        if camp_status == "suppressed":
            return True, "Record campaign status marked Suppressed."

        if lead_data.get("is_duplicate"):
            return True, str(lead_data.get("duplicate_reason") or "Duplicate record already captured in batch or registry.")

        if lead_data.get("is_excluded") or lead_data.get("entity_ineligible"):
            return True, str(lead_data.get("exclusion_reason") or "Marked ineligible / out-of-scope entity.")

        if lead_data.get("domain_invalid") or lead_data.get("is_invalid"):
            return True, str(lead_data.get("exclusion_reason") or "Invalid domain or malformed prospect record.")

        entity_type = str(lead_data.get("entity_type") or "").strip().lower()
        if entity_type in NON_B2B_ENTITY_TYPES or lead_data.get("is_b2b") is False:
            return True, f"Ineligible non-B2B entity type ('{entity_type or 'non-B2B'}')."

        has_domain_input = any(k in lead_data for k in ("domain", "website", "Website URL", "Website"))
        if has_domain_input:
            raw_target = (
                lead_data.get("domain")
                or lead_data.get("website")
                or lead_data.get("Website URL")
                or lead_data.get("Website")
                or ""
            )
            norm_dom = self._extract_clean_domain(raw_target)
            if not norm_dom or not self._is_valid_hostname(norm_dom):
                return True, f"Invalid or missing business domain/URL ('{str(raw_target).strip()}')."

            if self._domain_matches_set(norm_dom, EXCLUDED_PLATFORM_DOMAINS):
                return True, f"Directory, social, or marketplace platform ('{norm_dom}') is not an independent target business."

            if self._domain_matches_set(norm_dom, DISPOSABLE_OR_PLACEHOLDER_DOMAINS):
                return True, f"Placeholder or disposable domain ('{norm_dom}') is ineligible."

        return False, None

    def _check_research_sufficiency(self, lead_data: Dict[str, Any], problem_score: int) -> Tuple[bool, Optional[str]]:
        """
        Checks whether enough automated website research completed to score reliably.
        """
        if lead_data.get("insufficient_research"):
            return False, str(lead_data.get("research_gap_reason") or "Explicitly marked as needing further research.")

        if "research_status" in lead_data:
            res_status = str(lead_data.get("research_status") or "").strip()
            if not res_status.upper().startswith("COMPLETED"):
                return False, f"Website audit incomplete ({res_status or 'missing status'})."

        page_title = str(lead_data.get("page_title") or "").strip()
        page_title_lower = page_title.lower()
        if any(marker in page_title_lower for marker in BOT_BLOCK_PAGE_MARKERS):
            return False, f"Public website returned challenge or block page ('{page_title[:80]}')."

        desc = str(lead_data.get("business_description") or "").strip()
        ev_urls = lead_data.get("evidence_urls")
        dm_name = str(lead_data.get("decision_maker_name") or lead_data.get("name") or "Unavailable").strip()
        if (
            desc == "Public description unavailable."
            and not ev_urls
            and problem_score == 0
            and dm_name in ("", "Unavailable")
        ):
            return False, "No usable website description, signals, evidence URLs, or leadership data extracted."

        return True, None

    def _calculate_business_fit(self, lead: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        score = 0
        details = {}
        industry = (lead.get("industry") or "").strip().lower()
        country = (lead.get("country") or "").strip().upper()
        size_est = lead.get("employee_count") or lead.get("estimated_employees") or 0

        # Core Industry check (12 pts)
        if any(tgt in industry for tgt in TARGET_INDUSTRIES):
            score += 12
            details["industry"] = "Core target industry (+12)"
        elif industry:
            score += 6
            details["industry"] = "Adjacent service business (+6)"
        else:
            details["industry"] = "Unspecified industry (0)"

        # Target Geography check (8 pts)
        if country in TARGET_COUNTRIES:
            score += 8
            details["geography"] = f"Priority target country {country} (+8)"
        elif country:
            score += 3
            details["geography"] = f"Secondary country {country} (+3)"
        else:
            details["geography"] = "Unknown country (0)"

        # Team Size Sweet-spot (3-50 employees is optimal for Ariyx) (5 pts)
        emp = self._parse_employee_count(size_est)
        if emp is not None:
            if 3 <= emp <= 50:
                score += 5
                details["team_size"] = f"Optimal team size {emp} staff (+5)"
            elif 1 <= emp <= 100:
                score += 3
                details["team_size"] = f"Viable team size {emp} staff (+3)"
            elif 101 <= emp <= 250:
                score += 2
                details["team_size"] = f"Mid-market team size {emp} staff (+2)"
            else:
                score += 0
                details["team_size"] = f"Enterprise team size {emp} staff (Exceeds 250 ICP threshold) (0)"
        else:
            score += 2
            details["team_size"] = "Estimated SMB (2)"

        return min(25, score), details

    @staticmethod
    def _parse_employee_count(val: Any) -> Optional[int]:
        """Safely parses integer employee count or upper bound of range (e.g. '10-25' -> 25, '500+' -> 500)."""
        if val is None:
            return None
        if isinstance(val, int):
            return val
        s = str(val).strip().replace(",", "")
        # Range e.g. "10-25" or "100 - 250"
        range_match = re.search(r"(\d+)\s*[-–—]\s*(\d+)", s)
        if range_match:
            return int(range_match.group(2))
        # Plus e.g. "500+" or "10000+"
        plus_match = re.search(r"(\d+)\s*\+", s)
        if plus_match:
            return int(plus_match.group(1))
        # Single integer in string
        digits = re.findall(r"\d+", s)
        if digits:
            return int(digits[0])
        return None

    def _calculate_dm_score(self, lead: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        tier = lead.get("dm_tier") or lead.get("decision_maker_tier") or lead.get("tier") or "tier_4"
        name = lead.get("decision_maker_name") or lead.get("name") or "Unavailable"
        title = lead.get("decision_maker_title") or lead.get("title") or "Unavailable"

        if name == "Unavailable" or not name.strip():
            return 0, {"role": "No verified decision-maker found (0)"}

        if tier == "tier_1":
            return 25, {"role": f"Tier 1 Executive ({title}: {name}) (+25)"}
        elif tier == "tier_2":
            return 20, {"role": f"Tier 2 Leader ({title}: {name}) (+20)"}
        elif tier == "tier_3":
            return 15, {"role": f"Tier 3 Operational Manager ({title}: {name}) (+15)"}
        else:
            return 0, {"role": "Generic or unverified contact (0)"}

    def _calculate_problem_evidence(self, lead: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        # Take observed signal score from auditor (already capped at 35)
        observed_score = lead.get("signal_score") or lead.get("problem_score") or 0
        signals = lead.get("potential_buying_signals") or lead.get("signals") or []
        count = len(signals)
        details = {
            "signal_count": count,
            "observed_score": observed_score,
            "evidence_present": count > 0
        }
        return min(35, int(observed_score)), details

    def _calculate_contact_quality(self, lead: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        score = 0
        details = {}
        email_status = lead.get("email_verification_status") or "Unavailable"
        phone_status = lead.get("phone_status") or "Unavailable"

        # Email quality (up to 12 pts)
        if email_status in ("Provider-Verified", "SMTP-Verified"):
            score += 12
            details["email"] = f"{email_status} business email (+12)"
        elif email_status == "Publicly Listed (Unverified)":
            score += 8
            details["email"] = "Publicly listed unverified email (+8)"
        elif email_status == "Verification Inconclusive":
            score += 4
            details["email"] = "Public email discovered (Verification Inconclusive) (+4)"
        elif email_status == "Catch-All / Risky":
            score += 4
            details["email"] = "Catch-All / Risky email (+4)"
        else:
            details["email"] = "Invalid or unavailable email (0)"

        # Phone quality (up to 3 pts)
        if phone_status == "Public Business Phone":
            score += 3
            details["phone"] = "Valid E.164 public business phone (+3)"
        else:
            details["phone"] = "No public business phone (0)"

        return min(15, score), details

    def _evaluate_triple_lock(
        self,
        lead_data: Dict[str, Any],
        dm_score: int,
        fit_score: int,
        problem_score: int,
        is_enterprise: bool = False,
    ) -> Tuple[bool, bool, bool]:
        """
        Enforces the 3 mandatory locks for core SMB Tier 1 qualification:
        1. Lock DM: Founder/Owner/CEO/Managing Director confirmed (dm_score >= 20).
        2. Lock Fit: Core target industry in target country and <= 250 employees.
        3. Lock Problem: Concrete potential problem evidence observed with URL (problem_score >= 12).
        """
        dm_tier = lead_data.get("dm_tier") or lead_data.get("decision_maker_tier") or lead_data.get("tier")
        dm_name = lead_data.get("decision_maker_name") or lead_data.get("name") or "Unavailable"
        has_dm = (dm_name != "Unavailable") and (dm_tier in ("tier_1", "tier_2") or dm_score >= 20)

        industry = (lead_data.get("industry") or "").lower()
        country = (lead_data.get("country") or "").upper()
        has_fit = (
            any(tgt in industry for tgt in TARGET_INDUSTRIES)
            and (country in TARGET_COUNTRIES)
            and not is_enterprise
        )

        min_problem = (
            self.weights.get("tier_requirements", {})
            .get("tier_1_hot", {})
            .get("triple_lock_mandatory", {})
            .get("min_problem_evidence_score", 12)
        )
        has_problem = (problem_score >= min_problem)

        return has_dm, has_fit, has_problem
