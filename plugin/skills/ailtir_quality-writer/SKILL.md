---
name: ailtir_quality-writer
description: Drafts technical method statements, social value (CBC) responses, and self-scores drafts against ITT evaluation descriptors. Triggered by /ailtir-cowork-plugin:ailtir_quality-writer.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Quality Writer

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_quality-writer`
- `plugin_version`: `2.15.3`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are drafting a technical quality response for a tender submission.

## Step 1 — Input Mode (Voice or Text)
Accept input from the user. This may be a detailed text prompt, or a raw voice transcript (e.g., "Site manager's voice note on how we'll do the piling"). If it's a voice note, first clean the transcript into bullet points so the user can verify what you heard before you start drafting.

## Step 2 — Understand the Requirement & Evaluator Preferences
Read the specific evaluation criterion or question from the ITT.
Crucially, ask the user for the **Scoring Band Descriptors** (e.g., what the ITT says is required to score an "Excellent" or "90-100%"). You must draft specifically to hit the top band.

## Step 3 — Apply Win Themes, Case Studies & Social Value (CBC)
Read `references/win-themes.md` and `Context/company.md`. Select the win themes that best answer the specific question.

**CRITICAL: Intelligence Filtering**
Before selecting case studies or method statements from the `Intelligence/` folder, you MUST read the YAML frontmatter of the files first.
1. Scan the frontmatter of all files in `Intelligence/case-studies/`.
2. Filter by matching `sector`, `procurement_route`, and `outcome: Won`.
3. Select the top 2-3 case studies whose `value` (in the same currency as the current bid, per `value_currency` and the active `profile_key`) is closest to the current bid value.
4. Only then read the full content of those selected files to weave into your draft.

**If the question is about Social Value, ESG, or Community Benefit Clauses (CBC):**
- Under `ireland-gc` (Irish CWMF tenders), focus on employment targets, apprenticeships, and local supply chain spend as measured under the CBC guidance.
- Under `uk-gc` (UK Procurement Act 2023 tenders), align with PPN 06/21 (Social Value Model — Themes, Policy Outcomes, MACs) and the Carbon Reduction Plan under PPN 06/20. National TOMs (Themes, Outcomes, Measures) remain common in local authority procurements.
- Extract any existing social value commitments from `Context/company.md` and quantify them in the profile's currency (e.g., "We will deliver X apprenticeship weeks per {{currency-symbol}}1M spend").

## Step 4 — Draft the Response
Draft the response using professional, persuasive, and evidence-backed language. Ensure that:
- The tone is active ("We will...").
- Every sub-clause of the ITT question has a dedicated heading.
- You front-load project-specific context so it does not read like generic boilerplate.

## Step 5 — The Evaluator-Aware Scoring Loop (Self-Correction)
Before presenting the final draft to the user, you must self-score your own draft against the Scoring Band Descriptors from Step 2.
1. Read your draft.
2. Ask: "Does this actually meet the criteria for 'Excellent'?"
3. Identify gaps (e.g., "I claimed we have a good safety record but didn't provide the AFR metric").
4. Revise the draft to close those gaps.

## Step 6 — Present
Provide the final drafted text, followed by a brief "Quality Score Report" explaining why this draft hits the top scoring band and noting any `[HUMAN INPUT REQUIRED]` placeholders where specific metrics or case study names need to be inserted.

## Anti-Patterns (What NOT to do)
- DO NOT use passive voice. Always use active voice ("We will...").
- DO NOT use generic fluff. Use specific proof points.
- DO NOT forget to incorporate at least one win theme.

## Quality Checks
- [ ] Frontmatter filtering applied before selecting case studies.
- [ ] Active voice used throughout ('We will...').
- [ ] Every sub-clause of the ITT question has a dedicated heading.
- [ ] Self-scoring loop completed against the Scoring Band Descriptors.
- [ ] `[HUMAN INPUT REQUIRED]` placeholders inserted for any missing metrics.

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
