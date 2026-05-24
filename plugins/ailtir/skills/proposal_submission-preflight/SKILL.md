---
name: ailtir_prop_submission-preflight
description: "[Proposal] Run a deterministic compliance audit of the assembled tender package against the ITT Returnable Schedules list, block on any RED finding, and gate submission until the Bid Coordinator signs off. Invoke with /ailtir:ailtir_prop_submission-preflight."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Deterministic compliance validation workflow that audits the assembled tender package before portal submission. Performs rule-based checks (file presence, format, naming, signatures, tracked changes, addenda acknowledgement, file size, cross-document consistency) and blocks submission until every RED item is resolved and the Bid Coordinator explicitly signs off.

## Scope

Does: inventory the package against the Returnable Schedules list, check file format and size, detect tracked changes and draft watermarks, verify signature blocks, confirm addenda acknowledgement, run cross-document consistency spot-checks, produce a GREEN/AMBER/RED compliance report, support remediation loops, and log an immutable sign-off record.

Does NOT: write or edit content, assemble or format documents (Agent 6.3 does that), build the compliance checklist (Agent 4.3 does that), analyse contract risk, make Go/No-Bid decisions, upload to the portal, or override RED items — only the Director can approve submission with unresolved RED flags.

## Instructions

1. **Load the organisation profile.** Run `ailtir profiles get`. If missing, stop: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Confirm the package is ready.** Ask the user to confirm: (a) the assembled submission package is in the bid workspace (output from `/ailtir:ailtir_prop_doc-assembly`), (b) the Returnable Schedules list is available (from the ITT compliance matrix), and (c) the submission deadline and target portal are known.

3. **Inventory check.** Scan every file in the submission package against the Returnable Schedules list. For each required schedule: check file presence (missing = RED), naming convention match (deviation = AMBER), file type compliance (wrong format = RED), per-file size limit (exceeded = RED), and page count against ITT page limit (exceeded = AMBER).

4. **Signature verification.** For each signable document in the Signature Requirements Matrix: check for a signature block (missing = RED), verify the signatory role matches the ITT requirement (wrong role = AMBER), and confirm the attestation text matches (mismatch = AMBER). Stop and confirm with the user if the signature requirements list was entered manually rather than loaded from the compliance matrix.

5. **Tracked changes and watermark detection.** Scan all Word documents for tracked changes or comments (any found = RED: "Accept all changes and delete all comments before re-scanning"). Scan all PDFs for DRAFT, INTERNAL, or CONFIDENTIAL watermarks (any found = RED: "Regenerate clean final version").

6. **Addenda acknowledgement check.** If addenda were issued during the tender period, scan the Cover Letter and Compliance Statement for an acknowledgement statement (missing = RED: "Add acknowledgement listing all addenda received").

7. **Cross-document consistency spot-checks.** Run soft checks (AMBER, not blockers): financial summary total versus detailed breakdown, programme duration versus resource plan duration, H&S Plan site address versus ITT project definition, company name consistency across all documents. Flag any mismatch for the Bid Manager's awareness.

8. **Total package size check.** Sum all file sizes. If total exceeds the portal upload limit, flag as AMBER. If it exceeds the limit by more than 20%, escalate as RED.

9. **Generate the compliance report.** Produce an itemised checklist with GREEN/AMBER/RED status per document, evidence for each finding (file path, size, format detected), and step-by-step remediation instructions for every non-GREEN item. Report the overall package status as the worst-case item. Stop and confirm with the user: "Pre-Flight report ready. [N] RED, [M] AMBER, [X] GREEN. Review findings."

10. **Remediation loop.** For each RED or AMBER item, route the fix to the appropriate owner: tracked changes to the document author, missing documents to the assigned owner from the compliance matrix, format issues to `/ailtir:ailtir_prop_doc-assembly`, signature issues to the named signatory. After fixes are applied, trigger a re-scan. Repeat up to 5 cycles. If 3 or more cycles complete without reaching GREEN, escalate to the Bid Manager.

11. **Bid Coordinator sign-off.** When the package reaches GREEN (or AMBER-only with documented rationale for each accepted item), stop and confirm with the user: "Pre-Flight status: [status]. Confirm: 'I confirm this package is compliant and ready for submission.' For each accepted AMBER item, document the rationale." Log the sign-off record with timestamp and approver identity.

12. **Block sign-off on RED status.** If the user attempts to sign off with any unresolved RED items, block and state: "Pre-Flight status is RED. [N] critical issues must be resolved before submission. Director override required to proceed with unresolved RED items."

13. **Issue portal upload instructions.** Provide the Bid Coordinator with the portal-specific upload checklist (from the assembly manifest): portal URL, file upload order, and any portal-specific requirements (e.g., individual files for eTenders).

14. **Log submission confirmation.** After the Bid Coordinator completes the upload, ask them to provide the portal confirmation reference number and timestamp. Log the submission record to the bid workspace and note: "Bid status updated to Submitted."

## Error Handling

- **Required file missing:** RED — block submission: "CRITICAL: Required document [schedule name] missing. Assigned owner: [name]. Contact immediately."
- **File corrupted or unreadable:** RED — "Regenerate from source and retry. If persistent, contact `/ailtir:ailtir_prop_doc-assembly` to re-assemble."
- **Multiple versions of the same document detected:** AMBER — "Multiple versions of [document] detected: [file1] (modified [date1]), [file2] (modified [date2]). Confirm which version to submit and remove the other."
- **Tracked changes in a Word document:** RED — "Tracked changes detected in [filename] ([N] changes, [M] comments). Accept all changes and delete all comments. Route to document author."
- **Draft watermark in a PDF:** RED — "Draft watermark detected in [filename]. Regenerate clean final PDF."
- **Addenda not acknowledged:** RED — "Addenda acknowledgement missing. [N] addenda issued. Add acknowledgement statement to Cover Letter."
- **Scan initiated with fewer than 4 hours to deadline:** Warn the user: "Submission deadline is in [X] hours. Prioritise RED items only if time is short."
- **Compliance matrix unavailable (MVP):** Fall back to manual schedule entry via the user. Flag: "Manual schedule entry — may be incomplete. Double-check against ITT before sign-off."
- **Excel file contains hidden sheets:** AMBER — "Hidden sheet(s) detected: [sheet names]. Review and delete internal notes before submission."
- **Portal does not return a confirmation receipt:** AMBER — "Submission logged as Pending Confirmation. Check the portal's Submitted Tenders page, save a screenshot, and email the authority to confirm receipt."
