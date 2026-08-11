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


def test_load_data_missing_file_exits():
    # A bad --data path should exit(1) with a message, not a raw traceback.
    import tempfile, os
    missing = os.path.join(tempfile.gettempdir(), "definitely_no_such_ailtir.json")
    try:
        R.load_data(missing)
        assert False, "expected SystemExit"
    except SystemExit as e:
        assert e.code == 1


def test_save_workbook_creates_parent_dir(tmp_note="creates nested dir"):
    import tempfile, os
    d = tempfile.mkdtemp()
    nested = os.path.join(d, "a", "b", "out.xlsx")
    wb = R.build_workbook({"fields": []}, [{"title": "2. X", "headers": ["h"], "rows": [["v"]]}])
    R.save_workbook(wb, nested)
    assert os.path.exists(nested), nested


def test_sheet_title_sanitised():
    # Excel forbids / \ * ? : [ ] in sheet names; the tab spec keeps the display
    # title but the worksheet name is sanitised, so build_workbook must not raise.
    tabs = [{"title": "3. Go / No-Go", "headers": ["A"], "rows": [["x"]]}]
    wb = R.build_workbook({"fields": []}, tabs)
    assert "3. Go - No-Go" in wb.sheetnames, wb.sheetnames
    assert R.safe_sheet_title("a/b:c") == "a-b-c"
    assert len(R.safe_sheet_title("x" * 40)) == 31


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
