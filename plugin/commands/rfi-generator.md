---
description: Drafts RFIs, logs them, and processes RFI responses for scope impacts.
---

# Ailtir RFI Generator

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" rfi-generator >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" rfi-generator > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" rfi-generator >nul 2>nul
```

Run the hidden `ailtir-rfi-generator` workflow to draft or process RFIs.

<skill name="ailtir-rfi-generator" />
