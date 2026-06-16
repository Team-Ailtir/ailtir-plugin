---
description: Prepares subcontractor enquiry packs for selected trade packages.
---

# Ailtir Subcontractor Enquiry

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" subcontractor-enquiry >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" subcontractor-enquiry > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" subcontractor-enquiry >nul 2>nul
```

Run the hidden `ailtir-subcontractor-enquiry` workflow to prepare subcontractor enquiry packs.

<skill name="ailtir-subcontractor-enquiry" />
