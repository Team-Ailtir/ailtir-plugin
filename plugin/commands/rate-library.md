---
description: Looks up Irish construction labor rates, material costs, and m2 benchmarks.
---

# Ailtir Rate Library

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" rate-library >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" rate-library > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" rate-library >nul 2>nul
```

Run the hidden `ailtir-rate-library` reference workflow for Irish construction rates and benchmarks.

<skill name="ailtir-rate-library" />
