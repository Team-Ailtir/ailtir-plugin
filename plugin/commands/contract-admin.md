---
description: Drafts PW-CF or RIAI contractual notices with the correct time-bar checks.
---

# Ailtir Contract Admin

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" contract-admin >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" contract-admin > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" contract-admin >nul 2>nul
```

Run the hidden `ailtir-contract-admin` workflow to draft a formal contractual notice.

<skill name="ailtir-contract-admin" />
