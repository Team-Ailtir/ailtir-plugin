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
