/**
 * Ariyx Systems – Outbound Intelligence Hub
 * Segmented Email Campaign Integration (Apps Script Ready-Kit)
 *
 * SAFETY DEFAULT:
 *   LIVE_SENDING_ENABLED is hardcoded to false.
 *   No emails will be dispatched unless the operator explicitly approves compliance,
 *   populates approved templates in the "Email Templates" tab, sets Active = TRUE,
 *   marks specific rows "Approved for Outreach" in Column V, and enables live sending.
 *
 * Column Ownership Boundaries on "Outbound Leads Intelligence":
 *   - Cols A–U  (1–21):  Python Lead Intelligence system-managed
 *   - Cols V–AA (22–27): Operator-managed manual review & notes (NEVER overwritten by sync)
 *   - Cols AB–AG (28–33): Segmented Email Campaign tracking managed right of Col AA
 */

const CONFIG = {
  MAIN_SHEET: "Outbound Leads Intelligence",
  TEMPLATES_SHEET: "Email Templates",
  RUN_LOGS_SHEET: "Daily Run Logs",
  SUPPRESSION_SHEET: "Suppression & Opt-Outs",

  // HARD SAFETY LOCK: Keep false until templates, sending caps, timing, bounce, & compliance are approved.
  LIVE_SENDING_ENABLED: false,
  HARD_MAX_DAILY_EMAILS: 30,

  // Email verification (Col J) and compliance/outreach eligibility (Col U & Col V) are kept strictly separate.
  // Publicly Listed (Unverified) emails retain their exact unverified label in Col J while eligible for manual review.
  ALLOWED_EMAIL_STATUSES: ["SMTP-Verified", "Provider-Verified", "Publicly Listed (Unverified)"],
  BLOCKED_EMAIL_STATUSES: ["Invalid", "Unavailable", "Catch-All / Risky", "Verification Inconclusive"],
  BLOCKED_COMPLIANCE_STATUSES: ["RESTRICTED", "OPT_OUT_RECORDED", "ELIGIBILITY_NOT_ESTABLISHED"],
  REQUIRED_CAMPAIGN_STATUS_FOR_SEND: "Approved for Outreach",

  // 1-based column indices matching sheet_schema.py
  COL: {
    LEAD_ID: 1,                  // A
    DATE_RESEARCHED: 2,          // B
    BUSINESS_NAME: 3,            // C
    WEBSITE_URL: 4,              // D
    INDUSTRY: 5,                 // E
    COUNTRY_CITY: 6,             // F
    DM_NAME: 7,                  // G
    JOB_TITLE: 8,                // H
    EMAIL: 9,                    // I
    EMAIL_STATUS: 10,            // J
    PHONE: 11,                   // K
    COMPANY_SIZING: 14,          // N
    BUYING_SIGNALS: 16,          // P
    FIT_HYPOTHESIS: 17,          // Q
    SCORE: 19,                   // S
    TIER: 20,                    // T
    COMPLIANCE_STATUS: 21,       // U
    CAMPAIGN_STATUS: 22,         // V (Operator-managed gate)
    OUTREACH_CHANNEL: 24,        // X
    OUTREACH_DATE: 25,           // Y
    PROSPECT_RESPONSE: 26,       // Z
    MANUAL_NOTES: 27,            // AA
    OUTREACH_SEGMENT: 28,        // AB
    ASSIGNED_TEMPLATE_ID: 29,    // AC
    SEQUENCE_STEP: 30,           // AD
    LAST_EMAIL_SENT_AT: 31,      // AE
    GMAIL_THREAD_ID: 32,         // AF
    DELIVERY_STATUS: 33,         // AG
  }
};

const OUTREACH_HEADERS_AB_TO_AG = [
  "Outreach Segment",
  "Assigned Template ID",
  "Sequence Step",
  "Last Email Sent At",
  "Gmail Thread ID",
  "Delivery & Opt-Out Status"
];

const TEMPLATE_HEADERS = [
  "Template ID",
  "Template Name",
  "Outreach Segment",
  "Target Tier Filter",
  "Subject Template",
  "Plain Text Body",
  "HTML Body",
  "Active",
  "Daily Cap",
  "Compliance & Review Notes"
];

