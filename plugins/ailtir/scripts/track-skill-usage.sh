#!/usr/bin/env bash
set -u

# This hook is intentionally fail-open. Skill usage must never depend on
# telemetry being configured, reachable, or accepted by PostHog.

main() {
  local input
  input="$(cat 2>/dev/null || true)"

  [ -n "${AILTIR_POSTHOG_PROJECT_TOKEN:-}" ] || {
    debug_log "AILTIR_POSTHOG_PROJECT_TOKEN is not set"
    exit 0
  }
  [ -n "$input" ] || {
    debug_log "hook input is empty"
    exit 0
  }

  local event_json
  event_json="$(build_event "$input" 2>/dev/null || true)"
  [ -n "$event_json" ] || {
    debug_log "hook input did not produce a telemetry event"
    exit 0
  }

  local host="${AILTIR_POSTHOG_HOST:-https://eu.i.posthog.com}"
  host="${host%/}"
  local response_file
  response_file="$(mktemp 2>/dev/null || true)"

  local http_code
  http_code="$(curl \
    --silent \
    --show-error \
    --location \
    --max-time "${AILTIR_POSTHOG_TIMEOUT_SECONDS:-1.5}" \
    --header "Content-Type: application/json" \
    --data "$event_json" \
    --output "${response_file:-/dev/null}" \
    --write-out "%{http_code}" \
    "$host/capture/" 2>/dev/null || true)"

  debug_log "posted to ${host}/capture/ status=${http_code:-curl_failed} response=$(head -c 200 "${response_file:-/dev/null}" 2>/dev/null || true)"
  [ -n "$response_file" ] && rm -f "$response_file"
}

debug_log() {
  [ -n "${AILTIR_POSTHOG_DEBUG:-}" ] || return 0

  local data_root="${CLAUDE_PLUGIN_DATA:-$HOME/.cache/ailtir-plugin}"
  mkdir -p "$data_root" 2>/dev/null || return 0
  printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >> "$data_root/telemetry.log" 2>/dev/null || true
}

build_event() {
  python3 - "$@" <<'PY'
import hashlib
import json
import os
import pathlib
import re
import sys
import uuid

try:
    hook_input = json.loads(sys.argv[1])
except Exception:
    sys.exit(0)

if hook_input.get("hook_event_name") != "UserPromptExpansion":
    sys.exit(0)

if hook_input.get("expansion_type") != "slash_command":
    sys.exit(0)

if hook_input.get("command_source") not in (None, "plugin"):
    sys.exit(0)

prompt = hook_input.get("prompt") or ""
command_name = hook_input.get("command_name") or ""
command_args = hook_input.get("command_args") or ""

if prompt and not prompt.startswith("/ailtir:"):
    sys.exit(0)

raw_skill_name = command_name
if raw_skill_name.startswith("ailtir:"):
    raw_skill_name = raw_skill_name.split(":", 1)[1]
elif prompt.startswith("/ailtir:"):
    raw_skill_name = prompt[len("/ailtir:"):].split(None, 1)[0]

if not re.fullmatch(r"[A-Za-z0-9_.-]+", raw_skill_name or ""):
    sys.exit(0)

plugin_root = pathlib.Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "")).resolve()
skills_root = plugin_root / "skills"
skill_path = (skills_root / raw_skill_name).resolve()

try:
    skill_path.relative_to(skills_root.resolve())
except Exception:
    sys.exit(0)

if not (skill_path / "SKILL.md").is_file():
    sys.exit(0)

plugin_version = "unknown"
manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
try:
    plugin_version = json.loads(manifest_path.read_text()).get("version") or plugin_version
except Exception:
    pass

data_root = pathlib.Path(os.environ.get("CLAUDE_PLUGIN_DATA") or pathlib.Path.home() / ".cache" / "ailtir-plugin")
install_id_path = data_root / "install_id"
try:
    data_root.mkdir(parents=True, exist_ok=True)
    if install_id_path.is_file():
        install_id = install_id_path.read_text().strip()
    else:
        install_id = str(uuid.uuid4())
        install_id_path.write_text(install_id)
except Exception:
    install_id = str(uuid.uuid4())

cwd = hook_input.get("cwd") or ""
cwd_hash = hashlib.sha256(cwd.encode("utf-8")).hexdigest() if cwd else None

properties = {
    "skill_name": raw_skill_name,
    "plugin_version": plugin_version,
    "command_args_present": bool(str(command_args).strip()),
    "command_source": hook_input.get("command_source"),
    "session_id": hook_input.get("session_id"),
    "$process_person_profile": False,
}

if cwd_hash:
    properties["cwd_hash"] = cwd_hash

event = {
    "api_key": os.environ["AILTIR_POSTHOG_PROJECT_TOKEN"],
    "event": "ailtir_skill_used",
    "distinct_id": install_id,
    "properties": properties,
}

print(json.dumps(event, separators=(",", ":")))
PY
}

main "$@"
