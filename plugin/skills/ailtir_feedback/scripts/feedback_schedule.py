#!/usr/bin/env python3
"""Maintain the local schedule for occasional Ailtir feedback invitations."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

DEFAULT_ROOT = "~/Ailtir-Tendering"
STATE_FILE = ".feedback_state.json"
WORKFLOWS_BETWEEN_PROMPTS = 5
DAYS_BETWEEN_PROMPTS = 10


def state_path() -> Path:
    root = os.environ.get("AILTIR_PLUGIN_DATA") or DEFAULT_ROOT
    return Path(os.path.expandvars(root)).expanduser().resolve() / STATE_FILE


def default_state() -> dict[str, object]:
    return {
        "schema_version": 1,
        "enabled": False,
        "completed_workflows": 0,
        "completed_since_prompt": 0,
        "last_prompted": None,
    }


def load_state(path: Path) -> dict[str, object]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_state()
    state = default_state()
    if isinstance(loaded, dict):
        state.update(loaded)
    return state


def save_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def invitation_reason(state: dict[str, object], now: datetime) -> str | None:
    if not state.get("enabled", True):
        return None
    if int(state.get("completed_since_prompt", 0)) >= 1 and not state.get(
        "last_prompted"
    ):
        return "first_completed_workflow"
    if int(state.get("completed_since_prompt", 0)) >= WORKFLOWS_BETWEEN_PROMPTS:
        return "five_completed_workflows"
    last_prompted = state.get("last_prompted")
    if isinstance(last_prompted, str):
        try:
            previous = datetime.fromisoformat(last_prompted.replace("Z", "+00:00"))
        except ValueError:
            return None
        if now - previous >= timedelta(days=DAYS_BETWEEN_PROMPTS):
            return "ten_days"
    return None


def complete(path: Path, now: datetime) -> dict[str, object]:
    state = load_state(path)
    state["completed_workflows"] = int(state.get("completed_workflows", 0)) + 1
    state["completed_since_prompt"] = int(state.get("completed_since_prompt", 0)) + 1
    save_state(path, state)
    reason = invitation_reason(state, now)
    return {"invite": reason is not None, "reason": reason}


def prompted(path: Path, now: datetime) -> dict[str, object]:
    state = load_state(path)
    state["completed_since_prompt"] = 0
    state["last_prompted"] = (
        now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )
    save_state(path, state)
    return {"recorded": True}


def configure(path: Path, enabled: bool) -> dict[str, object]:
    state = load_state(path)
    state["enabled"] = enabled
    save_state(path, state)
    return {"enabled": enabled}


def main() -> None:
    parser = argparse.ArgumentParser()
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("complete")
    subcommands.add_parser("prompted")
    configure_parser = subcommands.add_parser("configure")
    configure_parser.add_argument("--enabled", choices=("true", "false"), required=True)
    args = parser.parse_args()

    path = state_path()
    now = datetime.now(UTC)
    if args.command == "complete":
        result = complete(path, now)
    elif args.command == "prompted":
        result = prompted(path, now)
    else:
        result = configure(path, args.enabled == "true")
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
