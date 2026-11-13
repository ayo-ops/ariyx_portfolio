"""
Ariyx Lead Intelligence System - Research Engine & Batch Runner
CLI entry point for running controlled research batches.
Strictly decoupled from the live website. Does not send emails, fabricate contacts, or scrape behind logins.
"""

import argparse
import hashlib
import html as html_lib
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import primp
import requests
from bs4 import BeautifulSoup

# Ensure local package imports work
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.compliance.compliance_checker import ComplianceChecker
from src.discovery.search_discovery import SearchDiscovery
from src.discovery.seed_loader import SeedLoader
from src.enrichment.buying_signals import BuyingSignalAuditor
from src.enrichment.leadership_finder import LeadershipFinder
from src.scoring.acceptance_evaluator import AcceptanceEvaluator, NON_COMMERCIAL_EMAIL_PREFIXES
from src.scoring.lead_scorer import LeadScorer
from src.storage.deduplicator import Deduplicator
from src.storage.local_store import LocalStore
from src.verification.email_verifier import EmailVerifier
from src.verification.phone_verifier import PhoneVerifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("AriyxLeadIntelligence")

EMPLOYEE_PHRASE_REGEX = re.compile(
    r"\b(?:over\s+|more\s+than\s+|team\s+of\s+|staff\s+of\s+|around\s+)?(\d{1,5})(?:\+)?\s*"
    r"(?:employees|staff|specialists|team\s+members|consultants|marketers|experts|people)\b",
    re.I,
)
JSONLD_EMP_REGEX = re.compile(r'"numberOfEmployees"\s*:\s*\{?[^}]*?(?:"value"|minValue|maxValue)?\s*:?\s*(\d+)', re.I)


