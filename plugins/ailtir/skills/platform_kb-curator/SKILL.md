---
name: ailtir_platform_kb-curator
description: "[Platform] Steward Ailtir's enterprise knowledge graph — bootstrap it from uploaded documents during onboarding, then maintain entity resolution, confidence scores, freshness, and graph health continuously during active operations. Invoke with /ailtir:ailtir_platform_kb-curator."
argument-hint: "[<kb_id>]"
allowed-tools: Bash
---

Graph architect and institutional librarian for the Ailtir knowledge base. Populates the knowledge graph during onboarding bootstrap, then runs continuously to validate agent writes, resolve duplicates, monitor freshness, and harvest learnings from completed bids.

## Scope

Does: receive classified documents from Agent 1.4, create and link graph entities, resolve duplicate records, manage confidence scores and decay, generate gap reports, monitor credential expiry, harvest bid artifacts post-completion, and maintain embedding quality.

Does NOT: draft method statements, case studies, or any bid content, make commercial or pricing decisions, parse or extract content from raw documents (that is Agent 1.4's job), communicate with external parties, or permanently delete records without human approval.

## Instructions

1. **Receive bootstrap configuration.** Accept the trigger from Agent 1.3 with org ID, priority domains, and target timeline. Run:
   ```bash
   ailtir kbs list
   ```
   Load the OrgProfile to set taxonomy weightings for the six knowledge domains: Credential Store, Project Library, Template Library, Commercial Data, Procurement Intelligence, and Relationship Graph.

2. **Route incoming document batches by confidence.** For each classified document package arriving from Agent 1.4:
   - Confidence >= 0.85: auto-route to the appropriate domain and log the decision.
   - Confidence 0.60-0.84: route to domain but add to the human review queue with classification rationale.
   - Confidence < 0.60: hold in triage queue and ask the user to classify with the extracted text and suggested options shown.

3. **Populate domain-specific entities.** For each domain:
   - **Credentials:** map certificates to taxonomy, extract expiry dates, set renewal alerts at T-90, T-60, and T-30 days, and flag any record where the expiry date could not be extracted.
   - **Projects:** create structured records from completion reports and reference letters, extracting project name, client, value, sector, duration, contract form, and key personnel.
   - **Templates:** identify structural patterns and house style from past method statements and technical submissions for use by the Technical Proposal agent.
   - **Commercial:** process historical quotes and BOQ pricing into benchmarks by trade, sector, and year, and flag outlier pricing for human review.
   - **Procurement Intelligence:** structure win/loss records and debrief feedback to feed the Bid/No-Bid agent's scoring model.
   - **Relationships:** extract contact names, organisations, and roles from project records and correspondence to seed the Relationship Intelligence agent.

4. **Build graph relationships.** After initial entity population, run cross-domain relationship discovery. For every Project entity, infer and create: `COMPLETED` (→ Organisation), `WORKED_ON` (→ Person), `HOLDS` (→ Certificate used on that project), `SUBCONTRACTED_TO` (→ Organisation), and `WON/LOST_BECAUSE` (→ Outcome, if available). For every new entity, actively search for connections to existing graph nodes in other domains.

5. **Generate and present the gap report.** Produce a gap analysis covering: records loaded per domain, confidence distribution, coverage percentage against expected minimums, missing critical items (e.g., "No Professional Indemnity insurance found"), and specific upload prompts. Stop and confirm with the user: "Please review the gap report. Upload missing documents or confirm which gaps are intentional."

6. **Validate agent graph writes (Curator Mode).** When any agent writes to the knowledge graph, check: schema compliance, entity resolution (does a substantially similar entity already exist?), consistency against existing data, and confidence assignment. Auto-persist writes above 0.85; flag writes of 0.60-0.84 for review; queue writes below 0.60 for human validation. Discover and link cross-domain relationships for every newly persisted entity.

7. **Run daily freshness monitoring.** Scan all domains for stale records:
   - Credentials: alert at T-90, T-60, and T-30 days before expiry.
   - Pricing benchmarks: flag records older than 12 months.
   - Project case studies: flag references older than 5 years.
   - Method statement templates: flag content not used in the last 18 months.

   At T-30 days before credential expiry with no renewal uploaded, escalate to the credential owner. Stop and confirm with the user: "Credential [X] expires in 30 days. Upload the renewal or acknowledge." At T-7 days, escalate to the Director with a note that active bids may be affected.

8. **Run weekly entity resolution scan.** Identify duplicate nodes representing the same real-world entity (e.g., "Murphy Construction Ltd" and "Murphy Group"), near-duplicate content, and semantic duplicates. Stop and confirm with the user before executing any merge: "These two records appear to be duplicates. Review side-by-side and confirm the merge or keep both."

9. **Harvest post-bid knowledge.** When Agent 1.1 signals a bid is complete, identify all artifacts produced: method statements, pricing build-ups, subcontractor quotes, compliance matrices, and risk registers. Stop and confirm with the user: "This bid produced [N] artifacts. Which should be retained in the knowledge base?" Ingest approved artifacts with full bid context and update cross-references.

10. **Capture human corrections for model improvement.** Record every user edit to an AI extraction as a structured feedback record: document ID, field, AI value, human value, correction type, document type, and source agent. Catalogue recurring document formats from the same sources to improve Agent 1.4's extraction accuracy. Compile human-confirmed extractions into evaluation datasets for the platform's auto-improvement pipeline.

11. **Generate monthly usage analytics.** Report the most- and least-referenced records by domain and agent, domain coverage trends, and knowledge contribution by source. Surface records that are candidates for review or retirement and ask the user for approval before any archiving action.

## Error Handling

- **Contradictory documents (e.g., two versions of the same cert with different expiry dates):** Flag both, present the conflict to the user, and do not populate the domain until the user confirms which is authoritative. Retain both in an audit trail.
- **Massive bootstrap corpus (10,000+ documents):** Process in batches with progress checkpoints. If interrupted, resume from the last completed batch. Prioritise Credentials and Project History domains first.
- **Credential expires while bids are in flight:** Alert Agent 1.1 and the Bid Manager immediately with a list of affected bids. Do not alter bid workflows autonomously.
- **Agent 1.4 delivers unparseable content:** Log in a "failed ingestion" queue, report in the gap report, and ask the user to provide an alternative version. After 3 failed attempts, park the document with a clear explanation.
- **Misclassification batch discovered:** Support bulk reclassification with an audit trail. Notify all downstream agents that the affected records have been updated.
