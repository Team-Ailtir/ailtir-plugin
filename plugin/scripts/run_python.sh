#!/usr/bin/env sh

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)
if [ -z "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  CLAUDE_PLUGIN_ROOT=$(dirname -- "$script_dir")
  export CLAUDE_PLUGIN_ROOT
fi

if [ "$#" -lt 1 ]; then
  printf '%s\n' "usage: run_python.sh <script.py> [args...]" >&2
  exit 2
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$@"
fi

if command -v python >/dev/null 2>&1; then
  exec python "$@"
fi

if command -v py >/dev/null 2>&1; then
  exec py -3 "$@"
fi

printf '%s\n' "Python 3 was not found. Install Python 3 and ensure python3, python, or py is on PATH." >&2
exit 127
