---
description: Compares subcontractor quotes, normalizes scope, and creates an Excel comparison.
---

# Ailtir Bid Leveling

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" bid-leveling >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" bid-leveling > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" bid-leveling >nul 2>nul
```

Run the hidden `ailtir-bid-leveling` workflow to compare received subcontractor quotes.

<skill name="ailtir-bid-leveling" />
