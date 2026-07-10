---
name: ailtir_notion-second-brain
description: An advanced setup skill that builds a complete construction company "second brain" in Notion, including SOPs, cost history, and lessons learned. Triggered by /ailtir-cowork-plugin:ailtir_notion-second-brain.
---

# Ailtir Notion Second Brain Setup

## Usage Reporting

Before doing workflow-specific work, call the `plugin_report_usage` tool from
the bundled `ailtir` MCP server with these arguments:

- `skill_name`: `ailtir_notion-second-brain`
- `plugin_version`: `2.15.0`

If reporting returns `failed`, leave the failure visible and continue the workflow.

You are guiding a construction business through setting up an advanced Notion workspace. This goes beyond the basic databases (CRM, Bid Pipeline, RFI Log) created by `notion-setup`. It builds a comprehensive knowledge base that Claude can read to understand the company's DNA.

## Step 1 — Explain the Value
Explain to the user that a "Second Brain" allows Ailtir to learn their specific way of working. It will store their standard operating procedures (SOPs), historical costs, contract risk positions, and lessons learned from past projects.

## Step 2 — Define the Architecture
Present the proposed Notion architecture:
1. **Company HQ:** Mission, vision, branding guidelines, team directory.
2. **Standard Operating Procedures (SOPs):** How we estimate, how we run sites, how we manage safety.
3. **Cost History Database:** A searchable database of past project costs — e.g., cost/m² for schools, cost/m³ for concrete — recorded in the currency of the source project (EUR for `ireland-gc` records, GBP for `uk-gc` records).
4. **Contract Playbook:** Our standard amendments and risk positions for the contract forms in use — PW-CF and RIAI under `ireland-gc`; JCT SBC/DB 2024 and NEC4 ECC under `uk-gc`.
5. **Lessons Learned Log:** What went wrong on past jobs and how we avoid it next time.
6. **Supply Chain Directory:** Subcontractors rated by performance and safety compliance.

## Step 3 — Build the Structure
If the Notion MCP connector is active, use it to create these pages and databases within the user's workspace.
If the connector is not active, provide a detailed Markdown template that the user can import into Notion manually.

## Step 4 — Seed the Data
Ask the user for 2-3 key lessons learned from recent projects, or 1-2 standard cost metrics, and add them to the newly created databases to demonstrate how it works.

## Step 5 — Output
Confirm the setup is complete. Explain that the `/ailtir-cowork-plugin:ailtir_prime` command will now sync this expanded knowledge base into the local `Context/notion-cache/` folder for Ailtir to use in future sessions.

## Anti-Patterns (What NOT to do)
- DO NOT overwrite existing Notion pages without asking for permission first.
- DO NOT create overly complex, deeply nested databases that a site manager won't use. Keep it flat and searchable.
- DO NOT store sensitive passwords or banking details in the Notion workspace.
- [HUMAN INPUT REQUIRED] You must ask the user if they want to proceed with this advanced setup, as it will create multiple new pages in their Notion workspace.

## Quality Checks
- [ ] User explicitly confirmed they want to proceed with advanced setup.
- [ ] No existing Notion pages overwritten without permission.
- [ ] Architecture is flat and searchable — not deeply nested.
- [ ] No sensitive data (passwords, banking) stored in Notion.
