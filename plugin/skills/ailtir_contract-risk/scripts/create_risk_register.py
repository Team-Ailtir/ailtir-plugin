"""Ailtir Contract Risk Register workbook.

The engine guarantees 3 tabs exist with Ailtir styling. The model supplies
all headers, rows, and section structure via --data JSON.
See the DATA CONTRACT section in ailtir_contract-risk/SKILL.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402

CORE_TABS = [
    {"key": "risk_register",   "title": "1. Risk Register"},
    {"key": "contract_data",   "title": "2. Contract Data"},
    {"key": "action_tracker",  "title": "3. Action Tracker"},
]


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir Contract Risk Register workbook")
    p.add_argument("--output",  required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--client",  default="TBC")
    p.add_argument("--data",    default=None,
                   help="Path to model-supplied JSON (headers, rows, sections per tab)")
    args = p.parse_args()

    data = R.load_data(args.data)

    cover = {
        "sheet_title": "0. Overview",
        "title": f"CONTRACT RISK REGISTER — {args.project.upper()}",
        "fields": [
            ("Project Name:", args.project),
            ("Client:",       args.client),
        ],
    }

    tabs = R.merge_rows(CORE_TABS, data)
    wb = R.build_workbook(cover, tabs)
    R.save_workbook(wb, args.output)
    print(f"Risk register written to {args.output}")


if __name__ == "__main__":
    main()
