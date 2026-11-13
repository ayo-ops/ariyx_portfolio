"""
Comprehensive Unit Tests for Google Sheets Synchronization Module.
Covers:
1. 27-Column Schema definition & column letter boundaries (A-U vs V-AA).
2. Domain normalization.
3. System row formatting (21 values, A-U) and Full row formatting (27 values, A-AA).
4. All 5 duplicate matching scenarios:
   - Case 1: Lead ID and domain match same row -> UPDATE range A{row}:U{row}.
   - Case 2: Neither matches -> INSERT next row.
   - Case 3: Only Lead ID matches -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW.
   - Case 4: Only domain matches -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW.
   - Case 5: Both match different rows -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW.
5. In-place update preserves operator columns V-AA.
6. Insertion initializes Column V as 'Ready for Manual Review' and leaves W-AA empty.
7. Repeat-run idempotency (second run results in 0 inserts, updates only).
8. CSV and JSON export file loading and field validation.
9. Failed / incomplete input handling (missing fields, invalid formats).
10. Offline dry-run verification (zero network requests).
11. Git exclusion verification for credentials and environment files.
"""

import json
import os
import subprocess
import pytest
from pathlib import Path
from typing import Any, Dict, List

from src.storage.sheet_schema import (
    ALL_COLUMNS,
    COLUMN_LETTERS,
    INSERT_COLUMNS,
    OPERATOR_COLUMNS,
    SYSTEM_COLUMNS,
    format_full_row,
    format_insert_row,
    format_system_row,
    load_export_file,
    normalize_domain,
    validate_lead_record,
)
from src.storage.sheet_syncer import (
    ActionPlan,
    SHEETS_API_SCOPES,
    SheetSyncer,
    read_local_env,
)


class MockWorksheet:
    """Mock Google Sheets Worksheet for deterministic, zero-network testing."""
    def __init__(self, initial_rows: List[List[Any]] = None):
        self.rows: List[List[Any]] = [list(r) for r in initial_rows] if initial_rows else []
        self.update_calls: List[Dict[str, Any]] = []
        self.append_calls: List[Dict[str, Any]] = []

    def get_all_values(self) -> List[List[str]]:
        return [[str(c) for c in r] for r in self.rows]

    def update(self, range_name: str, values: List[List[Any]], **kwargs):
        self.update_calls.append({"range_name": range_name, "values": values, "kwargs": kwargs})
        # Simulate header initialization on A1:AA1
        if range_name == "A1:AA1":
            if not self.rows:
                self.rows.append(list(values[0]))
            else:
                self.rows[0] = list(values[0])
            return

        # Simulate in-place update if range is A{row}:U{row}
        import re
        match = re.match(r"^A(\d+):U(\d+)$", range_name)
        if match:
            start_row = int(match.group(1))
            row_idx = start_row - 1
            if row_idx < len(self.rows):
                # Update cols 0 to 20, preserve cols 21 to 26
                existing_row = self.rows[row_idx]
                operator_part = existing_row[21:] if len(existing_row) > 21 else []
                new_system_part = values[0][:21]
                self.rows[row_idx] = new_system_part + operator_part

    def append_rows(self, values: List[List[Any]], **kwargs):
        self.append_calls.append({"values": values, "kwargs": kwargs})
        for row in values:
            # Strictly verify that new row insertions contain ONLY Columns A-V (22 items)
            assert len(row) == 22, f"Insert row must strictly contain 22 columns (A-V), got {len(row)}"
            self.rows.append(list(row))


@pytest.fixture
def sample_lead():
    return {
        "lead_id": "ARI-US-001",
        "date_researched": "2026-11-09",
        "business_name": "Apex Digital",
        "website": "https://apexdigital.com/contact",
        "domain": "apexdigital.com",
        "industry": "Marketing agencies",
        "country": "US",
        "city": "Austin",
        "decision_maker_name": "Sarah Connor",
        "decision_maker_title": "CEO",
        "verified_email": "sarah@apexdigital.com",
        "email_verification_status": "Publicly Listed (Unverified)",
        "formatted_phone": "+15125550100",
        "decision_maker_linkedin": "https://linkedin.com/in/sarahconnor",
        "company_linkedin": "https://linkedin.com/company/apexdigital",
        "estimated_employees": "25-50 (Estimate)",
        "business_description": "Premier B2B growth agency.",
        "potential_buying_signals": [
            {"signal_type": "NO_CHAT", "description": "No live chat detected"}
        ],
        "fit_hypothesis": "Ariyx Sub-60s Inbound Engine opportunity.",
        "evidence_urls": ["https://apexdigital.com/about"],
        "lead_score": 85,
        "qualification_tier": "Tier 1",
        "compliance_status": "REVIEW_REQUIRED",
    }


