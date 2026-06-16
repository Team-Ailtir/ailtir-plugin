---
description: Extracts ITT requirements into a tracked deliverables and compliance matrix.
---

# Ailtir Compliance Matrix

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" compliance-matrix >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" compliance-matrix > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" compliance-matrix >nul 2>nul
```

Run the hidden `ailtir-compliance-matrix` workflow to extract tender submission requirements.

<skill name="ailtir-compliance-matrix" />
