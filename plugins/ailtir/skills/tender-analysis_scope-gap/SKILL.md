---
name: ailtir_ta_scope-gap
description: "[Tender Analysis] Cross-reference specification, BOQ, and drawings to identify scope gaps and draft prioritized clarification questions for QS review. Invoke with /ailtir:ailtir_ta_scope-gap."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Specification and BOQ analyzer for Irish construction procurement. Cross-references tender documents to identify missing items, ambiguous requirements, and discrepancies between the specification, Bill of Quantities, and drawings, then drafts clarification questions for submission to the employer.

## Scope

Does: ingest specification and BOQ documents, detect gaps and ambiguities, cross-reference drawing references, estimate financial impact of gaps, prioritize findings against contract risk context, and draft clarification questions.

Does NOT: make Go/No-Bid decisions, modify BOQ line items or pricing, draft contract amendment language, assess technical feasibility, or interpret drawings without text specification support.

## Instructions

1. **Load the contractor profile.** Run `ailtir profile get`. Extract: project sector, organization type. If no profile exists, stop and prompt: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Obtain the tender documents.** Ask the user to provide: (required) the specification PDF and BOQ PDF; (optional) the drawings package as a list of PDF sheets. Also ask for basic project metadata: project type, contract value, and programme duration.

3. **Check for contract risk findings.** Ask: "Have you already run Contract Risk analysis on this tender? If so, please paste or upload the flagged risk items — this will help prioritize the scope gap investigation." If risk findings are provided, note the high-priority areas (e.g., extended defects liability → prioritize durable finishes spec; restricted variations → prioritize ambiguous scope items).

4. **Extract and structure the specification.** Parse the specification PDF, identify section headings (Structure, Finishes, MEP, External Works, etc.), and map each section to the standard construction work phases.

5. **Extract and structure the BOQ.** Parse the BOQ, identify trade sections, line item descriptions, and quantities. Normalize descriptions to standard construction taxonomy using fuzzy matching where needed.

6. **Run Specification vs. BOQ gap detection.** For each specification section, verify corresponding BOQ line items exist. Flag: (a) specification sections with no BOQ coverage ("Spec Section [X] requires mechanical ventilation with heat recovery — no corresponding BOQ line found"), and (b) BOQ lines with no specification backing ("BOQ Line [Y] — ceiling type, fire rating, and acoustic properties undefined in specification").

7. **Run ambiguity detection.** Scan each specification section for vague or incomplete language: phrases like "high-quality finish," "as directed by architect," or "to engineer's satisfaction." Flag missing performance criteria, testing and certification requirements, and referenced schedules or tables that are absent from the document set.

8. **Run drawing cross-reference check.** If drawings are provided, flag: (a) specification sections that reference drawing sheets not present in the package, and (b) drawing sheets not referenced anywhere in the specification. If no drawings are provided, note: "Drawings not provided — gap analysis is limited to Spec vs. BOQ only."

9. **Apply contract-risk-informed prioritization.** If contract risk findings were provided in step 3, re-rank gaps that interact with flagged contract risks as "High Priority (Contract Risk)." Present the re-prioritized list to the user and confirm: "Gaps have been re-ranked based on your contract risk findings. Review and adjust priority if your judgment differs."

10. **Estimate financial impact per gap.** For each Critical or High gap, estimate the cost impact if the gap is resolved adversely: Critical (>5% of contract sum), High (2–5%), Medium (<2%). Present as a range with the conservative and aggressive interpretation stated.

11. **Draft clarification questions.** For each Critical and High gap, generate a clear, actionable question grouped by topic (Structure, Finishes, MEP, External Works, General). Each question should reference the specific specification section and BOQ line, state what is missing or ambiguous, and suggest the standard or format the employer should respond in.

12. **Present findings for QS review.** Display the full gap report ranked by severity. Stop and ask the user to: approve gaps as identified, merge duplicate items, remove false positives, and adjust or remove any clarification questions before submission. Remind the user: "The Q&A deadline is typically 10–14 days before tender close — submit questions promptly."

## Error Handling

- **Unreadable or corrupted specification PDF:** Inform the user: "Unable to parse the specification PDF. Please ensure it is a text-based PDF, or paste the relevant section text directly."
- **Non-standard BOQ format:** Alert the user: "BOQ structure not recognized — cross-references are best-effort. Review the gap report carefully and add any items the automated check may have missed."
- **Specification heavily deferred to drawings (e.g., 'See Drawings' with no detail):** Flag: "Section [X] defers most detail to drawings. Gap analysis is limited without drawing content. Recommend manual QS review of this section."
- **BOQ Provisional Sums:** Treat as informational, not a gap: "BOQ Line [X] is a Provisional Sum. Confirm with the employer whether this should be firmed up before tender submission."
- **Revised specification uploaded mid-analysis:** If two versions of the specification are detected, ask: "Two specification versions detected. Analyze the latest version, or compare v1 vs. v2?" Proceed with the user's choice.
