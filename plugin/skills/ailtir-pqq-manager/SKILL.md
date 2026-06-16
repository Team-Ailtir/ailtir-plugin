---
name: ailtir-pqq-manager
description: Auto-fills PQQs (Pre-Qualification Questionnaires) or SAQs (Suitability Assessment Questionnaires) from the company context. Triggered by /ailtir-cowork-plugin:pqq-manager.
user-invocable: false
disable-model-invocation: true
---

# Ailtir PQQ Manager

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" ailtir-pqq-manager >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" ailtir-pqq-manager > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" ailtir-pqq-manager >nul 2>nul
```

You are managing Pre-Qualification Questionnaires (PQQs) or Suitability Assessment Questionnaires (SAQs). This skill operates in two modes:
1. **Complete Mode:** Filling out a PQQ for the contractor to submit to a client.
2. **Evaluate Mode:** Scoring incoming PQQs submitted by subcontractors.

## Step 1 — Determine Mode
Ask the user if they are *completing* a PQQ for a bid, or *evaluating* a PQQ from a subcontractor.

## Complete Mode: Step 2 — Read the Questionnaire
Read the provided PQQ document. Identify the required fields (e.g., Company Name, CRO Number, Turnover, Insurance Levels, Health & Safety stats).

## Complete Mode: Step 3 — Extract Answers
Read `Context/company.md` and `Context/team.md`.
Extract the exact answers required by the PQQ.

## Complete Mode: Step 4 — Draft the Response
Draft the responses in a clear format so the user can easily copy-paste them into the eTenders portal or the Word document.
If any information is missing from the Context files (e.g., a specific turnover figure for the last financial year), flag it clearly with `[HUMAN INPUT REQUIRED]`. Do NOT hallucinate or invent data. Ensure word counts or character limits are strictly adhered to.

## Complete Mode: Step 5 — Present
Provide the drafted responses.

## Evaluate Mode: Step 2 — Check Mandatory Gates
Check the subcontractor's submission against mandatory gates (e.g., CIRI registration, Safe-T-Cert, valid insurances). If they fail a mandatory gate, stop the evaluation and flag them as a FAIL.

## Evaluate Mode: Step 3 — Score the Submission
Score the remaining sections (Financial, Experience, Safety, Quality) based on the evidence provided. Provide a detailed rationale for each score.

## Evaluate Mode: Step 4 — Output Recommendation
Provide a clear PASS/FAIL/PASS WITH CONDITIONS recommendation for the subcontractor.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate or invent data. If it's not in the Context files, flag it as `[HUMAN INPUT REQUIRED]`.
- DO NOT ignore word counts or character limits.
- DO NOT change the format of the PQQ questions. Match them exactly.

## Quality Checks
- [ ] Every PQQ question answered — no blanks left.
- [ ] CIRI and Safe-T-Cert details sourced from `Context/company.md`.
- [ ] Subcontractor evaluation mode: RED/YELLOW/GREEN rating applied to every submission.
