"""
Google Sheets Synchronization Engine for Ariyx Lead Intelligence System.
Implements the 27-column structure, column protection (A-U vs V-AA),
offline --dry-run, read-only --live-preview, and the 5-case matching table.

Security and Integrity Constraints:
1. Column Protection:
   - System fields (Columns A-U, indices 0-20) are updated from research data.
   - Operator fields (Columns V-AA, indices 21-26) are NEVER overwritten on update.
   - New records initialize Column V ("Campaign Status") to "Ready for Manual Review".
2. Five-Case Matching Table:
   - Case 1: Both Lead ID and domain match the same row -> UPDATE row (range A{row}:U{row}).
   - Case 2: Neither Lead ID nor domain matches -> INSERT / APPEND new row.
   - Case 3: Only Lead ID matches -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW (quarantine).
   - Case 4: Only domain matches -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW (quarantine).
   - Case 5: Both match different rows -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW (quarantine).
   - Never automatically merge or overwrite ambiguous records.
3. Offline & Preview Modes:
   - --dry-run: 100% offline. Zero network calls, zero credentials required.
   - --live-preview: Read-only Google Sheets inspection. Zero write calls.
"""

import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.scoring.acceptance_evaluator import AcceptanceEvaluator, assign_outreach_segment
from src.storage.sheet_schema import (
    ALL_COLUMNS,
    DAILY_RUN_LOG_COLUMNS,
    EMAIL_TEMPLATE_COLUMNS,
    INSERT_COLUMNS,
    OPERATOR_COLUMNS,
    OUTREACH_TRACKING_COLUMNS,
    SUPPRESSION_LOG_COLUMNS,
    SYSTEM_COLUMNS,
    format_full_row,
    format_insert_row,
    format_system_row,
    load_export_file,
    normalize_domain,
    validate_lead_record,
)

logger = logging.getLogger(__name__)

# Strictly scoped to Google Sheets API only (Drive API not used or requested)
SHEETS_API_SCOPES: List[str] = ["https://www.googleapis.com/auth/spreadsheets"]
PLACEHOLDER_SPREADSHEET_IDS = {"", "your_spreadsheet_id_here", "<spreadsheet_id>"}


def read_local_env(env_path: Optional[Union[str, Path]] = None) -> Dict[str, str]:
    """
    Safely parses a local .env configuration file into a dictionary without
    mutating global os.environ and without logging or exposing sensitive values.
    """
    target = Path(env_path) if env_path is not None else (Path(__file__).resolve().parent.parent.parent / ".env")
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
            if len(val) >= 2 and (
                (val.startswith('"') and val.endswith('"'))
                or (val.startswith("'") and val.endswith("'"))
            ):
                val = val[1:-1].strip()
            if key and val:
                values[key] = val
    except OSError:
        logger.warning("Could not read local .env configuration file.")

    return values


@dataclass
class PlannedAction:
    lead_id: str
    business_name: str
    domain: str
    action_type: str  # 'UPDATE', 'INSERT', 'AMBIGUOUS_MATCH_MANUAL_REVIEW'
    case_number: int  # 1, 2, 3, 4, 5
    target_row: Optional[int] = None
    target_range: Optional[str] = None
    reason: str = ""
    system_payload: Optional[List[Any]] = None
    insert_payload: Optional[List[Any]] = None  # Exactly 22 items (Columns A-V)
    full_payload: Optional[List[Any]] = None    # Kept for compatibility
    preserved_operator_values: Optional[List[Any]] = None
    outreach_segment: str = "UNASSIGNED"


@dataclass
class ActionPlan:
    file_path: str
    total_leads: int
    valid_leads: int
    invalid_leads: int
    validation_errors: List[Dict[str, Any]] = field(default_factory=list)
    intra_batch_duplicates: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[PlannedAction] = field(default_factory=list)
    ambiguous_records: List[PlannedAction] = field(default_factory=list)
    rejected_unaccepted: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)


