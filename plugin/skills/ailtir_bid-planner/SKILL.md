---
name: ailtir_bid-planner
description: The master Phase 1 orchestrator for a new tender. Catalogues the tender pack, runs Go/No-Go analysis, extracts compliance requirements, flags contract risks against the active Ailtir profile's playbook (Irish PW-CF/RIAI or UK JCT/NEC4), and generates a 9-tab Bid Plan Workbook and folder structure. Triggered by /ailtir_bid-planner.
---

# Ailtir Bid Planner — Phase 1 Orchestrator

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_bid-planner`
- `plugin_version`: `2.16.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are a Bid Manager orchestrating a new tender. Your job is to run a chained workflow that analyses the tender pack and produces a working Bid Plan Excel workbook.

This is a planning tool, not a decision-maker. It builds the framework for the human team to decide.

## Human-in-the-Loop Checkpoints
Pause at three points:
1. **After context gathered** — "Here's what I'm working with. Correct before I catalogue?"
2. **After analysis** — Present headline findings (gaps, DQ risks, Go/No-Go score). Ask: "Anything to adjust before I build the workbook?"
3. **After generation** — Present the Excel workbook and ZIP folder.

---

## Step 0 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir_setup`. The `profile_key` value selects the reference files this skill reads in Step 2 — the Go/No-Go criteria (Step 2B) and the contract playbook (Step 2D), both under `references/{profile_key}/`.

## Step 1 — Gather Context

Ask conversationally:
1. Project name?
2. Client / Employer?
3. Tender return date and time?
4. What documents have you uploaded?
5. Procurement route? Under `ireland-gc` — CWMF Restricted, CWMF Open, Private Negotiated, Private D&B, Framework. Under `uk-gc` — Open Procedure, Competitive Flexible Procedure, Direct Award, Framework Call-Off, Dynamic Market, Private Traditional / D&B.

---

## Step 2 — Analyse the Pack (Work Silently, Build One Data Object)

This is the shallow-but-complete first pass. Do all of the following analysis,
then assemble a single JSON object (the `--data` payload for Step 3). Do NOT
call `openpyxl` yourself and do NOT invoke sibling skills — the planner does the
summary depth here; the deep dives come later.

### A. Document register + gaps
Catalogue every document (filename, title, type, rev, date, notes). Cross-
reference BOQ references against the document list; list any missing files.

### B. Go/No-Go — full scoring (inlined)
Read `references/{profile_key}/go-no-go-criteria.md` from THIS skill's directory.
Check every mandatory gate and score all four weighted dimensions against the
bands in that file. This is done in full here — the planner owns go/no-go.

### C. Compliance & submission (summary depth — one row per item)
Extract every returnable and evaluation criterion (with exact weightings) and the
submission rules (method, format, naming, deadlines). One row each — this is the
glance view, not the full tracker.

### D. Risk summary (summary depth — top 5)
Identify the contract form and flag the top 5 commercial risks against the
profile playbook. One row each.

### E. Package outline (summary depth)
List the likely trade packages at a high level. If packages cannot yet be
determined, leave empty with an N/A note — the full register is a later phase.

### Assemble the data payload
Write the results to a JSON file (e.g. `/tmp/bid_plan_data.json`) with this shape.
Every key is optional; omit a section and its tab renders with an N/A note.

```json
{
  "tabs": {
    "document_register": {"rows": [["file.pdf","Title","Spec","P1","2026-01-01","note"]]},
    "go_no_go": {"score": 72, "gate_fail": false,
                 "rows": [["Client & Relationship","30","20","Known client"]]},
    "compliance_submission": {"sections": {
        "returnables": {"rows": [["Vol B","Form of Tender","Pass/Fail","YES","Director"]]},
        "submission_rules": {"rows": [["Deadline","28/02 16:00 via eTenders"]]}}},
    "risk_summary": {"rows": [["CR-01","20-day time bar","RED","Loss of EOT","Notice register"]]},
    "package_outline": {"rows": [], "na_note": "N/A at plan stage — see enquire-and-procure phase."},
    "bid_programme": {"rows": [["Query deadline","2026-02-07","Bid Mgr",""]]},
    "team_raci": {"rows": [["Pricing","QS","Director","Estimator","PM"]]},
    "clarifications": {"rows": [["CL-01","Portal access?","2026-01-10","Open",""]]}
  },
  "optional_tabs": [
    {"title": "Design Risk", "headers": ["Item","Note"], "rows": [["PI cover","Fitness-for-purpose flagged"]]}
  ]
}
```

