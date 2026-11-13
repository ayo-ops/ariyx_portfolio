"""
Buying Signals and Website Observation Auditor
Analyzes public website elements to identify POTENTIAL buying signals and technical fit for Ariyx Systems.
Rule: All observations are treated as potential signals (hypotheses), not confirmed operational problems.
Every signal must include concrete evidence and the exact source URL.
"""

import logging
import re
from typing import Any, Dict, List, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Known booking calendar identifiers in embeds/scripts
CALENDAR_PATTERNS = [
    re.compile(r"calendly\.com", re.I),
    re.compile(r"acuityscheduling\.com", re.I),
    re.compile(r"leadconnectorhq\.com", re.I),
    re.compile(r"msgsndr\.com", re.I),  # GoHighLevel
    re.compile(r"hubspot\.com/meetings", re.I),
    re.compile(r"meetings\.hubspot\.com", re.I),
    re.compile(r"tidycal\.com", re.I),
    re.compile(r"oncehub\.com", re.I),
    re.compile(r"youcanbook\.me", re.I),
    re.compile(r"cal\.com/", re.I),
    re.compile(r"savvycal\.com", re.I),
    re.compile(r"chili\s*piper", re.I),
]

# Known chat widget identifiers
CHAT_PATTERNS = [
    re.compile(r"leadconnector", re.I),
    re.compile(r"intercom", re.I),
    re.compile(r"drift\.com", re.I),
    re.compile(r"tidio", re.I),
    re.compile(r"crisp\.chat", re.I),
    re.compile(r"zendesk\.com", re.I),
    re.compile(r"livechat", re.I),
    re.compile(r"hubspot-messages", re.I),
    re.compile(r"tawk\.to", re.I),
    re.compile(r"freshchat", re.I),
]

# Manual delay / callback friction phrases
FRICTION_PHRASES = [
    re.compile(r"within\s+(?:\d+\s*(?:-\s*\d+)?\s*(?:hours|business\s+days))", re.I),
    re.compile(r"get\s+back\s+to\s+you\s+(?:shortly|soon|within|as\s+soon)", re.I),
    re.compile(r"respond\s+(?:shortly|soon|within|to\s+all\s+inquiries)", re.I),
    re.compile(r"request\s+a\s+(?:call\s*back|quote|proposal|consultation)", re.I),
    re.compile(r"fill\s+(?:out|in)\s+the\s+(?:contact\s+)?form", re.I),
    re.compile(r"we\s+will\s+review\s+your\s+application", re.I),
]

# Internal form values and security tokens to ignore during form inspection
IGNORED_INTERNAL_FIELD_PATTERNS = [
    re.compile(r"csrf", re.I),
    re.compile(r"token", re.I),
    re.compile(r"nonce", re.I),
    re.compile(r"_wpcf7", re.I),
    re.compile(r"action", re.I),
    re.compile(r"handle", re.I),
    re.compile(r"form_id", re.I),
    re.compile(r"form_build_id", re.I),
    re.compile(r"timestamp", re.I),
    re.compile(r"honeypot", re.I),
]


