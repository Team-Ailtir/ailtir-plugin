---
name: ailtir_intelligence-builder
description: Builds and maintains the Ailtir Intelligence knowledge base through interviews or bulk ingestion of historical tender material.
allowed-tools:
  - mcp__plugin_ailtir-cowork-plugin_ailtir__plugin_report_usage
---

# Ailtir Intelligence Builder

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_intelligence-builder`
- `plugin_version`: `2.15.4`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.
`intelligence-builder`

## Description
Run this skill when you want to capture a new case study, method statement, or win theme for your intelligence base, or when you want to bulk-ingest historical tenders from an existing shared drive.

## Use When
- You have just won a project and want to capture the case study while it's fresh
- You have lost a bid and want to capture the lessons learned
- You have an existing folder full of old CVs, case studies, or successful tender submissions that you want Claude to read and extract into the `Intelligence/` folder
- You want to formalise a method statement you've been using informally
- You want to update your company's win themes

## Required Inputs
None required to start. The skill will ask you which mode you want to use.

## Workflow

### Step 1: Mode Selection
Ask the user: "Do you want to build intelligence through an **Interview** (for a single new case study/method statement) or through **Bulk Ingest** (pointing me to an existing folder of historical tenders/CVs)?"

### Step 2: Execution (Based on Mode)

#### Path A: Interview Mode
1. Ask the user what they want to capture (Case Study, Method Statement, Win Theme, or Lessons Learned).
2. Conduct a brief, conversational interview to gather the details. Encourage the user to use voice notes for speed.
3. For Case Studies: Ask for project name, client, value, duration, key challenges overcome, and the standout success metric.
4. For Method Statements: Ask for the task, the sequence of works, safety controls, and quality checks.
5. Draft the document in the Ailtir brand voice (professional, objective, Irish AEC terminology).
6. **CRITICAL:** Read `references/metadata-schema.md` and generate the correct YAML frontmatter block for the document type. Place this at the very top of the draft.
7. Ask the user to review the draft and the metadata tags.
8. Save the approved document to the correct subfolder in `Intelligence/` (e.g., `Intelligence/case-studies/2026-Ballymun-School.md`).

#### Path B: Bulk Ingest Mode
1. Ask the user for the absolute path to the folder containing their historical documents (e.g., a synced SharePoint or Google Drive folder, or a local directory).
2. [HUMAN INPUT REQUIRED] Wait for the user to provide the path.
3. Scan the provided directory.
4. For each relevant file found (PDFs, Word docs, Markdown):
   - Read the content.
   - Classify it (Case Study, CV, Method Statement, Past Quality Submission).
   - Extract the core reusable intelligence (e.g., pull the methodology out of a past submission, extract the project details from a case study PDF).
   - Convert the extracted intelligence into clean Markdown format.
   - **CRITICAL:** Read `references/metadata-schema.md` and prepend the correct YAML frontmatter block to the Markdown file. Infer the metadata tags (sector, value, route) from the content where possible; leave placeholders where not.
   - Save the new Markdown file to the appropriate `Intelligence/` subfolder.
5. Provide a summary report of what was ingested and where it was saved.

### Step 3: Confirmation
Confirm to the user that the `Intelligence/` folder has been updated and that `quality-writer` will now use this new knowledge in future bids.

## Anti-Patterns
- **NEVER** save raw, unformatted PDFs or Word docs directly into the `Intelligence/` folder. Always extract the text and save it as clean Markdown so Claude can read it efficiently in future sessions.
- **NEVER** overwrite existing intelligence files without asking the user first.
- **NEVER** invent or hallucinate project details, values, or safety controls. If the user doesn't provide them, leave placeholders.
- **NEVER** save an intelligence file without a valid YAML frontmatter block at the top. The quality-writer relies on this metadata to filter documents.

## Quality Checks
- [ ] YAML frontmatter written to every file saved to `Intelligence/`.
- [ ] Metadata tags (sector, value, route, outcome) inferred from content where possible.
- [ ] No raw PDFs or Word docs saved directly — always extracted to Markdown.
- [ ] User confirmed the intelligence folder path before bulk ingest.

## Occasional Feedback

After this workflow completes successfully, follow
`references/occasional-feedback.md` from the sibling `ailtir_feedback` skill.
Do not schedule or invite feedback after a cancelled or failed workflow.
