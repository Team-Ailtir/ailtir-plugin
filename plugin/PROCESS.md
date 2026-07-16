# The Ailtir Bid Lifecycle

This is the canonical, step-by-step process the Ailtir plugin runs a tender
through. It doubles as onboarding: read it top to bottom to understand how the
skills fit together and which file each one produces.

## The two-tier principle

Every analysis has two depths:

- **Tier 1 — the first pass (`ailtir_bid-planner`).** One workbook + one deck
  that summarise *everything* at a glance, so you can decide whether to commit.
  Go/No-Go is done in full here; compliance, risk, and packages are summarised
  (one row per item) with a banner pointing at the deep dive.
- **Tier 2 — the deep dives.** When you commit to bidding, dedicated skills
  produce their own richer workbooks: `ailtir_contract-risk` (clause-by-clause)
  and `ailtir_compliance-matrix` (full returnables tracker).

**Why:** you get a complete overview in one command without drowning in detail,
then go deep only where it matters — with no duplicated files, because the Tier-1
tabs are explicitly summaries and each deep dive writes its own file.

## How outputs are built (for skill authors)

Scripts own **structure** (tab titles, order, headers, styling, computed values);
the model owns **content** (every data row). Scripts take a `--data <json>`
payload the model assembles from its analysis. Core tabs are always built; a tab
with no applicable data is stamped with an N/A note, never deleted. Genuinely
tender-specific extra tabs are declared as `optional_tabs`. This keeps output
identical run-to-run while the analysis stays intelligent.

## The phases

| Phase | Skills (in order) | Key output |
|-------|-------------------|-----------|
| opportunity | `ailtir_go-no-go` (optional early screen) | score |
| pre-bid | `ailtir_bid-planner` → `ailtir_contract-risk` → `ailtir_compliance-matrix` → `ailtir_pqq-manager` | Bid plan workbook + deck; risk register; compliance matrix |
| estimating | `ailtir_package-breakdown` → `ailtir_takeoff` → `ailtir_subcontractor-enquiry` → `ailtir_prelims-builder` → `ailtir_bid-leveling` → `ailtir_cost-reconciliation` | Package register; priced estimate |
| submission | `ailtir_quality-writer` → `ailtir_programme-builder` → `ailtir_bid-assembly` → `ailtir_submission-preflight` | Compiled submission |
| post-tender | `ailtir_post-tender-interview` → `ailtir_case-study-generator` → `ailtir_feedback` | Debrief; case study |
| delivery | `ailtir_site-diary`, `ailtir_contract-admin` | Site records |

## Bid state and the conductor

Every bid's `README.md` carries YAML frontmatter recording `completed[]` skills.
Each entry has a `result`:

- `proceed` — done in full.
- `summarised` — the Tier-1 planner covered it at a glance; the deep dive is
  still worthwhile. `ailtir_conductor` surfaces these as the next step, framed as
  a deep dive, not a repeat. The deep-dive skill upgrades the entry to `proceed`.
- `skipped` — deliberately not done (with a reason).

Run `/ailtir_conductor` at any time to see where every bid stands and what to run
next.
