#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ailtir Takeoff — annotate.py.

Produce an annotated PDF from a source drawing plus a takeoff JSON.
Draws per-discipline coloured circular markers plus text callouts,
grouped into Optional Content Groups so a reviewer can toggle each
trade on and off in Bluebeam / Acrobat, and appends a summary legend
page.

Standards referenced:
  * PyMuPDF: Page.add_circle_annot / Page.add_freetext_annot /
    Annot.set_colors / Annot.set_border / Annot.set_opacity /
    Annot.update / Annot.set_oc / Document.add_ocg /
    Document.save(deflate=True, clean=False, garbage=0).
  * PDF 32000-1:2008 § 8.11 — Optional Content.
  * BS EN ISO 19650-2:2018 UK NA — single-character role codes.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import traceback
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import fitz  # PyMuPDF
except ImportError as _exc:  # pragma: no cover
    sys.stderr.write("annotate.py: PyMuPDF required: %s\n" % _exc)
    raise

# --- constants --------------------------------------------------------------

# Ailtir-brand palette tuned for CAD contrast. Yellow is a mustard (not
# pure yellow) so it survives white backgrounds; fire is magenta so it
# is unmistakable. Keyed by ISO 19650 single-character role code.
# Overridable programmatically by callers.
DISCIPLINE_COLOURS: Dict[str, str] = {
    "A": "#1F4E79", "S": "#C55A11", "M": "#C00000", "E": "#BF8F00",
    "P": "#008080", "C": "#7F5F3F", "L": "#548235", "F": "#C00099",
    "Z": "#595959",
}
DISCIPLINE_NAMES: Dict[str, str] = {
    "A": "Architectural", "S": "Structural", "M": "Mechanical",
    "E": "Electrical", "P": "Public Health", "C": "Civil",
    "L": "Landscape", "F": "Fire", "Z": "General",
}
OCG_TRADE_PREFIX = "Ailtir Takeoff — "
OCG_WATERMARK, OCG_LEGEND = "AILTIR: Watermark", "AILTIR: Legend"
LEGEND_W, LEGEND_H = 1191.0, 842.0                # A3 landscape (pt)
MARKER_MIN, MARKER_MAX = 3.0, 36.0
FONT_MIN, FONT_MAX = 5.0, 24.0
LOW_CONF = 0.5
OVERLAP_TOLERANCE = 0.20
CURRENCY_SYMBOLS = {"EUR": "€", "GBP": "£", "USD": "$", "AUD": "A$", "CAD": "C$"}


# --- tiny helpers -----------------------------------------------------------

def _log(msg: str) -> None:
    sys.stderr.write("annotate.py: %s\n" % msg)


def _hex_rgb(h: str) -> Tuple[float, float, float]:
    s = (h or "").lstrip("#").strip()
    if len(s) != 6:
        return (0.35, 0.35, 0.35)
    try:
        return (int(s[0:2], 16) / 255.0, int(s[2:4], 16) / 255.0, int(s[4:6], 16) / 255.0)
    except ValueError:
        return (0.35, 0.35, 0.35)


def _code(raw: Any) -> str:
    """Normalise a discipline value to a single upper-case role code."""
    if not raw:
        return "Z"
    c = str(raw).strip().upper()[:1]
    return c if c in DISCIPLINE_COLOURS else "Z"


def _ocg_name(code: str) -> str:
    return f"{OCG_TRADE_PREFIX}{code} · {DISCIPLINE_NAMES.get(code, 'General')}"


def _fmt_qty(qty: Any, unit: Any) -> str:
    if qty is None:
        return ""
    try:
        f = float(qty)
    except (TypeError, ValueError):
        return f"{qty}{(' ' + str(unit)) if unit else ''}"
    body = f"{int(round(f))}" if abs(f - round(f)) < 1e-9 else f"{f:.2f}"
    return f"{body}{(' ' + str(unit)) if unit else ''}"


def _label(sheet_number: str, item: Dict[str, Any]) -> str:
    """One-line callout label per spec §Callout labels."""
    tail = str(item.get("id", "?")).split("-")[-1] or str(item.get("id", "?"))
    cat = str(item.get("category") or "").replace("_", " ").strip().title()
    qty = _fmt_qty(item.get("quantity"), item.get("unit"))
    parts = [f"{sheet_number}-{tail}" if sheet_number else tail]
    if cat:
        parts.append(cat)
    if qty:
        parts.append(qty)
    return "  ".join(parts)


