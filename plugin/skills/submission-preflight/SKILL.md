---
name: submission-preflight
description: Runs final deterministic compliance checks before submission. Triggered by /ailtir-cowork-plugin:submission-preflight.
---

# Ailtir Submission Pre-Flight

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" submission-preflight >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" submission-preflight > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" submission-preflight >nul 2>nul
```

You are running the final checks before the bid is submitted to the client.

## Step 1 — Review the Master Document
Read the assembled master submission document.

## Step 2 — Check against ITT
Cross-reference against the Compliance Matrix.
Check:
- Are all mandatory forms included?
- Are word/page limits respected?
- Is the naming convention correct?
- Are there any blank placeholders (e.g., `[TBC]`, `[INSERT HERE]`, `[HUMAN INPUT REQUIRED]`)?
- Are all signatures and dates present where required?

## Step 3 — Temporal Consistency Check (The "Stale Output" Check)
This is a critical risk check. During the tender period, the authority often issues Q&A answers or Addenda that change the scope or specification.
Ask the user: "Were any Q&A answers or Addenda received during this tender?"
If yes, check the timestamps/dates of the final bid documents.
- If a method statement or pricing document was finalised *before* a relevant Q&A answer was received, flag it as a **STALE OUTPUT RISK**.
- Example: "Warning: The Mechanical Method Statement was drafted on Tuesday, but Q&A #4 (which changed the HVAC spec) was received on Thursday. Has this document been updated?"

## Step 4 — eTenders Portal Checklist
Provide the user with the mandatory eTenders Ireland upload checklist:
- [ ] Are any single files over the 2.14 GB eTenders limit?
- [ ] Is the Form of Tender signed and dated?
- [ ] Are all files named exactly as requested in the ITT?
- [ ] Is there sufficient time before the deadline (typically 12:00 noon or 17:00)? Do not upload at the last minute.

## Step 5 — Present
Provide a Pass/Fail report. If there are any fails, flag them prominently in RED so the user can fix them before uploading to eTenders.

## Anti-Patterns (What NOT to do)
- DO NOT approve the submission if there are RED ALERTS.
- DO NOT skip checking word/page limits if they were specified in the ITT.
- DO NOT ignore missing signatures or dates.

## Quality Checks
- [ ] All mandatory returnables from the Compliance Matrix present.
- [ ] No blank placeholders (`[TBC]`, `[INSERT HERE]`) remaining.
- [ ] Stale output check completed — documents post-date all Q&A answers.
- [ ] eTenders file size limit (2.14 GB per file) checked.
