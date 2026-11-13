"""
Free Multi-Source Domain Discovery Module
Discovers independent B2B service businesses (marketing agencies, consulting firms,
coaches, advisory firms) across approved target markets (US, UK, CA, AU) using ONLY
free, permitted, keyless/open sources:
1. DuckDuckGo HTML Search (html.duckduckgo.com/html/ POST with /l/?uddg= redirect decoding)
2. Wikidata SPARQL Open Business Registry (official websites wdt:P856 by industry & country)
3. UK Companies House Official API (optional when user provides free developer API key)

Supports persistent seen-domain filtering and cursor rotation so daily runs avoid
repeatedly returning the same candidates across a 30-day campaign.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs, unquote, urlparse

import primp
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Diverse, city-and-niche rotated search queries across approved B2B markets
EXPANDED_QUERY_BANK: List[Dict[str, str]] = [
    # UK Marketing Agencies
    {"industry": "Marketing agencies", "country": "UK", "city": "London", "kl": "uk-en", "q": "digital marketing agency London our team contact"},
    {"industry": "Marketing agencies", "country": "UK", "city": "Manchester", "kl": "uk-en", "q": "B2B marketing agency Manchester leadership contact"},
    {"industry": "Marketing agencies", "country": "UK", "city": "Birmingham", "kl": "uk-en", "q": "SEO marketing agency Birmingham about us email"},
    {"industry": "Marketing agencies", "country": "UK", "city": "Bristol", "kl": "uk-en", "q": "performance marketing agency Bristol team contact"},
    {"industry": "Marketing agencies", "country": "UK", "city": "Leeds", "kl": "uk-en", "q": "digital agency Leeds founder director contact"},
    {"industry": "Marketing agencies", "country": "UK", "city": "Edinburgh", "kl": "uk-en", "q": "creative marketing agency Edinburgh our team"},
    {"industry": "Marketing agencies", "country": "UK", "city": "Brighton", "kl": "uk-en", "q": "PPC SEO agency Brighton team contact"},
    # UK Consulting Firms
    {"industry": "Consulting firms", "country": "UK", "city": "London", "kl": "uk-en", "q": "management consultancy London managing partner contact"},
    {"industry": "Consulting firms", "country": "UK", "city": "Manchester", "kl": "uk-en", "q": "business consulting firm Manchester directors contact"},
    {"industry": "Consulting firms", "country": "UK", "city": "Bristol", "kl": "uk-en", "q": "strategy consultancy Bristol partners contact us"},
    {"industry": "Consulting firms", "country": "UK", "city": "Leeds", "kl": "uk-en", "q": "B2B sales consultancy UK founder contact"},
    # US Marketing Agencies
    {"industry": "Marketing agencies", "country": "US", "city": "Austin", "kl": "us-en", "q": "B2B digital marketing agency Austin Texas leadership contact"},
    {"industry": "Marketing agencies", "country": "US", "city": "Chicago", "kl": "us-en", "q": "performance marketing agency Chicago Illinois our team contact"},
    {"industry": "Marketing agencies", "country": "US", "city": "Denver", "kl": "us-en", "q": "SEO PPC agency Denver Colorado founder contact"},
    {"industry": "Marketing agencies", "country": "US", "city": "Boston", "kl": "us-en", "q": "B2B marketing agency Boston Massachusetts about team"},
    {"industry": "Marketing agencies", "country": "US", "city": "New York", "kl": "us-en", "q": "boutique digital marketing agency New York leadership"},
    {"industry": "Marketing agencies", "country": "US", "city": "San Diego", "kl": "us-en", "q": "growth marketing agency San Diego California team"},
    {"industry": "Marketing agencies", "country": "US", "city": "Portland", "kl": "us-en", "q": "digital strategy agency Portland Oregon our team"},
    {"industry": "Marketing agencies", "country": "US", "city": "Atlanta", "kl": "us-en", "q": "B2B branding marketing agency Atlanta Georgia team"},
    {"industry": "Marketing agencies", "country": "US", "city": "Seattle", "kl": "us-en", "q": "SEO marketing agency Seattle Washington team contact"},
    {"industry": "Marketing agencies", "country": "US", "city": "Nashville", "kl": "us-en", "q": "digital marketing agency Nashville Tennessee founder"},
    {"industry": "Marketing agencies", "country": "US", "city": "Dallas", "kl": "us-en", "q": "advertising marketing agency Dallas Texas our team"},
    {"industry": "Marketing agencies", "country": "US", "city": "Minneapolis", "kl": "us-en", "q": "B2B marketing consultancy Minneapolis team contact"},
    # US Consulting & Coaching Firms
    {"industry": "Consulting firms", "country": "US", "city": "New York", "kl": "us-en", "q": "boutique management consulting firm New York managing partner"},
    {"industry": "Consulting firms", "country": "US", "city": "Boston", "kl": "us-en", "q": "operations consulting firm Boston leadership contact"},
    {"industry": "Consulting firms", "country": "US", "city": "Chicago", "kl": "us-en", "q": "revenue consulting firm Chicago partners team"},
    {"industry": "Consulting firms", "country": "US", "city": "Austin", "kl": "us-en", "q": "business growth consulting Austin Texas founder"},
    {"industry": "Business consulting", "country": "US", "city": "San Francisco", "kl": "us-en", "q": "B2B advisory consulting firm San Francisco leadership"},
    {"industry": "Financial coaches", "country": "US", "city": "Denver", "kl": "us-en", "q": "business financial coaching firm USA founder contact"},
    # Canada & Australia Target Markets
    {"industry": "Marketing agencies", "country": "CA", "city": "Toronto", "kl": "ca-en", "q": "B2B digital marketing agency Toronto Ontario our team"},
    {"industry": "Marketing agencies", "country": "CA", "city": "Vancouver", "kl": "ca-en", "q": "marketing agency Vancouver BC leadership contact"},
    {"industry": "Consulting firms", "country": "CA", "city": "Toronto", "kl": "ca-en", "q": "management consulting firm Toronto partners contact"},
    {"industry": "Marketing agencies", "country": "AU", "city": "Sydney", "kl": "au-en", "q": "digital marketing agency Sydney Australia our team contact"},
    {"industry": "Marketing agencies", "country": "AU", "city": "Melbourne", "kl": "au-en", "q": "B2B marketing agency Melbourne founder contact"},
    {"industry": "Consulting firms", "country": "AU", "city": "Sydney", "kl": "au-en", "q": "business consulting firm Sydney Australia leadership"},
]


def _build_30day_query_bank() -> List[Dict[str, str]]:
    """Builds a 140+ query rotation across approved B2B markets, metros, and sub-niches."""
    metros = [
        ("UK", "uk-en", ["London", "Manchester", "Birmingham", "Bristol", "Leeds", "Edinburgh", "Glasgow", "Reading", "Sheffield", "Oxford"]),
        ("US", "us-en", ["Austin", "Chicago", "Denver", "Boston", "Seattle", "Atlanta", "Dallas", "Minneapolis", "Charlotte", "Raleigh", "Phoenix", "Nashville", "Columbus", "Tampa", "San Diego", "Portland"]),
        ("CA", "ca-en", ["Toronto", "Vancouver", "Calgary", "Ottawa", "Montreal"]),
        ("AU", "au-en", ["Sydney", "Melbourne", "Brisbane", "Perth"]),
    ]
    subniches = [
        ("Marketing agencies", "B2B lead generation agency {city} team contact"),
        ("Marketing agencies", "HubSpot marketing agency {city} leadership"),
        ("Marketing agencies", "web design conversion agency {city} founder contact"),
        ("Consulting firms", "revenue operations consulting {city} partners contact"),
        ("Consulting firms", "fractional CFO advisory firm {city} leadership team"),
        ("Consulting firms", "B2B sales consultancy {city} founder contact"),
        ("Financial coaches", "business growth coaching firm {city} founder"),
        ("Marketing agencies", "SEO PPC agency {city} directors email"),
    ]
    seen_q: Set[str] = {e["q"] for e in EXPANDED_QUERY_BANK}
    extended = list(EXPANDED_QUERY_BANK)
    for industry, tmpl in subniches:
        for country, kl, cities in metros:
            for city in cities:
                q_str = tmpl.format(city=city)
                if q_str not in seen_q:
                    seen_q.add(q_str)
                    extended.append({
                        "industry": industry,
                        "country": country,
                        "city": city,
                        "kl": kl,
                        "q": q_str,
                    })
    return extended


EXPANDED_QUERY_BANK = _build_30day_query_bank()

DISCOVERY_QUERIES = {
    "marketing_agencies_uk": [q["q"] for q in EXPANDED_QUERY_BANK if q["industry"] == "Marketing agencies" and q["country"] == "UK"],
    "marketing_agencies_us": [q["q"] for q in EXPANDED_QUERY_BANK if q["industry"] == "Marketing agencies" and q["country"] == "US"],
    "consulting_firms_uk": [q["q"] for q in EXPANDED_QUERY_BANK if q["industry"] == "Consulting firms" and q["country"] == "UK"],
    "consulting_firms_us": [q["q"] for q in EXPANDED_QUERY_BANK if q["industry"] == "Consulting firms" and q["country"] == "US"],
}

EXCLUDED_DOMAINS: Set[str] = {
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "youtube.com", "tiktok.com", "pinterest.com", "reddit.com",
    "wikipedia.org", "wikidata.org", "wikimedia.org", "merriam-webster.com", "dictionary.cambridge.org", "oed.com",
    "clutch.co", "sortlist.com", "designrush.com", "goodfirms.co", "agency.com", "upcity.com", "expertise.com",
    "themanifest.com", "selectedfirms.co", "visualobjects.com", "agencyanalytics.com",
    "yelp.com", "yellowpages.com", "yell.com", "thomsonlocal.com",
    "upwork.com", "fiverr.com", "toptal.com", "freelancer.com",
    "glassdoor.com", "glassdoor.co.uk", "indeed.com", "ziprecruiter.com",
    "g2.com", "capterra.com", "trustpilot.com", "bbb.org",
    "medium.com", "forbes.com", "entrepreneur.com", "inc.com", "hubspot.com", "semrush.com",
    "gov.uk", "companieshouse.gov.uk", "sec.gov", "crunchbase.com", "zoominfo.com", "apollo.io",
    "contactout.com", "rocketreach.co", "lusha.com", "seamless.ai", "leadiq.com", "hunter.io",
    "duckduckgo.com", "bing.com", "google.com", "yahoo.com",
}


class SearchDiscovery:
    """
    Executes multi-source, zero-cost discovery across DuckDuckGo HTML and Wikidata SPARQL.
    """

    def __init__(self, delay_seconds: float = 1.8):
        self.delay_seconds = delay_seconds
        self.client = primp.Client()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AriyxLeadResearch/1.0 (+https://ariyxsystems.com)",
            "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
        })

    def discover(
        self,
        industry_key: str,
        country: str,
        max_results: int = 25,
        exclude_domains: Optional[Set[str]] = None,
        query_offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Backward-compatible discovery entry point for a specific industry and country.
        """
        entries = [
            q for q in EXPANDED_QUERY_BANK
            if (not country or q["country"].upper() == country.strip().upper())
            and (not industry_key or industry_key.strip().lower() in q["industry"].lower())
        ]
        if not entries:
            entries = [{
                "industry": industry_key or "Marketing agencies",
                "country": country or "US",
                "city": "",
                "kl": f"{(country or 'us').lower()}-en",
                "q": f"{industry_key} {country} our team contact",
            }]
        results, _ = self.discover_batch(
            max_results=max_results,
            exclude_domains=exclude_domains,
            query_offset=query_offset,
            query_entries=entries,
            include_wikidata=False,
        )
        return results

    def discover_batch(
        self,
        max_results: int = 40,
        exclude_domains: Optional[Set[str]] = None,
        query_offset: int = 0,
        query_entries: Optional[List[Dict[str, str]]] = None,
        include_wikidata: bool = True,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Discovers a batch of fresh candidate domains not in `exclude_domains`.
        Returns (candidates_list, next_query_offset).
        """
        bank = query_entries or EXPANDED_QUERY_BANK
        blocked = {self._extract_clean_domain(d) or d.lower().strip() for d in (exclude_domains or set()) if d}
        seen_domains: Set[str] = set()
        discovered: List[Dict[str, Any]] = []

        if not bank:
            return [], query_offset

        cursor = query_offset % len(bank)
        queries_attempted = 0
        max_queries = min(len(bank), max(6, (max_results // 5) + 2))

        while len(discovered) < max_results and queries_attempted < max_queries:
            entry = bank[cursor]
            cursor = (cursor + 1) % len(bank)
            queries_attempted += 1

            raw_items = self._search_duckduckgo_html(
                query=entry["q"],
                kl=entry.get("kl", "us-en"),
                max_items=20,
            )

            for item in raw_items:
                dom = self._extract_clean_domain(item.get("url", ""))
                if not dom or self._is_excluded_domain(dom):
                    continue
                if dom in blocked or dom in seen_domains:
                    continue

                seen_domains.add(dom)
                discovered.append({
                    "domain": dom,
                    "website_url": f"https://{dom}",
                    "industry": entry["industry"],
                    "country": entry["country"],
                    "city": entry.get("city", ""),
                    "source_query": entry["q"],
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "discovery_source": "DuckDuckGo HTML Public Search",
                })
                if len(discovered) >= max_results:
                    break

            if queries_attempted < max_queries and len(discovered) < max_results:
                time.sleep(self.delay_seconds)

        # Supplement with paginated Wikidata SPARQL open commercial records if still needing candidates
        if include_wikidata and len(discovered) < max_results:
            wiki_offset = (int(query_offset) * 15) % 400
            wiki_items = self._discover_wikidata_agencies(
                limit=max_results - len(discovered) + 15,
                offset=wiki_offset,
            )
            for item in wiki_items:
                dom = self._extract_clean_domain(item.get("website_url", ""))
                if not dom or self._is_excluded_domain(dom):
                    continue
                if dom in blocked or dom in seen_domains:
                    continue
                seen_domains.add(dom)
                item["domain"] = dom
                discovered.append(item)
                if len(discovered) >= max_results:
                    break

        logger.info(f"Discovered {len(discovered)} unique non-excluded candidates (next cursor={cursor}).")
        return discovered, cursor

    def _search_duckduckgo_html(self, query: str, kl: str = "us-en", max_items: int = 20) -> List[Dict[str, str]]:
        """Queries DuckDuckGo HTML endpoint and decodes clean destination URLs."""
        items: List[Dict[str, str]] = []
        try:
            resp = self.client.post(
                "https://html.duckduckgo.com/html/",
                data={"q": query, "kl": kl},
                timeout=12,
            )
            if resp.status_code != 200:
                logger.warning(f"DuckDuckGo HTML returned HTTP {resp.status_code} for '{query}'.")
                return items

            soup = BeautifulSoup(resp.text, "html.parser")
            for result_div in soup.select("div.result"):
                a = result_div.select_one("a.result__a")
                if not a:
                    continue
                href = a.get("href", "").strip()
                target_url = self._decode_ddg_href(href)
                if not target_url.startswith("http"):
                    continue
                snippet_el = result_div.select_one("a.result__snippet, div.result__snippet")
                items.append({
                    "url": target_url,
                    "title": a.get_text(" ", strip=True),
                    "snippet": snippet_el.get_text(" ", strip=True) if snippet_el else "",
                })
                if len(items) >= max_items:
                    break
        except Exception as exc:
            logger.warning(f"DuckDuckGo HTML query failed for '{query}': {type(exc).__name__}: {exc}")

        return items

    def _discover_wikidata_agencies(self, limit: int = 40, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Queries Wikidata public SPARQL endpoint for marketing/advertising/consulting
        entities with official websites (P856) headquartered in US, UK, CA, or AU.
        """
        sparql = f"""
        SELECT DISTINCT ?itemLabel ?website ?countryCode WHERE {{
          VALUES ?industry {{ wd:Q13235160 wd:Q39809 wd:Q15911314 wd:Q623480 wd:Q620591 }}
          VALUES (?country ?countryCode) {{
            (wd:Q30 "US")
            (wd:Q145 "UK")
            (wd:Q16 "CA")
            (wd:Q408 "AU")
          }}
          ?item wdt:P452 ?industry .
          ?item wdt:P17 ?country .
          ?item wdt:P856 ?website .
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT {int(limit)}
        OFFSET {int(offset)}
        """
        items: List[Dict[str, Any]] = []
        try:
            resp = self.session.get(
                "https://query.wikidata.org/sparql",
                params={"format": "json", "query": sparql},
                timeout=12,
            )
            if resp.status_code != 200:
                return items
            data = resp.json()
            for row in data.get("results", {}).get("bindings", []):
                website = row.get("website", {}).get("value", "").strip()
                label = row.get("itemLabel", {}).get("value", "").strip()
                cc = row.get("countryCode", {}).get("value", "US").strip().upper()
                if not website.startswith("http"):
                    continue
                items.append({
                    "domain": self._extract_clean_domain(website),
                    "website_url": website,
                    "business_name": label if label and not label.startswith("Q") else "",
                    "industry": "Marketing agencies",
                    "country": cc,
                    "city": "",
                    "estimated_employees": "Unknown (Wikidata Public Entry)",
                    "employee_status": "Estimate",
                    "discovery_source": "Wikidata Open Business Registry",
                })
        except Exception as exc:
            logger.debug(f"Wikidata SPARQL discovery notice: {type(exc).__name__}: {exc}")

        return items

    @staticmethod
    def _decode_ddg_href(href: str) -> str:
        if "uddg=" in href:
            qs = parse_qs(urlparse(href).query)
            raw = qs.get("uddg", [""])[0]
            return unquote(raw).strip()
        if href.startswith("//"):
            return "https:" + href
        return href

    @staticmethod
    def _is_excluded_domain(domain: str) -> bool:
        if not domain or "." not in domain:
            return True
        dom_lower = domain.lower()
        if dom_lower.endswith((".gov", ".gov.uk", ".edu", ".ac.uk", ".mil")):
            return True
        if any(dom_lower == d or dom_lower.endswith(f".{d}") for d in EXCLUDED_DOMAINS):
            return True
        if any(k in dom_lower for k in ("ukagencies.co.uk", "directory", "bestagencies", "topagencies", "agencyranking", "findagency")):
            return True
        return False

    @staticmethod
    def _extract_clean_domain(url: str) -> str:
        if not url:
            return ""
        raw = str(url).strip().lower()
        if not (raw.startswith("http://") or raw.startswith("https://")):
            raw = f"http://{raw}"
        try:
            netloc = urlparse(raw).netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            if netloc.startswith("www."):
                netloc = netloc[4:]
            return netloc.strip()
        except Exception:
            return ""
