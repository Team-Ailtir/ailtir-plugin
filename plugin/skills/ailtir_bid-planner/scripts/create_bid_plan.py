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


def decision_callout(score, gate_fail):
    """One-line verdict for the amber callout at the top of the Go/No-Go tab."""
    verdict = go_no_go_recommendation(score, gate_fail)
    if gate_fail:
        return f"DECISION: {verdict} — {score}/100 scored, but a mandatory gate failed"
    return f"DECISION: {verdict} — {score}/100"


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
     "requires": ["gates", "scoring", "callout"], "sections": [
         {"key": "gates", "heading": "A. Mandatory Gates (Pass / Fail)",
          "headers": ["#", "Gate", "Requirement", "Status", "Evidence / Notes"],
          "widths": [6, 26, 40, 12, 44]},
         {"key": "scoring", "heading": "B. Weighted Scoring Matrix",
          "headers": ["Dimension", "Max", "Actual", "Band Hit", "Rationale"],
          "widths": [30, 8, 8, 34, 50]},
     ]},
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
    callout = decision_callout(score, gate_fail)

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
    for spec in tabs:
        if spec.get("key") == "go_no_go":
            spec["callout"] = callout
    if args.data:
        problems = R.validate_requirements(tabs)
        if problems:
            print("Payload is missing required content:", file=sys.stderr)
            for prob in problems:
                print(f"  - {prob}", file=sys.stderr)
            return 1
    wb = R.build_workbook(cover, tabs)
    R.save_workbook(wb, args.output)
    print(f"Created {args.output} ({recommendation if args.data else 'TBC'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
