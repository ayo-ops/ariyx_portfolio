"""
Google Sheets Schema and Mapping Specification for Ariyx Lead Intelligence System.
Defines the 27-column structure, column ownership boundaries, domain normalization,
and bidirectional conversion between local lead exports and spreadsheet rows.

Column Ownership Boundaries:
- Columns A-U (System-Managed, indices 0-20): Automatically updated from research data.
- Columns V-AA (Operator-Managed, indices 21-26): Preserved in place; never overwritten by sync.
  Column V ("Campaign Status") is initialized to "Ready for Manual Review" upon row insertion.
"""

import csv
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# System-Managed Columns (A-U: Indices 0-20)
SYSTEM_COLUMNS: List[str] = [
    "Lead ID",                          # Col A
    "Date Researched",                  # Col B
    "Business Name",                    # Col C
    "Website URL",                      # Col D
    "Industry & Sub-niche",             # Col E
    "Country & City",                   # Col F
    "Decision-Maker Full Name",         # Col G
    "Job Title",                        # Col H
    "Public Business Email",            # Col I
    "Email Verification Status",        # Col J
    "Public Business Phone",            # Col K
    "Decision-Maker LinkedIn URL",      # Col L
    "Company LinkedIn URL",             # Col M
    "Company Sizing",                   # Col N
    "Business Description",             # Col O
    "Potential Buying Signals",         # Col P
    "Ariyx Fit Hypothesis",             # Col Q
    "Source URLs & Evidence",           # Col R
    "Lead Qualification Score",         # Col S
    "Qualification Tier",               # Col T
    "Compliance Status",                # Col U
]

# Operator-Managed Columns (V-AA: Indices 21-26)
OPERATOR_COLUMNS: List[str] = [
    "Campaign Status",                  # Col V (Initialized to 'Ready for Manual Review')
    "Assigned Rep",                     # Col W
    "Outreach Channel",                 # Col X
    "Outreach Date",                    # Col Y
    "Prospect Response",                # Col Z
    "Manual Notes",                     # Col AA
]

# Insertion Columns (A-V: Indices 0-21, exactly 22 columns)
# New records write strictly to A-V; Columns W-AA are reserved for manual entry.
INSERT_COLUMNS: List[str] = SYSTEM_COLUMNS + ["Campaign Status"]

# Complete 27-Column Schema
ALL_COLUMNS: List[str] = SYSTEM_COLUMNS + OPERATOR_COLUMNS

# Optional Segmented Outreach & Apps Script Tracking Columns (AB-AG: Indices 27-32)
# Placed right of Column AA so Columns A-U and V-AA ownership boundaries stay untouched.
OUTREACH_TRACKING_COLUMNS: List[str] = [
    "Outreach Segment",           # Col AB (auto-assigned segment on accepted insert / Apps Script)
    "Assigned Template ID",       # Col AC (populated when operator selects/runs template)
    "Sequence Step",              # Col AD
    "Last Email Sent At",         # Col AE
    "Gmail Thread ID",            # Col AF
    "Delivery & Opt-Out Status",  # Col AG
]

# Auxiliary Tabs in 'Ariyx Systems – Outbound Intelligence Hub'
EMAIL_TEMPLATE_COLUMNS: List[str] = [
    "Template ID",
    "Template Name",
    "Outreach Segment",
    "Target Tier Filter",
    "Subject Template",
    "Plain Text Body",
    "HTML Body",
    "Active",
    "Daily Cap",
    "Compliance & Review Notes",
]

DAILY_RUN_LOG_COLUMNS: List[str] = [
    "Run Date",
    "Campaign Day",
    "Run Status",
    "Target Accepted",
    "Accepted Count",
    "Research Attempts",
    "Rejected Candidates",
    "Decision-Makers Found",
    "Verified Emails",
    "Unverified / Inconclusive",
    "Duplicates Prevented",
    "Sheets Inserted",
    "Completion %",
    "Primary Blockers",
]

SUPPRESSION_LOG_COLUMNS: List[str] = [
    "Recorded At",
    "Domain",
    "Email",
    "Company Name",
    "Source",
    "Reason",
    "Processed Locally",
]

# Column letters mapping
COLUMN_LETTERS: List[str] = [
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z", "AA"
]


