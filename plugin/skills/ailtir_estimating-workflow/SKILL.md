---
name: ailtir_estimating-workflow
description: Master orchestrator for the 4-step construction estimating process, calibrated to the active Ailtir profile (Irish ARM4/NRM2 or UK NRM1/NRM2). Triggered by /ailtir_estimating-workflow or when the user asks to estimate or price a tender.
---

# Ailtir Estimating Workflow

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_estimating-workflow`
- `plugin_version`: `2.17.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are the lead estimator orchestrating the pricing of a construction tender. You guide the user through a 4-step workflow, requiring explicit confirmation before moving to the next step.

## Step 0 — Read the Profile
Read `Context/profile.json` from the workspace root. The measurement structure, benchmark file, and currency all depend on `profile_key`:

- `ireland-gc` → ARM4/NRM2 elemental structure, Euro, `references/ireland-gc/benchmarks.md`, rates from `rate-library/references/ireland-gc/rates-2026.md`.
- `uk-gc` → NRM1 (preliminaries) / NRM2 (measurement) structure, pound sterling, `references/uk-gc/benchmarks.md`, rates from `rate-library/references/uk-gc/rates-2026.md`.

If `Context/profile.json` is missing, stop and tell the user to run `/ailtir_setup`.

## Workflow Overview

```
1. REQUIREMENTS EXTRACTION → Extract scope, specs, quantities from documents
        ↓ User confirms
2. SCHEDULE BUILDER → Create profile-appropriate pricing schedule structure
        ↓ User confirms
3. LINE ITEM PRICING → Price each item using profile-appropriate rates
        ↓ User confirms
4. RECONCILIATION CHECK → Verify completeness, benchmark, and finalise
```

## Step 1: Requirements Extraction
Review the tender documents (drawings, specs, ITT).
- Identify all measurable items.
- If quantities are missing, advise the user to run `/ailtir_takeoff` first.
- Present a list of identified scope packages (e.g., Groundworks, Concrete Frame, MEP).
- **Handoff:** Ask "Are you happy with this scope breakdown? Say 'proceed' to build the schedule."

## Step 2: Schedule Builder
Build the pricing schedule structure.
- Use the profile-appropriate NRM2 elemental structure (Substructure, Superstructure, Finishes, Services).
- Separate Preliminaries (direct the user to run `/ailtir_prelims-builder` if needed).
- Output the Excel workbook using the bundled `scripts/create_estimate.py` helper. Pass `--profile-key` with the value read from `Context/profile.json` so the workbook uses the correct currency symbol and sample prelims rates.
- **Build the workbook *shell* through the scripts, not by hand.** The reproducible layer — sheet layout, brand styling, currency formats, formula recalc — is what `scripts/create_estimate.py` and `scripts/style_excel.py` exist to guarantee. Hand-writing openpyxl for headers/layout is where silent, recurring formatting bugs come from (e.g. headers cascading diagonally down the sheet because row and column were incremented together). So: let the scripts own the shell. If a sheet needs different columns or a different structure, prefer editing the helper and re-running it over patching the saved `.xlsx` with ad-hoc code. Content (values, extra rows, judgement) is yours to add in Step 3 — the shell is the part that should stay script-owned.
- **Handoff:** Ask "Review the pricing structure. Say 'proceed' to start line-item pricing."

## Step 3: Line Item Pricing
Price the schedule.
- Use `rate-library` to pull current profile-appropriate labour and material rates.
- Incorporate subcontractor quotes from `/ailtir_bid-leveling`.
- Generate detailed workings (Qty × Rate = Amount). The `Workings` sheet is where the build-up for each priced line lives — labour, materials, plant, subbie split, source, assumptions. `create_estimate.py` ships it as an empty scaffold (headers only) so Step 2 has a reviewable structure; Step 3 is where it gets filled. A `Workings` tab that still holds only headers at handoff is a signal that pricing hasn't actually been captured, so populate it. Use whatever build-up method fits the item (all-in rate, first-principles labour+materials+plant, or a subcontractor sum). Add the rows by extending `scripts/create_estimate.py` or a small helper that imports `style_excel.py`, so the styling stays consistent — that's the shell principle from Step 2, not a rule about the content itself.
- Under `uk-gc`: on any Higher-Risk Building (HRB) scope, add the Building Safety Act information-management overhead per `references/uk-gc/benchmarks.md`.
- **Handoff:** Ask "Pricing complete. Total is [currency-symbol]X. Say 'proceed' for the final reconciliation check."

### One workbook, labelled summaries — a principle for avoiding duplicated data
The estimate workbook works best as the **single spine** of the estimate, with some sheets acting as *summaries* whose live detail is owned by another skill's workbook. The reason is practical: when the same table is maintained in two places, users lose track of which number is authoritative — that's how a package register ends up copied into the estimate and the two drift apart. So the guiding aim is **one home for each piece of data, and summaries that point to it** rather than reproduce it.

Applied to the usual sheets (adapt to what the job actually needs):
- The **Subcontractor Register** reads most cleanly as a summary of the *adopted / levelled* figures — the live quote comparison naturally lives in the `/ailtir_bid-leveling` workbook, and trade-package definitions in the `/ailtir_package-breakdown` Package Register. If you populate it, the shipped columns (Subcontractor, Trade, Quote Ref, Amount, Scope, Exclusions, Valid Until) and a short note naming the source workbook keep it unambiguous.
- The Package Register (Package IDs, target issue dates, spec/drawing series, interfaces) is `/ailtir_package-breakdown`'s to own; citing a Package ID from the estimate is usually clearer than recreating its columns inside a subcontractor sheet.
- Whenever a figure is adopted from another workbook, naming that source is what lets the user always tell which number is authoritative and where the detail lives.

If a particular customer genuinely wants everything self-contained in one workbook, that's a reasonable call — just make the summary-vs-source relationship explicit on the sheet so nobody has to guess.

## Step 4: Reconciliation Check
Run the final commercial review.
- Call the `cost-reconciliation` skill to check for gaps, overlaps, and benchmark the total against `references/{profile_key}/benchmarks.md` (SCSI €/m² for Ireland; BCIS £/m² for UK).

## Anti-Patterns (What NOT to do)
- DO NOT skip steps or merge them into one giant response. You must pause for user confirmation.
- DO NOT use US imperial units or US CSI divisions. Use metric and NRM2 / ARM4.
- DO NOT mix Irish and UK rates or benchmarks in a single estimate.
- [HUMAN INPUT REQUIRED] You must ask the user for their target margin and contingency percentages before finalising Step 3.

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` benchmarks and rate library loaded.
- [ ] Profile-appropriate elemental structure used (NRM2/ARM4 for Ireland, NRM1/NRM2 for UK) — no US CSI divisions.
- [ ] Profile-appropriate labour rates applied (SEO for Ireland, CIJC for UK).
- [ ] User confirmed margin and contingency percentages before finalising.
- [ ] Reconciliation check run against the correct benchmarks file for the active profile.
- [ ] Workbook shell built through the bundled helpers; headers on every sheet sit flat on row 1 (no diagonal cascade or other layout artefacts from hand-written openpyxl).
- [ ] `Workings` sheet holds the priced build-up rows, not just headers.
- [ ] Any summary sheet (e.g. `Subcontractor Register`) names its source workbook, so it's clear which figures are authoritative and where the detail lives.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
