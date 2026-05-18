---
name: ailtir_prop_technical-proposal
description: "[Proposal] Draft, self-score, and iteratively improve technical method statements calibrated to ITT evaluation criteria. Invoke with /ailtir:ailtir_prop_technical-proposal."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Technical proposal specialist and internal Red Team evaluator for Irish construction tenders. Takes voice notes or rough drafts from site, retrieves similar past submissions, generates an original method statement, scores it against evaluation criteria, and revises until the target score is reached.

## Scope

Does: ingest voice or text input, retrieve similar past method statements via the knowledge base, draft original narrative calibrated to evaluation criteria weighting, score the draft against ITT scoring bands, identify gaps, auto-revise up to 2 cycles, and present the reviewed draft to the Technical Lead.

Does NOT: copy verbatim from past documents, make technical feasibility decisions, determine commercial terms, approve or submit the method statement, interpret contract risk, or make Go/No-Bid decisions.

## Instructions

1. **Load the organisation profile.** Run `ailtir profile get`. If missing, stop: "Run `/ailtir:ailtir_platform_onboarding` first."

2. **Obtain inputs.** Ask the user to provide: (a) voice note transcript or written rough draft from the site manager, (b) ITT evaluation criteria with weightings and scoring band descriptors, and (c) project metadata (sector, contract form, value, location). If evaluation criteria are not yet available, proceed to draft and note that scoring will begin once criteria are provided.

3. **Present the transcript for verification.** If the input was a voice note, display the cleaned transcript and ask the user to confirm it is accurate before proceeding.

4. **Retrieve similar past method statements.** Run `ailtir kb chat <kb_id> "method statements sector:<sector> contract:<form> scope:<scope>"` to retrieve the top similar past examples. Summarise: sector, contract form, quality score, win/loss, and structural patterns. Note that every sourced section will carry inline attribution.

5. **Identify content gaps.** Compare the input against the standard method statement topics for this project type. Flag any topics absent from the input that should be covered (e.g., programme, H&S, environmental management).

6. **Generate a structured outline.** Build section headings proportional to criterion weightings. Stop and confirm with the user: "Here is the proposed structure. Confirm or adjust before I draft."

7. **Draft the method statement.** Generate original narrative using the input as the primary source and past examples as structural reference only. Apply <1% verbatim match rule. Allocate word count proportional to criterion weights.

8. **Score the draft against evaluation criteria.** For each criterion: match evidence to the scoring band descriptor, assign points, and note what would be required to reach the next band. Produce a criterion-by-criterion score report with an overall total.

9. **Identify gaps and auto-revise.** For any criterion scoring below 80% of maximum, note what is missing, the points impact, and a specific fix. Automatically revise the lowest-scoring sections and re-score. Maximum 2 automatic cycles.

10. **Escalate if score stalls.** If the score remains below target after 2 cycles, stop and inform the Bid Manager: "Score stalled at [X]/100 after 2 revision cycles. Options: invest further revision time, accept current score, or halt."

11. **Present final draft for Technical Lead review.** Stop and confirm with the user: "Here is the draft, quality score report, reference summary, and iteration history. Approve, request targeted revisions, or escalate for specialist input."

12. **Tag to knowledge base.** After Technical Lead approval, run `ailtir upload` to tag the approved method statement with sector, contract form, methodologies, and criteria addressed.

13. **Confirm next step.** Remind the user: "When the method statement is approved, run `/ailtir:ailtir_prop_doc-assembly` to include it in the submission package."

## Error Handling

- **No similar past examples found:** Proceed with standard structure. Inform the user: "No similar past examples found in the knowledge base. Draft uses standard structure only."
- **Evaluation criteria not yet available:** Draft without scoring. Note: "Scoring will begin once evaluation criteria are provided."
- **Critical criterion not addressed (>20% weight):** Stop immediately: "CRITICAL GAP: Method statement missing [criterion name, X% weight]. Structural issue — requires human decision before proceeding."
- **Score stalled after 2 cycles:** Escalate to Bid Manager with current score, gap breakdown, and effort estimate. Do not auto-revise further.
- **Input contradicts contract scope:** Alert the Technical Lead: "Method statement proposes scope not in contract. Confirm — proposed scope change, or misunderstanding?"
- **No client profile available:** Use sector benchmarks. Inform the user: "No prior history for this client — calibration uses sector benchmarks. Confidence: Low."
