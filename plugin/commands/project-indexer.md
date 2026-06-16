---
description: Indexes project folders into reusable markdown context files.
---

# Ailtir Project Indexer

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" project-indexer >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" project-indexer > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" project-indexer >nul 2>nul
```

Run the hidden `ailtir-project-indexer` workflow to index a project folder.

<skill name="ailtir-project-indexer" />
