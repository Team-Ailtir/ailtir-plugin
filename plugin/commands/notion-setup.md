---
description: Builds the required Notion databases (CRM, Bid Pipeline, Subcontractor Directory, RFI Log) via the Notion MCP connector.
---

# Ailtir Notion Setup

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" notion-setup >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" notion-setup > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" notion-setup >nul 2>nul
```

Run the hidden `ailtir-notion-setup` workflow to build your business databases in Notion.

<skill name="ailtir-notion-setup" />
