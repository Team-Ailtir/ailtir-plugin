---
name: ailtir_setup
description: First-time Ailtir workspace setup. Runs the onboarding interview and builds your local Context folder. Triggered by /ailtir-cowork-plugin:ailtir_setup.
---

# Ailtir Setup

## Step 0A — Feedback and Ailtir Connector

Before reporting usage, inspecting the workspace, or starting the interview,
tell the user:

> Ailtir provides this plugin free of charge. In return, we ask users to enable
> anonymous usage reporting and occasionally invite them to provide anonymous
> feedback. Usage reports contain the skill name, plugin version, timestamp,
> and an anonymous installation identifier that links events from this
> installation.
> They do not contain company names, tender documents, prices, workspace paths,
> or account details. Feedback is submitted only when you choose to answer it.

Check whether the bundled Ailtir MCP server exposes the `plugin_report_usage`
tool. Do not attempt to call a missing tool. If it is unavailable, tell the user
to:

1. Open **Customize → Connectors** in Claude.
2. Add a custom connector named **Ailtir** with the URL
   `https://app.ailtir.ai/ailtir-mcp`.
3. Enable the connector.
4. Restart Claude Desktop or start a new Cowork session.
5. Run `/ailtir-cowork-plugin:ailtir_setup` again.

Stop setup at that point without starting the company interview or writing
workspace files.

When the tool is available, run the bundled `scripts/feedback_schedule.py`
helper from the sibling `ailtir_feedback` skill with `configure --enabled true`.
Then read the stable anonymous UUID from `~/Ailtir-Tendering/install_id`. If the
file is missing, create its parent directory, generate a UUID v4, and write only
that UUID to the file. Re-read the file and call `plugin_report_usage` with:

- `skill_name`: `ailtir_setup`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

Initialize a new Ailtir workspace. Act as an onboarding consultant.

## Step 0B — Workspace Pre-flight

Before starting the interview, check whether the workspace has already been set up. Look for a `CLAUDE.md` file in the workspace root (`AILTIR_PLUGIN_DATA` or `~/Ailtir-Tendering`) with `os: ailtir-cowork` in its YAML frontmatter.

- If it does **not** exist → proceed to Step 1 (fresh setup).
- If it **does** exist → use `AskUserQuestion` to offer three choices, and act accordingly:
  1. **Update profile** — re-run the interview, refresh `Context/*.md` and `Context/profile.json`, rewrite the workspace `CLAUDE.md`. Preserve `Bids/`, `Active Projects/`, `Intelligence/`, and `Daily/`.
  2. **Full reset** — delete `Context/` and workspace `CLAUDE.md`. Ask for confirmation a second time before deleting. Preserve `Bids/`, `Active Projects/`, `Intelligence/`, and `Daily/` (destroying tender history is never appropriate here).
  3. **Cancel** — exit the skill with no changes.

## Step 1 — The Interview

Ask the user the following questions, ONE AT A TIME. Wait for their answer before asking the next. Do NOT ask all questions at once. Be conversational and professional.

1. **Company Name:** What is the name of the contracting company?
2. **Location & Sectors:** Where are you based, and what are your primary sectors (e.g., Commercial, Residential, Public Works)?
3. **Region:** Which market do you primarily tender in — Ireland or the UK? (Use `AskUserQuestion` with the options: "Ireland" and "United Kingdom". Default to Ireland if the user is on the fence.) Store the answer as `ireland` or `uk`.
4. **Vertical:** What is your role in that market? For v1 the only supported answer is **General Contractor (main contractor)**. Confirm this with the user. Store the answer as `gc`. Civil-engineering-only contractors and consulting engineers are planned for a later release — if the user says they are one of those, note it in `Context/company.md` under "Sectors" and continue with `gc` for now.
5. **Turnover & Size:** What is your rough annual turnover and typical project value range?
6. **Accreditations:** What key accreditations do you hold?
   - If Region = Ireland, prompt for CIRI, Safe-T-Cert, ISO 9001/14001/45001.
   - If Region = UK, prompt for SSIP (CHAS/SafeContractor/Constructionline Gold), ISO 9001/14001/45001, and Building Safety Act competency where relevant.
7. **Key Personnel:** Who are the key directors or bid team members I should know about?
8. **Connectors:** Are we using Notion for the business databases (CRM, Pipeline, Subcontractors, RFIs)?
9. **Win Themes:** What are your top 3 differentiators when bidding against competitors?

## Step 2 — Create the Workstation Structure

Run the Python script to build the definitive Ailtir workstation folder structure:

Run the bundled `scripts/create_workstation.py` helper in this skill's directory with `python3`. No arguments needed.

This uses `AILTIR_PLUGIN_DATA` as the workspace root. If it is not set, it defaults to `~/Ailtir-Tendering`. It creates `Context/`, `Bids/`, `Intelligence/`, `Active Projects/`, and `Daily/` under that root.