# ==============================================================================
# 1. Schema & Column Boundary Tests
# ==============================================================================

def test_schema_column_counts_and_ownership():
    assert len(SYSTEM_COLUMNS) == 21, "Columns A-U must be exactly 21 system-managed columns"
    assert len(OPERATOR_COLUMNS) == 6, "Columns V-AA must be exactly 6 operator-managed columns"
    assert len(ALL_COLUMNS) == 27, "Total columns must be exactly 27"
    assert len(COLUMN_LETTERS) == 27
    assert COLUMN_LETTERS[0] == "A"
    assert COLUMN_LETTERS[20] == "U"
    assert COLUMN_LETTERS[21] == "V"
    assert COLUMN_LETTERS[26] == "AA"


def test_column_i_and_j_naming():
    assert SYSTEM_COLUMNS[8] == "Public Business Email"
    assert SYSTEM_COLUMNS[9] == "Email Verification Status"
    assert OPERATOR_COLUMNS[0] == "Campaign Status"


def test_domain_normalization():
    assert normalize_domain("https://www.DirectiveConsulting.com/contact/") == "directiveconsulting.com"
    assert normalize_domain("http://ironpaper.com:8080/about?ref=1") == "ironpaper.com"
    assert normalize_domain("ignitedigital.com") == "ignitedigital.com"
    assert normalize_domain("www.example.co.uk/") == "example.co.uk"
    assert normalize_domain("") == ""
    assert normalize_domain(None) == ""


def test_format_system_row(sample_lead):
    row = format_system_row(sample_lead)
    assert len(row) == 21
    assert row[0] == "ARI-US-001"                # Col A: Lead ID
    assert row[2] == "Apex Digital"             # Col C: Business Name
    assert row[3] == "https://apexdigital.com/contact" # Col D: Website URL
    assert row[6] == "Sarah Connor"             # Col G: DM Name
    assert row[7] == "CEO"                      # Col H: Job Title
    assert row[8] == "sarah@apexdigital.com"    # Col I: Public Business Email
    assert row[9] == "Publicly Listed (Unverified)" # Col J: Email Verification Status
    assert row[18] == 85                        # Col S: Score
    assert row[19] == "Tier 1"                  # Col T: Tier
    assert row[20] == "REVIEW_REQUIRED"         # Col U: Compliance Status


def test_format_insert_row_strictly_22_columns(sample_lead):
    """Verifies that format_insert_row returns exactly 22 columns (A-V) without W-AA."""
    row = format_insert_row(sample_lead)
    assert len(row) == 22, f"Insert row must contain exactly 22 columns (A-V), got {len(row)}"
    assert row[0] == "ARI-US-001"                # Col A: Lead ID
    assert row[20] == "REVIEW_REQUIRED"         # Col U: Compliance Status
    assert row[21] == "Ready for Manual Review"  # Col V: Campaign Status initialized
    # Crucial: Columns W-AA must NOT be present in the insertion payload
    assert len(row) < 27


def test_format_full_row_initializes_campaign_status(sample_lead):
    row = format_full_row(sample_lead)
    assert len(row) == 27
    assert row[21] == "Ready for Manual Review"  # Col V: Initialized
    assert row[22] == ""                         # Col W: Assigned Rep (empty)
    assert row[23] == ""                         # Col X: Outreach Channel (empty)
    assert row[24] == ""                         # Col Y: Outreach Date (empty)
    assert row[25] == ""                         # Col Z: Prospect Response (empty)
    assert row[26] == ""                         # Col AA: Manual Notes (empty)


# ==============================================================================
# 2. Five-Case Matching Table Tests
# ==============================================================================

