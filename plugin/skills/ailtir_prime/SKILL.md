---
name: ailtir_prime
description: Session initialization. Syncs Notion databases to local markdown cache and presents a briefing. Triggered by /ailtir-cowork-plugin:ailtir_prime.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Session Prime

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_prime`
- `plugin_version`: `2.15.4`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

This skill prepares the workspace for a new session.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, tell the user the workspace has not been set up and direct them to run `/ailtir-cowork-plugin:ailtir_setup`. Do not continue.

Hold onto the `profile_key`, `region`, and `vertical` values — the briefing header uses them, and downstream skills read them from `Context/profile.json` when they need to branch.

## Step 2 — Sync Notion Cache
Run the bundled `scripts/sync_notion_cache.py` helper in this skill's directory with `python3`. Pass `--output-dir Context/notion-cache/`. This pulls the latest data from the Notion databases (Bid Pipeline, Subcontractor Directory, CRM, RFI Log) into the local cache folder.

## Step 3 — Read Context
Read `Context/company.md`, `CLAUDE.md`, and the newly synced `Context/notion-cache/bid-pipeline.md`.
Read the `Daily/` notes from the last 3 days to understand recent activity.

## Step 4 — Provide Briefing
Present a concise, professional morning briefing. Lead with the active profile so the user can see the plugin is not silently using defaults from another region:

```text
Active profile: {{REGION_NAME}} — {{VERTICAL_NAME}}   (profile_key: {{PROFILE_KEY}})
```

Use human-readable names: `Ireland` / `United Kingdom` for region, `General Contractor` for vertical.

Then present:
- **Active Bids:** List the top 3 active bids and their return dates.
- **Pending Tasks:** List any outstanding items from recent Daily notes.
- **Suggested Focus:** Recommend what the user should focus on today.

## Step 5 — Route to the Conductor

Check whether any bid folders exist under `Bids/` in the workspace root.

- **If at least one bid folder exists**, hand off to `ailtir_conductor` inline. Do not require a second slash command — proceed to run the conductor's flow now: read its SKILL.md, execute Step 1 (scan), Step 2 (backfill missing frontmatter), Step 3 (rank), Step 4 (recommend), and Step 5 (prompt) against the bids just surfaced in the briefing. The user should see one continuous experience: profile → briefing → "here's what to do next".
- **If no bids exist yet** (first-time user post-setup), offer the three onboarding branches instead:
  1. `/ailtir-cowork-plugin:ailtir_intelligence-builder` — capture case studies & win themes so quality-writer works from day one.
  2. `/ailtir-cowork-plugin:ailtir_notion-setup` — build the Notion CRM/Pipeline/Sub Directory/RFI Log.
  3. `/ailtir-cowork-plugin:ailtir_bid-planner` — start a bid on an ITT you already have.

Then ask: "What are we tackling first?"

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
