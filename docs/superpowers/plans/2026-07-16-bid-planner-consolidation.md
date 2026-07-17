# Bid Planner Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/ailtir_bid-planner` produce one deterministic 9-core-tab workbook (plus a shareable `.pptx` deck) as a shallow first pass, and give the `compliance-matrix` and `contract-risk` deep-dives their own deterministic multi-tab workbooks — so structure is code-owned and never improvised, while analytical content stays model-generated.

**Architecture:** A shared, testable Python render engine (`_xlsx_render.py`) turns declarative tab specs + model-supplied `--data` JSON into styled workbooks. Each skill script defines its fixed `CORE_TABS` skeleton; the model does the analysis, emits JSON rows, and the script renders deterministically. The conductor gains a `summarised` completion state so it frames deep-dives as depth passes, not repeats. A `PROCESS.md` documents the lifecycle as onboarding material.

**Tech Stack:** Python 3 + openpyxl 3.1.5 (workbooks), Node.js + PptxGenJS (deck), Markdown (skills, phase-map, docs).

## Global Constraints

- **Runtime:** Cowork sandbox. Scripts are invoked by absolute path; cwd is the session root, NOT the skill dir. Anchor all imports via `sys.path.insert(0, str(Path(__file__).resolve().parent))`. NO cross-skill Python imports — bundle `_xlsx_render.py` verbatim into each skill's `scripts/` dir.
- **No test framework installed.** Tests are plain `python3` scripts using `assert`, runnable with `python3 <test_file>.py`, exiting non-zero on failure. Do NOT introduce pytest.
- **Determinism boundary:** scripts own tab existence/order/titles, column headers, styling (Ailtir palette), cover layout, and computed values (go/no-go recommendation). The model owns every data row. A core tab with no applicable data is still built and stamped with an N/A note — never deleted.
- **Ailtir palette (verbatim):** Navy `0A1128`, Purple `7C3AED`, Light `F5F7FA`, White `FFFFFF`, Amber `F59E0B`. Header font `Space Grotesk`, body font `Inter`. Never prefix hex with `#`.
- **Slash-command copy:** always the short form `/ailtir_<name>` in any user-facing text, never the fully-qualified `/ailtir-cowork-plugin:ailtir_<name>` form.
- **Version:** bump `plugin/.claude-plugin/plugin.json` and every touched SKILL.md `plugin_version:` string from `2.15.5` to `2.16.0`; add a `CHANGELOG.md` entry.
- **Plugin root:** `plugin/`. Skills live in `plugin/skills/ailtir_<name>/`.

---

### Task 1: Shared workbook render engine

**Files:**
- Create: `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py`
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_render.py`

**Interfaces:**
- Produces:
  - `load_data(path: str | None) -> dict` — read `--data` JSON, `{}` if path is None.
  - `build_workbook(cover: dict, tabs: list) -> Workbook` — cover dict `{sheet_title?, title, fields: [(label,value)]}`; each tab spec `{title, headers?, rows?, na_note?, banner?, sections?}`. Sections spec: `{heading, headers, rows, na_note?}`.
  - `merge_rows(core_tabs: list, data: dict) -> list` — fill each core tab's `rows` from `data["tabs"][spec["key"]]`, honour per-section `key`, append `data["optional_tabs"]` verbatim.

- [ ] **Step 1: Write the failing test**

Create `plugin/skills/ailtir_bid-planner/scripts/test_render.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R


def test_builds_cover_and_tabs():
    cover = {"title": "T", "fields": [("Project:", "X")]}
    tabs = [{"title": "2. Docs", "headers": ["A", "B"], "rows": [["1", "2"]]}]
    wb = R.build_workbook(cover, tabs)
    assert wb.sheetnames == ["1. Bid Summary", "2. Docs"], wb.sheetnames
    ws = wb["2. Docs"]
    assert ws.cell(row=1, column=1).value == "A"
    assert ws.cell(row=2, column=1).value == "1"


def test_custom_cover_sheet_title():
    wb = R.build_workbook({"sheet_title": "1. Cover", "fields": []}, [])
    assert wb.sheetnames == ["1. Cover"], wb.sheetnames