def normalize_domain(url_or_domain: Optional[str]) -> str:
    """
    Normalizes a URL or domain string into a clean, lowercased canonical domain.
    Strips protocols, www prefix, paths, queries, fragments, ports, and trailing slashes.

    Examples:
        'https://www.DirectiveConsulting.com/contact/' -> 'directiveconsulting.com'
        'http://ironpaper.com:8080'                    -> 'ironpaper.com'
        'ignitedigital.com'                            -> 'ignitedigital.com'
    """
    if not url_or_domain:
        return ""

    raw = str(url_or_domain).strip().lower()
    if not raw:
        return ""

    # Prepend http:// if scheme missing for urlparse to parse netloc accurately
    if not (raw.startswith("http://") or raw.startswith("https://")):
        raw = f"http://{raw}"

    try:
        parsed = urlparse(raw)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Strip port if present
        if ":" in domain:
            domain = domain.split(":")[0]
        # Strip leading www.
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.strip()
    except Exception:
        # Fallback regex extraction
        cleaned = re.sub(r"^https?://", "", raw)
        cleaned = re.sub(r"^www\.", "", cleaned)
        return cleaned.split("/")[0].split(":")[0].strip()


def validate_lead_record(lead: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates that a lead record contains the necessary minimum fields for synchronization.
    Returns (is_valid, list_of_errors).
    """
    errors: List[str] = []

    lead_id = lead.get("Lead ID") or lead.get("lead_id")
    if not lead_id or str(lead_id).strip() == "":
        errors.append("Missing required Lead ID")

    website = lead.get("Website URL") or lead.get("Website") or lead.get("website")
    domain = lead.get("domain") or normalize_domain(website)
    if not website and not domain:
        errors.append("Missing required Website URL or Domain")

    score = lead.get("Lead Qualification Score")
    if score is None:
        score = lead.get("lead_score")
    if score is None:
        errors.append("Missing Lead Qualification Score")

    tier = lead.get("Qualification Tier") or lead.get("qualification_tier")
    if not tier:
        errors.append("Missing Qualification Tier")

    return (len(errors) == 0, errors)


def format_system_row(lead: Dict[str, Any]) -> List[Any]:
    """
    Formats a lead record dictionary into exactly 21 values corresponding
    to Columns A-U (System-Managed).
    """
    # Helper to resolve field from multiple candidate keys
    def get_val(*keys, default="Unavailable"):
        for k in keys:
            v = lead.get(k)
            if v is not None and str(v).strip() != "":
                return v
        return default

    lead_id = get_val("Lead ID", "lead_id", default="")
    date_researched = get_val("Date Researched", "date_researched", default="")
    business_name = get_val("Business Name", "business_name", default="Unavailable")
    website = get_val("Website URL", "Website", "website", default="")
    industry = get_val("Industry & Sub-niche", "industry", default="Unavailable")

    # Country & City
    country_city = lead.get("Country & City")
    if not country_city:
        country = lead.get("country", "")
        city = lead.get("city", "")
        country_city = f"{country}, {city}".strip(", ") if (country or city) else "Unavailable"

    decision_maker_name = get_val("Decision-Maker Full Name", "decision_maker_name", default="Unavailable")
    job_title = get_val("Job Title", "decision_maker_title", default="Unavailable")
    
    # Column I: Public Business Email (Never implied verified without evidence)
    email = get_val("Public Business Email", "Verified Business Email", "verified_email", "public_business_email", default="Unavailable")
    
    # Column J: Email Verification Status
    email_status = get_val("Email Verification Status", "email_verification_status", default="Unavailable")
    
    phone = get_val("Public Business Phone", "formatted_phone", default="Unavailable")
    dm_linkedin = get_val("Decision-Maker LinkedIn URL", "decision_maker_linkedin", default="Unavailable")
    comp_linkedin = get_val("Company LinkedIn URL", "company_linkedin", default="Unavailable")
    sizing = get_val("Company Sizing", "Company Size / Estimated Employees", "estimated_employees", default="Unavailable")
    description = get_val("Business Description", "business_description", default="Unavailable")

    # Potential Buying Signals summary
    signals_val = lead.get("Potential Buying Signals")
    if signals_val is None:
        raw_signals = lead.get("potential_buying_signals", [])
        if isinstance(raw_signals, list) and raw_signals:
            signals_val = " | ".join([
                f"[{s.get('signal_type')}]: {s.get('description')}" 
                for s in raw_signals if isinstance(s, dict)
            ])
        else:
            signals_val = "None observed"

    hypothesis = get_val("Ariyx Fit Hypothesis", "fit_hypothesis", default="Unavailable")

    # Source URLs & Evidence summary (mirrors LocalStore._format_row rich proof format)
    evidence_val = lead.get("Source URLs & Evidence")
    if evidence_val is None:
        evidence_items: List[str] = []
        if lead.get("page_title") and lead.get("page_title") != "Unavailable":
            evidence_items.append(f"[Page Title Metadata]: {lead.get('page_title')}")

        if lead.get("employee_source_url"):
            evidence_items.append(
                f"[Employee Evidence]: {lead.get('estimated_employees')} "
                f"({lead.get('employee_status', 'Estimate')}) "
                f"(Source: {lead.get('employee_source_url')})"
            )

        if lead.get("decision_maker_name") and lead.get("decision_maker_name") != "Unavailable":
            dm_proof = (
                f"[DM Proof]: {lead.get('decision_maker_name')} "
                f"({lead.get('decision_maker_title')}) - "
                f"{lead.get('decision_maker_evidence', 'DOM Verified')} "
                f"(Source: {lead.get('decision_maker_source_url', website)})"
            )
            evidence_items.append(dm_proof)

        raw_signals_for_ev = lead.get("potential_buying_signals", [])
        if isinstance(raw_signals_for_ev, list):
            for s in raw_signals_for_ev:
                if isinstance(s, dict) and (s.get("evidence") or s.get("source_url")):
                    evidence_items.append(
                        f"[Signal Proof]: {s.get('evidence', '')} (Source: {s.get('source_url', '')})"
                    )

        if lead.get("research_status") and lead.get("research_status") != "COMPLETED":
            evidence_items.append(f"[Research Notice]: {lead.get('research_status')}")

        if evidence_items:
            evidence_val = " | ".join(evidence_items)
        else:
            raw_evidence = lead.get("evidence_urls", [])
            if isinstance(raw_evidence, list) and raw_evidence:
                evidence_val = " | ".join([str(e) for e in raw_evidence])
            else:
                evidence_val = website or "Unavailable"

    # Qualification score and tier
    score_raw = lead.get("Lead Qualification Score")
    if score_raw is None:
        score_raw = lead.get("lead_score", 0)
    try:
        score = int(score_raw)
    except (ValueError, TypeError):
        score = 0

    tier = get_val("Qualification Tier", "qualification_tier", default="Needs Further Research")
    compliance = get_val("Compliance Status", "compliance_status", default="ELIGIBILITY_NOT_ESTABLISHED")

    return [
        str(lead_id),               # Col A
        str(date_researched),       # Col B
        str(business_name),         # Col C
        str(website),               # Col D
        str(industry),              # Col E
        str(country_city),          # Col F
        str(decision_maker_name),   # Col G
        str(job_title),             # Col H
        str(email),                 # Col I
        str(email_status),          # Col J
        str(phone),                 # Col K
        str(dm_linkedin),           # Col L
        str(comp_linkedin),         # Col M
        str(sizing),                # Col N
        str(description),           # Col O
        str(signals_val),           # Col P
        str(hypothesis),            # Col Q
        str(evidence_val),          # Col R
        score,                      # Col S
        str(tier),                  # Col T
        str(compliance),            # Col U
    ]


def format_insert_row(
    lead: Dict[str, Any], 
    initial_campaign_status: str = "Ready for Manual Review"
) -> List[Any]:
    """
    Formats a new lead record strictly covering Columns A-V (exactly 22 columns).
    Columns A-U: System-managed fields (21 items).
    Column V: Initialized to initial_campaign_status ('Ready for Manual Review', 1 item).
    Columns W-AA (indices 22-26) are NEVER included in the insert payload,
    ensuring they are reserved strictly for manual operator entry and never overwritten.
    """
    system_row = format_system_row(lead)  # exactly 21 items
    return system_row + [initial_campaign_status]  # exactly 22 items (Columns A-V)


def format_full_row(
    lead: Dict[str, Any], 
    initial_campaign_status: str = "Ready for Manual Review"
) -> List[Any]:
    """
    Formats a full 27-column row representation (for testing or full row inspections).
    Columns A-V: Insert payload (22 items).
    Columns W-AA: Operator fields initialized to empty string (5 items).
    """
    return format_insert_row(lead, initial_campaign_status=initial_campaign_status) + ["", "", "", "", ""]


def load_export_file(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Loads an export file (JSON or CSV) and normalizes each record into a standardized dictionary.
    Includes canonical 'domain' field on every record.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Export file not found: {path}")

    leads: List[Dict[str, Any]] = []

    if path.suffix.lower() == ".json":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                raise ValueError(f"JSON export must contain an array of lead objects, got {type(data).__name__}")
            for item in data:
                if isinstance(item, dict):
                    website = item.get("website") or item.get("Website URL") or item.get("Website", "")
                    domain = item.get("domain") or normalize_domain(website)
                    record = dict(item)
                    record["domain"] = domain
                    record["Lead ID"] = record.get("Lead ID") or record.get("lead_id", "")
                    record["Website URL"] = website
                    record["Business Name"] = record.get("Business Name") or record.get("business_name", "")
                    leads.append(record)

    elif path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                website = row.get("Website URL") or row.get("Website", "")
                domain = normalize_domain(website)
                record = dict(row)
                record["domain"] = domain
                record["Lead ID"] = record.get("Lead ID", "")
                record["Website URL"] = website
                record["Business Name"] = record.get("Business Name", "")
                leads.append(record)
    else:
        raise ValueError(f"Unsupported export file extension: {path.suffix}. Expected .json or .csv")

    return leads
