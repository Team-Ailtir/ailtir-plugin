#!/usr/bin/env sh
set +e

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)
script_path="$script_dir/report_skill_usage.py"

if command -v python3 >/dev/null 2>&1; then
  python3 "$script_path" "$@"
  [ "$?" -eq 0 ] && exit 0
fi

if command -v python >/dev/null 2>&1; then
  python "$script_path" "$@"
  [ "$?" -eq 0 ] && exit 0
fi

if command -v py >/dev/null 2>&1; then
  py -3 "$script_path" "$@"
fi

exit 0