const SUPPRESSION_HEADERS = [
  "Recorded At",
  "Domain",
  "Email",
  "Company Name",
  "Source",
  "Reason",
  "Processed Locally"
];

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu("Ariyx Outreach")
    .addItem("1. Setup Campaign Columns (AB:AG) & Tabs", "setupCampaignHub")
    .addItem("2. Auto-Assign Segments & Dry-Run Preview (Zero Sends)", "previewOutreachQueue")
    .addItem("3. Preview Rendered Email for Selected Row (Zero Sends)", "previewSelectedRowTemplate")
    .addItem("4. Mark Selected Row Opt-Out / Suppressed", "recordSelectedRowOptOut")
    .addItem("5. Emergency Pause All Outreach", "pauseOutreach")
    .addItem("6. Resume Pause Lock (Still Dry-Run Unless Configured)", "resumeOutreachLock")
    .addToUi();
}

/**
 * Safely creates campaign tracking columns AB1:AG1 (leaving A:AA untouched)
 * and ensures Email Templates & Suppression tabs exist with inactive defaults.
 */
function setupCampaignHub() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const main = ss.getSheetByName(CONFIG.MAIN_SHEET);
  if (!main) {
    throw new Error("Main worksheet '" + CONFIG.MAIN_SHEET + "' not found.");
  }

  if (main.getMaxColumns() < 33) {
    main.insertColumnsAfter(main.getMaxColumns(), 33 - main.getMaxColumns());
  }
  main.getRange("AB1:AG1").setValues([OUTREACH_HEADERS_AB_TO_AG]);

  if (!ss.getSheetByName(CONFIG.TEMPLATES_SHEET)) {
    const tmpl = ss.insertSheet(CONFIG.TEMPLATES_SHEET);
    tmpl.getRange("A1:J4").setValues([
      TEMPLATE_HEADERS,
      [
        "TMPL_AGENCY_S2L_01",
        "Agency Speed-to-Lead Opportunity",
        "AGENCY_SPEED_TO_LEAD",
        "Tier 1 - Hot, Tier 2 - Warm",
        "Quick question on {{Company}}'s inbound lead flow",
        "Draft template placeholder - paste operator-approved copy before enabling.",
        "",
        "FALSE",
        10,
        "Disabled by default until compliance & unsubscribe footer approved."
      ],
      [
        "TMPL_AGENCY_AI_01",
        "Agency 24/7 Conversational AI",
        "AGENCY_CONVERSATIONAL_AI",
        "Tier 1 - Hot, Tier 2 - Warm",
        "Inbound screening idea for {{Company}}",
        "Draft template placeholder - paste operator-approved copy before enabling.",
        "",
        "FALSE",
        10,
        "Disabled by default until compliance & unsubscribe footer approved."
      ],
      [
        "TMPL_CONSULT_PIPE_01",
        "Consulting Pipeline & Booking Automation",
        "CONSULTING_PIPELINE_AUTOMATION",
        "Tier 1 - Hot, Tier 2 - Warm",
        "Consultation scheduling workflow for {{Company}}",
        "Draft template placeholder - paste operator-approved copy before enabling.",
        "",
        "FALSE",
        10,
        "Disabled by default until compliance & unsubscribe footer approved."
      ]
    ]);
  }

  if (!ss.getSheetByName(CONFIG.SUPPRESSION_SHEET)) {
    const supp = ss.insertSheet(CONFIG.SUPPRESSION_SHEET);
    supp.getRange("A1:G1").setValues([SUPPRESSION_HEADERS]);
  }

  SpreadsheetApp.getUi().alert(
    "Campaign Hub Ready.\n\nColumns AB1:AG1 and inactive starter tabs created safely. LIVE_SENDING_ENABLED remains FALSE (0 emails sent)."
  );
}

/**
 * Deterministic segment classifier matching Python AcceptanceEvaluator.assign_outreach_segment.
 */
function classifySegment_(industry, buyingSignals) {
  const ind = String(industry || "").toLowerCase();
  const sig = String(buyingSignals || "").toUpperCase();
  const isAgency = /marketing|seo|advertising|branding|digital|creative|public relations/.test(ind);
  const isConsulting = /consulting|consultancy|advisory|coach|accounting|financial/.test(ind);

  if (isAgency) {
    if (sig.indexOf("STATIC_FORM_NO_CALENDAR") !== -1 || sig.indexOf("MANUAL_FOLLOWUP_FRICTION") !== -1) {
      return "AGENCY_SPEED_TO_LEAD";
    }
    if (sig.indexOf("DISCONNECTED_FORM_STACK") !== -1 || sig.indexOf("NO_CONVERSATIONAL_WIDGET") !== -1) {
      return "AGENCY_CONVERSATIONAL_AI";
    }
    return "AGENCY_GENERAL_AUTOMATION";
  }

  if (isConsulting) {
    if (sig.indexOf("STATIC_FORM_NO_CALENDAR") !== -1 || sig.indexOf("MANUAL_FOLLOWUP_FRICTION") !== -1) {
      return "CONSULTING_PIPELINE_AUTOMATION";
    }
    return "CONSULTING_EXECUTIVE_OUTBOUND";
  }

  return "B2B_SERVICE_FOUNDER_DIRECT";
}

