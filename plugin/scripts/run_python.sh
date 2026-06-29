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

# Resolve a command to its full path, or fail if it resolves to a Windows App
# Execution Alias stub. Those are zero-byte redirect shims under WindowsApps
# that print "Python was not found..." and exit non-zero, and they often sit
# ahead of the real interpreter on PATH.
resolve_python() {
  _candidate=$1
  _path=$(command -v "$_candidate" 2>/dev/null) || return 1
  [ -n "$_path" ] || return 1
  case "$_path" in
    */WindowsApps/*|*\\WindowsApps\\*) return 1 ;;
  esac
  printf '%s\n' "$_path"
}

# On Windows the py launcher is the most reliable entry point because it
# bypasses PATH-ordering issues with the App Execution Alias stubs.
case "$(uname -s 2>/dev/null)" in
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    if command -v py >/dev/null 2>&1; then
      exec py -3 "$@"
    fi
    ;;
esac

if _p=$(resolve_python python3); then
  exec "$_p" "$@"
fi

if _p=$(resolve_python python); then
  exec "$_p" "$@"
fi

if command -v py >/dev/null 2>&1; then
  exec py -3 "$@"
fi

printf '%s\n' "Python 3 was not found. Install Python 3 and ensure python3, python, or py is on PATH (and disable the Microsoft Store python.exe App Execution Aliases on Windows)." >&2
exit 127
