---
description: Completes or evaluates PQQ and SAQ documents from company context.
---

# Ailtir PQQ Manager

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" pqq-manager >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" pqq-manager > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" pqq-manager >nul 2>nul
```

Run the hidden `ailtir-pqq-manager` workflow to manage PQQ or SAQ documents.

<skill name="ailtir-pqq-manager" />
