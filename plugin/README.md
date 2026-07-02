# The Ailtir Co-Work Plugin

The Ailtir Co-Work Plugin is a Claude plugin for construction tender management, built primarily for **Claude Cowork** (claude.com/product/cowork) and compatible with Claude Code. It covers the full tender lifecycle — opportunity monitoring, bid planning, estimating, submission, post-award records, and reusable bid intelligence — across the Irish and UK construction markets, using a profile architecture designed to expand to further markets and verticals.

Use [INSTALL.md][install] for setup and [CONTRIBUTING.md][contributing] for development workflow.

## What It Provides

- Scoped Claude skills under `/ailtir-cowork-plugin:*` covering the full tender lifecycle.
- Bundled Python helpers (per-skill) for workbooks, project indexing, PDF processing, and takeoff support.
- MCP server definitions for Notion and Microsoft 365 integrations.
- **Profile-based market calibration** — `/ailtir-cowork-plugin:ailtir_setup` writes `Context/profile.json`; every skill loads the reference file matching the active profile:
  - **`ireland-gc`** — CWMF, PW-CF, RIAI, SEO, SCSI, ARM4, NRM2, CIRI, Safe-T-Cert, BCAR, PSDP/PSCS.
  - **`uk-gc`** — Procurement Act 2023, JCT 2024, NEC4, CIJC, BCIS, NRM1/NRM2, SSIP (CHAS/SafeContractor/Constructionline), CDM 2015, PPN 06/20 (Carbon Reduction Plan), PPN 06/21 (Social Value), Modern Slavery Act, and Building Safety Act 2022 gates for Higher-Risk Buildings.

## Core Workflow

```text
SETUP
  /ailtir-cowork-plugin:ailtir_setup
  /ailtir-cowork-plugin:ailtir_notion-setup
  /ailtir-cowork-plugin:ailtir_notion-second-brain

EVERY SESSION
  /ailtir-cowork-plugin:ailtir_prime

FEEDBACK
  /ailtir-cowork-plugin:ailtir_feedback

PHASE 0 - OPPORTUNITY IDENTIFICATION
  /ailtir-cowork-plugin:ailtir_opportunity-monitor

PHASE 1 - QUALIFY & PLAN
  /ailtir-cowork-plugin:ailtir_bid-planner
  /ailtir-cowork-plugin:ailtir_project-indexer
  /ailtir-cowork-plugin:ailtir_go-no-go
  /ailtir-cowork-plugin:ailtir_compliance-matrix
  /ailtir-cowork-plugin:ailtir_contract-risk

PHASE 2 - ESTIMATE & PRICE
  /ailtir-cowork-plugin:ailtir_takeoff
  /ailtir-cowork-plugin:ailtir_prelims-builder
  /ailtir-cowork-plugin:ailtir_estimating-workflow
  /ailtir-cowork-plugin:ailtir_cost-reconciliation

PHASE 3 - ENQUIRE & PROCURE
  /ailtir-cowork-plugin:ailtir_package-breakdown
  /ailtir-cowork-plugin:ailtir_subcontractor-enquiry
  /ailtir-cowork-plugin:ailtir_bid-leveling

PHASE 4 - WRITE & SUBMIT
  /ailtir-cowork-plugin:ailtir_pqq-manager
  /ailtir-cowork-plugin:ailtir_rfi-generator
  /ailtir-cowork-plugin:ailtir_quality-writer
  /ailtir-cowork-plugin:ailtir_programme-builder
  /ailtir-cowork-plugin:ailtir_bid-assembly
  /ailtir-cowork-plugin:ailtir_submission-preflight
  /ailtir-cowork-plugin:ailtir_post-tender-interview

POST-AWARD & INTELLIGENCE
  /ailtir-cowork-plugin:ailtir_contract-admin
  /ailtir-cowork-plugin:ailtir_site-diary
  /ailtir-cowork-plugin:ailtir_case-study-generator
  /ailtir-cowork-plugin:ailtir_intelligence-builder
  /ailtir-cowork-plugin:ailtir_dashboard
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

### v2.13

- **Profile architecture (`ireland-gc` + `uk-gc`).** `/ailtir-cowork-plugin:ailtir_setup` now asks the user for Region (Ireland or UK) and Vertical (General Contractor), writes `Context/profile.json`, and picks the matching workspace `CLAUDE.md` variant so currency, dates, terminology, and standards apply automatically to every prompt.
- **Per-skill profile references.** Skills that were coupled to Irish market data (`contract-risk`, `contract-admin`, `opportunity-monitor`, `rate-library`, `estimating-workflow`, `go-no-go`) now load from `references/{profile_key}/…`. Existing Irish content is preserved under `ireland-gc/`; UK counterparts live under `uk-gc/`.
- **UK content.** JCT SBC/DB 2024 and NEC4 ECC playbooks, Early Warning / Compensation Event / EOT / Loss & Expense notice templates, Procurement Act 2023 opportunity scoring model, Find a Tender + Contracts Finder alert-source config, CIJC/BCIS rates for 2026, and CDM 2015 + Building Safety Act 2022 gap checks in estimating-workflow.
- **UK opportunity parser.** New `parse_fts_email.py` sibling to the existing eTenders parser; SKILL.md picks the parser by `profile_key`.
- **Profile-aware Excel generator.** `create_estimate.py` accepts `--profile-key` and emits £ or € number formats and profile-appropriate sample prelims rates.
- **Setup pre-flight.** Setup now detects an existing workspace and offers Update / Full reset / Cancel rather than silently overwriting.
- **Prime briefing header.** `/ailtir-cowork-plugin:ailtir_prime` shows the active profile at the top of every session briefing.
- **Notion schema** extended with UK procurement routes (Procurement Act 2023 notice and procedure taxonomy) and UK subcontractor accreditation checkboxes (SSIP, CHAS, SafeContractor, Constructionline, ISO tiers, Modern Slavery statement).

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
