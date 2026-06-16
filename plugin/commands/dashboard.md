---
description: Builds an interactive bid pipeline, subcontractor, CRM, or RFI dashboard.
---

# Ailtir Dashboard

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" dashboard >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" dashboard > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" dashboard >nul 2>nul
```

Run the hidden `ailtir-dashboard` workflow to build an interactive dashboard from Notion data.

<skill name="ailtir-dashboard" />
