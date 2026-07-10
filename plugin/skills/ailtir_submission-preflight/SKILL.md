---
name: ailtir_submission-preflight
description: Runs final deterministic compliance checks before submission, targeting the portal appropriate to the active Ailtir profile (Irish eTenders or UK Find a Tender / Contracts Finder). Triggered by /ailtir-cowork-plugin:ailtir_submission-preflight.
---

# Ailtir Submission Pre-Flight

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_submission-preflight`
- `plugin_version`: `2.15.1`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are running the final checks before the bid is submitted to the contracting authority.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir-cowork-plugin:ailtir_setup`. The portal-specific checks in Step 4 depend on `profile_key`.

## Step 2 — Review the Master Document
Read the assembled master submission document.

## Step 3 — Check against ITT
Cross-reference against the Compliance Matrix.
Check:
- Are all mandatory forms included?
- Are word/page limits respected?
- Is the naming convention correct?
- Are there any blank placeholders (e.g., `[TBC]`, `[INSERT HERE]`, `[HUMAN INPUT REQUIRED]`)?
- Are all signatures and dates present where required?
- **Under `uk-gc`, central government contracts:** is the Carbon Reduction Plan (PPN 06/20) attached where required? Is the Social Value response (PPN 06/21) present and addressing the specified MACs? Is the Modern Slavery statement referenced?

## Step 4 — Temporal Consistency Check (The "Stale Output" Check)
This is a critical risk check. During the tender period, the authority often issues Q&A answers or Addenda that change the scope or specification.
Ask the user: "Were any Q&A answers or Addenda received during this tender?"
If yes, check the timestamps/dates of the final bid documents.
- If a method statement or pricing document was finalised *before* a relevant Q&A answer was received, flag it as a **STALE OUTPUT RISK**.
- Example: "Warning: The Mechanical Method Statement was drafted on Tuesday, but Q&A #4 (which changed the HVAC spec) was received on Thursday. Has this document been updated?"

## Step 5 — Portal Checklist

**Under `ireland-gc` — eTenders Ireland:**
- [ ] Are any single files over the 2.14 GB eTenders limit?
- [ ] Is the Form of Tender signed and dated?
- [ ] Are all files named exactly as requested in the ITT?
- [ ] Is there sufficient time before the deadline (typically 12:00 noon or 17:00 Irish time)? Do not upload at the last minute.

**Under `uk-gc` — Find a Tender / Contracts Finder / Constructionline / private portal:**
- [ ] Are any single files over the portal's per-file limit? (Find a Tender allows up to 50 MB per file by default; check the notice for the specific configuration.)
- [ ] Is the Form of Tender / Certificate of Bona Fide Tender signed and dated?
- [ ] Are all files named exactly as requested in the ITT? Note that UK ITTs often prescribe a strict naming convention including bid reference and section number.
- [ ] Under Procurement Act 2023: has the tender response been submitted via the buyer's e-tendering platform (Delta, Jaggaer, Proactis, In-tend, or Bravo Solutions are the common ones)?
- [ ] Are Carbon Reduction Plan and Social Value / Modern Slavery attachments included where required?
- [ ] Is there sufficient time before the deadline (UK deadlines are commonly 12:00 or 17:00 UK time — check the notice)? Do not upload at the last minute.

## Step 6 — Present
Provide a Pass/Fail report. If there are any fails, flag them prominently in RED so the user can fix them before uploading.

## Anti-Patterns (What NOT to do)
- DO NOT approve the submission if there are RED ALERTS.
- DO NOT skip checking word/page limits if they were specified in the ITT.
- DO NOT ignore missing signatures or dates.
- DO NOT apply Irish portal limits to a UK submission or vice versa.

## Quality Checks
- [ ] `Context/profile.json` read; correct portal checklist applied.
- [ ] All mandatory returnables from the Compliance Matrix present.
- [ ] No blank placeholders (`[TBC]`, `[INSERT HERE]`) remaining.
- [ ] Stale output check completed — documents post-date all Q&A answers.
- [ ] Portal-specific file-size and naming checks completed for the active profile.
- [ ] Under `uk-gc` central government: CRP, Social Value, and Modern Slavery attachments confirmed where required.

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
