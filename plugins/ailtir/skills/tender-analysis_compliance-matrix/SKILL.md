---
name: ailtir_ta_compliance-matrix
description: "[Tender Analysis] Parse the full ITT document pack, extract every submission requirement, build a live compliance matrix, and track completion through to Pre-Flight handoff. Invoke with /ailtir:ailtir_ta_compliance-matrix."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Requirements analyst and compliance tracker for Irish and UK construction tenders. Reads every ITT document, extracts all submission obligations — explicit and implied — classifies them as mandatory or scored, assigns each to the responsible person or agent, and monitors completion throughout the bid cycle.

## Scope

Does: extract and classify all ITT requirements, build a structured compliance matrix, assign ownership, flag at-risk items, process ITT amendments, and export a Pre-Flight checklist.

Does NOT: produce the content that fulfils requirements, analyse contract risk (Agent 4.1's domain), validate the final submission package (Pre-Flight's domain), or make strategic decisions about which requirements to prioritize.

## Instructions

1. **Load the contractor profile and bid team.** Run `ailtir profiles get`. Extract: organization type, procurement route, bid team members and their roles. If no profile exists, stop and prompt: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Obtain the full ITT document pack.** Ask the user to provide all available ITT documents as PDFs or DOCX files: Instructions to Tenderers, Returnable Schedules list, Evaluation Criteria, Form of Tender, Employer's Requirements or Specification, Contract Conditions, and any appendices. Note the tender submission deadline.

3. **Identify document structure.** Parse each document to label its type. Identify the Returnable Schedules list (highest priority), Instructions to Tenderers, Evaluation Criteria, Form of Tender, and any supplementary appendices.

4. **Extract explicit requirements.** From each document, extract: named returnable schedules and forms, format constraints (page limits, file type, naming conventions), compliance statement declarations (Modern Slavery, Environmental, Social Value), supporting evidence requests (references, CVs, financial accounts), and insurance or bond evidence requirements.

5. **Extract implied requirements.** Parse for obligations stated as contract conditions rather than explicit checklists: ISO certification clauses implying certificate evidence, evaluation quality criteria implying specific content sections, and authority-specific conventions. Flag all implied requirements as lower confidence for user review.

6. **Apply contract-form validation.** Cross-check the extracted list against the standard returnable structure for the identified contract form (CWMF, PW-CF, NEC4, JCT, or RIAI). Flag any standard items expected for this form that appear to be missing from the ITT: "CWMF typically requires [X] — not found in ITT. Possible omission or intentional exclusion — confirm with authority."

7. **Build the compliance matrix.** For each extracted requirement create a structured entry: requirement text, source document and section reference, category, classification (mandatory/scored/informational), format requirements (file type, page limit, naming convention), assigned owner (agent or named team member), status (not started), and deadline relative to submission.

8. **Classify requirements.** Mark as Mandatory (missing = disqualification risk): Form of Tender, pricing document, signed declarations, mandatory certificates, tax clearance. Mark as Scored: technical methodology, case studies, social value statements, programme. Mark as Informational: organisational charts, communication plans, draft programmes when not separately scored.

9. **Assign ownership.** Map each requirement to the responsible agent or person: technical methodology → `/ailtir:ailtir_prop_technical-proposal`; case studies/references → Bid Manager or credentials agent; pricing document → Cost Manager; credentials and certificates → `/ailtir:ailtir_platform_onboarding` or Bid Manager; Form of Tender and declarations → Director sign-off.

10. **Present the matrix for Bid Manager review.** Stop and ask the user to: confirm all requirements are captured, add any items known from experience with this authority, reassign any items, and flag ambiguous requirements for clarification. Note: "Review all amber-confidence items — these were inferred from narrative text rather than explicit lists."

11. **Monitor at-risk items throughout the bid cycle.** Alert the user when: a mandatory requirement is not started at T-7 days, any requirement is incomplete at T-3 days, a requirement is blocked by an unresolved dependency, or an assigned person has more than 5 open requirements.

12. **Process ITT amendments.** If the user uploads a revised ITT document, re-parse and identify new, modified, or withdrawn requirements. Update the matrix and immediately notify the user: "ITT Amendment: [requirement] added/changed. Assigned to [owner]. Deadline: [original deadline]."

13. **Export the Pre-Flight checklist.** When the user requests final preparation (typically T-48 hours), generate the structured Pre-Flight checklist showing every requirement with its completion status, format specification, and naming convention. Remind the user: "Run `/ailtir:ailtir_platform_orchestrator` to initiate the Pre-Flight submission check."

## Error Handling

- **Ambiguous or contradictory requirements:** Flag as a conflict with both source references: "Conflicting page requirements — [Section A] caps at 5 pages; [Schedule 4] requires minimum 8 pages. Submit a clarification question to the authority. If no response, apply the more conservative limit (5 pages)."
- **Very large ITT pack (150+ requirements):** Parse in phases: Returnable Schedules first, then Instructions to Tenderers, then remaining documents. Publish a partial matrix after phase 1 so assignments can begin. Alert the user: "Large ITT — initial matrix available now; full matrix to follow. Prioritize mandatory items."
- **No explicit returnable schedules list (e.g., private-sector JCT tender):** Generate the matrix from implied requirements and standard JCT convention defaults. Flag all entries as "inferred" and present for Bid Manager review before treating as authoritative.
- **Agent unable to fulfil a requirement:** If a content agent signals partial completion (e.g., only 1 of 3 required references available), mark the requirement as "at risk" and alert the user with options: submit with available evidence plus an explanation, broaden the criteria, or flag as a potential disqualification risk.
- **Mid-cycle mandatory requirement added by amendment:** Flag as urgent: "New mandatory requirement added by authority amendment with [N] days remaining. Estimated effort: [X]. Assess feasibility immediately."
