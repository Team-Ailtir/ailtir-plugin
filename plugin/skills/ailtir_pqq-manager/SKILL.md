---
name: ailtir_pqq-manager
description: Auto-fills PQQs/SQ documents from the company context, or evaluates incoming subcontractor PQQs, applying the accreditation and disclosure requirements of the active Ailtir profile (Irish CIRI/Safe-T-Cert or UK SSIP/Modern Slavery/Carbon Reduction Plan). Triggered by /ailtir_pqq-manager.
---

# Ailtir PQQ Manager

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_pqq-manager`
- `plugin_version`: `2.17.0`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

You are managing Pre-Qualification Questionnaires (PQQs) or, under the Procurement Act 2023, the Central Digital Platform Supplier Information regime that replaces the pre-Brexit Selection Questionnaire (SQ). This skill operates in two modes:
1. **Complete Mode:** Filling out a PQQ / Supplier Information response for the contractor to submit to a client.
2. **Evaluate Mode:** Scoring incoming PQQs submitted by subcontractors.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir_setup`. The accreditations to check, statutory disclosures required, and typical PQQ instrument depend on `profile_key`:

- `ireland-gc` — Irish PQQs on eTenders. Check: CIRI registration, Safe-T-Cert, ISO 9001/14001/45001, insurance limits, turnover, CIS/Revenue tax clearance.
- `uk-gc` — UK PQQs / Supplier Information under Procurement Act 2023 Central Digital Platform (or legacy SQ under the Public Contracts Regulations 2015 on pre-February-2025 procurements). Check: SSIP (CHAS / SafeContractor / Constructionline Gold / Achilles Building Confidence), ISO 9001/14001/45001, insurance limits, turnover, Modern Slavery Act s.54 statement (mandatory disclosure if turnover ≥£36m), Carbon Reduction Plan reference under PPN 06/20 for central government contracts >£5m/year, Social Value response under PPN 06/21 (minimum 10% weighting on central government works), and Building Safety Act competency evidence where the project involves Higher-Risk Buildings.

## Step 2 — Determine Mode
Ask the user if they are *completing* a PQQ for a bid, or *evaluating* a PQQ from a subcontractor.

## Complete Mode: Step 3 — Read the Questionnaire
Read the provided PQQ document. Identify the required fields (Company Name, registered number, Turnover, Insurance Levels, Health & Safety stats, and — under `uk-gc` — Modern Slavery, Carbon Reduction, and Social Value sections).

## Complete Mode: Step 4 — Extract Answers
Read `Context/company.md` and `Context/team.md`.
Extract the exact answers required by the PQQ. For `uk-gc`, cross-check that the following are available and current:

- Published Modern Slavery s.54 statement (required if the company's turnover ≥£36m) — link or filename in `Context/company.md`.
- Compliant Carbon Reduction Plan under PPN 06/20 (Emissions baseline, target Net Zero date ≤2050, published on the company website).
- Social Value narrative addressing the PPN 06/21 themes and MACs (Model Award Criteria).
- SSIP accreditation certificate reference and expiry date.
- Building Safety Act competency evidence — where the notice explicitly requires it.

## Complete Mode: Step 5 — Draft the Response
Draft the responses in a clear format so the user can easily copy-paste them into the portal (eTenders under `ireland-gc`, Find a Tender / Contracts Finder under `uk-gc`) or the Word document.
If any information is missing from the Context files (e.g., a specific turnover figure for the last financial year, or the most recent Modern Slavery statement URL), flag it clearly with `[HUMAN INPUT REQUIRED]`. Do NOT hallucinate or invent data. Ensure word counts and character limits are strictly adhered to.

## Complete Mode: Step 6 — Present
Provide the drafted responses.

## Evaluate Mode: Step 3 — Check Mandatory Gates
Check the subcontractor's submission against the mandatory gates for the active profile:

- Under `ireland-gc`: CIRI registration, Safe-T-Cert, valid insurances, Revenue tax clearance.
- Under `uk-gc`: SSIP membership, ISO certifications where required, valid insurances, HMRC tax compliance, and — for HRB scope — BSA competency evidence.

If they fail a mandatory gate, stop the evaluation and flag them as a FAIL.

## Evaluate Mode: Step 4 — Score the Submission
Score the remaining sections (Financial, Experience, Safety, Quality) based on the evidence provided. Provide a detailed rationale for each score.

## Evaluate Mode: Step 5 — Output Recommendation
Provide a clear PASS / FAIL / PASS WITH CONDITIONS recommendation for the subcontractor.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate or invent data. If it's not in the Context files, flag it as `[HUMAN INPUT REQUIRED]`.
- DO NOT ignore word counts or character limits.
- DO NOT change the format of the PQQ questions. Match them exactly.
- DO NOT apply Irish gates (CIRI, Safe-T-Cert) to a UK PQQ, or UK gates (SSIP, Modern Slavery, CRP) to an Irish PQQ.

## Quality Checks
- [ ] `Context/profile.json` read; correct accreditation and statutory-disclosure gates applied.
- [ ] Every PQQ question answered — no blanks left.
- [ ] Under `ireland-gc`: CIRI and Safe-T-Cert details sourced from `Context/company.md`.
- [ ] Under `uk-gc`: SSIP membership, Modern Slavery statement, Carbon Reduction Plan, and Social Value response all cited from `Context/company.md`.
- [ ] Subcontractor evaluation mode: RED / AMBER / GREEN rating applied to every submission.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