class BuyingSignalAuditor:
    """
    Audits website HTML across single or multiple pages to detect potential
    operational bottlenecks and automation opportunities.
    """

    def audit_page(self, html: str, page_url: str, is_contact_page: bool = False) -> Dict[str, Any]:
        """
        Parses page HTML to identify potential buying signals with concrete DOM evidence.
        """
        if not html:
            return {
                "signals": [],
                "signal_score": 0,
                "fit_hypothesis": "Insufficient public website data to observe buying signals.",
                "evidence_urls": []
            }

        soup = BeautifulSoup(html, "html.parser")
        signals: List[Dict[str, Any]] = []
        html_lower = html.lower()

        # 1. Check for Calendar Self-Scheduling Embeds
        has_calendar = any(pattern.search(html) for pattern in CALENDAR_PATTERNS)

        # 2. Check for Chat / Conversational Widgets
        has_chat = any(pattern.search(html) for pattern in CHAT_PATTERNS)

        # 3. Analyze Forms (Ignore hidden inputs, CSRF tokens, and search boxes)
        forms = soup.find_all("form")
        has_static_form = False
        form_evidence_snippet = ""
        form_classes: List[str] = []

        for form in forms:
            classes = form.get("class", [])
            if isinstance(classes, list):
                form_classes.extend([str(c) for c in classes])

            form_role = (form.get("role") or "").lower()
            form_action = (form.get("action") or "").lower()
            if form_role == "search" or "search" in " ".join(classes).lower() or "?s=" in form_action:
                continue

            # Collect visible inputs only (exclude type="hidden", type="submit", etc.)
            visible_inputs = []
            for tag in form.find_all(["input", "textarea", "select"]):
                tag_type = (tag.get("type") or "text").lower()
                if tag_type in ("hidden", "submit", "button", "reset", "image", "search"):
                    continue
                name = tag.get("name") or tag.get("id") or tag.get("placeholder") or tag_type
                if name:
                    if any(p.search(name) for p in IGNORED_INTERNAL_FIELD_PATTERNS):
                        continue
                    visible_inputs.append(name.strip())

            # Check for typical contact/lead form fields
            has_name = any("name" in n.lower() for n in visible_inputs)
            has_email = any("email" in n.lower() or "mail" in n.lower() for n in visible_inputs)
            has_msg = any(k in n.lower() for n in visible_inputs for k in ("message", "comment", "project", "details", "inquiry"))

            if has_email or has_name or has_msg or len(visible_inputs) >= 2:
                has_static_form = True
                cleaned_fields = list(dict.fromkeys(visible_inputs))[:4]
                fields_str = ", ".join(cleaned_fields) if cleaned_fields else "standard contact inputs"
                form_evidence_snippet = f"<form with visible fields: {fields_str}>"
                break

        # Detect third-party embedded forms without calendar sync (HubSpot Form / Typeform / Jotform / Webflow)
        if not has_static_form and not has_calendar:
            if re.search(r"hbspt\.forms\.create|typeform\.com/to/|jotform\.com", html, re.I):
                has_static_form = True
                form_evidence_snippet = "<embedded third-party inquiry form without calendar embed>"

        # SIGNAL 1: Static lead inquiry form without automated self-scheduling
        if has_static_form and not has_calendar:
            signals.append({
                "signal_type": "STATIC_FORM_NO_CALENDAR",
                "points": 12,
                "description": "Potential buying signal: Static lead inquiry form observed without automated instant self-scheduling calendar (potential opportunity for inbound scheduling).",
                "evidence": f"Found form element ({form_evidence_snippet}) on {page_url} with no integrated calendar embed (Calendly, GoHighLevel, Acuity).",
                "source_url": page_url,
                "ariyx_solution": "Sub-60-Second Inbound Engagement Engine & Automated Calendar Booking"
            })

        # SIGNAL 2: Multi-step booking friction / manual callback language
        for phrase_pattern in FRICTION_PHRASES:
            match = phrase_pattern.search(html)
            if match:
                start = max(0, match.start() - 40)
                end = min(len(html), match.end() + 40)
                raw_snippet = re.sub(r"\s+", " ", BeautifulSoup(html[start:end], "html.parser").get_text()).strip()
                signals.append({
                    "signal_type": "MANUAL_FOLLOWUP_FRICTION",
                    "points": 10,
                    "description": "Potential buying signal: Observed text indicating manual response delay or callback scheduling (potential opportunity for speed-to-lead automation).",
                    "evidence": f"Text observation: '...{raw_snippet[:120]}...'",
                    "source_url": page_url,
                    "ariyx_solution": "Instant Speed-to-Lead SMS & Multi-channel Automated Qualification"
                })
                break

        # SIGNAL 3: Disconnected / legacy website form plugins
        legacy_indicators = [
            ("wpcf7", "WordPress Contact Form 7"),
            ("elementor-form", "Elementor Form without visible CRM webhook"),
            ("gform_wrapper", "Gravity Forms without calendar sync"),
            ("ninja-forms", "Ninja Forms"),
            ("wpforms-form", "WPForms handler"),
            ("sqs-block-form", "Squarespace static form"),
        ]
        detected_legacy = []
        for class_name, tech_label in legacy_indicators:
            if any(class_name in str(c) for c in form_classes) or class_name in html_lower:
                detected_legacy.append(tech_label)

        if detected_legacy:
            signals.append({
                "signal_type": "DISCONNECTED_FORM_STACK",
                "points": 8,
                "description": "Potential buying signal: Detected standard CMS form handler without direct CRM pipeline integration (potential opportunity for CRM webhook integration).",
                "evidence": f"Detected form markup: {', '.join(detected_legacy)} on {page_url}.",
                "source_url": page_url,
                "ariyx_solution": "GoHighLevel Snapshot / CRM Pipeline Architecture & Webhook Middleware"
            })

        # SIGNAL 4: Absence of conversational chat widget
        if not has_chat:
            signals.append({
                "signal_type": "NO_CONVERSATIONAL_WIDGET",
                "points": 5,
                "description": "Potential buying signal: Absence of live web chat or conversational screening assistant in public DOM (potential opportunity for 24/7 conversational assistant).",
                "evidence": f"No chat or conversational capture scripts detected in page DOM at {page_url}.",
                "source_url": page_url,
                "ariyx_solution": "24/7 AI Inbound Screening & Voice / Web Chat Agents"
            })

        total_score = min(35, sum(s["points"] for s in signals))
        evidence_urls = list(dict.fromkeys(s["source_url"] for s in signals))
        primary_url = evidence_urls[0] if evidence_urls else page_url
        fit_hypothesis = self._build_fit_hypothesis(signals, primary_url)

        return {
            "signals": signals,
            "signal_score": total_score,
            "fit_hypothesis": fit_hypothesis,
            "evidence_urls": evidence_urls
        }

    def audit_pages(self, pages: List[Tuple[str, str, bool]]) -> Dict[str, Any]:
        """
        Audits multiple pages (list of (html, page_url, is_contact_page)) for one business
        and merges unique observed signals without double-counting the same signal type.
        Also clears NO_CONVERSATIONAL_WIDGET or STATIC_FORM_NO_CALENDAR if calendar/chat is found on any audited page.
        """
        if not pages:
            return self.audit_page("", "", False)

        merged_signals_by_type: Dict[str, Dict[str, Any]] = {}
        any_calendar = False
        any_chat = False

        for html, page_url, is_contact in pages:
            if not html:
                continue
            if any(p.search(html) for p in CALENDAR_PATTERNS):
                any_calendar = True
            if any(p.search(html) for p in CHAT_PATTERNS):
                any_chat = True

            res = self.audit_page(html, page_url, is_contact_page=is_contact)
            for sig in res.get("signals", []):
                stype = sig.get("signal_type", "")
                if stype not in merged_signals_by_type:
                    merged_signals_by_type[stype] = sig
                elif is_contact:
                    # Prefer contact page evidence over homepage if both found
                    merged_signals_by_type[stype] = sig

        # Cross-page consistency: never report NO_CHAT or NO_CALENDAR if detected on another audited page of the same site
        if any_calendar:
            merged_signals_by_type.pop("STATIC_FORM_NO_CALENDAR", None)
        if any_chat:
            merged_signals_by_type.pop("NO_CONVERSATIONAL_WIDGET", None)

        signals = list(merged_signals_by_type.values())
        total_score = min(35, sum(s["points"] for s in signals))
        evidence_urls = list(dict.fromkeys(s["source_url"] for s in signals))
        fallback_url = next((u for h, u, _ in pages if h and u), "")
        fit_hypothesis = self._build_fit_hypothesis(signals, evidence_urls[0] if evidence_urls else fallback_url)

        return {
            "signals": signals,
            "signal_score": total_score,
            "fit_hypothesis": fit_hypothesis,
            "evidence_urls": evidence_urls,
        }

    @staticmethod
    def _build_fit_hypothesis(signals: List[Dict[str, Any]], primary_url: str) -> str:
        """Constructs a deterministic, evidence-based fit explanation separating factual observations from commercial hypotheses."""
        if not signals:
            return f"Hypothesis (Baseline Audit): Standard service business on {primary_url}; baseline CRM and automation review recommended."

        signal_types = {s["signal_type"] for s in signals}
        observations = []

        if "STATIC_FORM_NO_CALENDAR" in signal_types:
            observations.append("website relies on a static contact form without automated calendar self-scheduling")
        if "MANUAL_FOLLOWUP_FRICTION" in signal_types:
            observations.append("public text indicates manual callback delays")
        if "DISCONNECTED_FORM_STACK" in signal_types:
            observations.append("uses CMS form handlers without direct CRM webhook pipeline sync")
        if "NO_CONVERSATIONAL_WIDGET" in signal_types:
            observations.append("lacks an automated 24/7 conversational screening assistant")

        joined_obs = "; ".join(observations)
        return (
            f"Ariyx Systems Fit Hypothesis (Potential Automation Opportunity): Public website exhibits observed characteristics: {joined_obs}. "
            f"These observations represent potential commercial opportunities for introducing Ariyx Sub-60-Second Inbound Engagement Engine and automated CRM pipeline setup, subject to direct client discovery. "
            f"Source Evidence URL: {primary_url}"
        )
