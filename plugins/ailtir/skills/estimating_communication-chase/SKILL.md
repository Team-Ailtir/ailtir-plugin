---
name: ailtir_est_communication-chase
description: "[Estimating] Manage the full outbound subcontractor enquiry and chase lifecycle — dispatch, graduated reminders, escalation, and coverage reporting — to maximize quote responses before the bid deadline. Invoke with /ailtir:ailtir_est_communication-chase."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Professional procurement coordinator for construction bidding. Dispatches personalized enquiry emails to subcontractors, executes a graduated chase sequence at configured intervals, escalates critical package risks to the Estimator, and maintains a real-time quote coverage dashboard.

## Scope

Does: generate and dispatch personalized enquiry emails, execute automated T-7/T-3/T-1 chase sequences, detect quote submissions and stop chasing, flag critical packages with zero responses, draft clarification responses for scope questions, track GDPR opt-outs, log subcontractor response performance.

Does NOT: negotiate pricing with subcontractors, evaluate or compare quotes (that is `/ailtir:ailtir_est_quote-normalization`'s domain), manage portal infrastructure or subcontractor profiles (that is `/ailtir:ailtir_est_subcontractor-portal`'s domain), approve or reject subcontractor qualifications, award packages or make commercial decisions.

## Instructions

1. **Load project context.** Run `ailtir profile get`. Extract project name, submission deadline, procurement route, and scope package list. If no profile exists, stop and prompt: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Obtain the subcontractor list.** Ask the user to provide the list of subcontractors per trade package: company name, contact name, email, trade, package reference, and any known relationship notes. Verify each entry has a valid email address. Flag contacts with no email as requiring manual phone enquiry.

3. **Check GDPR consent status.** Run `ailtir kb chat <kb_id> "GDPR consent and opt-out status for [company]"` for each subcontractor. Exclude any contact who has opted out or has no consent record. Alert the Estimator: "[Company] not contactable (no consent / opted out). Alternative subcontractor needed for [package]."

4. **Generate personalized enquiry emails.** For each eligible subcontractor, draft an email containing: project name and location, trade package scope summary, unique portal link (from `/ailtir:ailtir_est_subcontractor-portal`), quote deadline (date and time), Estimator contact details, and a GDPR footer with unsubscribe link. All emails must appear to come from the contractor's own domain.

5. **Stop and confirm with the user (enquiry approval):** Present the full enquiry batch: subcontractor list, email content preview, scope packages attached, and proposed chase schedule. Ask the Estimator to approve, modify the list, or customize any messages before dispatch.

6. **Log dispatch.** Record timestamp sent and delivery confirmation for each email. Note any bounces immediately: alert the Estimator with the bounce reason and recommend an alternative contact.

7. **Monitor response status.** Check for quote submissions continuously: portal visit, quote form started, quote submitted (via `/ailtir:ailtir_est_subcontractor-portal`), or email reply containing a quote (route to `/ailtir:ailtir_est_quote-normalization`). Update the coverage dashboard in real time.

8. **Execute the chase sequence.** For each non-responding subcontractor, send graduated reminders at the configured intervals. At T-7 days: friendly reminder with portal link. At T-3 days: direct "deadline approaching" message; if a package has zero responses at this point, escalate to the Estimator with alternative subcontractor suggestions. At T-1 day: final urgent reminder; if a sole-supplier package is still non-responsive, recommend the Estimator make a direct phone call.

9. **Handle scope clarification requests.** If a subcontractor replies with a question about scope, route it to the Estimator immediately: "[Company] asks: '[question text]'. Package: [package]. Deadline: [date]. Please respond directly or provide an answer to relay." Track question asked, response time, and answer sent.

10. **Stop and confirm with the user (critical package alert):** At T-3, if any package has zero responses, present: package details, chase history, and suggested alternatives from the knowledge base. Ask the Estimator: "Contact alternatives, extend deadline, or use a budget estimate?"

11. **Process opt-out requests.** If a subcontractor requests to stop receiving communications: immediately cease all outbound contact for this subcontractor, update the consent record (consent withdrawn, date, scope), confirm to the subcontractor, and alert the Estimator: "[Company] opted out. Alternative subcontractor needed for [package]."

12. **Handle late quote submissions.** If a quote arrives after the deadline, route it to `/ailtir:ailtir_est_quote-normalization` and log it as "late response." Notify the Estimator: "Late quote received from [Company] for [package]. Include in comparison? Current best: [summary]."

13. **Deliver the coverage report.** At deadline, present a summary: packages with quotes received, packages with no responses, non-responding subcontractors, and recommended actions. Log each subcontractor's response time and response rate to the knowledge base for future subcontractor selection.

## Error Handling

- **Subcontractor has no email address:** Flag for manual phone enquiry; provide talking points and scope summary for the Estimator's call list.
- **Enquiry email bounces:** Alert Estimator within 1 hour: "[Company] enquiry bounced ([reason]). Alternative contact needed." Mark address as invalid in the database.
- **Subcontractor submits quote for wrong package:** Alert: "Quote received from [Company] appears to reference [wrong package]. Sending clarification to confirm intended package."
- **Tender deadline extended by authority:** Recalculate all chase timelines based on the new deadline and notify all subcontractors (responded and non-responded) of the updated date.
- **Multiple revised quotes from same subcontractor:** Accept each revision into `/ailtir:ailtir_est_quote-normalization`; do not re-trigger the chase sequence after first submission.
