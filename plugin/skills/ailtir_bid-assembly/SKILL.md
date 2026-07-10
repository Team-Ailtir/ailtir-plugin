---
name: ailtir_bid-assembly
description: Compiles the final submission documents. Triggered by /ailtir-cowork-plugin:ailtir_bid-assembly.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Bid Assembly

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_bid-assembly`
- `plugin_version`: `2.15.3`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are compiling the final tender submission.

## Step 1 — Reconciliation Check
Before assembly, perform a final reconciliation check:
- Cross-check all ITT requirements against the priced schedule and drafted responses.
- Identify any gaps or overlaps.
- Verify arithmetic in the pricing schedule (if provided).
- Flag any missing items to the user.

## Step 2 — Check Requirements
Read the Compliance Matrix (or the Submission Requirements tab in the Bid Plan Workbook).

## Step 3 — Gather Documents
Gather all drafted responses, completed forms, and pricing schedules.

## Step 4 — Compile
Combine the text into a single master Markdown document, structured exactly as required by the ITT.
- Add a professional title page.
- Create a clear Table of Contents.
- Insert each response under the correct heading, matching the ITT structure exactly.
- Read `Context/company.md` to ensure the company name and details are correct on the title page.
Add placeholders for any external PDFs (e.g., `[INSERT INSURANCE CERTIFICATE HERE]`).

## Step 5 — Present
Provide the master Markdown document. Instruct the user to export it to PDF or copy it into their DTP software (e.g., InDesign).

- [HUMAN INPUT REQUIRED] Before compiling, confirm with the user that all drafted responses have been reviewed and approved.

## Anti-Patterns (What NOT to do)
- DO NOT change the structure from what the ITT requires.
- DO NOT forget to include placeholders for external PDFs.
- DO NOT hallucinate company details on the title page. Read `Context/company.md`.

## Quality Checks
- [ ] All mandatory returnables from the Compliance Matrix are included.
- [ ] Title page uses company name from `Context/company.md` — no hallucinated details.
- [ ] Placeholders `[INSERT ...]` added for all external PDFs (insurance certs, etc.).
- [ ] Structure matches the ITT section order exactly.

## On Completion — Update Bid State

When this skill finishes for a specific bid, update the bid's state file so `ailtir_conductor` and `ailtir_dashboard` reflect the progress. Run the sibling `ailtir_conductor` skill's `scripts/update_frontmatter.py` helper with `python3`:

```
python3 <ailtir_conductor>/scripts/update_frontmatter.py \
    --bid-path Bids/<BID> \
    --complete <this skill's folder name> \
    --result proceed
```

Substitute `<BID>` for the bid folder name (e.g. `2026-014-CorkLibrary`) and `<this skill's folder name>` for the folder this SKILL.md lives in (e.g. `ailtir_project-indexer`). Use `--result skipped` and `--reason "..."` if the user asked to skip rather than complete.

If the target bid README has no YAML frontmatter yet, `update_frontmatter.py` will exit with code 3. In that case, run `scripts/init_bid_frontmatter.py` from the same sibling skill first, then retry the update.

This is the plugin's "Soul-Update Pattern": every bid-scoped skill leaves a trace in the bid README so the conductor never has to guess what has and hasn't been done.

## On Completion — Recommend the Next Step

After the frontmatter has been updated, help the user by naming what comes next — do not make them re-invoke `ailtir_conductor` just to see it.

Read `references/phase-map.md` from the sibling `ailtir_conductor` skill's directory. Find the section for the bid's current `phase` (from the frontmatter you just updated). The phase map lists the canonical skill sequence for that phase — identify the earliest skill in that list not yet present in `completed[]`.

Then print exactly this block at the very end of your response:

```text
Next up on {bid_id} ({phase} phase):
  → /ailtir-cowork-plugin:{next_skill} — {one-line rationale from the phase map}

Or run /ailtir-cowork-plugin:ailtir_conductor for a full cross-bid view.
```

Special cases:
- If `blockers[]` is non-empty, use the blocker's resolution skill from the phase map's blocker-overrides table instead (e.g. `ailtir_rfi-generator` for `type: rfi`) and lead with "Blocked — resolve first:".
- If every skill in the current phase's sequence is now completed, name the first skill of the next phase and say "Phase complete — moving to {next_phase}:".
- If the bid has reached `closed` or `delivery` with no obvious next step, print "No canonical next step — run `/ailtir-cowork-plugin:ailtir_conductor` to see the full pipeline." instead of a specific recommendation.
