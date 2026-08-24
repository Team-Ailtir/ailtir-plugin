# The Ailtir Co-Work Plugin

The Ailtir Co-Work Plugin is a Claude plugin for construction tender management, built primarily for **Claude Cowork** (claude.com/product/cowork) and compatible with Claude Code. It covers the full tender lifecycle — opportunity monitoring, bid planning, estimating, submission, post-award records, and reusable bid intelligence — across the Irish and UK construction markets, using a profile architecture designed to expand to further markets and verticals.

> **New here?** Read [PROCESS.md](PROCESS.md) for the end-to-end bid lifecycle and how the skills fit together.

Use [INSTALL.md][install] for setup and [CONTRIBUTING.md][contributing] for development workflow.

## What It Provides

- Scoped Claude skills under `/*` covering the full tender lifecycle.
- Bundled Python helpers (per-skill) for workbooks, project indexing, PDF processing, and takeoff support.
- MCP server definitions for anonymous Ailtir reporting plus Notion and Microsoft 365 integrations.
- **Profile-based market calibration** — `/ailtir_setup` writes `Context/profile.json`; every skill loads the reference file matching the active profile:
  - **`ireland-gc`** — CWMF, PW-CF, RIAI, SEO, SCSI, ARM4, NRM2, CIRI, Safe-T-Cert, BCAR, PSDP/PSCS.
  - **`uk-gc`** — Procurement Act 2023, JCT 2024, NEC4, CIJC, BCIS, NRM1/NRM2, SSIP (CHAS/SafeContractor/Constructionline), CDM 2015, PPN 06/20 (Carbon Reduction Plan), PPN 06/21 (Social Value), Modern Slavery Act, and Building Safety Act 2022 gates for Higher-Risk Buildings.

## Core Workflow

> Canonical phase and skill order is maintained in [`skills/ailtir_conductor/references/phase-map.md`](skills/ailtir_conductor/references/phase-map.md). The block below is derived from it.

