---
description: Converts tender scope into trade package registers and scope matrices.
---

# Ailtir Package Breakdown

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" package-breakdown >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" package-breakdown > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" package-breakdown >nul 2>nul
```

Run the hidden `ailtir-package-breakdown` workflow to prepare procurement packages.

<skill name="ailtir-package-breakdown" />
