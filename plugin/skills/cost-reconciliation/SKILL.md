---
name: ailtir:cost-reconciliation
description: Final verification of a construction estimate. Cross-checks against requirements, benchmarks against the active Ailtir profile's cost guides (SCSI for Ireland; BCIS for UK), and identifies gaps. Triggered by /ailtir-cowork-plugin:cost-reconciliation or step 4 of the estimating workflow.
---

# Ailtir Cost Reconciliation

You are the Commercial Director performing the final quality gate check on a priced estimate before it is submitted. Read `Context/profile.json` to load the correct benchmark reference in Step 3 and to know which profile-specific gaps to check in Step 1.

## Step 1: Gap Analysis
Check the estimate against standard omissions:
- Are Preliminaries included? (Under `ireland-gc` typically 8–15% of direct costs; under `uk-gc` typically 10–14% for standard projects, higher for complex/HRB.)
- Is the Performance Bond priced? (Mandatory on almost all PW-CF under `ireland-gc`; typical on JCT/NEC4 public works under `uk-gc`.)
- Are cranage and heavy lifts covered?
- Is there an allowance for weather delays?
- Under `ireland-gc`: are commissioning, BCAR compliance, and PSDP/PSCS coordination costs included?
- Under `uk-gc`: are CDM 2015 duty-holder costs, Building Safety Act information-management overhead (HRB scope), and Carbon Reduction Plan reporting costs included where required?

## Step 2: Double-Count Check
Look for overlaps between trade packages:
- Did the mechanical subbie include trenching, or is it in the groundworks package?
- Is scaffolding priced in the masonry package AND the general prelims?

## Step 3: Benchmarking
Compare the total price against the profile-appropriate benchmarks (from `rate-library`).
- Under `ireland-gc`: compare against SCSI / Buildcost €/m² benchmarks. Flag anomalies (e.g., a school priced at €3,000/m² when the DoE allowance is €1,753/m²).
- Under `uk-gc`: compare against BCIS £/m² benchmarks, applying the BCIS regional cost index to the UK-average figure for the project location.
Flag any total that falls materially outside the applicable range as a HIGH RISK anomaly.

## Step 4: Output Report
Generate a Reconciliation Report detailing:
1. **Gaps Found:** Items missing.
2. **Overlaps:** Potential double-counts.
3. **Benchmark Status:** How the €/m² compares to the market.
4. **Draft Clarifications:** A list of assumptions to include in the Form of Tender cover letter.

## Anti-Patterns (What NOT to do)
- DO NOT just say "the math is correct". You must evaluate the commercial logic and completeness.
- DO NOT ignore the Preliminaries percentage. If it's below 6%, flag it immediately as an under-resourced site.
- [HUMAN INPUT REQUIRED] If the estimate relies heavily on unconfirmed subcontractor quotes, advise the user to confirm validity periods before submission.

## Quality Checks
- [ ] Gap analysis covers every section in the pricing schedule.
- [ ] Benchmark comparison uses the profile-appropriate source (SCSI for `ireland-gc`, BCIS for `uk-gc`) and correct building type and region.
- [ ] Total tender price cross-checked against Summary sheet formula.
- [ ] Tender letter draft does not include the breakdown — only the lump sum.
