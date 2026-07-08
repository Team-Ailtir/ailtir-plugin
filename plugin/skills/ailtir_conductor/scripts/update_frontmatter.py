"""Surgically update a single field or append a completed[] entry on a bid README.

Usage examples:
    # Append a completed skill entry
    python3 update_frontmatter.py --bid-path Bids/2026-014-CorkLibrary \
        --complete ailtir_project-indexer --result proceed

    # Mark a step skipped with a reason
    python3 update_frontmatter.py --bid-path Bids/2026-014-CorkLibrary \
        --skip ailtir_pqq-manager --reason "No PQQ in this pack"

    # Set the phase or status directly
    python3 update_frontmatter.py --bid-path Bids/2026-014-CorkLibrary \
        --set phase=estimating --set status=active

    # Update next_action.reason (used when the conductor defers a bid)
    python3 update_frontmatter.py --bid-path Bids/2026-014-CorkLibrary \
        --set next_action.reason="Deferred by user on 2026-07-08"

Only the keys documented in the state contract (SKILL.md) are supported. If a
bid README has no frontmatter, this script exits with code 3 — call
init_bid_frontmatter.py first.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _frontmatter  # noqa: E402


def _apply_set(fm: Dict[str, Any], expr: str) -> None:
    """Apply `key=value` or `nested.key=value` in-place."""
    if "=" not in expr:
        raise ValueError(f"--set expects key=value, got: {expr}")
    key, _, value = expr.partition("=")
    value = value.strip().strip('"').strip("'")
    keys = key.split(".")
    target = fm
    for k in keys[:-1]:
        if k not in target or not isinstance(target[k], dict):
            target[k] = {}
        target = target[k]
    if value.lower() in ("true", "false"):
        target[keys[-1]] = value.lower() == "true"
    elif value.lower() in ("null", "none", ""):
        target[keys[-1]] = None
    else:
        try:
            target[keys[-1]] = int(value)
        except ValueError:
            target[keys[-1]] = value


def main() -> int:
    parser = argparse.ArgumentParser(description="Update bid frontmatter")
    parser.add_argument("--bid-path", required=True)
    parser.add_argument(
        "--complete",
        action="append",
        default=[],
        help="Append a skill to completed[] (repeatable)",
    )
    parser.add_argument("--result", default="proceed", help="Result for --complete entries")
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        help="Append a skill to completed[] with result=skipped (repeatable)",
    )
    parser.add_argument("--reason", default="", help="Reason for --skip entries")
    parser.add_argument(
        "--set",
        action="append",
        default=[],
        dest="sets",
        help="Set a scalar field: key=value or nested.key=value (repeatable)",
    )
    parser.add_argument(
        "--add-blocker",
        default=None,
        help="Append a blocker in the form type:ref:description",
    )
    parser.add_argument(
        "--clear-blocker",
        default=None,
        help="Remove blockers matching this ref",
    )
    args = parser.parse_args()

    bid_path = Path(args.bid_path)
    readme = bid_path / "README.md"
    if not readme.exists():
        print(f"error: README not found at {readme}", file=sys.stderr)
        return 2

    text = readme.read_text(encoding="utf-8")
    fm, body = _frontmatter.parse(text)
    if fm is None:
        print(
            f"error: no frontmatter on {readme}. Run init_bid_frontmatter.py first.",
            file=sys.stderr,
        )
        return 3

    today = date.today().isoformat()
    completed: List[Dict[str, Any]] = fm.get("completed") or []

    for skill in args.complete:
        completed.append({"skill": skill, "at": today, "result": args.result})
    for skill in args.skip:
        entry: Dict[str, Any] = {"skill": skill, "at": today, "result": "skipped"}
        if args.reason:
            entry["reason"] = args.reason
        completed.append(entry)
    if args.complete or args.skip:
        fm["completed"] = completed

    if args.add_blocker:
        parts = args.add_blocker.split(":", 2)
        blocker: Dict[str, Any] = {"type": parts[0]}
        if len(parts) > 1:
            blocker["ref"] = parts[1]
        if len(parts) > 2:
            blocker["description"] = parts[2]
        blockers = fm.get("blockers") or []
        blockers.append(blocker)
        fm["blockers"] = blockers

    if args.clear_blocker:
        blockers = fm.get("blockers") or []
        fm["blockers"] = [b for b in blockers if b.get("ref") != args.clear_blocker]

    for expr in args.sets:
        _apply_set(fm, expr)

    readme.write_text(_frontmatter.serialize(fm) + body, encoding="utf-8")
    print(f"updated {readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