def test_case_1_lead_id_and_domain_match_same_row(sample_lead):
    """Case 1: Lead ID and domain match same row -> UPDATE range A{row}:U{row}."""
    existing_rows = [{
        "row_number": 5,
        "lead_id": "ARI-US-001",
        "domain": "apexdigital.com",
        "business_name": "Apex Digital",
        "operator_values": ["In Outreach", "John Doe", "Email", "2026-11-08", "Follow-up", "VIP lead"]
    }]

    syncer = SheetSyncer()
    plan = syncer.evaluate_batch([sample_lead], existing_rows)

    assert plan.summary["case_1_updates"] == 1
    assert plan.summary["case_2_inserts"] == 0
    assert plan.summary["total_ambiguous"] == 0
    assert len(plan.actions) == 1

    action = plan.actions[0]
    assert action.action_type == "UPDATE"
    assert action.case_number == 1
    assert action.target_row == 5
    assert action.target_range == "A5:U5"
    assert action.preserved_operator_values == ["In Outreach", "John Doe", "Email", "2026-11-08", "Follow-up", "VIP lead"]


def test_case_2_neither_lead_id_nor_domain_matches(sample_lead):
    """Case 2: Neither matches -> INSERT new row at next available position strictly covering Columns A-V."""
    existing_rows = [{
        "row_number": 2,
        "lead_id": "ARI-US-999",
        "domain": "othercompany.com",
        "business_name": "Other Co",
        "operator_values": ["Ready for Manual Review", "", "", "", "", ""]
    }]

    syncer = SheetSyncer()
    plan = syncer.evaluate_batch([sample_lead], existing_rows)

    assert plan.summary["case_1_updates"] == 0
    assert plan.summary["case_2_inserts"] == 1
    assert plan.summary["total_ambiguous"] == 0

    action = plan.actions[0]
    assert action.action_type == "INSERT"
    assert action.case_number == 2
    assert action.target_row == 3
    # Crucial: Target range is strictly A3:V3 (22 columns), never A3:AA3
    assert action.target_range == "A3:V3"
    assert len(action.insert_payload) == 22
    assert action.insert_payload[21] == "Ready for Manual Review"


def test_case_3_only_lead_id_matches(sample_lead):
    """Case 3: Only Lead ID matches -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW."""
    existing_rows = [{
        "row_number": 4,
        "lead_id": "ARI-US-001",
        "domain": "differentdomain.com",  # Different domain!
        "business_name": "Apex Digital",
        "operator_values": ["", "", "", "", "", ""]
    }]

    syncer = SheetSyncer()
    plan = syncer.evaluate_batch([sample_lead], existing_rows)

    assert plan.summary["case_3_ambiguous_id_only"] == 1
    assert plan.summary["total_ambiguous"] == 1
    assert len(plan.ambiguous_records) == 1
    assert plan.ambiguous_records[0].case_number == 3
    assert "AMBIGUOUS MATCH (Case 3)" in plan.ambiguous_records[0].reason


def test_case_4_only_domain_matches(sample_lead):
    """Case 4: Only domain matches -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW."""
    existing_rows = [{
        "row_number": 7,
        "lead_id": "ARI-US-OLD-ID",       # Different Lead ID!
        "domain": "apexdigital.com",
        "business_name": "Apex Digital",
        "operator_values": ["", "", "", "", "", ""]
    }]

    syncer = SheetSyncer()
    plan = syncer.evaluate_batch([sample_lead], existing_rows)

    assert plan.summary["case_4_ambiguous_domain_only"] == 1
    assert plan.summary["total_ambiguous"] == 1
    assert len(plan.ambiguous_records) == 1
    assert plan.ambiguous_records[0].case_number == 4
    assert "AMBIGUOUS MATCH (Case 4)" in plan.ambiguous_records[0].reason


def test_case_5_both_match_different_rows(sample_lead):
    """Case 5: Lead ID matches row A, domain matches row B -> FLAG AMBIGUOUS_MATCH_MANUAL_REVIEW."""
    existing_rows = [
        {
            "row_number": 3,
            "lead_id": "ARI-US-001",
            "domain": "firstcompany.com",
            "business_name": "First Co",
            "operator_values": ["", "", "", "", "", ""]
        },
        {
            "row_number": 8,
            "lead_id": "ARI-US-888",
            "domain": "apexdigital.com",
            "business_name": "Apex Digital",
            "operator_values": ["", "", "", "", "", ""]
        }
    ]

    syncer = SheetSyncer()
    plan = syncer.evaluate_batch([sample_lead], existing_rows)

    assert plan.summary["case_5_ambiguous_cross_match"] == 1
    assert plan.summary["total_ambiguous"] == 1
    assert len(plan.ambiguous_records) == 1
    assert plan.ambiguous_records[0].case_number == 5
    assert "CROSS MATCH" in plan.ambiguous_records[0].reason