def test_na_note_when_empty():
    tabs = [{"title": "6. Pkg", "headers": ["P"], "rows": [], "na_note": "N/A here"}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["6. Pkg"]
    assert ws.cell(row=2, column=1).value == "N/A here"


def test_banner_rendered():
    tabs = [{"title": "5. Risk", "headers": ["R"], "rows": [["x"]], "banner": "Run deep dive"}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["5. Risk"]
    found = any(c.value == "Run deep dive" for row in ws.iter_rows() for c in row)
    assert found


def test_sections_tab():
    tabs = [{"title": "4. C&S", "sections": [
        {"heading": "A", "headers": ["x"], "rows": [["1"]]},
        {"heading": "B", "headers": ["y"], "rows": [["2"]]},
    ]}]
    wb = R.build_workbook({"fields": []}, tabs)
    ws = wb["4. C&S"]
    vals = [c.value for row in ws.iter_rows() for c in row if c.value]
    assert "A" in vals and "B" in vals and "1" in vals and "2" in vals, vals


def test_merge_rows_fills_and_appends_optional():
    core = [{"key": "risk_summary", "title": "5. Risk", "headers": ["R"]}]
    data = {"tabs": {"risk_summary": {"rows": [["r1"]]}},
            "optional_tabs": [{"title": "Design Risk", "headers": ["D"], "rows": [["d1"]]}]}
    tabs = R.merge_rows(core, data)
    assert tabs[0]["rows"] == [["r1"]]
    assert tabs[-1]["title"] == "Design Risk"


def test_merge_rows_section_keys():
    core = [{"key": "cs", "title": "4. C&S", "sections": [
        {"key": "ret", "heading": "A", "headers": ["x"]},
        {"key": "sub", "heading": "B", "headers": ["y"]},
    ]}]
    data = {"tabs": {"cs": {"sections": {"ret": {"rows": [["1"]]}, "sub": {"rows": [["2"]]}}}}}
    tabs = R.merge_rows(core, data)
    assert tabs[0]["sections"][0]["rows"] == [["1"]]
    assert tabs[0]["sections"][1]["rows"] == [["2"]]


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    print("ALL PASS" if not failed else f"{failed} FAILED")
    raise SystemExit(1 if failed else 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py`
Expected: FAIL — `ModuleNotFoundError: No module named '_xlsx_render'`

- [ ] **Step 3: Write the render engine**

Create `plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py`:

```python
"""Deterministic Ailtir workbook renderer.

The script owns structure (tab titles, order, headers) and styling; the model
supplies row content via a --data JSON blob. Scripts define a CORE_TABS
skeleton and pass model data through merge_rows() into build_workbook().

Bundled verbatim into each skill's scripts/ directory because Cowork does not
support reliable cross-skill Python imports (scripts run with cwd = session
root, and are invoked by absolute path).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
except ImportError:
    print("openpyxl not installed. Run: python3 -m pip install openpyxl", file=sys.stderr)
    raise

# Ailtir brand palette
NAVY = "0A1128"
PURPLE = "7C3AED"
WHITE = "FFFFFF"
NA_GREY = "9CA3AF"

HEADER_FONT = Font(bold=True, color=WHITE, size=11, name="Space Grotesk")
HEADER_FILL = PatternFill("solid", fgColor=NAVY)
SECTION_FONT = Font(bold=True, color=WHITE, size=11, name="Space Grotesk")
SECTION_FILL = PatternFill("solid", fgColor=PURPLE)
TITLE_FONT = Font(bold=True, color=WHITE, size=14, name="Space Grotesk")
BODY_FONT = Font(size=10, name="Inter")
LABEL_FONT = Font(bold=True, size=10, name="Inter")
NA_FONT = Font(italic=True, color=NA_GREY, size=10, name="Inter")
BANNER_FONT = Font(italic=True, color=PURPLE, size=10, name="Inter")
_THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="top", wrap_text=True)


def load_data(path):
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _style_header(ws, row, ncols, fill=HEADER_FILL, font=HEADER_FONT):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = font
        cell.fill = fill
        cell.alignment = CENTER
        cell.border = BORDER


def _autosize(ws, ncols, widths=None):
    for c in range(1, ncols + 1):
        w = widths[c - 1] if widths and c - 1 < len(widths) else 22
        ws.column_dimensions[get_column_letter(c)].width = w


def _render_cover(ws, cover):
    ws.title = cover.get("sheet_title", "1. Bid Summary")
    ws.merge_cells("A1:F1")
    ws["A1"] = cover.get("title", "AILTIR BID PLAN")
    ws["A1"].font = TITLE_FONT
    ws["A1"].fill = HEADER_FILL
    ws["A1"].alignment = CENTER
    row = 3
    for label, value in cover.get("fields", []):
        ws.cell(row=row, column=1, value=label).font = LABEL_FONT
        ws.cell(row=row, column=2, value=value).font = BODY_FONT
        row += 1
    _autosize(ws, 2, [26, 60])


def _render_grid(ws, start_row, headers, rows, na_note):
    r = start_row
    if headers:
        for i, h in enumerate(headers, 1):
            ws.cell(row=r, column=i, value=h)
        _style_header(ws, r, len(headers))
        r += 1
    if rows:
        for row_vals in rows:
            for i, val in enumerate(row_vals, 1):
                cell = ws.cell(row=r, column=i, value=val)
                cell.font = BODY_FONT
                cell.alignment = LEFT
                cell.border = BORDER
            r += 1
    elif na_note:
        ws.cell(row=r, column=1, value=na_note).font = NA_FONT
        r += 1
    _autosize(ws, max(len(headers) if headers else 1, 1))
    return r


def _render_tab(wb, spec):
    ws = wb.create_sheet(spec["title"])
    r = 1
    sections = spec.get("sections")
    if sections:
        for sec in sections:
            ncols = max(len(sec.get("headers", [])), 1)
            ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=ncols)
            ws.cell(row=r, column=1, value=sec["heading"])
            _style_header(ws, r, ncols, fill=SECTION_FILL, font=SECTION_FONT)
            r += 1
            r = _render_grid(ws, r, sec.get("headers", []), sec.get("rows", []), sec.get("na_note"))
            r += 1
    else:
        r = _render_grid(ws, r, spec.get("headers", []), spec.get("rows", []), spec.get("na_note"))
    if spec.get("banner"):
        r += 1
        ws.cell(row=r, column=1, value=spec["banner"]).font = BANNER_FONT
    return ws


def build_workbook(cover, tabs):
    wb = Workbook()
    _render_cover(wb.active, cover)
    for spec in tabs:
        _render_tab(wb, spec)
    return wb


def merge_rows(core_tabs, data):
    filled = []
    supplied = data.get("tabs", {})
    for spec in core_tabs:
        out = dict(spec)
        d = supplied.get(spec.get("key"), {})
        if "sections" in spec:
            secs = []
            sd_all = d.get("sections", {})
            for base in spec["sections"]:
                ms = dict(base)
                sd = sd_all.get(base.get("key"), {})
                ms["rows"] = sd.get("rows", [])
                if "na_note" in sd:
                    ms["na_note"] = sd["na_note"]
                secs.append(ms)
            out["sections"] = secs
        else:
            out["rows"] = d.get("rows", [])
            if "na_note" in d:
                out["na_note"] = d["na_note"]
        filled.append(out)
    for opt in data.get("optional_tabs", []):
        filled.append(opt)
    return filled
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py`
Expected: 7 `PASS` lines then `ALL PASS`, exit 0.

- [ ] **Step 5: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py plugin/skills/ailtir_bid-planner/scripts/test_render.py
git commit -m "feat: shared deterministic xlsx render engine for bid workbooks"
```

---

### Task 2: Rewrite the Tier-1 bid-planner workbook script

**Files:**
- Modify (full rewrite): `plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py`
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py`

**Interfaces:**
- Consumes: `_xlsx_render` (Task 1) — `load_data`, `merge_rows`, `build_workbook`.
- Produces: `go_no_go_recommendation(score: int, gate_fail: bool) -> str`; CLI `--output --project --client --return-date --route --data`; module-level `CORE_TABS: list`.

- [ ] **Step 1: Write the failing test**

Create `plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_bid_plan as B


def test_gate_fail_forces_nogo():
    assert B.go_no_go_recommendation(95, True).startswith("NO-GO")


def test_thresholds():
    assert B.go_no_go_recommendation(80, False) == "Strong GO"
    assert B.go_no_go_recommendation(79, False) == "Marginal GO"
    assert B.go_no_go_recommendation(60, False) == "Marginal GO"
    assert B.go_no_go_recommendation(59, False) == "NO-GO"


def test_core_tabs_are_the_eight_after_cover():
    # Tab 1 (Bid Summary) is the cover, built separately, so CORE_TABS holds 8.
    titles = [t["title"] for t in B.CORE_TABS]
    assert titles == [
        "2. Document Register", "3. Go / No-Go", "4. Compliance & Submission",
        "5. Risk Summary", "6. Package Outline", "7. Bid Programme",
        "8. BID TEAM RACI", "9. Clarifications Log",
    ], titles


def test_summary_tabs_have_banners():
    by_key = {t["key"]: t for t in B.CORE_TABS}
    for key in ("compliance_submission", "risk_summary", "package_outline"):
        assert by_key[key].get("banner"), key


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS {name}")
            except AssertionError as e:
                failed += 1; print(f"FAIL {name}: {e}")
    print("ALL PASS" if not failed else f"{failed} FAILED")
    raise SystemExit(1 if failed else 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd plugin/skills/ailtir_bid-planner/scripts && python3 test_bid_plan.py`
Expected: FAIL — old `create_bid_plan.py` has no `go_no_go_recommendation` / `CORE_TABS` (AttributeError).

- [ ] **Step 3: Rewrite the script**

Replace the entire contents of `plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py` with:

```python
"""Tier-1 bid-planner workbook: 9 deterministic core tabs (+ optional tabs).

Structure, headers, and styling are owned here; the model supplies row content
via --data JSON. See ailtir_bid-planner/SKILL.md for the data contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402


def go_no_go_recommendation(score, gate_fail):
    if gate_fail:
        return "NO-GO (mandatory gate failed)"
    if score >= 80:
        return "Strong GO"
    if score >= 60:
        return "Marginal GO"
    return "NO-GO"


BANNER_COMPLIANCE = ("Summarised view. Run /ailtir_compliance-matrix for the full "
                     "returnables tracker with templates, owners & deadlines.")
BANNER_RISK = ("Summarised view. Run /ailtir_contract-risk for the full "
               "clause-by-clause register, contract data & action tracker.")
BANNER_PACKAGE = ("Summarised view. Run /ailtir_package-breakdown in the "
                  "enquire-and-procure phase for the full package register.")

CORE_TABS = [
    {"key": "document_register", "title": "2. Document Register",
     "headers": ["Filename", "Title", "Type", "Rev", "Date", "Notes"]},
    {"key": "go_no_go", "title": "3. Go / No-Go",
     "headers": ["Criteria", "Max Score", "Actual Score", "Notes"]},
    {"key": "compliance_submission", "title": "4. Compliance & Submission",
     "banner": BANNER_COMPLIANCE, "sections": [
         {"key": "returnables", "heading": "A. Returnables & Award Criteria",
          "headers": ["Ref", "Requirement / Criterion", "Weighting", "Template", "Owner"]},
         {"key": "submission_rules", "heading": "B. Submission Rules",
          "headers": ["Item", "Requirement"]},
     ]},
    {"key": "risk_summary", "title": "5. Risk Summary", "banner": BANNER_RISK,
     "headers": ["Ref", "Risk", "Rating", "Impact", "Mitigation"]},
    {"key": "package_outline", "title": "6. Package Outline", "banner": BANNER_PACKAGE,
     "headers": ["Package", "Scope", "Est. Value", "Target Date"]},
    {"key": "bid_programme", "title": "7. Bid Programme",
     "headers": ["Milestone", "Date", "Owner", "Notes"]},
    {"key": "team_raci", "title": "8. BID TEAM RACI",
     "headers": ["Activity", "Responsible", "Accountable", "Consulted", "Informed"]},
    {"key": "clarifications", "title": "9. Clarifications Log",
     "headers": ["Ref", "Query", "Raised", "Status", "Response"]},
]


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir Tier-1 bid plan workbook")
    p.add_argument("--output", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--client", default="TBC")
    p.add_argument("--return-date", default="TBC")
    p.add_argument("--route", default="TBC")
    p.add_argument("--data", default=None, help="Path to model-supplied JSON row content")
    args = p.parse_args()

    data = R.load_data(args.data)
    gng = data.get("tabs", {}).get("go_no_go", {})
    score = int(gng.get("score", 0))
    gate_fail = bool(gng.get("gate_fail", False))
    recommendation = go_no_go_recommendation(score, gate_fail)

    cover = {
        "title": f"AILTIR BID PLAN — {args.project.upper()}",
        "fields": [
            ("Project Name:", args.project),
            ("Client:", args.client),
            ("Tender Return:", args.return_date),
            ("Procurement Route:", args.route),
            ("Go/No-Go Score:", f"{score}/100" if args.data else "TBC"),
            ("Recommendation:", recommendation if args.data else "TBC"),
        ],
    }

    tabs = R.merge_rows(CORE_TABS, data)
    wb = R.build_workbook(cover, tabs)
    wb.save(args.output)
    print(f"Created {args.output} ({recommendation})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run unit test to verify it passes**

Run: `cd plugin/skills/ailtir_bid-planner/scripts && python3 test_bid_plan.py`
Expected: 4 `PASS` lines then `ALL PASS`, exit 0.

- [ ] **Step 5: End-to-end smoke test with sample data**

Run:
```bash
cd plugin/skills/ailtir_bid-planner/scripts
cat > /tmp/bp.json <<'JSON'
{"tabs":{"go_no_go":{"score":72,"gate_fail":false,"rows":[["Client & Relationship","30","20","Known client"]]},
"risk_summary":{"rows":[["CR-01","20-day time bar","RED","Loss of EOT","Notice register"]]},
"compliance_submission":{"sections":{"returnables":{"rows":[["Vol B","Form of Tender","Pass/Fail","YES","Director"]]},
"submission_rules":{"rows":[["Deadline","28/02 16:00 eTenders"]]}}},
"package_outline":{"rows":[],"na_note":"N/A at plan stage — see enquire-and-procure phase."}},
"optional_tabs":[{"title":"Design Risk","headers":["Item","Note"],"rows":[["PI cover","Fitness-for-purpose flagged"]]}]}
JSON
python3 create_bid_plan.py --output /tmp/BidPlan.xlsx --project "Athenry NRR" --client "Galway CC" --return-date 2026-02-28 --route "CWMF Open" --data /tmp/bp.json
python3 - <<'PY'
import openpyxl
wb = openpyxl.load_workbook("/tmp/BidPlan.xlsx")
print(wb.sheetnames)
assert wb.sheetnames[0] == "1. Bid Summary"
assert "Design Risk" in wb.sheetnames  # optional tab appended
# "/" is illegal in Excel sheet names; the engine sanitises "3. Go / No-Go" -> "3. Go - No-Go"
assert wb.sheetnames.count("3. Go - No-Go") == 1  # no duplicates
PY
```
Expected: prints 10 sheet names (9 core + 1 optional), no `AssertionError`, `Created /tmp/BidPlan.xlsx (Marginal GO)`.

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/scripts/create_bid_plan.py plugin/skills/ailtir_bid-planner/scripts/test_bid_plan.py
git commit -m "feat: rewrite bid-planner workbook as deterministic 9-tab skeleton"
```

---

### Task 3: Deep-dive compliance matrix script

**Files:**
- Create: `plugin/skills/ailtir_compliance-matrix/scripts/_xlsx_render.py` (verbatim copy from Task 1)
- Create: `plugin/skills/ailtir_compliance-matrix/scripts/create_compliance_matrix.py`
- Test: `plugin/skills/ailtir_compliance-matrix/scripts/test_compliance_matrix.py`

**Interfaces:**
- Consumes: bundled `_xlsx_render`.
- Produces: CLI `--output --data`; module-level `CORE_TABS` (4 tabs: Award Criterion, Mandatory Returnables, Submission Rules, Template & Doc Gap Check).

- [ ] **Step 1: Bundle the render engine**

```bash
cp plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py plugin/skills/ailtir_compliance-matrix/scripts/_xlsx_render.py
```
(Create the `scripts/` dir first if absent: `mkdir -p plugin/skills/ailtir_compliance-matrix/scripts`.)

- [ ] **Step 2: Write the failing test**

Create `plugin/skills/ailtir_compliance-matrix/scripts/test_compliance_matrix.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_compliance_matrix as C


def test_core_tabs():
    assert [t["title"] for t in C.CORE_TABS] == [
        "2. Award Criterion", "3. Mandatory Returnables",
        "4. Submission Rules", "5. Template & Doc Gap Check",
    ]


def test_build_renders_cover_first():
    import _xlsx_render as R
    wb = R.build_workbook(C.cover({"project": "X"}), R.merge_rows(C.CORE_TABS, {}))
    assert wb.sheetnames[0] == "1. Cover"
    assert "3. Mandatory Returnables" in wb.sheetnames


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS {name}")
            except AssertionError as e:
                failed += 1; print(f"FAIL {name}: {e}")
    print("ALL PASS" if not failed else f"{failed} FAILED")
    raise SystemExit(1 if failed else 0)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd plugin/skills/ailtir_compliance-matrix/scripts && python3 test_compliance_matrix.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'create_compliance_matrix'`.

- [ ] **Step 4: Write the script**

Create `plugin/skills/ailtir_compliance-matrix/scripts/create_compliance_matrix.py`:

```python
"""Tier-2 deep-dive compliance matrix: 4 deterministic tabs + cover.

Structure/headers/styling owned here; model supplies rows via --data JSON.
Writes its OWN workbook — never the bid-planner file. See SKILL.md for the
data contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402


CORE_TABS = [
    {"key": "award_criterion", "title": "2. Award Criterion",
     "headers": ["Ref", "Criterion", "Weight", "Notes", "Status"]},
    {"key": "returnables", "title": "3. Mandatory Returnables",
     "headers": ["No.", "Ref", "Document / Item", "Category",
                 "Template Provided", "Status", "Owner", "Notes"]},
    {"key": "submission_rules", "title": "4. Submission Rules",
     "headers": ["Item", "Requirement"]},
    {"key": "gap_check", "title": "5. Template & Doc Gap Check",
     "headers": ["Ref", "Document", "Required?", "Template in Pack?", "Action Required"]},
]


def cover(meta):
    fields = [(f"{k}:", v) for k, v in meta.items()]
    return {"sheet_title": "1. Cover", "title": "COMPLIANCE MATRIX", "fields": fields}


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir compliance matrix workbook")
    p.add_argument("--output", required=True)
    p.add_argument("--data", default=None, help="Path to model-supplied JSON")
    args = p.parse_args()
    data = R.load_data(args.data)
    wb = R.build_workbook(cover(data.get("cover", {})), R.merge_rows(CORE_TABS, data))
    wb.save(args.output)
    print(f"Created {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd plugin/skills/ailtir_compliance-matrix/scripts && python3 test_compliance_matrix.py`
Expected: 2 `PASS` lines then `ALL PASS`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/ailtir_compliance-matrix/scripts/
git commit -m "feat: deterministic deep-dive compliance matrix workbook script"
```

---

### Task 4: Deep-dive contract risk register script

**Files:**
- Create: `plugin/skills/ailtir_contract-risk/scripts/_xlsx_render.py` (verbatim copy from Task 1)
- Create: `plugin/skills/ailtir_contract-risk/scripts/create_risk_register.py`
- Test: `plugin/skills/ailtir_contract-risk/scripts/test_risk_register.py`

**Interfaces:**
- Consumes: bundled `_xlsx_render`.
- Produces: CLI `--output --data`; module-level `CORE_TABS` (3 tabs: Risk Register, Schedule Part 1 - Data, Action Tracker); `cover(meta) -> dict`.

- [ ] **Step 1: Bundle the render engine**

```bash
mkdir -p plugin/skills/ailtir_contract-risk/scripts
cp plugin/skills/ailtir_bid-planner/scripts/_xlsx_render.py plugin/skills/ailtir_contract-risk/scripts/_xlsx_render.py
```

- [ ] **Step 2: Write the failing test**

Create `plugin/skills/ailtir_contract-risk/scripts/test_risk_register.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_risk_register as K


def test_core_tabs():
    assert [t["title"] for t in K.CORE_TABS] == [
        "2. Risk Register", "3. Schedule Part 1 - Data", "4. Action Tracker",
    ]


def test_build_renders_cover_first():
    import _xlsx_render as R
    wb = R.build_workbook(K.cover({"contract": "PW-CF5"}), R.merge_rows(K.CORE_TABS, {}))
    assert wb.sheetnames[0] == "1. Cover"
    assert "2. Risk Register" in wb.sheetnames


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn(); print(f"PASS {name}")
            except AssertionError as e:
                failed += 1; print(f"FAIL {name}: {e}")
    print("ALL PASS" if not failed else f"{failed} FAILED")
    raise SystemExit(1 if failed else 0)
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd plugin/skills/ailtir_contract-risk/scripts && python3 test_risk_register.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'create_risk_register'`.

- [ ] **Step 4: Write the script**

Create `plugin/skills/ailtir_contract-risk/scripts/create_risk_register.py`:

```python
"""Tier-2 deep-dive contract risk register: 3 deterministic tabs + cover.

Structure/headers/styling owned here; model supplies rows via --data JSON.
Writes its OWN workbook. See SKILL.md for the data contract.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _xlsx_render as R  # noqa: E402


CORE_TABS = [
    {"key": "risk_register", "title": "2. Risk Register",
     "headers": ["Ref", "Risk Description", "Clause / Schedule Ref", "Rating",
                 "Commercial Impact", "Mitigation / Action", "Owner"]},
    {"key": "contract_data", "title": "3. Schedule Part 1 - Data",
     "headers": ["Schedule Part", "Ref", "Data Item", "Value in Contract",
                 "Playbook Standard / Note"]},
    {"key": "action_tracker", "title": "4. Action Tracker",
     "headers": ["#", "Risk Ref", "Action", "Who", "Due By", "Status", "Notes"]},
]


def cover(meta):
    fields = [(f"{k}:", v) for k, v in meta.items()]
    return {"sheet_title": "1. Cover", "title": "CONTRACT RISK REGISTER", "fields": fields}


def main():
    p = argparse.ArgumentParser(description="Generate the Ailtir contract risk register workbook")
    p.add_argument("--output", required=True)
    p.add_argument("--data", default=None, help="Path to model-supplied JSON")
    args = p.parse_args()
    data = R.load_data(args.data)
    wb = R.build_workbook(cover(data.get("cover", {})), R.merge_rows(CORE_TABS, data))
    wb.save(args.output)
    print(f"Created {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd plugin/skills/ailtir_contract-risk/scripts && python3 test_risk_register.py`
Expected: 2 `PASS` lines then `ALL PASS`, exit 0.

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/ailtir_contract-risk/scripts/
git commit -m "feat: deterministic deep-dive contract risk register workbook script"
```

---

### Task 5: Bid kick-off deck (.pptx)

**Files:**
- Create: `plugin/skills/ailtir_bid-planner/scripts/create_bid_deck.js`
- Create: `plugin/skills/ailtir_bid-planner/scripts/package.json`
- Test: `plugin/skills/ailtir_bid-planner/scripts/test_deck.sh`

**Interfaces:**
- Produces: CLI `node create_bid_deck.js --config <json> --output <pptx>`. Config keys: `project, client, value, sector, contractForm, route, returnDate, overview[], packStatus{received,missing,gaps}, missingDocs[], requirements[], priceOnly(bool), programme[], packages[], risks[], actions[]`.

- [ ] **Step 1: Declare the dependency**

Create `plugin/skills/ailtir_bid-planner/scripts/package.json`:

```json
{
  "name": "ailtir-bid-deck",
  "version": "1.0.0",
  "private": true,
  "description": "Ailtir bid kick-off deck generator",
  "dependencies": {
    "pptxgenjs": "^3.12.0"
  }
}
```

- [ ] **Step 2: Install pptxgenjs**

Run: `cd plugin/skills/ailtir_bid-planner/scripts && npm install`
Expected: `node_modules/pptxgenjs` created, no errors.

- [ ] **Step 3: Write the deck generator**

Create `plugin/skills/ailtir_bid-planner/scripts/create_bid_deck.js`:

```javascript
// Ailtir bid kick-off deck. Internal working document, not a client pitch.
// Reads a JSON config (Claude builds it from the workbook data) and emits .pptx.
const pptxgen = require("pptxgenjs");
const fs = require("fs");

const NAVY = "0A1128";
const PURPLE = "7C3AED";
const WHITE = "FFFFFF";
const AMBER = "F59E0B";
const RED = "C0392B";
const GREEN = "2E7D32";

function arg(flag) {
  const i = process.argv.indexOf(flag);
  return i >= 0 ? process.argv[i + 1] : null;
}

function main() {
  const configPath = arg("--config");
  const output = arg("--output") || "Bid_KickOff.pptx";
  if (!configPath) {
    console.error("Usage: node create_bid_deck.js --config <json> --output <pptx>");
    process.exit(2);
  }
  const c = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const p = new pptxgen();
  p.defineLayout({ name: "A4", width: 11.7, height: 8.27 });
  p.layout = "A4";

  const H = (s, o = {}) => ({ text: s, options: { fontFace: "Space Grotesk", ...o } });
  const B = (s, o = {}) => ({ text: s, options: { fontFace: "Inter", ...o } });

  // Slide 1 — Title
  let s = p.addSlide();
  s.background = { color: NAVY };
  s.addText(c.project || "Bid Kick-Off", { x: 0.5, y: 2.6, w: 10.7, h: 1, fontFace: "Space Grotesk", fontSize: 40, bold: true, color: WHITE });
  s.addText(
    [B(`${c.client || ""}   `, { color: WHITE }), B(`${c.value || ""}  ${c.sector || ""}`, { color: "CFD3DC" })],
    { x: 0.5, y: 3.7, w: 10.7, h: 0.5, fontSize: 16 }
  );
  s.addText(`Tender return: ${c.returnDate || "TBC"}`, { x: 6.7, y: 7.2, w: 4.5, h: 0.6, align: "right", fontFace: "Inter", fontSize: 16, bold: true, color: WHITE, fill: { color: RED } });

  // Slide 2 — Project overview
  s = p.addSlide();
  s.addText("Project Overview", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  s.addText((c.overview || []).map((t) => B(t, { color: "222222", bullet: true })), { x: 0.5, y: 1.2, w: 10.7, h: 6, fontSize: 13 });

  // Slide 3 — Tender pack status
  s = p.addSlide();
  s.addText("Tender Pack Status", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  const ps = c.packStatus || {};
  const stat = (label, val, color, x) =>
    s.addText([H(String(val), { fontSize: 40, bold: true, color: WHITE }), B(`\n${label}`, { fontSize: 12, color: WHITE })], { x, y: 1.2, w: 3.3, h: 1.6, align: "center", fill: { color } });
  stat("Received", ps.received ?? 0, GREEN, 0.5);
  stat("Missing", ps.missing ?? 0, RED, 4.1);
  stat("Gaps", ps.gaps ?? 0, AMBER, 7.7);
  if ((c.missingDocs || []).length) {
    s.addTable([["Missing Document", "Impact"], ...c.missingDocs.map((d) => [d.doc || d, d.impact || ""])], { x: 0.5, y: 3.1, w: 10.7, fontFace: "Inter", fontSize: 11, border: { pt: 0.5, color: "D9D9D9" }, fill: { color: "F5F7FA" } });
  }

  // Slide 4 — Submission requirements (skip quality for price-only)
  s = p.addSlide();
  s.addText("Submission Requirements", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  if (c.priceOnly) {
    s.addText("Price-dominant tender — no formal quality submission. Returnable documents only.", { x: 0.5, y: 1.2, w: 10.7, h: 0.6, fontFace: "Inter", fontSize: 13, italic: true, color: "555555" });
  }
  if ((c.requirements || []).length) {
    s.addTable([["Ref", "Requirement", "Weight", "Owner"], ...c.requirements.map((r) => [r.ref || "", r.text || "", r.weight || "", r.owner || ""])], { x: 0.5, y: 1.9, w: 10.7, fontFace: "Inter", fontSize: 11, border: { pt: 0.5, color: "D9D9D9" } });
  }

  // Slide 5 — Programme
  s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("Bid Programme", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: WHITE });
  s.addText((c.programme || []).map((m) => B(`${m.date || ""}  —  ${m.label || m}`, { color: WHITE, bullet: true })), { x: 0.5, y: 1.2, w: 10.7, h: 6, fontSize: 13 });

  // Slide 6 — Work packages
  s = p.addSlide();
  s.addText("Work Packages", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  s.addText((c.packages || []).map((pk) => B(String(pk.name || pk), { color: "222222", bullet: true })), { x: 0.5, y: 1.2, w: 10.7, h: 6, fontSize: 13 });

  // Slide 7 — Top risks
  s = p.addSlide();
  s.background = { color: NAVY };
  s.addText("Top Risks", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: WHITE });
  (c.risks || []).slice(0, 7).forEach((r, i) => {
    s.addText([H(`${i + 1}. `, { color: RED, bold: true }), H(r.title || r, { color: WHITE, bold: true }), B(`   ${r.owner || ""}`, { color: AMBER })], { x: 0.5, y: 1.2 + i * 0.75, w: 10.7, h: 0.6, fontSize: 13 });
  });

  // Slide 8 — Immediate actions
  s = p.addSlide();
  s.addText("Immediate Actions", { x: 0.5, y: 0.3, w: 10.7, h: 0.6, fontFace: "Space Grotesk", fontSize: 24, bold: true, color: NAVY });
  if ((c.actions || []).length) {
    s.addTable([["When", "What", "Who"], ...c.actions.map((a) => [a.when || "", a.what || a, a.who || ""])], { x: 0.5, y: 1.2, w: 10.7, fontFace: "Inter", fontSize: 12, border: { pt: 0.5, color: "D9D9D9" } });
  }

  p.writeFile({ fileName: output }).then(() => console.log(`Created ${output}`));
}

main();
```

- [ ] **Step 4: Write the smoke test**

Create `plugin/skills/ailtir_bid-planner/scripts/test_deck.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
cat > /tmp/deck.json <<'JSON'
{"project":"Athenry NRR","client":"Galway CC","value":"€2.0M","sector":"Civils","returnDate":"2026-02-28",
"overview":["Road widening","Bridge works"],"packStatus":{"received":12,"missing":2,"gaps":3},
"missingDocs":[{"doc":"Geotech report","impact":"Pricing blind"}],"priceOnly":true,
"requirements":[{"ref":"WP-1","text":"PSCS statement","owner":"Director"}],
"programme":[{"date":"2026-02-07","label":"Query deadline"}],
"packages":[{"name":"Groundworks"},{"name":"Concrete"}],
"risks":[{"title":"20-day time bar","owner":"Commercial"}],
"actions":[{"when":"TODAY","what":"Issue subbie enquiries","who":"Estimator"}]}
JSON
node create_bid_deck.js --config /tmp/deck.json --output /tmp/deck.pptx
test -s /tmp/deck.pptx
echo "DECK OK"
```

- [ ] **Step 5: Run the smoke test**

Run: `bash plugin/skills/ailtir_bid-planner/scripts/test_deck.sh`
Expected: `Created /tmp/deck.pptx` then `DECK OK`, exit 0.

- [ ] **Step 6: Ignore node_modules and commit**

```bash
echo "plugin/skills/ailtir_bid-planner/scripts/node_modules/" >> plugin/.gitignore
git add plugin/skills/ailtir_bid-planner/scripts/create_bid_deck.js plugin/skills/ailtir_bid-planner/scripts/package.json plugin/skills/ailtir_bid-planner/scripts/test_deck.sh plugin/.gitignore
git add plugin/skills/ailtir_bid-planner/scripts/package-lock.json 2>/dev/null || true
git commit -m "feat: Ailtir-branded bid kick-off deck generator"
```

---

### Task 6: Rewrite bid-planner SKILL.md

**Files:**
- Modify: `plugin/skills/ailtir_bid-planner/SKILL.md`

**Interfaces:**
- Consumes: `create_bid_plan.py --data` (Task 2), `create_bid_deck.js` (Task 5), `references/{profile_key}/go-no-go-criteria.md` (existing).

- [ ] **Step 1: Replace Step 2 (the chained analysis) to emit a data JSON**

In `plugin/skills/ailtir_bid-planner/SKILL.md`, replace the whole `## Step 2 — The Chained Analysis (Work Silently)` section (from that heading through the end of its subsection D, i.e. up to but not including `## Step 3 — Generate Outputs`) with:

```markdown
## Step 2 — Analyse the Pack (Work Silently, Build One Data Object)

This is the shallow-but-complete first pass. Do all of the following analysis,
then assemble a single JSON object (the `--data` payload for Step 3). Do NOT
call `openpyxl` yourself and do NOT invoke sibling skills — the planner does the
summary depth here; the deep dives come later.

### A. Document register + gaps
Catalogue every document (filename, title, type, rev, date, notes). Cross-
reference BOQ references against the document list; list any missing files.

### B. Go/No-Go — full scoring (inlined)
Read `references/{profile_key}/go-no-go-criteria.md` from THIS skill's directory.
Check every mandatory gate and score all four weighted dimensions against the
bands in that file. This is done in full here — the planner owns go/no-go.

### C. Compliance & submission (summary depth — one row per item)
Extract every returnable and evaluation criterion (with exact weightings) and the
submission rules (method, format, naming, deadlines). One row each — this is the
glance view, not the full tracker.

### D. Risk summary (summary depth — top 5)
Identify the contract form and flag the top 5 commercial risks against the
profile playbook. One row each.

### E. Package outline (summary depth)
List the likely trade packages at a high level. If packages cannot yet be
determined, leave empty with an N/A note — the full register is a later phase.

### Assemble the data payload
Write the results to a JSON file (e.g. `/tmp/bid_plan_data.json`) with this shape.
Every key is optional; omit a section and its tab renders with an N/A note.

```json
{
  "tabs": {
    "document_register": {"rows": [["file.pdf","Title","Spec","P1","2026-01-01","note"]]},
    "go_no_go": {"score": 72, "gate_fail": false,
                 "rows": [["Client & Relationship","30","20","Known client"]]},
    "compliance_submission": {"sections": {
        "returnables": {"rows": [["Vol B","Form of Tender","Pass/Fail","YES","Director"]]},
        "submission_rules": {"rows": [["Deadline","28/02 16:00 via eTenders"]]}}},
    "risk_summary": {"rows": [["CR-01","20-day time bar","RED","Loss of EOT","Notice register"]]},
    "package_outline": {"rows": [], "na_note": "N/A at plan stage — see enquire-and-procure phase."},
    "bid_programme": {"rows": [["Query deadline","2026-02-07","Bid Mgr",""]]},
    "team_raci": {"rows": [["Pricing","QS","Director","Estimator","PM"]]},
    "clarifications": {"rows": [["CL-01","Portal access?","2026-01-10","Open",""]]}
  },
  "optional_tabs": [
    {"title": "Design Risk", "headers": ["Item","Note"], "rows": [["PI cover","Fitness-for-purpose flagged"]]}
  ]
}
```

**Adaptation rules (fixed core + judgement at the edges):**
- The 9 core tabs are always built. If a core section does not apply to this
  tender, supply `"rows": []` and an `"na_note"` explaining why (e.g. price-only
  → no quality returnables). Never omit a core tab to "clean up".
- Pre-populate `team_raci` from the team members in `Context/profile.json` /
  `Context/company.md` where present; otherwise use role names.
- Add an entry to `optional_tabs` ONLY when the tender genuinely needs a tab the
  core set lacks — e.g. `Design Risk` on D&B, `Framework Call-Off` on a call-off,
  `Lots` on a multi-lot public tender. Give it `title`, `headers`, `rows`.
```

- [ ] **Step 2: Replace Step 3 Part A to call the script with `--data`**

Replace the `### Part A — The Bid Plan Workbook` block (from that heading to `### Part B — Folder Structure`) with:

```markdown
### Part A — The Bid Plan Workbook
Run the bundled `scripts/create_bid_plan.py` helper in this skill's directory with
`python3`, passing the data payload from Step 2. Do NOT populate tabs with
`openpyxl` yourself — the script owns all structure and styling:

- `--output "Bid_Plan_[Project].xlsx"`
- `--project "[Name]"`
- `--client "[Client]"`
- `--return-date "YYYY-MM-DD"`
- `--route "[Route]"`
- `--data "/tmp/bid_plan_data.json"`

The workbook has 9 fixed core tabs (Bid Summary, Document Register, Go/No-Go,
Compliance & Submission, Risk Summary, Package Outline, Bid Programme, BID TEAM
RACI, Clarifications Log) plus any optional tabs you declared. The Go/No-Go score
and recommendation are computed by the script from your payload.

### Part A2 — The Kick-Off Deck (shareable)
Build a JSON config from the same analysis and run the bundled
`scripts/create_bid_deck.js` helper with `node` (run `npm install` in the
`scripts/` dir first if `node_modules` is absent):

`node scripts/create_bid_deck.js --config /tmp/bid_deck.json --output "Bid_KickOff_[Project].pptx"`

This is an internal working deck (Title → Overview → Pack Status → Submission
Requirements → Programme → Packages → Top Risks → Immediate Actions). Set
`"priceOnly": true` in the config to skip quality sections.
```

- [ ] **Step 3: Add the handoff + state note to Step 4**

In `## Step 4 — Present Findings`, replace the final line
`Ask: "Would you like me to move to Phase 2 and break this down into trade packages (`/ailtir_package-breakdown`)?"`
with:

```markdown
Then present the handoff explicitly — the workbook is a summarised first pass:

> The bid plan and kick-off deck are ready. Go/No-Go is done in full. The
> Compliance, Risk, and Package tabs are **summarised** — run the deep dives when
> you commit to bidding:
> - `/ailtir_contract-risk` — full clause-by-clause register, contract data & actions
> - `/ailtir_compliance-matrix` — full returnables tracker with templates, owners & deadlines
>
> See `PROCESS.md` for how the whole bid lifecycle fits together.

## On Completion — Update Bid State

When this workflow finishes for a specific bid, record what was done so the
conductor and dashboard reflect it. Run the sibling `ailtir_conductor` skill's
`scripts/update_frontmatter.py` with `python3`, once per analysis:

```
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_go-no-go --result proceed
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_compliance-matrix --result summarised
python3 <ailtir_conductor>/scripts/update_frontmatter.py --bid-path Bids/<BID> \
    --complete ailtir_contract-risk --result summarised
```

Go/No-Go is `proceed` (done in full). Compliance and contract-risk are
`summarised` — the conductor will recommend them as deep dives, not repeats.
```

- [ ] **Step 4: Bump the hardcoded version**

In the `## Usage Reporting` block, change `plugin_version`: `2.15.5` to `2.16.0`.

- [ ] **Step 5: Verify the edits**

Run: `grep -n "create_bid_plan.py\|create_bid_deck.js\|summarised\|2.16.0\|optional_tabs" plugin/skills/ailtir_bid-planner/SKILL.md`
Expected: matches for the script calls, the two `summarised` completes, the version, and the optional_tabs guidance. Confirm the old "9 tabs via secondary Python script or direct manipulation" text is gone: `grep -c "direct manipulation" plugin/skills/ailtir_bid-planner/SKILL.md` → `0`.

- [ ] **Step 6: Commit**

```bash
git add plugin/skills/ailtir_bid-planner/SKILL.md
git commit -m "docs: bid-planner emits data JSON, inlines go/no-go, adds deck + handoff"
```

---

### Task 7: Update deep-dive SKILL.md files

**Files:**
- Modify: `plugin/skills/ailtir_compliance-matrix/SKILL.md`
- Modify: `plugin/skills/ailtir_contract-risk/SKILL.md`

**Interfaces:**
- Consumes: `create_compliance_matrix.py` (Task 3), `create_risk_register.py` (Task 4).

- [ ] **Step 1: compliance-matrix — replace Step 3 (Present)**

In `plugin/skills/ailtir_compliance-matrix/SKILL.md`, replace the `## Step 3 — Present` section (through its `[HUMAN INPUT REQUIRED]` line) with:

```markdown
## Step 3 — Generate the Workbook
This is the deep-dive pass. Assemble your extracted analysis into a JSON payload
and run the bundled `scripts/create_compliance_matrix.py` with `python3` — the
script owns all tab structure and styling; you supply the rows:

`python3 scripts/create_compliance_matrix.py --output "Compliance_Matrix_[Bid].xlsx" --data /tmp/compliance_data.json`

Payload shape (each `rows` is a list of row-arrays matching the tab's columns):

```json
{
  "cover": {"Project": "X", "ITT Ref": "ITT-W2", "Submission": "28/02 16:00"},
  "tabs": {
    "award_criterion": {"rows": [["AC-1","Lowest cost","100%","Price only","Price only"]]},
    "returnables": {"rows": [["1","Vol B","Form of Tender","Contract Doc","YES","To Do","Director","Complete all blanks"]]},
    "submission_rules": {"rows": [["SUBMISSION METHOD","eTenders only"]]},
    "gap_check": {"rows": [["Doc 7","QW Part 1","RETURN","YES","Complete fully"]]}
  }
}
```

This writes its OWN workbook — never the bid-planner file. If a section does not
apply, pass `"rows": []` with a `"na_note"`.

- [HUMAN INPUT REQUIRED] If the submission method or deadline is not stated in the ITT, ask the user before finalising the matrix.
```

- [ ] **Step 2: compliance-matrix — upgrade the completion result to `proceed`**

In the same file's `## On Completion — Update Bid State` section, the `--complete <this skill's folder name>` example already uses `--result proceed`. Add this sentence immediately before the code block:

```markdown
This deep dive **upgrades** the bid-planner's `summarised` entry to a full
`proceed`. Use `--result proceed`.
```

- [ ] **Step 3: compliance-matrix — bump version**

Change `plugin_version`: `2.15.5` → `2.16.0` in the Usage Reporting block.

- [ ] **Step 4: contract-risk — replace Step 4 (Present)**

In `plugin/skills/ailtir_contract-risk/SKILL.md`, replace the `## Step 4 — Present` section (through its `[HUMAN INPUT REQUIRED]` line) with:

```markdown
## Step 4 — Generate the Workbook
This is the deep-dive pass. Assemble your clause-by-clause analysis into a JSON
payload and run the bundled `scripts/create_risk_register.py` with `python3` —
the script owns all tab structure and styling; you supply the rows:

`python3 scripts/create_risk_register.py --output "Contract_Risk_Register_[Bid].xlsx" --data /tmp/risk_data.json`

Payload shape:

```json
{
  "cover": {"Project": "X", "Contract Form": "PW-CF5 v2.7", "Playbook Base": "ireland-gc"},
  "tabs": {
    "risk_register": {"rows": [["CR-01","20-Working-Day Time Bar","Sub-clause 10.3","RED","Loss of EOT","Notice register","Commercial Manager"]]},
    "contract_data": {"rows": [["Part 1A","ER","Employer's Representative","Named","Standard"]]},
    "action_tracker": {"rows": [["A-01","CR-01","Establish CE notice register","Commercial","START DATE","OPEN",""]]}
  }
}
```

This writes its OWN workbook — never the bid-planner file.

- [HUMAN INPUT REQUIRED] If the contract form cannot be determined from the documents, ask the user before proceeding.
```

- [ ] **Step 5: contract-risk — add the `proceed` upgrade note + bump version**

Before the code block in `## On Completion — Update Bid State`, add:

```markdown
This deep dive **upgrades** the bid-planner's `summarised` entry to a full
`proceed`. Use `--result proceed`.
```

Change `plugin_version`: `2.15.5` → `2.16.0` in the Usage Reporting block.

- [ ] **Step 6: Verify and commit**

Run: `grep -c "create_compliance_matrix.py" plugin/skills/ailtir_compliance-matrix/SKILL.md; grep -c "create_risk_register.py" plugin/skills/ailtir_contract-risk/SKILL.md`
Expected: each prints `1` or more.

```bash
git add plugin/skills/ailtir_compliance-matrix/SKILL.md plugin/skills/ailtir_contract-risk/SKILL.md
git commit -m "docs: deep-dive skills generate own deterministic workbooks, upgrade summarised->proceed"
```

---

### Task 8: Conductor + phase-map changes

**Files:**
- Modify: `plugin/skills/ailtir_conductor/references/phase-map.md`
- Modify: `plugin/skills/ailtir_conductor/SKILL.md`

**Interfaces:**
- Consumes: the `summarised` result value written by bid-planner (Task 6).

- [ ] **Step 1: Rewrite the pre-bid phase in the phase-map**

In `plugin/skills/ailtir_conductor/references/phase-map.md`, replace the entire `## Phase: `pre-bid`` section (from that heading up to the `---` before `## Phase: `estimating``) with:

```markdown
## Phase: `pre-bid`

Tender pack in hand, decision to bid taken. The canonical entry point is the
Tier-1 planner, which produces a summarised first pass; the deep dives follow.

1. `ailtir_bid-planner` — the Tier-1 first pass. Produces one 9-tab workbook +
   kick-off deck. Does Go/No-Go **in full** (recorded `result: proceed`) and
   **summarises** compliance and contract-risk (recorded `result: summarised`).
2. `ailtir_contract-risk` — deep dive: full clause-by-clause register, contract
   data, action tracker. Upgrades the `summarised` entry to `proceed`.
3. `ailtir_compliance-matrix` — deep dive: full returnables tracker with
   templates, owners, deadlines. Upgrades the `summarised` entry to `proceed`.
4. `ailtir_pqq-manager` — if a PQQ / SQ / Supplier Info form is part of the pack.

**`summarised` handling:** a skill whose latest `completed[]` entry has
`result: summarised` is NOT done — surface it as the next step, but frame it as a
deep dive, e.g. *"Summarised in the bid plan — run for the full clause-by-clause
review."* Never present it as a blind repeat. Once its entry is `proceed` (or
`skipped`), treat it as complete.

**Advance criterion:** `bid-planner` done, `contract-risk` and
`compliance-matrix` both at `result: proceed` (or `skipped`), and `pqq-manager`
done or skipped (no PQQ). Bid advances to `estimating`.

**Note:** `ailtir_package-breakdown` is NOT part of pre-bid. It belongs to the
enquire-and-procure work in the `estimating` phase; the planner's Package Outline
tab is only a glance.

**Alternatives / sideways moves at this phase:**

- `ailtir_rfi-generator` — draft an RFI whenever a gap is found.
```

- [ ] **Step 2: Teach the conductor the `summarised` state**

In `plugin/skills/ailtir_conductor/SKILL.md`, in `## Step 4 — Recommend Next Actions`, append this paragraph at the end of the section (immediately before `## Step 5 — Prompt the User`):

```markdown
**`summarised` entries:** an entry in `completed[]` with `result: summarised` (written
by `ailtir_bid-planner` for compliance and contract-risk) counts as "overview done,
deep pass still valuable". Recommend it as `next_skill` and phrase the rationale as
a deep dive — e.g. "Summarised in the bid plan; run for the full clause-by-clause
review." Treat `result: proceed` or `skipped` as fully complete (do not re-recommend).
```

- [ ] **Step 3: Fix the "already completed" anti-pattern to exempt `summarised`**

In `plugin/skills/ailtir_conductor/SKILL.md`, in `## Anti-Patterns`, replace the line:

```
- DO NOT recommend a skill that is already in `completed[]` with `result: proceed` or better. Skipped skills can be re-recommended if the user changes their mind (they must explicitly ask).
```

with:

```
- DO NOT recommend a skill that is already in `completed[]` with `result: proceed`. An entry with `result: summarised` is NOT complete — recommend it as a deep dive (see Step 4). Skipped skills can be re-recommended if the user explicitly asks.
```

- [ ] **Step 4: Bump version**

Change `plugin_version`: `2.15.5` → `2.16.0` in the conductor's Usage Reporting block.

- [ ] **Step 5: Verify and commit**

Run: `grep -c "summarised" plugin/skills/ailtir_conductor/references/phase-map.md plugin/skills/ailtir_conductor/SKILL.md`
Expected: both files print a non-zero count.

```bash
git add plugin/skills/ailtir_conductor/references/phase-map.md plugin/skills/ailtir_conductor/SKILL.md
git commit -m "feat: conductor treats summarised as deep-dive next-step, promotes bid-planner"
```

---

### Task 9: PROCESS.md, README link, version bump

**Files:**
- Create: `plugin/PROCESS.md`
- Modify: `plugin/README.md`
- Modify: `plugin/.claude-plugin/plugin.json`
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write PROCESS.md**

Create `plugin/PROCESS.md`:

```markdown
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
```

- [ ] **Step 2: Link PROCESS.md from the README**

In `plugin/README.md`, add this line near the top (after the first heading/intro paragraph — pick the first blank line after the opening heading):

```markdown
> **New here?** Read [PROCESS.md](PROCESS.md) for the end-to-end bid lifecycle and how the skills fit together.
```

- [ ] **Step 3: Bump the manifest version**

In `plugin/.claude-plugin/plugin.json`, change `"version": "2.15.5"` to `"version": "2.16.0"`.

- [ ] **Step 4: Add a changelog entry**

At the top of `CHANGELOG.md` (immediately after the header block, before `## 2.15.5`), insert:

```markdown
## 2.16.0 - 2026-07-16

- Rewrote the bid-planner workbook as a deterministic 9-tab skeleton (structure
  script-owned, content model-supplied via `--data` JSON) — ending the
  improvised, inconsistent tab output.
- Inlined full Go/No-Go scoring into the bid-planner; added an Ailtir-branded
  kick-off deck (`create_bid_deck.js`).
- Gave `compliance-matrix` and `contract-risk` their own deterministic deep-dive
  workbook scripts; each writes its own file.
- Added the `summarised` completion state: the planner summarises compliance and
  risk, and the conductor recommends the deep dives as depth passes, not repeats.
- Promoted `bid-planner` to the canonical pre-bid entry point; moved
  `package-breakdown` guidance to the estimating phase.
- Added `PROCESS.md` documenting the full bid lifecycle as onboarding material.
```

- [ ] **Step 5: Verify the whole suite still passes**

Run:
```bash
cd plugin/skills/ailtir_bid-planner/scripts && python3 test_render.py && python3 test_bid_plan.py
cd ../../ailtir_compliance-matrix/scripts && python3 test_compliance_matrix.py
cd ../../ailtir_contract-risk/scripts && python3 test_risk_register.py
```
Expected: every file ends `ALL PASS`, exit 0.

Run: `grep -rn "2.15.5" plugin/skills/ailtir_bid-planner/SKILL.md plugin/skills/ailtir_compliance-matrix/SKILL.md plugin/skills/ailtir_contract-risk/SKILL.md plugin/skills/ailtir_conductor/SKILL.md plugin/.claude-plugin/plugin.json`
Expected: no matches (all bumped to 2.16.0).

- [ ] **Step 6: Commit**

```bash
git add plugin/PROCESS.md plugin/README.md plugin/.claude-plugin/plugin.json CHANGELOG.md
git commit -m "docs: add PROCESS.md lifecycle guide; bump plugin to 2.16.0"
```

---

## Notes for the implementer

- Run every command from the repo root (`ailtir-plugin/`) unless a step `cd`s elsewhere.
- The three `_xlsx_render.py` copies must stay byte-identical. If you change one, re-copy to the others (Tasks 3 & 4 copy from the Task 1 original).
- Do not add pytest or any new Python dependency. openpyxl is already present.
- The deck's `node_modules/` is gitignored (Task 5, Step 6); the committed artifacts are the `.js`, `package.json`, and (if produced) `package-lock.json`.
