---
description: Drafts technical responses, method statements, and social value answers.
---

# Ailtir Quality Writer

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" quality-writer >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" quality-writer > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" quality-writer >nul 2>nul
```

Run the hidden `ailtir-quality-writer` workflow to draft tender quality responses.

<skill name="ailtir-quality-writer" />
