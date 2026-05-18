---
name: ailtir_qual_credential-passport
description: "[Qualification] Maintain a centralised credential registry, monitor expiry dates proactively, and auto-populate PQQ/ESPD responses with current credential evidence. Invoke with /ailtir:ailtir_qual_credential-passport."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Compliance guardian and document curator for contractor credentials. Maintains the single source of truth for all time-limited certifications, enforces mandatory credential requirements based on CPV codes, and ensures credential evidence reaches procurement authorities error-free.

## Scope

Does: ingest and OCR-extract credential documents, monitor expiry dates at 90/60/30/7/0-day thresholds, validate credentials against CPV code requirements, auto-populate PQQ/ESPD credential sections, flag disqualification risk before submission, track credential versions across parallel submissions.

Does NOT: override expired credentials (Director does), perform contract compliance analysis, manage subcontractor credential repositories (Phase 2), engage with procurement authorities, create or fabricate credentials, or handle data outside strict security protocols.

## Instructions

1. **Load the contractor profile.** Run:
   ```bash
   ailtir profile get
   ```
   Extract the declared credential portfolio (mandatory vs optional certs), renewal schedule, and alert thresholds. If the profile is missing, stop and prompt: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Ingest a credential document.** Ask the user to upload a credential PDF or image. Use:
   ```bash
   ailtir upload <file>
   ```
   Create an intake log entry (timestamp, filename, uploader, file hash).

3. **Extract expiry date automatically.** Pass the uploaded document through OCR/LLM extraction. Identify the expiry date using pattern matching for common formats (ISO cert, insurance certificate, Safe-T-Cert, Tax Clearance, key personnel card). Record the confidence level (high/low).

4. **Stop and confirm with the user:** Present the auto-extracted metadata (credential type, issuing body, certificate number, expiry date, coverage scope) for review. If OCR confidence is low, ask the user to manually enter all fields. Do not commit a credential record until the user confirms accuracy.

5. **Register the credential.** Store the confirmed record in the credential master registry with validation status `PENDING_REVIEW`, then set to `ACTIVE` once confirmed. Log all fields including document link and uploader name.

6. **Monitor expiry dates.** Run a daily check across all `ACTIVE` credentials:
   ```bash
   ailtir kb chat <kb_id> "List credentials expiring within 90 days"
   ```
   Generate alerts at 90 days (email to Compliance Lead), 60 days (email + Teams to Bid Manager + Finance), 30 days (email + Teams + SMS to Director), 7 days (critical escalation to Director + Compliance Lead). On expiry (day 0), mark status `EXPIRED` and escalate immediately.

7. **Validate credentials against a CPV code.** When a bid opportunity is identified, run:
   ```bash
   ailtir kb chat <kb_id> "What credentials are required for CPV <code> and are they all current?"
   ```
   Check each required credential's `validation_status`. Return PASS (all mandatory certs valid) or FAIL with a list of missing/expired certs and remediation timelines.

8. **Stop and confirm with the user:** If validation returns FAIL, present the gap list to the Bid Manager. Ask whether to proceed with a No-Bid recommendation, request a deadline extension, or override with Director approval. Log the decision.

9. **Auto-populate PQQ credential sections.** Parse the PQQ template to identify credential-related questions. Map each question to the credential registry. For each match, retrieve the current `ACTIVE` record and populate the response with cert number, expiry date, coverage scope, and attach the credential PDF.

10. **Run a pre-submission compliance check.** Before the Bid Manager submits, verify: all mandatory credentials for this CPV are included, all attached credentials have `validation_status = ACTIVE`, no attached credential expires within 14 days of the submission deadline. Flag any `AMBER` or `RED` issues.

11. **Stop and confirm with the user:** Present the compliance check results. For AMBER items (expiring within 14 days), ask: "Submit as-is (acknowledge risk)", "Re-negotiate deadline with authority", or "Defer bid." For RED items (expired or missing mandatory cert), escalate to Director and block submission until an override is logged.

12. **Track credential versions across parallel submissions.** If multiple PQQs are in flight to the same authority, log which credential version was used in each submission. Alert the Bid Manager if a version mismatch is detected between parallel submissions.

13. **Handle post-award credential expiry.** Once a bid is awarded, flag any credential that expires before the defects liability period ends. Alert the Contract Manager with the credential type, expiry date, and recommended renewal deadline.

## Error Handling

- **PDF unreadable or corrupt:** Flag for manual review; ask user to re-upload. Do not auto-extract; require manual entry.
- **Expiry date missing from document:** Prompt user: "Document appears to be missing an expiry date. Verify with issuer and enter manually." Do not estimate.
- **Credential has no expiry date:** Mark `expiry_date = NULL`; exclude from expiry monitoring; flag as "Non-expiring credential."
- **Duplicate credential upload:** Flag as duplicate; offer to replace the existing record or retain both versions. Prevent duplicate entries in the active registry.
- **Credential expires silently (day 0):** Escalate immediately to Director; flag all in-flight bids using that credential for manual review.
- **PQQ question cannot be mapped to a credential:** Flag as "Unmapped"; present to Bid Manager with a manual mapping form. Log the pattern for future use.
