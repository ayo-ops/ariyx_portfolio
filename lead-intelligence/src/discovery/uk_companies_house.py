"""
UK Companies House Official Registry Module
Integrates with the official, free UK Companies House API for verified corporate and director data.
Permitted and authorized by the UK Government.
"""

import base64
import logging
from typing import Dict, Any, List, Optional
import requests

logger = logging.getLogger(__name__)

API_BASE = "https://api.company-information.service.gov.uk"


class UKCompaniesHouse:
    """
    Interfaces with the official Companies House REST API (Free developer registration).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.session = requests.Session()
        if self.api_key:
            auth_str = f"{self.api_key}:"
            encoded = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
            self.session.headers.update({"Authorization": f"Basic {encoded}"})

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def search_company(self, query: str, items_per_page: int = 5) -> List[Dict[str, Any]]:
        """Searches for active UK companies by name or keyword."""
        if not self.is_configured():
            logger.info("UK Companies House API key not configured; skipping direct registry call.")
            return []

        url = f"{API_BASE}/search/companies"
        params = {"q": query, "items_per_page": items_per_page}

        try:
            resp = self.session.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                results = []
                for item in items:
                    if item.get("company_status") == "active":
                        results.append({
                            "company_number": item.get("company_number"),
                            "title": item.get("title"),
                            "address": item.get("address_snippet"),
                            "date_of_creation": item.get("date_of_creation"),
                            "sic_codes": item.get("sic_codes", []),
                            "source_url": f"https://find-and-update.company-information.service.gov.uk/company/{item.get('company_number')}"
                        })
                return results
            else:
                logger.warning(f"Companies House API returned status {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            logger.error(f"Error querying Companies House: {e}")
            return []

    def get_officers(self, company_number: str) -> List[Dict[str, Any]]:
        """Retrieves verified directors and officers for a registered company."""
        if not self.is_configured():
            return []

        url = f"{API_BASE}/company/{company_number}/officers"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                officers = []
                for officer in data.get("items", []):
                    if not officer.get("resigned_on"):
                        officers.append({
                            "name": officer.get("name"),
                            "officer_role": officer.get("officer_role"),
                            "appointed_on": officer.get("appointed_on"),
                            "nationality": officer.get("nationality")
                        })
                return officers
            return []
        except Exception as e:
            logger.error(f"Error retrieving officers for {company_number}: {e}")
            return []
