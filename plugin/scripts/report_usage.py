#!/usr/bin/env python3
"""Report anonymous Ailtir skill or command usage to PostHog.

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


EVENT_NAMES = {
    "command": "ailtir_command_used",
    "skill": "ailtir_skill_used",
}
DEFAULT_POSTHOG_HOST = "https://eu.i.posthog.com"
DEFAULT_TIMEOUT_SECONDS = 1.5

POSTHOG_DEBUG = False
POSTHOG_PROJECT_TOKEN = "phc_9gC5EKe7JulA1RKMs8AwlnaLiKHaI6l3mFyWf1XklO7"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report anonymous Ailtir skill or command usage to PostHog."
    )
    parser.add_argument("name", help="Ailtir skill or command name")
    parser.add_argument(
        "--kind",
        choices=sorted(EVENT_NAMES),
        default="skill",
        help="Usage entity kind to report",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the event JSON without sending it",
    )
    args = parser.parse_args()

    event = build_event(args.name, args.kind)
    if not event:
        return 0

    if args.dry_run:
        print(json.dumps(event, sort_keys=True))
        return 0

    send_event(event)
    return 0


def build_event(name: str, kind: str) -> dict[str, object] | None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", name):
        debug_log(f"invalid {kind} name: {name!r}")
        return None

    token = posthog_project_token()
    if not token:
        debug_log("PostHog project token is not configured")
        return None

    plugin_root = resolve_plugin_root()
    if not plugin_root:
        debug_log("could not resolve plugin root")
        return None

    if not entity_exists(plugin_root, name, kind):
        debug_log(f"{kind} does not exist: {name}")
        return None

    name_key = f"{kind}_name"

    properties: dict[str, object] = {
        name_key: name,
        "plugin_version": plugin_version(plugin_root),
        "source": kind,
        "$process_person_profile": False,
    }

    cwd = os.getcwd()
    if cwd:
        properties["cwd_hash"] = hashlib.sha256(cwd.encode("utf-8")).hexdigest()

    return {
        "api_key": token,
        "event": EVENT_NAMES[kind],
        "distinct_id": install_id(),
        "properties": properties,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def entity_exists(plugin_root: pathlib.Path, name: str, kind: str) -> bool:
    if kind == "skill":
        entities_root = plugin_root / "skills"
        entity_path = (entities_root / name).resolve()
        try:
            entity_path.relative_to(entities_root.resolve())
        except ValueError:
            debug_log(f"skill path escapes skills root: {name}")
            return False
        return (entity_path / "SKILL.md").is_file()

    commands_root = plugin_root / "commands"
    command_path = (commands_root / f"{name}.md").resolve()
    try:
        command_path.relative_to(commands_root.resolve())
    except ValueError:
        debug_log(f"command path escapes commands root: {name}")
        return False
    return command_path.is_file()


def posthog_project_token() -> str | None:
    token = POSTHOG_PROJECT_TOKEN
    token = token.strip()
    if not token:
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
    host = DEFAULT_POSTHOG_HOST
    timeout = DEFAULT_TIMEOUT_SECONDS
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


def debug_log(message: str) -> None:
    if not POSTHOG_DEBUG:
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
