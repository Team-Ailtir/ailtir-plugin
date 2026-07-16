# Bid Planner Consolidation — Design

**Date:** 2026-07-16
**Status:** Approved for planning
**Plugin:** ailtir-cowork-plugin (v2.15.5 at time of writing)

## Problem

Running `/ailtir_bid-planner` today produces an inconsistent, malformed workbook,
and the conductor then re-recommends work the planner already did — so users end
up with duplicated effort and a scatter of Excel files per bid.

Root causes, confirmed by inspecting a real generated workbook
(`Bid_Plan_2026-001-AthenryNRR.xlsx`):

1. **The planner script and its prose disagree.** `create_bid_plan.py` builds
   only 5 tabs; the SKILL.md prose promises a "9-tab workbook" and instructs the
   model to improvise the rest with ad-hoc `openpyxl`. Result: 10 tabs, **two of
   them numbered "5."**, one official `5. Risk Register` left **empty** while the
   model's improvised `5. Contract Risk` sits beside it. Improvised tabs
   (Programme, RACI, Package Tracker, Clarifications) have different names and
   columns on every run.

2. **No analysis skill has a deterministic script.** `go-no-go`,
   `compliance-matrix`, and `contract-risk` have **no scripts at all** — every run
   improvises Excel structure. The output can still be excellent (see below)
   because the *reference material* is strong, but the *structure* drifts run to
   run.

3. **The planner and the standalone skills cover the same ground from the same
   reference files** — near-total content overlap, differing only in prose depth,
   which is not defined anywhere.

4. **The conductor re-recommends already-done work.** Its `phase-map` sequences
   `pre-bid` as separate steps (`compliance-matrix`, `contract-risk`, …) and lists
   `bid-planner` as merely an "alternative", so after the planner runs the
   conductor tells the user to run compliance/risk again from scratch.

## Key finding: where the value actually lives

Two real deep-dive workbooks the user generated
(`Contract_Risk_Register_…xlsx`, `Compliance_Matrix_…xlsx`) are **excellent**.
Their value is almost entirely in **content** that is deeply pack-specific and
analytical — e.g. "20-Working-Day Time Bar — Strict Condition Precedent,
Sub-clause 10.3"; "Retention 6% — Above Playbook Standard"; 24 mandatory
returnables each with owner, template-provided status, and specific notes. No
script can or should generate this.

This defines the deterministic boundary precisely:

- **Deterministic (script owns):** tab existence / order / names, column headers,
  Cover-tab layout and labels, styling (Ailtir palette, header fills, borders,
  column widths, freeze panes, autofilters), and Cover metadata *values* passed
  in as arguments.
- **Non-deterministic (model owns):** every data row — the risks, returnables,
  clause findings, actions, scores. This is the product and must stay
  model-generated.

The current failure is the inverse of what we want: today the model improvises
*structure* (badly) while the *analysis* is free. We pin the structure and keep
the analysis free.

## Architecture: two tiers

### Tier 1 — bid-planner (shallow, complete, one workbook + deck)

One deterministic workbook giving a scannable overview of *everything*, plus a
shareable Ailtir-branded `.pptx`. It is the first pass: "I can see, at a glance,
where this bid stands." Summary tabs explicitly hand off to the deep-dives.

### Tier 2 — deep-dive skills (full depth, own workbooks)

`ailtir_compliance-matrix`, `ailtir_contract-risk`, `ailtir_package-breakdown`
each get their own deterministic script producing a richer multi-tab workbook —
the "we're bidding, go deep" pass. Each writes its **own** file, never the
planner's, so nothing gets clobbered. Depth difference (summary vs full) is
defined in code, not improvised prose.

## The `--data <json>` skeleton pattern (applies to every script)

Every workbook script becomes a **typed skeleton**, never a content generator:

1. The model performs the analysis and emits a JSON blob matching a documented
   schema.
2. The script accepts `--data <path-to-json>` (or stdin), validates it, and
   deterministically renders it into fixed, styled tabs.
3. Structure, order, headers, and styling are guaranteed; content is free.

This beats today's "model calls openpyxl directly" (structure drift) and beats
"script hardcodes rows" (would kill the analysis). "A workbook with blank
structural rows is a failure" — the script builds every tab even when a data
section is empty, and the model must populate it.

## Tier 1 workbook — the 10 tabs

`create_bid_plan.py` is rewritten to build all ten deterministically. Tabs
4/5/6 are one-row-per-item *distillations* of the deep-dive workbooks (not
re-derivations), each ending with a bottom banner pointing to its deep-dive.

| #  | Tab                | Depth      | Notes |
|----|--------------------|------------|-------|
| 1  | Bid Summary        | overview   | Cover + headline go/no-go score + top gaps — the "one glance" tab |
| 2  | Document Register  | full-ish   | Doc list + gaps section (project-indexer logic) |
| 3  | Go / No-Go         | **full**   | Fully scored grid + gate checks + recommendation — **inlined** |
| 4  | Compliance Summary | summary    | Top returnables + award criteria, 1 row each. Banner → `/ailtir_compliance-matrix` |
| 5  | Risk Summary       | summary    | Top 5 risks with rating, 1 row each. Banner → `/ailtir_contract-risk` |
| 6  | Package Outline    | summary    | Trade list. Banner → `/ailtir_package-breakdown` |
| 7  | Bid Programme      | full-ish   | Key dates / milestones from the pack |
| 8  | Submission Rules   | full-ish   | Method, format, naming, deadlines — high-value, stands alone |
| 9  | BID TEAM RACI      | full-ish   | **Pre-populated from profile team members** where present, else roles |
| 10 | Clarifications Log | seed       | Pre-seeded pack-level issues |

