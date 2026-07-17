import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_risk_register as K


def test_core_tabs():
    assert [t["title"] for t in K.CORE_TABS] == [
        "2. Risk Register", "3. Schedule Part 1 - Data", "4. Action Tracker",
    ]


def test_titles_fit_excel_limit():
    # Excel caps sheet names at 31 chars; the engine truncates silently, so a
    # too-long title would lose characters. Guard every core-tab title here.
    import _xlsx_render as R
    for t in K.CORE_TABS:
        assert R.safe_sheet_title(t["title"]) == t["title"], t["title"]


def test_build_renders_all_sheets():
    import _xlsx_render as R
    wb = R.build_workbook(K.cover({"contract": "PW-CF5"}), R.merge_rows(K.CORE_TABS, {}))
    assert wb.sheetnames == [
        "1. Cover", "2. Risk Register", "3. Schedule Part 1 - Data",
        "4. Action Tracker",
    ], wb.sheetnames


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
