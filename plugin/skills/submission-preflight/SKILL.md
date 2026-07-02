---
name: ailtir:submission-preflight
description: Runs final deterministic compliance checks before submission, targeting the portal appropriate to the active Ailtir profile (Irish eTenders or UK Find a Tender / Contracts Finder). Triggered by /ailtir-cowork-plugin:submission-preflight.
---

# Ailtir Submission Pre-Flight

You are running the final checks before the bid is submitted to the contracting authority.

## Step 1 — Read the Profile
Read `Context/profile.json` from the workspace root. If it is missing, stop and tell the user to run `/ailtir-cowork-plugin:setup`. The portal-specific checks in Step 4 depend on `profile_key`.

## Step 2 — Review the Master Document
Read the assembled master submission document.

## Step 3 — Check against ITT
Cross-reference against the Compliance Matrix.
Check:
- Are all mandatory forms included?
- Are word/page limits respected?
- Is the naming convention correct?
- Are there any blank placeholders (e.g., `[TBC]`, `[INSERT HERE]`, `[HUMAN INPUT REQUIRED]`)?
- Are all signatures and dates present where required?
- **Under `uk-gc`, central government contracts:** is the Carbon Reduction Plan (PPN 06/20) attached where required? Is the Social Value response (PPN 06/21) present and addressing the specified MACs? Is the Modern Slavery statement referenced?

## Step 4 — Temporal Consistency Check (The "Stale Output" Check)
This is a critical risk check. During the tender period, the authority often issues Q&A answers or Addenda that change the scope or specification.
Ask the user: "Were any Q&A answers or Addenda received during this tender?"
If yes, check the timestamps/dates of the final bid documents.
- If a method statement or pricing document was finalised *before* a relevant Q&A answer was received, flag it as a **STALE OUTPUT RISK**.
- Example: "Warning: The Mechanical Method Statement was drafted on Tuesday, but Q&A #4 (which changed the HVAC spec) was received on Thursday. Has this document been updated?"

## Step 5 — Portal Checklist

**Under `ireland-gc` — eTenders Ireland:**
- [ ] Are any single files over the 2.14 GB eTenders limit?
- [ ] Is the Form of Tender signed and dated?
- [ ] Are all files named exactly as requested in the ITT?
- [ ] Is there sufficient time before the deadline (typically 12:00 noon or 17:00 Irish time)? Do not upload at the last minute.

**Under `uk-gc` — Find a Tender / Contracts Finder / Constructionline / private portal:**
- [ ] Are any single files over the portal's per-file limit? (Find a Tender allows up to 50 MB per file by default; check the notice for the specific configuration.)
- [ ] Is the Form of Tender / Certificate of Bona Fide Tender signed and dated?
- [ ] Are all files named exactly as requested in the ITT? Note that UK ITTs often prescribe a strict naming convention including bid reference and section number.
- [ ] Under Procurement Act 2023: has the tender response been submitted via the buyer's e-tendering platform (Delta, Jaggaer, Proactis, In-tend, or Bravo Solutions are the common ones)?
- [ ] Are Carbon Reduction Plan and Social Value / Modern Slavery attachments included where required?
- [ ] Is there sufficient time before the deadline (UK deadlines are commonly 12:00 or 17:00 UK time — check the notice)? Do not upload at the last minute.

## Step 6 — Present
Provide a Pass/Fail report. If there are any fails, flag them prominently in RED so the user can fix them before uploading.

## Anti-Patterns (What NOT to do)
- DO NOT approve the submission if there are RED ALERTS.
- DO NOT skip checking word/page limits if they were specified in the ITT.
- DO NOT ignore missing signatures or dates.
- DO NOT apply Irish portal limits to a UK submission or vice versa.

## Quality Checks
- [ ] `Context/profile.json` read; correct portal checklist applied.
- [ ] All mandatory returnables from the Compliance Matrix present.
- [ ] No blank placeholders (`[TBC]`, `[INSERT HERE]`) remaining.
- [ ] Stale output check completed — documents post-date all Q&A answers.
- [ ] Portal-specific file-size and naming checks completed for the active profile.
- [ ] Under `uk-gc` central government: CRP, Social Value, and Modern Slavery attachments confirmed where required.
