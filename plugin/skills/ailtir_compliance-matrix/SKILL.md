---
name: ailtir_compliance-matrix
description: Extracts all ITT requirements into a tracked deliverables matrix. Triggered by /ailtir-cowork-plugin:ailtir_compliance-matrix or when bid-planner runs.
---

# Ailtir Compliance Matrix Builder

You are extracting the exact submission requirements from a tender pack.

## Step 1 — Extract Requirements
Scan the ITT (Instruction to Tenderers) and any Returnable Schedules.
Extract:
- Every evaluation criterion and its weighting.
- Every mandatory returnable document (e.g., Form of Tender, Pricing Schedule, Programme).
- Page limits, formatting rules, and submission methods (e.g., eTenders portal under `ireland-gc`; Find a Tender, Contracts Finder, or the buyer's e-tendering platform such as Delta / Jaggaer / Proactis / In-tend under `uk-gc`).

## Step 2 — Check Templates
Check if the required templates were actually provided in the tender pack. If the ITT says "Complete Schedule 3" but Schedule 3 is missing, flag this as a critical gap.

## Step 3 — Present
Provide a clear, structured list of requirements.
If called by the `bid-planner`, return the data to the orchestrator to populate the Excel tab. If called directly, present it to the user.

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
