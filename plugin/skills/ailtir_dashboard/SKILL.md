---
name: ailtir_dashboard
description: Builds a live interactive HTML dashboard as a Claude Artifact, pulling data from Notion via MCP to visualise the bid pipeline, subcontractor register, and BD KPIs. Triggered by /ailtir-cowork-plugin:ailtir_dashboard.
---

# Ailtir Dashboard Builder

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_dashboard`
- `plugin_version`: `2.15.0`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are building a live interactive HTML dashboard as a Claude Artifact. The dashboard reads data from the Notion databases via MCP and renders it as a visual, interactive page inside the Claude conversation.

## Before You Start

Read the Notion database IDs from `Context/notion-cache/databases.md`. You need:
- Bid Pipeline database ID
- Subcontractor Directory database ID
- CRM database ID
- RFI Log database ID

**Also read every bid's phase state.** Run the sibling `ailtir_conductor` skill's `scripts/scan_bids.py` helper with `python3` and `--bids-dir Bids/`. Parse the JSON it prints — each record has `bid_id`, `frontmatter.phase`, `frontmatter.next_action.skill`, and `frontmatter.blockers`. Hold this in memory as `bidState` for use in the Bid Pipeline dashboard (Step 4, Dashboard 1). This gives the dashboard a live view of each bid's phase/next action that mirrors what `ailtir_conductor` recommends. If `scripts/scan_bids.py` returns an empty array or errors, fall back gracefully — render the Notion data alone and skip the Phase/Next column.

---

## Step 1 — Ask Which Dashboard

Ask the user which view they want:

| Option | Dashboard | What It Shows |
|---|---|---|
| 1 | **Bid Pipeline** | All active bids by stage, value, deadline, and strategic fit score |
| 2 | **BD KPIs** | Win rate, pipeline coverage ratio, bids by sector and region |
| 3 | **Subcontractor Register** | All subs by trade, profile-appropriate accreditation status (CIRI/Safe-T-Cert under `ireland-gc`; SSIP/Constructionline under `uk-gc`), and last used date |
| 4 | **RFI Tracker** | Open RFIs by bid, age, and status |

---

## Step 2 — Fetch Data from Notion

Use the Notion MCP connector to fetch records from the relevant database.

```javascript
// Use the cowork MCP pattern
const raw = await window.cowork.callMcpTool('list_records_for_table', {
  table_id: '[DATABASE_ID]'
});
const records = unwrap(raw);
```

Always use the `unwrap()` and `getField()` helper functions. Never index into connector responses directly.

---

## Step 3 — Build the Artifact

Create an HTML artifact with the following structure:

### Ailtir Dashboard Skeleton

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ailtir — [Dashboard Name]</title>
  <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    /* Ailtir brand colours */
    :root {
      --navy-900: #0A1128;
      --navy-800: #0F1A3C;
      --navy-700: #1A2550;
      --purple-600: #6D28D9;
      --purple-500: #7C3AED;
      --purple-400: #8B5CF6;
      --amber-400: #F59E0B;
      --white: #FFFFFF;
      --text-body: rgba(255,255,255,0.70);
      --text-muted: rgba(255,255,255,0.50);
      --border-standard: rgba(255,255,255,0.07);
    }
    body { font-family: 'Inter', sans-serif;
           background-color: var(--navy-900);
           background-image: radial-gradient(rgba(139,92,246,0.14) 1px, transparent 1px), radial-gradient(ellipse 50% 60% at 72% 50%, rgba(109,40,217,0.14), transparent);
           background-size: 28px 28px, 100% 100%;
           color: var(--text-body); margin: 0; padding: 0; }
    h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.03em; color: var(--white); }
    header { background: var(--navy-800); color: var(--white); padding: 20px 32px;
             display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-standard); }
    header h1 { margin: 0; font-size: 20px; font-weight: 500; }
    header .subtitle { margin: 4px 0 0; font-size: 13px; color: var(--text-secondary); font-family: 'Inter', sans-serif; }
    .last-loaded { font-size: 12px; color: var(--text-muted); }
    .kpi-strip { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                 gap: 16px; padding: 24px 32px; }
    .kpi-tile { background: rgba(255,255,255,0.03); border: 1px solid var(--border-standard); border-radius: 8px; padding: 20px; }
    .kpi-tile .label { font-size: 11px; color: var(--purple-400); text-transform: uppercase;
                       letter-spacing: 0.2em; margin-bottom: 8px; }
    .kpi-tile .value { font-size: 32px; font-weight: 700; color: var(--white); font-family: 'Space Grotesk', sans-serif; font-variant-numeric: tabular-nums; }
    .kpi-tile .delta { font-size: 12px; margin-top: 4px; color: var(--text-muted); }
    .ai-summary { background: var(--navy-800); border-left: 4px solid var(--purple-500);
                  margin: 0 32px 24px; padding: 16px 20px; border-radius: 0 8px 8px 0;
                  font-size: 14px; line-height: 1.7; border: 1px solid var(--border-standard); border-left-width: 4px; }
    .section { padding: 0 32px 32px; }
    .section h2 { font-size: 18px; font-weight: 500; margin-bottom: 16px; color: var(--white); }
    table { width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.03);
            border-radius: 8px; overflow: hidden; border: 1px solid var(--border-standard); }
    th { background: var(--navy-700); color: var(--white); padding: 12px 16px;
         text-align: left; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; border-bottom: 1px solid var(--border-standard); }
    td { padding: 12px 16px; border-bottom: 1px solid var(--border-standard); font-size: 14px; color: var(--text-body); }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255,255,255,0.05); }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 12px;
             font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; }
    .badge-purple { background: var(--purple-500); color: var(--white); }
    .badge-amber { background: rgba(245,158,11,0.2); color: var(--amber-400); border: 1px solid rgba(245,158,11,0.5); }
    .badge-muted { background: rgba(124,58,237,0.2); color: var(--purple-400); border: 1px solid rgba(124,58,237,0.3); }
    .chart-container { background: rgba(255,255,255,0.03); border: 1px solid var(--border-standard); border-radius: 8px; padding: 24px; }
    footer { padding: 16px 32px; font-size: 12px; color: var(--text-muted);
             border-top: 1px solid var(--border-standard); display: flex; align-items: center; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Ailtir — [Dashboard Name]</h1>
      <p class="subtitle">[Purpose one-liner]</p>
    </div>
    <div class="last-loaded" id="loaded-time">Loading...</div>
  </header>

  <div class="kpi-strip" id="kpi-strip">
    <!-- KPI tiles injected by JS -->
  </div>

  <div class="ai-summary" id="ai-summary">
    Loading summary...
  </div>

  <div class="section">
    <h2>[Primary View Title]</h2>
    <!-- Table or chart injected by JS -->
    <div id="primary-view"></div>
  </div>

  <div class="section" style="padding-top:0;">
    <div style="background: rgba(124,58,237,0.08); border: 1px solid rgba(124,58,237,0.3); border-radius: 8px; padding: 14px 18px; font-size: 13px; color: var(--text-body);">
      <strong style="color: var(--white);">Next actions</strong> — to act on these recommendations, run
      <code style="background: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 4px; color: var(--purple-400);">/ailtir-cowork-plugin:ailtir_conductor</code>
      in your Claude session.
    </div>
  </div>

  <footer>
    <span>Sources: Notion + local bid frontmatter · Loaded <span id="footer-time">just now</span></span>
    <a href="#" id="debug-toggle" style="font-size:11px;opacity:0.5;margin-left:12px;">debug</a>
  </footer>
  <div id="debug-panel" style="display:none;margin:0 32px 32px;padding:12px;background:#f4f4f4;
       border:1px solid #ddd;font:11px/1.4 monospace;white-space:pre-wrap;max-height:400px;overflow:auto;"></div>

  <script>
    // ── Helpers ──────────────────────────────────────────────────────────────
    window.__dashboardDebug = [];
    function unwrap(raw) {
      if (!raw) return [];
      if (Array.isArray(raw)) return raw;
      const keys = Object.keys(raw);
      for (const k of keys) { if (Array.isArray(raw[k])) return raw[k]; }
      return [];
    }
    function getField(record, fieldName) {
      if (!record || !record.fields) return null;
      return record.fields[fieldName] ?? null;
    }

    // ── Debug panel ──────────────────────────────────────────────────────────
    document.getElementById('debug-toggle').addEventListener('click', (e) => {
      e.preventDefault();
      const panel = document.getElementById('debug-panel');
      panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
      panel.textContent = JSON.stringify(window.__dashboardDebug, null, 2);
    });

    // ── Main data load ───────────────────────────────────────────────────────
    async function loadDashboard() {
      try {
        // [REPLACE THIS BLOCK with the actual MCP fetch for the chosen dashboard]
        const raw = await window.cowork.callMcpTool('list_records_for_table', {
          table_id: '[DATABASE_ID]'
        });
        const records = unwrap(raw);
        window.__dashboardDebug.push({ tool: 'list_records', count: records.length });

        // [REPLACE THIS BLOCK with the rendering logic for the chosen dashboard]
        renderKPIs(records);
        renderSummary(records);
        renderPrimaryView(records);

        document.getElementById('loaded-time').textContent =
          'Loaded ' + new Date().toLocaleTimeString('en-IE');
        document.getElementById('footer-time').textContent =
          new Date().toLocaleTimeString('en-IE');

      } catch (err) {
        document.getElementById('ai-summary').textContent =
          'Error loading data: ' + err.message + ' — click debug for details.';
        window.__dashboardDebug.push({ error: err.message });
      }
    }

    loadDashboard();
  </script>
</body>
</html>
```