class SheetSyncer:
    """
    Manages synchronization between local Ariyx lead intelligence batches
    and the 'Outbound Leads Intelligence' Google Sheet tab.
    """

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
        worksheet_name: Optional[str] = None,
        client: Optional[Any] = None,
        worksheet: Optional[Any] = None,
        load_env: bool = True,
        env_path: Optional[Union[str, Path]] = None,
    ):
        local_env = read_local_env(env_path=env_path) if load_env else {}

        raw_cred_json = (
            os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
            or os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
            or local_env.get("GOOGLE_SERVICE_ACCOUNT_JSON")
            or local_env.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
        )
        self.credentials_json = raw_cred_json.strip() if (raw_cred_json and raw_cred_json.strip()) else None

        raw_cred = credentials_path if credentials_path is not None else (
            os.getenv("GOOGLE_SHEETS_CREDENTIALS_PATH") or local_env.get("GOOGLE_SHEETS_CREDENTIALS_PATH")
        )
        self.credentials_path = (
            os.path.expandvars(os.path.expanduser(raw_cred.strip()))
            if (raw_cred and raw_cred.strip())
            else None
        )

        raw_sheet_id = spreadsheet_id if spreadsheet_id is not None else (
            os.getenv("SPREADSHEET_ID") or local_env.get("SPREADSHEET_ID")
        )
        cleaned_sheet_id = raw_sheet_id.strip() if raw_sheet_id else ""
        self.spreadsheet_id = None if cleaned_sheet_id.lower() in PLACEHOLDER_SPREADSHEET_IDS else cleaned_sheet_id

        raw_ws_name = worksheet_name if worksheet_name is not None else (
            os.getenv("WORKSHEET_NAME") or local_env.get("WORKSHEET_NAME")
        )
        self.worksheet_name = (
            raw_ws_name.strip()
            if (raw_ws_name and raw_ws_name.strip())
            else "Outbound Leads Intelligence"
        )

        self.scopes = list(SHEETS_API_SCOPES)
        self._client = client
        self._worksheet = worksheet

    def _get_client(self) -> Any:
        """
        Authenticates and returns a Google Sheets client using ONLY the
        https://www.googleapis.com/auth/spreadsheets scope.
        Supports both in-memory GOOGLE_SERVICE_ACCOUNT_JSON (for GitHub Actions Secrets)
        and local GOOGLE_SHEETS_CREDENTIALS_PATH.
        Never reads, prints, logs, or exposes JSON credential contents.
        """
        if self._client is not None:
            return self._client

        # Lazy import of gspread to allow offline operation without imports failing
        try:
            import gspread
        except ImportError:
            raise ImportError("gspread is required for live Google Sheets integration. Run: pip install gspread")

        if not self.spreadsheet_id:
            raise ValueError(
                "Missing SPREADSHEET_ID. Enter your Spreadsheet ID in lead-intelligence/.env "
                "or your GitHub Actions Secrets without sharing it in source code or Git."
            )

        if self.credentials_json:
            try:
                import json
                cred_info = json.loads(self.credentials_json)
                self._client = gspread.service_account_from_dict(
                    info=cred_info,
                    scopes=self.scopes,
                )
                return self._client
            except Exception as exc:
                raise ValueError(f"Invalid Google Service Account JSON provided in environment: {exc}")

        if not self.credentials_path:
            raise ValueError(
                "Missing Google Service Account credentials. Set GOOGLE_SERVICE_ACCOUNT_JSON in environment/secrets "
                "or GOOGLE_SHEETS_CREDENTIALS_PATH in lead-intelligence/.env. For offline testing, use --dry-run."
            )

        cred_path = Path(self.credentials_path)
        if not cred_path.exists():
            raise FileNotFoundError(
                f"Google Service Account key not found at: {cred_path}. "
                "Ensure credentials are saved in the protected user profile directory."
            )

        # Explicitly enforce ONLY Google Sheets API scope (never request Google Drive scope)
        self._client = gspread.service_account(
            filename=str(cred_path),
            scopes=self.scopes,
        )
        return self._client

    def _get_worksheet(self, read_only: bool = True) -> Any:
        """
        Connects to Google Sheets via gspread and returns the target worksheet.
        Injectable via constructor for testing without network dependencies.
        """
        if self._worksheet is not None:
            return self._worksheet

        client = self._get_client()
        if not self.spreadsheet_id:
            raise ValueError(
                "Missing SPREADSHEET_ID. Enter your Spreadsheet ID in lead-intelligence/.env "
                "or your local environment variables."
            )

        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            worksheet = spreadsheet.worksheet(self.worksheet_name)
        except Exception as exc:
            if type(exc).__name__ == "WorksheetNotFound":
                if not read_only:
                    # Create worksheet if missing and authorized
                    worksheet = spreadsheet.add_worksheet(title=self.worksheet_name, rows=1000, cols=27)
                    worksheet.update(range_name="A1:AA1", values=[ALL_COLUMNS])
                else:
                    raise ValueError(
                        f"Worksheet '{self.worksheet_name}' does not exist yet in the target spreadsheet."
                    ) from exc
            else:
                raise

        self._worksheet = worksheet
        return self._worksheet

    def check_connection(self) -> Dict[str, Any]:
        """
        READ-ONLY CONNECTION TEST.
        Verifies credentials path, SPREADSHEET_ID, and Google Sheets API read access
        using ONLY https://www.googleapis.com/auth/spreadsheets.
        Does NOT create tabs, write cells, import leads, or expose credentials/IDs.
        """
        client = self._get_client()
        if not self.spreadsheet_id:
            raise ValueError(
                "Missing SPREADSHEET_ID. Enter your Spreadsheet ID in lead-intelligence/.env "
                "or your local environment variables."
            )

        spreadsheet = client.open_by_key(self.spreadsheet_id)
        worksheets = spreadsheet.worksheets()
        tab_names = [ws.title for ws in worksheets]
        target_exists = self.worksheet_name in tab_names

        target_row_count = None
        target_headers_present = None
        if target_exists:
            ws = spreadsheet.worksheet(self.worksheet_name)
            first_row = ws.row_values(1)
            target_row_count = ws.row_count
            target_headers_present = (first_row[:len(ALL_COLUMNS)] == ALL_COLUMNS)

        return {
            "status": "CONNECTED_READ_ONLY",
            "spreadsheet_title": spreadsheet.title,
            "scopes": list(self.scopes),
            "target_worksheet": self.worksheet_name,
            "target_worksheet_exists": target_exists,
            "available_worksheets": tab_names,
            "target_headers_initialized": target_headers_present,
            "worksheet_row_capacity": target_row_count,
        }

    def parse_existing_sheet_rows(self, raw_rows: List[List[str]]) -> List[Dict[str, Any]]:
        """
        Parses raw row data from Google Sheets into structured index objects.
        Row 1 is assumed to be the header row.
        Data rows start at row 2 (1-based spreadsheet row numbers).
        """
        parsed: List[Dict[str, Any]] = []
        if not raw_rows or len(raw_rows) <= 1:
            return parsed

        for idx, row in enumerate(raw_rows[1:], start=2):
            # Safe column extraction with fallback for short rows
            lead_id = row[0].strip() if len(row) > 0 and row[0] else ""
            website = row[3].strip() if len(row) > 3 and row[3] else ""
            domain = normalize_domain(website)
            business_name = row[2].strip() if len(row) > 2 and row[2] else ""
            email = row[8].strip().lower() if len(row) > 8 and row[8] else ""

            # Extract operator columns (Cols V-AA: indices 21-26)
            operator_values: List[str] = []
            for col_idx in range(21, 27):
                if len(row) > col_idx:
                    operator_values.append(row[col_idx])
                else:
                    operator_values.append("")

            parsed.append({
                "row_number": idx,
                "lead_id": lead_id,
                "website": website,
                "domain": domain,
                "email": email,
                "business_name": business_name,
                "operator_values": operator_values,
                "raw": row
            })

        return parsed

    def evaluate_batch(
        self,
        leads: List[Dict[str, Any]],
        existing_rows: List[Dict[str, Any]],
        file_path: str = "",
        strict_accepted_only: bool = False,
        acceptance_evaluator: Optional[AcceptanceEvaluator] = None,
    ) -> ActionPlan:
        """
        Core evaluation engine implementing the Five-Case Matching Table,
        intra-batch duplicate detection, and optional strict acceptance gating.
        """
        evaluator = acceptance_evaluator or AcceptanceEvaluator()
        plan = ActionPlan(
            file_path=file_path,
            total_leads=len(leads),
            valid_leads=0,
            invalid_leads=0,
            summary={
                "case_1_updates": 0,
                "case_2_inserts": 0,
                "case_3_ambiguous_id_only": 0,
                "case_4_ambiguous_domain_only": 0,
                "case_5_ambiguous_cross_match": 0,
                "other_ambiguous": 0,
                "total_ambiguous": 0,
                "rejected_unaccepted": 0,
            }
        )

        # 1. Intra-batch duplicate & validation check
        seen_lead_ids: Dict[str, int] = {}
        seen_domains: Dict[str, int] = {}
        valid_lead_list: List[Dict[str, Any]] = []

        for idx, lead in enumerate(leads, start=1):
            is_valid, errors = validate_lead_record(lead)
            if not is_valid:
                plan.invalid_leads += 1
                plan.validation_errors.append({
                    "batch_index": idx,
                    "lead": lead.get("Lead ID") or lead.get("lead_id", "Unknown"),
                    "errors": errors
                })
                continue

            if strict_accepted_only:
                decision = evaluator.evaluate(lead)
                if not decision.accepted:
                    plan.summary["rejected_unaccepted"] += 1
                    plan.rejected_unaccepted.append({
                        "batch_index": idx,
                        "lead_id": str(lead.get("Lead ID") or lead.get("lead_id", "")),
                        "business_name": str(lead.get("Business Name") or lead.get("business_name", "Unknown")),
                        "domain": normalize_domain(lead.get("domain") or lead.get("website") or lead.get("Website URL") or ""),
                        "blocker_codes": decision.blocker_codes,
                        "blocking_reasons": decision.blocking_reasons,
                    })
                    continue

            plan.valid_leads += 1
            lead_id = str(lead.get("Lead ID") or lead.get("lead_id", "")).strip()
            website = lead.get("Website URL") or lead.get("Website") or lead.get("website", "")
            domain = normalize_domain(lead.get("domain") or website)

            # Intra-batch duplicate checks
            if lead_id and lead_id in seen_lead_ids:
                plan.intra_batch_duplicates.append({
                    "batch_index": idx,
                    "type": "DUPLICATE_LEAD_ID",
                    "value": lead_id,
                    "previous_index": seen_lead_ids[lead_id]
                })
            elif lead_id:
                seen_lead_ids[lead_id] = idx

            if domain and domain in seen_domains:
                plan.intra_batch_duplicates.append({
                    "batch_index": idx,
                    "type": "DUPLICATE_DOMAIN",
                    "value": domain,
                    "previous_index": seen_domains[domain]
                })
            elif domain:
                seen_domains[domain] = idx

            valid_lead_list.append(lead)

        # 2. Build index of existing rows in spreadsheet
        highest_row = 1
        for er in existing_rows:
            if er["row_number"] > highest_row:
                highest_row = er["row_number"]

        next_append_row = highest_row + 1

        # 3. Apply Five-Case Matching Table
        for lead in valid_lead_list:
            lead_id = str(lead.get("Lead ID") or lead.get("lead_id", "")).strip()
            business_name = lead.get("Business Name") or lead.get("business_name", "Unavailable")
            website = lead.get("Website URL") or lead.get("Website") or lead.get("website", "")
            domain = normalize_domain(lead.get("domain") or website)

            matched_id_rows = [r for r in existing_rows if r["lead_id"] and r["lead_id"] == lead_id]
            matched_domain_rows = [r for r in existing_rows if r["domain"] and r["domain"] == domain]

            system_row = format_system_row(lead)
            segment = lead.get("outreach_segment") or assign_outreach_segment(lead)

            # Case 1: Both Lead ID and domain match the SAME row
            if (
                len(matched_id_rows) == 1
                and len(matched_domain_rows) == 1
                and matched_id_rows[0]["row_number"] == matched_domain_rows[0]["row_number"]
            ):
                target_row = matched_id_rows[0]["row_number"]
                preserved_ops = matched_id_rows[0].get("operator_values", ["", "", "", "", "", ""])
                action = PlannedAction(
                    lead_id=lead_id,
                    business_name=business_name,
                    domain=domain,
                    action_type="UPDATE",
                    case_number=1,
                    target_row=target_row,
                    target_range=f"A{target_row}:U{target_row}",
                    reason=f"Lead ID and Domain match row {target_row}. Update system fields A-U in place.",
                    system_payload=system_row,
                    preserved_operator_values=preserved_ops,
                    outreach_segment=segment,
                )
                plan.actions.append(action)
                plan.summary["case_1_updates"] += 1

            # Case 2: Neither Lead ID nor domain matches any existing row
            elif len(matched_id_rows) == 0 and len(matched_domain_rows) == 0:
                target_row = next_append_row
                insert_row = format_insert_row(lead)  # exactly 22 items (Columns A-V)
                action = PlannedAction(
                    lead_id=lead_id,
                    business_name=business_name,
                    domain=domain,
                    action_type="INSERT",
                    case_number=2,
                    target_row=target_row,
                    target_range=f"A{target_row}:V{target_row}",
                    reason=f"New Lead. Neither Lead ID nor Domain exists. Insert at row {target_row} (Columns A-V only, W-AA untouched).",
                    system_payload=system_row,
                    insert_payload=insert_row,
                    full_payload=insert_row,
                    outreach_segment=segment,
                )
                plan.actions.append(action)
                plan.summary["case_2_inserts"] += 1
                next_append_row += 1

            # Case 3: Only Lead ID matches
            elif len(matched_id_rows) == 1 and len(matched_domain_rows) == 0:
                matched_row = matched_id_rows[0]["row_number"]
                existing_dom = matched_id_rows[0]["domain"]
                reason = (
                    f"AMBIGUOUS MATCH (Case 3): Lead ID '{lead_id}' matches row {matched_row}, "
                    f"but incoming domain '{domain}' does not match existing sheet domain '{existing_dom}'."
                )
                action = PlannedAction(
                    lead_id=lead_id,
                    business_name=business_name,
                    domain=domain,
                    action_type="AMBIGUOUS_MATCH_MANUAL_REVIEW",
                    case_number=3,
                    target_row=matched_row,
                    reason=reason,
                )
                plan.actions.append(action)
                plan.ambiguous_records.append(action)
                plan.summary["case_3_ambiguous_id_only"] += 1
                plan.summary["total_ambiguous"] += 1

            # Case 4: Only Domain matches
            elif len(matched_id_rows) == 0 and len(matched_domain_rows) == 1:
                matched_row = matched_domain_rows[0]["row_number"]
                existing_id = matched_domain_rows[0]["lead_id"]
                reason = (
                    f"AMBIGUOUS MATCH (Case 4): Domain '{domain}' matches row {matched_row}, "
                    f"but incoming Lead ID '{lead_id}' does not match existing sheet Lead ID '{existing_id}'."
                )
                action = PlannedAction(
                    lead_id=lead_id,
                    business_name=business_name,
                    domain=domain,
                    action_type="AMBIGUOUS_MATCH_MANUAL_REVIEW",
                    case_number=4,
                    target_row=matched_row,
                    reason=reason,
                )
                plan.actions.append(action)
                plan.ambiguous_records.append(action)
                plan.summary["case_4_ambiguous_domain_only"] += 1
                plan.summary["total_ambiguous"] += 1

            # Case 5: Both match different rows
            elif (
                len(matched_id_rows) == 1
                and len(matched_domain_rows) == 1
                and matched_id_rows[0]["row_number"] != matched_domain_rows[0]["row_number"]
            ):
                id_row = matched_id_rows[0]["row_number"]
                dom_row = matched_domain_rows[0]["row_number"]
                reason = (
                    f"AMBIGUOUS MATCH (Case 5 - CROSS MATCH): Lead ID '{lead_id}' matches row {id_row}, "
                    f"while Domain '{domain}' matches row {dom_row}."
                )
                action = PlannedAction(
                    lead_id=lead_id,
                    business_name=business_name,
                    domain=domain,
                    action_type="AMBIGUOUS_MATCH_MANUAL_REVIEW",
                    case_number=5,
                    reason=reason,
                )
                plan.actions.append(action)
                plan.ambiguous_records.append(action)
                plan.summary["case_5_ambiguous_cross_match"] += 1
                plan.summary["total_ambiguous"] += 1

            # Edge Case: Multiple rows match either ID or Domain in existing sheet
            else:
                reason = (
                    f"AMBIGUOUS MATCH (Multiple Matches): Lead ID matches {len(matched_id_rows)} rows, "
                    f"Domain matches {len(matched_domain_rows)} rows. Sheet requires manual deduplication."
                )
                action = PlannedAction(
                    lead_id=lead_id,
                    business_name=business_name,
                    domain=domain,
                    action_type="AMBIGUOUS_MATCH_MANUAL_REVIEW",
                    case_number=0,
                    reason=reason,
                )
                plan.actions.append(action)
                plan.ambiguous_records.append(action)
                plan.summary["other_ambiguous"] += 1
                plan.summary["total_ambiguous"] += 1

        return plan

    @staticmethod
    def _filter_leads_by_ids(
        leads: List[Dict[str, Any]],
        lead_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Optionally filters an export batch to only the requested Lead ID(s).
        Fails loudly if any requested Lead ID is absent from the input batch.
        """
        if not lead_ids:
            return leads

        requested = [lid.strip() for lid in lead_ids if lid and lid.strip()]
        if not requested:
            return leads

        requested_set = set(requested)
        filtered = [
            lead for lead in leads
            if str(lead.get("Lead ID") or lead.get("lead_id", "")).strip() in requested_set
        ]
        found_ids = {
            str(lead.get("Lead ID") or lead.get("lead_id", "")).strip()
            for lead in filtered
        }
        missing = [lid for lid in requested if lid not in found_ids]
        if missing:
            raise ValueError(f"Requested Lead ID(s) not found in export file: {', '.join(missing)}")
        return filtered

    def dry_run(
        self,
        file_path: Union[str, Path],
        baseline_existing_rows: Optional[List[Dict[str, Any]]] = None,
        lead_ids: Optional[List[str]] = None,
        strict_accepted_only: bool = False,
    ) -> ActionPlan:
        """
        100% OFFLINE DRY RUN.
        Zero network calls, zero credentials required.
        """
        leads = self._filter_leads_by_ids(load_export_file(file_path), lead_ids=lead_ids)
        existing = baseline_existing_rows if baseline_existing_rows is not None else []
        return self.evaluate_batch(leads, existing, file_path=str(file_path), strict_accepted_only=strict_accepted_only)

    def live_preview(
        self,
        file_path: Union[str, Path],
        lead_ids: Optional[List[str]] = None,
        strict_accepted_only: bool = False,
    ) -> ActionPlan:
        """
        READ-ONLY LIVE PREVIEW.
        Zero write operations executed.
        """
        leads = self._filter_leads_by_ids(load_export_file(file_path), lead_ids=lead_ids)
        worksheet = self._get_worksheet(read_only=True)
        raw_rows = worksheet.get_all_values()
        existing_rows = self.parse_existing_sheet_rows(raw_rows)
        return self.evaluate_batch(leads, existing_rows, file_path=str(file_path), strict_accepted_only=strict_accepted_only)

    def sync(
        self,
        file_path: Union[str, Path],
        allow_inserts: bool = True,
        allow_updates: bool = True,
        lead_ids: Optional[List[str]] = None,
        strict_accepted_only: bool = False,
        write_segment_column: bool = False,
    ) -> Dict[str, Any]:
        """
        SYNCHRONIZATION EXECUTION from an export file.
        """
        leads = self._filter_leads_by_ids(load_export_file(file_path), lead_ids=lead_ids)
        return self.sync_records(
            leads=leads,
            source_label=str(file_path),
            allow_inserts=allow_inserts,
            allow_updates=allow_updates,
            strict_accepted_only=strict_accepted_only,
            write_segment_column=write_segment_column,
        )

    def sync_records(
        self,
        leads: List[Dict[str, Any]],
        source_label: str = "in-memory-batch",
        allow_inserts: bool = True,
        allow_updates: bool = True,
        strict_accepted_only: bool = True,
        write_segment_column: bool = False,
    ) -> Dict[str, Any]:
        """
        Synchronizes a list of normalized lead records into 'Outbound Leads Intelligence'.
        When strict_accepted_only=True (default for daily pipeline), rejects ANY record
        failing AcceptanceEvaluator before writing anything to the sheet.
        - Case 1 (Updates): Writes strictly to A{row}:U{row}, leaving V-AA untouched.
        - Case 2 (Inserts): Appends new row strictly covering A-V (22 columns), leaving W-AA untouched.
        - Optional Outreach Segment column (Col AB) written ONLY via dedicated AB{row} range if write_segment_column=True.
        """
        worksheet = self._get_worksheet(read_only=False)
        raw_rows = worksheet.get_all_values()

        headers_initialized_now = False
        if not raw_rows or not any(str(cell).strip() for row in raw_rows for cell in row):
            worksheet.update(range_name="A1:AA1", values=[ALL_COLUMNS], value_input_option="RAW")
            raw_rows = [ALL_COLUMNS]
            headers_initialized_now = True

        existing_rows = self.parse_existing_sheet_rows(raw_rows)
        plan = self.evaluate_batch(
            leads,
            existing_rows,
            file_path=source_label,
            strict_accepted_only=strict_accepted_only,
        )

        applied_updates = 0
        applied_inserts = 0
        inserted_lead_ids: List[str] = []
        skipped_ambiguous = len(plan.ambiguous_records)

        if allow_updates:
            for act in plan.actions:
                if act.action_type == "UPDATE" and act.target_range and act.system_payload:
                    worksheet.update(
                        range_name=act.target_range,
                        values=[act.system_payload],
                        value_input_option="RAW"
                    )
                    applied_updates += 1

        if allow_inserts:
            insert_actions: List[PlannedAction] = []
            new_rows_payload: List[List[Any]] = []
            for act in plan.actions:
                if act.action_type == "INSERT":
                    payload = act.insert_payload or act.full_payload
                    if payload:
                        new_rows_payload.append(list(payload[:22]))
                        insert_actions.append(act)

            if new_rows_payload:
                worksheet.append_rows(
                    new_rows_payload,
                    value_input_option="RAW",
                    table_range="A1:V1"
                )
                applied_inserts += len(new_rows_payload)
                inserted_lead_ids = [a.lead_id for a in insert_actions if a.lead_id]

                # Populate Col AB ("Outreach Segment") safely right of W-AA only when enabled
                if write_segment_column and insert_actions:
                    if getattr(worksheet, "col_count", 33) < 33 and hasattr(worksheet, "add_cols"):
                        worksheet.add_cols(33 - int(worksheet.col_count))
                    for act in insert_actions:
                        if act.target_row:
                            worksheet.update(
                                range_name=f"AB{act.target_row}:AB{act.target_row}",
                                values=[[act.outreach_segment]],
                                value_input_option="RAW",
                            )

        return {
            "status": "SUCCESS",
            "file_synced": source_label,
            "headers_initialized_now": headers_initialized_now,
            "total_input_leads": plan.total_leads,
            "applied_updates": applied_updates,
            "applied_inserts": applied_inserts,
            "inserted_lead_ids": inserted_lead_ids,
            "rejected_unaccepted": plan.summary.get("rejected_unaccepted", 0),
            "rejected_details": plan.rejected_unaccepted,
            "quarantined_ambiguous": skipped_ambiguous,
            "ambiguous_details": [
                {
                    "lead_id": a.lead_id,
                    "business_name": a.business_name,
                    "domain": a.domain,
                    "case": a.case_number,
                    "reason": a.reason
                }
                for a in plan.ambiguous_records
            ]
        }

    def get_existing_sheet_identifiers(self) -> Dict[str, Set[str]]:
        """Reads existing Lead IDs, domains, and emails from the main sheet for cross-run deduplication."""
        worksheet = self._get_worksheet(read_only=True)
        raw_rows = worksheet.get_all_values()
        parsed = self.parse_existing_sheet_rows(raw_rows)
        return {
            "domains": {r["domain"] for r in parsed if r.get("domain")},
            "lead_ids": {r["lead_id"] for r in parsed if r.get("lead_id")},
            "emails": {r["email"] for r in parsed if r.get("email") and r["email"] != "unavailable"},
        }

    def ensure_campaign_hub_tabs(self) -> Dict[str, Any]:
        """
        Idempotently prepares outreach automation columns (AB1:AG1 on main tab, leaving V-AA untouched)
        and auxiliary tabs: 'Email Templates', 'Daily Run Logs', 'Suppression & Opt-Outs'.
        Zero emails sent. Safe starter templates default Active=FALSE.
        """
        client = self._get_client()
        if not self.spreadsheet_id:
            raise ValueError("Missing SPREADSHEET_ID.")
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        existing_titles = {ws.title: ws for ws in spreadsheet.worksheets()}
        created_tabs: List[str] = []

        # 1. Ensure AB1:AG1 outreach tracking headers on main worksheet without touching A1:AA1
        main_ws = self._get_worksheet(read_only=False)
        if getattr(main_ws, "col_count", 33) < 33 and hasattr(main_ws, "add_cols"):
            main_ws.add_cols(33 - int(main_ws.col_count))
        header_row = main_ws.row_values(1)
        if not header_row:
            main_ws.update(range_name="A1:AA1", values=[ALL_COLUMNS], value_input_option="RAW")
        if header_row[27:33] != OUTREACH_TRACKING_COLUMNS:
            main_ws.update(range_name="AB1:AG1", values=[OUTREACH_TRACKING_COLUMNS], value_input_option="RAW")

        # 2. Email Templates tab (Active defaults to FALSE so nothing ever auto-sends)
        if "Email Templates" not in existing_titles:
            tmpl_ws = spreadsheet.add_worksheet(title="Email Templates", rows=100, cols=len(EMAIL_TEMPLATE_COLUMNS))
            starter_rows = [
                EMAIL_TEMPLATE_COLUMNS,
                [
                    "TMPL_AGENCY_S2L_01",
                    "Agency Speed-to-Lead Opportunity",
                    "AGENCY_SPEED_TO_LEAD",
                    "Tier 1 - Hot, Tier 2 - Warm",
                    "Quick question about lead response on {{Website}}",
                    "Paste approved plain text email template here before enabling.",
                    "",
                    "FALSE",
                    "10",
                    "Awaiting operator template copy & explicit approval.",
                ],
                [
                    "TMPL_AGENCY_AI_01",
                    "Agency 24/7 Screening Assistant",
                    "AGENCY_CONVERSATIONAL_AI",
                    "Tier 1 - Hot, Tier 2 - Warm",
                    "Inbound lead capture idea for {{Company}}",
                    "Paste approved plain text email template here before enabling.",
                    "",
                    "FALSE",
                    "10",
                    "Awaiting operator template copy & explicit approval.",
                ],
                [
                    "TMPL_CONSULT_PIPE_01",
                    "Consulting CRM & Calendar Automation",
                    "CONSULTING_PIPELINE_AUTOMATION",
                    "Tier 1 - Hot, Tier 2 - Warm",
                    "Automating consultation booking for {{Company}}",
                    "Paste approved plain text email template here before enabling.",
                    "",
                    "FALSE",
                    "10",
                    "Awaiting operator template copy & explicit approval.",
                ],
            ]
            tmpl_ws.update(range_name="A1:J4", values=starter_rows, value_input_option="RAW")
            created_tabs.append("Email Templates")

        # 3. Daily Run Logs tab
        if "Daily Run Logs" not in existing_titles:
            log_ws = spreadsheet.add_worksheet(title="Daily Run Logs", rows=120, cols=len(DAILY_RUN_LOG_COLUMNS))
            log_ws.update(range_name="A1:N1", values=[DAILY_RUN_LOG_COLUMNS], value_input_option="RAW")
            created_tabs.append("Daily Run Logs")

        # 4. Suppression & Opt-Outs tab
        if "Suppression & Opt-Outs" not in existing_titles:
            supp_ws = spreadsheet.add_worksheet(title="Suppression & Opt-Outs", rows=500, cols=len(SUPPRESSION_LOG_COLUMNS))
            supp_ws.update(range_name="A1:G1", values=[SUPPRESSION_LOG_COLUMNS], value_input_option="RAW")
            created_tabs.append("Suppression & Opt-Outs")

        # 5. Pipeline State tab (For $0 ephemeral cloud state hydration)
        if "Pipeline State" not in existing_titles:
            p_state_ws = spreadsheet.add_worksheet(title="Pipeline State", rows=50, cols=3)
            p_state_ws.update(range_name="A1:C1", values=[["Key", "Value", "Updated At"]], value_input_option="RAW")
            created_tabs.append("Pipeline State")

        # 6. Pipeline Deduplication tab (Compact cloud domain check log)
        if "Pipeline Deduplication" not in existing_titles:
            p_dedup_ws = spreadsheet.add_worksheet(title="Pipeline Deduplication", rows=1000, cols=4)
            p_dedup_ws.update(
                range_name="A1:D1",
                values=[["Domain", "Status", "Last Checked Date", "Reason"]],
                value_input_option="RAW",
            )
            created_tabs.append("Pipeline Deduplication")

        return {
            "status": "READY",
            "created_tabs": created_tabs,
            "outreach_headers_range": "AB1:AG1",
        }

    def sync_daily_run_log(self, run_summary: Dict[str, Any]) -> None:
        """Writes or updates today's telemetry row in the 'Daily Run Logs' tab idempotently by Run Date."""
        client = self._get_client()
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            log_ws = spreadsheet.worksheet("Daily Run Logs")
        except Exception:
            log_ws = spreadsheet.add_worksheet(title="Daily Run Logs", rows=120, cols=len(DAILY_RUN_LOG_COLUMNS))
            log_ws.update(range_name="A1:N1", values=[DAILY_RUN_LOG_COLUMNS], value_input_option="RAW")

        target = max(1, int(run_summary.get("target_accepted", 30)))
        accepted = int(run_summary.get("accepted_count", 0))
        email_counts = run_summary.get("email_verification_counts", {})
        verified_emails = int(email_counts.get("SMTP-Verified", 0)) + int(email_counts.get("Provider-Verified", 0))
        unverified_emails = sum(
            int(v) for k, v in email_counts.items()
            if k not in ("SMTP-Verified", "Provider-Verified")
        )
        completion_pct = f"{(accepted / target) * 100:.1f}%"

        row_values = [
            str(run_summary.get("run_date", "")),
            int(run_summary.get("campaign_day", 1)),
            str(run_summary.get("status", "")),
            target,
            accepted,
            int(run_summary.get("research_attempts", 0)),
            int(run_summary.get("rejected_count", 0)),
            int(run_summary.get("dm_identified_count", 0)),
            verified_emails,
            unverified_emails,
            int(run_summary.get("skipped_duplicates", 0)),
            int(run_summary.get("sheets_inserted", 0)),
            completion_pct,
            str(run_summary.get("blocker_summary", "")),
        ]

        existing_dates = log_ws.col_values(1)
        run_date = row_values[0]
        target_row_idx = None
        for idx, val in enumerate(existing_dates, start=1):
            if idx > 1 and str(val).strip() == run_date:
                target_row_idx = idx
                break

        if target_row_idx:
            log_ws.update(range_name=f"A{target_row_idx}:N{target_row_idx}", values=[row_values], value_input_option="RAW")
        else:
            log_ws.append_row(row_values, value_input_option="RAW", table_range="A1:N1")

    def fetch_sheet_opt_outs(self) -> List[Dict[str, str]]:
        """Reads recorded opt-outs/bounces from 'Suppression & Opt-Outs' tab if present."""
        client = self._get_client()
        if not self.spreadsheet_id:
            return []
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            supp_ws = spreadsheet.worksheet("Suppression & Opt-Outs")
        except Exception:
            return []

        rows = supp_ws.get_all_values()
        items: List[Dict[str, str]] = []
        for row in rows[1:]:
            dom = normalize_domain(row[1]) if len(row) > 1 else ""
            email = row[2].strip().lower() if len(row) > 2 else ""
            comp = row[3].strip() if len(row) > 3 else ""
            reason = row[5].strip() if len(row) > 5 else "sheet_opt_out"
            if dom or email or comp:
                items.append({"domain": dom, "email": email, "company_name": comp, "reason": reason})
        return items

    def get_pipeline_state(self) -> Dict[str, str]:
        """Reads key-value metadata from 'Pipeline State' worksheet if present."""
        client = self._get_client()
        if not self.spreadsheet_id:
            return {}
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            state_ws = spreadsheet.worksheet("Pipeline State")
        except Exception:
            return {}

        rows = state_ws.get_all_values()
        if not rows or len(rows) <= 1:
            return {}
        state: Dict[str, str] = {}
        for row in rows[1:]:
            if len(row) >= 2 and row[0].strip():
                state[row[0].strip()] = row[1].strip()
        return state

    def save_pipeline_state(self, updates: Dict[str, Any]) -> None:
        """Saves or updates key-value metadata in 'Pipeline State' worksheet idempotently."""
        if not updates:
            return
        client = self._get_client()
        if not self.spreadsheet_id:
            return
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            state_ws = spreadsheet.worksheet("Pipeline State")
        except Exception:
            state_ws = spreadsheet.add_worksheet(title="Pipeline State", rows=50, cols=3)
            state_ws.update(range_name="A1:C1", values=[["Key", "Value", "Updated At"]], value_input_option="RAW")

        from datetime import datetime, timezone
        now_str = datetime.now(timezone.utc).isoformat()
        rows = state_ws.get_all_values()
        existing_keys: Dict[str, int] = {}
        if rows:
            for idx, r in enumerate(rows[1:], start=2):
                if r and r[0].strip():
                    existing_keys[r[0].strip()] = idx

        for k, v in updates.items():
            str_val = str(v)
            if k in existing_keys:
                row_idx = existing_keys[k]
                state_ws.update(range_name=f"A{row_idx}:C{row_idx}", values=[[k, str_val, now_str]], value_input_option="RAW")
            else:
                state_ws.append_row([k, str_val, now_str], value_input_option="RAW")

    def fetch_deduplication_domains(self) -> Dict[str, str]:
        """Reads compact processed domain records from 'Pipeline Deduplication' tab if present."""
        client = self._get_client()
        if not self.spreadsheet_id:
            return {}
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            dedup_ws = spreadsheet.worksheet("Pipeline Deduplication")
        except Exception:
            return {}

        rows = dedup_ws.get_all_values()
        if not rows or len(rows) <= 1:
            return {}
        res: Dict[str, str] = {}
        for r in rows[1:]:
            if r and r[0].strip():
                dom = normalize_domain(r[0].strip())
                status = r[1].strip() if len(r) > 1 and r[1].strip() else "CHECKED"
                if dom:
                    res[dom] = status
        return res

    def append_deduplication_domains(self, records: List[Dict[str, str]]) -> None:
        """Appends compact processed domain records to 'Pipeline Deduplication' tab."""
        if not records:
            return
        client = self._get_client()
        if not self.spreadsheet_id:
            return
        spreadsheet = client.open_by_key(self.spreadsheet_id)
        try:
            dedup_ws = spreadsheet.worksheet("Pipeline Deduplication")
        except Exception:
            dedup_ws = spreadsheet.add_worksheet(title="Pipeline Deduplication", rows=1000, cols=4)
            dedup_ws.update(
                range_name="A1:D1",
                values=[["Domain", "Status", "Last Checked Date", "Reason"]],
                value_input_option="RAW",
            )

        rows_to_add: List[List[str]] = []
        for rec in records:
            dom = rec.get("domain", "").strip()
            if dom:
                rows_to_add.append([
                    dom,
                    str(rec.get("status", "CHECKED")),
                    str(rec.get("last_checked_date", "")),
                    str(rec.get("reason", ""))[:100],
                ])
        if rows_to_add:
            dedup_ws.append_rows(rows_to_add, value_input_option="RAW")


