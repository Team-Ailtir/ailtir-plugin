---
name: ailtir_compliance-matrix
description: Extracts all ITT requirements into a tracked deliverables matrix. Triggered by /ailtir_compliance-matrix or when bid-planner runs.
---

# Ailtir Compliance Matrix Builder

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_compliance-matrix`
- `plugin_version`: `2.16.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are extracting the exact submission requirements from a tender pack.

## Step 1 — Extract Requirements
Scan the ITT (Instruction to Tenderers) and any Returnable Schedules.
Extract:
- Every evaluation criterion and its weighting.
- Every mandatory returnable document (e.g., Form of Tender, Pricing Schedule, Programme).
- Page limits, formatting rules, and submission methods (e.g., eTenders portal under `ireland-gc`; Find a Tender, Contracts Finder, or the buyer's e-tendering platform such as Delta / Jaggaer / Proactis / In-tend under `uk-gc`).

## Step 2 — Check Templates
Check if the required templates were actually provided in the tender pack. If the ITT says "Complete Schedule 3" but Schedule 3 is missing, flag this as a critical gap.

## Step 3 — Generate the Workbook
This is the deep-dive pass. Assemble your extracted analysis into a JSON payload
and run the bundled `scripts/create_compliance_matrix.py` with `python3` — the
script owns all tab structure and styling; you supply the rows:

`python3 scripts/create_compliance_matrix.py --output "Compliance_Matrix_[Bid].xlsx" --data /tmp/compliance_data.json`

Payload shape (each `rows` is a list of row-arrays matching the tab's columns):

```json
{
  "cover": {"Project": "X", "ITT Ref": "ITT-W2", "Submission": "28/02 16:00"},
  "tabs": {
    "award_criterion": {"rows": [["AC-1","Lowest cost","100%","Price only","Price only"]]},
    "returnables": {"rows": [["1","Vol B","Form of Tender","Contract Doc","YES","To Do","Director","Complete all blanks"]]},
    "submission_rules": {"rows": [["SUBMISSION METHOD","eTenders only"]]},
    "gap_check": {"rows": [["Doc 7","QW Part 1","RETURN","YES","Complete fully"]]}
  }
}
```

This writes its OWN workbook — never the bid-planner file. If a section does not
apply, pass `"rows": []` with a `"na_note"`.

- [HUMAN INPUT REQUIRED] If the submission method or deadline is not stated in the ITT, ask the user before finalising the matrix.

## Anti-Patterns (What NOT to do)
- DO NOT miss mandatory returnables. Scan the entire ITT.
- DO NOT hallucinate deadlines or weightings. Use exact figures from the ITT.
- DO NOT guess the submission method if it is not stated; flag it as a question.

## Quality Checks
- [ ] Every evaluation criterion captured with exact weighting.
- [ ] Missing templates explicitly flagged.
- [ ] Submission method and deadline captured.

## On Completion — Update Bid State

When this skill finishes for a specific bid, update the bid's state file so `ailtir_conductor` and `ailtir_dashboard` reflect the progress. Run the sibling `ailtir_conductor` skill's `scripts/update_frontmatter.py` helper with `python3`:

This deep dive **upgrades** the bid-planner's `summarised` entry to a full
`proceed`. Use `--result proceed`.

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
