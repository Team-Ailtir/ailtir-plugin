---
description: Builds a priced Schedule of Preliminaries for Irish public works tenders.
---

# Ailtir Prelims Builder

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" prelims-builder >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" prelims-builder > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" prelims-builder >nul 2>nul
```

Run the hidden `ailtir-prelims-builder` workflow to price preliminaries.

<skill name="ailtir-prelims-builder" />
