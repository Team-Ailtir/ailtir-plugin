---
description: Turns rough field notes into formal PW-CF-compliant daily site diaries.
---

# Ailtir Site Diary

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" site-diary >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" site-diary > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" site-diary >nul 2>nul
```

Run the hidden `ailtir-site-diary` workflow to create a formal site diary.

<skill name="ailtir-site-diary" />
