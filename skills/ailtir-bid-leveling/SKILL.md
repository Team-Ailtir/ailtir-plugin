---
name: ailtir-bid-leveling
description: Phase 2 skill. Compares received subcontractor quotes for a specific trade package. Normalises pricing, scopes, and exclusions into a multi-tab Excel comparison. Triggered by /ailtir-bid-leveling.
---

# Ailtir — Bid Leveling (Quote Analysis)

You are a Commercial Manager leveling subcontractor quotes.

## Step 1 — Extract Base Data

Read all uploaded quotes for the package.
Extract from each:
- Subcontractor name
- Headline price
- Line item breakdown (if provided)
- Explicit inclusions
- Explicit exclusions
- Qualifications / assumptions
- Commercial terms (validity period, payment terms, retention)

## Step 2 — Scope Normalisation Protocol (Critical)

Subcontractor quotes rarely cover the exact same scope. You must perform a formal scope normalisation before comparing prices.

1. **Extract the Baseline Scope:** Read the ITT trade package specification (or the BOQ lines for this trade). This is the 100% scope baseline.
2. **Map Quotes to Baseline:** Map every line item and inclusion from each quote against the baseline.
3. **Identify Gaps (Missing Scope):** Identify items in the baseline that a subcontractor has excluded or failed to price.
4. **Identify Overlaps (Double-Counting):** Identify items a subcontractor has priced that belong to a different trade package (e.g., the mechanical sub pricing builder's work in connection, which the main contractor will do).
5. **Apply Normalisation Plugs:** 
   - For missing scope: Add a "plug" cost to that subcontractor's total to make them 100% compliant. Use the highest price quoted by another sub for that item, or flag it as `[REQUIRES ESTIMATOR PLUG]`.
   - For overlaps: Deduct the value of the overlapping item from their total.

*The goal is a Like-for-Like (LFL) Adjusted Total, which is often completely different from the headline price.*

## Step 3 — Generate Comparison

Run the Python script to generate the Comparison Excel workbook:
```bash
python scripts/create_comparison.py --output "Quote_Comparison_[Package].xlsx" --package "[Package Name]"
```

- [HUMAN INPUT REQUIRED] If a plug value for missing scope cannot be estimated from other quotes, flag it as `[REQUIRES ESTIMATOR PLUG]` and ask the user.

## Anti-Patterns (What NOT to do)
- DO NOT run the Python script without replacing `[Package Name]` with the actual package name.
- DO NOT ignore exclusions. They must be explicitly highlighted.
- DO NOT hallucinate plug values. Note them as estimates if they are not explicitly provided in the quotes.

Populate the workbook:
1. **Executive Summary:** Headline totals, variance from lowest, variance from budget.
2. **Commercial Comparison:** Side-by-side matrix of terms, validity, and exclusions.
3. **Like-for-Like Normalisation:** The mathematical leveling, adding plug numbers for missing scope.

## Step 3 — Present

Provide the Excel workbook. Summarise the findings: who is genuinely cheapest once exclusions are factored in, and what the key commercial risks are.

## Quality Checks
- [ ] Scope normalisation performed — every quote mapped against the baseline scope.
- [ ] Gaps (missing scope) identified and plug costs applied or flagged.
- [ ] Like-for-Like Adjusted Total calculated for every subcontractor.
- [ ] Executive Summary clearly identifies who is genuinely cheapest on an adjusted basis.