**Adaptation rules (fixed core + judgement at the edges):**
- The 9 core tabs are always built. If a core section does not apply to this
  tender, supply `"rows": []` and an `"na_note"` explaining why (e.g. price-only
  → no quality returnables). Never omit a core tab to "clean up".
- Pre-populate `team_raci` from the team members in `Context/profile.json` /
  `Context/company.md` where present; otherwise use role names.
- Add an entry to `optional_tabs` ONLY when the tender genuinely needs a tab the
  core set lacks — e.g. `Design Risk` on D&B, `Framework Call-Off` on a call-off,
  `Lots` on a multi-lot public tender. Give it `title`, `headers`, `rows`.

---

## Step 3 — Generate Outputs

### Part A — The Bid Plan Workbook
Run the bundled `scripts/create_bid_plan.py` helper in this skill's directory with
`python3`, passing the data payload from Step 2. Do NOT populate tabs with
`openpyxl` yourself — the script owns all structure and styling:

- `--output "Bid_Plan_[Project].xlsx"`
- `--project "[Name]"`
- `--client "[Client]"`
- `--return-date "YYYY-MM-DD"`
- `--route "[Route]"`
- `--data "/tmp/bid_plan_data.json"`

The workbook has 9 fixed core tabs (Bid Summary, Document Register, Go/No-Go,
Compliance & Submission, Risk Summary, Package Outline, Bid Programme, BID TEAM
RACI, Clarifications Log) plus any optional tabs you declared. The Go/No-Go score
and recommendation are computed by the script from your payload.

### Part A2 — The Kick-Off Deck (shareable)
Build a JSON config from the same analysis and run the bundled
`scripts/create_bid_deck.js` helper with `node` (run `npm install` in the
`scripts/` dir first if `node_modules` is absent):

`node scripts/create_bid_deck.js --config /tmp/bid_deck.json --output "Bid_KickOff_[Project].pptx"`

This is an internal working deck (Title → Overview → Pack Status → Submission
Requirements → Programme → Packages → Top Risks → Immediate Actions). Set
`"priceOnly": true` in the config to skip quality sections. The config shape (all
keys optional; a missing array just renders an empty slide):

```json
{
  "project": "[Name]", "client": "[Client]", "value": "€2.0M", "sector": "Civils",
  "returnDate": "YYYY-MM-DD", "priceOnly": false,
  "overview": ["Road widening", "New bridge"],
  "packStatus": {"received": 12, "missing": 2, "gaps": 3},
  "missingDocs": [{"doc": "Geotech report", "impact": "Pricing blind"}],
  "requirements": [{"ref": "WP-1", "text": "PSCS statement", "weight": "", "owner": "Director"}],
  "programme": [{"date": "2026-02-07", "label": "Query deadline"}],
  "packages": [{"name": "Groundworks"}, {"name": "Concrete"}],
  "risks": [{"title": "20-day time bar", "owner": "Commercial"}],
  "actions": [{"when": "TODAY", "what": "Issue subbie enquiries", "who": "Estimator"}]
}
```

### Part B — Folder Structure
Generate a Bid Reference Number (format: `YYYY-NNN-ProjectName`, e.g. `2026-004-BallymunSchool`). Check the Notion Bid Pipeline for the next sequential number, or ask the user.

