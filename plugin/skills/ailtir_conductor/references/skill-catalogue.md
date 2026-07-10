# Ailtir Skill Catalogue — What Each Skill Does

Customer-facing reference. When the user picks `e` (explain) in the conductor prompt, read the paragraph for the recommended skill and print it. Also useful as a scannable overview for new users.

Grouped by lifecycle phase. Each entry is three sentences: **what it does · when to run it · what it produces**.

---

## Setup & Session

### `ailtir_setup`
Runs the first-time onboarding interview and scaffolds the workspace folders (`Context/`, `Bids/`, `Intelligence/`, etc.). Run once when you install the plugin, or again with the "Update profile" branch if your region, vertical, or company details change. Produces `Context/profile.json`, `Context/company.md`, and the workspace `CLAUDE.md`.

### `ailtir_prime`
The daily session-start ritual — syncs Notion databases into a local cache and presents a briefing on active bids, pending tasks, and suggested focus. Run at the start of every working session. From run 2 onward it auto-invokes the conductor so you jump straight into the next action.

### `ailtir_conductor`
Scans every bid, tells you the phase it's in, and recommends the next skill to run. Run anytime you want a proactive "what should I do next" view across your pipeline. Uses the YAML frontmatter on each bid's README to compute recommendations.

### `ailtir_dashboard`
Renders a live HTML dashboard as a Claude artifact — bid pipeline, BD KPIs, subcontractor register, or RFI tracker. Run when you want a visual snapshot to share or reflect on. Also mirrors the conductor's phase and next-action recommendations per bid.

### `ailtir_notion-setup`
Builds the Notion CRM, Bid Pipeline, Subcontractor Directory, and RFI Log databases. Run once, after setup, if you use Notion as your business system. Every downstream skill reads/writes these databases via the Notion MCP.

### `ailtir_notion-second-brain`
Extends Notion with SOPs, cost-history, and lessons-learned databases. Run after `notion-setup` when you're ready to layer in operational knowledge. Feeds richer briefings in `ailtir_prime`.

---

## Opportunity & Pre-Bid Decision

### `ailtir_enable-monitor`
Schedules a daily cron that runs `ailtir_opportunity-monitor`. Run once to switch on automated pipeline monitoring. Requires the Ailtir mailbox to be configured.

### `ailtir_opportunity-monitor`
Scans the Ailtir opportunity mailbox, scores each new tender against your profile, and logs it to the Notion Bid Pipeline. Runs on a schedule (from `enable-monitor`) or on demand. Produces new Pipeline records and a `Context/notion-cache/opportunity-log-*.md` entry.

### `ailtir_go-no-go`
Scores a specific opportunity against the profile-appropriate gate criteria (CIRI, Safe-T-Cert, turnover for `ireland-gc`; SSIP, Modern Slavery, Building Safety Act for `uk-gc`). Run once per opportunity before committing bid-team hours. Produces a numeric score and a proceed/no-bid recommendation.

---

## Pre-Bid Setup

### `ailtir_bid-planner`
The Phase-1 orchestrator — indexes the tender pack, runs go/no-go, extracts compliance requirements, flags contract risks, and generates a 9-tab Bid Plan Workbook plus the `Bids/[BID]/` folder structure. Run once per new tender you commit to. Produces `Bid_Plan_[Project].xlsx` and the bid folder tree.

### `ailtir_project-indexer`
Indexes every document in a bid folder into markdown, catalogues drawings, splits multi-page drawing PDFs, and produces navigation files under `Bids/[BID]/0. AI Context/`. Run early — every other pre-bid skill benefits from indexed context. Produces `CLAUDE.md`, `project.md`, `drawings.md`, and split drawing PDFs.

### `ailtir_ingest`
Routes dropped files into the correct bid folder or Intelligence subfolder, updates Notion, and updates the bid README status line. Run whenever you drop new documents into the workspace root. Follows the Soul-Update Pattern to keep the README current.

### `ailtir_compliance-matrix`
Extracts every submission requirement, evaluation criterion, and mandatory returnable from the ITT. Run after indexing, before writing quality responses. Produces a matrix that `ailtir_bid-assembly` and `ailtir_submission-preflight` both consume.

### `ailtir_contract-risk`
Clause-by-clause review of the contract against the profile-appropriate playbook (PW-CF, RIAI, JCT, NEC4). Run once the contract form is identified. Produces a risk register with the top 5 risks and mitigation positions.

### `ailtir_pqq-manager`
Completes or evaluates a PQQ / SQ / Supplier Info form using data from `Context/company.md`. Run when the tender pack includes a PQQ. Produces draft PQQ responses.

