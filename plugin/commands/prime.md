---
description: Session initialization. Syncs Notion databases to local markdown cache and presents a briefing. Triggered by /ailtir-cowork-plugin:prime.
---

# Ailtir Session Prime

This command prepares the workspace for a new session.

## Step 1 — Sync Notion Cache
Run the `sync_notion_cache.py` script to pull the latest data from the Notion databases (Bid Pipeline, Subcontractor Directory, CRM, RFI Log) into the local `Context/notion-cache/` folder.
```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/run_python.sh" "${CLAUDE_PLUGIN_ROOT}/commands/sync_notion_cache.py" --output-dir Context/notion-cache/
```

## Step 2 — Read Context
Read `Context/company.md`, `CLAUDE.md`, and the newly synced `Context/notion-cache/bid-pipeline.md`.
Read the `Daily/` notes from the last 3 days to understand recent activity.

## Step 3 — Provide Briefing
Present a concise, professional morning briefing:
- **Active Bids:** List the top 3 active bids and their return dates.
- **Pending Tasks:** List any outstanding items from recent Daily notes.
- **Suggested Focus:** Recommend what the user should focus on today.

Ask: "What are we tackling first?"
