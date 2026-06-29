# The Ailtir Co-Work Plugin

The Ailtir Co-Work Plugin is a Claude plugin for Irish construction tender management, built primarily for **Claude Cowork** (claude.com/product/cowork) and compatible with Claude Code. It covers the CWMF tender lifecycle from opportunity monitoring and bid planning through estimating, submission, post-award records, and reusable bid intelligence.

Use [INSTALL.md][install] for setup and [CONTRIBUTING.md][contributing] for development workflow.

## What It Provides

- Scoped Claude skills under `/ailtir-cowork-plugin:*` covering the full tender lifecycle.
- Bundled Python helpers (per-skill) for workbooks, project indexing, PDF processing, and takeoff support.
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
| `AILTIR_PLUGIN_DATA` | Optional | Setup resources, feedback log | Sets the Ailtir workspace root. Defaults to `~/Ailtir-Tendering`. |

## Telemetry

This plugin has **no built-in telemetry**. Cowork's sandbox blocks all outbound network traffic, so PostHog-style HTTP reporting cannot function. The `feedback` skill records user feedback to a local Markdown log inside the workspace (`Daily/feedback.md`) instead of sending it anywhere.

## Release Notes

### v2.12

- Removed all `${CLAUDE_PLUGIN_ROOT}` references from SKILL.md bodies — the variable doesn't resolve in Cowork. Script invocations and bundled-file references are now described in natural language so Claude resolves the absolute path itself from the SKILL.md's known location.
- Removed the plugin-root `scripts/` folder (telemetry wrappers and Python launchers). Outbound network is blocked in the Cowork sandbox; the telemetry pipeline has been silently dead there since the plugin migrated to Cowork.
- `feedback` skill now writes feedback to a local Markdown log in the user's workspace instead of POSTing to PostHog.
- Added the diagnostic `telemetry-test` skill for verifying sandbox capabilities (egress allowlist, path resolution, env var substitution) in any future Cowork deployment.

### v2.11

- Commands and skills unified — every workflow is now a skill under `skills/<name>/SKILL.md` and the slash command is `/ailtir-cowork-plugin:<name>`.
- The old `commands/` and `resources/` folders are removed. Setup templates, the workstation creator, the Notion cache sync script, and brand references now live inside the skill that uses them.
- New skills: `setup`, `prime`, `enable-monitor` (previously command-only).
- Skill folders no longer carry the `ailtir-` prefix — the plugin namespace already supplies it.

### v2.7

- All user-facing workflows are scoped commands.
- Implementation skills are hidden from the slash menu.
- Setup resources and scripts use portable plugin-relative paths.
- MCP setup is documented in [INSTALL.md][install].

[contributing]: ./CONTRIBUTING.md
[install]: ./INSTALL.md