---

## Step 4 — Dashboard-Specific Logic

### Dashboard 1: Bid Pipeline

**KPIs to show:** Total pipeline value (in the currency from `Context/profile.json` — € for `ireland-gc`, £ for `uk-gc`), Active bids, Bids due this week, Win rate (rolling 12 months from Notion data).

**Primary view:** Kanban-style stage columns (Lead → Go/No-Go → Active Bid → Submitted → Won/Lost) with bid cards showing value and deadline.

**Secondary view:** Bar chart of pipeline value by sector.

**Tertiary view — Phase & Next Action table.** Below the Kanban, render a table with one row per bid from the `bidState` array (from `ailtir_conductor`'s `scan_bids.py`). Columns:

| Bid | Phase | Next Action | Blockers |
|-----|-------|-------------|----------|

Colour-code the `Phase` cell using the Ailtir brand palette only:
- `opportunity` → `--purple-400` background
- `pre-bid`     → `--purple-500` background
- `estimating`  → `--purple-600` background
- `submission`  → `--amber-400` background
- `post-tender` → `--navy-700` background
- `delivery`    → `--navy-800` background
- `closed`      → muted `--text-muted` text, no background

`Next Action` shows the value of `frontmatter.next_action.skill` as a purple pill badge (`.badge-muted` class). `Blockers` shows an amber pill for each blocker (`.badge-amber` — never red, per brand rules).

If `bidState` is empty (no bids, or `scan_bids.py` unavailable), omit this table entirely.

**Status badge logic (deadline column):**
- Deadline > 14 days: green
- Deadline 7–14 days: amber
- Deadline < 7 days: red

### Dashboard 2: BD KPIs

**KPIs to show:** Win rate %, Pipeline coverage ratio (weighted pipeline / annual target), Average strategic fit score, Bids submitted this quarter.

**Primary view:** Table of all submitted bids with outcome, value, and score.

**Secondary view:** Doughnut chart of bids by sector.

### Dashboard 3: Subcontractor Register

**KPIs to show:** Total subs, Subs used in last 12 months, plus the accreditation percentages appropriate to the active profile. Under `ireland-gc`: CIRI registered %, Safe-T-Cert %. Under `uk-gc`: SSIP %, Constructionline Gold+ %, Modern Slavery statement current %.

**Primary view:** Table with the profile-appropriate accreditation status badges (green = valid, red = expired/missing). Read `Context/profile.json` to decide which columns to render.

### Dashboard 4: RFI Tracker

**KPIs to show:** Open RFIs, Overdue RFIs (no answer in > 5 working days), RFIs answered this week.

**Primary view:** Table of open RFIs with age (days since sent) and status badges.

---

## Step 5 — Verification Handshake

After creating the artifact, ask the user: "Can you see the data on screen? If the dashboard is empty, click the 'debug' link in the footer to see what the connector returned."

If the data is missing or malformed, use `update_artifact` to patch the parsing logic — do not rebuild the whole dashboard.

---

- [HUMAN INPUT REQUIRED] Confirm the data source (Notion cache or manual input) with the user before generating the dashboard.

## Anti-Patterns (What NOT to do)

- **DO NOT index into connector responses directly.** Always use `unwrap()` and `getField()`.
- **DO NOT skip the debug panel.** It is the only way to diagnose empty dashboards without rebuilding.
- **DO NOT use Airtable patterns from ContractorOS.** Ailtir uses Notion — the MCP tool names and response shapes are different.
- **DO NOT present the artifact as done until the user confirms data is visible on screen.**
- **DO NOT use colours outside the Ailtir brand palette** (navy `#0A1128`, purple `#7C3AED`, amber `#F59E0B`). Never use teal or red.

## Quality Checks
- [ ] Dashboard uses Ailtir brand colours only (navy `#0A1128`, purple `#7C3AED`, amber `#F59E0B`).
- [ ] No teal or red colours used anywhere in the HTML output.
- [ ] Space Grotesk used for all headings, Inter for all body text.
- [ ] All KPI figures sourced from `Context/notion-cache/` — no hallucinated numbers.
