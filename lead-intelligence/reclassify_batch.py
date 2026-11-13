"""
Offline Batch Reclassification Tool for Ariyx Lead Intelligence System.
Applies the updated LeadScorer qualification logic to an existing local JSON export
without modifying the original archive files, touching live websites, or contacting Google Sheets.

Guarantees:
- Preserves all researched companies, 0-100 scores, evidence URLs, signals, and descriptions.
- Keeps Compliance Status completely independent of Qualification Tier.
- Keeps Campaign Status as 'Ready for Manual Review' (or 'Suppressed' for opt-outs).
"""

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from src.scoring.lead_scorer import LeadScorer
from src.storage.deduplicator import Deduplicator
from src.storage.local_store import LocalStore


def reclassify_leads(
    leads: List[Dict[str, Any]],
    scorer: Optional[LeadScorer] = None,
    deduplicator: Optional[Deduplicator] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Re-evaluates qualification tiers for an existing list of researched lead records
    while preserving their 0-100 scores, evidence, research details, and compliance statuses.
    """
    lead_scorer = scorer or LeadScorer()
    dedup = deduplicator or Deduplicator()

    seen_ids = set()
    reclassified: List[Dict[str, Any]] = []
    tier_counts: Dict[str, int] = {}

    for raw_lead in leads:
        record = copy.deepcopy(raw_lead)
        lead_id = str(record.get("lead_id") or "").strip()
        norm_domain = dedup.normalize_domain(record.get("domain") or record.get("website") or "")
        comp_status = str(record.get("compliance_status") or "").strip().upper()
        business_name = str(record.get("business_name") or "").strip()
        email = str(record.get("verified_email") or "")
        if email.lower() == "unavailable":
            email = ""

        # Check suppression / duplicate status without overwriting Compliance Status
        is_supp, supp_reason = dedup.is_suppressed(norm_domain, email=email, company_name=business_name)
        is_dup_domain, dup_reason = dedup.is_duplicate(norm_domain)
        is_dup_id = bool(lead_id and lead_id in seen_ids)

        if lead_id:
            seen_ids.add(lead_id)
        if norm_domain and not is_dup_domain:
            dedup.register(norm_domain)

        eval_payload = dict(record)
        # Keep Compliance Status completely independent of qualification scoring
        # (except internal suppression list / OPT_OUT_RECORDED opt-out checks)
        if comp_status != "OPT_OUT_RECORDED":
            eval_payload.pop("compliance_status", None)

        if is_supp:
            eval_payload["is_suppressed"] = True
            eval_payload["suppression_reason"] = supp_reason
        if is_dup_domain or is_dup_id:
            eval_payload["is_duplicate"] = True
            eval_payload["duplicate_reason"] = dup_reason or f"Duplicate Lead ID '{lead_id}' in batch."

        score_result = lead_scorer.score_lead(eval_payload)

        # Preserve original researched 0-100 score if present
        if "lead_score" in record and record["lead_score"] is not None:
            record["lead_score"] = int(record["lead_score"])
        else:
            record["lead_score"] = score_result["total_score"]

        record["qualification_tier"] = score_result["qualification_tier"]
        record["tier_rationale"] = score_result["tier_rationale"]
        record["triple_lock_status"] = score_result["triple_lock_status"]

        # Never automatically grant outreach eligibility
        if not record.get("campaign_status"):
            record["campaign_status"] = "Ready for Manual Review"

        tier = record["qualification_tier"]
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        reclassified.append(record)

    return reclassified, tier_counts


def main():
    parser = argparse.ArgumentParser(
        description="Reclassify an existing Ariyx lead intelligence JSON batch offline."
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=str(BASE_DIR / "data" / "exports" / "mixed_services_uk_us_20261109_193531.json"),
        help="Path to the source JSON export file (never modified)."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save reclassified output as a new timestamped JSON and CSV batch in data/exports/."
    )
    parser.add_argument(
        "--batch-name",
        type=str,
        default="mixed_services_uk_us_reclassified",
        help="Output batch filename prefix when --save is enabled."
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        leads = json.load(f)

    reclassified, tier_counts = reclassify_leads(leads)

    print(f"Source File (Untouched): {input_path}")
    print(f"Total Companies:         {len(reclassified)}")
    print("Tier Counts:")
    for tier, count in tier_counts.items():
        print(f"  - {tier}: {count}")

    if args.save:
        store = LocalStore()
        export_paths = store.save_batch(reclassified, batch_name=args.batch_name)
        print(f"Saved JSON: {export_paths['json_path']}")
        print(f"Saved CSV:  {export_paths['csv_path']}")


if __name__ == "__main__":
    main()
