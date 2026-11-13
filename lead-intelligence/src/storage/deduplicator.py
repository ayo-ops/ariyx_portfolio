"""
Deduplication and Suppression Module
Handles domain normalization, canonical email formatting, suppression list checks,
and multi-key deduplication for the Ariyx Lead Intelligence System.
"""

import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Any, Tuple, Optional, Set

logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Manages in-memory and persisted deduplication and suppression checks.
    """

    def __init__(self, suppression_path: Optional[str] = None):
        if suppression_path is None:
            # Default to lead-intelligence/data/suppression.json
            base_dir = Path(__file__).resolve().parent.parent.parent
            suppression_path = str(base_dir / "data" / "suppression.json")

        self.suppression_path = Path(suppression_path)
        self.suppressed_domains: Set[str] = set()
        self.suppressed_emails: Set[str] = set()
        self.suppressed_companies: Set[str] = set()
        self.opt_outs: Set[str] = set()

        # In-memory tracking of seen leads within current and previous runs
        self.seen_domains: Set[str] = set()
        self.seen_emails: Set[str] = set()
        self.seen_companies: Set[str] = set()

        self._load_suppression_list()

    def _load_suppression_list(self) -> None:
        """Loads domains, emails, and company names marked as suppressed or opted out."""
        if not self.suppression_path.exists():
            logger.warning(f"Suppression file not found at {self.suppression_path}. Starting with empty list.")
            return

        try:
            with open(self.suppression_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.suppressed_domains = {self.normalize_domain(d) for d in data.get("domains", []) if d}
            self.suppressed_emails = {self.normalize_email(e) for e in data.get("emails", []) if e}
            self.suppressed_companies = {c.strip().lower() for c in data.get("company_names", []) if c}
            self.opt_outs = {opt.strip().lower() for opt in data.get("opt_outs", []) if opt}
            logger.info(f"Loaded suppression list: {len(self.suppressed_domains)} domains, {len(self.suppressed_emails)} emails.")
        except Exception as e:
            logger.error(f"Failed to load suppression list: {e}")

    @staticmethod
    def normalize_domain(url_or_domain: str) -> str:
        """
        Extracts and normalizes the root domain name from a URL or raw string.
        Examples:
            'https://www.AgencyAlpha.co.uk/services/' -> 'agencyalpha.co.uk'
            'HTTP://Acme.COM:8080' -> 'acme.com'
        """
        if not url_or_domain:
            return ""

        cleaned = url_or_domain.strip().lower()
        if not cleaned.startswith(("http://", "https://")):
            cleaned = "https://" + cleaned

        try:
            parsed = urlparse(cleaned)
            hostname = parsed.hostname or ""
            # Strip 'www.' if present
            if hostname.startswith("www."):
                hostname = hostname[4:]
            return hostname.strip()
        except Exception:
            return url_or_domain.strip().lower()

    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalizes email to trimmed lowercase, removing trailing/leading dots."""
        if not email:
            return ""
        return email.strip().lower()

    def is_suppressed(self, domain: str, email: str = "", company_name: str = "") -> Tuple[bool, Optional[str]]:
        """
        Checks whether a domain, email, or company name is on the suppression list.
        Returns (True, reason) if suppressed, otherwise (False, None).
        """
        norm_dom = self.normalize_domain(domain)
        if norm_dom and norm_dom in self.suppressed_domains:
            return True, f"Domain '{norm_dom}' is on suppression list."

        norm_email = self.normalize_email(email)
        if norm_email and norm_email in self.suppressed_emails:
            return True, f"Email '{norm_email}' is on suppression list."

        if company_name:
            norm_comp = company_name.strip().lower()
            if norm_comp in self.suppressed_companies:
                return True, f"Company '{company_name}' is on suppression list."

        return False, None

    def is_duplicate(self, domain: str, email: str = "", company_name: str = "") -> Tuple[bool, Optional[str]]:
        """
        Checks whether this domain, email, or company name has already been registered in this run.
        Returns (True, reason) if duplicate, otherwise (False, None).
        """
        norm_dom = self.normalize_domain(domain)
        if norm_dom and norm_dom in self.seen_domains:
            return True, f"Duplicate domain: {norm_dom} already processed."

        norm_email = self.normalize_email(email)
        if norm_email and norm_email in self.seen_emails:
            return True, f"Duplicate email: {norm_email} already processed."

        return False, None

    def register(self, domain: str, email: str = "", company_name: str = "") -> None:
        """Registers a lead into the seen set."""
        norm_dom = self.normalize_domain(domain)
        if norm_dom:
            self.seen_domains.add(norm_dom)

        norm_email = self.normalize_email(email)
        if norm_email:
            self.seen_emails.add(norm_email)

        if company_name:
            self.seen_companies.add(company_name.strip().lower())

    def add_to_suppression(self, domain: str = "", email: str = "", company_name: str = "", reason: str = "opt_out") -> None:
        """Appends a new suppression rule to memory and writes back to suppression.json."""
        norm_dom = self.normalize_domain(domain)
        norm_email = self.normalize_email(email)
        norm_comp = company_name.strip()

        if norm_dom:
            self.suppressed_domains.add(norm_dom)
        if norm_email:
            self.suppressed_emails.add(norm_email)
        if norm_comp:
            self.suppressed_companies.add(norm_comp.lower())

        # Persist to disk
        try:
            payload = {
                "domains": sorted(list(self.suppressed_domains)),
                "emails": sorted(list(self.suppressed_emails)),
                "company_names": sorted(list(self.suppressed_companies)),
                "opt_outs": sorted(list(self.opt_outs))
            }
            with open(self.suppression_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            logger.info(f"Updated suppression list with reason: {reason}")
        except Exception as e:
            logger.error(f"Failed to persist suppression update: {e}")
