---
description: First-time Ailtir workspace setup. Runs the onboarding interview and builds your local Context folder.
---

# Ailtir Setup

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
python "${CLAUDE_PLUGIN_ROOT}/skills/ailtir-setup/scripts/create_workstation.py" --path ~/Ailtir-Tendering
```

This creates `Context/`, `Bids/`, `Intelligence/`, `Active Projects/`, and `Daily/` in the user's home directory.

## Step 3 — Build the Context Folder

Once all questions are answered, write the data to the user's workspace.
Use the file operation tools to create the following files in `~/Ailtir-Tendering/Context/`:

- `~/Ailtir-Tendering/Context/company.md` (Company name, location, sectors, turnover, accreditations, win themes)
- `~/Ailtir-Tendering/Context/team.md` (Key personnel)
- `~/Ailtir-Tendering/Context/connectors.md` (Notion status and mapping)

## Step 4 — Write the Global CLAUDE.md

Read `${CLAUDE_PLUGIN_ROOT}/skills/ailtir-setup/templates/CLAUDE.md`. Replace the placeholders (`{{COMPANY_NAME}}`, etc.) with the data gathered in the interview.
Write the final result to `~/Ailtir-Tendering/CLAUDE.md` in the root of the workspace.

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

If you want to do that now, run `/ailtir-intelligence-builder`.
If you are using Notion, run `/ailtir-notion-setup` to build your databases.
Otherwise, drop a tender pack into the workspace and run `/bid-planner` to begin.
```

## Quality Checks

- [ ] `~/Ailtir-Tendering/` folder structure created with all required subfolders.
- [ ] `Context/company.md`, `Context/team.md`, and `Context/connectors.md` written with user-provided data.
- [ ] `CLAUDE.md` written to workstation root.
- [ ] No placeholder data shipped with the plugin appears in the output files.
