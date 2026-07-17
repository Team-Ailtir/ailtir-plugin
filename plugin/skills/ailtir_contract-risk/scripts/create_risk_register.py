"""Tier-2 deep-dive contract risk register: 3 deterministic tabs + cover.

Structure/headers/styling owned here; model supplies rows via --data JSON.
Writes its OWN workbook. See SKILL.md for the data contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402


CORE_TABS = [
    {"key": "risk_register", "title": "2. Risk Register",
     "headers": ["Ref", "Risk Description", "Clause / Schedule Ref", "Rating",
                 "Commercial Impact", "Mitigation / Action", "Owner"]},
    {"key": "contract_data", "title": "3. Schedule Part 1 - Data",
     "headers": ["Schedule Part", "Ref", "Data Item", "Value in Contract",
                 "Playbook Standard / Note"]},
    {"key": "action_tracker", "title": "4. Action Tracker",
     "headers": ["#", "Risk Ref", "Action", "Who", "Due By", "Status", "Notes"]},
]


def cover(meta):
    fields = [(f"{k}:", v) for k, v in meta.items()]
    return {"sheet_title": "1. Cover", "title": "CONTRACT RISK REGISTER", "fields": fields}


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir contract risk register workbook")
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
