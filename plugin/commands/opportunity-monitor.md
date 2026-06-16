---
description: Checks tender alert emails, scores opportunities, and logs qualified leads.
---

# Ailtir Opportunity Monitor

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" opportunity-monitor >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" opportunity-monitor > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" opportunity-monitor >nul 2>nul
```

Run the hidden `ailtir-opportunity-monitor` workflow to process tender alerts.

<skill name="ailtir-opportunity-monitor" />
