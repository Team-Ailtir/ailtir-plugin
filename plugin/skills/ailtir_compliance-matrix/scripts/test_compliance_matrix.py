import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_compliance_matrix as C


def test_core_tabs():
    assert [t["title"] for t in C.CORE_TABS] == [
        "2. Award Criterion", "3. Mandatory Returnables",
        "4. Submission Rules", "5. Template & Document Gap Check",
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
