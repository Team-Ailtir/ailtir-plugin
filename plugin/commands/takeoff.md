---
description: Extracts quantities from construction drawings into Irish-standard takeoff registers.
---

# Ailtir Takeoff

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" takeoff >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" takeoff > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" takeoff >nul 2>nul
```

Run the hidden `ailtir-takeoff` workflow to measure construction drawings.

<skill name="ailtir-takeoff" />
