---
description: Orchestrates the four-step Irish construction estimating process.
---

# Ailtir Estimating Workflow

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" estimating-workflow >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" estimating-workflow > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" estimating-workflow >nul 2>nul
```

Run the hidden `ailtir-estimating-workflow` workflow to guide tender pricing.

<skill name="ailtir-estimating-workflow" />
