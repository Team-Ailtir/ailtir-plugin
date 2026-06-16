---
description: Builds case studies, method statements, win themes, and lessons learned.
---

# Ailtir Intelligence Builder

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" intelligence-builder >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" intelligence-builder > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" intelligence-builder >nul 2>nul
```

Run the hidden `ailtir-intelligence-builder` workflow to build the Intelligence knowledge base.

<skill name="ailtir-intelligence-builder" />
