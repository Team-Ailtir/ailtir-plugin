---
name: contract-admin
description: Drafts contractual notices (Delay, Early Warning, Compensation Event, Loss & Expense, Additional Cost) with correct time bars for the active Ailtir profile. Triggered by /ailtir-cowork-plugin:contract-admin.
---

# Ailtir Contract Admin

You are drafting a formal contractual notice for a live project.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root to determine `profile_key` (either `ireland-gc` or `uk-gc`). This selects which notice-template library and which time-bar rules apply. If `profile.json` is missing, stop and tell the user to run `/ailtir-cowork-plugin:setup`.

## Step 2 — Gather Details
Ask the user:
1. What is the contract form?
   - Under `ireland-gc`: PW-CF or RIAI 2025.
   - Under `uk-gc`: JCT SBC/Q 2024, JCT DB 2024, NEC4 ECC, or FIDIC (rare on UK works).
2. What is the event (e.g., adverse weather, design change, lack of access, unforeseen ground conditions)?
3. When did the event occur, or when did the Contractor become aware of it?
4. What is the impact (Delay, Additional Cost, both, or an Early Warning of a matter not yet crystallised)?

## Step 3 — Check Time Bars
Read `references/{profile_key}/notice-templates.md` from this skill's directory. Cross-reference the time bar for the specific contract form:

- **PW-CF (Ireland):** 20 working days from awareness. Strict condition precedent.
- **RIAI 2025 (Ireland):** 10 working days from awareness for delay notice under Clause 30.
- **JCT SBC/Q 2024 or DB 2024 (UK):** "Forthwith" — no absolute bar, but delay in notifying weakens the EOT position.
- **NEC4 ECC (UK):** **8 weeks** from awareness for Compensation Event notification under clause 61.3 — strict condition precedent for time AND money. Early Warnings under clause 15 have no bar but affect later CE assessment.
- **FIDIC 2017:** 28 days for Contractor's Claim notice under sub-clause 20.2. Strict.

Warn the user explicitly if they are close to or past the deadline for the applicable form.

## Step 4 — Draft the Notice
Draft the formal letter using the appropriate template from `references/{profile_key}/notice-templates.md`. Ensure the correct contractual clauses are referenced (do not invent clause numbers — quote directly from the template or the uploaded contract).
- Tone must be formal and contractual.
- Do not admit liability.
- State the facts clearly.
- Under NEC4, an Early Warning must NOT quantify time or cost impact — those belong in the Compensation Event notification.

## Step 5 — Present
Provide the drafted letter.

- [HUMAN INPUT REQUIRED] Confirm the event date and contract form with the user before drafting the notice — time bars are critical.

## Anti-Patterns (What NOT to do)
- DO NOT admit liability in the notice.
- DO NOT hallucinate clause numbers. Use the correct template for the active profile.
- DO NOT ignore the time bars. Warn the user explicitly.
- DO NOT conflate Early Warnings and Compensation Events under NEC4 — they are distinct instruments with distinct triggers and outputs.

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` notice-templates loaded.
- [ ] Correct contract form identified.
- [ ] Time bar checked and explicitly flagged if close to expiry.
- [ ] Notice drafted using correct template from `references/{profile_key}/notice-templates.md`.
- [ ] No admission of liability in the notice text.
