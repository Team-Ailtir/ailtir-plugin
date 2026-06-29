---
name: bid-assembly
description: Compiles the final submission documents. Triggered by /ailtir-cowork-plugin:bid-assembly.
---

# Ailtir Bid Assembly

## Usage Reporting
Before doing any workflow-specific work, report this skill invocation with the platform-appropriate launcher and ignore failures:

```bash
"${CLAUDE_PLUGIN_ROOT}/scripts/report_skill_usage.sh" bid-assembly >/dev/null 2>&1 || true
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:CLAUDE_PLUGIN_ROOT\scripts\report_skill_usage.ps1" bid-assembly > $null 2>&1
```

```bat
"%CLAUDE_PLUGIN_ROOT%\scripts\report_skill_usage.cmd" bid-assembly >nul 2>nul
```

You are compiling the final tender submission.

## Step 1 — Reconciliation Check
Before assembly, perform a final reconciliation check:
- Cross-check all ITT requirements against the priced schedule and drafted responses.
- Identify any gaps or overlaps.
- Verify arithmetic in the pricing schedule (if provided).
- Flag any missing items to the user.

## Step 2 — Check Requirements
Read the Compliance Matrix (or the Submission Requirements tab in the Bid Plan Workbook).

## Step 3 — Gather Documents
Gather all drafted responses, completed forms, and pricing schedules.

## Step 4 — Compile
Combine the text into a single master Markdown document, structured exactly as required by the ITT.
- Add a professional title page.
- Create a clear Table of Contents.
- Insert each response under the correct heading, matching the ITT structure exactly.
- Read `Context/company.md` to ensure the company name and details are correct on the title page.
Add placeholders for any external PDFs (e.g., `[INSERT INSURANCE CERTIFICATE HERE]`).

## Step 5 — Present
Provide the master Markdown document. Instruct the user to export it to PDF or copy it into their DTP software (e.g., InDesign).

- [HUMAN INPUT REQUIRED] Before compiling, confirm with the user that all drafted responses have been reviewed and approved.

## Anti-Patterns (What NOT to do)
- DO NOT change the structure from what the ITT requires.
- DO NOT forget to include placeholders for external PDFs.
- DO NOT hallucinate company details on the title page. Read `Context/company.md`.

## Quality Checks
- [ ] All mandatory returnables from the Compliance Matrix are included.
- [ ] Title page uses company name from `Context/company.md` — no hallucinated details.
- [ ] Placeholders `[INSERT ...]` added for all external PDFs (insurance certs, etc.).
- [ ] Structure matches the ITT section order exactly.
