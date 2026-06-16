---
description: Scores bid viability against CIRI, Safe-T-Cert, and Ailtir weighted criteria.
---

# Ailtir Go/No-Go

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" go-no-go >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" go-no-go > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" go-no-go >nul 2>nul
```

Run the hidden `ailtir-go-no-go` workflow to evaluate bid viability.

<skill name="ailtir-go-no-go" />
