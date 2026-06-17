---
description: Captures a 1-10 usefulness rating, reason, and structured follow-up feedback for an Ailtir workflow.
---

# Ailtir Feedback

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" feedback >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" feedback > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" feedback >nul 2>nul
```

Run the hidden `ailtir-feedback` workflow to collect structured feedback.

<skill name="ailtir-feedback" />