function loadSuppressionSets_(ss) {
  const domains = new Set();
  const emails = new Set();
  const sheet = ss.getSheetByName(CONFIG.SUPPRESSION_SHEET);
  if (!sheet || sheet.getLastRow() < 2) {
    return { domains, emails };
  }
  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, 7).getValues();
  for (const row of values) {
    const dom = normalizeDomain_(row[1]);
    const email = String(row[2] || "").trim().toLowerCase();
    if (dom) domains.add(dom);
    if (email) emails.add(email);
  }
  return { domains, emails };
}

function loadTemplatesBySegment_(ss) {
  const sheet = ss.getSheetByName(CONFIG.TEMPLATES_SHEET);
  const bySegment = {};
  if (!sheet || sheet.getLastRow() < 2) return bySegment;

  const rows = sheet.getRange(2, 1, sheet.getLastRow() - 1, 10).getValues();
  for (const row of rows) {
    const templateId = String(row[0] || "").trim();
    const segment = String(row[2] || "").trim();
    const tierFilter = String(row[3] || "").trim();
    const subject = String(row[4] || "");
    const plainBody = String(row[5] || "");
    const htmlBody = String(row[6] || "");
    const activeVal = String(row[7] || "").trim().toUpperCase();
    const dailyCap = Number(row[8] || 10);

    if (!templateId || !segment) continue;
    bySegment[segment] = {
      templateId,
      name: String(row[1] || ""),
      segment,
      tierFilter,
      subject,
      plainBody,
      htmlBody,
      active: activeVal === "TRUE",
      dailyCap: isNaN(dailyCap) ? 10 : dailyCap
    };
  }
  return bySegment;
}

/**
 * DRY-RUN PREVIEW ONLY: Assigns Col AB Segment & matches Template ID in Col AC
 * and reports exactly which leads would be eligible vs blocked. NEVER sends emails.
 */
function previewOutreachQueue() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const main = ss.getSheetByName(CONFIG.MAIN_SHEET);
  if (!main || main.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert("No prospect rows available yet.");
    return;
  }

  const lastRow = main.getLastRow();
  const rows = main.getRange(2, 1, lastRow - 1, 33).getValues();
  const suppression = loadSuppressionSets_(ss);
  const templates = loadTemplatesBySegment_(ss);

  let readyCount = 0;
  let awaitingReviewCount = 0;
  let blockedCount = 0;
  let unverifiedInQueueCount = 0;

  for (let i = 0; i < rows.length; i++) {
    const rowNum = i + 2;
    const row = rows[i];
    const domain = normalizeDomain_(row[CONFIG.COL.WEBSITE_URL - 1]);
    const email = String(row[CONFIG.COL.EMAIL - 1] || "").trim().toLowerCase();
    const emailStatus = String(row[CONFIG.COL.EMAIL_STATUS - 1] || "").trim();
    const compliance = String(row[CONFIG.COL.COMPLIANCE_STATUS - 1] || "").trim().toUpperCase();
    const campaignStatus = String(row[CONFIG.COL.CAMPAIGN_STATUS - 1] || "").trim();
    const tier = String(row[CONFIG.COL.TIER - 1] || "").trim();

    let segment = String(row[CONFIG.COL.OUTREACH_SEGMENT - 1] || "").trim();
    if (!segment) {
      segment = classifySegment_(row[CONFIG.COL.INDUSTRY - 1], row[CONFIG.COL.BUYING_SIGNALS - 1]);
      main.getRange(rowNum, CONFIG.COL.OUTREACH_SEGMENT).setValue(segment);
    }

    const tmpl = templates[segment];
    if (tmpl && !row[CONFIG.COL.ASSIGNED_TEMPLATE_ID - 1]) {
      main.getRange(rowNum, CONFIG.COL.ASSIGNED_TEMPLATE_ID).setValue(tmpl.templateId);
    }

    const suppressed = suppression.domains.has(domain) || suppression.emails.has(email);
    const emailEligible = CONFIG.ALLOWED_EMAIL_STATUSES.indexOf(emailStatus) !== -1;
    const isUnverifiedPublic = emailStatus === "Publicly Listed (Unverified)";
    const complianceNotProhibited = CONFIG.BLOCKED_COMPLIANCE_STATUSES.indexOf(compliance) === -1 && compliance !== "";
    const approvedByOperator = campaignStatus === CONFIG.REQUIRED_CAMPAIGN_STATUS_FOR_SEND;

    if (suppressed || !emailEligible || !complianceNotProhibited) {
      blockedCount++;
    } else if (!approvedByOperator) {
      awaitingReviewCount++;
      if (isUnverifiedPublic) unverifiedInQueueCount++;
    } else if (tmpl && tmpl.active && (!tmpl.tierFilter || tmpl.tierFilter.indexOf(tier) !== -1)) {
      readyCount++;
      if (isUnverifiedPublic) unverifiedInQueueCount++;
    } else {
      blockedCount++;
    }
  }

  SpreadsheetApp.getUi().alert(
    "Dry-Run Queue Preview (0 Emails Sent)\n\n" +
    "Eligible & Operator-Approved (matching active template): " + readyCount + "\n" +
    "Awaiting Operator Approval in Col V: " + awaitingReviewCount + "\n" +
    "  -> Of eligible leads above, labeled 'Publicly Listed (Unverified)': " + unverifiedInQueueCount + "\n" +
    "Blocked (Invalid Email / Catch-All / Compliance / Suppressed / Inactive Template): " + blockedCount + "\n\n" +
    "LIVE_SENDING_ENABLED = " + CONFIG.LIVE_SENDING_ENABLED + " (Gmail sends locked)"
  );
}

