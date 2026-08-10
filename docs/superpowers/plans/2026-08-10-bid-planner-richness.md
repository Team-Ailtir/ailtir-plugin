# Bid Planner Richness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the bid-plan workbook express rich, tender-specific shapes (a real RACI matrix, profile-driven Go/No-Go gates, a fuller cover) while the script keeps sole ownership of which tabs exist, their order, and their styling.

**Architecture:** Three-tier contract. The script owns the *frame* (tabs, order, titles, brand styling). Each tab spec declares its *required elements*, validated before render so a thin payload fails loudly instead of degrading silently. The model supplies the *fill* — headers, section count, matrix width, row depth. All engine changes are additive: existing tabs must render byte-identically. The model still never calls `openpyxl` itself.

**Tech Stack:** Python 3, `openpyxl`, plain-assert test files with a `if __name__ == "__main__"` runner (no pytest).

## Global Constraints

- Working directory for every path below: `C:/Users/DonaghBuachalla/Documents/AI-Workspace/DEV/projects/Ailtir/ailtir-plugin/ailtir-plugin`
- Branch: `bid-planner-richness` (already created, spec committed at `852554f`)
- `_xlsx_render.py` is bundled **byte-identical** into three skills: `ailtir_bid-planner`, `ailtir_compliance-matrix`, `ailtir_contract-risk`. There is no sync script — copying is manual. Baseline md5 of all three: `7f5832c88409aa414589e05ce0e12f9b`.
- Engine edits are made in the `ailtir_bid-planner` copy, then copied verbatim to the other two in Task 5. Do not hand-edit the sibling copies.
- All changes additive. These existing suites must stay green at every commit: `ailtir_bid-planner/scripts/test_render.py` (11 tests), `ailtir_bid-planner/scripts/test_bid_plan.py` (4 tests), `ailtir_compliance-matrix/scripts/test_compliance_matrix.py`, `ailtir_contract-risk/scripts/test_risk_register.py`. All report `ALL PASS` at baseline.
- Tests are run directly: `python3 test_render.py` (not via pytest). The runner prints `ALL PASS` or `N FAILED` and exits non-zero on failure.
- `AMBER = "F59E0B"` is already declared at `_xlsx_render.py:31` and referenced nowhere. Use it for the decision callout; do not add a new colour.
- Brand fonts already declared: `Space Grotesk` for headers/titles, `Inter` for body. Use the existing font constants.
- Version bump touches **only** the bid-planner skill: the repo convention is that a skill's `plugin_version` is bumped only when that skill is modified (31 skills sit at `2.15.5`, 4 at `2.16.0`). Do not sweep the other skills.
- Do not touch these files — they hold uncommitted work from a separate workstream: `plugin/PROCESS.md`, `plugin/README.md`, `plugin/skills/ailtir_conductor/SKILL.md`, `plugin/skills/ailtir_conductor/references/phase-map.md`, `plugin/skills/ailtir_setup/SKILL.md`, `plugin/skills/ailtir_takeoff/SKILL.md`.

---

## File Structure

| File | Responsibility |
|---|---|
| `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py` | Render engine. Gains flexible headers, column widths, callout block, extensible sections, contract validator. Edited here first. |
| `plugin/skills/ailtir_compliance-matrix/scripts/_xlsx_render.py` | Byte-identical copy (Task 5). |
| `plugin/skills/ailtir_contract-risk/scripts/_xlsx_render.py` | Byte-identical copy (Task 5). |
| `plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py` | Bid-plan tab specs. Go/No-Go rebuilt to three elements, RACI to a matrix, cover to a flexible field list. |
| `plugin/skills/ailtir_bid-planner/scripts/test_render.py` | Engine tests. Gains ~8 tests; existing 11 unchanged. Bundled to siblings in Task 5. |
| `plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py` | Spec tests. Gains ~5 tests; existing 4 unchanged. |
| `plugin/skills/ailtir_bid-planner/SKILL.md` | Depth rules, payload contract, version string. |
| `plugin/.claude-plugin/plugin.json`, `CHANGELOG.md` | Version 2.16.0 → 2.17.0. |

Tasks 1–4 build the engine bottom-up, each independently testable. Task 5 is the bundling gate. Tasks 6–8 consume the engine. Task 9 aligns the model's instructions. Task 10 proves the whole thing end-to-end against both profiles.

---

### Task 1: Flexible headers and column widths

The change that unlocks everything else: `merge_rows` currently discards any headers the model supplies, so tab shape is frozen at whatever the script declared.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py` (`_render_grid` ~line 110, `_render_tab` ~line 132, `merge_rows` ~line 161)
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_render.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `merge_rows(core_tabs, data)` honours a model-supplied `"headers"` list on any tab or section, falling back to the script-declared headers when absent. Tab and section specs accept an optional `"widths"` list of integers passed through to column sizing.

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py`, above the `if __name__ == "__main__":` block:

```python
def test_model_headers_override_declared():
    core = [{"key": "raci", "title": "8. RACI", "headers": ["Activity"]}]
    data = {"tabs": {"raci": {"headers": ["Activity", "A. Ryan", "B. Nolan"],
                              "rows": [["Pricing", "R", "C"]]}}}
    tabs = R.merge_rows(core, data)
    assert tabs[0]["headers"] == ["Activity", "A. Ryan", "B. Nolan"], tabs[0]["headers"]


def test_declared_headers_used_when_model_silent():
    core = [{"key": "docs", "title": "2. Docs", "headers": ["Filename", "Title"]}]
    tabs = R.merge_rows(core, {"tabs": {"docs": {"rows": [["a.pdf", "A"]]}}})
    assert tabs[0]["headers"] == ["Filename", "Title"], tabs[0]["headers"]


def test_wide_matrix_renders_all_columns():
    tabs = [{"title": "8. RACI",
             "headers": ["Activity", "P1", "P2", "P3", "P4", "P5"],
             "rows": [["Pricing", "R", "A", "C", "I", "I"]]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["8. RACI"]
    assert [ws.cell(row=1, column=c).value for c in range(1, 7)] == \
        ["Activity", "P1", "P2", "P3", "P4", "P5"]
    assert ws.cell(row=2, column=6).value == "I"


def test_section_headers_override_declared():
    core = [{"key": "gng", "title": "3. GNG", "sections": [
        {"key": "gates", "heading": "A. Gates", "headers": ["Gate"]}]}]
    data = {"tabs": {"gng": {"sections": {"gates": {
        "headers": ["#", "Gate", "Status"], "rows": [["1", "CIRI", "PASS"]]}}}}}
    tabs = R.merge_rows(core, data)
    assert tabs[0]["sections"][0]["headers"] == ["#", "Gate", "Status"]


def test_widths_applied():
    tabs = [{"title": "8. RACI", "headers": ["Activity", "P1"],
             "rows": [["Pricing", "R"]], "widths": [40, 8]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["8. RACI"]
    assert ws.column_dimensions["A"].width == 40
    assert ws.column_dimensions["B"].width == 8
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: FAIL on `test_model_headers_override_declared` (headers stay `["Activity"]`), `test_section_headers_override_declared`, and `test_widths_applied` (width is the default 22). The other two may already pass — `build_workbook` already renders whatever headers it is handed.

- [ ] **Step 3: Thread widths through the grid renderer**

In `_render_grid`, change the signature and the autosize call:

```python
def _render_grid(ws, start_row, headers, rows, na_note, widths=None):
```

and replace the `_autosize` line at the end of the function:

```python
    _autosize(ws, max(len(headers) if headers else 1, 1), widths)
