---
name: ailtir_bid-planner
description: The master Phase 1 orchestrator for a new tender. Catalogues the tender pack, runs Go/No-Go analysis, extracts compliance requirements, flags contract risks against the active Ailtir profile's playbook (Irish PW-CF/RIAI or UK JCT/NEC4), and generates a 9-tab Bid Plan Workbook and folder structure. Triggered by /ailtir-cowork-plugin:ailtir_bid-planner.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Bid Planner — Phase 1 Orchestrator

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_bid-planner`
- `plugin_version`: `2.15.4`
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
Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir-cowork-plugin:ailtir_setup`. The `profile_key` value drives Steps 2B and 2D and — through the downstream skills — every other analysis in this orchestrator.

## Step 1 — Gather Context

Ask conversationally:
1. Project name?
2. Client / Employer?
3. Tender return date and time?
4. What documents have you uploaded?
5. Procurement route? Under `ireland-gc` — CWMF Restricted, CWMF Open, Private Negotiated, Private D&B, Framework. Under `uk-gc` — Open Procedure, Competitive Flexible Procedure, Direct Award, Framework Call-Off, Dynamic Market, Private Traditional / D&B.

---

## Step 2 — The Chained Analysis (Work Silently)

Run these four analysis steps in sequence. Store the results in memory to feed the Python script later.

### A. Tender Indexing (Invoke `project-indexer` logic)
Catalogue every document. Extract all dates (return, site visit, clarification deadline). Cross-reference BOQ references against the document list to find missing files. Flag critical gaps.

### B. Go/No-Go Assessment (Invoke `go-no-go` logic)
Read `references/{profile_key}/go-no-go-criteria.md` from this skill's directory. Evaluate the tender against the profile-appropriate criteria. Calculate a preliminary score. Flag any mandatory gate failures — under `ireland-gc` these include missing CIRI or Safe-T-Cert; under `uk-gc` these include missing SSIP membership, missing Modern Slavery statement (if applicable), and missing Building Safety Act competency where the project is a Higher-Risk Building.

### C. Compliance Matrix (Invoke `compliance-matrix` logic)
Extract every submission requirement, evaluation criterion, and mandatory returnable document from the ITT. Note if templates were provided.

### D. Contract Risk (Invoke `contract-risk` logic)
Identify the contract form (under `ireland-gc`: PW-CF1-5, RIAI 2025, JCT, or bespoke; under `uk-gc`: JCT 2024 SBC/DB, NEC4 ECC, FIDIC, or bespoke). The `contract-risk` skill will load the correct profile-scoped playbook. Scan for non-standard amendments, unusual retention, high liquidated damages, or harsh time bars. Flag top 5 risks.

---

## Step 3 — Generate Outputs

### Part A — The Bid Plan Workbook
Run the bundled `scripts/create_bid_plan.py` helper in this skill's directory to generate the Excel workbook. Invoke it with `python3` and pass:
- `--output "Bid_Plan_[Project].xlsx"`
- `--project "[Name]"`
- `--client "[Client]"`
- `--return-date "YYYY-MM-DD"`
- `--route "[Route]"`

Then use `openpyxl` (via a secondary Python script or direct manipulation) to populate the 9 tabs with the data you extracted in Step 2.

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

Ask: "Would you like me to move to Phase 2 and break this down into trade packages (`/ailtir-cowork-plugin:ailtir_package-breakdown`)?"

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
- [ ] `Context/profile.json` read; downstream skills invoked with the correct `profile_key`.
- [ ] Bid reference follows format YYYY-NNN-ProjectName.
- [ ] Go/No-Go score is based on actual scoring criteria from `references/{profile_key}/go-no-go-criteria.md`, not a guess.
- [ ] All mandatory gates for the active profile explicitly checked (CIRI/Safe-T-Cert/turnover for `ireland-gc`; SSIP/turnover/BSA/Modern Slavery for `uk-gc`).
- [ ] Compliance Matrix captures every evaluation criterion with exact weighting from the ITT.
- [ ] Bid folder created under the workspace root (`AILTIR_PLUGIN_DATA` or `~/Ailtir-Tendering`) at `Bids/[BID]/` with all 9 sections.
- [ ] Bid logged to Notion Bid Pipeline with correct status and return date.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
