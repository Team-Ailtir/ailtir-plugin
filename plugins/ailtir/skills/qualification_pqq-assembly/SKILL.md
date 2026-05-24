---
name: ailtir_qual_pqq-assembly
description: "[Qualification] Orchestrate credential responses and case study narratives into a complete, compliance-checked PQQ submission package ready for Bid Manager review. Invoke with /ailtir:ailtir_qual_pqq-assembly."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Deterministic orchestration module that combines credential evidence from the Credential Passport and case study narratives from the Case Study agent into a submission-ready PQQ response package. Coordinates outputs, ensures format compliance with the authority's PQQ template, and validates completeness before Bid Manager sign-off.

## Scope

Does: parse PQQ templates to classify sections, route sections to the correct source (credentials, case studies, compliance statements), merge outputs into the PQQ structure, compile evidence bundles with naming conventions, run a pre-submission compliance check (RED/AMBER/GREEN per section), and present the complete package for Bid Manager review.

Does NOT: select which credentials to present (the Credential Passport agent does), choose which projects to reference (the Case Study agent does), draft case study narratives, perform contract risk analysis, make Go/No-Bid decisions, submit the PQQ to the authority portal, or override expired credentials without Director approval.

## Instructions

1. **Load the bid context.** Run:
   ```bash
   ailtir profiles get
   ailtir kbs list
   ```
   Confirm the active opportunity, submission deadline, procurement route, and available KBs. If a bid context is missing, ask the user to provide the opportunity details before proceeding.

2. **Obtain the PQQ template.** Ask the user to upload or paste the authority's PQQ/ESPD template. Parse the structure to identify all sections, question types, word/page limits, and file format requirements. Classify each section:
   - Credential proof → Credential Passport (`/ailtir:ailtir_qual_credential-passport`)
   - Project references → Case Study (`/ailtir:ailtir_qual_case-study`)
   - Compliance statements (H&S policy, environmental statement, modern slavery) → Knowledge Domain 1
   - Financial standing → Credential Passport + manual input
   - Methodology/approach → Manual (Bid Manager)

3. **Run the Credential Passport skill first.** Inform the user: "Run `/ailtir:ailtir_qual_credential-passport` to validate credentials against the CPV codes for this bid and retrieve auto-populated credential responses. Return here once complete."

4. **Run the Case Study skill next.** Inform the user: "Run `/ailtir:ailtir_qual_case-study` to select projects and generate tailored narratives for this PQQ. Return here with the approved project package once complete."

5. **Retrieve compliance statements.** Query the corporate credentials KB for approved standard text:
   ```bash
   ailtir kbs chat <kb_id> "Retrieve the current H&S policy statement, environmental management statement, and modern slavery declaration with their last-updated dates"
   ```
   Flag any statement last updated more than 12 months ago as AMBER. Flag any statement more than 24 months old as RED and block inclusion until refreshed — escalate to the Compliance Lead.

6. **Assemble the PQQ response document.** Merge all inputs into the PQQ structure:
   - Insert credential responses into credential sections; attach credential PDFs.
   - Insert tailored project narratives into project reference sections; attach evidence bundles.
   - Insert compliance statements into the relevant sections.
   - Insert any route-specific content required by the procurement route (e.g., CWMF insurance attestation, NEC4 early-warning procedure description).
   - Check each section against word/page limits. Flag overages with specific counts.

7. **Compile the evidence bundle.** Collect all attachments from both upstream skills. Apply the authority's file naming convention. Generate a manifest listing every file mapped to its PQQ section. Deduplicate files attached to multiple sections.

8. **Run the pre-submission compliance check.** Verify:
   - All mandatory sections are populated.
   - All required documents are attached.
   - All credentials are `ACTIVE` (not expired).
   - No credential expires before the likely contract award date (submission deadline + 6 months).
   - All file sizes are within the portal's upload limit.
   - All word/page counts are within limits.
   - All compliance statements are current (within 12 months).
   Output a RED/AMBER/GREEN status per section with remediation instructions for every non-GREEN item.

9. **Stop and confirm with the user (Project Selection Review):** Present the ranked project candidates from the Case Study skill with fit scores and rationale. Confirm the pre-selected 3 projects or allow the user to swap individual projects. For consultant OrgProfiles, review proposed team CVs instead of project references.

10. **Stop and confirm with the user (PQQ Draft Review):** Present the complete assembled PQQ draft (editable), the compliance status panel, credential expiry flags, and the evaluation criteria alignment report. The Bid Manager may: approve as-is, edit specific sections, request a narrative revision from the Case Study skill (triggers a re-run), flag a credential issue (triggers the Credential Passport skill), or update a compliance statement.

11. **Stop and confirm with the user (Final Package Sign-Off):** Once the Bid Manager approves, present the final submission-ready package with the evidence manifest and the pre-submission compliance report. If any RED compliance items remain, escalate to the Director before proceeding. The Bid Manager signs off to route the package to the Pre-Flight check.

12. **Deliver the final package.** Produce: completed PQQ form (PDF), all credential attachments, all project evidence bundles, compliance statement documents, and file manifest. Inform the user: "Package is ready. Submit via the procurement portal or run the Pre-Flight workflow."

## Error Handling

- **Credential Passport returns an expired credential:** RED flag on the affected section. Ask the Bid Manager to choose: exclude the section with a "renewal pending" note, escalate to the Director for override, or defer the submission until renewed.
- **Case Study skill returns no projects with fit score above 50:** AMBER alert. Present best-available projects with a caveat. Recommend the Bid Manager reviews the Go decision.
- **PQQ template not parseable (confidence below 60%):** Fall back to manual mode. Present the raw template to the Bid Manager with a form to classify each section manually. Log the pattern for future use.
- **Word/page limit exceeded:** AMBER flag with exact overage count. Offer: regenerate a shorter narrative, manually trim, or proceed with the overage at acknowledged risk.
- **Evidence documents missing from Case Study package:** AMBER flag. Ask user to locate the document, swap to an alternative project, or proceed without (noting the risk).
- **Either upstream skill times out:** Present partial results from the skill that completed. Alert the user to wait and retry, fill gaps manually, or escalate to support.
- **Parallel PQQs to same authority:** Alert the Bid Manager to ensure consistent credential versions and different project references across both submissions. Cross-reference with the Credential Passport's multi-draft tracking.
- **Total package size exceeds portal limit:** Flag with current and maximum sizes. Suggest compressing PDFs, reducing photo resolution, or contacting the authority for guidance.