/**
 * DRY-RUN TEMPLATE PREVIEW FOR SELECTED ROW (0 emails sent, 0 Gmail writes).
 */
function previewSelectedRowTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  if (sheet.getName() !== CONFIG.MAIN_SHEET) {
    SpreadsheetApp.getUi().alert("Select a lead row in '" + CONFIG.MAIN_SHEET + "' first.");
    return;
  }
  const rowNum = sheet.getActiveRange().getRow();
  if (rowNum < 2) {
    SpreadsheetApp.getUi().alert("Select a data row (Row 2 or below).");
    return;
  }

  const row = sheet.getRange(rowNum, 1, 1, 33).getValues()[0];
  const segment = String(row[CONFIG.COL.OUTREACH_SEGMENT - 1] || "").trim() ||
    classifySegment_(row[CONFIG.COL.INDUSTRY - 1], row[CONFIG.COL.BUYING_SIGNALS - 1]);
  const templates = loadTemplatesBySegment_(ss);
  const tmpl = templates[segment];
  if (!tmpl) {
    SpreadsheetApp.getUi().alert("No template mapped for segment '" + segment + "' in the 'Email Templates' tab.");
    return;
  }

  const ctx = {
    dmName: row[CONFIG.COL.DM_NAME - 1],
    jobTitle: row[CONFIG.COL.JOB_TITLE - 1],
    company: row[CONFIG.COL.BUSINESS_NAME - 1],
    website: row[CONFIG.COL.WEBSITE_URL - 1],
    fitHypothesis: row[CONFIG.COL.FIT_HYPOTHESIS - 1]
  };
  const renderedSubject = renderTemplateText_(tmpl.subject, ctx);
  const renderedBody = renderTemplateText_(tmpl.plainBody, ctx);

  SpreadsheetApp.getUi().alert(
    "Template Preview (Row " + rowNum + " | 0 Emails Sent)\n\n" +
    "To: " + (row[CONFIG.COL.EMAIL - 1] || "Unavailable") + "\n" +
    "Email Status (Col J): " + (row[CONFIG.COL.EMAIL_STATUS - 1] || "Unavailable") + "\n" +
    "Compliance (Col U): " + (row[CONFIG.COL.COMPLIANCE_STATUS - 1] || "Unavailable") + "\n" +
    "Segment (Col AB): " + segment + " | Template: " + tmpl.templateId + " (Active=" + tmpl.active + ")\n\n" +
    "Subject: " + renderedSubject + "\n\n" +
    renderedBody
  );
}

/**
 * Operator opt-out button: updates selected row and logs entry to Suppression & Opt-Outs
 * so the Python pipeline syncs it into suppression.json automatically on next run.
 */
