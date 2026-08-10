# Bid Planner Richness — Design

**Date:** 2026-08-10
**Status:** Approved (design sections confirmed by user)
**Scope:** `ailtir_bid-planner` workbook depth + the shared `_xlsx_render.py` engine
**Version target:** plugin 2.16.0 → 2.17.0

---

## Problem

The v2.16.0 bid-planner consolidation made the workbook thinner. The
Boyce Street plan (built 17 Jul, post-refactor) is poorer than Athenry
(3 Jul, pre-refactor): the RACI collapsed to five rows with names crammed
into cells, Go/No-Go lost its mandatory gates and decision line, the cover
shrank to six fields, and the Document Register dropped from 29 rows to 10.

### Correction to the earlier diagnosis

An earlier investigation recorded this as "the refactor imposed narrower
schemas than the old free-form model generated — the container shrank."
That is not what happened, and the distinction changes the fix.

The pre-refactor script (`.test-harness/old-plugin/.../create_bid_plan.py`,
109 lines) built **five sheets, headers only, zero rows, and no RACI tab at
all**. Its Go/No-Go headers were `["Criteria", "Max Score", "Actual Score",
"Notes"]` — identical to today's. Athenry's people-as-columns matrix, eight
mandatory gates and eighteen-field cover were **improvised by the model
freehand with `openpyxl`** on top of an empty skeleton.

So v2.16.0 did not shrink a rich container. It replaced an empty one and
closed off the improvisation that had been filling it. The job is therefore
not to restore lost script capability but to decide what the deterministic
engine should be **capable of expressing**.

### Root cause

The refactor paid for determinism with the wrong currency. What was wanted
was predictable **presence and styling** — same tabs, same order, Ailtir
brand, no improvised duplicate tabs. What was implemented was fixed
**column shape**, a far heavier constraint, and the one that flattened the
content. The two are separable.

---

## Approach: three tiers, not two

| Tier | Owner | Covers |
|---|---|---|
| **Frame** | Script, non-negotiable | Which tabs exist, order, titles, brand styling, sheet-name sanitising, deep-dive banners |
| **Contract** | Script-declared minimum | Each tab declares required *elements*; validated, fails loudly |
| **Fill** | Model, per tender | Columns, section count, matrix width, row depth, extra sections |

Today Tier 2 does not exist and Tier 3 has been collapsed into Tier 1.
That is the whole defect.

**Guardrail:** the model still may not call `openpyxl` itself. It supplies
richer JSON; the engine remains the only thing that draws. This is what
preserves visual consistency while letting content breathe.

---

## Section 1 — Engine additions (`_xlsx_render.py`)

All changes additive; existing tabs must render byte-identically.

**a) Flexible headers.** `_render_grid` already takes headers as a
parameter. The change is in `merge_rows`: if the model supplies `"headers"`
for a tab or section, use them; otherwise fall back to the script's
declared headers. This single change unlocks the RACI matrix — the model
sends `["Activity", "D. Buachalla", "M. Ryan", ...]` and the grid renders
as wide as the team.

**b) Callout block.** New spec type for the Go/No-Go decision banner:
merged across tab width, amber fill (`F59E0B` — already in the palette,
currently unused), large bold text. Renders at the **top** of the tab so
the verdict is seen first.

**c) Model-extensible `sections`.** Today `merge_rows` iterates only the
script's declared sections and silently drops anything else. Change: after
the declared sections, append any extra sections the model supplied, with
their own heading and headers, in the order supplied.

**d) Contract validator.** Each tab spec may declare
`"requires": ["gates", "scoring", "decision"]`. If the payload is missing a
required element, the script exits non-zero naming the gap. This is what
stops silent degradation — the exact failure mode diagnosed above.

**Bundling:** `_xlsx_render.py` is bundled byte-identical across
`ailtir_bid-planner`, `ailtir_compliance-matrix` and `ailtir_contract-risk`
(verified same md5). All three copies get the same change, and
`test_render.py` is bundled alongside each — today it exists only under
`bid-planner`.

---

## Section 2 — Tab specs (`create_bid_plan.py`)

Depth tied to ownership. Five tabs open up; three stay deliberately thin.

### Go/No-Go — full rebuild
`requires: [gates, scoring, decision]`

- **Decision callout** at top: verdict, score, and — where a gate failed —
  which one. The script computes the verdict via
  `go_no_go_recommendation()`; the model cannot overrule it.
- **Gates section**, model-supplied headers, one row per gate *actually in
  the active profile's criteria file*: 4 for `ireland-gc`, 7 for `uk-gc`.
  The row count must flex by profile — precisely what the fixed schema
  could not do.
- **Scoring section**: the four weighted dimensions with max, actual, band
  hit and rationale.
- Model may append extra sections (e.g. Director sign-off on a marginal
  call).

### BID TEAM RACI — matrix
Script declares the first column (`Activity`) and requires at least one
more. The model supplies person/role columns from `Context/profile.json` or
`Context/company.md`; cells hold R/A/C/I. Falls back to role names when no
named team exists — never to the collapsed five-column form.

### Cover — flexible field list
Script keeps five guaranteed fields (Project, Client, Tender Return,
Procurement Route, Go/No-Go Score + Recommendation). The model appends
tender-specific extras after them: employer, location, value, contract
form, bond, tender validity, award criterion, programme duration, PSCS/PD,
query deadline, prepared-by. Athenry-level cover without hardcoding a field
set that will not suit every tender.

### Doc Register, Bid Programme, Clarifications — open depth
Headers unchanged; the `SKILL.md` row cap comes off. A 29-document pack
gets 29 register rows. The 29→10 drop was collateral from a blanket
instruction, not a decision about these tabs.