class LeadIntelligenceEngine:
    """
    Main orchestration engine for research, qualification, and scoring.
    """

    def __init__(
        self,
        smtp_timeout: float = 3.5,
        load_env: bool = True,
        email_verifier: Optional[EmailVerifier] = None,
    ):
        self.deduplicator = Deduplicator()
        self.compliance_checker = ComplianceChecker()
        self.email_verifier = email_verifier or EmailVerifier(smtp_timeout=smtp_timeout, load_env=load_env)
        self.phone_verifier = PhoneVerifier()
        self.signal_auditor = BuyingSignalAuditor()
        self.leadership_finder = LeadershipFinder()
        self.lead_scorer = LeadScorer()
        self.acceptance_evaluator = AcceptanceEvaluator()
        self.local_store = LocalStore()
        self.search_discovery = SearchDiscovery()

        self.client = primp.Client()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def process_lead(
        self,
        domain: str,
        website_url: str,
        industry: str,
        country: str,
        city: str = "",
        business_name_hint: str = "",
        discovery_source: str = "Search Discovery",
        estimated_employees: Optional[str] = None,
        employee_status: str = "Estimate",
        employee_source_url: str = "",
        skip_internal_dedup: bool = False,
        defer_email_api_unless_prequalified: bool = False,
        max_email_checks: int = 2,
        skip_smtp_probe: bool = False,
    ) -> Dict[str, Any]:
        """
        Processes a single prospect through multi-page crawl, audit, leadership,
        email/phone verification, compliance, and scoring.
        Never fabricates data.
        """
        norm_domain = self.deduplicator.normalize_domain(domain)
        lead_id = f"ARI-{country[:2].upper()}-{hashlib.md5(norm_domain.encode()).hexdigest()[:6].upper()}"

        logger.info(f"Processing candidate: {norm_domain} ({country} - {industry})...")

        # 1. Suppression Check
        is_suppressed, supp_reason = self.deduplicator.is_suppressed(norm_domain, company_name=business_name_hint)
        if is_suppressed:
            logger.warning(f"Suppressed candidate skipped: {norm_domain} ({supp_reason})")
            return self._build_suppressed_record(lead_id, norm_domain, website_url, country, industry, supp_reason)

        # 2. Duplicate Check
        if not skip_internal_dedup:
            is_dup, _ = self.deduplicator.is_duplicate(norm_domain)
            if is_dup:
                logger.info(f"Skipping duplicate domain: {norm_domain}")
                return {}
            self.deduplicator.register(norm_domain)

        # 3. Fetch Public Website HTML (Homepage + multiple Contact / Team pages)
        homepage_html, final_url, fetch_error = self._fetch_html(website_url)

        contact_pages: List[Tuple[str, str]] = []
        team_pages: List[Tuple[str, str]] = []

        if homepage_html:
            discovered_contact_urls, discovered_team_urls = self._discover_candidate_pages(final_url, homepage_html)
            for c_url in discovered_contact_urls[:2]:
                time.sleep(0.25)
                c_html, resolved_c_url, _ = self._fetch_html(c_url)
                if c_html:
                    contact_pages.append((c_html, resolved_c_url))

            for t_url in discovered_team_urls[:3]:
                time.sleep(0.25)
                t_html, resolved_t_url, _ = self._fetch_html(t_url)
                if t_html:
                    team_pages.append((t_html, resolved_t_url))

        # Primary contact / team page fallback references
        primary_contact_html = contact_pages[0][0] if contact_pages else ""
        actual_contact_url = contact_pages[0][1] if contact_pages else final_url
        primary_team_html = team_pages[0][0] if team_pages else ""
        actual_team_url = team_pages[0][1] if team_pages else final_url

        # 4. Extract Business Name & Description
        raw_page_title, clean_page_title, description = self._extract_business_meta(
            homepage_html, business_name_hint or norm_domain
        )
        hint_is_generic = any(
            str(business_name_hint or "").lower().startswith(g)
            for g in ("meet the team", "contact", "our team", "about us", "about", "home", "best ppc", "best seo", "top ", "welcome", "digital marketing agency", "marketing agency")
        )
        business_name = (
            clean_page_title
            if clean_page_title and (hint_is_generic or not business_name_hint or business_name_hint == norm_domain)
            else (business_name_hint or clean_page_title)
        )

        # 5. Leadership & Decision-Maker Identification across team pages -> contact pages -> homepage
        dm_data = self._find_best_leadership(
            pages=team_pages + contact_pages + ([(homepage_html, final_url)] if homepage_html else []),
            fallback_url=actual_team_url or final_url,
        )

        # 6. Multi-page Buying Signal & Problem Evidence Audit
        audit_pages_input: List[Tuple[str, str, bool]] = [(h, u, True) for h, u in contact_pages]
        if homepage_html:
            audit_pages_input.append((homepage_html, final_url, False))
        audit_data = self.signal_auditor.audit_pages(audit_pages_input)

        # 7a. Extract Ranked Public Business Emails (no guessing, prior to API credit spend)
        ranked_emails = self._extract_ranked_email_candidates(
            pages_with_urls=contact_pages + team_pages + ([(homepage_html, final_url)] if homepage_html else []),
            target_domain=norm_domain,
            dm_name=dm_data.get("name"),
        )
        top_email_addr = ranked_emails[0][0] if ranked_emails else ""
        if top_email_addr:
            supp_top, supp_top_reason = self.deduplicator.is_suppressed(norm_domain, email=top_email_addr)
            if supp_top:
                return self._build_suppressed_record(lead_id, norm_domain, website_url, country, industry, supp_top_reason)

        # 8. Extract & Verify Public Business Phone
        candidate_phone = None
        phone_source_url = actual_contact_url or final_url
        for html_src, url_src in contact_pages + team_pages + ([(homepage_html, final_url)] if homepage_html else []):
            ph = self._extract_phone_candidate(html_src)
            if ph:
                candidate_phone = ph
                phone_source_url = url_src
                break
        phone_verification = self.phone_verifier.verify(
            candidate_phone, default_country=country, source_url=phone_source_url
        )

        # 9. Infer/Check Company Sizing from Public Evidence when not provided
        est_emp, emp_status, emp_src = self._resolve_company_sizing(
            pages=team_pages + ([(homepage_html, final_url)] if homepage_html else []),
            provided_est=estimated_employees,
            provided_status=employee_status,
            provided_src=employee_source_url,
        )

        # 10a. Preliminary Compliance & Pre-API Qualification Gate (protects limited $0 verification credits)
        research_status = "COMPLETED" if homepage_html else f"FAILED: {fetch_error or 'Website Unreachable'}"
        evidence_urls = audit_data.get("evidence_urls", [final_url] if final_url else [])
        prelim_compliance = self.compliance_checker.evaluate(
            country=country,
            email=top_email_addr,
            is_suppressed=False,
        )

        allow_ext_api = True
        if defer_email_api_unless_prequalified:
            pre_payload = {
                "lead_id": lead_id,
                "website": final_url or website_url,
                "domain": norm_domain,
                "industry": industry,
                "country": country,
                "business_name": business_name,
                "page_title": raw_page_title,
                "business_description": description,
                "decision_maker_name": dm_data.get("name", "Unavailable"),
                "decision_maker_title": dm_data.get("title", "Unavailable"),
                "decision_maker_tier": dm_data.get("tier", "tier_4"),
                "decision_maker_evidence": dm_data.get("evidence", "Unavailable"),
                "decision_maker_source_url": dm_data.get("source_url", "Unavailable"),
                "signal_score": audit_data.get("signal_score", 0),
                "potential_buying_signals": audit_data.get("signals", []),
                "fit_hypothesis": audit_data.get("fit_hypothesis", "Unavailable"),
                "verified_email": top_email_addr or "Unavailable",
                "estimated_employees": est_emp,
                "compliance_status": prelim_compliance.get("compliance_status", "ELIGIBILITY_NOT_ESTABLISHED"),
                "research_status": research_status,
                "is_suppressed": False,
                "is_duplicate": False,
            }
            pre_decision = self.acceptance_evaluator.evaluate_pre_email(pre_payload)
            if not pre_decision.accepted:
                allow_ext_api = False

        # 7b. Verify Best Public Email Candidate (DNS MX + optional HTTPS/SMTP check; never fabricates verified status)
        email_verification = self._verify_best_email_candidate(
            ranked_emails=ranked_emails,
            default_source_url=actual_contact_url or final_url,
            allow_external_provider=allow_ext_api,
            max_checks=max_email_checks,
            skip_smtp_probe=skip_smtp_probe,
        )

        # Secondary suppression check if discovered email itself is on suppression list
        verified_addr = email_verification.get("email", "")
        if verified_addr:
            supp_email, supp_email_reason = self.deduplicator.is_suppressed(norm_domain, email=verified_addr)
            if supp_email:
                return self._build_suppressed_record(lead_id, norm_domain, website_url, country, industry, supp_email_reason)

        # 10b. Final Regulatory Compliance Assessment on Chosen Email
        compliance_eval = self.compliance_checker.evaluate(
            country=country,
            email=email_verification.get("email", ""),
            is_suppressed=False
        )

        # 11. Lead Qualification & Triple-Lock Scoring

        scoring_payload = {
            "domain": norm_domain,
            "website": final_url or website_url,
            "industry": industry,
            "country": country,
            "employee_count": est_emp,
            "estimated_employees": est_emp,
            "employee_status": emp_status,
            "employee_source_url": emp_src,
            "dm_tier": dm_data.get("tier"),
            "decision_maker_name": dm_data.get("name"),
            "decision_maker_title": dm_data.get("title"),
            "signal_score": audit_data.get("signal_score", 0),
            "potential_buying_signals": audit_data.get("signals", []),
            "email_verification_status": email_verification.get("verification_status"),
            "phone_status": phone_verification.get("status"),
            "research_status": research_status,
            "page_title": raw_page_title,
            "business_description": description,
            "evidence_urls": evidence_urls,
            "is_suppressed": False,
            "is_duplicate": False,
        }

        score_result = self.lead_scorer.score_lead(scoring_payload)

        # Assemble Master Record (Compliance Status strictly independent; Campaign Status always requires manual review)
        record = {
            "lead_id": lead_id,
            "date_researched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "business_name": business_name,
            "page_title": raw_page_title,
            "website": final_url or website_url,
            "domain": norm_domain,
            "industry": industry,
            "country": country,
            "city": city,
            "decision_maker_name": dm_data.get("name", "Unavailable"),
            "decision_maker_title": dm_data.get("title", "Unavailable"),
            "decision_maker_tier": dm_data.get("tier", "tier_4"),
            "decision_maker_evidence": dm_data.get("evidence", "Unavailable"),
            "decision_maker_source_url": dm_data.get("source_url", "Unavailable"),
            "decision_maker_linkedin": dm_data.get("decision_maker_linkedin", "Unavailable"),
            "company_linkedin": dm_data.get("company_linkedin", "Unavailable"),
            "verified_email": email_verification.get("email") or "Unavailable",
            "email_verification_status": email_verification.get("verification_status", "Unavailable"),
            "email_verification_notes": email_verification.get("verification_notes", ""),
            "verification_provider": email_verification.get("verification_provider", ""),
            "smtp_port_25_blocked": bool(email_verification.get("smtp_port_25_blocked", False)),
            "formatted_phone": phone_verification.get("formatted_phone") or "Unavailable",
            "phone_status": phone_verification.get("status", "Unavailable"),
            "estimated_employees": est_emp,
            "employee_status": emp_status,
            "employee_source_url": emp_src,
            "business_description": description,
            "potential_buying_signals": audit_data.get("signals", []),
            "signal_score": audit_data.get("signal_score", 0),
            "fit_hypothesis": audit_data.get("fit_hypothesis", "Unavailable"),
            "evidence_urls": evidence_urls,
            "lead_score": score_result.get("total_score", 0),
            "qualification_tier": score_result.get("qualification_tier", "Needs Further Research"),
            "tier_rationale": score_result.get("tier_rationale", ""),
            "triple_lock_status": score_result.get("triple_lock_status", {}),
            "compliance_status": compliance_eval.get("compliance_status", "ELIGIBILITY_NOT_ESTABLISHED"),
            "compliance_framework": compliance_eval.get("framework", ""),
            "compliance_notes": compliance_eval.get("review_notes", []),
            "campaign_status": "Ready for Manual Review",
            "research_status": research_status,
            "discovery_source": discovery_source
        }

        return record

    def _find_best_leadership(self, pages: List[Tuple[str, str]], fallback_url: str) -> Dict[str, Any]:
        """Searches fetched pages in priority order and returns highest-tier confirmed DM."""
        tier_rank = {"tier_1": 0, "tier_2": 1, "tier_3": 2, "tier_4": 3}
        best: Optional[Dict[str, Any]] = None
        fallback_company_li = "Unavailable"

        for html_src, page_url in pages:
            if not html_src:
                continue
            res = self.leadership_finder.find_leadership(html_src, page_url)
            if res.get("company_linkedin") and res["company_linkedin"] != "Unavailable":
                fallback_company_li = res["company_linkedin"]

            if res.get("name") and res["name"] != "Unavailable":
                if best is None or tier_rank.get(res.get("tier", "tier_4"), 9) < tier_rank.get(best.get("tier", "tier_4"), 9):
                    best = res
                if res.get("tier") == "tier_1":
                    break

        if best:
            if best.get("company_linkedin", "Unavailable") == "Unavailable":
                best["company_linkedin"] = fallback_company_li
            return best

        empty = self.leadership_finder._empty_result(fallback_url)
        empty["company_linkedin"] = fallback_company_li
        return empty

    def _verify_best_email_candidate(
        self,
        ranked_emails: List[Tuple[str, str]],
        default_source_url: str,
        allow_external_provider: bool = True,
        max_checks: int = 2,
        skip_smtp_probe: bool = False,
    ) -> Dict[str, Any]:
        """
        Tests ranked public email candidates and returns best verified/valid result.
        Stops immediately on Catch-All domains or quota-exhausted/inconclusive results
        to conserve limited free HTTPS verification credits.
        """
        if not ranked_emails:
            return self.email_verifier.verify(None, source_url=default_source_url)

        best_res: Optional[Dict[str, Any]] = None
        for email_addr, src_url in ranked_emails[:max(1, int(max_checks))]:
            res = self.email_verifier.verify(
                email_addr,
                source_url=src_url or default_source_url,
                allow_external_provider=allow_external_provider,
                skip_smtp_probe=skip_smtp_probe,
            )
            status = res.get("verification_status", "")
            if self.email_verifier.is_strictly_verified(status):
                return res
            if best_res is None:
                best_res = res
            elif best_res.get("verification_status") in ("Invalid", "Unavailable") and status not in ("Invalid", "Unavailable"):
                best_res = res

            # Catch-all applies domain-wide and inconclusive/port25/quota won't resolve on another alias
            if status in ("Catch-All / Risky", "Verification Inconclusive", "Publicly Listed (Unverified)"):
                break

        return best_res or self.email_verifier.verify(None, source_url=default_source_url)

    def _resolve_company_sizing(
        self,
        pages: List[Tuple[str, str]],
        provided_est: Optional[str],
        provided_status: str,
        provided_src: str,
    ) -> Tuple[str, str, str]:
        """Resolves company headcount honestly without inventing estimates."""
        if provided_est and "unknown" not in str(provided_est).lower():
            return str(provided_est), provided_status or "Estimate", provided_src or ""

        for html_src, page_url in pages:
            if not html_src:
                continue
            m_json = JSONLD_EMP_REGEX.search(html_src)
            if m_json:
                count = int(m_json.group(1))
                if count > 0:
                    return f"{count} (Schema)", "Confirmed", page_url

            text = BeautifulSoup(html_src, "html.parser").get_text(" ", strip=True)
            m_phrase = EMPLOYEE_PHRASE_REGEX.search(text)
            if m_phrase:
                count = int(m_phrase.group(1))
                if 2 <= count <= 100000:
                    return f"{count}+ (Public Copy)", "Estimate", page_url

        if provided_est:
            return str(provided_est), provided_status or "Unknown", provided_src or ""
        return "Unknown (Public Audit)", "Unknown", ""

    def _fetch_html(self, url: str, timeout: float = 8.0) -> tuple[str, str, Optional[str]]:
        """Safely retrieves HTML from target URL with strict timeout. Returns (html, final_url, error_message)."""
        try:
            resp = self.client.get(url, timeout=timeout)
            if resp.status_code == 200:
                return resp.text, str(resp.url), None
            elif resp.status_code in (404, 410, 429, 425, 500, 502, 503):
                return "", url, f"HTTP {resp.status_code}"
            elif resp.status_code != 403:
                return "", url, f"HTTP {resp.status_code}"
        except Exception:
            pass

        try:
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text, resp.url, None
            else:
                return "", url, f"HTTP {resp.status_code} ({resp.reason})"
        except requests.exceptions.Timeout:
            return "", url, f"Connection Timeout ({int(timeout)}s)"
        except requests.exceptions.SSLError:
            return "", url, "SSL Certificate Error"
        except requests.exceptions.ConnectionError:
            return "", url, "Connection Failed / Host Unreachable"
        except Exception as e:
            return "", url, f"Network Error: {type(e).__name__}"

    def _discover_internal_pages(self, base_url: str, homepage_html: str) -> tuple[Optional[str], Optional[str]]:
        """Legacy helper returning top contact and team URL."""
        c_urls, t_urls = self._discover_candidate_pages(base_url, homepage_html)
        return (c_urls[0] if c_urls else None), (t_urls[0] if t_urls else None)

    def _discover_candidate_pages(self, base_url: str, homepage_html: str) -> Tuple[List[str], List[str]]:
        """Discovers prioritized internal /contact and /team /leadership /about URLs on same root domain."""
        if not homepage_html:
            return [], []

        soup = BeautifulSoup(homepage_html, "html.parser")
        base_dom = self.deduplicator.normalize_domain(base_url)

        contact_candidates: List[Tuple[int, str]] = []
        team_candidates: List[Tuple[int, str]] = []
        seen_urls = {base_url.rstrip("/")}

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            href_lower = href.lower()
            text_lower = a.get_text(" ", strip=True).lower()

            if not href or href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue

            full_url = urljoin(base_url, href).split("#")[0].rstrip("/")
            if not full_url.startswith("http"):
                continue
            if self.deduplicator.normalize_domain(full_url) != base_dom:
                continue
            if full_url in seen_urls or any(ext in href_lower for ext in (".pdf", ".jpg", ".png", ".svg", ".xml")):
                continue

            # Contact priority ranking
            if any(k in href_lower or k in text_lower for k in ("contact", "get-in-touch", "reach-us", "book-a-call", "work-with-us", "inquire")):
                score = 0 if "/contact" in href_lower else 1
                contact_candidates.append((score, full_url))
                seen_urls.add(full_url)
            # Dedicated leadership/team pages get higher priority than generic /about pages
            elif any(k in href_lower or k in text_lower for k in ("team", "our-team", "leadership", "people", "founders", "directors")):
                team_candidates.append((0, full_url))
                seen_urls.add(full_url)
            elif any(k in href_lower or k in text_lower for k in ("who-we-are", "about-us", "about", "our-story")):
                team_candidates.append((1, full_url))
                seen_urls.add(full_url)

        contact_candidates.sort(key=lambda x: x[0])
        team_candidates.sort(key=lambda x: x[0])

        contact_urls = [u for _, u in contact_candidates[:2]]
        team_urls = [u for _, u in team_candidates[:3]]

        # Clean path fallback only if nav links did not surface dedicated paths
        parsed_root = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        if not contact_urls:
            contact_urls.append(f"{parsed_root}/contact")
        if not team_urls:
            team_urls.extend([f"{parsed_root}/team", f"{parsed_root}/about"])

        return contact_urls[:2], team_urls[:3]

    @staticmethod
    def _extract_business_meta(html: str, fallback_name: str) -> tuple[str, str, str]:
        """
        Extracts raw page title, cleaned page title, and meta description.
        Returns: (raw_page_title, clean_page_title, meta_description)
        """
        if not html:
            return fallback_name, fallback_name, "Public description unavailable."

        soup = BeautifulSoup(html, "html.parser")
        og_site = soup.find("meta", attrs={"property": re.compile(r"og:site_name", re.I)})
        if not og_site:
            og_site = soup.find("meta", attrs={"name": re.compile(r"og:site_name", re.I)})
        og_name = og_site["content"].strip() if og_site and og_site.get("content") else ""

        title_tag = soup.find("title")
        raw_title = title_tag.get_text().strip() if title_tag else fallback_name

        clean_name = og_name or re.split(r"[-|–—:]", raw_title)[0].strip() or fallback_name
        if any(clean_name.lower().startswith(g) for g in ("home", "contact", "meet the team", "our team", "about us", "about", "welcome")):
            parts = [p.strip() for p in re.split(r"[-|–—:]", raw_title) if p.strip()]
            for p in parts[1:]:
                if not any(p.lower().startswith(g) for g in ("home", "contact", "meet the team", "our team", "about us", "about")):
                    clean_name = p
                    break

        meta_desc = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        desc_text = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else ""

        if not desc_text:
            desc_text = f"Full-service provider operating at {fallback_name}."

        return raw_title[:150], clean_name[:60], desc_text[:250]

    @staticmethod
    def _extract_ranked_email_candidates(
        pages_with_urls: List[Tuple[str, str]],
        target_domain: str,
        dm_name: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        """
        Collects, cleans, filters, and ranks ONLY published public email addresses
        from crawled HTML (never fabricates addresses).
        """
        ignored_domains = [
            re.compile(r"sentry\.io$", re.I),
            re.compile(r"bugsnag\.com$", re.I),
            re.compile(r"datadog\.com$", re.I),
            re.compile(r"example\.(?:com|org|net)$", re.I),
            re.compile(r"w3\.org$", re.I),
            re.compile(r"wixpress\.com$", re.I),
            re.compile(r"squarespace\.com$", re.I),
        ]
        ignored_exact_emails = {
            "name@email.com", "you@company.com", "user@example.com", "test@test.com",
            "info@example.com", "email@example.com", "yourname@domain.com", "name@domain.com",
            "sample@email.com", "first.last@company.com"
        }

        dm_tokens = []
        if dm_name and dm_name != "Unavailable":
            dm_tokens = [re.sub(r"[^a-z]", "", t.lower()) for t in dm_name.split() if len(t) >= 2]

        def is_valid_candidate(email_str: str) -> bool:
            clean = email_str.strip().lower()
            if "@" not in clean or clean in ignored_exact_emails:
                return False
            local, dom = clean.split("@", 1)
            if not local or not dom or "." not in dom:
                return False
            if local in NON_COMMERCIAL_EMAIL_PREFIXES:
                return False
            if any(p.search(dom) for p in ignored_domains):
                return False
            if any(clean.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".svg", ".js", ".css")):
                return False
            return True

        def score_candidate(email_str: str) -> int:
            local, dom = email_str.split("@", 1)
            pts = 0
            if target_domain and (dom == target_domain or dom.endswith(f".{target_domain}")):
                pts += 50
            if any(tok and tok in local for tok in dm_tokens):
                pts += 35
            if local in ("founder", "ceo", "director", "hello", "contact", "enquiries", "inquiries", "newbusiness", "info", "sales", "team"):
                pts += 15
            return pts

        found: Dict[str, Tuple[int, str]] = {}
        for raw_html, page_url in pages_with_urls:
            if not raw_html:
                continue
            decoded_html = html_lib.unescape(raw_html)
            soup = BeautifulSoup(decoded_html, "html.parser")

            candidates_here: List[str] = []
            for a in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
                cand = a["href"].replace("mailto:", "").split("?")[0].strip().lower()
                if cand:
                    candidates_here.append(cand)

            text_matches = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", decoded_html)
            for m in text_matches:
                candidates_here.append(m.lower())

            for c in candidates_here:
                if is_valid_candidate(c):
                    sc = score_candidate(c)
                    if c not in found or sc > found[c][0]:
                        found[c] = (sc, page_url)

        ranked = sorted(
            [(email, meta[1], meta[0]) for email, meta in found.items()],
            key=lambda x: x[2],
            reverse=True,
        )
        return [(email, url) for email, url, _ in ranked]

    @staticmethod
    def _extract_email_candidate(html: str, dm_name: Optional[str] = None) -> Optional[str]:
        ranked = LeadIntelligenceEngine._extract_ranked_email_candidates(
            pages_with_urls=[(html, "")],
            target_domain="",
            dm_name=dm_name,
        )
        return ranked[0][0] if ranked else None

    @staticmethod
    def _extract_phone_candidate(html: str) -> Optional[str]:
        """Finds public telephone number from tel: tags or standard format."""
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")

        tel_tag = soup.find("a", href=re.compile(r"^tel:", re.I))
        if tel_tag:
            return tel_tag["href"].replace("tel:", "").strip()

        phone_matches = re.findall(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}", html)
        if phone_matches:
            for p in phone_matches:
                cleaned_p = re.sub(r"\D", "", p)
                if 9 <= len(cleaned_p) <= 15:
                    return p.strip()

        return None

    @staticmethod
    def _build_suppressed_record(lead_id, domain, url, country, industry, reason):
        return {
            "lead_id": lead_id,
            "date_researched": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "business_name": domain,
            "website": url,
            "domain": domain,
            "industry": industry,
            "country": country,
            "lead_score": 0,
            "qualification_tier": "Excluded",
            "triple_lock_status": {
                "confirmed_decision_maker": False,
                "strong_business_fit": False,
                "credible_problem_evidence": False,
                "all_passed": False
            },
            "compliance_status": "OPT_OUT_RECORDED",
            "campaign_status": "Suppressed",
            "research_status": "SKIPPED_SUPPRESSED",
            "tier_rationale": f"Excluded (Suppressed / Opt-Out): {reason}"
        }


