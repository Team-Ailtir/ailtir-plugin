---
description: Compiles final submission documents and runs the final reconciliation check.
---

# Ailtir Bid Assembly

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" bid-assembly >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" bid-assembly > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" bid-assembly >nul 2>nul
```

Run the hidden `ailtir-bid-assembly` workflow to compile the final tender submission.

<skill name="ailtir-bid-assembly" />
