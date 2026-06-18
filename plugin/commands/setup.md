---
description: First-time Ailtir workspace setup. Runs the onboarding interview and builds your local Context folder.
---

# Ailtir Setup

## Command Usage Reporting
Before doing any command-specific work, report this command invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_command_usage.sh" setup >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_command_usage.ps1" setup > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_command_usage.cmd" setup >nul 2>nul
```

Initialize a new Ailtir workspace. Act as an onboarding consultant.

## Step 1 — The Interview

Ask the user the following questions, ONE AT A TIME. Wait for their answer before asking the next. Do NOT ask all questions at once. Be conversational and professional.

1. **Company Name:** What is the name of the contracting company?
2. **Location & Sectors:** Where are you based, and what are your primary sectors (e.g., Commercial, Residential, Public Works)?
3. **Turnover & Size:** What is your rough annual turnover and typical project value range?
4. **Accreditations:** Do you hold CIRI, Safe-T-Cert, ISO 9001/14001/45001, or other key accreditations?
5. **Key Personnel:** Who are the key directors or bid team members I should know about?
6. **Connectors:** Are we using Notion for the business databases (CRM, Pipeline, Subcontractors, RFIs)?
7. **Win Themes:** What are your top 3 differentiators when bidding against competitors?

## Step 2 — Create the Workstation Structure

Run the Python script to build the definitive Ailtir workstation folder structure:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run_python.sh" "${CLAUDE_PLUGIN_ROOT}/resources/setup/scripts/create_workstation.py"
```

This uses `AILTIR_PLUGIN_DATA` as the workspace root. If it is not set, it defaults to `~/Ailtir-Tendering`. It creates `Context/`, `Bids/`, `Intelligence/`, `Active Projects/`, and `Daily/` under that root.

## Step 3 — Build the Context Folder

Once all questions are answered, write the data to the user's workspace.
Resolve the workspace root from `AILTIR_PLUGIN_DATA`, or use `~/Ailtir-Tendering` if it is not set. Use the file operation tools to create the following files under that root:

- `Context/company.md` (Company name, location, sectors, turnover, accreditations, win themes)
- `Context/team.md` (Key personnel)
- `Context/connectors.md` (Notion status and mapping)

## Step 4 — Write the Global CLAUDE.md

Read `${CLAUDE_PLUGIN_ROOT}/resources/setup/templates/CLAUDE.md`. Replace the placeholders (`{{COMPANY_NAME}}`, etc.) with the data gathered in the interview.
Write the final result to `CLAUDE.md` in the root of the workspace.

- [HUMAN INPUT REQUIRED] All 7 interview questions must be answered by the user before writing any Context files.

## Anti-Patterns

- DO NOT ask all the interview questions in a single message.
- DO NOT write files until the interview is fully complete.
- DO NOT hallucinate company details if the user skips a question; write `[Not provided]` instead.

## Step 5 — Next Steps

Tell the user:

```text
Setup complete. Your workspace is configured for [Company Name].

To get the most out of the quality-writer from day one, we should add 2-3 case studies and your top win themes to the `Intelligence/` folder. I can interview you for 10 minutes to write them up, or you can point me to a folder of old CVs and tenders and I'll extract them automatically.

If you want to do that now, run `/ailtir-cowork-plugin:intelligence-builder`.
If you are using Notion, run `/ailtir-cowork-plugin:notion-setup` to build your databases.
Otherwise, drop a tender pack into the workspace and run `/ailtir-cowork-plugin:bid-planner` to begin.
```

## Quality Checks

- [ ] Workspace folder structure created under `AILTIR_PLUGIN_DATA` or `~/Ailtir-Tendering` with all required subfolders.
- [ ] `Context/company.md`, `Context/team.md`, and `Context/connectors.md` written with user-provided data.
- [ ] `CLAUDE.md` written to workstation root.
- [ ] No placeholder data shipped with the plugin appears in the output files.
