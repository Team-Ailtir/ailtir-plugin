---
description: Routes messy data (quotes, RFIs, emails) into the right project folder and updates Notion databases.
---

# Ailtir Ingestion Engine

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" ingest >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" ingest > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" ingest >nul 2>nul
```

Run the hidden `ailtir-ingest` workflow to process and route the provided files or text.

<skill name="ailtir-ingest" />
