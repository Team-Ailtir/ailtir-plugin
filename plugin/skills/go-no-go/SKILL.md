---
name: go-no-go
description: Evaluates bid viability against the accreditation gates and weighted scoring matrix appropriate to the active Ailtir profile (Irish CIRI/Safe-T-Cert or UK SSIP). Triggered by /ailtir-cowork-plugin:go-no-go or when bid-planner runs.
---

# Ailtir Go/No-Go Evaluator

You are evaluating a tender against the Go/No-Go framework for the active market.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root to determine `profile_key`. If it is missing, stop and tell the user to run `/ailtir-cowork-plugin:setup`.

## Step 2 — Evaluate Mandatory Gates
Read the profile-appropriate criteria file from the sibling `bid-planner` skill's directory:

- `ireland-gc` → `references/ireland-gc/go-no-go-criteria.md` in the `bid-planner` skill.
- `uk-gc` → `references/uk-gc/go-no-go-criteria.md` in the `bid-planner` skill.

Check the user's `Context/company.md` against the tender requirements. The gates depend on profile:

- **Under `ireland-gc`:** Safe-T-Cert grade, CIRI registration, turnover ≥1.5×–2× annualised contract value, bond/insurance capacity, site management capacity.
- **Under `uk-gc`:** SSIP membership (CHAS / SafeContractor / Constructionline Gold / Achilles Building Confidence), ISO 9001/14001/45001, turnover ≥1.5×–2× annualised contract value, bond/insurance capacity, site management capacity, and — for Higher-Risk Buildings — BSA 2022 Principal Contractor competency, Modern Slavery s.54 statement (if company turnover ≥£36m), and a compliant Carbon Reduction Plan (for central government contracts >£5m/year).

If any gate fails, flag it as a **RED NO-GO RISK**.

## Step 3 — Score the Opportunity
Score the tender out of 100 using the four dimensions in the loaded criteria file:
1. Client & Relationship (30)
2. Sector & Experience (25)
3. Commercial & Contract (25) — note the scoring bands are profile-specific (PW-CF/RIAI risk allocation for `ireland-gc`; unamended JCT/NEC4 for `uk-gc`).
4. Competition & Procurement (20) — routes differ by profile (CWMF vs Procurement Act 2023 procedures).

## Step 4 — Present
Provide the final score and a recommendation (Strong GO, Marginal GO, NO-GO).
If called by the `bid-planner`, return the score to the orchestrator. If called directly, present it to the user.

- [HUMAN INPUT REQUIRED] If the tender pack is missing key data (e.g., contract value, procurement route), ask the user before scoring.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate the scoring weights. Read the loaded criteria file.
- DO NOT proceed if a mandatory gate is failed. Flag it immediately.
- DO NOT invent missing information; ask the user to clarify if the tender pack is missing data.
- DO NOT apply Irish accreditation gates to UK tenders (or vice versa).

## Quality Checks
- [ ] `Context/profile.json` read; correct `profile_key` criteria file loaded from the `bid-planner` skill's references.
- [ ] Mandatory gates for the active profile explicitly checked against actual context data.
- [ ] No hallucinated scores; every score justified by evidence from the tender pack.
- [ ] Final recommendation aligns with the scoring thresholds in the loaded criteria file.
