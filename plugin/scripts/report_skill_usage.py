#!/usr/bin/env python3
"""Report anonymous Ailtir skill usage to PostHog.

This helper is intentionally fail-open. A workflow must continue if telemetry is
not configured, PostHog is unreachable, or a response is rejected.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request
import uuid


EVENT_NAME = "ailtir_skill_used"
DEFAULT_POSTHOG_HOST = "https://eu.i.posthog.com"
DEFAULT_TIMEOUT_SECONDS = 1.5

# Historical docs only contain the placeholder project token. Replace this with
# the real phc_ project token when it is available.
POSTHOG_PROJECT_TOKEN = "phc_your_project_token_here"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report anonymous Ailtir skill usage to PostHog."
    )
    parser.add_argument("skill_name", help="Ailtir skill directory name")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the event JSON without sending it",
    )
    args = parser.parse_args()

    event = build_event(args.skill_name)
    if not event:
        return 0

    if args.dry_run:
        print(json.dumps(event, sort_keys=True))
        return 0

    send_event(event)
    return 0


def build_event(skill_name: str) -> dict[str, object] | None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", skill_name):
        debug_log(f"invalid skill name: {skill_name!r}")
        return None

    token = posthog_project_token()
    if not token:
        debug_log("PostHog project token is not configured")
        return None

    plugin_root = resolve_plugin_root()
    if not plugin_root:
        debug_log("could not resolve plugin root")
        return None

    skills_root = plugin_root / "skills"
    skill_path = (skills_root / skill_name).resolve()
    try:
        skill_path.relative_to(skills_root.resolve())
    except ValueError:
        debug_log(f"skill path escapes skills root: {skill_name}")
        return None

    if not (skill_path / "SKILL.md").is_file():
        debug_log(f"skill does not exist: {skill_name}")
        return None

    properties: dict[str, object] = {
        "skill_name": skill_name,
        "plugin_version": plugin_version(plugin_root),
        "source": "skill",
        "$process_person_profile": False,
    }

    cwd = os.environ.get("PWD") or os.getcwd()
    if cwd:
        properties["cwd_hash"] = hashlib.sha256(cwd.encode("utf-8")).hexdigest()

    return {
        "api_key": token,
        "event": EVENT_NAME,
        "distinct_id": install_id(),
        "properties": properties,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def posthog_project_token() -> str | None:
    token = os.environ.get("AILTIR_POSTHOG_PROJECT_TOKEN") or POSTHOG_PROJECT_TOKEN
    token = token.strip()
    if not token or token == "phc_your_project_token_here":
        return None
    return token


def resolve_plugin_root() -> pathlib.Path | None:
    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        return pathlib.Path(env_root).resolve()

    current = pathlib.Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".claude-plugin" / "plugin.json").is_file():
            return parent
    return None


def plugin_version(plugin_root: pathlib.Path) -> str:
    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "unknown"
    return str(manifest.get("version") or "unknown")


def install_id() -> str:
    data_root = pathlib.Path(
        os.environ.get("CLAUDE_PLUGIN_DATA") or pathlib.Path.home() / ".cache/ailtir-plugin"
    )
    install_id_path = data_root / "install_id"
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        if install_id_path.is_file():
            value = install_id_path.read_text(encoding="utf-8").strip()
            if value:
                return value

        value = str(uuid.uuid4())
        install_id_path.write_text(value, encoding="utf-8")
        return value
    except OSError:
        return str(uuid.uuid4())


def send_event(event: dict[str, object]) -> None:
    host = os.environ.get("AILTIR_POSTHOG_HOST") or DEFAULT_POSTHOG_HOST
    host = host.rstrip("/")
    timeout = timeout_seconds()
    body = json.dumps(event, separators=(",", ":")).encode("utf-8")
    request = urllib.request.Request(
        f"{host}/capture/",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            response_body = response.read(200).decode("utf-8", errors="replace")
            debug_log(f"posted to {host}/capture/ status={status} response={response_body}")
    except (OSError, urllib.error.URLError) as exc:
        debug_log(f"PostHog request failed: {exc}")


def timeout_seconds() -> float:
    raw = os.environ.get("AILTIR_POSTHOG_TIMEOUT_SECONDS")
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return max(0.1, float(raw))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def debug_log(message: str) -> None:
    if not os.environ.get("AILTIR_POSTHOG_DEBUG"):
        return

    data_root = pathlib.Path(
        os.environ.get("CLAUDE_PLUGIN_DATA") or pathlib.Path.home() / ".cache/ailtir-plugin"
    )
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        with (data_root / "telemetry.log").open("a", encoding="utf-8") as handle:
            handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {message}\n")
    except OSError:
        return


if __name__ == "__main__":
    sys.exit(main())
