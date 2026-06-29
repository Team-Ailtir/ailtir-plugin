---
name: telemetry-test
description: Diagnostic probe for Cowork sandbox capabilities. Runs a relative-path bundled Python script that tests DNS, TCP/TLS, and HTTP egress to PostHog, then prints a verdict. Use this once to confirm whether telemetry can work before standardising the per-skill telemetry pattern.
---

# Telemetry & Sandbox Probes

This skill bundles two diagnostic probes for the Cowork sandbox.

**Probe #1 (`test_posthog.py`)** — answered: PostHog is blocked, relative paths don't resolve from cwd.

**Probe #2 (`test_egress_and_paths.py`)** — answers two follow-up questions:

1. **Path resolution.** Is `${CLAUDE_SKILL_DIR}` or `${CLAUDE_PLUGIN_ROOT}` exported as an environment variable to the script? Where is cwd actually pointing? What's the reliable way to anchor a path to the skill's own directory?
2. **Egress allowlist.** Which common SaaS / cloud hostnames does Cowork's proxy actually allow outbound to? Tested independently so a single PASS unlocks the option of routing telemetry through a relay on that domain.

## How to run

The script's location must be resolved relative to the skill's directory. The portable way:

```bash
python3 "$(dirname "$0" 2>/dev/null || pwd)/scripts/test_egress_and_paths.py"
```

If that doesn't work (because `$0` isn't bound in the skill invocation context), fall back to the absolute path Claude already knows for this skill:

```bash
python3 <ABSOLUTE_PATH_TO_THIS_SKILL>/scripts/test_egress_and_paths.py
```

## How to read the output

Three sections:

- **Path resolution** — lists cwd, sys.argv[0], `__file__`, and every env var with "CLAUDE" in it. Tells us how to write reliable bundled-file references.
- **Egress allowlist test** — for each host: DNS resolves and HTTP HEAD succeeds (PASS) or proxy blocks it (FAIL). Any single PASS means we have a viable telemetry destination if we relay through that domain.
- **Verdict** — names reachable hosts (if any) and whether `${CLAUDE_SKILL_DIR}` / `${CLAUDE_PLUGIN_ROOT}` are exported as env vars.

Paste the full output back so we can finalise the telemetry strategy.

## Probe #1 (original PostHog reachability test)

Still bundled; not needed to rerun. Result: DNS+egress blocked, relative paths failed.

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