## Step 3 — Derive the Profile

From the Region and Vertical answers, compute:

- `profile_key` = `{region}-{vertical}` (e.g. `ireland-gc`, `uk-gc`).
- `currency` = `EUR` if region is `ireland`, `GBP` if region is `uk`.
- `date_format` = `DD/MM/YYYY` for both supported regions.

## Step 4 — Write `Context/profile.json`

Write the following file to `Context/profile.json` in the workspace root, substituting today's date for `{{DATE}}` (in `YYYY-MM-DD` format):

```json
{
  "region": "{{REGION}}",
  "vertical": "{{VERTICAL}}",
  "currency": "{{CURRENCY}}",
  "date_format": "DD/MM/YYYY",
  "profile_key": "{{PROFILE_KEY}}",
  "created": "{{DATE}}",
  "schema_version": 1
}
```

This file is the single source of truth for which region/vertical the workspace targets. Every skill that needs to branch on jurisdiction reads it.

## Step 5 — Build the Context Folder

Once all questions are answered, write the data to the user's workspace.
Resolve the workspace root from `AILTIR_PLUGIN_DATA`, or use `~/Ailtir-Tendering` if it is not set. Use the file operation tools to copy and customise the templates bundled with this skill at `templates/Context/`:

- Read `templates/Context/company.md` from this skill's directory, replace placeholders, and write to `Context/company.md` in the workspace.
- Read `templates/Context/team.md` from this skill's directory, replace placeholders, and write to `Context/team.md` in the workspace.
- Read `templates/Context/connectors.md` from this skill's directory, replace `{{ACTIVE_CONNECTORS}}` with the user's Notion status, and write to `Context/connectors.md` in the workspace.

## Step 6 — Write the Global CLAUDE.md

Pick the correct workspace CLAUDE.md template based on `profile_key`:

- `ireland-gc` → read `templates/CLAUDE.ireland-gc.md` from this skill's directory.
- `uk-gc` → read `templates/CLAUDE.uk-gc.md` from this skill's directory.

Replace the placeholders (`{{COMPANY_NAME}}`, `{{LOCATION}}`, `{{SECTORS}}`, `{{ACCREDITATIONS}}`, `{{DATE}}`) with the data gathered in the interview.
Write the final result to `CLAUDE.md` in the root of the workspace.

- [HUMAN INPUT REQUIRED] All interview questions must be answered by the user before writing any Context files.

## Anti-Patterns

- DO NOT ask all the interview questions in a single message.
- DO NOT write files until the interview is fully complete.
- DO NOT hallucinate company details if the user skips a question; write `[Not provided]` instead.
- DO NOT silently overwrite an existing workspace — always run the Step 0 pre-flight.
- DO NOT invent a new profile key. If the user asks for a region or vertical outside `ireland-gc`/`uk-gc`, tell them clearly it is not yet supported and offer the closest match.

## Step 7 — Next Steps

Tell the user:

```text
Setup complete. Your workspace is configured for [Company Name] on the [profile_key] profile.

To get the most out of the quality-writer from day one, we should add 2-3 case studies and your top win themes to the `Intelligence/` folder. I can interview you for 10 minutes to write them up, or you can point me to a folder of old CVs and tenders and I'll extract them automatically.

If you want to do that now, run `/ailtir-cowork-plugin:ailtir_intelligence-builder`.
If you are using Notion, run `/ailtir-cowork-plugin:ailtir_notion-setup` to build your databases.
Otherwise, drop a tender pack into the workspace and run `/ailtir-cowork-plugin:ailtir_bid-planner` to begin.

Once you have a bid or two in flight, run `/ailtir-cowork-plugin:ailtir_conductor` for a proactive "what should I do next?" view across every bid — or `/ailtir-cowork-plugin:ailtir_dashboard` for the visual version. You never need to memorise the 30+ skill catalogue; the conductor will always tell you what to run next.
```

## Quality Checks

- [ ] Reporting was explained before the first usage event.
- [ ] The Ailtir connector was available before onboarding began.
- [ ] Occasional feedback scheduling was enabled locally.
- [ ] Pre-flight ran — either fresh setup, update, or cancel (never silent overwrite).
- [ ] Workspace folder structure created under `AILTIR_PLUGIN_DATA` or `~/Ailtir-Tendering` with all required subfolders.
- [ ] `Context/profile.json` written with valid `region`, `vertical`, `currency`, `date_format`, `profile_key`, `created`, `schema_version`.
- [ ] `Context/company.md`, `Context/team.md`, and `Context/connectors.md` written with user-provided data.
- [ ] `CLAUDE.md` written to workstation root using the correct region-specific template.
- [ ] No placeholder data shipped with the plugin appears in the output files.
