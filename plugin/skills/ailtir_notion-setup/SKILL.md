---
name: ailtir_notion-setup
description: Builds the required Notion databases for an Ailtir workspace via the Notion MCP connector. Creates the Bid Pipeline, Subcontractor Directory, RFI Log, and CRM databases with the correct properties and relations. USE THIS when the user runs /ailtir-cowork-plugin:ailtir_notion-setup or asks to set up their Notion databases.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Notion Database Setup

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_notion-setup`
- `plugin_version`: `2.15.3`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are building the "business brain" for a construction contractor in Notion. The database schemas are a superset across the `ireland-gc` and `uk-gc` profiles — the user simply leaves fields they do not need blank.

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
3. **Subcontractor Directory** — Build this third. Needs the profile-aware accreditation fields defined in `references/database-schemas.md` (CIRI, Safe-T-Cert, SSIP, CHAS, SafeContractor, Constructionline, ISO tiers, Modern Slavery statement, insurance expiry).
4. **RFI Log** — Build this fourth. Needs a Relation property pointing to the Bid Pipeline.

## Step 4 — Confirm

Once built, update `references/database-schemas.md` with the actual database IDs returned by Notion.
Tell the user:
"Notion databases created successfully. You now have a connected CRM, Bid Pipeline, Subcontractor Directory, and RFI Log.

When you run `/ailtir-cowork-plugin:ailtir_bid-planner` on a new tender, I will automatically log it in the Bid Pipeline. When you run `/ailtir-cowork-plugin:ailtir_rfi-generator`, I will log the questions in the RFI Log."

- [HUMAN INPUT REQUIRED] Confirm the Notion connector is active before attempting to create databases.

## Anti-Patterns (What NOT to do)
- DO NOT proceed if the Notion connector is missing. Stop and instruct the user.
- DO NOT hallucinate database IDs. Wait for the connector to return them.
- DO NOT build duplicate databases if they already exist.

## Quality Checks
- [ ] All 4 databases created: CRM, Bid Pipeline, Subcontractor Directory, RFI Log.
- [ ] Bid Pipeline has a Relation property pointing to CRM.
- [ ] RFI Log has a Relation property pointing to Bid Pipeline.
- [ ] Subcontractor Directory includes the full accreditation superset from `references/database-schemas.md` (Irish CIRI/Safe-T-Cert plus UK SSIP/CHAS/SafeContractor/Constructionline/ISO tiers/Modern Slavery).
