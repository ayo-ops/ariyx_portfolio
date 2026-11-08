import {
  Clock,
  UserX,
  CalendarX,
  FileSpreadsheet,
  Unplug,
  Zap,
  CheckCircle2,
  Workflow,
  Bot,
  Layers,
  ArrowRight,
} from "lucide-react";

export const SOLUTIONS = [
  {
    id: "missed-leads",
    problemNumber: "01",
    tag: "Speed-to-Lead Failure",
    problemTitle: "Inquiries Sitting Unanswered While Leads Move to Competitors",
    problemDesc:
      "When a potential client submits an inquiry or requests a quote, every minute of delay cuts your conversion rate. In most businesses, inquiries sit in an email inbox for hours or days before a human notices them.",
    impact: "Over 75% of high-intent buyers sign with the vendor who responds first.",
    solutionTitle: "Sub-60-Second Inbound Engagement Engine",
    solutionDesc:
      "We engineer instant multi-channel response triggers. The moment a lead submits a form, an automated sequence immediately validates their details, sends a personalized SMS/WhatsApp confirmation, and prompts them to self-book an appointment on your calendar.",
    workflowSteps: [
      "Real-time webhook triggers upon webform or ad submission",
      "Lead phone and email automatically validated and deduplicated",
      "Instant 2-way SMS or WhatsApp conversation initiated within 45 seconds",
      "Automated prompt to self-select a time slot on your live calendar",
    ],
    technicalHighlights: ["GoHighLevel Workflows", "Twilio / WhatsApp API", "Instant Webhooks", "Calendar Sync"],
    accent: "electric",
  },
  {
    id: "poor-follow-up",
    problemNumber: "02",
    tag: "Pipeline Leakage",
    problemTitle: "Leads Stalling After Initial Contact With Inconsistent Nurture",
    problemDesc:
      "Most sales reps follow up once or twice, get busy, and let qualified prospects fall through the cracks. Without automated persistence, up to 60% of potential revenue is lost to forgotten pipelines.",
    impact: "Unworked leads decay in value within 48 hours without systematic touchpoints.",
    solutionTitle: "Structured Multi-Channel Nurture & Pipeline Routing",
    solutionDesc:
      "We structure custom CRM pipelines where every opportunity has an explicit status, assigned owner, and automated follow-up cadence. If a prospect doesn't book, automated behavioral sequences keep them warm without requiring manual rep effort.",
    workflowSteps: [
      "Visual pipeline stages clearly demarcate qualified vs. stalled deals",
      "Automated 7-touch behavioral email and SMS follow-up sequence",
      "Task assignment and notifications sent to sales reps if manual action is needed",
      "Automated long-term reactivation campaigns for dormant contacts",
    ],
    technicalHighlights: ["Custom CRM Schemas", "Deal Scoring", "Behavioral Drips", "Pipeline Automations"],
    accent: "teal",
  },
  {
    id: "high-no-shows",
    problemNumber: "03",
    tag: "Calendar Drop-Off",
    problemTitle: "Empty Time Slots Caused by Appointment No-Shows and Cancellations",
    problemDesc:
      "Prospects book appointments days in advance, forget their commitment, or encounter conflicts without a friction-free way to reschedule. Your sales team wastes valuable hours waiting on empty Zoom or phone links.",
    impact: "No-shows burn expensive sales rep hours and disrupt revenue forecasting.",
    solutionTitle: "Two-Way Confirmation & 1-Click Self-Rescheduling System",
    solutionDesc:
      "We deploy multi-stage reminder journeys that require active confirmation. If a lead needs to change their time, they receive an instant self-service rescheduling link that updates your calendar and frees up the old slot for other prospects.",
    workflowSteps: [
      "Immediate calendar invite sent with dynamic Google/Outlook integration",
      "24-hour and 2-hour SMS & email reminders with confirmation request",
      "1-click self-service reschedule link reduces friction and cancellations",
      "Automated missed-appointment recovery workflow triggered within 15 minutes",
    ],
    technicalHighlights: ["Two-Way Calendar Sync", "SMS Reminder Logic", "Dynamic Reschedule Links", "Zoom/Meet API"],
    accent: "electric",
  },
  {
    id: "manual-processes",
    problemNumber: "04",
    tag: "Operational Overhead",
    problemTitle: "Teams Drowning in Repetitive Admin, Data Entry, and Copy-Pasting",
    problemDesc:
      "High-value team members spend 10–20 hours each week typing lead details into spreadsheets, creating duplicate contracts, emailing onboarding links, and notifying other departments by hand.",
    impact: "Manual data entry introduces human error and caps your operational capacity.",
    solutionTitle: "End-to-End Business Process Automation Architecture",
    solutionDesc:
      "We replace manual task handoffs with event-driven automation. When a deal reaches 'Closed Won', contracts are generated, client folders are created, billing subscriptions are initiated, and your fulfillment team is notified automatically.",
    workflowSteps: [
      "Automatic contract & invoice generation upon deal stage progression",
      "Cross-departmental notifications routed to Slack, email, or project boards",
      "Client onboarding portal credentials generated and delivered securely",
      "Internal task lists created and delegated based on service requirements",
    ],
    technicalHighlights: ["n8n / Make Orchestration", "Document Generation", "Stripe Billing Webhooks", "Slack / Team Alerts"],
    accent: "teal",
  },
  {
    id: "disconnected-tools",
    problemNumber: "05",
    tag: "Data Silos",
    problemTitle: "Software Stacks That Don't Talk to Each Other, Creating Data Clutter",
    problemDesc:
      "Businesses often pay for 6 to 10 different SaaS tools—CRM, website, email software, payment processors, support desks, and calendars—none of which synchronize smoothly, forcing manual reconciliation.",
    impact: "Mismatched customer records, lost invoices, and zero unified executive reporting.",
    solutionTitle: "Bi-Directional API & Webhook Integration Bridges",
    solutionDesc:
      "We build custom middleware bridges connecting all parts of your technology stack. Whether connecting GoHighLevel to custom databases, Stripe, or proprietary backends, data flows bi-directionally with full validation and error recovery.",
    workflowSteps: [
      "Custom REST API middleware and webhook receivers programmed",
      "Bi-directional data sync eliminates duplicate contacts and mismatched records",
      "Automated payload validation and retry mechanisms prevent data loss",
      "Single unified CRM dashboard provides clean, executive-level visibility",
    ],
    technicalHighlights: ["Custom REST APIs", "Webhook Receivers", "Error Catching & Retries", "Unified Master Database"],
    accent: "electric",
  },
];
