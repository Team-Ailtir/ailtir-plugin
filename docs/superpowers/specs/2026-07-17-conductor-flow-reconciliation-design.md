# Conductor & Flow Reconciliation — Design (DRAFT, brainstorm in progress)

**Status:** Design presented, awaiting user confirmation on Sections 2 & 3. NOT yet approved. Not yet a plan.
**Scope decision:** Docs/flow fix now; estimating-workbook fragmentation deferred to a separate spec.
**Constraint:** Contractor OS (`.competitor-reference-quarantine/`) is AUDIT-ONLY — must NOT be read or referenced when designing Ailtir. This design is built from Ailtir's own logic + profile standards only.

---

## Problem

Three documents define the skill flow and they disagree:
- `plugin/README.md` — "Core Workflow" (4 marketing-style phases; skills mis-ordered, some in wrong phase)
- `plugin/PROCESS.md` — onboarding narrative
- `plugin/skills/ailtir_conductor/references/phase-map.md` — what the conductor actually executes

Plus: intelligence-builder placement is ambiguous, and the estimating skills produce fragmented output.

## Decisions locked in

1. **Source of truth = `phase-map.md`.** README + PROCESS.md get rewritten to conform. Add a note at the top of each pointing to phase-map as the authority.
2. **Conductor gains a "show full process" capability** — user can ask "what's the full process?" and the conductor renders phase-map as a human-readable walkthrough. Makes phase-map do double duty (machine routing table + human process doc).
3. **Scope:** docs/flow + the one concrete bug now. Fragmentation captured in a separate deferred spec.
4. **intelligence-builder:** user chose "Setup + post-tender" (see open question — reconcile with the "again at submission" ask).

## Key finding — estimating workflow is fragmented, not broken

Functional (each skill runs, well-styled output) but mechanically fragmented:
- **Four disconnected workbooks:** `takeoff_register.xlsx`, `Package_Register_[Project].xlsx`, `Quote_Comparison_[Package].xlsx`, `estimate.xlsx`. Nothing reads another; estimator re-keys takeoff quantities into the estimate by hand. Estimate's Subcontractor Register overlaps bid-leveling; package data overlaps Package Register.
- The `estimating-workflow` SKILL.md already articulates the "one spine, labelled summaries" principle and warns of the duplication trap — but nothing *enforces* it.
- Styling coherent (Ailtir navy/purple/amber) but achieved two ways: real module sharing (`takeoff` imports `estimating-workflow/scripts/style_excel.py`) vs. copy-pasted palette constants (`package-breakdown`, `bid-leveling`).
- Separate `_xlsx_render.py` `--data`-JSON engine exists but only under bid-side skills (`contract-risk`, `compliance-matrix`, `bid-planner`) — NOT the estimating set.

**Concrete bug (fix now):** `ailtir_takeoff/SKILL.md` calls `excel_output.py takeoff.json -o takeoff_register.xlsx`, but the script requires `--json / --out / --profile` flags (no positional/`-o` support). Runs fail as written.

---

## Design sections (as presented to user)

### Section 1 — Single source of truth
`phase-map.md` canonical. Rewrite PROCESS.md + README "Core Workflow" to match exactly. Add a one-line "phase-map is authoritative" note at top of PROCESS.md and README.

### Section 2 — Corrected estimating sequence  ⚠️ AWAITING CONFIRMATION
Logical order (packages before enquiry/leveling; quotes back before leveling):

| # | Skill | Why here |
|---|-------|----------|
| 1 | `package-breakdown` | Define trade packages — nothing downstream works without them |
| 2 | `takeoff` | Quantities → NRM2 register |
| 3 | `subcontractor-enquiry` | Issue ITTs per package |
| 4 | `prelims-builder` | Priced prelims schedule |
| 5 | `bid-leveling` | Normalise quotes once they return |
| 6 | `cost-reconciliation` | Final gap/benchmark check |

- `estimating-workflow` = alternative orchestrator (not in sequence).
- `rate-library` = support skill (not sequenced).
- **phase-map.md bug:** currently OMITS `package-breakdown` from the estimating list (only mentions in a note it "belongs to estimating"). Add it as step 1.
- README's ESTIMATE&PRICE / ENQUIRE&PROCURE split is acceptable human grouping, but skills inside are mis-ordered and some (pqq-manager, rfi-generator, post-tender-interview) are in the wrong phase entirely. Re-derive all of it from phase-map.

### Section 3 — intelligence-builder placement  ⚠️ AWAITING CONFIRMATION
User picked "Setup + post-tender" but opening ask also said "again at submission." Proposed reconciliation:
- **Setup (seed):** keep Step 7 nudge, make it firmer — explicit recommended action after setup, so quality-writer has material from day one.
- **Post-tender (capture):** case-study-generator already feeds it; phase-map documents this as the capture point.
- **Submission (the "again"):** NOT a hard sequence step — conductor nudges intelligence-builder at start of submission phase ONLY IF `Intelligence/` is thin (quality-writer reads from it there).
- Stays under Cross-Cutting Support in catalogue (genuinely cross-phase), but phase-map "Skill Availability Notes" updated so conductor surfaces it at those moments.
- **OPEN:** soft submission nudge (proposed) vs. hard step in submission sequence?

### Section 4 — "Show the full process" in conductor
New action: user asks "what's the full process?" / picks a **"Show full process"** card → conductor renders phase-map as readable human-facing walkthrough (phases in order, skills per phase, one line each). Add a step (likely Step 0.5 or branch in Step 5) + a `conductor: show process` action.

### Section 5 — The one real bug + deferred spec
- **Fix now:** takeoff SKILL.md `excel_output.py` flag mismatch (`-o` → `--json/--out/--profile`).
- **Defer:** four-disconnected-workbooks fragmentation → separate standalone spec (one-spine consolidation). No scripts rewritten in this piece of work.

---

## Files in play

- `plugin/skills/ailtir_conductor/SKILL.md` — add show-process action
- `plugin/skills/ailtir_conductor/references/phase-map.md` — canonical; add package-breakdown to estimating, fix intel-builder notes
- `plugin/skills/ailtir_conductor/references/skill-catalogue.md` — the file user had open; keep intel-builder under Cross-Cutting
- `plugin/PROCESS.md` — rewrite to match phase-map
- `plugin/README.md` — rewrite Core Workflow to match phase-map
- `plugin/skills/ailtir_setup/SKILL.md` — firm up Step 7 intel-builder nudge
- `plugin/skills/ailtir_takeoff/SKILL.md` — fix excel_output.py invocation

## Next steps when resuming

1. Get user confirmation on Section 2 (estimating order) and Section 3 (soft nudge vs hard step).
2. Finish brainstorm → write final spec (this file) → user reviews → invoke writing-plans.
3. Separately: write the deferred estimating-fragmentation spec.
