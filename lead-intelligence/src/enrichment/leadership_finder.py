"""
Leadership and Decision-Maker Identification Module
Extracts decision-makers from public /team, /about, /leadership, JSON-LD schema,
and grounded bio copy.
Rule: Never invent names, titles, or LinkedIn URLs. Distinguish verified from unavailable.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

# Role hierarchy patterns (CEOs, Founders, Owners, Managing Partners are top priority Tier 1)
TIER_1_PATTERNS = [
    re.compile(r"\b(?:co-?founder|founder|owner|chief\s+executive\s+officer|ceo|managing\s+partner|principal)\b", re.I)
]

TIER_2_PATTERNS = [
    re.compile(r"\b(?:president|managing\s+director|partner)\b", re.I)
]

TIER_3_PATTERNS = [
    re.compile(r"\b(?:chief\s+operating\s+officer|coo|vp\s+of\s+operations|head\s+of\s+growth|vice\s+president)\b", re.I)
]

# LinkedIn profile URL regex
LINKEDIN_IN_REGEX = re.compile(r"https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?", re.I)
LINKEDIN_COMPANY_REGEX = re.compile(r"https?://(?:www\.)?linkedin\.com/company/([a-zA-Z0-9_-]+)/?", re.I)

NON_PERSON_PHRASES = re.compile(
    r"\b(?:team|about|leadership|our|services|agency|consulting|contact|privacy|policy|"
    r"careers|blog|insights|work|case\s+studies|clients|solutions|digital|marketing|seo|"
    r"growth|company|overview|menu|home|read\s+more|learn\s+more|book\s+a\s+call)\b",
    re.I,
)

# Grounded bio sentence patterns:
# e.g., "Founded by Sarah Jenkins" or "Sarah Jenkins, Founder & CEO"
BIO_FOUNDED_BY_REGEX = re.compile(
    r"\bfounded\s+by\s+([A-Z][a-z]{1,20}(?:\s+[A-Z][a-zA-Z'\-]{1,22}){1,2})\b"
)
BIO_NAME_ROLE_REGEX = re.compile(
    r"\b([A-Z][a-z]{1,20}(?:\s+[A-Z][a-zA-Z'\-]{1,22}){1,2})\s*(?:,|–|-|\||is\s+(?:the\s+)?)\s*"
    r"(Co-?Founder|Founder|Owner|Chief Executive Officer|CEO|Managing Director|Managing Partner|President|COO|Principal)\b"
)


NON_PERSON_NAME_WORDS = {
    "view", "bio", "bios", "message", "founder", "founders", "owner", "owners", "ceo", "coo", "cto",
    "cfo", "director", "directors", "partner", "partners", "partnership", "president", "principal",
    "executive", "leadership", "team", "our", "your", "the", "from", "for", "with", "and", "talk",
    "speak", "meet", "ask", "call", "contact", "about", "read", "more", "learn", "get", "touch",
    "program", "programmes", "advertising", "marketing", "digital", "agency",
    "ecommerce", "e-commerce", "hearing", "aid", "business", "businesses", "company", "services",
    "solutions", "media", "consulting", "consultancy", "group", "ltd", "llc", "inc", "corp",
    "microsoft", "google", "meta", "shopify", "hubspot", "wordpress", "certified", "award",
    "winner", "winning", "case", "study", "studies", "client", "clients", "customer", "customers",
    "stories", "story", "news", "insights", "blog", "inspired", "card", "right", "what", "how",
    "why", "who", "we", "are", "best", "top", "uk", "usa", "london", "manchester", "birmingham",
    "bristol", "edinburgh", "brighton", "leeds",
}


class LeadershipFinder:
    """
    Identifies bona fide decision-makers from public web data and structured schema.
    """

    def find_leadership(self, html: str, page_url: str) -> Dict[str, Any]:
        """
        Parses page HTML to extract leadership profiles and company social URLs.
        """
        if not html:
            return self._empty_result(page_url)

        soup = BeautifulSoup(html, "html.parser")

        # 1. Look for Company LinkedIn URL anywhere on the page
        company_linkedin = self._extract_company_linkedin(soup)

        # 2. Check JSON-LD structured data first (including nested founders/employees/authors)
        json_ld_result = self._extract_from_json_ld(soup, page_url)
        if json_ld_result and json_ld_result.get("name") != "Unavailable":
            json_ld_result["company_linkedin"] = company_linkedin or json_ld_result.get("company_linkedin", "Unavailable")
            return json_ld_result

        # 3. DOM parsing of team cards / leadership containers / semantic headings
        dom_result = self._extract_from_dom(soup, page_url)
        if dom_result and dom_result.get("name") != "Unavailable":
            dom_result["company_linkedin"] = company_linkedin or "Unavailable"
            return dom_result

        # 4. Grounded bio prose patterns ("Founded by ...", "Name, Founder & CEO")
        prose_result = self._extract_from_bio_prose(soup, page_url)
        if prose_result and prose_result.get("name") != "Unavailable":
            prose_result["company_linkedin"] = company_linkedin or "Unavailable"
            return prose_result

        # 5. Fallback if no specific individual is confirmed
        res = self._empty_result(page_url)
        res["company_linkedin"] = company_linkedin or "Unavailable"
        return res

    def _extract_company_linkedin(self, soup: BeautifulSoup) -> Optional[str]:
        """Searches for company LinkedIn profile link in header/footer/social links."""
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            match = LINKEDIN_COMPANY_REGEX.search(href)
            if match:
                return f"https://www.linkedin.com/company/{match.group(1)}/"
        return None

    def _extract_from_json_ld(self, soup: BeautifulSoup, page_url: str) -> Optional[Dict[str, Any]]:
        """Recursively parses schema.org/Person nodes (top-level, @graph, or nested founder/employee)."""
        scripts = soup.find_all("script", type="application/ld+json")
        candidates: List[Dict[str, Any]] = []

        def walk(node: Any) -> None:
            if isinstance(node, list):
                for item in node:
                    walk(item)
            elif isinstance(node, dict):
                node_type = node.get("@type", "")
                types = [node_type] if isinstance(node_type, str) else (node_type if isinstance(node_type, list) else [])
                if "Person" in types:
                    name = str(node.get("name") or "").strip()
                    job_title = str(node.get("jobTitle") or "").strip()
                    if self._is_plausible_person_name(name) and job_title:
                        tier = self._classify_role(job_title)
                        if tier != "tier_4":
                            linkedin = self._extract_linkedin_from_string(str(node)) or "Unavailable"
                            candidates.append({
                                "name": name,
                                "title": job_title,
                                "tier": tier,
                                "decision_maker_linkedin": linkedin,
                                "source_url": page_url,
                                "confidence": "HIGH_SCHEMA_VERIFIED",
                                "evidence": f"Found schema.org/Person structured markup ({job_title}: {name}) on {page_url}",
                            })
                # Recurse into nested objects (founder, employee, member, @graph, author, etc.)
                for val in node.values():
                    if isinstance(val, (dict, list)):
                        walk(val)

        for script in scripts:
            try:
                data = json.loads(script.string or "{}")
                walk(data)
            except Exception:
                continue

        if not candidates:
            return None

        tier_rank = {"tier_1": 0, "tier_2": 1, "tier_3": 2, "tier_4": 3}
        candidates.sort(key=lambda c: tier_rank.get(c["tier"], 9))
        return candidates[0]

    def _extract_from_dom(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
        """Scans DOM blocks and heading-role sibling pairs for executive decision-makers."""
        # Pass A: Structured team / card / bio containers
        containers = soup.find_all(
            ["div", "section", "article", "li", "figure"],
            class_=re.compile(r"team|member|leader|bio|person|staff|founder|director|executive|profile|card|people", re.I),
        )
        # Also match id attributes like #team, #leadership
        containers.extend(
            soup.find_all(["div", "section"], id=re.compile(r"team|leader|founder|people", re.I))
        )

        best_match: Optional[Dict[str, Any]] = None
        best_rank = 9

        for element in containers:
            res = self._inspect_card_element(element, page_url)
            if res:
                rank = {"tier_1": 0, "tier_2": 1, "tier_3": 2}.get(res["tier"], 9)
                if rank < best_rank:
                    best_match = res
                    best_rank = rank
                    if rank == 0:
                        return best_match

        if best_match:
            return best_match

        # Pass B: Heading tags followed by nearby role title text in parent card
        for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
            name_text = heading.get_text(" ", strip=True)
            if not self._is_plausible_person_name(name_text):
                continue
            parent = heading.parent
            if not isinstance(parent, Tag):
                continue
            # Check small local container only (prevent scanning entire body)
            card_text = parent.get_text(" ", strip=True)
            if len(card_text) > 500:
                sibling_bits = []
                for sib in list(heading.next_siblings)[:4]:
                    if isinstance(sib, Tag):
                        sibling_bits.append(sib.get_text(" ", strip=True))
                card_text = " ".join(sibling_bits)

            for role_pattern, tier in self._get_priority_role_checks():
                if role_pattern.search(card_text):
                    title_clean = self._extract_title_snippet(card_text)
                    dm_linkedin = "Unavailable"
                    for a in parent.find_all("a", href=True):
                        match = LINKEDIN_IN_REGEX.search(a["href"])
                        if match:
                            dm_linkedin = f"https://www.linkedin.com/in/{match.group(1)}/"
                            break
                    return {
                        "name": name_text,
                        "title": title_clean,
                        "tier": tier,
                        "decision_maker_linkedin": dm_linkedin,
                        "source_url": page_url,
                        "confidence": "DOM_CONFIRMED",
                        "evidence": f"Found heading + role pair on {page_url} ({name_text}: {title_clean})",
                    }

        return self._empty_result(page_url)

    def _inspect_card_element(self, element: Tag, page_url: str) -> Optional[Dict[str, Any]]:
        block_text = element.get_text(" ", strip=True)
        # Skip huge wrapper containers that hold multiple bios mixed together when possible
        if len(block_text) > 1200:
            return None

        for role_pattern, tier in self._get_priority_role_checks():
            if role_pattern.search(block_text):
                for tag_name in ["h2", "h3", "h4", "h5", "strong", "b", "span"]:
                    for name_tag in element.find_all(tag_name, limit=4):
                        candidate_name = re.sub(r"\s+", " ", name_tag.get_text(" ", strip=True)).strip()
                        # Strip trailing ", Founder" if heading combined both
                        if "," in candidate_name:
                            candidate_name = candidate_name.split(",", 1)[0].strip()
                        if self._is_plausible_person_name(candidate_name):
                            dm_linkedin = "Unavailable"
                            for a in element.find_all("a", href=True):
                                match = LINKEDIN_IN_REGEX.search(a["href"])
                                if match:
                                    dm_linkedin = f"https://www.linkedin.com/in/{match.group(1)}/"
                                    break
                            title_clean = self._extract_title_snippet(block_text)
                            return {
                                "name": candidate_name,
                                "title": title_clean,
                                "tier": tier,
                                "decision_maker_linkedin": dm_linkedin,
                                "source_url": page_url,
                                "confidence": "DOM_CONFIRMED",
                                "evidence": f"Found leadership member card on {page_url} ({candidate_name}: {title_clean})",
                            }
        return None

    def _extract_from_bio_prose(self, soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
        """Extracts explicitly attributed executive names from About/Story prose."""
        text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
        if not text:
            return self._empty_result(page_url)

        m_named = BIO_NAME_ROLE_REGEX.search(text)
        if m_named:
            name = m_named.group(1).strip()
            raw_role = m_named.group(2).strip()

            # Guard against client testimonial quotes: check 30 chars before name for closing quotation marks
            prefix = text[max(0, m_named.start() - 30):m_named.start()].strip()
            is_quote = any(q in prefix for q in ('"', "”", "’", "'", "»", "“"))

            if not is_quote and self._is_plausible_person_name(name):
                tier = self._classify_role(raw_role)
                if tier != "tier_4":
                    snippet = text[max(0, m_named.start() - 25):min(len(text), m_named.end() + 45)].strip()
                    return {
                        "name": name,
                        "title": self._extract_title_snippet(raw_role),
                        "tier": tier,
                        "decision_maker_linkedin": "Unavailable",
                        "source_url": page_url,
                        "confidence": "PROSE_ATTRIBUTED",
                        "evidence": f"Observed executive attribution on {page_url}: '...{snippet}...'",
                    }

        m_founded = BIO_FOUNDED_BY_REGEX.search(text)
        if m_founded:
            name = m_founded.group(1).strip()
            prefix = text[max(0, m_founded.start() - 30):m_founded.start()].strip()
            is_quote = any(q in prefix for q in ('"', "”", "’", "'", "»", "“"))
            if not is_quote and self._is_plausible_person_name(name):
                snippet = text[max(0, m_founded.start() - 20):min(len(text), m_founded.end() + 45)].strip()
                return {
                    "name": name,
                    "title": "Founder",
                    "tier": "tier_1",
                    "decision_maker_linkedin": "Unavailable",
                    "source_url": page_url,
                    "confidence": "PROSE_ATTRIBUTED",
                    "evidence": f"Observed founder credit on {page_url}: '...{snippet}...'",
                }

        return self._empty_result(page_url)

    @staticmethod
    def _is_plausible_person_name(name: str) -> bool:
        cleaned = re.sub(r"\s+", " ", (name or "")).strip()
        if not (4 <= len(cleaned) <= 45):
            return False
        if NON_PERSON_PHRASES.search(cleaned):
            return False
        # Reject non-alphabetic symbols common in CTAs, headings, cards, and punctuation
        if any(ch.isdigit() or ch in "@/:;|()[]{}>—–•\"'“”!?*#+=\\<>" for ch in cleaned):
            return False
        words = [w for w in cleaned.split(" ") if w]
        if not (2 <= len(words) <= 4):
            return False
        # Reject if any token is a known role, business word, or CTA verb
        for w in words:
            w_lower = re.sub(r"[^a-z]", "", w.lower())
            if w_lower in NON_PERSON_NAME_WORDS:
                return False
        # Require majority capitalized name tokens (First Last)
        cap_words = sum(1 for w in words if w[0].isupper())
        return cap_words >= 2

    def _classify_role(self, title: str) -> str:
        """Categorizes job title into tier_1, tier_2, tier_3, or tier_4."""
        for pattern in TIER_1_PATTERNS:
            if pattern.search(title):
                return "tier_1"
        for pattern in TIER_2_PATTERNS:
            if pattern.search(title):
                return "tier_2"
        for pattern in TIER_3_PATTERNS:
            if pattern.search(title):
                return "tier_3"
        return "tier_4"

    def _get_priority_role_checks(self):
        """Returns sorted list of regexes for DOM iteration."""
        checks = []
        for p in TIER_1_PATTERNS:
            checks.append((p, "tier_1"))
        for p in TIER_2_PATTERNS:
            checks.append((p, "tier_2"))
        for p in TIER_3_PATTERNS:
            checks.append((p, "tier_3"))
        return checks

    @staticmethod
    def _extract_title_snippet(text: str) -> str:
        """Extracts clean executive title without trailing biography or sentence fragments."""
        match = re.search(
            r"\b(Co-?Founder|Founder|Owner|Chief Executive Officer|CEO|Managing Director|Managing Partner|President|Chief Operating Officer|COO|Principal|Associate Partner|Partner)\b(?:\s+(?:and|&)\s+\b(Co-?Founder|Founder|Owner|CEO|Managing Director|Managing Partner|President|COO|Partner)\b)?(?:\s*\|\s*|\s*,\s*)?(?:Head\s+of\s+[A-Za-z\s]+)?",
            text,
            re.I
        )
        if match:
            return match.group(0).strip().rstrip(" ,|–—")
        return "Executive Leadership"

    @staticmethod
    def _extract_linkedin_from_string(text: str) -> Optional[str]:
        match = LINKEDIN_IN_REGEX.search(text)
        if match:
            return f"https://www.linkedin.com/in/{match.group(1)}/"
        return None

    @staticmethod
    def _empty_result(page_url: str) -> Dict[str, Any]:
        return {
            "name": "Unavailable",
            "title": "Unavailable",
            "tier": "tier_4",
            "decision_maker_linkedin": "Unavailable",
            "company_linkedin": "Unavailable",
            "source_url": page_url,
            "confidence": "UNAVAILABLE",
            "evidence": "No leadership profile discovered from public website."
        }
