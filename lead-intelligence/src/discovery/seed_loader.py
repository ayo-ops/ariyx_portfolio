"""
Seed Loader Module
Loads manually provided or curated seed target lists from CSV or text files.
Enables controlled, deterministic batch research without automated scraping.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SeedLoader:
    """
    Parses seed files containing target businesses, domains, and locations.
    """

    @staticmethod
    def load_from_csv(csv_path: str) -> List[Dict[str, Any]]:
        path = Path(csv_path)
        if not path.exists():
            logger.warning(f"Seed file not found: {csv_path}")
            return []

        leads = []
        try:
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cleaned_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    domain = cleaned_row.get("domain") or cleaned_row.get("website") or ""
                    if domain:
                        leads.append({
                            "business_name": cleaned_row.get("business_name") or cleaned_row.get("company_name") or "",
                            "website": domain if domain.startswith("http") else f"https://{domain}",
                            "domain": domain.replace("https://", "").replace("http://", "").split("/")[0],
                            "industry": cleaned_row.get("industry", "Marketing agencies"),
                            "country": cleaned_row.get("country", "US"),
                            "city": cleaned_row.get("city", ""),
                            "estimated_employees": cleaned_row.get("estimated_employees") or cleaned_row.get("employee_count") or "10-25",
                            "employee_status": cleaned_row.get("employee_status", "Estimate"),
                            "employee_source_url": cleaned_row.get("employee_source_url", ""),
                            "discovery_source": "Curated Seed File"
                        })
            logger.info(f"Loaded {len(leads)} seed prospects from {csv_path}.")
            return leads
        except Exception as e:
            logger.error(f"Failed to parse seed CSV: {e}")
            return []