```

- [ ] **Step 4: Pass widths from the tab and section specs**

In `_render_tab`, update both `_render_grid` calls. The sections branch:

```python
            r = _render_grid(ws, r, sec.get("headers", []), sec.get("rows", []),
                             sec.get("na_note"), sec.get("widths"))
```

and the flat branch:

```python
        r = _render_grid(ws, r, spec.get("headers", []), spec.get("rows", []),
                         spec.get("na_note"), spec.get("widths"))
```

- [ ] **Step 5: Honour model-supplied headers and widths in merge_rows**

In `merge_rows`, inside the `if "sections" in spec:` branch, after `sd = sd_all.get(base.get("key"), {})`, add:

```python
                ms["headers"] = sd.get("headers", base.get("headers", []))
                if "widths" in sd:
                    ms["widths"] = sd["widths"]
```

and in the `else:` branch, after `out["rows"] = d.get("rows", [])`, add:

```python
            out["headers"] = d.get("headers", spec.get("headers", []))
            if "widths" in d:
                out["widths"] = d["widths"]
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: `ALL PASS`, 16 tests. The 11 original tests must still pass — that is the proof this change is additive.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py \
        plugin/skills/ailtir_bid-planner/scripts/test_render.py
git commit -m "feat(render): honour model-supplied headers and column widths"
```

---

### Task 2: Decision callout block

A merged amber banner at the top of a tab, for the Go/No-Go verdict. Distinct from the existing `banner` (italic purple, bottom of tab, deep-dive pointer) — both must coexist.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py` (constants ~line 42, `_render_tab` ~line 132)
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_render.py`

**Interfaces:**
- Consumes: Task 1's `widths` threading (unchanged behaviour, no new coupling)
- Produces: a tab spec accepts `"callout": "<text>"`, rendered as row 1 merged across the tab width with amber fill and bold 12pt `Space Grotesk`. Tab content starts below it. `"banner"` continues to render last.

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py`:

```python
def test_callout_renders_at_top():
    tabs = [{"title": "3. GNG", "callout": "STRONG GO - 82/100",
             "headers": ["Criteria"], "rows": [["Client"]]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["3. GNG"]
    assert ws.cell(row=1, column=1).value == "STRONG GO - 82/100"
    # callout occupies row 1, row 2 is a blank spacer, content starts at row 3
    assert ws.cell(row=2, column=1).value is None
    assert ws.cell(row=3, column=1).value == "Criteria"


def test_callout_is_amber_and_merged():
    tabs = [{"title": "3. GNG", "callout": "NO-GO",
             "headers": ["A", "B", "C"], "rows": [["1", "2", "3"]]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["3. GNG"]
    assert ws.cell(row=1, column=1).fill.fgColor.rgb.endswith(R.AMBER)
    assert ws.cell(row=1, column=1).font.bold
    assert any(str(rng) == "A1:C1" for rng in ws.merged_cells.ranges), \
        [str(r) for r in ws.merged_cells.ranges]


def test_callout_coexists_with_banner():
    tabs = [{"title": "3. GNG", "callout": "MARGINAL GO", "banner": "Run deep dive",
             "headers": ["A"], "rows": [["1"]]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["3. GNG"]
    vals = [c.value for row in ws.iter_rows() for c in row if c.value]
    assert vals[0] == "MARGINAL GO", vals
    assert vals[-1] == "Run deep dive", vals


def test_callout_width_spans_widest_section():
    tabs = [{"title": "3. GNG", "callout": "GO", "sections": [
        {"heading": "A", "headers": ["x", "y"], "rows": [["1", "2"]]},
        {"heading": "B", "headers": ["p", "q", "r", "s"], "rows": [["1", "2", "3", "4"]]},
    ]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["3. GNG"]
    assert any(str(rng) == "A1:D1" for rng in ws.merged_cells.ranges), \
        [str(r) for r in ws.merged_cells.ranges]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: all four FAIL — `callout` is currently an unknown key, so row 1 holds the header instead.

- [ ] **Step 3: Add the callout style constants**

In `_xlsx_render.py`, after the `BANNER_FONT` line (~line 42), add:

```python
CALLOUT_FONT = Font(bold=True, color=NAVY, size=12, name="Space Grotesk")
CALLOUT_FILL = PatternFill("solid", fgColor=AMBER)
```

- [ ] **Step 4: Render the callout at the top of the tab**

In `_render_tab`, replace the opening two lines:

```python
def _render_tab(wb, spec):
    ws = wb.create_sheet(safe_sheet_title(spec["title"]))
    r = 1
```

with:

```python
def _render_tab(wb, spec):
    ws = wb.create_sheet(safe_sheet_title(spec["title"]))
    r = 1
    if spec.get("callout"):
        ncols = _tab_width(spec)
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
        ws.cell(row=r, column=1, value=spec["callout"])
        for c in range(1, ncols + 1):
            cell = ws.cell(row=r, column=c)
            cell.font = CALLOUT_FONT
            cell.fill = CALLOUT_FILL
            cell.alignment = CENTER
        r += 2