### `ailtir_package-breakdown`
Breaks the works into trade packages with a scope matrix and a package register. Run after compliance matrix, before estimating starts. Produces `Package_Register_[Project].xlsx`.

---

## Estimating & Pricing

### `ailtir_estimating-workflow`
The Phase-4 orchestrator — chains takeoff → prelims → rate library → bid-leveling → cost reconciliation with a checkpoint at each step. Run as an alternative to invoking each estimating skill individually. Produces a fully priced estimate workbook.

### `ailtir_takeoff`
Extracts quantities from drawings and produces a NRM2-formatted takeoff register. Run as the first estimating step, once drawings are indexed. Produces `takeoff_register.xlsx`.

### `ailtir_rate-library`
Serves profile-appropriate current rates for the estimator. A lookup, not a phase step — used inside `estimating-workflow`, `prelims-builder`, and `cost-reconciliation`. Returns rate figures for the specific items requested.

### `ailtir_subcontractor-enquiry`
Drafts ITT letters for each trade package and packs them for issue. Run once packages are defined. Produces ITT letter markdown and a ZIP of the enquiry pack.

### `ailtir_bid-leveling`
Normalises subcontractor quotes into a like-for-like comparison — flags exclusions, contingencies, and scope gaps. Run as sub quotes come back. Produces `Quote_Comparison_[Package].xlsx`.

### `ailtir_prelims-builder`
Builds a priced schedule of preliminaries (ARM4 for `ireland-gc`, NRM1 for `uk-gc`). Run after takeoff, before cost reconciliation. Produces `prelims_schedule.xlsx`.

### `ailtir_cost-reconciliation`
Runs a final gap/benchmark check on the estimate against `references/{profile_key}/benchmarks.md`. Run as the last estimating step, before submission drafting. Produces a Reconciliation Report highlighting outliers.

### `ailtir_rfi-generator`
Drafts RFIs (or processes incoming answers), logs to the Notion RFI Log, and flags downstream docs that may now be stale (compliance matrix, contract risk, BOQ). Run whenever a gap or ambiguity is found. Produces a formatted RFI and an impact-cascade report.

---

## Submission

### `ailtir_programme-builder`
Builds a tender programme (CSV) and a narrative that explains the sequencing logic. Run once packages and prelims are locked. Produces `tender_programme.csv`.

### `ailtir_quality-writer`
Drafts technical, social value, and method statement responses using YAML metadata from your `Intelligence/` folder and the win themes reference. Run for each quality question in the ITT. Produces response drafts ready for review.

### `ailtir_bid-assembly`
Compiles the final submission as a master markdown document — pulls compliance matrix responses, quality drafts, prelims, and schedules into one deliverable. Run once quality-writer is complete. Produces the master submission document.

### `ailtir_submission-preflight`
Runs a deterministic pre-submit check against the compliance matrix — pass/fail on every returnable, format, and evaluation criterion. Run immediately before sending. Produces a Pass/Fail report; do not submit until this passes.

---

## Post-Tender

### `ailtir_post-tender-interview`
Preps the team for a post-tender interview using the win themes and the compliance matrix responses. Run when the client invites the team to interview. Produces `interview_prep.md`.

### `ailtir_case-study-generator`
Captures a debrief and, on wins, seeds a STAR-format case study for the `Intelligence/` folder. Run on `status: won` or `status: lost` — critical for feeding future `quality-writer` output. Produces a case-study markdown and debrief signals.

### `ailtir_feedback`
Prompts for a 1-10 rating and three follow-up questions on the bid experience. Run at the end of any bid; submits anonymous feedback through the public Ailtir MCP tool.

---

## Delivery (Won Bids)

### `ailtir_site-diary`
Turns rough site notes into a formal daily diary — flags any commercial triggers (delays, EW, CE, L&E) for follow-up. Run daily, or catch up at week's end. Produces `Site_Diary_YYYY-MM-DD.md` and flags to `contract-admin`.

### `ailtir_contract-admin`
Drafts formal contract notices — delay, early-warning, compensation event, loss & expense — using the profile-appropriate template. Run whenever `site-diary` flags a trigger. Produces formal notice letters ready for issue.

---

## Cross-Cutting Support

### `ailtir_intelligence-builder`
Captures case studies, method statements, and win themes in a structured YAML-fronted format. Run periodically, or when `case-study-generator` prompts you to. Feeds `quality-writer` — the more you populate, the better the auto-drafts get.
