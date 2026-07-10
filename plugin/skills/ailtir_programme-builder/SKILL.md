---
name: ailtir_programme-builder
description: Generates a tender programme (Gantt schedule) and narrative. Adapts phrasing to the active Ailtir profile — CWMF requirements for Ireland, Procurement Act 2023 / JCT / NEC4 requirements for UK. Triggered by /ailtir-cowork-plugin:ailtir_programme-builder or when the user asks for a project schedule.
---

# Ailtir Programme Builder

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_programme-builder`
- `plugin_version`: `2.15.1`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are creating a tender programme (schedule) and accompanying narrative. Under `ireland-gc` this satisfies CWMF requirements for Irish public works tenders. Under `uk-gc` this satisfies typical JCT / NEC4 tender programme requirements — for NEC4 the Contractor's programme becomes the Accepted Programme under clause 31/32 once approved, so make sure the WBS supports subsequent Compensation Event assessment.

## Step 1 — Gather Project Parameters
Ask the user for:
1. **Start Date:**
2. **Required Completion Date / Duration:**
3. **Key Milestones:** (e.g., watertight, sectional handovers)
4. **Main Scope Elements:** (e.g., earthworks, steel frame, fit-out)

## Step 2 — Develop the Work Breakdown Structure (WBS)
Create a logical construction sequence:
1. Pre-construction & Mobilisation
2. Substructure / Groundworks
3. Superstructure (Frame, Floors, Roof)
4. Envelope / Watertight
5. MEP First Fix
6. Internal Partitions & Plastering
7. MEP Second Fix
8. Finishes (Floors, Ceilings, Joinery)
9. Commissioning & Snagging
10. Handover

## Step 3 — Generate the Programme Data
Create a table with: Task Name, Predecessor, Duration (Days), Start Date, End Date.
Ensure the critical path is logical (e.g., you cannot start first fix until the roof is on).

## Step 4 — Write the Programme Narrative
Most tenders (CWMF under `ireland-gc`; JCT/NEC4 under `uk-gc`) require a written narrative explaining the programme. Draft a 1-page document covering:
- **Overall Strategy:** How the project will be phased.
- **Critical Path:** Identification of the driving activities.
- **Risk Mitigation:** Weather allowances, long-lead procurement (e.g., switchgear, AHUs).
- **Resourcing:** Peak labour periods.

## Step 5 — Output
Provide the WBS table and the narrative. Offer to write the WBS data to a CSV file (`tender_programme.csv`) so the user can import it into Asta Powerproject or MS Project.

## Anti-Patterns (What NOT to do)
- DO NOT create unrealistic overlapping tasks (e.g., painting while pouring concrete floors).
- DO NOT ignore the commissioning period — always allow 2-4 weeks at the end for testing and snagging.
- DO NOT use US date formats (MM/DD/YYYY). Both supported profiles use DD/MM/YYYY.
- [HUMAN INPUT REQUIRED] Do not assume standard durations for complex elements like deep basements or specialist facades; ask the user if they have specific durations in mind.

## Quality Checks
- [ ] Critical path is logical — no impossible overlaps.
- [ ] Commissioning period included (minimum 2-4 weeks).
- [ ] DD/MM/YYYY date format used throughout.
- [ ] Written programme narrative covers overall strategy, critical path, and risk mitigation.

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
