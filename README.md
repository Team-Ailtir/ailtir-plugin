# The Ailtir Co-Work Plugin

**The AI-native tender management platform for Irish construction contractors.**

Built for Claude. Covers the full CWMF tender lifecycle — from daily eTenders email alerts through estimating to post-award site diary.

---

## Quick Start

1. **Install** this plugin in Claude.
2. Run `/ailtir-cowork-plugin:setup` — a 7-question interview that builds your workspace `Context/` files.
3. Run `/ailtir-cowork-plugin:notion-setup` — creates your Bid Pipeline, CRM, Subcontractor Directory, and RFI Log in Notion.
4. Run `/ailtir-cowork-plugin:enable-monitor` — sets up the automated daily eTenders opportunity monitor.
5. For a live tender, drop the pack and run `/ailtir-cowork-plugin:bid-planner`.

---

## The Full Workflow

```
SETUP
  /ailtir-cowork-plugin:setup                         → Workspace interview → builds Context/ files
  /ailtir-cowork-plugin:notion-setup                  → Creates 4 Notion databases
  /ailtir-cowork-plugin:notion-second-brain           → (Optional) Advanced company knowledge base

EVERY SESSION
  /ailtir-cowork-plugin:prime                         → Syncs Notion cache, loads context, briefs Claude

PHASE 0 — OPPORTUNITY IDENTIFICATION
  /ailtir-cowork-plugin:opportunity-monitor    → Parse eTenders/OJEU daily email → filter → log to Notion

PHASE 1 — QUALIFY & PLAN (per tender)
  /ailtir-cowork-plugin:bid-planner                   → Master orchestrator: indexes, scores, extracts, flags risks
    └── ailtir-project-indexer   → ISO 19650 folder index + AI context files
    └── ailtir-go-no-go          → CIRI/Safe-T-Cert gates + weighted scoring
    └── ailtir-compliance-matrix → ITT requirements register
    └── ailtir-contract-risk     → PW-CF / RIAI clause-by-clause review

PHASE 2 — ESTIMATE & PRICE
  /ailtir-cowork-plugin:takeoff                → Quantity extraction from drawings (SCSI/NRM2 format)
  /ailtir-cowork-plugin:prelims-builder        → Priced Schedule of Preliminaries (ARM4 structure)
  /ailtir-cowork-plugin:estimating-workflow    → Full 4-step estimate: extract → schedule → price → reconcile
    └── ailtir-rate-library      → Current Irish SEO labour rates + SCSI benchmarks
    └── ailtir-cost-reconciliation → Gap check, double-count, benchmark vs SCSI €/m²

PHASE 3 — ENQUIRE & PROCURE
  /ailtir-cowork-plugin:package-breakdown      → Trade package register + scope matrix
  /ailtir-cowork-plugin:subcontractor-enquiry  → Enquiry packs per trade
  /ailtir-cowork-plugin:bid-leveling           → Quote comparison workbook

PHASE 4 — WRITE & SUBMIT
  /ailtir-cowork-plugin:pqq-manager            → PQQ completion or subcontractor evaluation
  /ailtir-cowork-plugin:rfi-generator          → Formal RFIs + Notion log
  /ailtir-cowork-plugin:quality-writer         → Method statements using win themes + frontmatter-filtered case studies
  /ailtir-cowork-plugin:programme-builder      → Tender programme (Gantt) + narrative
  /ailtir-cowork-plugin:bid-assembly           → Master submission document + reconciliation check
  /ailtir-cowork-plugin:submission-preflight   → Final compliance + eTenders portal checklist
  /ailtir-cowork-plugin:post-tender-interview  → Presentation outline + Q&A prep

POST-AWARD
  /ailtir-cowork-plugin:contract-admin         → PW-CF / RIAI notices (Delay, Variation, Additional Cost)
  /ailtir-cowork-plugin:site-diary             → Field notes → formal daily site diary
  /ailtir-cowork-plugin:case-study-generator   → Project data → case studies for future bids

INTELLIGENCE
  /ailtir-cowork-plugin:intelligence-builder   → Build and maintain the Intelligence/ knowledge base
  /ailtir-cowork-plugin:dashboard              → Live HTML bid pipeline dashboard
```

---

## Irish Market Calibration

This plugin is specifically calibrated for:

| Standard | Application |
|---|---|
| CWMF | PW-CF contract forms, SAQ/PQQ, Gate reviews, eTenders portal |
| RIAI 2025 | Standard private sector contract forms and risk positions |
| SEO (Construction) 2025 | Statutory labour rates (Aug 2025: Craftsperson €23.00/hr) |
| SCSI / Buildcost 2025 | Cost-per-m² benchmarks across all building types |
| ARM4 | Agreed Rules of Measurement for Preliminaries |
| NRM2 | Elemental cost structure for estimating |
| CIRI / Safe-T-Cert | Mandatory pre-qualification gates |
| ISO 19650 | Document naming and folder structure conventions |

---

## What's New in v2.7

### Command-First Plugin Interface

| Change | Detail |
|---|---|
| Scoped command surface | All user-facing workflows now appear as `/ailtir-cowork-plugin:*` commands |
| Hidden implementation skills | Workflow skills stay available to commands but no longer clutter the slash menu |
| Portable support paths | Setup resources and workflow scripts now use `${CLAUDE_PLUGIN_ROOT}` paths |
| Automated opportunity monitor | `/ailtir-cowork-plugin:enable-monitor` sets up scheduled daily eTenders monitoring via email connector |

---

## Connectors Required

| Connector | Required For | Priority |
|---|---|---|
| Notion | Database reads/writes | Required |
| Gmail or Microsoft 365 Outlook | Automated opportunity monitor | Required for monitor |
| Microsoft 365 / SharePoint | Document storage | Recommended |
| Google Drive | Alternative document storage | Optional |

See `CONNECTORS.md` for setup instructions.