### Compliance, Risk Summary, Package Outline — unchanged, still thin
Fixed shape, one row per item / top-5 risks, banners retained. These
summarise real deep dives; enriching them would duplicate
`/ailtir_compliance-matrix` and `/ailtir_contract-risk` and undercut the
two-tier flow.

### Noted, not in scope
Go/No-Go stays fully inside the planner. The separate `ailtir_go-no-go`
skill writes no workbook and the planner already records it as `proceed`,
so no change is needed — but the duplication deserves its own look later.

---

## Section 3 — `SKILL.md` changes

The script can only render what the model sends, so `SKILL.md` changes in
step or the new capacity goes unused.

- **Step 2B (Go/No-Go):** rewrite to require the three-element shape — one
  gate row per gate in the profile criteria file, scoring rows with
  band-hit and rationale, `gate_fail` set from the gate results rather than
  judged loosely.
- **Step 2 header:** split the blanket "summary depth" framing. Tabs the
  planner owns in full (Go/No-Go, RACI, Doc Register, Programme,
  Clarifications) get **complete** depth — every document, every milestone,
  every gate. Tabs that summarise a later deep dive (Compliance, Risk,
  Package) stay at one row per item / top-5 risks and keep their banners.
  One instruction currently governs both, which is why the Doc Register
  lost 19 rows for no reason.
- **RACI instruction:** keep the existing "pre-populate from
  `Context/profile.json` / `Context/company.md`" line, but specify matrix
  output — named people as columns, activities as rows, R/A/C/I in cells.
  Role names only where no named team is available.
- **Payload example** (currently `SKILL.md` lines 82–101): this JSON block
  is the model's actual contract, so it is rewritten to show the new
  shapes — `headers` alongside `rows`, the Go/No-Go three-element
  structure, the RACI matrix, cover extras.
- **Quality Checks:** add gates rendered one row per profile gate; RACI is
  a matrix with ≥2 columns; Doc Register row count equals catalogued
  document count.
- **Version:** bump `plugin/.claude-plugin/plugin.json` 2.16.0 → 2.17.0, add
  a `## 2.17.0` CHANGELOG entry, and update the `plugin_version` string in
  the bid-planner usage-reporting block (`SKILL.md` line 18).
  **Only the bid-planner block changes** — the repo convention is that a
  skill's `plugin_version` is bumped only when that skill is touched
  (31 skills currently sit at 2.15.5, 4 at 2.16.0). Do not sweep the rest.
- The `openpyxl` prohibition stays exactly as-is.

---

## Section 4 — Testing and verification

TDD via the existing test files, following the pattern already there:
plain asserts, `if __name__ == "__main__"` runner, no pytest dependency.

**`test_render.py`** — engine-level, written before the engine changes:
- Model-supplied headers override script-declared ones; absent headers fall
  back to declared
- A wide matrix renders correctly — 6 headers in, 6 columns out
- Callout block renders merged, amber, at top of tab
- Extra model-supplied sections append after declared ones, in order
- Contract validator: a payload missing a `requires` element exits
  non-zero and names the missing element
- **All existing tests pass unchanged** — the regression guard proving the
  additive changes did not alter current rendering

**`test_bid_plan.py`** — spec-level:
- Go/No-Go declares all three required elements
- RACI declares `Activity` plus a minimum column count
- Cover renders the five guaranteed fields and appends model extras after
  them
- Existing threshold and gate-fail tests unchanged
  (`go_no_go_recommendation` logic is not changing)
- Banner test extended: the three summary tabs keep banners **and** the
  newly-opened tabs gain none

**End-to-end check.** Build a realistic payload for both profiles and
generate two workbooks — `ireland-gc` (4 gates) and `uk-gc` (7 gates).
Verify by reading the output back with `openpyxl`: gate row count matches
the profile, RACI is genuinely wide, decision callout present. This is the
check that answers "is it better than Athenry"; both files are shown to the
user.

**Bundling verification.** `md5sum` across all three `_xlsx_render.py`
copies to confirm they remain byte-identical, and run `test_render.py` in
each skill directory. The compliance-matrix and contract-risk workbooks
must be unaffected.

---

## Files in play

- `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py` — engine changes
- `plugin/skills/ailtir_compliance-matrix/scripts/_xlsx_render.py` — same, bundled
- `plugin/skills/ailtir_contract-risk/scripts/_xlsx_render.py` — same, bundled
- `plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py` — tab specs
- `plugin/skills/ailtir_bid-planner/scripts/test_render.py` — engine tests
- `plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py` — spec tests
- `plugin/skills/ailtir_compliance-matrix/scripts/test_render.py` — new, bundled
- `plugin/skills/ailtir_contract-risk/scripts/test_render.py` — new, bundled
- `plugin/skills/ailtir_bid-planner/SKILL.md` — depth rules, payload contract, version
- `plugin/.claude-plugin/plugin.json` — version bump 2.16.0 → 2.17.0
- `CHANGELOG.md` — new `## 2.17.0` entry above `## 2.16.0`

## Baseline (verified 2026-08-10)

- `test_render.py` (11 tests) and `test_bid_plan.py` (4 tests) both report
  `ALL PASS` before any change. These are the regression guard.
- `AMBER = "F59E0B"` is declared at `_xlsx_render.py:31` and referenced
  nowhere — free for the decision callout.
- All three `_xlsx_render.py` copies share md5 `7f5832c8...`.
- `test_render.py` currently exists only under `ailtir_bid-planner`.

## Out of scope

- Estimating-workbook fragmentation (deferred spec of its own)
- Conductor flow reconciliation (separate in-progress design)
- Merging or removing the standalone `ailtir_go-no-go` skill
- Any change to the kick-off deck (`create_bid_deck.js`)
