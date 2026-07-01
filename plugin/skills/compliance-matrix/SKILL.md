---
name: compliance-matrix
description: Extracts all ITT requirements into a tracked deliverables matrix. Triggered by /ailtir-cowork-plugin:compliance-matrix or when bid-planner runs.
---

# Ailtir Compliance Matrix Builder

You are extracting the exact submission requirements from a tender pack.

## Step 1 — Extract Requirements
Scan the ITT (Instruction to Tenderers) and any Returnable Schedules.
Extract:
- Every evaluation criterion and its weighting.
- Every mandatory returnable document (e.g., Form of Tender, Pricing Schedule, Programme).
- Page limits, formatting rules, and submission methods (e.g., eTenders portal under `ireland-gc`; Find a Tender, Contracts Finder, or the buyer's e-tendering platform such as Delta / Jaggaer / Proactis / In-tend under `uk-gc`).

## Step 2 — Check Templates
Check if the required templates were actually provided in the tender pack. If the ITT says "Complete Schedule 3" but Schedule 3 is missing, flag this as a critical gap.

## Step 3 — Present
Provide a clear, structured list of requirements.
If called by the `bid-planner`, return the data to the orchestrator to populate the Excel tab. If called directly, present it to the user.

- [HUMAN INPUT REQUIRED] If the submission method or deadline is not stated in the ITT, ask the user before finalising the matrix.

## Anti-Patterns (What NOT to do)
- DO NOT miss mandatory returnables. Scan the entire ITT.
- DO NOT hallucinate deadlines or weightings. Use exact figures from the ITT.
- DO NOT guess the submission method if it is not stated; flag it as a question.

## Quality Checks
- [ ] Every evaluation criterion captured with exact weighting.
- [ ] Missing templates explicitly flagged.
- [ ] Submission method and deadline captured.
