---
description: Reviews PW-CF or RIAI contracts clause-by-clause against the risk playbook.
---

# Ailtir Contract Risk

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" contract-risk >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" contract-risk > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" contract-risk >nul 2>nul
```

Run the hidden `ailtir-contract-risk` workflow to review a proposed contract.

<skill name="ailtir-contract-risk" />
