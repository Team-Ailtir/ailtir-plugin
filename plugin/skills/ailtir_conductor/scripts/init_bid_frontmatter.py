"""Write a fresh YAML frontmatter block to a bid README.

Usage:
    python3 init_bid_frontmatter.py --bid-path Bids/2026-014-CorkLibrary

Behaviour:
  - Runs scan_bids._infer() on the bid to derive phase, completed[], next_action.
  - If the README already has frontmatter, we do NOT overwrite it — the caller
    should use update_frontmatter.py for surgical edits. Exits with code 0 and
    a "skipped" message on stdout so calling loops treat this as idempotent.
  - Preserves the existing README body verbatim.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frontmatter  # noqa: E402
from scan_bids import _infer  # noqa: E402


def build_frontmatter(bid_path: Path) -> Dict[str, Any]:
    inferred = _infer(bid_path)
    bid_id = bid_path.name

    # Try to split "YYYY-NNN-ProjectName" into project_name + year hint
    project_name = bid_id
    parts = bid_id.split("-", 2)
    if len(parts) == 3:
        project_name = parts[2]

    completed_entries: List[Dict[str, Any]] = [
        {"skill": s, "at": date.today().isoformat(), "result": "inferred"}
        for s in inferred["completed"]
    ]

    fm: Dict[str, Any] = {
        "schema_version": 1,
        "bid_id": bid_id,
        "project_name": project_name,
        "client": "",
        "phase": inferred["phase"],
        "status": "active",
        "next_action": inferred["next_action"] or {"skill": None, "reason": "no next action"},
        "completed": completed_entries,
        "blockers": [],
        "key_dates": {},
        "auto_drive": False,
    }
    return fm


def main() -> int:
    parser = argparse.ArgumentParser(description="Init bid README frontmatter")
    parser.add_argument("--bid-path", required=True, help="Path to bid folder (contains README.md)")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing frontmatter (destructive; default no)",
    )
    args = parser.parse_args()

    bid_path = Path(args.bid_path)
    if not bid_path.is_dir():
        print(f"error: not a directory: {bid_path}", file=sys.stderr)
        return 2

    readme = bid_path / "README.md"
    existing_text = readme.read_text(encoding="utf-8") if readme.exists() else ""
    existing_fm, body = _frontmatter.parse(existing_text)

    if existing_fm is not None and not args.force:
        print(f"skipped (frontmatter already present): {readme}")
        return 0

    fm = build_frontmatter(bid_path)

    if not body.strip():
        body = f"# {bid_path.name}\n\n**Status:** {fm['phase']}\n**Last Activity:** Frontmatter initialised\n\n"

    readme.write_text(_frontmatter.serialize(fm) + body, encoding="utf-8")
    print(f"wrote frontmatter to {readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