def _text_width(text: str, fontsize: float) -> float:
    try:
        return float(fitz.get_text_length(text, fontname="helv", fontsize=fontsize))
    except Exception:
        return len(text) * fontsize * 0.55


def _try(func, *args, **kwargs) -> None:
    """Call ``func``, swallow exceptions (for defensive annot properties)."""
    try:
        func(*args, **kwargs)
    except Exception:  # noqa: BLE001
        pass


# --- overlap-avoiding callout placement (unit-testable) --------------------

def _clamp(rect: "fitz.Rect", bounds: "fitz.Rect") -> "fitz.Rect":
    dx = max(bounds.x0 - rect.x0, 0.0) + min(bounds.x1 - rect.x1, 0.0)
    dy = max(bounds.y0 - rect.y0, 0.0) + min(bounds.y1 - rect.y1, 0.0)
    if dx == 0.0 and dy == 0.0:
        return rect
    return fitz.Rect(rect.x0 + dx, rect.y0 + dy, rect.x1 + dx, rect.y1 + dy)


def _overlap_frac(a: "fitz.Rect", b: "fitz.Rect") -> float:
    inter = a & b
    if not inter or inter.is_empty:
        return 0.0
    return float(inter.get_area()) / max(a.get_area(), 1e-6)


def place_callout(cx: float, cy: float, r: float, w: float, h: float,
                  placed: Sequence["fitz.Rect"], bounds: "fitz.Rect"
                  ) -> Tuple["fitz.Rect", int, bool]:
    """Pick the first non-overlapping candidate offset.

    Returns ``(rect, candidate_index, collided)``. Candidates are tried
    in the spec-mandated order: right-above (default), right-below,
    left-below, left-above, directly-above (centred), directly-below.
    If all six overlap existing rects by > OVERLAP_TOLERANCE, the
    default is returned with ``collided=True``.
    """
    pad = 2.0
    origins = [
        (cx + r + pad, cy - r - pad - h),        # 0: right-above
        (cx + r + pad, cy + r + pad),            # 1: right-below
        (cx - r - pad - w, cy + r + pad),        # 2: left-below
        (cx - r - pad - w, cy - r - pad - h),    # 3: left-above
        (cx - w / 2.0, cy - r - pad - h),        # 4: above, centred
        (cx - w / 2.0, cy + r + pad),            # 5: below, centred
    ]
    fallback: Optional["fitz.Rect"] = None
    for idx, (x0, y0) in enumerate(origins):
        rect = _clamp(fitz.Rect(x0, y0, x0 + w, y0 + h), bounds)
        if fallback is None:
            fallback = rect
        worst = max((_overlap_frac(rect, o) for o in placed), default=0.0)
        if worst <= OVERLAP_TOLERANCE:
            return rect, idx, False
    assert fallback is not None
    return fallback, 0, True


# --- profile-aware currency -------------------------------------------------

def resolve_currency(profile: Optional[str]) -> Tuple[str, str]:
    """Return (code, symbol) for the profile, falling back to EUR/€."""
    if not profile:
        return "EUR", "€"
    start = os.path.abspath(os.path.dirname(__file__) or ".")
    for _ in range(8):
        cand = os.path.join(start, "Context", "profiles", f"{profile}.json")
        if os.path.isfile(cand):
            try:
                with open(cand, "r", encoding="utf-8") as fh:
                    code = str((json.load(fh) or {}).get("currency") or "EUR").upper()
            except Exception as exc:  # noqa: BLE001 - fail-open
                _log(f"profile '{profile}' unreadable ({exc}); fallback EUR")
                code = "EUR"
            return code, CURRENCY_SYMBOLS.get(code, code + " ")
        parent = os.path.dirname(start)
        if parent == start:
            break
        start = parent
    return "EUR", "€"


# --- JSON schema (best-effort) ---------------------------------------------

