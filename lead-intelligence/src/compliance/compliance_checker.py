"""
Compliance Checker Module
Implements country-specific legal assessment for US, UK, Canada, Australia, and European nations.
Enforces cautious compliance statuses: REVIEW_REQUIRED, RESTRICTED, ELIGIBILITY_NOT_ESTABLISHED, OPT_OUT_RECORDED.
Strict Rule: Public listing of an email does NOT equal marketing consent.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

CONSUMER_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "hotmail.com",
    "hotmail.co.uk", "outlook.com", "live.com", "msn.com", "icloud.com",
    "me.com", "mac.com", "aol.com", "proton.me", "protonmail.com", "zoho.com"
}


class ComplianceChecker:
    """
    Evaluates regulatory compliance requirements per lead jurisdiction and contact type.
    """

    def __init__(self, rules_path: Optional[str] = None):
        if rules_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            rules_path = str(base_dir / "config" / "compliance_rules.json")

        self.rules_path = Path(rules_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict[str, Any]:
        """Loads compliance rules JSON configuration."""
        if not self.rules_path.exists():
            logger.warning(f"Compliance rules file not found at {self.rules_path}. Using hardcoded fallback.")
            return {}

        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load compliance rules: {e}")
            return {}

    @staticmethod
    def is_consumer_email(email: str) -> bool:
        """Checks if an email belongs to a public consumer/free webmail provider."""
        if not email or "@" not in email:
            return False
        domain = email.strip().lower().split("@")[-1]
        return domain in CONSUMER_EMAIL_DOMAINS

    def evaluate(
        self,
        country: str,
        email: str = "",
        is_suppressed: bool = False,
        suppression_reason: Optional[str] = None,
        entity_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assesses the compliance profile for a given prospect.
        Returns a dictionary with status, legal framework, and mandatory pre-outreach review notes.
        """
        # 1. Suppression / Opt-out check
        if is_suppressed:
            return {
                "compliance_status": "OPT_OUT_RECORDED",
                "framework": "Internal Suppression Registry",
                "risk_tier": "PROHIBITED",
                "review_notes": [
                    "Prospect or domain is registered on the suppression list.",
                    f"Reason: {suppression_reason or 'Opt-out/DNC'}",
                    "Do not initiate any communication."
                ]
            }

        # 2. Consumer webmail check
        # Under GDPR, PECR, and international standards, consumer addresses cannot be contacted via B2B legitimate interest
        if email and self.is_consumer_email(email):
            return {
                "compliance_status": "RESTRICTED",
                "framework": "Consumer Protection & Privacy Laws",
                "risk_tier": "HIGH_RISK",
                "review_notes": [
                    "Detected consumer webmail provider (e.g. Gmail/Yahoo/Outlook personal).",
                    "B2B corporate subscriber exemptions do NOT apply to personal webmail.",
                    "Cold marketing outreach strictly prohibited without demonstrable prior consent."
                ]
            }

        # 3. Country code normalization
        norm_country = (country or "").strip().upper()
        if norm_country in ("UNITED KINGDOM", "ENGLAND", "SCOTLAND", "WALES", "GB"):
            norm_country = "UK"
        elif norm_country in ("UNITED STATES", "USA", "AMERICA"):
            norm_country = "US"
        elif norm_country in ("CANADA",):
            norm_country = "CA"
        elif norm_country in ("AUSTRALIA",):
            norm_country = "AU"
        elif norm_country in ("GERMANY", "DEUTSCHLAND"):
            norm_country = "DE"
        elif norm_country in ("AUSTRIA", "ÖSTERREICH"):
            norm_country = "AT"
        elif norm_country in ("FRANCE",):
            norm_country = "FR"
        elif norm_country in ("NETHERLANDS", "HOLLAND"):
            norm_country = "NL"

        profiles = self.rules.get("country_profiles", {})

        # 4. If country is missing or unrecognized
        if not norm_country or (norm_country not in profiles and norm_country not in ("EU", "OTHER_EU")):
            return {
                "compliance_status": "ELIGIBILITY_NOT_ESTABLISHED",
                "framework": "Unverified Jurisdiction",
                "risk_tier": "UNKNOWN",
                "review_notes": [
                    "Country of establishment could not be verified from public records.",
                    "Public availability of contact information does NOT constitute consent.",
                    "Must establish target jurisdiction and legal entity type before outreach."
                ]
            }

        profile = profiles.get(norm_country, profiles.get("OTHER_EU", {}))
        status = profile.get("default_status", "REVIEW_REQUIRED")
        framework = profile.get("framework", "International Data Protection Regulations")
        requirements = list(profile.get("requirements", []))

        # Always attach the universal principle
        requirements.append("Mandatory Reminder: Public email availability is NOT marketing consent.")

        risk_tier = "HIGH_RISK" if status == "RESTRICTED" else "MODERATE_REVIEW"

        return {
            "compliance_status": status,
            "framework": framework,
            "risk_tier": risk_tier,
            "review_notes": requirements
        }
