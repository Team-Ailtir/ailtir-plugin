# The Ailtir Bid Lifecycle

This is the canonical, step-by-step process the Ailtir plugin runs a tender
through. It doubles as onboarding: read it top to bottom to understand how the
skills fit together and which file each one produces.

> **Canonical sequence:** the skill order and phase boundaries in this document are derived from [`skills/ailtir_conductor/references/phase-map.md`](skills/ailtir_conductor/references/phase-map.md), which is the machine-readable source of truth. If you spot a discrepancy, phase-map is authoritative.

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
- `summarised` — touched but not completed in full; conductor surfaces it as the next step.
- `skipped` — deliberately not done (with a reason).

Run `/ailtir_conductor` at any time to see where every bid stands and what to run
next.