# ==============================================================================
# 3. Live Sync Emulation & Column Protection
# ==============================================================================

def test_in_place_update_strictly_preserves_operator_columns(sample_lead, tmp_path):
    """Verifies that an update writes to A{row}:U{row} and preserves V-AA untouched."""
    # Existing sheet with headers at row 1, existing lead at row 2 with custom operator notes
    header_row = list(ALL_COLUMNS)
    existing_row = format_full_row(sample_lead)
    existing_row[21] = "Outreach In Progress"
    existing_row[22] = "Agent Alice"
    existing_row[23] = "LinkedIn InMail"
    existing_row[24] = "2026-11-09"
    existing_row[25] = "Meeting Booked"
    existing_row[26] = "Client requested proposal for inbound engine."

    mock_sheet = MockWorksheet(initial_rows=[header_row, existing_row])

    # Incoming updated lead with higher score
    updated_lead = dict(sample_lead)
    updated_lead["lead_score"] = 95
    updated_lead["business_name"] = "Apex Digital Systems"

    test_file = tmp_path / "test_update.json"
    test_file.write_text(json.dumps([updated_lead]), encoding="utf-8")

    syncer = SheetSyncer(worksheet=mock_sheet)
    result = syncer.sync(file_path=test_file)

    assert result["applied_updates"] == 1
    assert result["applied_inserts"] == 0
    assert len(mock_sheet.update_calls) == 1
    assert mock_sheet.update_calls[0]["range_name"] == "A2:U2"

    # Verify sheet state in memory
    final_row = mock_sheet.rows[1]
    assert final_row[0] == "ARI-US-001"
    assert final_row[2] == "Apex Digital Systems"  # Updated Business Name
    assert final_row[18] == 95                     # Updated Score
    # Crucial: Operator columns V-AA must be completely preserved
    assert final_row[21] == "Outreach In Progress"
    assert final_row[22] == "Agent Alice"
    assert final_row[23] == "LinkedIn InMail"
    assert final_row[24] == "2026-11-09"
    assert final_row[25] == "Meeting Booked"
    assert final_row[26] == "Client requested proposal for inbound engine."


def test_repeat_run_idempotency(sample_lead, tmp_path):
    """Verifies that running the same batch twice results in updates, 0 duplicate rows."""
    header_row = list(ALL_COLUMNS)
    mock_sheet = MockWorksheet(initial_rows=[header_row])

    test_file = tmp_path / "test_idempotency.json"
    test_file.write_text(json.dumps([sample_lead]), encoding="utf-8")

    syncer = SheetSyncer(worksheet=mock_sheet)

    # Run 1: Should append (Case 2)
    res1 = syncer.sync(file_path=test_file)
    assert res1["applied_inserts"] == 1
    assert res1["applied_updates"] == 0
    assert len(mock_sheet.rows) == 2  # Header + 1 row

    # Run 2: Should update existing row (Case 1), 0 appends
    res2 = syncer.sync(file_path=test_file)
    assert res2["applied_inserts"] == 0
    assert res2["applied_updates"] == 1
    assert len(mock_sheet.rows) == 2  # Still 1 data row, no duplicates!


# ==============================================================================
# 4. Input Validation & File Loading
# ==============================================================================

def test_validation_missing_lead_id_or_website():
    bad_lead_1 = {"lead_id": "", "website": "https://valid.com", "lead_score": 50, "qualification_tier": "Tier 2"}
    is_valid, errors = validate_lead_record(bad_lead_1)
    assert not is_valid
    assert any("Lead ID" in e for e in errors)

    bad_lead_2 = {"lead_id": "ARI-01", "website": "", "lead_score": 50, "qualification_tier": "Tier 2"}
    is_valid2, errors2 = validate_lead_record(bad_lead_2)
    assert not is_valid2
    assert any("Website" in e for e in errors2)


def test_load_export_actual_30_batch_files():
    """Validates that the real 30-lead CSV and JSON files load and validate properly."""
    base_dir = Path(__file__).resolve().parent.parent
    json_path = base_dir / "data" / "exports" / "mixed_services_uk_us_20261109_193531.json"
    csv_path = base_dir / "data" / "exports" / "mixed_services_uk_us_20261109_193531.csv"

    if json_path.exists():
        leads_json = load_export_file(json_path)
        assert len(leads_json) == 30
        for l in leads_json:
            valid, errs = validate_lead_record(l)
            assert valid, f"Lead failed validation: {errs}"

    if csv_path.exists():
        leads_csv = load_export_file(csv_path)
        assert len(leads_csv) == 30
        for l in leads_csv:
            valid, errs = validate_lead_record(l)
            assert valid, f"CSV Lead failed validation: {errs}"