```

- [ ] **Step 5: Add the tab-width helper**

Immediately above `_render_tab`, add:

```python
def _tab_width(spec):
    """Widest column count on the tab — sections may differ in width."""
    sections = spec.get("sections")
    if sections:
        return max((len(s.get("headers", [])) for s in sections), default=1) or 1
    return max(len(spec.get("headers", [])), 1)
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: `ALL PASS`, 20 tests.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py \
        plugin/skills/ailtir_bid-planner/scripts/test_render.py
git commit -m "feat(render): add amber decision callout block"
```

---

### Task 3: Model-extensible sections

`merge_rows` iterates only the script's declared sections, so any extra section the model supplies is silently dropped. Extras are declared under an explicit `extra_sections` key — ordered, and impossible to confuse with a typo'd declared key.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py` (`merge_rows` ~line 161)
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_render.py`

**Interfaces:**
- Consumes: Task 1's header fallback in `merge_rows`
- Produces: on a sections-based tab, model data may include `"extra_sections": [{"heading": str, "headers": [str], "rows": [[str]]}]`. These are appended after the declared sections, in the order given. Ignored on flat tabs.

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py`:

```python
def test_extra_sections_appended_after_declared():
    core = [{"key": "gng", "title": "3. GNG", "sections": [
        {"key": "gates", "heading": "A. Gates", "headers": ["Gate"]}]}]
    data = {"tabs": {"gng": {
        "sections": {"gates": {"rows": [["CIRI"]]}},
        "extra_sections": [
            {"heading": "C. Director Sign-Off", "headers": ["Note"],
             "rows": [["Marginal - MD to confirm"]]}]}}}
    tabs = R.merge_rows(core, data)
    headings = [s["heading"] for s in tabs[0]["sections"]]
    assert headings == ["A. Gates", "C. Director Sign-Off"], headings
    assert tabs[0]["sections"][1]["rows"] == [["Marginal - MD to confirm"]]


def test_extra_sections_preserve_order():
    core = [{"key": "gng", "title": "3. GNG", "sections": [
        {"key": "gates", "heading": "A", "headers": ["G"]}]}]
    data = {"tabs": {"gng": {"extra_sections": [
        {"heading": "B", "headers": ["x"], "rows": [["1"]]},
        {"heading": "C", "headers": ["y"], "rows": [["2"]]}]}}}
    tabs = R.merge_rows(core, data)
    assert [s["heading"] for s in tabs[0]["sections"]] == ["A", "B", "C"]


def test_extra_sections_render():
    core = [{"key": "gng", "title": "3. GNG", "sections": [
        {"key": "gates", "heading": "A", "headers": ["G"]}]}]
    data = {"tabs": {"gng": {"sections": {"gates": {"rows": [["g1"]]}},
                             "extra_sections": [
                                 {"heading": "B", "headers": ["x"], "rows": [["v1"]]}]}}}
    wb = R.build_workbook({"fields": []}, R.merge_rows(core, data))
    vals = [c.value for row in wb["3. GNG"].iter_rows() for c in row if c.value]
    assert "B" in vals and "v1" in vals, vals
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: FAIL — `headings` is `["A. Gates"]`; extras are dropped.

- [ ] **Step 3: Append extras in merge_rows**

In `merge_rows`, inside the `if "sections" in spec:` branch, after the `for base in spec["sections"]:` loop finishes and before `out["sections"] = secs`, add:

```python
            for extra in d.get("extra_sections", []):
                secs.append({
                    "heading": extra.get("heading", ""),
                    "headers": extra.get("headers", []),
                    "rows": extra.get("rows", []),
                    "na_note": extra.get("na_note"),
                    "widths": extra.get("widths"),
                })
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: `ALL PASS`, 23 tests.

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py \
        plugin/skills/ailtir_bid-planner/scripts/test_render.py
git commit -m "feat(render): allow model-supplied extra sections"
```

---

### Task 4: Contract validator

The piece that stops silent degradation. A tab declares the elements it must have; a payload missing one exits non-zero naming the gap, rather than rendering a thin tab that looks intentional.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py` (add `validate_requirements` after `merge_rows`)
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_render.py`

**Interfaces:**
- Consumes: `merge_rows` output from Tasks 1 and 3
- Produces: `validate_requirements(tabs)` returns a list of human-readable problem strings (empty when satisfied). A tab spec may declare `"requires": [str]` where each entry is either `"callout"` or a declared section key, and `"min_columns": int` checked against the tab's header count. Callers exit non-zero on a non-empty result.

- [ ] **Step 1: Write the failing tests**

Append to `test_render.py`:

```python
def test_validate_passes_when_satisfied():
    tabs = [{"title": "3. GNG", "callout": "GO", "requires": ["gates", "callout"],
             "sections": [{"key": "gates", "heading": "A", "headers": ["G"],
                           "rows": [["CIRI"]]}]}]
    assert R.validate_requirements(tabs) == []


def test_validate_flags_empty_required_section():
    tabs = [{"title": "3. GNG", "requires": ["gates"],
             "sections": [{"key": "gates", "heading": "A", "headers": ["G"], "rows": []}]}]
    problems = R.validate_requirements(tabs)
    assert len(problems) == 1
    assert "gates" in problems[0] and "3. GNG" in problems[0], problems


def test_validate_flags_missing_callout():
    tabs = [{"title": "3. GNG", "requires": ["callout"], "headers": ["A"], "rows": [["1"]]}]
    problems = R.validate_requirements(tabs)
    assert len(problems) == 1 and "callout" in problems[0], problems


def test_validate_flags_narrow_matrix():
    tabs = [{"title": "8. RACI", "min_columns": 3,
             "headers": ["Activity", "Owner"], "rows": [["Pricing", "QS"]]}]
    problems = R.validate_requirements(tabs)
    assert len(problems) == 1
    assert "8. RACI" in problems[0] and "3" in problems[0], problems


def test_validate_ignores_tabs_without_requirements():
    tabs = [{"title": "2. Docs", "headers": ["A"], "rows": []}]
    assert R.validate_requirements(tabs) == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: FAIL with `AttributeError: module '_xlsx_render' has no attribute 'validate_requirements'`.

- [ ] **Step 3: Implement the validator**

At the end of `_xlsx_render.py`, after `merge_rows`, add:

```python
def validate_requirements(tabs):
    """Check each tab against its declared contract.

    Returns a list of problem strings — empty when every requirement is met.
    A `requires` entry is either "callout" or the key of a declared section,
    which must carry at least one row. `min_columns` guards shapes (such as a
    RACI matrix) that are meaningless below a certain width.
    """
    problems = []
    for spec in tabs:
        title = spec.get("title", "<untitled>")
        by_key = {s.get("key"): s for s in spec.get("sections", [])}
        for req in spec.get("requires", []):
            if req == "callout":
                if not spec.get("callout"):
                    problems.append(f"{title}: required decision callout is missing")
                continue
            sec = by_key.get(req)
            if sec is None:
                problems.append(f"{title}: required section '{req}' is not declared")
            elif not sec.get("rows"):
                problems.append(f"{title}: required section '{req}' has no rows")
        min_cols = spec.get("min_columns")
        if min_cols and len(spec.get("headers", [])) < min_cols:
            problems.append(
                f"{title}: needs at least {min_cols} columns, "
                f"got {len(spec.get('headers', []))}")
    return problems
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py
```

Expected: `ALL PASS`, 28 tests.

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py \
        plugin/skills/ailtir_bid-planner/scripts/test_render.py
git commit -m "feat(render): add tab requirement validator"
```

---

### Task 5: Bundle the engine to all three skills

The engine is bundled by manual copy because Cowork cannot do cross-skill Python imports. Copies must be byte-identical, and the two sibling skills must be provably unaffected.

**Files:**
- Overwrite: `plugin/skills/ailtir_compliance-matrix/scripts/_xlsx_render.py`
- Overwrite: `plugin/skills/ailtir_contract-risk/scripts/_xlsx_render.py`
- Create: `plugin/skills/ailtir_compliance-matrix/scripts/test_render.py`
- Create: `plugin/skills/ailtir_contract-risk/scripts/test_render.py`

**Interfaces:**
- Consumes: the finished engine from Tasks 1–4
- Produces: three byte-identical `_xlsx_render.py` copies, each with `test_render.py` alongside it

- [ ] **Step 1: Confirm the sibling suites are green before copying**

```bash
cd plugin/skills/ailtir_compliance-matrix/scripts && python3 test_compliance_matrix.py
cd ../../ailtir_contract-risk/scripts && python3 test_risk_register.py
```

Expected: `ALL PASS` from both. This is the before-state.

- [ ] **Step 2: Copy the engine and its tests**

From the repo root:

```bash
for skill in ailtir_compliance-matrix ailtir_contract-risk; do
  cp plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py \
     "plugin/skills/$skill/scripts/_xlsx_render.py"
  cp plugin/skills/ailtir_bid-planner/scripts/test_render.py \
     "plugin/skills/$skill/scripts/test_render.py"
