# Google Apps Script Segmented Email Campaign Integration Guide

This Apps Script kit attaches to **Ariyx Systems – Outbound Intelligence Hub** to prepare segmented email campaign execution without modifying columns `A–AA` or sending any emails automatically.

## Safety Guarantees Built In

- **Hard Sending Lock (`LIVE_SENDING_ENABLED = false`):** Sending is completely disabled in [`Code.gs`](Code.gs). No `GmailApp` / `MailApp` OAuth send scopes are requested in [`appsscript.json`](appsscript.json).
- **Column Protection:** Automated pipeline columns (`A–U`) and operator-managed review columns (`V–AA`) are never overwritten. Campaign tracking uses columns `AB–AG`:
  - `AB`: Outreach Segment (`AGENCY_SPEED_TO_LEAD`, `AGENCY_CONVERSATIONAL_AI`, `CONSULTING_PIPELINE_AUTOMATION`, etc.)
  - `AC`: Assigned Template ID
  - `AD`: Sequence Step
  - `AE`: Last Email Sent At
  - `AF`: Gmail Thread ID
  - `AG`: Delivery & Opt-Out Status
- **Multi-Gate Safety:** Before any email could ever send after future activation, email verification (`Col J`) and compliance/approval (`Col U` + `Col V`) are evaluated independently, and a lead MUST pass:
  1. Valid public corporate email (`SMTP-Verified`, `Provider-Verified`, or DNS MX-checked `Publicly Listed (Unverified)` in Column `J`; never `Invalid`, `Unavailable`, `Catch-All / Risky`, or consumer webmail)
  2. Not `RESTRICTED`, `OPT_OUT_RECORDED`, or `ELIGIBILITY_NOT_ESTABLISHED` (Column `U`)
  3. Manual operator approval in Column `V` (`Approved for Outreach`, never auto-sending on `Ready for Manual Review`)
  4. Domain/email absent from `Suppression & Opt-Outs`
  5. Matching template in `Email Templates` explicitly set `Active = TRUE`

## Setup Steps (When You Are Ready)

1. Open **Ariyx Systems – Outbound Intelligence Hub** in Google Sheets.
2. Go to **Extensions -> Apps Script**.
3. Copy [`Code.gs`](Code.gs) into the Apps Script editor and enable **Show "appsscript.json" manifest file in editor** under Project Settings if updating [`appsscript.json`](appsscript.json).
4. Save and reload the spreadsheet to see the **Ariyx Outreach** menu.
5. Run **Ariyx Outreach -> 1. Setup Campaign Columns (AB:AG) & Tabs** (or run Python `python sync_sheets.py --setup-campaign-hub`).
6. Review/paste your templates into the **Email Templates** tab (keep `Active = FALSE` until approved).
7. Use **Ariyx Outreach -> 2. Auto-Assign Segments & Dry-Run Preview (Zero Sends)** to verify segmentation and gating with zero outgoing emails, or highlight a row and click **Ariyx Outreach -> 3. Preview Rendered Email for Selected Row (Zero Sends)** to test template variable rendering.

## Two-Way Opt-Out Sync

When an operator selects a lead row and clicks **Ariyx Outreach -> 4. Mark Selected Row Opt-Out / Suppressed**, the lead is logged into `Suppression & Opt-Outs`. The Python daily pipeline (`run_daily.py --sync-sheets`) automatically imports any rows from `Suppression & Opt-Outs` into local `data/suppression.json` before starting each daily run.