def load_takeoff(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("takeoff JSON must be an object")
    if not isinstance(data.get("items"), list):
        raise ValueError("takeoff JSON missing 'items' array")
    if not isinstance(data.get("sheet") or {}, dict):
        raise ValueError("'sheet' must be an object")
    data["sheet"] = data.get("sheet") or {}
    return data


# --- annotation drawing -----------------------------------------------------

def _add_ocgs(doc: "fitz.Document", codes: Iterable[str]) -> Dict[str, int]:
    ocgs: Dict[str, int] = {}
    for code in sorted({_code(c) for c in codes}):
        try:
            ocgs[_ocg_name(code)] = doc.add_ocg(
                _ocg_name(code), on=True, intent="View", usage="View")
        except Exception as exc:  # noqa: BLE001
            _log(f"add_ocg({_ocg_name(code)}) failed: {exc}")
    for fixed in (OCG_WATERMARK, OCG_LEGEND):
        try:
            ocgs[fixed] = doc.add_ocg(fixed, on=True, intent="View", usage="View")
        except Exception as exc:  # noqa: BLE001
            _log(f"add_ocg({fixed}) failed: {exc}")
    return ocgs


def _watermark(page: "fitz.Page", sheet_number: str, ocg: Optional[int]) -> None:
    text = f"AILTIR TAKEOFF — sheet {sheet_number or '?'}"
    x, y = 24.0, page.rect.height - 18.0
    try:
        rect = fitz.Rect(x, y - 12, x + _text_width(text, 10.0) + 6, y + 4)
        a = page.add_freetext_annot(rect, text, fontsize=10, fontname="helv",
                                    text_color=(0.2, 0.2, 0.2),
                                    fill_color=(1, 1, 1), border_color=(1, 1, 1),
                                    align=0, richtext=True)
        _try(a.set_opacity, 0.30)
        a.update()
        if ocg is not None:
            _try(a.set_oc, ocg)
    except Exception as exc:  # noqa: BLE001
        _log(f"watermark on page {page.number + 1} failed: {exc}")


def _annotate_item(page: "fitz.Page", item: Dict[str, Any],
                   marker_radius: float, font_size: float,
                   sheet_number: str, ocg: Optional[int],
                   placed: List["fitz.Rect"]) -> bool:
    """Draw one marker + callout. Returns True if the coord was clamped."""
    code = _code(item.get("discipline"))
    rgb = _hex_rgb(DISCIPLINE_COLOURS.get(code, DISCIPLINE_COLOURS["Z"]))
    conf = item.get("confidence")
    low_conf = isinstance(conf, (int, float)) and float(conf) < LOW_CONF

    try:
        cx = float(item["x_pt"])
        cy = float(item["y_pt"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("missing/invalid x_pt or y_pt") from exc

    b = page.rect
    clamped = False
    if cx < b.x0 + marker_radius:
        cx, clamped = b.x0 + marker_radius, True
    if cx > b.x1 - marker_radius:
        cx, clamped = b.x1 - marker_radius, True
    if cy < b.y0 + marker_radius:
        cy, clamped = b.y0 + marker_radius, True
    if cy > b.y1 - marker_radius:
        cy, clamped = b.y1 - marker_radius, True
    if clamped:
        _log("item %s outside media box (page %d) — clamped"
             % (item.get("id", "?"), page.number + 1))

    # Circle marker.
    marker_rect = fitz.Rect(cx - marker_radius, cy - marker_radius,
                            cx + marker_radius, cy + marker_radius)
    circle = page.add_circle_annot(marker_rect)
    try:
        circle.set_colors(stroke=rgb, fill=rgb)
    except Exception:  # older signature
        circle.set_colors({"stroke": rgb, "fill": rgb})
    border: Dict[str, Any] = {"width": 1.5}
    if low_conf:
        # Ailtir differentiator: dashed marker for low-confidence items.
        border["dashes"] = [3, 2]
    _try(circle.set_border, border)
    _try(circle.set_opacity, 0.15)
    circle.update()
    if ocg is not None:
        _try(circle.set_oc, ocg)

    # Callout.
    label = _label(sheet_number, item)
    tw = _text_width(label, font_size) + 6.0
    th = font_size + 4.0
    callout_rect, chosen_idx, _collided = place_callout(
        cx, cy, marker_radius, tw, th, placed, b)

    ft = page.add_freetext_annot(callout_rect, label, fontsize=font_size,
                                 fontname="helv", text_color=(0, 0, 0),
                                 fill_color=(1, 1, 1), border_color=rgb, align=0,
                                 richtext=True)
    _try(ft.set_border, {"width": 0.5})
    ft.update()
    if ocg is not None:
        _try(ft.set_oc, ocg)
    placed.append(callout_rect)

    # Leader line when the callout was displaced off the default position.
    if chosen_idx != 0:
        try:
            edges = [
                ((callout_rect.x0 + callout_rect.x1) / 2.0, callout_rect.y0),
                ((callout_rect.x0 + callout_rect.x1) / 2.0, callout_rect.y1),
                (callout_rect.x0, (callout_rect.y0 + callout_rect.y1) / 2.0),
                (callout_rect.x1, (callout_rect.y0 + callout_rect.y1) / 2.0),
            ]
            edges.sort(key=lambda pt: (pt[0] - cx) ** 2 + (pt[1] - cy) ** 2)
            ex, ey = edges[0]
            dx, dy = cx - ex, cy - ey
            d = (dx * dx + dy * dy) ** 0.5 or 1.0
            marker_edge = (cx - dx / d * marker_radius,
                           cy - dy / d * marker_radius)
            shape = page.new_shape()
            shape.draw_line(fitz.Point(ex, ey), fitz.Point(*marker_edge))
            shape.finish(color=rgb, width=0.5, stroke_opacity=0.5)
            shape.commit(overlay=False)
        except Exception as exc:  # noqa: BLE001
            _log(f"leader for item {item.get('id', '?')} failed: {exc}")

    return clamped


# --- legend page ------------------------------------------------------------

def _legend_page(doc: "fitz.Document", items: Sequence[Dict[str, Any]],
                 sheet_number: str, currency_symbol: str,
                 flagged: Sequence[Dict[str, Any]], ocg: Optional[int]) -> None:
    page = doc.new_page(width=LEGEND_W, height=LEGEND_H)
    today = _dt.date.today().isoformat()
    now = _dt.datetime.now().replace(microsecond=0).isoformat()

    # Header band.
    page.insert_text(fitz.Point(40, 54), "AILTIR",
                     fontname="hebo", fontsize=24, color=(0, 0, 0))
    right = f"Takeoff Annotation Report — {sheet_number or '?'} — {today}"
    page.insert_text(
        fitz.Point(LEGEND_W - 40 - _text_width(right, 10.0), 50),
        right, fontname="helv", fontsize=10, color=(0, 0, 0))
    page.draw_line(fitz.Point(40, 80), fitz.Point(LEGEND_W - 40, 80),
                   color=(0, 0, 0), width=1.0)

    by_code: Dict[str, List[Dict[str, Any]]] = {}
    for it in items:
        by_code.setdefault(_code(it.get("discipline")), []).append(it)

    # Left column — colour key.
    x_left, y = 40.0, 110.0
    page.insert_text(fitz.Point(x_left, y), "DISCIPLINE COLOUR KEY",
                     fontname="hebo", fontsize=14, color=(0, 0, 0))
    y += 24.0
    for code in sorted(by_code):
        rgb = _hex_rgb(DISCIPLINE_COLOURS.get(code, DISCIPLINE_COLOURS["Z"]))
        page.draw_rect(fitz.Rect(x_left, y - 10, x_left + 24, y + 2),
                       color=rgb, fill=rgb, width=0.5)
        units: Dict[str, float] = {}
        for it in by_code[code]:
            try:
                q = float(it.get("quantity") or 0.0)
            except (TypeError, ValueError):
                q = 0.0
            units[str(it.get("unit") or "").strip()] = (
                units.get(str(it.get("unit") or "").strip(), 0.0) + q)
        parts = []
        for u, t in units.items():
            if abs(t - round(t)) < 1e-9:
                parts.append(f"{int(round(t))} {u}".strip())
            else:
                parts.append(f"{t:.1f} {u}".strip())
        totals_str = ", ".join(p for p in parts if p) or "0"
        page.insert_text(
            fitz.Point(x_left + 32, y),
            f"{code} · {DISCIPLINE_NAMES.get(code, 'General')} "
            f"— {len(by_code[code])} items ({totals_str})",
            fontname="helv", fontsize=10, color=(0, 0, 0))
        y += 18.0

    # Right column — indicative totals.
    x_right, y = 620.0, 110.0
    page.insert_text(fitz.Point(x_right, y), "TOTALS",
                     fontname="hebo", fontsize=14, color=(0, 0, 0))
    y += 24.0
    for code in sorted(by_code):
        if any("indicative_rate" in it for it in by_code[code]):
            tot = 0.0
            for it in by_code[code]:
                try:
                    tot += float(it.get("quantity") or 0.0) * float(it.get("indicative_rate") or 0.0)
                except (TypeError, ValueError):
                    continue
            value = f"~{currency_symbol}{tot:,.0f}"
        else:
            value = "— (rates not supplied)"
        page.insert_text(
            fitz.Point(x_right, y),
            f"{code} · {DISCIPLINE_NAMES.get(code, 'General')}  —  {value}",
            fontname="helv", fontsize=10, color=(0, 0, 0))
        y += 18.0
    page.insert_text(
        fitz.Point(x_right, LEGEND_H - 60),
        "Indicative totals only. Not a priced estimate. "
        "See NRM2 register (Excel) for the priced output.",
        fontname="heit", fontsize=8, color=(0.25, 0.25, 0.25))

    # Flagged items block.
    if flagged:
        y = max(y + 12.0, 400.0)
        page.insert_text(fitz.Point(x_left, y), "REVIEW REQUIRED",
                         fontname="hebo", fontsize=12, color=(0.55, 0, 0))
        y += 18.0
        for it in flagged[:20]:
            line = (f"{it.get('id', '?')}  ·  {_code(it.get('discipline'))}  "
                    f"·  {str(it.get('description') or '')[:60]}  "
                    f"·  {it.get('_reason', '')}")
            if it.get("note"):
                line += f"  — {str(it['note'])[:40]}"
            page.insert_text(fitz.Point(x_left, y), line,
                             fontname="helv", fontsize=9, color=(0, 0, 0))
            y += 14.0
            if y > LEGEND_H - 40:
                break

    # Footer.
    page.insert_text(
        fitz.Point(40, 800),
        f"Generated by Ailtir Takeoff · {now} · "
        "Colour key follows ISO 19650 role codes "
        "(see BS EN ISO 19650-2:2018 UK National Annex)",
        fontname="helv", fontsize=8, color=(0.3, 0.3, 0.3))

    if ocg is not None:
        for a in page.annots() or []:
            _try(a.set_oc, ocg)


# --- orchestration ----------------------------------------------------------

def build_annotated_pdf(source_pdf: str, takeoff: Dict[str, Any],
                        output_pdf: str, marker_radius: float, font_size: float,
                        page_filter: Optional[int], include_legend: bool,
                        legend_only: bool, profile: Optional[str]) -> Dict[str, Any]:
    doc = fitz.open(source_pdf)
    if page_filter is not None and (page_filter < 1 or page_filter > doc.page_count):
        doc.close()
        raise IndexError(f"--page {page_filter} out of range ({doc.page_count} pages)")

    sheet = takeoff.get("sheet") or {}
    sheet_number = str(sheet.get("sheet_number") or "").strip()
    default_page = int(sheet.get("page") or 1)

    items: List[Dict[str, Any]] = list(takeoff.get("items") or [])
    if page_filter is not None:
        items = [it for it in items
                 if int(it.get("page", default_page) or default_page) == page_filter]

    codes = {_code(it.get("discipline")) for it in items} or {"Z"}
    ocgs = _add_ocgs(doc, codes)
    _, currency_symbol = resolve_currency(profile)

    flagged: List[Dict[str, Any]] = []
    per_page_placed: Dict[int, List["fitz.Rect"]] = {}
    ok_count = fail_count = 0

    if not legend_only:
        if not items:
            doc.close()
            raise LookupError("no takeoff items intersect requested page(s)")
        for item in items:
            try:
                page_idx = int(item.get("page", default_page) or default_page) - 1
                if page_idx < 0 or page_idx >= doc.page_count:
                    raise ValueError(f"page {page_idx + 1} outside source range")
                page = doc[page_idx]
                code = _code(item.get("discipline"))
                clamped = _annotate_item(
                    page, item, marker_radius, font_size, sheet_number,
                    ocgs.get(_ocg_name(code)),
                    per_page_placed.setdefault(page_idx, []))
                ok_count += 1
                if clamped:
                    flagged.append({**item, "_reason": "coordinate_clamped"})
                conf = item.get("confidence")
                if isinstance(conf, (int, float)) and float(conf) < LOW_CONF:
                    flagged.append({**item, "_reason": "low_confidence"})
            except Exception as exc:  # noqa: BLE001 - fail-open per item
                fail_count += 1
                _log(f"item {item.get('id', '?')} failed "
                     f"({exc.__class__.__name__}: {exc}); skipped")

        wm = ocgs.get(OCG_WATERMARK)
        for idx in sorted(per_page_placed):
            _watermark(doc[idx], sheet_number, wm)

    if include_legend:
        _legend_page(doc, items, sheet_number, currency_symbol,
                     flagged, ocgs.get(OCG_LEGEND))

    out_dir = os.path.dirname(os.path.abspath(output_pdf))
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)
    try:
        # Non-destructive save: deflate keeps size down; clean=False +
        # garbage=0 preserves the original object structure so the
        # source and annotated PDFs remain diff-able (additions only).
        doc.save(output_pdf, deflate=True, clean=False, garbage=0)
    except Exception as exc:  # noqa: BLE001
        doc.close()
        raise OSError(f"cannot write output PDF: {exc}") from exc
    doc.close()

    return {"successful": ok_count, "failed": fail_count,
            "flagged": flagged, "disciplines": sorted(codes),
            "ocg_names": sorted(ocgs.keys())}


# --- CLI --------------------------------------------------------------------

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="annotate.py",
        description="Annotate a PDF from an Ailtir takeoff JSON.")
    p.add_argument("source_pdf")
    p.add_argument("takeoff_json")
    p.add_argument("-o", "--output", required=True)
    p.add_argument("--profile", default=None)
    p.add_argument("--page", type=int, default=None)
    p.add_argument("--marker-radius", type=float, default=9.0)
    p.add_argument("--font-size", type=float, default=8.0)
    p.add_argument("--no-legend", dest="legend", action="store_false")
    p.add_argument("--legend-only", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p


def _dry_run(takeoff: Dict[str, Any]) -> None:
    items = takeoff.get("items") or []
    counts: Dict[str, int] = {}
    for it in items:
        c = _code(it.get("discipline"))
        counts[c] = counts.get(c, 0) + 1
    print(f"annotate.py DRY-RUN: {len(items)} item(s) across {len(counts)} discipline(s)")
    for code in sorted(counts):
        print(f"  {code} · {DISCIPLINE_NAMES.get(code, 'General')}: {counts[code]} items")
    print("Would create OCG layers:")
    for code in sorted(counts):
        print(f"  {_ocg_name(code)}")
    print(f"  {OCG_WATERMARK}")
    print(f"  {OCG_LEGEND}")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)

    if not (MARKER_MIN <= args.marker_radius <= MARKER_MAX):
        _log(f"--marker-radius must be in [{MARKER_MIN}, {MARKER_MAX}]")
        return 7
    if not (FONT_MIN <= args.font_size <= FONT_MAX):
        _log(f"--font-size must be in [{FONT_MIN}, {FONT_MAX}]")
        return 7

    if not os.path.isfile(args.source_pdf):
        _log(f"source PDF not found: {args.source_pdf}")
        return 2
    try:
        probe = fitz.open(args.source_pdf)
        pc = probe.page_count
        probe.close()
        if pc < 1:
            _log("source PDF has no pages")
            return 2
    except Exception as exc:  # noqa: BLE001
        _log(f"source PDF unreadable: {exc}")
        return 2

    try:
        takeoff = load_takeoff(args.takeoff_json)
    except FileNotFoundError:
        _log(f"takeoff JSON not found: {args.takeoff_json}")
        return 3
    except (ValueError, json.JSONDecodeError) as exc:
        _log(f"takeoff JSON invalid: {exc}")
        return 3

    if args.dry_run:
        _dry_run(takeoff)
        return 0

    include_legend = bool(args.legend) or bool(args.legend_only)
    try:
        summary = build_annotated_pdf(
            source_pdf=args.source_pdf, takeoff=takeoff,
            output_pdf=args.output,
            marker_radius=float(args.marker_radius),
            font_size=float(args.font_size),
            page_filter=args.page, include_legend=include_legend,
            legend_only=bool(args.legend_only), profile=args.profile)
    except IndexError as exc:  # exit 5
        _log(str(exc))
        return 5
    except LookupError as exc:  # exit 6
        _log(str(exc))
        return 6
    except OSError as exc:  # exit 4
        _log(str(exc))
        return 4
    except Exception as exc:  # noqa: BLE001
        _log(f"unexpected failure: {exc}\n{traceback.format_exc()}")
        return 4

    print(f"annotate.py: wrote {args.output} — "
          f"{summary['successful']} annotated, {summary['failed']} skipped, "
          f"{len(summary['flagged'])} flagged, "
          f"{len(summary['ocg_names'])} OCG layer(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
