# The Ailtir Co-Work Plugin

The Ailtir Co-Work Plugin is a Claude Code plugin for Irish construction tender management. It covers the CWMF tender lifecycle from opportunity monitoring and bid planning through estimating, submission, post-award records, and reusable bid intelligence.

Use [INSTALL.md][install] for setup and [CONTRIBUTING.md][contributing] for development workflow.

## What It Provides

- Scoped Claude commands under `/ailtir-cowork-plugin:*`.
- Hidden workflow skills that commands invoke behind the scenes.
- Bundled Python helpers for workbooks, project indexing, PDF processing, and takeoff support.
- MCP server definitions for Notion and Microsoft 365 integrations.
- Irish-market calibration for CWMF, PW-CF, RIAI, SEO, SCSI, ARM4, NRM2, CIRI, and Safe-T-Cert workflows.

## Core Workflow

```text
SETUP
  /ailtir-cowork-plugin:setup
  /ailtir-cowork-plugin:notion-setup
  /ailtir-cowork-plugin:notion-second-brain

EVERY SESSION
  /ailtir-cowork-plugin:prime

FEEDBACK
  /ailtir-cowork-plugin:feedback

PHASE 0 - OPPORTUNITY IDENTIFICATION
  /ailtir-cowork-plugin:opportunity-monitor

PHASE 1 - QUALIFY & PLAN
  /ailtir-cowork-plugin:bid-planner
  /ailtir-cowork-plugin:project-indexer
  /ailtir-cowork-plugin:go-no-go
  /ailtir-cowork-plugin:compliance-matrix
  /ailtir-cowork-plugin:contract-risk

PHASE 2 - ESTIMATE & PRICE
  /ailtir-cowork-plugin:takeoff
  /ailtir-cowork-plugin:prelims-builder
  /ailtir-cowork-plugin:estimating-workflow
  /ailtir-cowork-plugin:cost-reconciliation

PHASE 3 - ENQUIRE & PROCURE
  /ailtir-cowork-plugin:package-breakdown
  /ailtir-cowork-plugin:subcontractor-enquiry
  /ailtir-cowork-plugin:bid-leveling

PHASE 4 - WRITE & SUBMIT
  /ailtir-cowork-plugin:pqq-manager
  /ailtir-cowork-plugin:rfi-generator
  /ailtir-cowork-plugin:quality-writer
  /ailtir-cowork-plugin:programme-builder
  /ailtir-cowork-plugin:bid-assembly
  /ailtir-cowork-plugin:submission-preflight
  /ailtir-cowork-plugin:post-tender-interview

POST-AWARD & INTELLIGENCE
  /ailtir-cowork-plugin:contract-admin
  /ailtir-cowork-plugin:site-diary
  /ailtir-cowork-plugin:case-study-generator
  /ailtir-cowork-plugin:intelligence-builder
  /ailtir-cowork-plugin:dashboard
```

## Connectors

The plugin can run with local files only, but the intended setup uses:

| Connector | Purpose |
|---|---|
| Notion | CRM, Bid Pipeline, Subcontractor Directory, RFI Log |
| Microsoft 365 | SharePoint/OneDrive document access |
| Gmail or Outlook | eTenders and OJEU alert monitoring |

See [INSTALL.md][install] for MCP server prerequisites and credential setup.

## Environment Variables

The plugin can run with local files only. Connector features use the following
environment variables:

| Variable | Required | Used By | Purpose |
|---|---:|---|---|
| `NOTION_API_KEY` | Optional | `.mcp.json` Notion MCP server | Enables Notion CRM, Bid Pipeline, Subcontractor Directory, and RFI Log access. |
| `M365_TENANT_ID` | Optional | `.mcp.json` Microsoft 365 MCP server | Identifies the Microsoft 365 tenant for SharePoint/OneDrive access. |
| `M365_CLIENT_ID` | Optional | `.mcp.json` Microsoft 365 MCP server | Identifies the Microsoft 365 application/client. |
| `M365_CLIENT_SECRET` | Optional | `.mcp.json` Microsoft 365 MCP server | Authenticates the Microsoft 365 application/client. |
| `AILTIR_PLUGIN_DATA` | Optional | `commands/setup.md`, `resources/setup/scripts/create_workstation.py` | Sets the Ailtir workspace root. Defaults to `~/Ailtir-Tendering`. |
| `CLAUDE_PLUGIN_ROOT` | Runtime | Commands, skills, telemetry scripts | Provided by Claude Code for installed plugins. Points to the plugin package root. |
| `CLAUDE_PLUGIN_DATA` | Runtime | `scripts/report_usage.py`, `scripts/report_feedback.py` | Optional Claude/plugin data directory. Stores the anonymous install ID and telemetry debug log. Defaults to `~/.cache/ailtir-plugin`. |

Telemetry uses the plugin's bundled PostHog project token, the EU PostHog host,
and a fixed 1.5 second timeout. It is fail-open: data directory or network
failures do not block plugin workflows. Events set `$process_person_profile:
false` and use an anonymous install ID.

## Release Notes

### v2.7

- All user-facing workflows are scoped commands.
- Implementation skills are hidden from the slash menu.
- Setup resources and scripts use `${CLAUDE_PLUGIN_ROOT}` paths.
- MCP setup is documented in [INSTALL.md][install].

[contributing]: ./CONTRIBUTING.md
[install]: ./INSTALL.md
