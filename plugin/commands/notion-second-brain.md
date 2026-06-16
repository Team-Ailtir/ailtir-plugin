---
description: Builds an advanced Notion knowledge base for SOPs, cost history, and lessons learned.
---

# Ailtir Notion Second Brain

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" notion-second-brain >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" notion-second-brain > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" notion-second-brain >nul 2>nul
```

Run the hidden `ailtir-notion-second-brain` workflow to build an advanced company knowledge base in Notion.

<skill name="ailtir-notion-second-brain" />
