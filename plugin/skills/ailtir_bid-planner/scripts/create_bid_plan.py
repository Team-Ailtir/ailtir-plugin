"""Tier-1 bid-planner workbook: 9 deterministic core tabs (+ optional tabs).

Structure, headers, and styling are owned here; the model supplies row content
via --data JSON. See ailtir_bid-planner/SKILL.md for the data contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402


def go_no_go_recommendation(score, gate_fail):
    if gate_fail:
        return "NO-GO (mandatory gate failed)"
    if score >= 80:
        return "Strong GO"
    if score >= 60:
        return "Marginal GO"
    return "NO-GO"


BANNER_COMPLIANCE = ("Summarised view. Run /ailtir_compliance-matrix for the full "
                     "returnables tracker with templates, owners & deadlines.")
BANNER_RISK = ("Summarised view. Run /ailtir_contract-risk for the full "
               "clause-by-clause register, contract data & action tracker.")
BANNER_PACKAGE = ("Summarised view. Run /ailtir_package-breakdown in the "
                  "enquire-and-procure phase for the full package register.")

CORE_TABS = [
    {"key": "document_register", "title": "2. Document Register",
     "headers": ["Filename", "Title", "Type", "Rev", "Date", "Notes"]},
    {"key": "go_no_go", "title": "3. Go / No-Go",
     "headers": ["Criteria", "Max Score", "Actual Score", "Notes"]},
    {"key": "compliance_submission", "title": "4. Compliance & Submission",
     "banner": BANNER_COMPLIANCE, "sections": [
         {"key": "returnables", "heading": "A. Returnables & Award Criteria",
          "headers": ["Ref", "Requirement / Criterion", "Weighting", "Template", "Owner"]},
         {"key": "submission_rules", "heading": "B. Submission Rules",
          "headers": ["Item", "Requirement"]},
     ]},
    {"key": "risk_summary", "title": "5. Risk Summary", "banner": BANNER_RISK,
     "headers": ["Ref", "Risk", "Rating", "Impact", "Mitigation"]},
    {"key": "package_outline", "title": "6. Package Outline", "banner": BANNER_PACKAGE,
     "headers": ["Package", "Scope", "Est. Value", "Target Date"]},
    {"key": "bid_programme", "title": "7. Bid Programme",
     "headers": ["Milestone", "Date", "Owner", "Notes"]},
    {"key": "team_raci", "title": "8. BID TEAM RACI",
     "headers": ["Activity", "Responsible", "Accountable", "Consulted", "Informed"]},
    {"key": "clarifications", "title": "9. Clarifications Log",
     "headers": ["Ref", "Query", "Raised", "Status", "Response"]},
]


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir Tier-1 bid plan workbook")
    p.add_argument("--output", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--client", default="TBC")
    p.add_argument("--return-date", default="TBC")
    p.add_argument("--route", default="TBC")
    p.add_argument("--data", default=None, help="Path to model-supplied JSON row content")
    args = p.parse_args()

    data = R.load_data(args.data)
    gng = data.get("tabs", {}).get("go_no_go", {})
    score = int(gng.get("score", 0))
    gate_fail = bool(gng.get("gate_fail", False))
    recommendation = go_no_go_recommendation(score, gate_fail)

    cover = {
        "title": f"AILTIR BID PLAN — {args.project.upper()}",
        "fields": [
            ("Project Name:", args.project),
            ("Client:", args.client),
            ("Tender Return:", args.return_date),
            ("Procurement Route:", args.route),
            ("Go/No-Go Score:", f"{score}/100" if args.data else "TBC"),
            ("Recommendation:", recommendation if args.data else "TBC"),
        ],
    }

    tabs = R.merge_rows(CORE_TABS, data)
    wb = R.build_workbook(cover, tabs)
    R.save_workbook(wb, args.output)
    print(f"Created {args.output} ({recommendation if args.data else 'TBC'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
