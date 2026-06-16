---
name: ailtir-prelims-builder
description: Builds a priced Schedule of Preliminaries for Irish Public Works Contracts (PW-CF). Triggered by /ailtir-cowork-plugin:prelims-builder or when the user asks to price prelims.
user-invocable: false
disable-model-invocation: true
---

# Ailtir Prelims Builder

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" ailtir-prelims-builder >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" ailtir-prelims-builder > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" ailtir-prelims-builder >nul 2>nul
```

You are building a Schedule of Preliminaries for an Irish public works tender. Preliminaries represent the contractor's general obligations, site setup, and management costs that are not measured in the works items.

## Step 1 — Gather Project Context
Ask the user for:
1. **Contract Duration:** (e.g., 52 weeks)
2. **Estimated Contract Value:** (e.g., €5,000,000)
3. **Contract Type:** (e.g., PW-CF1, PW-CF5)
4. **Site Constraints:** (e.g., restricted city centre, greenfield)

## Step 2 — Draft the Prelims Schedule
Using the ARM4 (Agreed Rules of Measurement) structure, draft a schedule covering the following categories:
- **Management & Staff:** Project Manager, Site Manager, Engineer, QS, Safety Officer (calculate duration x weekly rate).
- **Site Establishment:** Cabins, welfare facilities, hoarding/fencing, temporary roads.
- **Temporary Services:** Temporary power, water, telecoms, waste management.
- **Plant & Equipment:** Tower cranes, teleporters, scaffolding (general).
- **Contractual & Insurances:** CAR insurance, EL/PL insurance, Performance Bond (typically 10% of contract value).
- **Health & Safety / Environmental:** PPE, signage, traffic management, dust/noise control.

## Step 3 — Apply Standard Irish Rates
Use standard Irish market rates (e.g., SCSI / Spon's 2025) for the build-up. For example:
- Site Manager: €1,500 - €1,800 / week
- 32ft Welfare Cabin: €150 - €200 / week
- Performance Bond: 1% - 2% of the bond amount

## Step 4 — Generate the Output
Present the prelims schedule as a detailed Markdown table with columns: Item, Description, Unit, Qty, Rate, Amount.
Ask the user if they want to export this to Excel. If yes, use a Python script with `pandas` to write the table to `prelims_schedule.xlsx`.

## Anti-Patterns (What NOT to do)
- DO NOT use US terminology (e.g., "General Conditions", "Trailer"). Use Irish terms (Preliminaries, Welfare Cabin).
- DO NOT lump all staff costs into a single percentage. Prelims must be built up from first principles (time x rate).
- DO NOT forget the Performance Bond cost — this is mandatory on almost all PW-CF contracts.
- [HUMAN INPUT REQUIRED] Do not guess the contract duration if it is not provided. You must ask the user.

## Quality Checks
- [ ] ARM4 structure used for all prelims items.
- [ ] Irish SEO management rates applied (PM €1,600/wk, SM €1,400/wk).
- [ ] Performance bond percentage matches ITT requirement (typically 10-12.5%).