Run the bundled `scripts/create_bid_folders.py` helper to generate the 9-section folder structure directly in the workstation. Invoke it with `python3` and pass:
- `--bid-ref "[Bid Reference]"`
- `--packages "Groundworks, Concrete, Steel, Roofing, MEP"`
- `--quality-questions "Q1 Methodology, Q2 Programme, Q3 Health and Safety"`
- `--has-interviews` (omit if no interviews)

*(Adjust the `--packages`, `--quality-questions`, and `--has-interviews` arguments based on the ITT analysis from Step 2.)*
This creates the `Bids/[Bid Reference]/` folder with all subdirectories and the initial README.

---

## Step 4 — Present Findings

Present a concise summary to the user:
- Document count & Gap count
- Preliminary Go/No-Go Score
- Top 3 Contract Risks
- Provide the `.xlsx` file (the folders are created directly on disk).

Then present the handoff explicitly — the workbook is a summarised first pass:

> The bid plan and kick-off deck are ready. Go/No-Go is done in full. The
> Compliance, Risk, and Package tabs are **summarised** — run the deep dives when
> you commit to bidding:
> - `/ailtir_contract-risk` — full clause-by-clause register, contract data & actions
> - `/ailtir_compliance-matrix` — full returnables tracker with templates, owners & deadlines
>
> See `PROCESS.md` for how the whole bid lifecycle fits together.

---

## On Completion — Update Bid State

When this workflow finishes for a specific bid, record what was done so the
conductor and dashboard reflect it. Run the sibling `ailtir_conductor` skill's
`scripts/update_frontmatter.py` with `python3`, once per analysis:

```
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_bid-planner --result proceed
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_go-no-go --result proceed
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_compliance-matrix --result summarised
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_contract-risk --result summarised
```

Record `ailtir_bid-planner` itself as `proceed` — without this entry the
conductor would recommend the planner again as the first unfinished pre-bid
step. Go/No-Go is `proceed` (done in full). Compliance and contract-risk are
`summarised` — the conductor will recommend them as deep dives, not repeats.

---

## Step 5 — Bid Close-Out (Run Only When Status Changes to Won/Lost)

If the user tells you the bid has been won or lost (or if you notice the status change in the Notion Bid Pipeline), you **must** prompt them to capture intelligence before closing out the bid.

Say:
> "I see this bid is now marked as [Won/Lost]. Before we close it out, let me capture a case study and lessons-learned entry for your `Intelligence/` folder. This takes 5 minutes and will improve every future bid. Shall we do it now?"

If they agree, run the `intelligence-builder` skill in Interview Mode.

## Anti-Patterns (What NOT to do)
- DO NOT skip the human checkpoints. Wait for the user to confirm before proceeding.
- DO NOT run the Python scripts with missing arguments. Check the script requirements first.
- DO NOT hallucinate the risk positions. Use the contract playbook.
- [HUMAN INPUT REQUIRED] Do not run `create_bid_folders.py` without first confirming the bid reference, package list, and quality question list with the user.
- [HUMAN INPUT REQUIRED] Do not log the bid to Notion without confirming the contract value and return date with the user.

## Quality Checks
- [ ] `Context/profile.json` read; `profile_key` used to select the Step 2 reference files (analysis done inline — no sibling skills invoked).
- [ ] Bid reference follows format YYYY-NNN-ProjectName.
- [ ] Go/No-Go score is based on actual scoring criteria from `references/{profile_key}/go-no-go-criteria.md`, not a guess.
- [ ] All mandatory gates for the active profile explicitly checked (CIRI/Safe-T-Cert/turnover for `ireland-gc`; SSIP/turnover/BSA/Modern Slavery for `uk-gc`).
- [ ] Compliance & Submission tab carries one row per returnable/criterion (summary depth — the full tracker is deferred to `/ailtir_compliance-matrix`).
- [ ] Bid folder created under the workspace root (`AILTIR_PLUGIN_DATA` or `~/Ailtir-Tendering`) at `Bids/[BID]/` with all 9 sections.
- [ ] Bid logged to Notion Bid Pipeline with correct status and return date.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
