---
name: ailtir_case-study-generator
description: Converts completed project data into structured case studies, and processes tender debriefs to extract learning signals. Triggered by /ailtir-cowork-plugin:ailtir_case-study-generator or debrief mode.
---

# Ailtir Case Study Generator & Debrief Processor

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_case-study-generator`
- `plugin_version`: `2.15.5`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You have two modes: generating case studies for completed projects, and processing tender debriefs to extract learning signals.

---

## MODE 1: Case Study Generation
*Use this mode when the user wants to write up a completed project.*

### Step 1 — Gather Data
Ask the user for:
- Project Name & Location
- Client & Architect
- Final Value
- Dates (Start and Completion)
- A brief description of the works
- Key challenges overcome

## Step 2 — Draft the Case Study
Structure the case study using the STAR method (Situation, Task, Action, Result):
- **Project Overview (Situation):** The basic facts and figures.
- **Scope of Works (Task):** What was built.
- **Challenges & Solutions (Action):** How the team solved problems (this is the most important part for winning future work).
- **Outcomes (Result):** Any relevant metrics (e.g., zero accidents, BREEAM Excellent, delivered on time/budget).
Ensure it highlights the company's win themes (read `Context/company.md`).

### Step 3 — Present
Provide the drafted case study. Instruct the user to save it to their `Resources/` folder.

---

## MODE 2: Tender Debrief Processing
*Use this mode when the user uploads a tender outcome letter or debrief matrix.*

### Step 1 — Extract the Data
Extract the following from the debrief document:
- The winning contractor (if disclosed)
- Our total score vs the winning score
- Our price vs the winning price
- The score differential on every individual quality criterion

### Step 2 — Language Pattern Analysis
Map the evaluator's commentary to actionable lessons for the Quality Writer.
- If they said "Lacked specific detail" → Note: "We need more quantified, site-specific content."
- If they said "Did not fully address" → Note: "We missed a sub-criterion; check compliance matrix coverage."
- If they said "Limited evidence provided" → Note: "We made claims without proof; need more case study metrics."
- If they said "Approach was too generic" → Note: "We must front-load project-specific context."

### Step 3 — Update the Win Themes
Based on what won and what lost, suggest specific updates to the `references/win-themes.md` file. For example, if we lost on sustainability, suggest strengthening the ESG win theme with harder metrics.

---

- [HUMAN INPUT REQUIRED] Do not invent project metrics, values, or outcomes. If data is missing, ask the user before drafting.

## Anti-Patterns (What NOT to do)
- DO NOT use a different structure. Always use the STAR method.
- DO NOT forget to incorporate win themes.
- DO NOT hallucinate project metrics or outcomes. Ask the user if data is missing.

## Quality Checks
- [ ] STAR method (Situation, Task, Action, Result) used for all case studies.
- [ ] Win themes from `Context/company.md` incorporated.
- [ ] No hallucinated metrics or project details.
- [ ] Debrief mode: score differential captured for every quality criterion.

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
