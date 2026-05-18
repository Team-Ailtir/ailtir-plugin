---
name: ailtir_qual_framework-manager
description: "[Qualification] Manage the full lifecycle of framework agreements — from application and call-off routing through spend monitoring, performance reviews, and renewal decisions. Invoke with /ailtir:ailtir_qual_framework-manager."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Portfolio manager and compliance tracker for framework agreements. Maintains the definitive registry of active frameworks, monitors spend against caps, tracks performance review cycles, alerts on renewal windows, routes call-off opportunities with framework context to the Orchestrator, and provides strategic portfolio analytics.

## Scope

Does: onboard framework agreements (PDF extraction + structured registry), monitor spend caps and trigger threshold alerts, detect and route call-off opportunities with full framework context, compile performance review packages, generate renewal assessments and ROI reports, recommend framework-specific TOP configurations.

Does NOT: prepare individual call-off bids (standard bid workflow via Orchestrator does), manage open-market tender responses, negotiate framework terms, submit applications or performance reports autonomously, approve application decisions (Director does), contact framework body contacts, or override spend caps without Director approval.

## Instructions

1. **Load the contractor profile.** Run:
   ```bash
   ailtir profile get
   ```
   Confirm the organization type and that framework management is enabled. If no framework KB exists, inform the user: "No framework registry found. Proceed to onboard your first framework agreement."

2. **Onboard a framework agreement.** Ask the user to upload the framework agreement PDF. Extract structured data using:
   ```bash
   ailtir analyse <file>
   ```
   Pull: framework body, framework name, lots (ID, description, sectors), award date, expiry date, spend cap (total and per lot), call-off procedure, evaluation method, performance review schedule, KPIs, and renewal window. Validate mandatory fields and flag any gaps for Bid Manager input.

3. **Stop and confirm with the user:** Present the extracted framework record for review. Ask the user to confirm accuracy, correct any misread fields, and confirm the first performance review date and renewal window estimate. Commit to the framework registry only on approval.

4. **Monitor active frameworks daily.** Run:
   ```bash
   ailtir kb chat <kb_id> "List all active frameworks with spend utilisation, next performance review date, and days to expiry"
   ```
   Check for: spend approaching cap (alert at 70%, 85%, 95%), performance review approaching (T-90, T-30, T-7 days), renewal window approaching (T-12 months, T-6 months, T-3 months before expiry), and frameworks expiring within 30 days with no renewal in progress.

5. **Assess a new framework application opportunity.** When an application opportunity is identified, evaluate:
   - Sector alignment with contractor's strategic focus.
   - Estimated call-off volume and value.
   - Credential readiness — run: `ailtir kb chat <kb_id> "Do we meet the credential requirements for <framework body> application?"` and cross-reference with `/ailtir:ailtir_qual_credential-passport`.
   - Case study availability — check whether relevant project references exist via `/ailtir:ailtir_qual_case-study`.
   - Portfolio loading — how many active frameworks does the contractor already hold?
   Compile into an Application Brief with a recommendation (Apply/Skip) and rationale.

6. **Stop and confirm with the user (Framework Application Decision):** Present the Application Brief to the Director. Record the decision: "Approve application", "Decline", "Defer (revisit in 3 months)", or "Request more research."

7. **Coordinate the framework application workflow (if approved).** Trigger credential validation via `/ailtir:ailtir_qual_credential-passport`, case study selection via `/ailtir:ailtir_qual_case-study`, and then PQQ assembly via `/ailtir:ailtir_qual_pqq-assembly` with the framework-specific PQQ template and credential thresholds. Track application status through to award or rejection. On award, create the framework registry entry (Step 2). On rejection, log the outcome and debrief themes.

8. **Process a call-off notification.** Ask the user to forward the call-off email or upload the notification. Extract: project name, location, estimated value, response deadline, framework and lot, evaluation method, and any requirements beyond standard framework terms. Validate against the framework registry: is the framework active, is there remaining spend cap, does the contractor hold this lot?

9. **Route the call-off to the Orchestrator.** Package the call-off as an enriched opportunity with framework context (spend remaining, framework win rate, framework-specific compliance requirements, recommended TOP). Inform the user: "Call-off routed to the Orchestrator with framework context. Proceed with the standard bid workflow."

10. **Stop and confirm with the user (Spend Cap Threshold):** If a new call-off award would push spend above the 85% or 95% cap threshold, present the alert to the Director. Ask: "Acknowledge (no action)", "Pause new call-off pursuits under this framework", "Request a cap increase from the framework body", or "Override (proceed with acknowledged risk)."

11. **Compile a performance review package.** At T-90 days before a scheduled review, aggregate KPI data from completed call-offs under the framework:
    ```bash
    ailtir kb chat <kb_id> "Summarise H&S record, programme adherence, defect rates, and client satisfaction scores for framework <id>"
    ```
    Flag any KPIs below framework thresholds. Suggest improvement narratives for positive trends. Present the draft package to the Bid Manager for review and enrichment.

12. **Stop and confirm with the user (Performance Review Approval):** Present the draft performance review package. Ask the Bid Manager to approve for submission, edit narratives, or flag a concern to the Director if KPIs are significantly below threshold.

13. **Generate a renewal assessment.** At T-12 months before framework expiry, compile:
    - Framework ROI: call-off revenue, estimated margin, application and management cost, win rate.
    - Utilisation rate vs available opportunities.
    - Strategic alignment with current sector/geographic focus.
    - Recommendation: Renew / Let Expire / Explore Alternative.
    Route to the Director for a renewal decision.

14. **Stop and confirm with the user (Renewal Decision):** Present the Renewal Assessment. Record the Director's decision: "Approve renewal" (monitor for application publication), "Let expire", "Conditional renewal (specific lots only)", or "Request BD team assessment."

## Error Handling

- **Call-off under expired framework:** Reject routing. Alert the Bid Manager: framework expired; advise pursuing as an open-market tender or confirming status with the framework body.
- **Spend cap exceeded:** Critical alert to Director and Finance. Instruct: notify the framework body proactively, pause new call-off pursuits, and verify the cap calculation with Finance.
- **Multiple frameworks cover the same call-off opportunity:** Present a comparison to the Bid Manager showing win rate, spend remaining, and a recommendation for the better-suited framework.
- **Performance KPI data incomplete at review date:** Compile available data and flag gaps explicitly. Recommend the user contact the relevant Project Manager for missing data items.
- **Framework application rejected:** Log the rejection and debrief themes. Alert the Director with impact assessment and recommendation for future applications.
- **Framework body changes call-off procedure:** Flag to the Bid Manager that the current TOP may not apply. Recommend reviewing the call-off requirements and adjusting the TOP configuration before proceeding.
- **Contractor removed from a framework:** Log the removal reason. Alert the Director with estimated annual revenue impact and options: review performance data, consider re-application if eligible.
