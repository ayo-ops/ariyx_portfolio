"""
Local Storage and Exporter Module
Saves researched batches to structured JSON and CSV in data/exports/.
Adheres strictly to the standardized 22-column schema.
"""

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

SCHEMA_COLUMNS = [
    "Lead ID",
    "Date Researched",
    "Business Name",
    "Website",
    "Industry & Sub-niche",
    "Country & City",
    "Decision-Maker Full Name",
    "Job Title",
    "Public Business Email",
    "Email Verification Status",
    "Public Business Phone",
    "Decision-Maker LinkedIn URL",
    "Company LinkedIn URL",
    "Company Size / Estimated Employees",
    "Business Description",
    "Potential Buying Signals",
    "Ariyx Fit Hypothesis",
    "Source URLs & Evidence",
    "Lead Qualification Score",
    "Qualification Tier",
    "Compliance Status",
    "Campaign Status"
]


class LocalStore:
    """
    Persists qualified lead intelligence batches to disk in CSV and JSON formats.
    """

    def __init__(self, exports_dir: Optional[str] = None):
        if exports_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            exports_dir = str(base_dir / "data" / "exports")
        self.exports_dir = Path(exports_dir)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def save_batch(self, leads: List[Dict[str, Any]], batch_name: str = "batch") -> Dict[str, str]:
        """
        Exports leads to both JSON and CSV files.
        Returns paths to the generated files.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_file = self.exports_dir / f"{batch_name}_{timestamp}.json"
        csv_file = self.exports_dir / f"{batch_name}_{timestamp}.csv"

        # 1. Save Full JSON
        try:
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON export: {json_file}")
        except Exception as e:
            logger.error(f"Failed to save JSON export: {e}")

        # 2. Save Standardized 22-Column CSV
        try:
            with open(csv_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=SCHEMA_COLUMNS)
                writer.writeheader()
                for lead in leads:
                    row = self._format_row(lead)
                    writer.writerow(row)
            logger.info(f"Saved CSV export: {csv_file}")
        except Exception as e:
            logger.error(f"Failed to save CSV export: {e}")

        return {
            "json_path": str(json_file),
            "csv_path": str(csv_file)
        }

    def _format_row(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """Maps an internal lead dictionary to the 22-column schema."""
        country = lead.get("country", "")
        city = lead.get("city", "")
        country_city = f"{country}, {city}".strip(", ") if (country or city) else "Unavailable"

        # Format buying signals summary
        signals = lead.get("potential_buying_signals", [])
        signals_text = " | ".join([f"[{s.get('signal_type')}]: {s.get('description')}" for s in signals]) if signals else "None observed"

        # Format evidence URLs and proof
        evidence_items = []
        if lead.get("page_title") and lead.get("page_title") != "Unavailable":
            evidence_items.append(f"[Page Title Metadata]: {lead.get('page_title')}")

        if lead.get("employee_source_url"):
            evidence_items.append(f"[Employee Evidence]: {lead.get('estimated_employees')} ({lead.get('employee_status', 'Estimate')}) (Source: {lead.get('employee_source_url')})")

        if lead.get("decision_maker_name") and lead.get("decision_maker_name") != "Unavailable":
            dm_proof = f"[DM Proof]: {lead.get('decision_maker_name')} ({lead.get('decision_maker_title')}) - {lead.get('decision_maker_evidence', 'DOM Verified')} (Source: {lead.get('decision_maker_source_url', lead.get('website'))})"
            evidence_items.append(dm_proof)

        for s in signals:
            sig_proof = f"[Signal Proof]: {s.get('evidence', '')} (Source: {s.get('source_url', '')})"
            evidence_items.append(sig_proof)

        if lead.get("research_status") and lead.get("research_status") != "COMPLETED":
            evidence_items.append(f"[Research Notice]: {lead.get('research_status')}")

        evidence_text = " | ".join(evidence_items) if evidence_items else lead.get("website", "")

        return {
            "Lead ID": lead.get("lead_id", ""),
            "Date Researched": lead.get("date_researched", datetime.now(timezone.utc).strftime("%Y-%m-%d")),
            "Business Name": lead.get("business_name", "Unavailable"),
            "Website": lead.get("website", ""),
            "Industry & Sub-niche": lead.get("industry", "Unavailable"),
            "Country & City": country_city,
            "Decision-Maker Full Name": lead.get("decision_maker_name", "Unavailable"),
            "Job Title": lead.get("decision_maker_title", "Unavailable"),
            "Public Business Email": lead.get("verified_email") or lead.get("public_business_email") or "Unavailable",
            "Email Verification Status": lead.get("email_verification_status", "Unavailable"),
            "Public Business Phone": lead.get("formatted_phone", "Unavailable"),
            "Decision-Maker LinkedIn URL": lead.get("decision_maker_linkedin", "Unavailable"),
            "Company LinkedIn URL": lead.get("company_linkedin", "Unavailable"),
            "Company Size / Estimated Employees": lead.get("estimated_employees", "Unavailable"),
            "Business Description": lead.get("business_description", "Unavailable"),
            "Potential Buying Signals": signals_text,
            "Ariyx Fit Hypothesis": lead.get("fit_hypothesis", "Unavailable"),
            "Source URLs & Evidence": evidence_text,
            "Lead Qualification Score": lead.get("lead_score", 0),
            "Qualification Tier": lead.get("qualification_tier", "Needs Further Research"),
            "Compliance Status": lead.get("compliance_status", "ELIGIBILITY_NOT_ESTABLISHED"),
            "Campaign Status": lead.get("campaign_status", "Ready for Manual Review")
        }
