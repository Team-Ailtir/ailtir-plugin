---
name: ailtir_ta_contract-risk
description: "[Tender Analysis] Identify non-standard contract clauses, flag deviations from Irish/UK frameworks, and recommend a risk premium for inclusion in the tender sum. Invoke with /ailtir:ailtir_ta_contract-risk."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Contract risk auditor for Irish and UK construction tenders. Reads ITT Contract Particulars, compares clauses against standard frameworks (CWMF, PW-CF, RIAI, NEC4, JCT), flags deviations with plain-English explanations, and recommends a risk premium.

## Scope

Does: extract key contract fields, detect clause deviations from baseline frameworks, quantify financial exposure for flagged items, calculate an aggregate risk premium recommendation, and present findings to the user for review.

Does NOT: make Go/No-Bid decisions, draft contract amendment language, contact procurement authorities, or perform competitor analysis.

## Instructions

1. **Load the contractor profile.** Run `ailtir profile get`. Extract: organization type (main contractor, subcontractor, consultant, D&B), sector focus, and any configured risk thresholds. If no profile exists, stop and prompt: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Obtain the ITT Contract Particulars.** Ask the user to provide the Contract Particulars PDF (upload path or pasted text). Optionally ask for the technical specification PDF for cross-referencing defects liability clauses.

3. **Identify the contract framework.** Ask the user to confirm the primary framework: CWMF, PW-CF, RIAI, NEC4, or JCT. If uncertain, present the most likely option based on document metadata and ask: "This appears to be a [X] contract — correct?"

4. **Extract mandatory Contract Particulars fields.** For each of the following, extract the stated value and flag if outside the typical range: liquidated damages rate (flag if >€15,000/day), retention percentage (flag if >5%), defects liability period (flag if <12 or >36 months), insurance minimums (EL €13M, PL €6.5M), payment terms (flag if >45 days), performance bond (flag if >15%), and price fluctuation provisions (flag if absent on contracts >24 months).

5. **Run clause-by-clause comparison.** For each major clause group (Payment, Defects Liability, Insurance, Variation Procedures, Dispute Resolution, Statutory Compliance), compare the ITT text against the standard framework baseline. Classify each deviation as: missing, modified-stricter, modified-looser, or silent on a key issue. Assign a risk category: Financial, Legal, Operational, or Health & Safety.

6. **Apply form-specific risk rules.** For RIAI: flag the 20-day notice and 25-day claim detail time bars. For NEC4: flag the 8-week CE notification, 3-week quotation, and 2-week PM response windows as prelims cost drivers. For JCT: flag Building Safety Act Gateway 2 triggers for buildings above 18m or 7 storeys.

7. **Rate each flagged item.** Assign Low (minor or standard deviation), Medium (material but manageable), or High (dangerous precedent or uninsurable). Stop and confirm with the user before proceeding if more than 3 High-risk items are identified: "This contract has [N] High-risk items. Review the list below and confirm you wish to continue with full premium calculation."

8. **Quantify financial exposure for flagged items.** For extended defects liability periods: calculate retention time-cost = (extended months / 12) × borrowing rate × contract value. For onerous retention rates: calculate cash-flow cost = retention amount × (contract duration / 2 weeks) × borrowing rate. Express each as a percentage of contract sum.

9. **Calculate the aggregate risk premium.** Sum all quantified allowances. Apply a contingency multiplier: ×1.15 if only Medium-risk items; ×1.25 if any High-risk items. Present the result as both a percentage and an absolute amount: "Recommended risk premium: [X]% (€[Y] on a €[Z] contract)."

10. **Present the risk register for user review.** List all flagged items ranked by risk level then financial impact. For each item include: clause reference, deviation description, risk category, financial impact estimate, and recommended action (accept/negotiate/flag for legal). Stop and ask the user to confirm or adjust the risk register before finalizing.

11. **Deliver the final output.** Summarize: total flagged items by risk level, the recommended risk premium with sensitivity ("If you negotiate away item [A], premium drops to [X]%"), and any items the user should flag to legal or a contracts manager. Remind the user to pass the risk findings to Scope Gap analysis: "Run `/ailtir:ailtir_ta_scope-gap` to cross-reference these findings with the specification and BOQ."

## Error Handling

- **Scanned or unreadable PDF:** Inform the user: "This document could not be parsed reliably. Please provide a text-based PDF or paste the key clause text directly."
- **Hybrid or unrecognised contract form:** Present the closest matching framework and flag all deviations in a separate "unmatched clauses" section. Ask the user to confirm the interpretation before calculating the premium.
- **Missing specification for cross-reference:** Proceed with contract-only analysis and note: "Specification not provided — defects liability clause alignment cannot be verified. Cross-reference when specification is available."
- **Contract value missing or zero:** Stop and prompt: "A valid contract value is required to calculate the risk premium as an absolute amount. Please provide the estimated contract sum."
- **More than 5 High-risk items:** Escalate immediately: "This contract has [N] High-risk items. A legal or contracts manager review is strongly recommended before submission."
