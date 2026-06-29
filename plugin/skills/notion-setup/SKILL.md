---
name: notion-setup
description: Builds the required Notion databases for an Ailtir workspace via the Notion MCP connector. Creates the Bid Pipeline, Subcontractor Directory, RFI Log, and CRM databases with the correct properties and relations. USE THIS when the user runs /ailtir-cowork-plugin:notion-setup or asks to set up their Notion databases.
---

# Ailtir Notion Database Setup

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" notion-setup >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" notion-setup > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" notion-setup >nul 2>nul
```

You are building the "business brain" for an Irish contractor in Notion.

Notion holds the business layer (pipelines, directories, logs). The local file system or SharePoint holds the project layer (drawings, specs, heavy files).

## Step 1 — Check Connector

Use `tool_search` to check if the Notion connector tools (e.g., `notion-create-database`, `notion-create-pages`) are available.
- **If available:** Proceed to Step 2.
- **If NOT available:** Tell the user to enable the Notion connector in their settings, then run this command again. Do not try to describe the tables in text — wait for the connector.

## Step 2 — Create the Hub Page

Use `notion-create-pages` to create a single top-level hub page named "Ailtir Business Hub". All databases will be nested under this page.

## Step 3 — Build the Databases

Read the schemas from `references/database-schemas.md`.
Use `notion-create-database` to build these four databases, setting the hub page as the parent:

1. **CRM (Clients & Architects)** — Build this first.
2. **Bid Pipeline** — Build this second. It needs a Relation property pointing to the CRM.
3. **Subcontractor Directory** — Build this third. Needs fields for CIRI and Safe-T-Cert.
4. **RFI Log** — Build this fourth. Needs a Relation property pointing to the Bid Pipeline.

## Step 4 — Confirm

Once built, update `references/database-schemas.md` with the actual database IDs returned by Notion.
Tell the user:
"Notion databases created successfully. You now have a connected CRM, Bid Pipeline, Subcontractor Directory, and RFI Log.

When you run `/ailtir-cowork-plugin:bid-planner` on a new tender, I will automatically log it in the Bid Pipeline. When you run `/ailtir-cowork-plugin:rfi-generator`, I will log the questions in the RFI Log."

- [HUMAN INPUT REQUIRED] Confirm the Notion connector is active before attempting to create databases.

## Anti-Patterns (What NOT to do)
- DO NOT proceed if the Notion connector is missing. Stop and instruct the user.
- DO NOT hallucinate database IDs. Wait for the connector to return them.
- DO NOT build duplicate databases if they already exist.

## Quality Checks
- [ ] All 4 databases created: CRM, Bid Pipeline, Subcontractor Directory, RFI Log.
- [ ] Bid Pipeline has a Relation property pointing to CRM.
- [ ] RFI Log has a Relation property pointing to Bid Pipeline.
- [ ] Subcontractor Directory includes CIRI and Safe-T-Cert checkbox fields.
