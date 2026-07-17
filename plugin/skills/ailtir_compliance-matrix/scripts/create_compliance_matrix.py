"""Tier-2 deep-dive compliance matrix: 4 deterministic tabs + cover.

Structure/headers/styling owned here; model supplies rows via --data JSON.
Writes its OWN workbook — never the bid-planner file. See SKILL.md for the
data contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402


CORE_TABS = [
    {"key": "award_criterion", "title": "2. Award Criterion",
     "headers": ["Ref", "Criterion", "Weight", "Notes", "Status"]},
    {"key": "returnables", "title": "3. Mandatory Returnables",
     "headers": ["No.", "Ref", "Document / Item", "Category",
                 "Template Provided", "Status", "Owner", "Notes"]},
    {"key": "submission_rules", "title": "4. Submission Rules",
     "headers": ["Item", "Requirement"]},
    {"key": "gap_check", "title": "5. Template & Doc Gap Check",
     "headers": ["Ref", "Document", "Required?", "Template in Pack?", "Action Required"]},
]


def cover(meta):
    fields = [(f"{k}:", v) for k, v in meta.items()]
    return {"sheet_title": "1. Cover", "title": "COMPLIANCE MATRIX", "fields": fields}


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir compliance matrix workbook")
    p.add_argument("--output", required=True)
    p.add_argument("--data", default=None, help="Path to model-supplied JSON")
    args = p.parse_args()
    data = R.load_data(args.data)
    wb = R.build_workbook(cover(data.get("cover", {})), R.merge_rows(CORE_TABS, data))
    R.save_workbook(wb, args.output)
    print(f"Created {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