def test_dry_run_is_completely_offline(sample_lead, tmp_path):
    """Ensures dry_run requires no credentials, no network, and returns a complete ActionPlan."""
    test_file = tmp_path / "offline_test.json"
    test_file.write_text(json.dumps([sample_lead]), encoding="utf-8")

    syncer = SheetSyncer(credentials_path=None, spreadsheet_id=None)
    plan = syncer.dry_run(test_file)

    assert plan.total_leads == 1
    assert plan.valid_leads == 1
    assert plan.summary["case_2_inserts"] == 1
    assert len(plan.actions) == 1


# ==============================================================================
# 5. Git Exclusion Rules Verification
# ==============================================================================

def test_git_exclusion_rules():
    """
    Checks that .gitignore excludes credentials, secrets, and environment files
    while preserving .env.example and JSON exports.
    """
    base_dir = Path(__file__).resolve().parent.parent
    gitignore_path = base_dir / ".gitignore"
    assert gitignore_path.exists()

    content = gitignore_path.read_text(encoding="utf-8")
    assert "*service_account*.json" in content
    assert "*credential*.json" in content or "*credentials*.json" in content
    assert ".env" in content
    assert "!.env.example" in content
    lines = [line.strip() for line in content.splitlines()]
    # Crucial: No blanket *.json rule
    assert "*.json" not in lines


# ==============================================================================
# 6. Local Configuration, Scope Enforcement & Read-Only Connection Check
# ==============================================================================

def test_sheets_only_scope_constant():
    """Ensures ONLY the Google Sheets API scope is configured (never Google Drive)."""
    assert SHEETS_API_SCOPES == ["https://www.googleapis.com/auth/spreadsheets"]


def test_gspread_authenticated_with_sheets_scope_only(monkeypatch, tmp_path):
    """Verifies SheetSyncer passes ONLY spreadsheets scope to gspread.service_account."""
    fake_cred_file = tmp_path / "fake_cred.json"
    fake_cred_file.write_text("{}", encoding="utf-8")

    captured = {}

    class DummyGspread:
        @staticmethod
        def service_account(filename, scopes=None):
            captured["filename"] = filename
            captured["scopes"] = scopes
            return "MOCK_CLIENT"

    import sys
    monkeypatch.setitem(sys.modules, "gspread", DummyGspread)

    syncer = SheetSyncer(
        credentials_path=str(fake_cred_file),
        spreadsheet_id="test-sheet-id-123",
        load_env=False,
    )
    client = syncer._get_client()

    assert client == "MOCK_CLIENT"
    assert captured["filename"] == str(fake_cred_file)
    assert captured["scopes"] == ["https://www.googleapis.com/auth/spreadsheets"]


def test_local_env_loading_and_placeholder_rejection(monkeypatch, tmp_path):
    """Verifies .env parsing, OS env precedence, and placeholder ID rejection."""
    monkeypatch.delenv("GOOGLE_SHEETS_CREDENTIALS_PATH", raising=False)
    monkeypatch.delenv("SPREADSHEET_ID", raising=False)
    monkeypatch.delenv("WORKSHEET_NAME", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Comment\n"
        "GOOGLE_SHEETS_CREDENTIALS_PATH=C:\\Users\\Test\\.ariyx\\cred.json\n"
        "SPREADSHEET_ID=your_spreadsheet_id_here\n"
        "WORKSHEET_NAME=Outbound Leads Intelligence\n",
        encoding="utf-8",
    )

    syncer = SheetSyncer(load_env=True, env_path=env_file)
    assert syncer.credentials_path == "C:\\Users\\Test\\.ariyx\\cred.json"
    assert syncer.spreadsheet_id is None  # Placeholder rejected
    assert syncer.worksheet_name == "Outbound Leads Intelligence"

    # OS env takes precedence over .env
    monkeypatch.setenv("SPREADSHEET_ID", "real-id-from-env")
    syncer2 = SheetSyncer(load_env=True, env_path=env_file)
    assert syncer2.spreadsheet_id == "real-id-from-env"