def run():
    parser = argparse.ArgumentParser(description="Ariyx Lead Intelligence System - Batch Runner")
    parser.add_argument("--count", type=int, default=25, help="Number of prospects to research (e.g. 25-50)")
    parser.add_argument("--industry", type=str, default="Marketing agencies", help="Target industry")
    parser.add_argument("--country", type=str, default="US", help="Target country (US or UK)")
    parser.add_argument("--seed-file", type=str, default="data/seed_companies.csv", help="Path to seed CSV file")
    parser.add_argument("--use-search", action="store_true", help="Use DuckDuckGo free search discovery")

    args = parser.parse_args()

    engine = LeadIntelligenceEngine()
    candidates: List[Dict[str, Any]] = []

    print("\n" + "=" * 70)
    print("  ARIYX SYSTEMS - LEAD INTELLIGENCE SYSTEM")
    print(f"  Target Industry: {args.industry} | Country: {args.country}")
    print(f"  Target Count:    {args.count}")
    print("=" * 70 + "\n")

    if args.use_search:
        candidates = engine.search_discovery.discover(
            industry_key=args.industry,
            country=args.country,
            max_results=args.count
        )
    else:
        seed_path = Path(__file__).resolve().parent / args.seed_file
        candidates = SeedLoader.load_from_csv(str(seed_path))

    if not candidates:
        logger.warning("No candidate domains available. Please provide a seed file or enable --use-search.")
        return

    candidates_to_process = candidates[:args.count]
    processed_leads: List[Dict[str, Any]] = []

    for idx, cand in enumerate(candidates_to_process, 1):
        domain = cand.get("domain") or cand.get("website")
        website = cand.get("website_url") or cand.get("website") or f"https://{domain}"
        industry = cand.get("industry") or args.industry
        country = cand.get("country") or args.country
        city = cand.get("city", "")
        name_hint = cand.get("business_name") or cand.get("title", "")

        print(f"\n[{idx}/{len(candidates_to_process)}] Researching: {domain}...")
        est_emp = cand.get("estimated_employees")
        emp_status = cand.get("employee_status", "Estimate")
        emp_src = cand.get("employee_source_url", "")
        lead = engine.process_lead(
            domain=domain,
            website_url=website,
            industry=industry,
            country=country,
            city=city,
            business_name_hint=name_hint,
            discovery_source=cand.get("discovery_source", "Curated Seed File"),
            estimated_employees=est_emp,
            employee_status=emp_status,
            employee_source_url=emp_src
        )

        if lead:
            processed_leads.append(lead)

        time.sleep(1.5)

    unique_countries = sorted(list({l.get("country", "").lower() for l in processed_leads if l.get("country")}))
    unique_industries = sorted(list({l.get("industry", "").lower().replace(" ", "_") for l in processed_leads if l.get("industry")}))

    geo_str = "_".join(unique_countries) if unique_countries else "multi_geo"
    if len(unique_industries) == 1:
        ind_str = unique_industries[0]
    elif len(unique_industries) > 1:
        ind_str = "mixed_services"
    else:
        ind_str = "leads"
    batch_name = f"{ind_str}_{geo_str}"

    export_files = engine.local_store.save_batch(processed_leads, batch_name=batch_name)

    tier_counts = {
        "Tier 1 - Hot": 0,
        "Tier 2 - Warm": 0,
        "Tier 3 - Low": 0,
        "Low-Priority Prospect": 0,
        "Enterprise Prospect": 0,
        "Needs Further Research": 0,
        "Excluded": 0,
    }
    comp_counts = {"REVIEW_REQUIRED": 0, "RESTRICTED": 0, "ELIGIBILITY_NOT_ESTABLISHED": 0, "OPT_OUT_RECORDED": 0}
    email_status_counts = {}
    dm_identified = []
    research_failures = []
    phones_found = 0

    for l in processed_leads:
        tier = l.get("qualification_tier", "Needs Further Research")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1

        c_status = l.get("compliance_status", "ELIGIBILITY_NOT_ESTABLISHED")
        comp_counts[c_status] = comp_counts.get(c_status, 0) + 1

        e_status = l.get("email_verification_status", "Unavailable")
        email_status_counts[e_status] = email_status_counts.get(e_status, 0) + 1

        dm_name = l.get("decision_maker_name")
        if dm_name and dm_name != "Unavailable":
            dm_identified.append((l.get("business_name"), dm_name, l.get("decision_maker_title"), l.get("decision_maker_tier")))

        if l.get("formatted_phone") and l.get("formatted_phone") != "Unavailable":
            phones_found += 1

        res_status = l.get("research_status", "")
        if res_status.startswith("FAILED"):
            research_failures.append((l.get("domain"), res_status))

    print("\n" + "=" * 70)
    print("  RESEARCH & QUALIFICATION BATCH COMPLETED")
    print("=" * 70)
    print(f"Total Prospects Researched: {len(processed_leads)}")
    if processed_leads:
        print(f"  - Decision-Makers Identified:        {len(dm_identified)} / {len(processed_leads)} ({len(dm_identified)/len(processed_leads)*100:.1f}%)")
    print(f"  - Business Phones Validated (E.164): {phones_found} / {len(processed_leads)}")
    print(f"  - Research Failures / Unreachable:   {len(research_failures)}")
    print("-" * 70)
    print("Lead Qualification Tier Distribution:")
    print(f"  [*] Tier 1 - Hot (Triple-Lock Passed): {tier_counts.get('Tier 1 - Hot', 0)}")
    print(f"  [-] Tier 2 - Warm:                     {tier_counts.get('Tier 2 - Warm', 0)}")
    print(f"  [-] Tier 3 - Low:                      {tier_counts.get('Tier 3 - Low', 0)}")
    print(f"  [-] Low-Priority Prospect (<40 Score): {tier_counts.get('Low-Priority Prospect', 0)}")
    print(f"  [-] Enterprise Prospect (>250 Staff):  {tier_counts.get('Enterprise Prospect', 0)}")
    print(f"  [-] Needs Further Research:            {tier_counts.get('Needs Further Research', 0)}")
    print(f"  [x] Excluded (Invalid/Dup/Suppressed): {tier_counts.get('Excluded', 0)}")
    print("-" * 70)
    print("Email Verification Breakdown:")
    for k, v in email_status_counts.items():
        print(f"  - {k}: {v}")
    print("-" * 70)
    print("Compliance Assessment (Review Required before Outreach):")
    for k, v in comp_counts.items():
        print(f"  - {k}: {v}")
    if research_failures:
        print("-" * 70)
        print("Research Failures:")
        for dom, reason in research_failures:
            print(f"  - {dom}: {reason}")
    print("-" * 70)
    print("Generated Local Export Files:")
    print(f"  - CSV:  {export_files['csv_path']}")
    print(f"  - JSON: {export_files['json_path']}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run()
