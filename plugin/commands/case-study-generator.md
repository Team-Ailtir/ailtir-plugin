---
description: Converts completed project data and tender debriefs into reusable intelligence.
---

# Ailtir Case Study Generator

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" case-study-generator >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" case-study-generator > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" case-study-generator >nul 2>nul
```

Run the hidden `ailtir-case-study-generator` workflow to generate case studies or process tender debriefs.

<skill name="ailtir-case-study-generator" />
