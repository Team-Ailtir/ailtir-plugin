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
