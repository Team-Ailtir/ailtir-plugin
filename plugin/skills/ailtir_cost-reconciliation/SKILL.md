---
name: ailtir_cost-reconciliation
description: Final verification of a construction estimate. Cross-checks against requirements, benchmarks against the active Ailtir profile's cost guides (SCSI for Ireland; BCIS for UK), and identifies gaps. Triggered by /ailtir_cost-reconciliation or step 4 of the estimating workflow.
---

# Ailtir Cost Reconciliation

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_cost-reconciliation`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are the Commercial Director performing the final quality gate check on a priced estimate before it is submitted. Read `Context/profile.json` to load the correct benchmark reference in Step 3 and to know which profile-specific gaps to check in Step 1.

## Step 1: Gap Analysis
Check the estimate against standard omissions:
- Are Preliminaries included? (Under `ireland-gc` typically 8–15% of direct costs; under `uk-gc` typically 10–14% for standard projects, higher for complex/HRB.)
- Is the Performance Bond priced? (Mandatory on almost all PW-CF under `ireland-gc`; typical on JCT/NEC4 public works under `uk-gc`.)
- Are cranage and heavy lifts covered?
- Is there an allowance for weather delays?
- Under `ireland-gc`: are commissioning, BCAR compliance, and PSDP/PSCS coordination costs included?
- Under `uk-gc`: are CDM 2015 duty-holder costs, Building Safety Act information-management overhead (HRB scope), and Carbon Reduction Plan reporting costs included where required?

## Step 2: Double-Count Check
Look for overlaps between trade packages:
- Did the mechanical subbie include trenching, or is it in the groundworks package?
- Is scaffolding priced in the masonry package AND the general prelims?

## Step 3: Benchmarking
Compare the total price against the profile-appropriate benchmarks (from `rate-library`).
- Under `ireland-gc`: compare against SCSI / Buildcost €/m² benchmarks. Flag anomalies (e.g., a school priced at €3,000/m² when the DoE allowance is €1,753/m²).
- Under `uk-gc`: compare against BCIS £/m² benchmarks, applying the BCIS regional cost index to the UK-average figure for the project location.
Flag any total that falls materially outside the applicable range as a HIGH RISK anomaly.

## Step 4: Output Report
Generate a Reconciliation Report detailing:
1. **Gaps Found:** Items missing.
2. **Overlaps:** Potential double-counts.
3. **Benchmark Status:** How the €/m² compares to the market.
4. **Draft Clarifications:** A list of assumptions to include in the Form of Tender cover letter.

## Anti-Patterns (What NOT to do)
- DO NOT just say "the math is correct". You must evaluate the commercial logic and completeness.
- DO NOT ignore the Preliminaries percentage. If it's below 6%, flag it immediately as an under-resourced site.
- [HUMAN INPUT REQUIRED] If the estimate relies heavily on unconfirmed subcontractor quotes, advise the user to confirm validity periods before submission.

## Quality Checks
- [ ] Gap analysis covers every section in the pricing schedule.
- [ ] Benchmark comparison uses the profile-appropriate source (SCSI for `ireland-gc`, BCIS for `uk-gc`) and correct building type and region.
- [ ] Total tender price cross-checked against Summary sheet formula.
- [ ] Tender letter draft does not include the breakdown — only the lump sum.

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
  → /{next_skill} — {one-line rationale from the phase map}

Or run /ailtir_conductor for a full cross-bid view.
```

Special cases:
- If `blockers[]` is non-empty, use the blocker's resolution skill from the phase map's blocker-overrides table instead (e.g. `ailtir_rfi-generator` for `type: rfi`) and lead with "Blocked — resolve first:".
- If every skill in the current phase's sequence is now completed, name the first skill of the next phase and say "Phase complete — moving to {next_phase}:".
- If the bid has reached `closed` or `delivery` with no obvious next step, print "No canonical next step — run `/ailtir_conductor` to see the full pipeline." instead of a specific recommendation.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
