# Ariyx Lead Intelligence System

A dedicated, isolated B2B lead intelligence and decision-maker identification engine engineered specifically for **Ariyx Systems**.

---

## 1. Project Boundaries & Isolation
- **100% Isolated:** Resides entirely within `/lead-intelligence`. The Ariyx Systems React/Vite website, public assets, build scripts, live Vercel deployments, and inbound contact form backends remain completely untouched.
- **Outbound Separation:** Outbound lead research is strictly separated from inbound website inquiries.
- **No Automatic Sending:** No emails or messages are sent automatically.
- **Zero Cost / No Subscriptions:** Uses free, permitted data sources, open-source libraries, and official government registries. No paid API credits or subscriptions.

---

## 2. Lead Qualification & Scoring Model (0–100 Scale)

Weights conform strictly to the approved specification:
- **Business & Industry Fit:** 25 points
- **Decision-Maker Identification:** 25 points
- **Evidence of Potential Problems (Ariyx Solutions):** 35 points
- **Contact Quality & Reachability:** 15 points

### The Tier 1 "Triple-Lock" Rule
A high numerical score alone **never** qualifies a lead as Tier 1. To achieve **Tier 1 (Hot)** status, a lead must satisfy all three locks simultaneously:
1. **Lock 1 (Decision-Maker):** Confirmed Founder, Co-Founder, Owner, CEO, or Managing Director.
2. **Lock 2 (Business Fit):** Core target industry (Marketing agency or Consulting firm) in target geography (US or UK for initial batches) with 3–50 staff.
3. **Lock 3 (Problem Evidence):** At least 12 points of observed potential buying signals supported by concrete DOM evidence and source URLs.

If any of these three locks fails, the lead is capped at **Tier 2 (Warm)** even if its numerical score is 80+.

---

## 3. Contact Verification Taxonomy & Free Mail-Routing Checks

Deliverability is **never guaranteed** based on an SMTP handshake, API response, or MX check alone. Every contact receives an explicit taxonomy status, kept strictly separate from regulatory `Compliance Status`:
1. `Provider-Verified`: Confirmed deliverable and **non-catch-all** via configured HTTPS verification API (optional).
2. `SMTP-Verified`: Confirmed deliverable (`250 OK` on target + `5xx` rejection on nonexistent random mailbox) via direct port 25 handshake (when port 25 is open).
3. `Publicly Listed (Unverified)`: Extracted directly from public business pages with active DNS MX records confirmed (`mx_found = True`), on a non-consumer corporate domain, without external API or SMTP confirmation. Allowed into the main sheet accurately labeled as unverified when no external verification API is used.
4. `Catch-All / Risky`: Mail server accepts all incoming mailboxes; high bounce/uncertainty risk. **Excluded** from main sheet.
5. `Verification Inconclusive`: DNS timeout or transient lookup failure. **Excluded** from main sheet.
6. `Invalid`: Syntax error, disposable/placeholder/telemetry address, or no active DNS MX records. **Excluded** from main sheet.
7. `Unavailable`: No public corporate email discovered. **Excluded** from main sheet.

*(Optional HTTPS verification providers remain supported in [`.env.example`](.env.example), but are not required under the zero-cost Gmail + Google Sheets workflow.)*

**Public Business Phone:** Formatted into international E.164 notation using Google's `phonenumbers` library.

---

## 4. Compliance & Regulatory Review Framework

Public availability of an email address is **never treated as marketing consent**. Leads are assigned cautious compliance statuses:
- **`REVIEW_REQUIRED`:** US (CAN-SPAM), UK (PECR corporate subscriber legitimate interest), Canada (CASL), and Australia (Spam Act). Specific business relevance and opt-out mechanics must be human-reviewed before outreach.
- **`RESTRICTED`:** Strict opt-in jurisdictions (e.g. Germany UWG §7, Austria) or detected consumer webmail (`@gmail.com`). Cold outreach strictly prohibited.
- **`ELIGIBILITY_NOT_ESTABLISHED`:** Country or legal entity type could not be determined. Must establish legal eligibility before proceeding.
- **`OPT_OUT_RECORDED`:** Prospect or domain is listed on the suppression list (`suppression.json`). Prohibited from contact.

