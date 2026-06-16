#!/usr/bin/env sh

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" 2>/dev/null && pwd)
"$script_dir/run_python.sh" "$script_dir/report_usage.py" "$@" --kind command >/dev/null 2>&1

exit 0
