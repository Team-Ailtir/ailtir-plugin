---
description: Prepares presentation outlines, Q&A scripts, and key talking points.
---

# Ailtir Post-Tender Interview

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" post-tender-interview >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" post-tender-interview > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" post-tender-interview >nul 2>nul
```

Run the hidden `ailtir-post-tender-interview` workflow to prepare for a post-tender interview.

<skill name="ailtir-post-tender-interview" />
