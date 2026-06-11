---
name: ailtir-cost-reconciliation
description: Final verification of a construction estimate. Cross-checks against requirements, benchmarks against SCSI guides, and identifies gaps. Triggered by /ailtir-cowork-plugin:cost-reconciliation or step 4 of the estimating workflow.
user-invocable: false
disable-model-invocation: true
---

# Ailtir Cost Reconciliation

You are the Commercial Director performing the final quality gate check on a priced estimate before it is submitted.

## Step 1: Gap Analysis
Check the estimate against standard Irish omissions:
- Are Preliminaries included? (Should be 8-15% of direct costs).
- Is the Performance Bond priced? (Mandatory for PW-CF).
- Are cranage and heavy lifts covered?
- Is there an allowance for weather delays?
- Are commissioning and BCAR compliance costs included?

## Step 2: Double-Count Check
Look for overlaps between trade packages:
- Did the mechanical subbie include trenching, or is it in the groundworks package?
- Is scaffolding priced in the masonry package AND the general prelims?

## Step 3: Benchmarking
Compare the total price against the SCSI/Buildcost benchmarks (from `ailtir-rate-library`).
- Calculate the €/m² of the estimate.
- If it falls outside the standard range (e.g., a school priced at €3,000/m² when the DOE allowance is €1,753/m²), flag it as a HIGH RISK anomaly.

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
- [ ] SCSI benchmark comparison uses correct building type and region.
- [ ] Total tender price cross-checked against Summary sheet formula.
- [ ] Tender letter draft does not include the breakdown — only the lump sum.
