---
description: Runs final compliance checks before tender submission.
---

# Ailtir Submission Preflight

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" submission-preflight >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" submission-preflight > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" submission-preflight >nul 2>nul
```

Run the hidden `ailtir-submission-preflight` workflow to check the bid before submission.

<skill name="ailtir-submission-preflight" />
