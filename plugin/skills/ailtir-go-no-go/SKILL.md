---
name: ailtir-go-no-go
description: Evaluates bid viability against CIRI/Safe-T-Cert gates and the Ailtir weighted scoring matrix. Triggered by /ailtir-cowork-plugin:go-no-go or when bid-planner runs.
user-invocable: false
disable-model-invocation: true
---

# Ailtir Go/No-Go Evaluator

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" ailtir-go-no-go >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" ailtir-go-no-go > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" ailtir-go-no-go >nul 2>nul
```

You are evaluating a tender against the Irish market Go/No-Go framework.

## Step 1 — Evaluate Mandatory Gates
Read `references/go-no-go-criteria.md`.
Check the user's `Context/company.md` against the tender requirements.
- Do they have the required Safe-T-Cert grade?
- Do they have the required CIRI registration?
- Is their turnover sufficient for the contract value?

If any gate fails, flag it as a **RED NO-GO RISK**.

## Step 2 — Score the Opportunity
Score the tender out of 100 based on the four criteria in the reference file:
1. Client & Relationship (30)
2. Sector & Experience (25)
3. Commercial & Contract (25)
4. Competition & Procurement (20)

## Step 3 — Present
Provide the final score and a recommendation (Strong GO, Marginal GO, NO-GO).
If called by the `ailtir-bid-planner`, return the score to the orchestrator. If called directly, present it to the user.

- [HUMAN INPUT REQUIRED] If the tender pack is missing key data (e.g., contract value, procurement route), ask the user before scoring.

## Anti-Patterns (What NOT to do)
- DO NOT hallucinate the scoring weights. Read `references/go-no-go-criteria.md`.
- DO NOT proceed if a mandatory gate (e.g., CIRI) is failed. Flag it immediately.
- DO NOT invent missing information; ask the user to clarify if the tender pack is missing data.

## Quality Checks
- [ ] Mandatory gates explicitly checked against actual context data.
- [ ] No hallucinated scores; every score justified by evidence from the tender pack.
- [ ] Final recommendation aligns with the scoring thresholds.
