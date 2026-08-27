"""Ailtir Tier-1 Bid Plan workbook.

The engine guarantees 9 tabs exist in the right order with Ailtir styling.
The model supplies all headers, rows, and section structure via --data JSON.
See the DATA CONTRACT section in ailtir_bid-planner/SKILL.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402

# Tab keys and titles are fixed — the model supplies all content.
CORE_TABS = [
    {"key": "document_register",      "title": "2. Document Register"},
    {"key": "go_no_go",               "title": "3. Go - No-Go"},
    {"key": "compliance_submission",  "title": "4. Compliance & Submission"},
    {"key": "risk_summary",           "title": "5. Risk Summary"},
    {"key": "package_outline",        "title": "6. Package Outline"},
    {"key": "bid_programme",          "title": "7. Bid Programme"},
    {"key": "team_raci",              "title": "8. BID TEAM RACI"},
    {"key": "clarifications",         "title": "9. Clarifications Log"},
]


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir Tier-1 bid plan workbook")
    p.add_argument("--output",      required=True)
    p.add_argument("--project",     required=True)
    p.add_argument("--client",      default="TBC")
    p.add_argument("--return-date", default="TBC")
    p.add_argument("--route",       default="TBC")
    p.add_argument("--data",        default=None,
                   help="Path to model-supplied JSON (headers, rows, sections per tab)")
    args = p.parse_args()

    data = R.load_data(args.data)

    cover_data = data.get("cover", {})
    extra_fields = [(pair[0], pair[1]) for pair in cover_data.get("extra_fields", []) if len(pair) >= 2]
    cover = {
        "sheet_title": "1. Bid Summary",
        "title": f"AILTIR BID PLAN — {args.project.upper()}",
        "fields": [
            ("Project Name:",      args.project),
            ("Client:",            args.client),
            ("Tender Return:",     args.return_date),
            ("Procurement Route:", args.route),
        ] + extra_fields,
    }

    tabs = R.merge_rows(CORE_TABS, data)
    wb = R.build_workbook(cover, tabs)
    R.save_workbook(wb, args.output)
    print(f"Bid plan written to {args.output}")


if __name__ == "__main__":
    main()
