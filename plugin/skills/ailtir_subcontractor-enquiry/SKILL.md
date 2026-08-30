---
name: ailtir_subcontractor-enquiry
description: Prepares subcontractor enquiry packs based on the package breakdown. Triggered by /ailtir_subcontractor-enquiry.
---

# Ailtir Subcontractor Enquiry Prep

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_subcontractor-enquiry`
- `plugin_version`: `2.17.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are preparing the formal enquiry packages to send to subcontractors.

## Step 1 — Gather Details
Ask the user:
- Which trade package are we sending out?
- What is the return date for the quotes?

## Step 2 — Draft the ITT Letter
Draft the Invitation to Tender (ITT) letter for the subcontractor.
Include:
- Project overview.
- Scope of works (reference the specific spec sections and drawings from the Package Register).
- Return date and instructions.
- Head Contract flow-downs (e.g., retention, DLP, insurances required).

## Step 3 — Compile the Pack
Instruct the user to create a ZIP file containing:
- The drafted ITT Letter.
- The relevant drawings and specs.
- The Pricing Schedule (if a BOQ is provided).

## Step 4 — Present
Provide the drafted ITT letter.

- [HUMAN INPUT REQUIRED] Confirm the return date and scope with the user before drafting the ITT letter.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate the return date. Ask the user.
- DO NOT guess the scope. Reference the specific spec sections and drawings from the Package Register.
- DO NOT forget to include the Head Contract flow-downs.

## Quality Checks
- [ ] ITT letter references the correct spec sections and drawing series.
- [ ] Head contract flow-downs (retention, DLP, insurances) included.
- [ ] Return date and instructions clearly stated.

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
