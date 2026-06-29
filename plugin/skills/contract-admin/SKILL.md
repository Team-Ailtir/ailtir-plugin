---
name: contract-admin
description: Drafts contractual notices (Delay, Additional Cost) with correct time bars for PW-CF and RIAI. Triggered by /ailtir-cowork-plugin:contract-admin.
---

# Ailtir Contract Admin

You are drafting a formal contractual notice for a live project.

## Step 1 — Gather Details
Ask the user:
1. What is the contract form (PW-CF or RIAI)?
2. What is the event (e.g., weather, design change, lack of access)?
3. When did the event occur?
4. What is the impact (Delay, Cost, or both)?

## Step 2 — Check Time Bars
Read `references/notice-templates.md`.
Check the time bar for the specific contract form.
- PW-CF: Notice must be within 20 working days.
- RIAI: Notice must be within 10 working days.
Warn the user if they are close to or past the deadline.

## Step 3 — Draft the Notice
Draft the formal letter using the appropriate template. Ensure the correct contractual clauses are referenced.
- Tone must be formal and contractual.
- Do not admit liability.
- State the facts clearly.

## Step 4 — Present
Provide the drafted letter.

- [HUMAN INPUT REQUIRED] Confirm the event date and contract form with the user before drafting the notice — time bars are critical.

## Anti-Patterns (What NOT to do)
- DO NOT admit liability in the notice.
- DO NOT hallucinate clause numbers. Use the correct template.
- DO NOT ignore the time bars. Warn the user explicitly.

## Quality Checks
- [ ] Correct contract form identified (PW-CF or RIAI).
- [ ] Time bar checked and explicitly flagged if close to expiry.
- [ ] Notice drafted using correct template from `references/notice-templates.md`.
- [ ] No admission of liability in the notice text.
