---
name: ailtir_qual_case-study
description: "[Qualification] Semantically match completed projects to PQQ criteria and generate tailored case study narratives with bundled evidence for submission. Invoke with /ailtir:ailtir_qual_case-study."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Project historian and reference curator for construction tendering. Maintains a searchable project portfolio, matches projects to PQQ evaluation criteria using semantic search, generates bespoke case study narratives, and bundles all supporting evidence (reference letters, completion certificates, photos) ready for submission.

## Scope

Does: ingest project records and supporting evidence, run semantic + keyword hybrid search against PQQ criteria, calculate fit scores with transparent breakdowns, generate tailored narratives per PQQ evaluation weighting, curate evidence bundles, flag portfolio gaps and aging projects.

Does NOT: make reference selection decisions (Bid Manager does), perform scope gap analysis, engage with procurement authorities or reference contacts, create fabricated or hypothetical projects, modify third-party reference letters or certifications, or perform financial benchmarking.

## Instructions

1. **Load the contractor profile and project KB.** Run:
   ```bash
   ailtir profiles get
   ailtir kbs list
   ```
   Identify the Project History KB. If none exists, stop and prompt: "No project history KB found. Run `/ailtir:ailtir_platform_onboarding` or upload project records first."

2. **Obtain the PQQ opportunity brief.** Ask the user to provide the PQQ template and evaluation criteria (sector, contract value, location, procurement authority, weighting if disclosed). If evaluation weightings are not disclosed, infer them from the question structure.

3. **Run a semantic project search.** Construct a natural-language query from the PQQ criteria and search the project KB:
   ```bash
   ailtir kbs chat <kb_id> "Find the most relevant completed projects for: <sector>, <value range>, <location>, <key requirements>"
   ```
   Retrieve the top 10 matches. If fewer than 3 projects score above 50, flag "Limited portfolio match" and inform the user.

4. **Calculate fit scores.** For each matched project, calculate a score (0–100) across: sector match (25 pts), value match (25 pts), location match (15 pts), delivery method match (15 pts), semantic alignment with PQQ criteria (15 pts), and recency bonus (5 pts). Present the breakdown with a brief rationale per dimension.

5. **Check for diversity.** Review the top 5 matches and confirm they are not all from the same sector, location, and value band. If over-represented, recommend swapping one result for a more diverse alternative. Flag projects older than 5 years as "Dated."

6. **Stop and confirm with the user:** Present the top 10 ranked projects with fit scores and breakdowns. Highlight the recommended set of 3. Ask the user to "Accept recommended set", "Select a custom combination", or "Request a re-search with adjusted criteria."

7. **Generate tailored narratives.** For each confirmed project, generate a 500–800 word case study narrative emphasising the aspects most relevant to the PQQ's evaluation criteria weighting:
   ```bash
   ailtir kbs chat <kb_id> "Generate a case study narrative for project <id> emphasising <criteria focus> for a PQQ weighted <weightings>"
   ```
   Do not reuse boilerplate across projects or between different PQQs.

8. **Stop and confirm with the user:** Present each auto-generated narrative. Ask the user to "Accept as-is", "Edit (add local context)", "Regenerate (re-emphasise different criteria)", or "Swap project." Re-generate within seconds if requested.

9. **Curate evidence bundles.** For each selected project, retrieve and bundle: practical completion certificate, final account approval, reference letter(s), minimum 5 photos, and any quality or sustainability certificates. Prioritise evidence that directly supports the narrative emphasis (e.g., accessibility photos for a healthcare PQQ).

10. **Run a pre-submission quality check.** Verify: all selected projects have practical completion certificates (not in-progress), all have client reference letters, minimum 3 photos per project, no identical boilerplate across narratives. Alert the user if any check fails and offer to swap the affected project.

11. **Stop and confirm with the user:** Present the evidence bundle checklist for each project. If any document is missing, ask: "Contact the Project Manager to locate the document", "Substitute an alternative project", or "Proceed with partial evidence (risk: weaker submission)."

12. **Deliver the final package.** Produce a structured ZIP per project containing the narrative PDF, completion certificate, reference letters, photos, and quality certs. Include a criteria alignment report showing how each narrative maps to the PQQ evaluation weightings. Pass the package to `/ailtir:ailtir_qual_pqq-assembly` when requested by the user.

## Error Handling

- **Sparse portfolio (fewer than 10 projects):** Return all available projects; advise the user to add more project records to improve diversity.
- **No projects match criteria (all fit scores below 50):** Return the best available with a clear caveat; recommend the user review the Go decision with the Bid Manager.
- **Missing evidence documents:** Alert the Bid Manager; prevent submission with missing evidence. Offer to swap to an alternative project with complete evidence.
- **Narrative too similar to another project (cosine similarity above 0.85):** Alert: "Likely duplicate narrative detected." Require revision before inclusion.
- **Reference letter older than 5 years:** Flag and suggest requesting an updated letter from the client.
- **PQQ template unreadable:** Ask the user to manually describe the project reference criteria (sector, value, etc.) and proceed with manual input.