```text
WORKSPACE SETUP (run once)
  /ailtir_setup
  /ailtir_notion-setup          (if using Notion)
  /ailtir_intelligence-builder  (recommended: seed before your first bid)

EVERY SESSION
  /ailtir_prime

PHASE: opportunity
  /ailtir_go-no-go

PHASE: pre-bid
  /ailtir_bid-planner           (Tier-1 first pass — workbook + deck)
  /ailtir_contract-risk         (deep dive)
  /ailtir_compliance-matrix     (deep dive)
  /ailtir_pqq-manager           (if a PQQ/SQ is required)

PHASE: estimating
  /ailtir_package-breakdown
  /ailtir_takeoff
  /ailtir_subcontractor-enquiry
  /ailtir_prelims-builder
  /ailtir_bid-leveling
  /ailtir_cost-reconciliation

PHASE: submission
  /ailtir_quality-writer
  /ailtir_programme-builder
  /ailtir_bid-assembly
  /ailtir_submission-preflight

PHASE: post-tender
  /ailtir_post-tender-interview (if invited)
  /ailtir_case-study-generator
  /ailtir_feedback

PHASE: delivery
  /ailtir_site-diary
  /ailtir_contract-admin

SUPPORT (available at any time, not sequenced)
  /ailtir_rfi-generator
  /ailtir_rate-library
  /ailtir_intelligence-builder
  /ailtir_dashboard
  /ailtir_opportunity-monitor
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
| `AILTIR_PLUGIN_DATA` | Optional | Setup resources | Sets the Ailtir workspace root. Defaults to `~/Ailtir-Tendering`. |

## Telemetry

Every skill reports a minimal anonymous usage event through the public
`plugin_report_usage` tool in `ailtir-mcp`. The event contains only the skill
name, plugin version, source, timestamp, and a stable anonymous installation
UUID stored in `~/Ailtir-Tendering/install_id`; it does not contain a workspace
path, user ID, or tenant ID. The feedback skill sends the anonymous rating and
user-approved answers through `plugin_feedback`. Reporting failures remain
visible but never block a workflow.
After the first successful substantive workflow, the plugin optionally invites
feedback; later invitations occur no more frequently than every 5 successful
workflows or 10 days. Scheduling stays local in `.feedback_state.json`, and no
feedback is submitted unless the user accepts and answers the invitation.

## Release Notes

### v2.15.4

- Added locally scheduled, optional feedback invitations with conservative
  frequency limits.
- Setup now explains reporting and requires the Ailtir connector before the
  onboarding interview begins.

### v2.15.3

- Pre-approved the two public reporting tools within the skills that use them,
  avoiding first-use tool permission prompts without approving other MCP tools.

### v2.15.2

- Restored a stable anonymous installation UUID for usage and feedback events.

### v2.15.1

- Switched anonymous reporting from a local `uvx` process to the hosted Ailtir
  Streamable HTTP connector so it installs correctly in Cowork.

### v2.15

- Added `ailtir-mcp` 2.1.0 and anonymous usage reporting to every skill.
- Moved feedback submission from `Daily/feedback.md` to the public `plugin_feedback` MCP tool.
- Kept direct script networking disabled while allowing MCP-mediated reporting.

### v2.13

- **Profile architecture (`ireland-gc` + `uk-gc`).** `/ailtir_setup` now asks the user for Region (Ireland or UK) and Vertical (General Contractor), writes `Context/profile.json`, and picks the matching workspace `CLAUDE.md` variant so currency, dates, terminology, and standards apply automatically to every prompt.
- **Per-skill profile references.** Skills that were coupled to Irish market data (`contract-risk`, `contract-admin`, `opportunity-monitor`, `rate-library`, `estimating-workflow`, `go-no-go`) now load from `references/{profile_key}/…`. Existing Irish content is preserved under `ireland-gc/`; UK counterparts live under `uk-gc/`.
- **UK content.** JCT SBC/DB 2024 and NEC4 ECC playbooks, Early Warning / Compensation Event / EOT / Loss & Expense notice templates, Procurement Act 2023 opportunity scoring model, Find a Tender + Contracts Finder alert-source config, CIJC/BCIS rates for 2026, and CDM 2015 + Building Safety Act 2022 gap checks in estimating-workflow.
- **UK opportunity parser.** New `parse_fts_email.py` sibling to the existing eTenders parser; SKILL.md picks the parser by `profile_key`.
- **Profile-aware Excel generator.** `create_estimate.py` accepts `--profile-key` and emits £ or € number formats and profile-appropriate sample prelims rates.
- **Setup pre-flight.** Setup now detects an existing workspace and offers Update / Full reset / Cancel rather than silently overwriting.
- **Prime briefing header.** `/ailtir_prime` shows the active profile at the top of every session briefing.
- **Notion schema** extended with UK procurement routes (Procurement Act 2023 notice and procedure taxonomy) and UK subcontractor accreditation checkboxes (SSIP, CHAS, SafeContractor, Constructionline, ISO tiers, Modern Slavery statement).

### v2.12

- Removed all `${CLAUDE_PLUGIN_ROOT}` references from SKILL.md bodies — the variable doesn't resolve in Cowork. Script invocations and bundled-file references are now described in natural language so Claude resolves the absolute path itself from the SKILL.md's known location.
- Removed the plugin-root `scripts/` folder (telemetry wrappers and Python launchers). Outbound network is blocked in the Cowork sandbox; the telemetry pipeline has been silently dead there since the plugin migrated to Cowork.
- `feedback` skill now writes feedback to a local Markdown log in the user's workspace instead of POSTing to PostHog.
- Added the diagnostic `telemetry-test` skill for verifying sandbox capabilities (egress allowlist, path resolution, env var substitution) in any future Cowork deployment.

### v2.11

- Commands and skills unified — every workflow is now a skill under `skills/<name>/SKILL.md` and the slash command is `/<name>`.
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
