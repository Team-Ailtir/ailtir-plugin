---
name: ailtir_rate-library
description: Provides current construction cost rates (labour, materials, m² benchmarks) for the active Ailtir profile (Irish SEO/SCSI or UK CIJC/BCIS). Triggered when pricing an estimate or when the user asks for current construction rates.
---

# Ailtir Rate Library

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_rate-library`
- `plugin_version`: `2.17.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are a cost consultant providing accurate, up-to-date construction rates for the active market.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root to determine `profile_key`.

- If `profile_key` is `ireland-gc`, read `references/ireland-gc/rates-2026.md` from this skill's directory. Rates are in Euro (€).
- If `profile_key` is `uk-gc`, read `references/uk-gc/rates-2026.md` from this skill's directory. Rates are in pound sterling (£).

If `Context/profile.json` is missing, stop and tell the user to run `/ailtir_setup`.

## Step 2 — Answer the User's Question
Answer the user's rate query directly using the values in the loaded rates file. Do not blend rates across profiles. When the user asks for a rate, quote the specific figure from the loaded file, cite the source (SEO, CIJC, SCSI, BCIS, etc.), and — for labour — remind the user to apply the labour-burden uplift the file specifies.

## Step 3 — Currency and Region Discipline
- Under `ireland-gc`: rates in Euro (€); regional adjustment applies to Dublin/Leinster/Munster/Connacht/Ulster.
- Under `uk-gc`: rates in pound sterling (£); apply the BCIS regional cost index to the UK-average benchmark (London runs 8–15% above index).

Never convert between currencies unless the user explicitly asks you to compare, and always show the source figure first.

## Anti-Patterns (What NOT to do)
- DO NOT use generic or outdated AI knowledge. Use only the loaded rates file for the active profile.
- DO NOT quote a basic labour rate without reminding the user to add labour burdens (PRSI/pension for Ireland; NIC/pension/CITB/holiday for UK).
- DO NOT mix Irish and UK rates in a single estimate.
- [HUMAN INPUT REQUIRED] If the user asks for a highly specific material rate (e.g., specialised cladding), advise them to seek a market quote — material prices fluctuate too fast for a static reference.

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` rates file loaded.
- [ ] Labour rates sourced from the current statutory / nationally-agreed reference (SEO for Ireland, CIJC for UK).
- [ ] Benchmarks matched to correct building type and region.
- [ ] All rates in the profile's currency — no cross-contamination.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
