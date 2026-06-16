---
description: Generates tender programs, Gantt data, and program narratives.
---

# Ailtir Programme Builder

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" programme-builder >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" programme-builder > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" programme-builder >nul 2>nul
```

Run the hidden `ailtir-programme-builder` workflow to create a tender program.

<skill name="ailtir-programme-builder" />