Banner text on tabs 4/5/6, e.g.:
> *Summarised view. Run `/ailtir_compliance-matrix` for the full returnables
> tracker with templates, owners & deadlines.*

### Go/No-Go inlining

The full go/no-go logic (mandatory gates + 4-dimension weighted scoring) moves
*into* the planner. Scoring criteria live in a reference file the planner owns:
`references/{profile_key}/go-no-go-criteria.md` (the file the standalone skill
already reads). The script builds a fully-scored Tab 3.
`ailtir_go-no-go` **remains** as a thin standalone wrapper reading the same
reference file — one source of truth, planner does it completely, standalone
still available.

## Tier 2 deep-dive scripts

Structures derived from the user's real (excellent) workbooks, pinned in code;
rows filled by the model via `--data`.

### `ailtir_compliance-matrix` → `create_compliance_matrix.py`
- Tab 1 — Cover (project/ITT metadata)
- Tab 2 — Award Criterion & Evaluation
- Tab 3 — Mandatory Returnables (No., Ref, Document, Category, Template Provided, Status, Owner, Notes)
- Tab 4 — Submission Rules (method, deadlines, file format, naming)
- Tab 5 — Template & Document Gap Check

### `ailtir_contract-risk` → `create_risk_register.py`
- Tab 1 — Cover (contract form, schedule form, playbook base)
- Tab 2 — Risk Register (Ref, Description, Clause/Schedule Ref, Rating, Commercial Impact, Mitigation, Owner)
- Tab 3 — Schedule Part 1 / Contract Data (Part, Ref, Data Item, Value in Contract, Playbook Standard/Note)
- Tab 4 — Action Tracker (#, Risk Ref, Action, Who, Due By, Status, Notes)

### `ailtir_package-breakdown` → extend `create_package_register.py`
From 1 tab to: Package List, Scope Matrix, Flow-Down Register.

## Tier 1 deck

Adapt Contractor OS's kick-off-deck spec into an Ailtir-branded `.pptx` via a new
`create_bid_deck.js` (PptxGenJS), Ailtir navy/purple palette + logo, generated
from the workbook data. Internal working document, not a client pitch:
information-dense, project-specific on every slide, ends on actions. Core slides:
Title → Project Overview → Tender Pack Status → Submission Requirements → Bid
Programme → Work Packages → Top Risks → Immediate Actions. Adapts to price-only
tenders (skip quality sections).

## Conductor & phase-map changes

- Introduce a new completion result value **`summarised`**. When bid-planner
  finishes it writes `completed[]` entries for `ailtir_go-no-go`,
  `ailtir_compliance-matrix`, `ailtir_contract-risk`, and
  `ailtir_package-breakdown` with `result: summarised`.
- `go-no-go` specifically is upgraded to `result: proceed` by the planner (the
  planner does it *in full*), while compliance / risk / packages stay
  `summarised`.
- The conductor treats `summarised` as "overview done, deep pass still valuable".
  Its `pre-bid` recommendation for those skills is framed explicitly as a deep
  dive: *"Summarised in the bid plan — run for the full clause-by-clause review."*
  Never blind re-running.
- Pre-bid sequence after the planner: `bid-planner` → `ailtir_contract-risk` →
  `ailtir_compliance-matrix` → `ailtir_package-breakdown`.
- Deep-dive skills, on completion, upgrade their own entry from `summarised` to
  `proceed`.
- `bid-planner` is promoted in the phase-map from "alternative" to the canonical
  entry point of `pre-bid`.

## PROCESS.md — the documented lifecycle (onboarding artifact)

A new `PROCESS.md` at the plugin root, linked from the main README, lays out the
canonical bid lifecycle step-by-step so it doubles as onboarding material for new
users and team members:

- The two-tier model (shallow first pass → deep dives) and *why*.
- Phase-by-phase walk: opportunity → pre-bid (planner → deep dives) → estimating
  → submission → post-tender → delivery.
- Which skill owns which output, and which file each produces.
- The `summarised` vs `proceed` state semantics.
- The deterministic-skeleton vs model-analysis boundary (so future skill authors
  follow the same pattern).

A short "How this fits together" note is added to `ailtir_bid-planner/SKILL.md`
pointing at `PROCESS.md`.

## Out of scope

- No change to estimating / submission / delivery phase skills beyond the
  package-breakdown extension.
- Telemetry plumbing untouched (separate known issue).
- No change to the interactive HTML card mechanism in the conductor.

## Success criteria

1. `/ailtir_bid-planner` produces exactly 10 tabs, correctly numbered, no
   duplicates, no empty structural tabs, identical structure every run.
2. Deep-dive skills produce their fixed multi-tab structure every run, with
   model-generated content of the quality seen in the Athenry workbooks.
3. Running the planner then the conductor never asks the user to redo go/no-go,
   and frames compliance/risk/packages as deep dives, not repeats.
4. One planner workbook + at most one file per deep-dive per bid — no scatter.
5. `PROCESS.md` exists and reads as a coherent onboarding walkthrough.