---

## 5. Potential Buying Signals & Observation Evidence

Website observations are treated as **potential buying signals (hypotheses)**, not confirmed operational problems. Every signal records:
- Concrete evidence (DOM snippet or observed text).
- The exact source URL where it was detected.
- The corresponding Ariyx Systems solution.

---

## 6. How to Run a Manual Batch

Run batches manually via the CLI using the local virtual environment:

```bash
# 1. Run using curated seed dataset (Default 25 prospects)
.\lead-intelligence\.venv\Scripts\python.exe lead-intelligence\run_batch.py --count 25 --industry "Marketing agencies" --country "US"

# 2. Run using UK seed prospects
.\lead-intelligence\.venv\Scripts\python.exe lead-intelligence\run_batch.py --count 15 --industry "Consulting firms" --country "UK"

# 3. Run using free DuckDuckGo domain discovery
.\lead-intelligence\.venv\Scripts\python.exe lead-intelligence\run_batch.py --count 20 --industry "Marketing agencies" --country "UK" --use-search
```

Exported batches are saved to:
- `lead-intelligence/data/exports/<batch_name>_<timestamp>.csv` (22 standardized columns)
- `lead-intelligence/data/exports/<batch_name>_<timestamp>.json` (Full audit trail and raw signals)

---

## 7. Google Sheets Connection Requirements

To synchronize qualified outbound batches to the dedicated **Ariyx Systems – Outbound Intelligence Hub** spreadsheet without touching website endpoints or inbound sheets:

1. **Google Cloud Project:** Create a project in Google Cloud Console (Free tier).
2. **Enable Google Sheets API Only:** Enable `Google Sheets API` (scope: `https://www.googleapis.com/auth/spreadsheets`). Google Drive API is not required.
3. **Service Account Key Outside Git:** Create a Service Account, download its JSON key, and store it outside the repository (e.g., `C:\Users\ADMIN\.ariyx\credentials\google_service_account.json`).
4. **Share Dedicated Spreadsheet:** Share `Ariyx Systems – Outbound Intelligence Hub` with the service account email as **Editor**.
5. **Local Configuration:** Set `GOOGLE_SHEETS_CREDENTIALS_PATH`, `SPREADSHEET_ID`, and `WORKSHEET_NAME=Outbound Leads Intelligence` in `lead-intelligence/.env` (excluded from Git via `.gitignore`).
## 8. Daily Acceptance-Driven Automation (Target: 30 Accepted/Day for 30 Days)

To run the strict acceptance-driven pipeline (which continuously discovers, audits, verifies, and replaces rejected candidates until 30 strictly qualified, email-verified, compliance-reviewed B2B prospects are reached without lowering thresholds):

```bash
# Offline / local SQLite dry run (zero Google Sheets writes)
.\lead-intelligence\.venv\Scripts\python.exe lead-intelligence\run_daily.py --target 30 --max-days 30

# Live run syncing ONLY strictly accepted leads into Outbound Leads Intelligence + updating Daily Run Logs
.\lead-intelligence\.venv\Scripts\python.exe lead-intelligence\run_daily.py --target 30 --max-days 30 --sync-sheets
```

For Windows Task Scheduler daily scheduling and Apps Script template-segmented outreach setup, see:
- [`scripts/run_daily_job.ps1`](scripts/run_daily_job.ps1) and [`scripts/install_daily_schedule.ps1`](scripts/install_daily_schedule.ps1)
- [`apps_script/Code.gs`](apps_script/Code.gs) and [`apps_script/SETUP_GUIDE.md`](apps_script/SETUP_GUIDE.md)

