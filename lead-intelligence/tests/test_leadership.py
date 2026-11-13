"""
Unit tests for LeadershipFinder.
Tests that executive titles are extracted cleanly without trailing bio fragments.
"""

import pytest
from src.enrichment.leadership_finder import LeadershipFinder


@pytest.fixture
def finder():
    return LeadershipFinder()


def test_title_snippet_clean_extraction(finder):
    # Case: Alex Melen bio snippet
    raw_text = "Alex Melen Co-Founder Before SmartSites, Alex worked at various tech firms."
    extracted = finder._extract_title_snippet(raw_text)
    assert extracted == "Co-Founder"

    # Case: Compound title
    raw_text_2 = "Sarah Connor Founder & CEO of NextGen Systems."
    extracted_2 = finder._extract_title_snippet(raw_text_2)
    assert extracted_2 == "Founder & CEO"

    # Case: Managing Director
    raw_text_3 = "Sophie Roberts Managing Director Koozai Agency."
    extracted_3 = finder._extract_title_snippet(raw_text_3)
    assert extracted_3 == "Managing Director"

    # Case: Associate Partner (Q5 Partners - Pavlina Kouvela)
    raw_text_4 = "Pavlina Kouvela | Associate Partner | Head of People Performance"
    extracted_4 = finder._extract_title_snippet(raw_text_4)
    assert "Associate Partner" in extracted_4

    # Case: Trailing punctuation stripped
    raw_text_5 = "Amy Weeden, CEO, Propeller Consulting"
    extracted_5 = finder._extract_title_snippet(raw_text_5)
    assert extracted_5 == "CEO"


def test_leadership_finder_tier_classification(finder):
    assert finder._classify_role("Chief Executive Officer") == "tier_1"
    assert finder._classify_role("CEO") == "tier_1"
    assert finder._classify_role("Co-Founder") == "tier_1"
    assert finder._classify_role("Managing Director") == "tier_2"
    assert finder._classify_role("COO") == "tier_3"
    assert finder._classify_role("Software Engineer") == "tier_4"


def test_nested_json_ld_founder_extraction(finder):
    html = """
    <html><head>
      <script type="application/ld+json">
      {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": "Bright Spark Digital",
        "founder": {
          "@type": "Person",
          "name": "Claire Jenkins",
          "jobTitle": "Founder & Managing Director",
          "sameAs": "https://www.linkedin.com/in/claire-jenkins-uk/"
        }
      }
      </script>
    </head><body></body></html>
    """
    res = finder.find_leadership(html, "https://brightspark.co.uk/about")
    assert res["name"] == "Claire Jenkins"
    assert res["tier"] == "tier_1"
    assert res["decision_maker_linkedin"] == "https://www.linkedin.com/in/claire-jenkins-uk/"


def test_bio_prose_and_heading_pair_extraction(finder):
    html_heading = """
    <html><body>
      <div class="grid-item">
        <h3>Marcus Vance</h3>
        <p>Managing Partner</p>
        <a href="https://linkedin.com/in/marcus-vance">LinkedIn</a>
      </div>
    </body></html>
    """
    res1 = finder.find_leadership(html_heading, "https://vanceconsulting.com/team")
    assert res1["name"] == "Marcus Vance"
    assert res1["tier"] in ("tier_1", "tier_2")

    html_prose = """
    <html><body>
      <p>Brightwave Media was founded by Hannah Patel in Austin to help B2B brands scale pipeline.</p>
    </body></html>
    """
    res2 = finder.find_leadership(html_prose, "https://brightwave.com/about")
    assert res2["name"] == "Hannah Patel"
    assert res2["title"] == "Founder"
    assert res2["tier"] == "tier_1"


def test_non_person_phrases_and_call_to_actions_rejected(finder):
    # Reject CTAs, headings, non-person words, and testimonial quotes
    bad_candidates = [
        "View Bio >",
        "Message from the Founder",
        "Microsoft Advertising Partner Program",
        "Hearing Aid Ecommerce",
        "For Businesses",
        "Talk to Richard",
        "Right Fuel Card",
        "What inspired Noble Deeds?",
        "Shopify Partner",
    ]
    for bad in bad_candidates:
        assert not finder._is_plausible_person_name(bad), f"Expected '{bad}' to be rejected as a person name"

    # Confirmed real names must pass
    valid_names = [
        "Hayley Jones",
        "Peter McKenna",
        "Mike Grindy",
        "JON CLEMENTS",
        "Xanthe Vaughan Williams",
        "David Bryan",
        "George Butler",
        "Diane Mackie",
        "Brian Coane",
        "Jonny Kermode",
        "Roxie Payne",
    ]
    for val in valid_names:
        assert finder._is_plausible_person_name(val), f"Expected '{val}' to be accepted as plausible person name"

    # Testimonial quotes must be ignored in bio prose
    html_testimonial = """
    <html><body>
      <p>Working with this team was a crux of my business.” Kara Walsh, Founder The Snug Rug Company</p>
    </body></html>
    """
    res = finder.find_leadership(html_testimonial, "https://example.com/about")
    assert res["name"] == "Unavailable"
