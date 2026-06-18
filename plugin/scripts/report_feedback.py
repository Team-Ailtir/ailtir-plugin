#!/usr/bin/env python3
"""Report anonymous Ailtir feedback to PostHog.

This helper is intentionally fail-open. Feedback collection must never block a
workflow if telemetry is not configured, PostHog is unreachable, or input is
malformed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time

from report_usage import (
    debug_log,
    entity_exists,
    install_id,
    plugin_version,
    posthog_project_token,
    resolve_plugin_root,
    send_event,
)


EVENT_NAME = "ailtir_feedback_submitted"
MAX_REASON_CHARS = 2000


def main() -> int:
    parser = argparse.ArgumentParser(description="Report anonymous Ailtir feedback.")
    parser.add_argument("--rating", type=int, required=True, help="Usefulness rating from 1 to 10")
    parser.add_argument("--reason", default="", help="User-provided reason for the rating")
    parser.add_argument("--workflow", default="", help="Command or skill this feedback applies to")
    parser.add_argument(
        "--workflow-kind",
        choices=["command", "skill", "plugin", "session"],
        default="command",
        help="Type of workflow target",
    )
    parser.add_argument(
        "--answer",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Structured follow-up answer, repeatable",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the event JSON without sending it",
    )
    args = parser.parse_args()

    event = build_event(
        rating=args.rating,
        reason=args.reason,
        workflow=args.workflow,
        workflow_kind=args.workflow_kind,
        answers=args.answer,
    )
    if not event:
        return 0

    if args.dry_run:
        print(json.dumps(event, sort_keys=True))
        return 0

    send_event(event)
    return 0


def build_event(
    rating: int,
    reason: str,
    workflow: str,
    workflow_kind: str,
    answers: list[str],
) -> dict[str, object] | None:
    if rating < 1 or rating > 10:
        debug_log(f"invalid feedback rating: {rating}")
        return None

    token = posthog_project_token()
    if not token:
        debug_log("PostHog project token is not configured")
        return None

    plugin_root = resolve_plugin_root()
    if not plugin_root:
        debug_log("could not resolve plugin root")
        return None

    workflow = workflow.strip()
    if workflow and not re.fullmatch(r"[A-Za-z0-9_.-]+", workflow):
        debug_log(f"invalid feedback workflow: {workflow!r}")
        return None

    if workflow and workflow_kind in {"command", "skill"}:
        if not entity_exists(plugin_root, workflow, workflow_kind):
            debug_log(f"feedback {workflow_kind} does not exist: {workflow}")
            return None

    reason = " ".join(reason.split())
    if len(reason) > MAX_REASON_CHARS:
        reason = reason[:MAX_REASON_CHARS]

    properties: dict[str, object] = {
        "rating": rating,
        "reason": reason,
        "reason_present": bool(reason),
        "plugin_version": plugin_version(plugin_root),
        "source": "feedback",
        "workflow_kind": workflow_kind,
        "$process_person_profile": False,
    }

    if workflow:
        properties["workflow_name"] = workflow

    followup_answers = parse_answers(answers)
    if followup_answers:
        properties["followup_answers"] = followup_answers

    cwd = os.getcwd()
    if cwd:
        properties["cwd_hash"] = hashlib.sha256(cwd.encode("utf-8")).hexdigest()

    return {
        "api_key": token,
        "event": EVENT_NAME,
        "distinct_id": install_id(),
        "properties": properties,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def parse_answers(raw_answers: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in raw_answers:
        if "=" not in raw:
            debug_log(f"invalid feedback answer: {raw!r}")
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        value = " ".join(value.split())
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", key):
            debug_log(f"invalid feedback answer key: {key!r}")
            continue
        if not value:
            continue
        parsed[key] = value[:200]
    return parsed


if __name__ == "__main__":
    sys.exit(main())