done
```

- [ ] **Step 3: Verify the copies are byte-identical**

```bash
md5sum plugin/skills/*/scripts/_xlsx_render.py
```

Expected: three lines, all the same hash, and that hash is **not** the `7f5832c8...` baseline (it must have changed).

- [ ] **Step 4: Run every suite in all three skills**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py && python3 test_bid_plan.py
cd ../../ailtir_compliance-matrix/scripts && python3 test_render.py && python3 test_compliance_matrix.py
cd ../../ailtir_contract-risk/scripts && python3 test_render.py && python3 test_risk_register.py
```

Expected: `ALL PASS` six times. The sibling suites passing proves the engine changes are additive — those skills supply no `headers`, `callout`, or `requires`, so they must render exactly as before.

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/ailtir_compliance-matrix/scripts/_xlsx_render.py \
        plugin/skills/ailtir_contract-risk/scripts/_xlsx_render.py \
        plugin/skills/ailtir_compliance-matrix/scripts/test_render.py \
        plugin/skills/ailtir_contract-risk/scripts/test_render.py
git commit -m "chore: bundle updated render engine and tests to all three skills"
```

---

### Task 6: Rebuild the Go/No-Go tab

From four fixed columns to three elements: a decision callout, a gates section whose row count follows the active profile (4 gates for `ireland-gc`, 7 for `uk-gc`), and a weighted-scoring section.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py` (`CORE_TABS` ~line 36, `main` ~line 58)
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py`

**Interfaces:**
- Consumes: `R.validate_requirements` (Task 4), callout rendering (Task 2), section header override (Task 1), `extra_sections` (Task 3)
- Produces: the `go_no_go` tab spec carries `requires: ["gates", "scoring", "callout"]` and two declared sections keyed `gates` and `scoring`. `main()` sets the callout from `go_no_go_recommendation()` and exits `1` listing problems when validation fails.

- [ ] **Step 1: Write the failing tests**

Append to `test_bid_plan.py`, above the `if __name__ == "__main__":` block:

```python
def test_go_no_go_declares_three_elements():
    gng = {t["key"]: t for t in B.CORE_TABS}["go_no_go"]
    assert set(gng["requires"]) == {"gates", "scoring", "callout"}, gng.get("requires")
    keys = [s["key"] for s in gng["sections"]]
    assert keys == ["gates", "scoring"], keys


def test_go_no_go_sections_have_default_headers():
    gng = {t["key"]: t for t in B.CORE_TABS}["go_no_go"]
    for sec in gng["sections"]:
        assert len(sec["headers"]) >= 3, sec


def test_callout_text_includes_score_and_verdict():
    text = B.decision_callout(82, False)
    assert "82/100" in text and "Strong GO" in text, text


def test_callout_names_failed_gate():
    text = B.decision_callout(90, True)
    assert "NO-GO" in text and "gate" in text.lower(), text
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_bid_plan.py
```

Expected: FAIL — `go_no_go` has no `requires` or `sections` key, and `decision_callout` does not exist.

- [ ] **Step 3: Add the callout text builder**

In `create_bid_plan.py`, directly below `go_no_go_recommendation`, add:

```python
def decision_callout(score, gate_fail):
    """One-line verdict for the amber callout at the top of the Go/No-Go tab."""
    verdict = go_no_go_recommendation(score, gate_fail)
    if gate_fail:
        return f"DECISION: {verdict} — {score}/100 scored, but a mandatory gate failed"
    return f"DECISION: {verdict} — {score}/100"
```

- [ ] **Step 4: Replace the Go/No-Go tab spec**

In `CORE_TABS`, replace the two-line `go_no_go` entry:

```python
    {"key": "go_no_go", "title": "3. Go / No-Go",
     "headers": ["Criteria", "Max Score", "Actual Score", "Notes"]},
```

with:

```python
    {"key": "go_no_go", "title": "3. Go / No-Go",
     "requires": ["gates", "scoring", "callout"], "sections": [
         {"key": "gates", "heading": "A. Mandatory Gates (Pass / Fail)",
          "headers": ["#", "Gate", "Requirement", "Status", "Evidence / Notes"],
          "widths": [6, 26, 40, 12, 44]},
         {"key": "scoring", "heading": "B. Weighted Scoring Matrix",
          "headers": ["Dimension", "Max", "Actual", "Band Hit", "Rationale"],
          "widths": [30, 8, 8, 34, 50]},
     ]},
```

- [ ] **Step 5: Set the callout and validate in main()**

In `main`, replace this block:

```python
    recommendation = go_no_go_recommendation(score, gate_fail)
```

with:

```python
    recommendation = go_no_go_recommendation(score, gate_fail)
    callout = decision_callout(score, gate_fail)
```

Then replace:

```python
    tabs = R.merge_rows(CORE_TABS, data)
    wb = R.build_workbook(cover, tabs)
```

with:

```python
    tabs = R.merge_rows(CORE_TABS, data)
    for spec in tabs:
        if spec.get("key") == "go_no_go":
            spec["callout"] = callout
    if args.data:
        problems = R.validate_requirements(tabs)
        if problems:
            print("Payload is missing required content:", file=sys.stderr)
            for prob in problems:
                print(f"  - {prob}", file=sys.stderr)
            return 1
    wb = R.build_workbook(cover, tabs)
```

The `args.data` guard keeps `create_bid_plan.py --project X --output y.xlsx` working as an empty-template generator; validation applies only when a payload was supplied.

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_bid_plan.py && python3 test_render.py
```

Expected: `ALL PASS` from both. Note `test_core_tabs_are_the_eight_after_cover` must still pass — the tab title `"3. Go / No-Go"` is unchanged.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py \
        plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py
git commit -m "feat(bid-planner): Go/No-Go gains gates, scoring and decision callout"
```

---

### Task 7: RACI matrix and flexible cover

Two shape changes that only the model can size: the RACI's width follows the actual bid team, and the cover's field list follows the tender.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py` (`CORE_TABS` RACI entry, `main` cover block ~line 74)
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py`

**Interfaces:**
- Consumes: `min_columns` validation (Task 4), model header override (Task 1)
- Produces: the `team_raci` spec declares `["Activity"]` plus `min_columns: 3`. `build_cover(args, score, recommendation, data)` returns the cover dict — five guaranteed fields followed by any `cover.extra_fields` pairs from the payload.

- [ ] **Step 1: Write the failing tests**

Append to `test_bid_plan.py`:

```python
def test_raci_declares_matrix_shape():
    raci = {t["key"]: t for t in B.CORE_TABS}["team_raci"]
    assert raci["headers"] == ["Activity"], raci["headers"]
    assert raci["min_columns"] == 3, raci.get("min_columns")


def test_cover_has_five_guaranteed_fields():
    cover = B.build_cover_fields("Proj", "Client", "2026-09-01", "Open", 72, "Marginal GO", {})
    labels = [label for label, _ in cover]
    assert labels == ["Project Name:", "Client:", "Tender Return:",
                      "Procurement Route:", "Go/No-Go Score:", "Recommendation:"], labels


def test_cover_appends_model_extras_after_guaranteed():
    data = {"cover": {"extra_fields": [["Contract Value:", "EUR 2.4M"],
                                       ["Contract Form:", "PW-CF1"]]}}
    cover = B.build_cover_fields("P", "C", "D", "R", 80, "Strong GO", data)
    assert cover[-2] == ("Contract Value:", "EUR 2.4M"), cover[-2]
    assert cover[-1] == ("Contract Form:", "PW-CF1"), cover[-1]
    assert cover[0][0] == "Project Name:"


def test_cover_extras_absent_is_fine():
    cover = B.build_cover_fields("P", "C", "D", "R", 0, "NO-GO", {})
    assert len(cover) == 6
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_bid_plan.py
```

Expected: FAIL — `build_cover_fields` does not exist and the RACI entry still has five headers.

- [ ] **Step 3: Replace the RACI tab spec**

In `CORE_TABS`, replace:

```python
    {"key": "team_raci", "title": "8. BID TEAM RACI",
     "headers": ["Activity", "Responsible", "Accountable", "Consulted", "Informed"]},
```

with:

```python
    # Width follows the actual bid team — the model supplies one column per
    # person (or role, where no named team exists) and R/A/C/I in the cells.
    {"key": "team_raci", "title": "8. BID TEAM RACI",
     "headers": ["Activity"], "min_columns": 3},
```

- [ ] **Step 4: Add the cover field builder**

Below `decision_callout`, add:

```python
def build_cover_fields(project, client, return_date, route, score, recommendation, data):
    """Five guaranteed fields, then any tender-specific extras from the payload."""
    fields = [
        ("Project Name:", project),
        ("Client:", client),
        ("Tender Return:", return_date),
        ("Procurement Route:", route),
        ("Go/No-Go Score:", f"{score}/100"),
        ("Recommendation:", recommendation),
    ]
    for pair in data.get("cover", {}).get("extra_fields", []):
        if len(pair) >= 2:
            fields.append((pair[0], pair[1]))
    return fields
```

- [ ] **Step 5: Use the builder in main()**

Replace the whole `cover = {...}` literal in `main` with:

```python
    cover = {
        "title": f"AILTIR BID PLAN — {args.project.upper()}",
        "fields": build_cover_fields(
            args.project, args.client, args.return_date, args.route,
            score, recommendation if args.data else "TBC", data),
    }
```

- [ ] **Step 6: Run tests to verify they pass**

```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_bid_plan.py && python3 test_render.py
```

Expected: `ALL PASS` from both.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py \
        plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py
git commit -m "feat(bid-planner): RACI matrix shape and flexible cover fields"
```

---

### Task 8: Rewrite the SKILL.md depth rules and payload contract

The script can only render what the model sends. Without this task, the new capacity goes unused — this is where the regression is actually fixed for the user.

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/SKILL.md` (line 18 version; Step 2 header ~line 49-54; Step 2B ~line 60-64; payload example ~line 82-101; adaptation rules ~line 103-111; Quality Checks ~line 236-242)

**Interfaces:**
- Consumes: every shape from Tasks 6 and 7 — this file documents them as the model's contract
- Produces: nothing consumed by later tasks (Task 10 exercises the shapes directly)

- [ ] **Step 1: Split the depth instruction**

In Step 2, replace the paragraph beginning "This is the shallow-but-complete first pass." with:

```markdown
This is the first pass. Do all of the following analysis, then assemble a
single JSON object (the `--data` payload for Step 3). Do NOT call `openpyxl`
yourself and do NOT invoke sibling skills.

**Depth is not uniform — it follows ownership:**

- **Full depth** (the planner owns these outright): Go/No-Go, BID TEAM RACI,
  Document Register, Bid Programme, Clarifications Log. Be complete. Every
  document in the pack gets a register row; every gate in the profile criteria
  file gets a gate row; every milestone gets a programme row. Do not truncate
  these to keep the workbook short.
- **Summary depth** (a Tier-2 deep dive goes deeper later): Compliance &
  Submission, Risk Summary, Package Outline. One row per item, top 5 risks.
  These tabs carry a banner pointing at the deep dive.
```

- [ ] **Step 2: Rewrite Step 2B for the three-element shape**

Replace the body of "### B. Go/No-Go — full scoring (inlined)" with:

```markdown
Read `references/{profile_key}/go-no-go-criteria.md` from THIS skill's
directory. The tab has three parts and all three are mandatory — the script
will refuse to build the workbook if any is empty:

1. **Gates** — one row per mandatory gate **in that file**, not a fixed
   count. `ireland-gc` has 4 (accreditations, turnover, bonding/insurance,
   capacity); `uk-gc` has 7 (adds Building Safety Act, Modern Slavery Act,
   Carbon Reduction Plan). Columns: `#`, Gate, Requirement, Status
   (`PASS` / `FAIL` / `N/A`), Evidence / Notes. Cite the evidence from
   `Context/company.md` — never assume a gate passes.
2. **Scoring** — one row per weighted dimension (Client & Relationship 30,
   Sector & Experience 25, Commercial & Contract 25, Competition &
   Procurement 20). Columns: Dimension, Max, Actual, Band Hit (quote the band
   text you matched), Rationale.
3. **Decision** — set `score` to the scoring total and `gate_fail` to `true`
   if **any** gate row is `FAIL`. The script computes the verdict banner from
   these two values; do not write the verdict yourself.

Where the call is marginal, add a Director sign-off section via
`extra_sections`.
```

- [ ] **Step 3: Replace the payload example**

Replace the entire ```json block with:

```json
{
  "cover": {"extra_fields": [
      ["Employer:", "Galway County Council"], ["Location:", "Athenry, Co. Galway"],
      ["Contract Value:", "EUR 2.4M"], ["Contract Form:", "PW-CF1 (amended)"],
      ["Award Criterion:", "70% price / 30% quality"], ["Performance Bond:", "12.5%"],
      ["Tender Validity:", "90 days"], ["Query Deadline:", "2026-02-07"],
      ["PSCS:", "Contractor"], ["Prepared By:", "D. Buachalla"]]},
  "tabs": {
    "document_register": {"rows": [["file.pdf","Title","Spec","P1","2026-01-01","note"]]},
    "go_no_go": {
      "score": 72, "gate_fail": false,
      "sections": {
        "gates": {"rows": [
            ["1","Accreditations","Safe-T-Cert + CIRI","PASS","Both current — company.md"],
            ["2","Turnover","1.5x annualised value","PASS","EUR 12M avg vs EUR 2.4M"],
            ["3","Bonding / Insurance","12.5% bond + PI","PASS","Facility confirmed"],
            ["4","Capacity","Team free for Q2 start","FAIL","PM committed elsewhere"]]},
        "scoring": {"rows": [
            ["Client & Relationship","30","20","Known client, neutral history","Two prior contracts"],
            ["Sector & Experience","25","15","Adjacent sector, similar studies","No identical scheme"],
            ["Commercial & Contract","25","17","Heavily amended, negotiable","Time bar at 20 days"],
            ["Competition & Procurement","20","20","Negotiated or 2-stage","Restricted list of 5"]]}},
      "extra_sections": [
        {"heading": "C. Director Sign-Off", "headers": ["Item","Note"],
         "rows": [["Capacity gate","MD to confirm PM release before commitment"]]}]},
    "compliance_submission": {"sections": {
        "returnables": {"rows": [["Vol B","Form of Tender","Pass/Fail","YES","Director"]]},
        "submission_rules": {"rows": [["Deadline","28/02 16:00 via eTenders"]]}}},
    "risk_summary": {"rows": [["CR-01","20-day time bar","RED","Loss of EOT","Notice register"]]},
    "package_outline": {"rows": [], "na_note": "N/A at plan stage — see enquire-and-procure phase."},
    "bid_programme": {"rows": [["Query deadline","2026-02-07","Bid Mgr",""]]},
    "team_raci": {
      "headers": ["Activity","D. Buachalla","M. Ryan","S. Nolan","T. Byrne"],
      "widths": [34, 16, 16, 16, 16],
      "rows": [["Pricing / BOQ","A","R","C","I"],
               ["Quality submission","A","C","R","I"],
               ["Programme","C","A","I","R"]]},
    "clarifications": {"rows": [["CL-01","Portal access?","2026-01-10","Open",""]]}
  },
  "optional_tabs": [
    {"title": "Design Risk", "headers": ["Item","Note"], "rows": [["PI cover","Fitness-for-purpose flagged"]]}
  ]
}
```

- [ ] **Step 4: Update the adaptation rules**

Replace the "Adaptation rules" bullet list with:

```markdown
**Adaptation rules (fixed frame, flexible shape):**
- The 9 core tabs are always built, in order, with Ailtir styling. You cannot
  add, remove, reorder or restyle them, and you must never call `openpyxl`
  yourself.
- Within a tab you choose the shape: `headers` sizes a tab or section to this
  tender, `widths` sets column widths, `extra_sections` adds a section a
  sections-based tab needs. Omit `headers` to accept the script's default.
- **RACI must be a matrix.** Supply one column per bid team member from
  `Context/profile.json` / `Context/company.md`, with R/A/C/I in the cells.
  Use role names only where no named team exists. A minimum of 3 columns is
  enforced; a single "Owner" column will be rejected.
- If a summary-depth core section does not apply, supply `"rows": []` with an
  `"na_note"` explaining why. Never omit a core tab to "clean up". This does
  not apply to Go/No-Go — its gates and scoring are always required.
- Add to `optional_tabs` ONLY when the tender genuinely needs a tab the core
  set lacks — e.g. `Design Risk` on D&B, `Lots` on a multi-lot tender.
```

- [ ] **Step 5: Update Quality Checks and the version string**

Replace the compliance-depth check line with these four:

```markdown
- [ ] Go/No-Go gates: exactly one row per mandatory gate in the active profile's criteria file (4 for `ireland-gc`, 7 for `uk-gc`), each with cited evidence.
- [ ] Go/No-Go scoring: all four weighted dimensions present with the matched band quoted.
- [ ] BID TEAM RACI is a matrix — one column per team member, R/A/C/I in cells, at least 3 columns.
- [ ] Document Register row count equals the number of documents catalogued in Step 2A (no truncation).
- [ ] Compliance & Submission, Risk Summary and Package Outline are at summary depth (the full trackers are the Tier-2 deep dives).
```

Then on line 18, change `2.16.0` to `2.17.0`.

- [ ] **Step 6: Verify the edits landed**

```bash
grep -n "2.17.0\|Full depth\|min_columns\|must be a matrix" plugin/skills/ailtir_bid-planner/SKILL.md
grep -c "2.16.0" plugin/skills/ailtir_bid-planner/SKILL.md
```

Expected: the first command shows the new content; the second prints `0`.

- [ ] **Step 7: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/SKILL.md
git commit -m "docs(bid-planner): depth by ownership, richer payload contract"
```

---

### Task 9: Version bump and changelog

**Files:**
- Modify: `plugin/.claude-plugin/plugin.json:3`
- Modify: `CHANGELOG.md` (insert above `## 2.16.0 - 2026-07-16`)

**Interfaces:**
- Consumes: the `2.17.0` string set in Task 8
- Produces: nothing

- [ ] **Step 1: Bump the manifest**

In `plugin/.claude-plugin/plugin.json`, change `"version": "2.16.0"` to `"version": "2.17.0"`.

- [ ] **Step 2: Add the changelog entry**

Insert directly above the `## 2.16.0 - 2026-07-16` heading:

```markdown
## 2.17.0 - 2026-08-10

- Bid-planner workbook regains full richness inside the deterministic frame.
  Tab *shape* is now model-supplied (headers, column widths, extra sections)
  while the script keeps sole ownership of which tabs exist, their order and
  their styling.
- Go/No-Go rebuilt into three mandatory elements: a pass/fail gates section
  sized to the active profile (4 gates for `ireland-gc`, 7 for `uk-gc`), a
  weighted scoring section with the matched band quoted, and an amber
  decision callout computed by the script.
- BID TEAM RACI is a real matrix again — one column per bid team member with
  R/A/C/I in the cells, replacing the five fixed columns that collapsed names
  into single cells.
- Bid Summary cover takes tender-specific extra fields (value, contract form,
  bond, award criterion, PSCS and so on) after the five guaranteed fields.
- New payload validator: a workbook build now fails loudly and names the gap
  when required content is missing, instead of silently rendering a thin tab.
- Document Register, Bid Programme and Clarifications are no longer capped —
  depth now follows whether a Tier-2 deep dive exists, so only Compliance,
  Risk and Package Outline stay at summary depth.
```

- [ ] **Step 3: Verify no stale version references**

```bash
grep -rn "2\.16\.0" plugin/.claude-plugin/plugin.json plugin/skills/ailtir_bid-planner/
```

Expected: no output.

- [ ] **Step 4: Commit**

```bash
git add plugin/.claude-plugin/plugin.json CHANGELOG.md
git commit -m "chore: bump plugin to 2.17.0"
```

---

### Task 10: End-to-end verification against both profiles

The check that actually answers "is it better than Athenry". Both profiles must be exercised, because the gate count differing between them is the whole point of the flexible shape.

**Files:**
- Create (temporary, not committed): `/tmp/bid_plan_ie.json`, `/tmp/bid_plan_uk.json`, `/tmp/verify_bid_plan.py`

**Interfaces:**
- Consumes: everything from Tasks 1–9
- Produces: two generated workbooks for user review

- [ ] **Step 1: Build the Ireland payload (4 gates)**

Write `/tmp/bid_plan_ie.json` using the exact payload from Task 8 Step 3 (it is an `ireland-gc` example with 4 gate rows and a failing capacity gate).

- [ ] **Step 2: Build the UK payload (7 gates)**

Write `/tmp/bid_plan_uk.json` as a copy of the Ireland payload with `gate_fail` set to `false`, the capacity gate `Status` set to `PASS`, and these seven gate rows:

```json
[["1","Accreditations","SSIP + ISO 9001/14001/45001","PASS","CHAS Premium current"],
 ["2","Turnover","1.5x annualised value","PASS","GBP 18M avg vs GBP 3.1M"],
 ["3","Bonding / Insurance","10% bond + PCG + PI","PASS","Facility confirmed"],
 ["4","Capacity","Team free for Q3 start","PASS","Site team released from Leeds"],
 ["5","Building Safety Act 2022","PC competency if HRB","N/A","Not a higher-risk building"],
 ["6","Modern Slavery Act 2015","s.54 statement if turnover >= GBP 36m","N/A","Turnover below threshold"],
 ["7","Carbon Reduction Plan","PPN 06/20 for central gov >GBP 5m/yr","PASS","CRP published 2026-01"]]
```

- [ ] **Step 3: Generate both workbooks**

```bash
cd plugin/skills/ailtir_bid-planner/scripts
python3 create_bid_plan.py --output /tmp/Bid_Plan_IE.xlsx --project "Athenry NRR" \
  --client "Galway County Council" --return-date "2026-02-28" \
  --route "CWMF Restricted" --data /tmp/bid_plan_ie.json
python3 create_bid_plan.py --output /tmp/Bid_Plan_UK.xlsx --project "Leeds Depot" \
  --client "Leeds City Council" --return-date "2026-03-14" \
  --route "Open Procedure" --data /tmp/bid_plan_uk.json
```

Expected: two `Created ...` lines. The Ireland one reports `NO-GO (mandatory gate failed)` because its capacity gate is `FAIL`, despite scoring 72.

- [ ] **Step 4: Verify the validator rejects a thin payload**

```bash
cd plugin/skills/ailtir_bid-planner/scripts
python3 -c "import json;d=json.load(open('/tmp/bid_plan_ie.json'));d['tabs']['go_no_go']['sections']['gates']['rows']=[];json.dump(d,open('/tmp/bid_plan_thin.json','w'))"
python3 create_bid_plan.py --output /tmp/should_not_exist.xlsx --project "X" \
  --data /tmp/bid_plan_thin.json; echo "exit=$?"
```

Expected: `exit=1`, a message naming the empty `gates` section, and no `/tmp/should_not_exist.xlsx` created.

- [ ] **Step 5: Read both workbooks back and assert the shapes**

Write `/tmp/verify_bid_plan.py`:

```python
from openpyxl import load_workbook

EXPECTED_TABS = ["1. Bid Summary", "2. Document Register", "3. Go - No-Go",
                 "4. Compliance & Submission", "5. Risk Summary", "6. Package Outline",
                 "7. Bid Programme", "8. BID TEAM RACI", "9. Clarifications Log",
                 "Design Risk"]


def check(path, expected_gates, expect_gate_fail):
    wb = load_workbook(path)
    assert wb.sheetnames == EXPECTED_TABS, wb.sheetnames

    gng = wb["3. Go - No-Go"]
    assert "DECISION:" in str(gng.cell(row=1, column=1).value), "no decision callout"
    if expect_gate_fail:
        assert "NO-GO" in gng.cell(row=1, column=1).value
    col_a = [str(c.value or "") for c in gng["A"]]
    gates = [v for v in col_a if v.isdigit()]
    assert len(gates) == expected_gates, f"{path}: {len(gates)} gates, want {expected_gates}"
    assert any("Weighted Scoring" in str(c.value) for c in gng["A"]), "no scoring section"
    assert any("Director Sign-Off" in str(c.value) for c in gng["A"]), "no extra section"

    raci = wb["8. BID TEAM RACI"]
    width = sum(1 for c in raci[1] if c.value)
    assert width >= 4, f"{path}: RACI only {width} columns wide"
    assert raci.cell(row=2, column=2).value in ("R", "A", "C", "I"), "no R/A/C/I in grid"

    cover = wb["1. Bid Summary"]
    labels = [str(c.value) for c in cover["A"] if c.value]
    assert len(labels) > 6, f"{path}: cover has only {len(labels)} fields"
    assert "Contract Form:" in labels, labels

    risk = wb["5. Risk Summary"]
    assert any("contract-risk" in str(c.value) for c in risk["A"]), "lost deep-dive banner"
    print(f"OK {path}: {len(gates)} gates, RACI {width} cols, {len(labels)} cover fields")


check("/tmp/Bid_Plan_IE.xlsx", 4, True)
check("/tmp/Bid_Plan_UK.xlsx", 7, False)
print("E2E PASS")
```

Run: `python3 /tmp/verify_bid_plan.py`
Expected: two `OK` lines then `E2E PASS`.

- [ ] **Step 6: Confirm the full suite and bundling are still intact**

```bash
md5sum plugin/skills/*/scripts/_xlsx_render.py
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py && python3 test_bid_plan.py
cd ../../ailtir_compliance-matrix/scripts && python3 test_render.py && python3 test_compliance_matrix.py
cd ../../ailtir_contract-risk/scripts && python3 test_risk_register.py
```

Expected: three identical hashes, `ALL PASS` five times.

- [ ] **Step 7: Show the user both workbooks**

Present `/tmp/Bid_Plan_IE.xlsx` and `/tmp/Bid_Plan_UK.xlsx` for review, calling out the gate-count difference (4 vs 7), the RACI matrix width, and the decision callout. This is the human gate on "is it actually better" — do not consider the plan complete until the user has looked.

- [ ] **Step 8: Commit the verification script**

```bash
mkdir -p plugin/skills/ailtir_bid-planner/scripts/fixtures
cp /tmp/bid_plan_ie.json plugin/skills/ailtir_bid-planner/scripts/fixtures/example_ireland.json
cp /tmp/bid_plan_uk.json plugin/skills/ailtir_bid-planner/scripts/fixtures/example_uk.json
git add plugin/skills/ailtir_bid-planner/scripts/fixtures/
git commit -m "test(bid-planner): add worked payload fixtures for both profiles"
```

The fixtures are worth keeping — they double as worked examples of the payload contract for anyone editing `SKILL.md` later.

---

## Self-Review

**Spec coverage:**

| Spec section | Task |
|---|---|
| §1a flexible headers | Task 1 |
| §1b callout block | Task 2 |
| §1c model-extensible sections | Task 3 |
| §1d contract validator | Task 4 |
| §1 bundling to 3 skills + test_render.py alongside each | Task 5 |
| §2 Go/No-Go three elements, profile-driven gates | Task 6 |
| §2 RACI matrix | Task 7 |
| §2 flexible cover | Task 7 |
| §2 Doc Register / Programme / Clarifications open depth | Task 8 (`SKILL.md` cap removal — no script change needed, headers unchanged) |
| §2 Compliance / Risk / Package stay thin | Task 8 depth rules; asserted by Task 10 Step 5 banner check |
| §3 Step 2B rewrite, depth split, RACI instruction, payload example, quality checks, version | Task 8 |
| §3 version convention (bid-planner only) | Tasks 8 and 9 |
| §4 engine tests | Tasks 1–4 |
| §4 spec tests | Tasks 6, 7 |
| §4 E2E both profiles | Task 10 |
| §4 bundling verification | Task 5 Step 4, Task 10 Step 6 |

No gaps.

**Placeholder scan:** No TBD/TODO. Every code step carries the actual code; every test step carries the actual assertions; every run step carries the exact command and expected output.

**Type consistency:** `validate_requirements(tabs) -> list[str]` defined in Task 4, called in Task 6 Step 5 and asserted in Task 4 Step 1. `decision_callout(score, gate_fail) -> str` defined in Task 6 Step 3, tested in Task 6 Step 1. `build_cover_fields(project, client, return_date, route, score, recommendation, data) -> list[tuple]` defined in Task 7 Step 4, called in Task 7 Step 5 with matching positional order, tested in Task 7 Step 1. `_tab_width(spec) -> int` defined in Task 2 Step 5, used in Task 2 Step 4. `_render_grid(..., widths=None)` signature changed in Task 1 Step 3, both call sites updated in Task 1 Step 4. Spec keys are consistent throughout: `headers`, `widths`, `callout`, `banner`, `requires`, `min_columns`, `sections`, `extra_sections`, `na_note`, `rows`, `key`, `title`, `heading`.

One deliberate naming note: the test in Task 7 refers to `B.build_cover_fields`, matching the `import create_bid_plan as B` alias already used in `test_bid_plan.py:5`.
