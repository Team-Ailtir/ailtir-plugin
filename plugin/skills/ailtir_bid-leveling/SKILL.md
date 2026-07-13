---
name: ailtir_bid-leveling
description: Phase 2 skill. Compares received subcontractor quotes for a specific trade package. Normalises pricing, scopes, and exclusions into a multi-tab Excel comparison. Triggered by /ailtir-cowork-plugin:ailtir_bid-leveling.
---

# Ailtir — Bid Leveling (Quote Analysis)

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_bid-leveling`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are a Commercial Manager leveling subcontractor quotes.

## Step 1 — Extract Base Data

Read all uploaded quotes for the package.
Extract from each:
- Subcontractor name
- Headline price
- Line item breakdown (if provided)
- Explicit inclusions
- Explicit exclusions
- Qualifications / assumptions
- Commercial terms (validity period, payment terms, retention)

## Step 2 — Scope Normalisation Protocol (Critical)

Subcontractor quotes rarely cover the exact same scope. You must perform a formal scope normalisation before comparing prices.

1. **Extract the Baseline Scope:** Read the ITT trade package specification (or the BOQ lines for this trade). This is the 100% scope baseline.
2. **Map Quotes to Baseline:** Map every line item and inclusion from each quote against the baseline.
3. **Identify Gaps (Missing Scope):** Identify items in the baseline that a subcontractor has excluded or failed to price.
4. **Identify Overlaps (Double-Counting):** Identify items a subcontractor has priced that belong to a different trade package (e.g., the mechanical sub pricing builder's work in connection, which the main contractor will do).
5. **Apply Normalisation Plugs:** 
   - For missing scope: Add a "plug" cost to that subcontractor's total to make them 100% compliant. Use the highest price quoted by another sub for that item, or flag it as `[REQUIRES ESTIMATOR PLUG]`.
   - For overlaps: Deduct the value of the overlapping item from their total.

*The goal is a Like-for-Like (LFL) Adjusted Total, which is often completely different from the headline price.*

## Step 3 — Generate Comparison

Run the bundled `scripts/create_comparison.py` helper in this skill's directory to generate the Comparison Excel workbook. Invoke it with `python3` and pass:
- `--output "Quote_Comparison_[Package].xlsx"`
- `--package "[Package Name]"`

- [HUMAN INPUT REQUIRED] If a plug value for missing scope cannot be estimated from other quotes, flag it as `[REQUIRES ESTIMATOR PLUG]` and ask the user.

## Anti-Patterns (What NOT to do)
- DO NOT run the Python script without replacing `[Package Name]` with the actual package name.
- DO NOT ignore exclusions. They must be explicitly highlighted.
- DO NOT hallucinate plug values. Note them as estimates if they are not explicitly provided in the quotes.

Populate the workbook:
1. **Executive Summary:** Headline totals, variance from lowest, variance from budget.
2. **Commercial Comparison:** Side-by-side matrix of terms, validity, and exclusions.
3. **Like-for-Like Normalisation:** The mathematical leveling, adding plug numbers for missing scope.

## Step 3 — Present

Provide the Excel workbook. Summarise the findings: who is genuinely cheapest once exclusions are factored in, and what the key commercial risks are.

## Quality Checks
- [ ] Scope normalisation performed — every quote mapped against the baseline scope.
- [ ] Gaps (missing scope) identified and plug costs applied or flagged.
- [ ] Like-for-Like Adjusted Total calculated for every subcontractor.
- [ ] Executive Summary clearly identifies who is genuinely cheapest on an adjusted basis.

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

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
