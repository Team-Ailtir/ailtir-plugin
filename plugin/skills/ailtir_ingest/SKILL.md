---
name: ailtir_ingest
description: Routes messy data dropped into an Ailtir workspace (subcontractor quotes, tender addendums, RFIs, emails) into the right project folder and updates Notion databases. Always confirms before writing. Triggered by /ailtir-cowork-plugin:ailtir_ingest or when the user drops files into the workspace without clear instructions.
---

# Ailtir Ingest

## Usage Reporting

Before doing workflow-specific work, read the stable anonymous UUID from
`~/Ailtir-Tendering/install_id`. If the file is missing, create its parent
directory, generate a UUID v4, and write only that UUID to the file. Re-read the
file and call the `plugin_report_usage` tool from the bundled `ailtir` MCP server
with these arguments:

- `skill_name`: `ailtir_ingest`
- `plugin_version`: `2.15.2`
- `installation_id`: the UUID read from `~/Ailtir-Tendering/install_id`

If the identifier cannot be read or created, leave that failure visible and
continue without reporting. If reporting returns `failed`, leave the failure visible and continue the workflow.

This skill is the central router for the Ailtir Tendering Workstation. When a user drops files into the workspace, you classify them, confirm the destination, move them, and update the Notion database and bid status.

## Step 1 — Classify the Content
Read the incoming content (file, ZIP, or pasted text).
Classify it into one of these categories:

| Content Type | Signals | Destination |
|---|---|---|
| ITT / Tender Notice | "Instructions to Tenderers", "Contract Notice", "Tender Notice", eTenders / Find a Tender / Contracts Finder reference | `Bids/[BID]/1. Tender Documents/1.1 ITT/` |
| Drawing set | PDF with title block, drawing number, revision | `Bids/[BID]/1. Tender Documents/1.2 Drawings/` |
| Specification | Spec section numbers, NBS format, RIAI spec, or CIBSE / MEP spec sections | `Bids/[BID]/1. Tender Documents/1.3 Specification/` |
| Draft contract | "PW-CF", "RIAI", "JCT", "NEC4", "FIDIC", "Conditions of Contract" | `Bids/[BID]/1. Tender Documents/1.4 Contract/` |
| Bill of Quantities / Pricing doc | BQ, schedule of rates, pricing schedule, NRM2 elemental cost plan | `Bids/[BID]/1. Tender Documents/1.5 Pricing Document/` |
| Reports and Surveys | Ground investigation, site survey, asbestos report | `Bids/[BID]/1. Tender Documents/1.6 Reports and Surveys/` |
| Addendum | "Addendum No.", "Clarification", issued during tender period | `Bids/[BID]/1. Tender Documents/1.7 Addenda/` |
| Subcontractor quote | PDF/Excel from sub, contains pricing | `Bids/[BID]/5. Estimating/5.4 Subcontractor Quotes/` |
| RFI response | Response to a previously sent RFI | `Bids/[BID]/4. Clarifications/Responses Received/` |
| Certificate / credential | ISO cert, Safe-T-Cert (Ireland) or SSIP/CHAS/Constructionline (UK), Modern Slavery statement (UK), insurance schedule | `Context/credentials/` |
| Case study / reference | Completion cert, client reference letter | `Intelligence/case-studies/` |
| Method statement (approved) | Post-award, signed off | `Intelligence/method-statements/` |
| Contact | Name, company, email, phone | `Context/team.md` or CRM |
| Daily site report | Date, weather, manpower, activities | `Active Projects/[PROJECT]/Site-Diary/` |

If unclear, ask the user to clarify.

### Knowledge Capture Check
If the ingested file is a **method statement**, **case study**, **reference**, or **rate schedule**, ask the user if they want to capture this intelligence:
- For method statements: "Do you want to save a copy of this to `Intelligence/method-statements/` as a reusable template?"
- For case studies/references: "Do you want to add this to `Intelligence/case-studies/`?"
- For rate schedules: "Do you want to update `Intelligence/rate-library/` with any rates from this?"

**CRITICAL:** If the user says yes, you MUST read `references/metadata-schema.md` from the sibling `intelligence-builder` skill's directory and prepend the correct YAML frontmatter block to the Markdown file before saving it to `Intelligence/`.

## Step 2 — Identify the Bid Reference
Most content belongs to a specific bid. 
1. Check the Notion Bid Pipeline cache (`Context/notion-cache/bid-pipeline.md`) for active bids.
2. Ask the user: "Which bid does this belong to?" List the active bids as options, plus "New Bid" and "Not project-specific (save to Intelligence/Context)".
3. If they select "New Bid", ask for the project name and generate a bid reference (format: `YYYY-NNN-ProjectName`).

## Step 3 — Show the Plan, Confirm, Write
Tell the user exactly what you're about to do:
"I will move these files to `Bids/[BID]/1. Tender Documents/1.2 Drawings/` and update the Bid Pipeline."
Ask for confirmation.
If confirmed, move the files.

## Step 4 — The Soul-Update Pattern
After writing the files, you MUST update the state of the workspace so the next session starts with current data.

1. **Update the local Bid README:** Update `Bids/[BID]/README.md` with the new status (e.g., "Received 14 architectural drawings", "Received quote from Murphy Elec").
2. **Update Notion:** If Notion is connected, update the relevant database via MCP:
   - ITT received → Update Bid Pipeline Status to "1. Lead Identified"
   - Sub quote received → Update Subcontractor Directory
   - RFI response received → Update RFI Log Status to "Response Received"

## Anti-Patterns (What NOT to do)
- [HUMAN INPUT REQUIRED] DO NOT auto-classify ambiguous files without asking the user.
- DO NOT execute any file moves or database updates before the user confirms.
- DO NOT create random folders. ONLY use the destinations listed in the routing table.
- DO NOT skip the soul-update pattern. The README must reflect the current state.

## Quality Checks
- [ ] Every file routed to the correct subfolder within `Bids/[BID]/`.
- [ ] Notion Bid Pipeline updated after routing.
- [ ] YAML frontmatter added to any file saved to `Intelligence/`.
- [ ] User confirmed routing plan before any files were moved.
