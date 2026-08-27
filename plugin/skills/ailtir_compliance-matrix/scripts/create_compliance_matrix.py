"""Ailtir Compliance Matrix workbook.

The engine guarantees 3 tabs exist with Ailtir styling. The model supplies
all headers, rows, and section structure via --data JSON.
See the DATA CONTRACT section in ailtir_compliance-matrix/SKILL.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402

CORE_TABS = [
    {"key": "returnables",       "title": "1. Returnables & Criteria"},
    {"key": "submission_rules",  "title": "2. Submission Rules"},
    {"key": "gaps",              "title": "3. Gaps & Queries"},
]


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir Compliance Matrix workbook")
    p.add_argument("--output",  required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--client",  default="TBC")
    p.add_argument("--data",    default=None,
                   help="Path to model-supplied JSON (headers, rows, sections per tab)")
    args = p.parse_args()

    data = R.load_data(args.data)

    cover = {
        "sheet_title": "0. Overview",
        "title": f"COMPLIANCE MATRIX — {args.project.upper()}",
        "fields": [
            ("Project Name:", args.project),
            ("Client:",       args.client),
        ],
    }

    tabs = R.merge_rows(CORE_TABS, data)
    wb = R.build_workbook(cover, tabs)
    R.save_workbook(wb, args.output)
    print(f"Compliance matrix written to {args.output}")


if __name__ == "__main__":
    main()
