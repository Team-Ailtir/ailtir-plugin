"""Scan the Bids/ folder and return one JSON record per bid.

For each bid folder we return:
  - bid_id
  - path
  - has_frontmatter
  - frontmatter (parsed dict, or null)
  - inferred (best-guess phase/completed/next_action from folder contents)
  - warnings[]

Anchored by __file__ so it works under Cowork where cwd is the session root.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Make sibling helper importable when Claude invokes us with an absolute path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frontmatter  # noqa: E402


BID_SCOPED_SKILLS_BY_PHASE = {
    "opportunity": ["ailtir_go-no-go"],
    "pre-bid": [
        "ailtir_project-indexer",
        "ailtir_compliance-matrix",
        "ailtir_contract-risk",
        "ailtir_pqq-manager",
        "ailtir_package-breakdown",
    ],
    "estimating": [
        "ailtir_takeoff",
        "ailtir_subcontractor-enquiry",
        "ailtir_prelims-builder",
        "ailtir_bid-leveling",
        "ailtir_cost-reconciliation",
    ],
    "submission": [
        "ailtir_quality-writer",
        "ailtir_programme-builder",
        "ailtir_bid-assembly",
        "ailtir_submission-preflight",
    ],
    "post-tender": [
        "ailtir_post-tender-interview",
        "ailtir_case-study-generator",
        "ailtir_feedback",
    ],
    "delivery": ["ailtir_site-diary", "ailtir_contract-admin"],
}

PHASE_ORDER = [
    "opportunity",
    "pre-bid",
    "estimating",
    "submission",
    "post-tender",
    "delivery",
    "closed",
]


def scan(bids_root: Path) -> List[Dict[str, Any]]:
    if not bids_root.exists():
        return []
    out: List[Dict[str, Any]] = []
    for entry in sorted(bids_root.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        record = _scan_one(entry)
        if record is not None:
            out.append(record)
    return out


def _scan_one(bid_path: Path) -> Optional[Dict[str, Any]]:
    readme = bid_path / "README.md"
    warnings: List[str] = []
    text = ""
    if readme.exists():
        try:
            text = readme.read_text(encoding="utf-8")
        except OSError as e:
            warnings.append(f"Could not read README: {e}")
    else:
        warnings.append("No README.md")

    fm, _ = _frontmatter.parse(text) if text else (None, "")
    inferred = _infer(bid_path)

    return {
        "bid_id": (fm or {}).get("bid_id") or bid_path.name,
        "path": str(bid_path.as_posix()),
        "has_frontmatter": fm is not None,
        "frontmatter": fm,
        "inferred": inferred,
        "warnings": warnings,
    }


def _infer(bid_path: Path) -> Dict[str, Any]:
    """Best-guess phase and completed[] from folder contents.

    Signals we look for:
      - "0. AI Context/CLAUDE.md" or "project.md"  → indexer ran
      - "1. Tender Documents/1.5 Pricing Document" has files → indexer likely
      - "2. Bid Management/compliance-matrix*.md/xlsx"       → compliance-matrix ran
      - "2. Bid Management/contract-risk*.md"                → contract-risk ran
      - "2. Bid Management/Package_Register*.xlsx"           → package-breakdown ran
      - "5. Estimating/5.1 Takeoff/takeoff_register*"        → takeoff ran
      - "5. Estimating/5.3 Prelims/prelims_schedule*"        → prelims-builder ran
      - "7. Submission/7.4 Final Submission/*"               → bid-assembly ran
    """
    completed: List[str] = []

    def has_any(rel_glob: str) -> bool:
        return any(bid_path.glob(rel_glob))

    if (bid_path / "0. AI Context" / "CLAUDE.md").exists() or (
        bid_path / "0. AI Context" / "project.md"
    ).exists():
        completed.append("ailtir_project-indexer")

    if has_any("2. Bid Management/*ompliance*matrix*") or has_any(
        "2. Bid Management/*Compliance*"
    ):
        completed.append("ailtir_compliance-matrix")

    if has_any("2. Bid Management/*ontract*risk*") or has_any(
        "2. Bid Management/*risk*register*"
    ):
        completed.append("ailtir_contract-risk")

    if has_any("2. Bid Management/Package_Register*") or has_any(
        "2. Bid Management/*package*register*"
    ):
        completed.append("ailtir_package-breakdown")

    if has_any("5. Estimating/5.1 Takeoff/takeoff*") or has_any(
        "5. Estimating/5.1 Takeoff/*.xlsx"
    ):
        completed.append("ailtir_takeoff")

    if has_any("5. Estimating/5.3 Prelims/prelims*") or has_any(
        "5. Estimating/5.3 Prelims/*.xlsx"
    ):
        completed.append("ailtir_prelims-builder")

    if has_any("7. Submission/7.4 Final Submission/*"):
        completed.append("ailtir_bid-assembly")

    # Infer phase: highest phase whose earliest expected skill is in completed
    phase = "opportunity"
    for candidate in PHASE_ORDER[:-1]:
        expected = BID_SCOPED_SKILLS_BY_PHASE.get(candidate, [])
        if not expected:
            continue
        if any(s in completed for s in expected):
            phase = candidate

    # If everything in current phase is done, promote to the next phase
    while True:
        idx = PHASE_ORDER.index(phase)
        if idx + 1 >= len(PHASE_ORDER):
            break
        expected = BID_SCOPED_SKILLS_BY_PHASE.get(phase, [])
        if expected and all(s in completed for s in expected):
            phase = PHASE_ORDER[idx + 1]
        else:
            break

    # Compute next_action from expected list minus completed
    expected_for_phase = BID_SCOPED_SKILLS_BY_PHASE.get(phase, [])
    next_skill: Optional[str] = None
    for s in expected_for_phase:
        if s not in completed:
            next_skill = s
            break

    return {
        "phase": phase,
        "completed": completed,
        "next_action": {
            "skill": next_skill,
            "reason": "inferred from folder contents",
        }
        if next_skill
        else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan Ailtir Bids folder")
    parser.add_argument("--bids-dir", default="Bids", help="Root Bids folder (default: Bids)")
    args = parser.parse_args()

    bids_root = Path(args.bids_dir)
    records = scan(bids_root)
    json.dump(records, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
