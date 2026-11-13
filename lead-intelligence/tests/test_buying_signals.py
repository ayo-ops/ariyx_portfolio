"""
Unit tests for BuyingSignalAuditor.
Verifies that website observations are treated as potential buying signals (hypotheses),
not confirmed operational problems, and always include source URLs and concrete DOM evidence.
"""

import pytest
from src.enrichment.buying_signals import BuyingSignalAuditor


@pytest.fixture
def auditor():
    return BuyingSignalAuditor()


def test_static_form_without_calendar(auditor):
    html = """
    <html>
      <body>
        <h1>Contact Us</h1>
        <form action="/submit" method="post">
          <input type="text" name="client_name" placeholder="Name">
          <input type="email" name="client_email" placeholder="Email">
          <textarea name="message"></textarea>
          <button type="submit">Send Message</button>
        </form>
      </body>
    </html>
    """
    page_url = "https://alpha-marketing.com/contact"
    audit = auditor.audit_page(html, page_url, is_contact_page=True)

    signals = audit["signals"]
    signal_types = [s["signal_type"] for s in signals]

    assert "STATIC_FORM_NO_CALENDAR" in signal_types
    static_signal = next(s for s in signals if s["signal_type"] == "STATIC_FORM_NO_CALENDAR")

    # Verify requirements: potential signal wording, evidence, source URL
    assert "potential buying signal" in static_signal["description"].lower()
    assert "found form element" in static_signal["evidence"].lower()
    assert static_signal["source_url"] == page_url
    assert static_signal["ariyx_solution"] == "Sub-60-Second Inbound Engagement Engine & Automated Calendar Booking"
    assert page_url in audit["fit_hypothesis"]


def test_manual_delay_friction(auditor):
    html = """
    <html>
      <body>
        <p>Thanks for your inquiry. A representative will get back to you within 24-48 hours to discuss pricing.</p>
      </body>
    </html>
    """
    page_url = "https://consultingpartners.co.uk/inquire"
    audit = auditor.audit_page(html, page_url)

    signals = audit["signals"]
    signal_types = [s["signal_type"] for s in signals]

    assert "MANUAL_FOLLOWUP_FRICTION" in signal_types
    friction_signal = next(s for s in signals if s["signal_type"] == "MANUAL_FOLLOWUP_FRICTION")
    assert "24-48 hours" in friction_signal["evidence"]
    assert friction_signal["source_url"] == page_url


def test_calendar_embed_prevents_static_form_signal(auditor):
    html = """
    <html>
      <body>
        <form action="/submit"><input type="email" name="email"></form>
        <!-- Embedded calendar -->
        <iframe src="https://calendly.com/agency/30min"></iframe>
      </body>
    </html>
    """
    audit = auditor.audit_page(html, "https://modernagency.com")
    signal_types = [s["signal_type"] for s in audit["signals"]]

    # Since an instant calendar is integrated, STATIC_FORM_NO_CALENDAR must NOT trigger
    assert "STATIC_FORM_NO_CALENDAR" not in signal_types


def test_hidden_inputs_and_csrf_tokens_ignored(auditor):
    """
    Verifies that hidden CSRF tokens, nonces, and internal form identifiers are excluded
    from form evidence strings.
    """
    html = """
    <html>
      <body>
        <form action="/contact" method="post">
          <input type="hidden" name="CRAFT_CSRF_TOKEN" value="xyz123">
          <input type="hidden" name="_wpnonce" value="abc789">
          <input type="hidden" name="action" value="submit_lead">
          <input type="text" name="full_name" placeholder="Full Name">
          <input type="email" name="work_email" placeholder="Work Email">
          <button type="submit">Submit</button>
        </form>
      </body>
    </html>
    """
    audit = auditor.audit_page(html, "https://agency.com/contact", is_contact_page=True)
    static_signal = next(s for s in audit["signals"] if s["signal_type"] == "STATIC_FORM_NO_CALENDAR")
    
    evidence = static_signal["evidence"]
    assert "CRAFT_CSRF_TOKEN" not in evidence
    assert "_wpnonce" not in evidence
    assert "action" not in evidence
    assert "full_name" in evidence
    assert "work_email" in evidence
