---
description: Checks an estimate for gaps, double-counting, and benchmark risk.
---

# Ailtir Cost Reconciliation

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" cost-reconciliation >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" cost-reconciliation > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" cost-reconciliation >nul 2>nul
```

Run the hidden `ailtir-cost-reconciliation` workflow to perform the final estimate quality gate.

<skill name="ailtir-cost-reconciliation" />
