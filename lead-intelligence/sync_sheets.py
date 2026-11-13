"""
CLI Entry Point for Ariyx Google Sheets Synchronization.
Usage:
  python sync_sheets.py --dry-run --file data/exports/mixed_services_uk_us_20261109_193531.json
  python sync_sheets.py --live-preview --file data/exports/mixed_services_uk_us_20261109_193531.json
  python sync_sheets.py --sync --file data/exports/mixed_services_uk_us_20261109_193531.json
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.storage.sheet_schema import ALL_COLUMNS, SYSTEM_COLUMNS, OPERATOR_COLUMNS
from src.storage.sheet_syncer import ActionPlan, SheetSyncer


def find_latest_export(exports_dir: Optional[Path] = None) -> Optional[Path]:
    """Finds the most recently created JSON or CSV file in data/exports/."""
    if exports_dir is None:
        exports_dir = BASE_DIR / "data" / "exports"

    if not exports_dir.exists():
        return None

    files = list(exports_dir.glob("*.json")) + list(exports_dir.glob("*.csv"))
    # Exclude .gitkeep or other hidden files
    valid_files = [f for f in files if not f.name.startswith(".")]
    if not valid_files:
        return None

    valid_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return valid_files[0]


def _sanitize_error(err: Exception, syncer: SheetSyncer) -> str:
    """Scrubs sensitive Spreadsheet ID from error output if present in API URLs."""
    msg = str(err) or type(err).__name__
    if getattr(syncer, "spreadsheet_id", None) and len(syncer.spreadsheet_id) > 4:
        msg = msg.replace(syncer.spreadsheet_id, "[REDACTED_SPREADSHEET_ID]")
    return f"{type(err).__name__}: {msg}" if msg != type(err).__name__ else msg


def print_plan_report(plan: ActionPlan, mode: str):
    """Prints a structured, human-readable report of the proposed sync actions."""
    print("\n" + "=" * 80)
    print(f" ARIYX SYSTEMS – OUTBOUND LEADS GOOGLE SHEETS SYNC REPORT")
    print(f" Execution Mode: {mode.upper()}")
    print("=" * 80)
    print(f" Export File:          {plan.file_path}")
    print(f" Total Input Leads:    {plan.total_leads}")
    print(f" Valid Leads:          {plan.valid_leads}")
    print(f" Invalid Leads:        {plan.invalid_leads}")
    print(f" Blocked (Unaccepted): {plan.summary.get('rejected_unaccepted', 0)}")
    print(f" Intra-batch Dupes:    {len(plan.intra_batch_duplicates)}")
    print("-" * 80)
    print(" PROPOSED ACTIONS BREAKDOWN (Five-Case Matching Table):")
    print(f"  [Case 1] In-Place Updates (A-U only):            {plan.summary.get('case_1_updates', 0)}")
    print(f"  [Case 2] New Inserts (A-V with Campaign Status): {plan.summary.get('case_2_inserts', 0)}")
    print(f"  [Case 3] Ambiguous (Lead ID only matches):       {plan.summary.get('case_3_ambiguous_id_only', 0)}")
    print(f"  [Case 4] Ambiguous (Domain only matches):        {plan.summary.get('case_4_ambiguous_domain_only', 0)}")
    print(f"  [Case 5] Ambiguous (Cross-row match):           {plan.summary.get('case_5_ambiguous_cross_match', 0)}")
    print(f"  Total Quarantined for Manual Review:             {plan.summary.get('total_ambiguous', 0)}")
    print("=" * 80)

    # Show intra-batch duplicates if any
    if plan.intra_batch_duplicates:
        print("\n[!] WARNING: INTRA-BATCH DUPLICATES DETECTED IN EXPORT FILE:")
        for dupe in plan.intra_batch_duplicates:
            print(f"  - Record #{dupe['batch_index']}: {dupe['type']} '{dupe['value']}' "
                  f"(previously seen at #{dupe['previous_index']})")

    # Show validation errors if any
    if plan.validation_errors:
        print("\n[!] INVALID RECORDS DETECTED (Skipped from Sync):")
        for err in plan.validation_errors:
            print(f"  - Lead: {err['lead']} (Errors: {', '.join(err['errors'])})")

    if plan.rejected_unaccepted:
        print("\n[!] RECORDS BLOCKED BY STRICT MAIN-SHEET ACCEPTANCE GATE:")
        for rej in plan.rejected_unaccepted[:10]:
            print(f"  - {rej['business_name']} ({rej['domain']}): {', '.join(rej['blocker_codes'])}")
        if len(plan.rejected_unaccepted) > 10:
            print(f"  ... and {len(plan.rejected_unaccepted) - 10} more blocked records.")

    # Show Ambiguous Matches Quarantined
    if plan.ambiguous_records:
        print("\n" + "!" * 80)
        print(" AMBIGUOUS RECORDS QUARANTINED (MANUAL REVIEW REQUIRED):")
        print(" These records will NOT be merged or inserted automatically.")
        print("!" * 80)
        for amb in plan.ambiguous_records:
            print(f"  * Lead ID:      {amb.lead_id}")
            print(f"    Business:     {amb.business_name}")
            print(f"    Domain:       {amb.domain}")
            print(f"    Case:         Case {amb.case_number}")
            print(f"    Diagnostic:   {amb.reason}")
            print("    " + "-" * 70)

    # Sample Preview of Proposed Actions (First 5)
    print("\n SAMPLE PREVIEW OF ACTIONS (Up to 5 records):")
    print("-" * 80)
    for act in plan.actions[:5]:
        target_str = act.target_range or f"Row {act.target_row}" or "Pending"
        print(f"  [{act.action_type:<7}] {act.lead_id} | {act.business_name:<25} | Domain: {act.domain}")
        print(f"             Target: {target_str:<15} | Reason: {act.reason}")
        if act.action_type == "UPDATE" and act.preserved_operator_values:
            print(f"             Preserved Operator Fields (V-AA): {act.preserved_operator_values}")
    if len(plan.actions) > 5:
        print(f"  ... and {len(plan.actions) - 5} additional records.")
    print("=" * 80)

    if mode.upper() == "DRY-RUN":
        print("\n [DRY-RUN COMPLETE]: 100% Offline execution. Zero network calls made.")
        print(" Zero Google Sheets modifications performed.\n")
    elif mode.upper() == "LIVE-PREVIEW":
        print("\n [LIVE-PREVIEW COMPLETE]: Read-only inspection of Google Sheet.")
        print(" Zero write operations executed.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Ariyx Systems - Google Sheets Lead Intelligence Synchronization Module"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--dry-run",
        action="store_true",
        help="Run 100% offline schema validation and payload preview (default, zero network calls)."
    )
    group.add_argument(
        "--check-connection",
        action="store_true",
        help="Perform a read-only connection check against Google Sheets without modifying or importing data."
    )
    group.add_argument(
        "--live-preview",
        action="store_true",
        help="Connect read-only to Google Sheets to preview proposed changes against live data."
    )
    group.add_argument(
        "--sync",
        action="store_true",
        help="Execute the synchronization to the Google Sheet (requires credentials and confirmation)."
    )

    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to the JSON or CSV export file to sync. Defaults to latest export in data/exports/."
    )
    parser.add_argument(
        "--credentials",
        type=str,
        help="Path to the Google Cloud Service Account JSON key file."
    )
    parser.add_argument(
        "--spreadsheet-id",
        type=str,
        help="Target Google Spreadsheet ID (found in Sheets URL)."
    )
    parser.add_argument(
        "--worksheet-name",
        type=str,
        default=None,
        help="Target worksheet/tab name (defaults to WORKSHEET_NAME env var or 'Outbound Leads Intelligence')."
    )
    parser.add_argument(
        "--lead-id",
        action="append",
        help="Optional Lead ID to filter sync/preview to specific lead(s) only (can be repeated)."
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt before executing live sync."
    )
    parser.add_argument(
        "--accepted-only",
        action="store_true",
        help="Enforce strict daily acceptance rules (only verified, evidenced, compliant accepted prospects enter the main sheet)."
    )
    parser.add_argument(
        "--setup-campaign-hub",
        action="store_true",
        help="Idempotently initialize campaign extension columns (AB1:AG1) and Email Templates / Daily Run Logs / Suppression tabs (writes headers/inactive template placeholders only; sends 0 emails)."
    )

    args = parser.parse_args()

    # Determine execution mode
    if args.sync:
        mode = "SYNC"
    elif args.live_preview:
        mode = "LIVE-PREVIEW"
    elif args.check_connection:
        mode = "CHECK-CONNECTION"
    else:
        mode = "DRY-RUN"

    # Initialize syncer (loads GOOGLE_SHEETS_CREDENTIALS_PATH, SPREADSHEET_ID, WORKSHEET_NAME safely)
    syncer = SheetSyncer(
        credentials_path=args.credentials,
        spreadsheet_id=args.spreadsheet_id,
        worksheet_name=args.worksheet_name,
    )

    if mode == "CHECK-CONNECTION":
        try:
            status = syncer.check_connection()
            print("\n" + "=" * 80)
            print(" ARIYX SYSTEMS – GOOGLE SHEETS CONNECTION CHECK (READ-ONLY)")
            print("=" * 80)
            print(f" Status:               {status['status']}")
            print(f" Spreadsheet Title:    {status['spreadsheet_title']}")
            print(f" OAuth Scope Used:     {', '.join(status['scopes'])}")
            print(f" Target Worksheet:     {status['target_worksheet']}")
            print(f" Target Tab Exists:    {status['target_worksheet_exists']}")
            print(f" Existing Tabs:        {', '.join(status['available_worksheets'])}")
            if status['target_worksheet_exists']:
                print(f" Headers Initialized:  {status['target_headers_initialized']}")
                print(f" Row Capacity:         {status['worksheet_row_capacity']}")
            print("=" * 80)
            print(" [READ-ONLY CHECK COMPLETE]: Zero writes or imports performed.\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n[CONNECTION CHECK BLOCKED]: {_sanitize_error(e, syncer)}", file=sys.stderr)
            sys.exit(1)

    if args.setup_campaign_hub:
        try:
            hub_res = syncer.ensure_campaign_hub_tabs()
            print(f"\n[CAMPAIGN HUB READY]: {hub_res}\n")
            if not args.sync and not args.live_preview and not args.dry_run:
                sys.exit(0)
        except Exception as e:
            print(f"\n[SETUP ERROR]: {_sanitize_error(e, syncer)}", file=sys.stderr)
            sys.exit(1)

    # Resolve target export file for dry-run / live-preview / sync
    target_file = args.file
    if not target_file:
        latest = find_latest_export()
        if not latest:
            print("[ERROR]: No export file specified and none found in data/exports/.", file=sys.stderr)
            sys.exit(1)
        target_file = str(latest)

    target_path = Path(target_file)
    if not target_path.exists():
        print(f"[ERROR]: Target export file does not exist: {target_path}", file=sys.stderr)
        sys.exit(1)

    if mode == "DRY-RUN":
        plan = syncer.dry_run(target_path, lead_ids=args.lead_id, strict_accepted_only=args.accepted_only)
        print_plan_report(plan, mode="DRY-RUN")
        sys.exit(0)

    elif mode == "LIVE-PREVIEW":
        # Check credentials
        try:
            plan = syncer.live_preview(target_path, lead_ids=args.lead_id, strict_accepted_only=args.accepted_only)
            print_plan_report(plan, mode="LIVE-PREVIEW")
        except Exception as e:
            print(f"\n[LIVE-PREVIEW BLOCKED]: {_sanitize_error(e, syncer)}", file=sys.stderr)
            print("To test offline schema validation and payload generation, use: python sync_sheets.py --dry-run\n")
            sys.exit(1)

    elif mode == "SYNC":
        try:
            if not args.yes:
                confirm = input("Are you sure you want to proceed with live Google Sheets synchronization? [y/N]: ")
                if confirm.strip().lower() not in ["y", "yes"]:
                    print("Sync cancelled by operator.")
                    sys.exit(0)

            result = syncer.sync(
                target_path,
                lead_ids=args.lead_id,
                strict_accepted_only=args.accepted_only,
                write_segment_column=args.accepted_only,
            )
            print("\n" + "=" * 80)
            print(" ARIYX SYSTEMS – SYNCHRONIZATION EXECUTION COMPLETE")
            print("=" * 80)
            print(f" Status:                  {result['status']}")
            print(f" File Synced:             {result['file_synced']}")
            print(f" Headers Initialized Now: {result.get('headers_initialized_now', False)}")
            print(f" Total Input Leads:       {result['total_input_leads']}")
            print(f" In-Place Updates:        {result['applied_updates']}")
            print(f" New Inserts:             {result['applied_inserts']}")
            print(f" Quarantined Ambiguous:   {result['quarantined_ambiguous']}")
            print("=" * 80 + "\n")
        except Exception as e:
            print(f"\n[SYNC ERROR]: {_sanitize_error(e, syncer)}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
