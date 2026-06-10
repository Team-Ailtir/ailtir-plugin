# The Ailtir Co-Work Plugin

**The AI-native tender management platform for Irish construction contractors.**

Built for Claude. Covers the full CWMF tender lifecycle — from daily eTenders email alerts through estimating to post-award site diary.

---

## Quick Start

1. **Install** this plugin in Claude.
2. Run `/setup` — a 7-question interview that builds your workspace `Context/` files.
3. Run `/notion-setup` — creates your Bid Pipeline, CRM, Subcontractor Directory, and RFI Log in Notion.
4. Run `/enable-monitor` — sets up the automated daily eTenders opportunity monitor.
5. For a live tender, drop the pack and run `/bid-planner`.

---

## The Full Workflow

```
SETUP
  /setup                         → Workspace interview → builds Context/ files
  /notion-setup                  → Creates 4 Notion databases
  /notion-second-brain           → (Optional) Advanced company knowledge base

EVERY SESSION
  /prime                         → Syncs Notion cache, loads context, briefs Claude

PHASE 0 — OPPORTUNITY IDENTIFICATION
  /ailtir-opportunity-monitor    → Parse eTenders/OJEU daily email → filter → log to Notion

PHASE 1 — QUALIFY & PLAN (per tender)
  /bid-planner                   → Master orchestrator: indexes, scores, extracts, flags risks
    └── ailtir-project-indexer   → ISO 19650 folder index + AI context files
    └── ailtir-go-no-go          → CIRI/Safe-T-Cert gates + weighted scoring
    └── ailtir-compliance-matrix → ITT requirements register
    └── ailtir-contract-risk     → PW-CF / RIAI clause-by-clause review

PHASE 2 — ESTIMATE & PRICE
  /ailtir-takeoff                → Quantity extraction from drawings (SCSI/NRM2 format)
  /ailtir-prelims-builder        → Priced Schedule of Preliminaries (ARM4 structure)
  /ailtir-estimating-workflow    → Full 4-step estimate: extract → schedule → price → reconcile
    └── ailtir-rate-library      → Current Irish SEO labour rates + SCSI benchmarks
    └── ailtir-cost-reconciliation → Gap check, double-count, benchmark vs SCSI €/m²

PHASE 3 — ENQUIRE & PROCURE
  /ailtir-package-breakdown      → Trade package register + scope matrix
  /ailtir-subcontractor-enquiry  → Enquiry packs per trade
  /ailtir-bid-leveling           → Quote comparison workbook

PHASE 4 — WRITE & SUBMIT
  /ailtir-pqq-manager            → PQQ completion or subcontractor evaluation
  /ailtir-rfi-generator          → Formal RFIs + Notion log
  /ailtir-quality-writer         → Method statements using win themes + frontmatter-filtered case studies
  /ailtir-programme-builder      → Tender programme (Gantt) + narrative
  /ailtir-bid-assembly           → Master submission document + reconciliation check
  /ailtir-submission-preflight   → Final compliance + eTenders portal checklist
  /ailtir-post-tender-interview  → Presentation outline + Q&A prep

POST-AWARD
  /ailtir-contract-admin         → PW-CF / RIAI notices (Delay, Variation, Additional Cost)
  /ailtir-site-diary             → Field notes → formal daily site diary
  /ailtir-case-study-generator   → Project data → case studies for future bids

INTELLIGENCE
  /ailtir-intelligence-builder   → Build and maintain the Intelligence/ knowledge base
  /ailtir-dashboard              → Live HTML bid pipeline dashboard
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

## What's New in v2.6

### Intelligence Layer & Full Audit

| Change | Detail |
|---|---|
| YAML frontmatter metadata | All 5 Intelligence document types now have mandatory YAML frontmatter for smart filtering in `ailtir-quality-writer` |
| Brand compliance fix | `create_estimate.py` and `style_excel.py` corrected to use `#0A1128` navy exclusively — red indicators removed |
| Anthropic standard compliance | `[HUMAN INPUT REQUIRED]` flags and `Quality Checks` sections added to all 30 skills |
| Intelligence filtering | `ailtir-quality-writer` now scans frontmatter before reading case studies — sector, route, and value-proximity filtering |
| Automated opportunity monitor | `/enable-monitor` command sets up scheduled daily eTenders monitoring via email connector |

---

## Connectors Required

| Connector | Required For | Priority |
|---|---|---|
| Notion | Database reads/writes | Required |
| Gmail or Microsoft 365 Outlook | Automated opportunity monitor | Required for monitor |
| Microsoft 365 / SharePoint | Document storage | Recommended |
| Google Drive | Alternative document storage | Optional |

See `CONNECTORS.md` for setup instructions.
