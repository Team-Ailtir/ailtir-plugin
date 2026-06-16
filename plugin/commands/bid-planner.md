---
description: The master orchestrator for new tenders. Catalogues the pack, runs Go/No-Go, checks compliance, and generates a Bid Plan Workbook.
---

# Ailtir Bid Planner

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" bid-planner >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" bid-planner > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" bid-planner >nul 2>nul
```

Run the hidden `ailtir-bid-planner` workflow to analyze a new tender pack.

<skill name="ailtir-bid-planner" />