def test_check_connection_read_only_without_writes():
    """Verifies check_connection reads spreadsheet metadata and never performs writes."""

    class MockTab:
        def __init__(self, title, header_row):
            self.title = title
            self._header_row = header_row
            self.row_count = 1000
            self.writes = 0

        def row_values(self, idx):
            return self._header_row if idx == 1 else []

    class MockSpreadsheet:
        def __init__(self):
            self.title = "Ariyx Systems – Outbound Intelligence Hub"
            self._tabs = [
                MockTab("Outbound Leads Intelligence", list(ALL_COLUMNS))
            ]

        def worksheets(self):
            return self._tabs

        def worksheet(self, name):
            for t in self._tabs:
                if t.title == name:
                    return t
            raise Exception("Not found")

    class MockClient:
        def open_by_key(self, key):
            assert key == "dummy-sheet-id"
            return MockSpreadsheet()

    syncer = SheetSyncer(
        credentials_path="unused.json",
        spreadsheet_id="dummy-sheet-id",
        client=MockClient(),
        load_env=False,
    )
    status = syncer.check_connection()

    assert status["status"] == "CONNECTED_READ_ONLY"
    assert status["spreadsheet_title"] == "Ariyx Systems – Outbound Intelligence Hub"
    assert status["scopes"] == ["https://www.googleapis.com/auth/spreadsheets"]
    assert status["target_worksheet"] == "Outbound Leads Intelligence"
    assert status["target_worksheet_exists"] is True
    assert status["target_headers_initialized"] is True


def test_single_lead_sync_initializes_headers_and_writes_raw_a_to_v(sample_lead, tmp_path):
    """
    Simulates initializing headers (A1:AA1) on an empty tab and syncing only one
    selected Lead ID (leaving other batch leads unsynced and columns W-AA untouched).
    """
    other_lead = dict(sample_lead)
    other_lead["lead_id"] = "ARI-US-999"
    other_lead["business_name"] = "Other Agency"
    other_lead["website"] = "https://otheragency.com"
    other_lead["domain"] = "otheragency.com"

    batch_file = tmp_path / "two_leads.json"
    batch_file.write_text(json.dumps([sample_lead, other_lead]), encoding="utf-8")

    # Completely empty worksheet (0 rows)
    mock_sheet = MockWorksheet(initial_rows=[])
    syncer = SheetSyncer(worksheet=mock_sheet, load_env=False)

    res = syncer.sync(file_path=batch_file, lead_ids=["ARI-US-001"])

    assert res["headers_initialized_now"] is True
    assert res["total_input_leads"] == 1
    assert res["applied_inserts"] == 1
    assert res["applied_updates"] == 0

    # Verify A1:AA1 header initialization call
    assert len(mock_sheet.update_calls) == 1
    assert mock_sheet.update_calls[0]["range_name"] == "A1:AA1"
    assert mock_sheet.update_calls[0]["values"] == [ALL_COLUMNS]
    assert mock_sheet.update_calls[0]["kwargs"].get("value_input_option") == "RAW"

    # Verify append call uses RAW input option and A1:V1 table_range with 22 columns
    assert len(mock_sheet.append_calls) == 1
    append_call = mock_sheet.append_calls[0]
    assert append_call["kwargs"].get("value_input_option") == "RAW"
    assert append_call["kwargs"].get("table_range") == "A1:V1"
    assert len(append_call["values"]) == 1
    assert len(append_call["values"][0]) == 22

    # Verify only row 1 (headers) and row 2 (ARI-US-001) exist
    assert len(mock_sheet.rows) == 2
    assert mock_sheet.rows[0] == ALL_COLUMNS
    assert mock_sheet.rows[1][0] == "ARI-US-001"
    assert mock_sheet.rows[1][10] == "+15125550100"
    assert mock_sheet.rows[1][21] == "Ready for Manual Review"


def test_filter_missing_lead_id_raises_error(sample_lead, tmp_path):
    batch_file = tmp_path / "one_lead.json"
    batch_file.write_text(json.dumps([sample_lead]), encoding="utf-8")

    syncer = SheetSyncer(load_env=False)
    with pytest.raises(ValueError, match="Requested Lead ID"):
        syncer.dry_run(batch_file, lead_ids=["NON-EXISTENT-ID"])