function recordSelectedRowOptOut() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getActiveSheet();
  if (sheet.getName() !== CONFIG.MAIN_SHEET) {
    SpreadsheetApp.getUi().alert("Select a lead row in '" + CONFIG.MAIN_SHEET + "' first.");
    return;
  }

  const rowNum = sheet.getActiveRange().getRow();
  if (rowNum < 2) {
    SpreadsheetApp.getUi().alert("Please select a data row (Row 2 or below).");
    return;
  }

  const website = sheet.getRange(rowNum, CONFIG.COL.WEBSITE_URL).getValue();
  const domain = normalizeDomain_(website);
  const businessName = sheet.getRange(rowNum, CONFIG.COL.BUSINESS_NAME).getValue();
  const email = String(sheet.getRange(rowNum, CONFIG.COL.EMAIL).getValue() || "").trim().toLowerCase();

  sheet.getRange(rowNum, CONFIG.COL.COMPLIANCE_STATUS).setValue("OPT_OUT_RECORDED");
  sheet.getRange(rowNum, CONFIG.COL.CAMPAIGN_STATUS).setValue("Suppressed");
  sheet.getRange(rowNum, CONFIG.COL.DELIVERY_STATUS).setValue("OPT_OUT_RECORDED");

  let suppSheet = ss.getSheetByName(CONFIG.SUPPRESSION_SHEET);
  if (!suppSheet) {
    suppSheet = ss.insertSheet(CONFIG.SUPPRESSION_SHEET);
    suppSheet.getRange("A1:G1").setValues([SUPPRESSION_HEADERS]);
  }
  suppSheet.appendRow([
    new Date().toISOString(),
    domain,
    email,
    businessName,
    "Sheets Operator Action",
    "Manual opt-out / do-not-contact",
    "FALSE"
  ]);

  SpreadsheetApp.getUi().alert("Recorded opt-out & suppression for " + (domain || email || businessName));
}

function pauseOutreach() {
  PropertiesService.getScriptProperties().setProperty("ARIYX_PAUSED", "true");
  SpreadsheetApp.getUi().alert("All Ariyx outreach is PAUSED.");
}

function resumeOutreachLock() {
  PropertiesService.getScriptProperties().setProperty("ARIYX_PAUSED", "false");
  SpreadsheetApp.getUi().alert("Pause flag cleared. Sending remains disabled while CONFIG.LIVE_SENDING_ENABLED is false.");
}

/**
 * Placeholder gated dispatch function.
 * Refuses execution unconditionally while CONFIG.LIVE_SENDING_ENABLED === false
 * or ARIYX_PAUSED === "true". Requires future Gmail send permission & approval.
 */
function runApprovedOutreachBatch_() {
  if (!CONFIG.LIVE_SENDING_ENABLED) {
    Logger.log("Blocked: CONFIG.LIVE_SENDING_ENABLED is false. No emails sent.");
    return { sent: 0, reason: "LIVE_SENDING_DISABLED" };
  }
  const paused = PropertiesService.getScriptProperties().getProperty("ARIYX_PAUSED");
  if (paused === "true") {
    Logger.log("Blocked: ARIYX_PAUSED is true.");
    return { sent: 0, reason: "PAUSED" };
  }

  // Note: When operator explicitly enables sending later, MailApp/GmailApp scope
  // and unsubscribe/postal-address footer checks + bounce scanner must be activated together.
  throw new Error("Live Gmail dispatch is intentionally not armed until user approves templates, sending limits, compliance, and bounce handling.");
}

function renderTemplateText_(templateStr, leadCtx) {
  const firstName = String(leadCtx.dmName || "").trim().split(/\s+/)[0] || "there";
  return String(templateStr || "")
    .replace(/\{\{FirstName\}\}/g, firstName)
    .replace(/\{\{FullName\}\}/g, leadCtx.dmName || "")
    .replace(/\{\{JobTitle\}\}/g, leadCtx.jobTitle || "")
    .replace(/\{\{Company\}\}/g, leadCtx.company || "")
    .replace(/\{\{Website\}\}/g, leadCtx.website || "")
    .replace(/\{\{FitHypothesis\}\}/g, leadCtx.fitHypothesis || "");
}

function normalizeDomain_(urlOrDomain) {
  let raw = String(urlOrDomain || "").trim().toLowerCase();
  if (!raw) return "";
  raw = raw.replace(/^https?:\/\//, "").replace(/^www\./, "");
  raw = raw.split("/")[0].split(":")[0].trim();
  return raw;
}
