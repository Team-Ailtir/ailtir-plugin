---
name: ailtir_prelims-builder
description: Builds a priced Schedule of Preliminaries using the measurement structure of the active Ailtir profile (Irish ARM4 for PW-CF, UK NRM1 for JCT/NEC4). Triggered by /ailtir_prelims-builder or when the user asks to price prelims.
---

# Ailtir Prelims Builder

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_prelims-builder`
- `plugin_version`: `2.17.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are building a Schedule of Preliminaries for a construction tender. Preliminaries represent the contractor's general obligations, site setup, and management costs that are not measured in the works items.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir_setup`. The measurement structure, rates library, currency, and typical clause references depend on `profile_key`:

- `ireland-gc` → ARM4 (Agreed Rules of Measurement) structure. Currency Euro (€). Rates from `rate-library/references/ireland-gc/rates-2026.md`.
- `uk-gc` → NRM1 (New Rules of Measurement — Order of Cost Estimating and Cost Planning for Capital Building Works) structure. Currency pound sterling (£). Rates from `rate-library/references/uk-gc/rates-2026.md`.

## Step 2 — Gather Project Context
Ask the user for:
1. **Contract Duration:** (e.g., 52 weeks)
2. **Estimated Contract Value**
3. **Contract Form:** Under `ireland-gc` — PW-CF1 to PW-CF5 or RIAI 2025. Under `uk-gc` — JCT SBC/Q 2024, JCT DB 2024, NEC4 ECC (specify Option), or bespoke.
4. **Site Constraints:** (e.g., restricted city centre, greenfield, HRB scope on `uk-gc`)

## Step 3 — Draft the Prelims Schedule

Draft a schedule covering the following categories, using the structure appropriate to the active profile:

- **Management & Staff:** Contract/Project Manager, Site Manager, Engineer, Quantity Surveyor, Safety Officer (calculate duration × weekly rate).
- **Site Establishment:** Cabins, welfare facilities (per CDM 2015 Schedule 2 for `uk-gc`; per Safety, Health and Welfare at Work (Construction) Regulations for `ireland-gc`), hoarding/fencing, temporary roads.
- **Temporary Services:** Temporary power, water, telecoms, waste management.
- **Plant & Equipment:** Tower cranes, teleporters, scaffolding (general).
- **Contractual & Insurances:**
  - Under `ireland-gc`: CAR insurance, EL/PL insurance, Performance Bond (typically 10% of contract value at ~1–2% cost), BCAR compliance overhead.
  - Under `uk-gc`: Contract Works (CAR) insurance, EL insurance (£10m+), PL insurance (£10m+), PI insurance (where D&B), Performance Bond (typically 10% at 0.5–1.5% cost), Building Safety Act information-management overhead where HRB.
- **Health, Safety & Environmental:** PPE, signage, traffic management, dust/noise control.
  - Under `ireland-gc`: PSDP/PSCS coordination costs.
  - Under `uk-gc`: CDM 2015 Principal Designer / Principal Contractor duties, Site Waste Management Plan compliance.

## Step 4 — Apply Standard Rates
Use rates from the profile-appropriate `rate-library` reference file. Under `ireland-gc` this is SEO/Buildcost; under `uk-gc` this is CIJC/BCIS. Do not mix.

## Step 5 — Generate the Output
Present the prelims schedule as a detailed Markdown table with columns: Item, Description, Unit, Qty, Rate, Amount. Rate and Amount columns must be in the profile's currency.
Ask the user if they want to export this to Excel. If yes, use a Python script with `pandas` to write the table to `prelims_schedule.xlsx`.

## Anti-Patterns (What NOT to do)
- DO NOT use US terminology (e.g., "General Conditions", "Trailer"). Use UK/Irish terms (Preliminaries, Welfare Cabin).
- DO NOT lump all staff costs into a single percentage. Prelims must be built up from first principles (time × rate).
- DO NOT forget the Performance Bond cost — this is mandatory on almost all PW-CF (Ireland) and typical on JCT/NEC4 public works (UK).
- DO NOT apply the wrong currency or the wrong measurement structure for the active profile.
- [HUMAN INPUT REQUIRED] Do not guess the contract duration if it is not provided. You must ask the user.

## Quality Checks
- [ ] `Context/profile.json` read; correct measurement structure (ARM4 for Ireland, NRM1 for UK) and rate library selected.
- [ ] Profile-appropriate management rates applied (SEO for Ireland, CIJC-derived for UK).
- [ ] Performance bond percentage matches ITT requirement (typically 10% of contract value).
- [ ] Under `uk-gc`, BSA HRB information-management overhead included where the project is in HRB scope.
- [ ] All values in the profile's currency — no cross-contamination.

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