def test_builtvisible_offline_update_preserves_simulated_manual_note_in_col_aa(tmp_path):
    """
    Offline test using Builtvisible (ARI-UK-38A564) from the real export file:
    Simulates manual operator entries in Columns V-AA (including a manual note in Col AA)
    and verifies that an in-place update writes strictly to A2:U2 (21 cols) and preserves W-AA.
    """
    base_dir = Path(__file__).resolve().parent.parent
    real_export = base_dir / "data" / "exports" / "mixed_services_uk_us_20261109_193531.json"
    all_leads = load_export_file(real_export)
    builtvisible = next(l for l in all_leads if l["Lead ID"] == "ARI-UK-38A564")

    # Initial row inserted into simulated offline sheet (Cols A-V), plus operator edits in V-AA
    initial_row_a_to_v = format_insert_row(builtvisible)
    assert len(initial_row_a_to_v) == 22

    # Simulate operator modifying Col V and filling manual tracking fields W-AA
    initial_row_a_to_v[21] = "In Outreach - Operator Approved"  # Col V: Campaign Status
    simulated_w_to_aa = [
        "Jordan (AE)",                                            # Col W: Assigned Rep
        "Email + LinkedIn",                                       # Col X: Outreach Channel
        "2026-11-11",                                             # Col Y: Outreach Date
        "Warm Reply Received",                                    # Col Z: Prospect Response
        "SIMULATED MANUAL NOTE: Preserve this note in Col AA.",   # Col AA: Manual Notes
    ]
    simulated_row_2 = initial_row_a_to_v + simulated_w_to_aa
    assert len(simulated_row_2) == 27

    mock_sheet = MockWorksheet(initial_rows=[list(ALL_COLUMNS), simulated_row_2])

    # Prepare updated Builtvisible research payload in a temp file (real export untouched)
    updated_builtvisible = dict(builtvisible)
    updated_builtvisible["date_researched"] = "2026-11-11"
    updated_builtvisible["lead_score"] = 92
    updated_builtvisible["fit_hypothesis"] = "Updated hypothesis after follow-up signal audit."
    updated_file = tmp_path / "builtvisible_updated.json"
    updated_file.write_text(json.dumps([updated_builtvisible]), encoding="utf-8")

    # Ensure zero real network or credential usage (offline MockWorksheet only)
    syncer = SheetSyncer(worksheet=mock_sheet, load_env=False)

    # First verify dry-run preview against simulated sheet state
    parsed_existing = syncer.parse_existing_sheet_rows(mock_sheet.get_all_values())
    plan = syncer.dry_run(updated_file, baseline_existing_rows=parsed_existing)
    assert plan.summary["case_1_updates"] == 1
    assert plan.summary["case_2_inserts"] == 0
    assert plan.actions[0].target_range == "A2:U2"
    assert len(plan.actions[0].system_payload) == 21
    assert plan.actions[0].preserved_operator_values[5] == "SIMULATED MANUAL NOTE: Preserve this note in Col AA."

    # Execute offline sync against MockWorksheet
    result = syncer.sync(file_path=updated_file, lead_ids=["ARI-UK-38A564"])
    assert result["applied_updates"] == 1
    assert result["applied_inserts"] == 0
    assert len(mock_sheet.append_calls) == 0

    # Strictly verify update targeted A2:U2 with exactly 21 columns (never V-AA)
    assert len(mock_sheet.update_calls) == 1
    call = mock_sheet.update_calls[0]
    assert call["range_name"] == "A2:U2"
    assert len(call["values"][0]) == 21
    assert call["kwargs"].get("value_input_option") == "RAW"

    # Verify updated system columns (A-U) AND completely preserved operator columns (V-AA)
    final_row = mock_sheet.rows[1]
    assert len(final_row) == 27
    assert final_row[0] == "ARI-UK-38A564"   # Col A
    assert final_row[1] == "2026-11-11"      # Col B updated
    assert final_row[10] == "+441392633731"  # Col K E.164 phone preserved
    assert final_row[16] == "Updated hypothesis after follow-up signal audit."  # Col Q updated
    assert final_row[18] == 92               # Col S score updated

    # Verify Columns V-AA (indices 21-26) are 100% preserved
    assert final_row[21] == "In Outreach - Operator Approved"                  # Col V
    assert final_row[22] == "Jordan (AE)"                                      # Col W
    assert final_row[23] == "Email + LinkedIn"                                 # Col X
    assert final_row[24] == "2026-11-11"                                       # Col Y
    assert final_row[25] == "Warm Reply Received"                              # Col Z
    assert final_row[26] == "SIMULATED MANUAL NOTE: Preserve this note in Col AA."  # Col AA



