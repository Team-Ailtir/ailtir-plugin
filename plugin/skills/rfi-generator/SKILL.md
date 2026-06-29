---
name: rfi-generator
description: Drafts formal Requests for Information (RFIs), logs them in Notion, and processes incoming RFI answers to flag impacts on other bid documents. Triggered by /ailtir-cowork-plugin:rfi-generator or when the user says "draft an RFI" or "process these RFI answers".
---

# Ailtir RFI Generator

You are drafting formal clarification questions for a tender.

## Step 1 — Understand the Query
Ask the user what they need clarified, or read their notes.

## Step 2 — Draft the RFI
Draft a professional, concise RFI.
Format:
- **Reference:** [Drawing/Spec Number]
- **Query:** [Clear, direct question]
- **Proposed Solution:** [Optional: suggest a solution to speed up the answer]

## Step 3 — Log it
If the Notion connector is active, use it to add a new row to the RFI Log database.
If not, just provide the drafted text to the user.

## Step 4 — Process Incoming Answers (When User Uploads Q&A Responses)
When the user uploads an RFI response document or pastes answers from the client:

1. **Classify the Answer:** For each answer, classify it into one of these categories:
   - `administrative` (process/logistics, no scope impact)
   - `scope_addition` (adds items not previously explicit)
   - `scope_deletion` (removes items)
   - `drawing_amendment` (revises drawings)
   - `spec_change` (changes material, standard, or performance)
   - `contract_conditions_change` (changes clause, LADs, retention)
   - `programme_change` (changes dates or phasing)

2. **Impact Cascade Assessment:** For every non-administrative answer, flag exactly what needs to be updated:
   - If `scope_addition` / `deletion`: Flag that the BOQ and Prelims must be re-priced.
   - If `spec_change`: Flag that the Compliance Matrix and Quality Method Statements must be reviewed.
   - If `contract_conditions_change`: Flag that the Contract Risk review must be updated.

3. **Present Impact Report:** Give the user a clear summary of which bid documents are now "stale" based on the answers received, so they know what to re-run.

- [HUMAN INPUT REQUIRED] Confirm the RFI number and project name with the user before logging to Notion.

## Anti-Patterns (What NOT to do)
- DO NOT draft vague questions. Be specific and reference the exact drawing or spec.
- DO NOT skip the Notion log if the connector is active.
- DO NOT ask multiple questions in a single RFI. One question per RFI is best practice.

## Quality Checks
- [ ] RFI number follows sequential format (RFI-001, RFI-002, etc.).
- [ ] Question is clear and references the specific drawing or spec section.
- [ ] RFI logged to Notion RFI Log with correct status (Draft/Submitted).
