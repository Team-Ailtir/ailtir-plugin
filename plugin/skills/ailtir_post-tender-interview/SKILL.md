---
name: ailtir_post-tender-interview
description: Prepares the contractor team for a post-tender interview (CWMF interview under `ireland-gc`; UK public/private post-submission clarification interview under `uk-gc`). Generates presentation outlines, Q&A prep, and key talking points. Triggered by /ailtir-cowork-plugin:ailtir_post-tender-interview or when the user asks to prep for a tender interview.
---

# Ailtir Post-Tender Interview Prep

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_post-tender-interview`
- `plugin_version`: `2.15.2`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are preparing a contractor's bid team for a post-tender interview with a public-sector or private client. These interviews are critical for securing the contract and focus heavily on risk, programme, and team capability. Read `Context/profile.json` and adapt terminology and accreditation references to the active profile — CIRI / Safe-T-Cert / PW-CF terminology under `ireland-gc`; SSIP / Building Safety Act / JCT-or-NEC4 terminology under `uk-gc`.

## Step 1 — Gather Interview Details
Ask the user for:
1. **Client & Project:**
2. **Interview Format:** (e.g., 20 min presentation, 30 min Q&A)
3. **Attendees:** Who is attending from the contractor's side? (e.g., Contracts Director, Project Manager, Site Manager)
4. **Key Bid Weaknesses:** What are the known weak spots in the submitted tender?

## Step 2 — Draft the Presentation Outline
Create a slide-by-slide outline tailored to the time limit.
Standard structure:
1. **Introduction:** The team and our commitment to the project.
2. **Project Understanding:** Key challenges and our strategy to solve them.
3. **Programme & Phasing:** The critical path and how we guarantee the handover date.
4. **Supply Chain & Resources:** Local delivery, key subcontractors, and profile-appropriate accreditation compliance (CIRI/Safe-T-Cert under `ireland-gc`; SSIP/Constructionline/BSA competency under `uk-gc`).
5. **Quality & Safety:** Safety accreditation approach and zero-harm culture (Safe-T-Cert under `ireland-gc`; SSIP + CDM 2015 under `uk-gc`).
6. **Summary:** Why we are the safest choice.

## Step 3 — Develop the Q&A Prep Sheet
Anticipate the tough questions the client's design team (Architect, QS) will ask, and script the ideal responses.
Focus on:
- "How will you manage the interface with the live hospital/school?"
- "Your prelims seem low. How are you adequately resourcing this?"
- "What happens if the steel frame is delayed?"
- "Explain your process for managing variations under the active contract form" (Change Orders under PW-CF for `ireland-gc`; Compensation Events under NEC4 or Variations under JCT for `uk-gc`).

## Step 4 — Assign Roles
Advise the user on who should answer what. The Project Manager should answer programme/site questions; the Contracts Director should answer commercial/contract questions.

## Step 5 — Output
Provide the complete prep pack. Offer to generate a Markdown file (`interview_prep.md`) that the team can print and study.

## Anti-Patterns (What NOT to do)
- DO NOT script the presentation word-for-word. Construction professionals speak best from bullet points.
- DO NOT ignore the commercial questions. The client's QS *will* ask about rates and prelims.
- DO NOT use generic advice like "dress professionally". Focus on the technical and commercial content.
- [HUMAN INPUT REQUIRED] You must ask the user for the specific roles of the team members attending, so you can tailor the Q&A assignments correctly.

## Quality Checks
- [ ] Presentation structure matches the ITT interview brief.
- [ ] Q&A prep covers the most likely evaluator questions for this sector.
- [ ] Win themes from `Context/company.md` woven into the narrative.

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
