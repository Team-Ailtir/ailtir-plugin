---
name: telemetry-test
description: Diagnostic probe for Cowork sandbox capabilities. Runs a relative-path bundled Python script that tests DNS, TCP/TLS, and HTTP egress to PostHog, then prints a verdict. Use this once to confirm whether telemetry can work before standardising the per-skill telemetry pattern.
---

# Telemetry Reachability Probe

This skill exists to answer two questions about the current Cowork sandbox:

1. **Do relative-path bundled scripts execute?** (`scripts/test_posthog.py` referenced relatively, not via `${CLAUDE_PLUGIN_ROOT}`.)
2. **Is PostHog reachable from this sandbox?** (DNS, TCP/TLS, and HTTP capture all tested independently.)

## What to do

Run the bundled probe script:

```bash
python scripts/test_posthog.py
```

If `python` is not on PATH, try:

```bash
python3 scripts/test_posthog.py
```

## How to read the output

The script prints three `[PASS]` / `[FAIL]` lines followed by a verdict:

- **All three PASS** → relative paths work AND PostHog is reachable. We can ship Option B (per-skill bundled telemetry) and it will function.
- **`dns` fails** → org-level egress is blocking DNS for posthog.com. Telemetry cannot work in this Cowork deployment without an admin allowlist change.
- **`tcp_tls` fails** → DNS resolves but outbound 443 is blocked. Same conclusion.
- **`http_capture` fails after the others pass** → network is fine; PostHog rejected the event. Likely a token or payload problem, not a sandbox issue.
- **The script itself fails to run** ("No such file or directory" / "scripts/test_posthog.py not found") → relative paths are not resolving the way the Skills docs describe; we need a different reference pattern before continuing.

Report the full output back so we know which option to take for the production telemetry rollout.
