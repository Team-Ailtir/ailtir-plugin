---
name: prime
description: Session initialization. Syncs Notion databases to local markdown cache and presents a briefing. Triggered by /ailtir-cowork-plugin:prime.
---

# Ailtir Session Prime

This skill prepares the workspace for a new session.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, tell the user the workspace has not been set up and direct them to run `/ailtir-cowork-plugin:setup`. Do not continue.

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

Ask: "What are we tackling first?"
