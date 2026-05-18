---
name: ailtir_platform_doc-ingestion
description: "[Platform] Accept any document uploaded to Ailtir, classify it into one of 7 categories, extract structured metadata with confidence scores, deduplicate against existing records, and route classified packages to the Knowledge Base Curator and downstream agents. Invoke with /ailtir:ailtir_platform_doc-ingestion."
argument-hint: "[<bid_id>]"
allowed-tools: Bash
---

Universal document processing pipeline and single entry point for all documents entering Ailtir. Transforms unstructured document uploads into classified, metadata-enriched records that downstream agents can consume immediately — without the user having to type.

## Scope

Does: accept PDF, DOCX, XLSX, CSV, JPG/PNG/TIFF, EML/MSG, DWG, and ZIP files; detect format and route through the correct extraction pipeline; classify into 7 primary categories; extract structured metadata with per-field confidence scores; detect duplicates and version conflicts; route classified records to Agent 1.2 and fast-path tender documents to analysis agents.

Does NOT: interpret document content beyond classification and metadata extraction, make commercial or strategic decisions, delete or archive documents, communicate with external parties, or store documents (passes content and metadata to Agent 1.2 for storage and indexing).

## Instructions

1. **Accept and validate the upload.** Receive one or more files via:
   ```bash
   ailtir upload <file_path> [--bid-id <bid_id>] [--category-hint <hint>]
   ```
   Validate that each file is not zero-byte, does not exceed 100 MB per file or 2 GB per batch, and passes virus scanning. Unpack ZIP files and process each contained file individually. Confirm receipt to the user immediately (within 2 seconds) — processing continues in the background.

2. **Detect format and route to the extraction pipeline.** Identify the true file type from magic bytes (not file extension):
   - Text-based PDF: direct text and table parsing.
   - Scanned PDF or image (JPG/PNG/TIFF): OCR pipeline. Flag documents with OCR quality below 70% for human review but continue with best-effort text.
   - DOCX: document parser preserving heading structure and tables.
   - XLSX/CSV: structured data parser. Detect whether it is a BOQ, contact list, pricing schedule, or other tabular data.
   - EML/MSG: extract body, sender/recipient metadata, and attachments (process recursively).
   - DWG: extract title block metadata only (full drawing parsing is Phase 3).
   - Multi-page PDF: detect if a single file contains multiple logical documents (e.g., a scanned certificate bundle) and split each into an independent processing job.

3. **Classify the document.** Apply a two-stage approach:
   - Stage 1 (heuristic): check the upload context hint and filename patterns. If heuristic confidence > 90%, proceed directly to metadata extraction and run AI classification in the background to verify.
   - Stage 2 (AI): classify into one of 7 primary categories: (1) Credentials & Certificates, (2) Project Records, (3) Tender Documents (ITT), (4) Past Submissions, (5) Commercial Documents, (6) Correspondence & Contacts, (7) Company Documents. Each category has defined subcategories (e.g., Credentials includes Safe-T-Cert, ISO, Insurance, Tax Clearance, CSCS). If Stage 1 and Stage 2 disagree, use the AI result but reduce confidence and increase the likelihood of queuing for human review.

4. **Extract structured metadata.** Apply the category-specific schema to extract all defined fields with per-field confidence scores. Critical fields by category:
   - Credentials: issuer, cert number, standard, scope, issue date, expiry date, company name.
   - Project Records: project name, client, value, sector, location, completion date, team members, role.
   - Tender Documents: contracting authority, tender reference, CPV codes, deadline, estimated value, procurement route, contract form, evaluation criteria.
   - Commercial Documents: company name, contact email, total price, scope summary, inclusions, exclusions, validity period, related tender.
   Never fabricate a field value — report `null` with a reason if a field cannot be extracted.

5. **Score confidence and route to review queue.** Calculate the overall confidence as the minimum of classification confidence and extraction confidence (weighted by field importance):
   - >= 0.85: auto-commit to knowledge base. No human action needed.
   - 0.60-0.84: present to user with highlighted source regions for confirmation. Target: 30 seconds per document.
   - 0.30-0.59: present for guided review with AI partial extraction and missing field prompts. Target: 2 minutes per document.
   - < 0.30: queue for manual classification. Target: 3 minutes per document.
   Stop and confirm with the user for all items below 0.85, showing the document preview and the AI suggestion.

6. **Run deduplication.** Compare against the existing document index:
   - Exact duplicate (SHA-256 hash match): do not create a new record — link to the existing document.
   - Near-duplicate for same-category documents: same cert number, or same issuer + standard + company + dates within 30 days for certificates; same company + tender + price within 5% for quotes.
   - Version detection: if a near-duplicate has a newer date or higher OCR quality, flag as "newer version" and recommend replacing.
   - Conflict detection: if two documents for the same entity contain contradictory data (e.g., two insurance certs with different expiry dates), stop and confirm with the user: "Conflicting data detected — review both documents and confirm which is authoritative."

7. **Route the classified record to downstream consumers.** Standard path: send to Agent 1.2 (Knowledge Base Curator) for all categories. Fast-path (when a bid ID is active): also send Tender Documents directly to the Contract Risk, Scope Gap, and Compliance Matrix agents; send Commercial Documents directly to the Quote Normalization agent. Both paths run in parallel — fast-path agents do not wait for knowledge base indexing.

8. **Present the batch summary.** After processing a bulk upload, notify the user: "X files processed: Y auto-classified, Z queued for review, W duplicates detected, V errors." Group review queue items by likely category and offer keyboard shortcuts for power users processing large batches.

9. **Feed corrections back to the classification model.** When a user corrects an auto-committed or suggested classification, log the correction as a structured feedback record (document ID, AI category, corrected category, corrected metadata). If a pattern of corrections emerges for a specific document type or source, flag to Agent 1.2 to lower the auto-commit threshold for that type and update the format pattern library.

## Error Handling

- **Corrupt or unreadable file:** Log the error and inform the user: "This file could not be read — it may be corrupt or password-protected. Please upload a different version." Store the original for manual review. Do not block batch processing of other files.
- **Password-protected PDF:** Prompt the user for the password. If not provided, queue with "password required" status.
- **Completely unrecognisable document (confidence < 0.30 on all categories):** Present with "We couldn't identify this document" and ranked best guesses. After 3 such failures from the same source, suggest to the user that these documents may not be relevant to Ailtir.
- **Multi-document PDF (certificate bundle):** Split into individual documents and process each independently. If boundary detection confidence is low, stop and confirm with the user before splitting.
- **Network failure during external enrichment:** Continue processing without enrichment data. Mark enrichment as "pending retry" and retry with exponential backoff (3 attempts over 24 hours). The classified record is routed regardless.
- **Malicious file detected:** Reject immediately, notify the user and system administrator, log the incident, and do not process or store file content.
- **Batch exceeds 500 files:** Accept the batch but process in priority chunks of 50. Prioritise active bid documents over onboarding backfill. Show estimated completion time.
