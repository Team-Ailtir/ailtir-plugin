#!/usr/bin/env python3
"""Ailtir takeoff — single-page PDF structured extractor.

Given a single-page construction drawing PDF (typically pre-split by
``split_and_extract.py``), read every structured signal a downstream
quantity-takeoff pipeline can hang measurements off, and emit a single
JSON blob. Every later stage in the takeoff pipeline (``validate.py``,
``annotate.py``, ``assembly_engine.py``) consumes this JSON rather than
the PDF itself, so the extraction is the audit-trail anchor for any
quantity that later appears in a bill.

The script is deliberately structured as five independent sub-extractors
plus a geometry pass-through:

* Text objects — via PyMuPDF ``page.get_text("dict")`` (see PyMuPDF
  documentation for the structured extraction API).
* Tag matching — regex patterns loaded from ``data/tags.json``, each
  carrying an ISO 19650 discipline role code (A, S, M, E, P, C, L, F,
  H, Q, ...) — see ``research/drawing-conventions.md`` § Role codes.
* Dimension annotations — three heuristics unioned (unit-suffix,
  adjacent-to-line, between-arrows).
* Scale — three-method cross-validated detector (text search of the
  title-block region per ``research/drawing-conventions.md`` § Standard
  title block content; grid-line spacing; scale-bar geometry per that
  document § Scale-bar detection). Explicit ``high|medium|low``
  confidence and ``methods_agreeing`` list.
* Legend regions — anchored on ``LEGEND`` / ``KEY`` / ``SYMBOLS`` /
  ``NOTATION`` keywords with row-pattern verification.
* Geometry — delegated to the sibling ``geometry`` module. This file
  never re-implements circle / arc / polyline / grid reconstruction.

Provenance follows the ISO 19650-1:2018 information-container idea:
every emitted JSON carries the source PDF's SHA-256 digest, the page
index, an ISO-8601 UTC timestamp, and any per-section warnings, so a
downstream quantity can always be traced back to the exact byte stream
and sheet it came from.

Non-goals (see spec): no OCR fallback, no vision-based extraction, no
interpretation of what tags mean, no unit conversion at extraction
time, no cross-page reasoning. A sheet stamped "DO NOT SCALE DRAWING"
is recorded faithfully (``reported_scale == "NTS"``); enforcement is a
``validate.py`` concern.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import math
import os
import re
import statistics
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# PyMuPDF is imported as ``fitz`` per its public documentation.
try:
    import fitz  # type: ignore
except ImportError as _fitz_import_err:  # pragma: no cover - env issue
    sys.stderr.write(
        "extract.py: PyMuPDF (fitz) is required. "
        f"Import failed: {_fitz_import_err}\n"
    )
    raise

# geometry.py is a sibling module — pure functions, no I/O.
# Per the takeoff spec, this file MUST NOT re-implement geometry.
try:
    import geometry  # type: ignore
except ImportError as _geo_err:  # pragma: no cover - env issue
    sys.stderr.write(
        "extract.py: sibling module 'geometry' is required but could "
        f"not be imported: {_geo_err}\n"
    )
    raise


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXTRACTOR_VERSION = "2.0"

# Profile-aware scale denominator allow-lists.
# Sourced from research/drawing-conventions.md § Standard drawing sizes
# and scales (typical UK/IE construction denominators).
SCALE_ALLOW_LISTS: Dict[str, List[int]] = {
    "ireland-gc": [2500, 1250, 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1],
    "uk-gc":       [2500, 1250, 1000, 500, 200, 100, 50, 20, 10, 5, 2, 1],
}
DEFAULT_PROFILE = "ireland-gc"

# ISO 216 sheet sizes in points (portrait). Landscape auto-detected by
# comparing which side is longer. ±5% tolerance per spec.
# 1 pt = 1/72 inch = 0.3528 mm.
ISO216_SHEETS_PT: Dict[str, Tuple[float, float]] = {
    "A0": (2384.0, 3370.0),
    "A1": (1684.0, 2384.0),
    "A2": (1191.0, 1684.0),
    "A3": (842.0, 1191.0),
    "A4": (595.0, 842.0),
}
SHEET_SIZE_TOLERANCE = 0.05

# Point <-> mm conversion factor (paper units).
PT_TO_MM = 25.4 / 72.0

# Grid-inference modules used by the grid-based scale detector.
# UK/IE typical structural grid modules (metres). See
# research/drawing-conventions.md § Typical scales.
ASSUMED_GRID_MODULES_M: List[float] = [6.0, 7.2, 7.5, 8.0, 9.0]

# Cross-validation tolerance between scale methods (relative denom).
SCALE_AGREEMENT_TOLERANCE = 0.10  # 10%

# Grid-square tolerance for horizontal vs vertical spacing to be
# treated as a square grid.
GRID_SQUARE_TOLERANCE = 0.05  # 5%

# Adjacent-to-line dimension proximity (points).
DIM_LINE_PROXIMITY_PT = 15.0

# Between-arrows heuristic: max length of an arrowhead segment
# (points) — real arrowheads on construction drawings are small.
ARROW_MAX_LENGTH_PT = 20.0

# Method priority for dimension dedup — higher wins.
_DIM_METHOD_PRIORITY = {
    "between-arrows": 3,
    "unit-suffix":    2,
    "adjacent-to-line": 1,
}

# Legend anchor keywords (uppercase, exact match after strip).
LEGEND_ANCHORS = {"LEGEND", "KEY", "SYMBOLS", "NOTATION"}

# Legend geometry-cluster / row heuristics (points).
LEGEND_ROW_MIN_HEIGHT_PT = 8.0
LEGEND_ROW_MAX_HEIGHT_PT = 30.0
LEGEND_SYMBOL_MAX_SIZE_PT = 40.0
LEGEND_SYMBOL_TO_TEXT_MAX_GAP_PT = 60.0
LEGEND_ROW_SPACING_TOLERANCE = 0.25
LEGEND_MIN_ROWS = 2

# Regexes reused across sub-extractors.
# Scale text patterns per research/drawing-conventions.md § Standard
# title block content: match "1:100", "1/100" (either separator).
RE_SCALE_TEXT = re.compile(r"\b1\s*[:/]\s*(\d{1,5})\b")
RE_NTS = re.compile(r"\bN\.?T\.?S\.?\b", re.IGNORECASE)
RE_SCALE_KEYWORD = re.compile(r"\bSCALE(?:\s*BAR)?\b", re.IGNORECASE)

# Dimension patterns — unit-suffix heuristic:
RE_DIM_WITH_UNIT = re.compile(
    r"^\s*(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>mm|cm|m|ft|'|\")?\s*$"
)
RE_DIM_BARE_NUMBER = re.compile(r"^\s*\d+(?:\.\d+)?\s*$")

# Scale-bar label metric magnitudes we accept when pairing text with
# rectangle groups (metres unless the text carries "mm").
SCALE_BAR_LABEL_NUMBERS = {0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _now_iso_utc() -> str:
    """ISO-8601 UTC timestamp, second precision. Trailing 'Z'."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_of_file(path: Path, chunk: int = 1 << 20) -> str:
    """SHA-256 hex digest of ``path``'s bytes. Streamed, not memory-bound."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _classify_page_size(width_pt: float, height_pt: float) -> str:
    """Return "A0".."A4" or "custom" — see research/drawing-conventions.md
    § Standard drawing sizes and scales. ±5% per spec."""
    if width_pt <= 0 or height_pt <= 0:
        return "custom"
    short, long_ = (width_pt, height_pt) if width_pt <= height_pt else (height_pt, width_pt)
    for label, (w_ref, h_ref) in ISO216_SHEETS_PT.items():
        ref_short = min(w_ref, h_ref)
        ref_long = max(w_ref, h_ref)
        if (
            abs(short - ref_short) / ref_short <= SHEET_SIZE_TOLERANCE
            and abs(long_ - ref_long) / ref_long <= SHEET_SIZE_TOLERANCE
        ):
            return label
    return "custom"


def _bbox_union(bboxes: Iterable[Sequence[float]]) -> Optional[List[float]]:
    """Axis-aligned union of a set of bboxes."""
    xs0, ys0, xs1, ys1 = [], [], [], []
    for b in bboxes:
        if b is None:
            continue
        xs0.append(float(b[0]))
        ys0.append(float(b[1]))
        xs1.append(float(b[2]))
        ys1.append(float(b[3]))
    if not xs0:
        return None
    return [min(xs0), min(ys0), max(xs1), max(ys1)]


def _bbox_center(b: Sequence[float]) -> Tuple[float, float]:
    return (0.5 * (b[0] + b[2]), 0.5 * (b[1] + b[3]))


def _distance(p: Sequence[float], q: Sequence[float]) -> float:
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return math.hypot(dx, dy)


def _round_denominator_to_allow_list(
    denom: float, allow_list: Sequence[int], tolerance: float = 0.10
) -> Optional[int]:
    """Snap a computed denominator to the nearest allow-list entry when
    within ``tolerance`` (relative). Returns None if nothing matches."""
    if denom <= 0:
        return None
    best: Optional[Tuple[float, int]] = None
    for d in allow_list:
        rel = abs(denom - d) / d
        if rel <= tolerance and (best is None or rel < best[0]):
            best = (rel, d)
    return best[1] if best else None


def _resolve_profile(cli_profile: Optional[str]) -> str:
    """Precedence: CLI flag > AILTIR_PROFILE env > DEFAULT_PROFILE."""
    if cli_profile and cli_profile in SCALE_ALLOW_LISTS:
        return cli_profile
    env = os.environ.get("AILTIR_PROFILE")
    if env and env in SCALE_ALLOW_LISTS:
        return env
    return DEFAULT_PROFILE


# ---------------------------------------------------------------------------
# Text extraction — PyMuPDF page.get_text("dict")
# ---------------------------------------------------------------------------


def extract_text_objects(page: "fitz.Page", page_number: int) -> List[Dict[str, Any]]:
    """Extract one entry per text *line* found by PyMuPDF's structured
    text API. See PyMuPDF documentation on ``page.get_text('dict')``:
    the return shape is ``{"blocks": [{"lines": [{"spans": [...]}], ...}]}``
    with span-level ``bbox``, ``font``, ``size``, ``color``, and ``flags``
    fields.

    Empty lines (after ``strip()``) are skipped. Line-level ``bbox`` is
    the union of its constituent spans. Font metadata comes from the
    first span of the line (most drawings do not mix fonts within a line;
    when they do, the first span is representative for downstream reasoning).
    """
    out: List[Dict[str, Any]] = []
    try:
        raw = page.get_text("dict")
    except Exception as exc:  # pragma: no cover - PyMuPDF internal
        sys.stderr.write(f"extract.py: text extraction failed: {exc}\n")
        return out

    for block_index, block in enumerate(raw.get("blocks", [])):
        # ``block["type"] == 0`` is text; image blocks are type 1.
        if block.get("type", 0) != 0:
            continue
        for line_index, line in enumerate(block.get("lines", [])):
            spans = line.get("spans", []) or []
            if not spans:
                continue

            # Concatenate span text. PyMuPDF preserves whitespace between
            # spans within a span's own text, so simple concatenation is
            # faithful — no extra spaces injected.
            text = "".join(span.get("text", "") for span in spans)
            if not text.strip():
                continue

            span_bboxes = [span.get("bbox") for span in spans if span.get("bbox")]
            bbox = _bbox_union(span_bboxes)
            if bbox is None:
                bbox = list(line.get("bbox", [0.0, 0.0, 0.0, 0.0]))

            first = spans[0]
            origin = first.get("origin", None)

            out.append({
                "text": text,
                "bbox": [float(v) for v in bbox],
                "page": page_number,
                "font": first.get("font", ""),
                "size": float(first.get("size", 0.0)),
                "color": int(first.get("color", 0)),
                "flags": int(first.get("flags", 0)),
                "block_index": block_index,
                "line_index": line_index,
                "origin": (
                    [float(origin[0]), float(origin[1])]
                    if isinstance(origin, (list, tuple)) and len(origin) >= 2
                    else None
                ),
            })
    return out


# ---------------------------------------------------------------------------
# Tag matching — data/tags.json (ISO 19650 discipline codes)
# ---------------------------------------------------------------------------


def _tags_json_path() -> Path:
    """Resolve ``data/tags.json`` relative to *this* file, so behaviour is
    CWD-independent."""
    return Path(__file__).resolve().parent.parent / "data" / "tags.json"


def load_tag_patterns(warnings: List[str]) -> List[Dict[str, Any]]:
    """Load and compile tag patterns.

    Missing file: warn and return an empty list (spec: do NOT crash).
    Malformed JSON: warn and return an empty list.
    Individual pattern failing to compile: warn and skip that entry.
    """
    path = _tags_json_path()
    if not path.exists():
        msg = f"tag-load: {path} not found; skipping tag matching."
        sys.stderr.write(f"extract.py: {msg}\n")
        warnings.append(msg)
        return []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"tag-load: could not parse {path.name}: {exc}"
        sys.stderr.write(f"extract.py: {msg}\n")
        warnings.append(msg)
        return []

    if not isinstance(raw, list):
        msg = "tag-load: data/tags.json is not a JSON list"
        sys.stderr.write(f"extract.py: {msg}\n")
        warnings.append(msg)
        return []

    compiled: List[Dict[str, Any]] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        name = entry.get("name")
        pattern = entry.get("pattern")
        discipline = entry.get("discipline", "Z")  # Z = general per ISO 19650
        if not name or not pattern:
            continue
        try:
            regex = re.compile(pattern)
        except re.error as exc:
            msg = (
                f"tag-load: pattern '{pattern}' (name={name}) failed to "
                f"compile: {exc}"
            )
            sys.stderr.write(f"extract.py: {msg}\n")
            warnings.append(msg)
            continue
        compiled.append({
            "name": str(name),
            "pattern": str(pattern),
            "discipline": str(discipline),
            "regex": regex,
        })
    return compiled


def match_tags(
    text_objects: Sequence[Dict[str, Any]],
    patterns: Sequence[Dict[str, Any]],
    page_number: int,
    warnings: List[str],
) -> List[Dict[str, Any]]:
    """Match each text object against each compiled pattern.

    Multiple patterns can hit the same text (e.g. ambiguous marks); all
    matches are recorded. Dedup key is
    ``(name, match_string, round(bbox[0], 1), round(bbox[1], 1))``.
    """
    if not patterns:
        return []
    seen: set = set()
    out: List[Dict[str, Any]] = []
    for idx, txt in enumerate(text_objects):
        raw_text = txt.get("text", "")
        stripped = raw_text.strip()
        if not stripped:
            continue
        bbox = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
        try:
            for pat in patterns:
                m = pat["regex"].search(stripped)
                if not m:
                    continue
                match_str = m.group(0)
                key = (
                    pat["name"],
                    match_str,
                    round(float(bbox[0]), 1),
                    round(float(bbox[1]), 1),
                )
                if key in seen:
                    continue
                seen.add(key)
                out.append({
                    "name": pat["name"],
                    "discipline": pat["discipline"],
                    "pattern": pat["pattern"],
                    "match": match_str,
                    "text_object_index": idx,
                    "bbox": [float(v) for v in bbox],
                    "page": page_number,
                })
        except Exception as exc:  # non-fatal per spec
            msg = f"tag-match: exception on text idx {idx}: {exc}"
            sys.stderr.write(f"extract.py: {msg}\n")
            warnings.append(msg)
            continue
    return out


# ---------------------------------------------------------------------------
# Dimension extraction — three heuristics, unioned, deduped
# ---------------------------------------------------------------------------


def extract_dimensions_unit_suffix(
    text_objects: Sequence[Dict[str, Any]],
    page_number: int,
) -> List[Dict[str, Any]]:
    """Heuristic (1): a text token that is a number optionally followed by
    a unit token (``mm``, ``m``, ``cm``, ``ft``, ``'``, ``"``).

    Bare numbers without a unit are excluded here — they get a second
    chance in the adjacent-to-line heuristic.
    """
    out: List[Dict[str, Any]] = []
    for idx, txt in enumerate(text_objects):
        stripped = txt.get("text", "").strip()
        if not stripped:
            continue
        m = RE_DIM_WITH_UNIT.match(stripped)
        if not m:
            continue
        unit = m.group("unit")
        if unit is None:
            # bare number — will be re-picked up by adjacent-to-line
            continue
        try:
            value = float(m.group("num"))
        except ValueError:
            continue
        out.append({
            "value": value,
            "unit": unit,
            "raw": m.group("num"),
            "method": "unit-suffix",
            "text_object_index": idx,
            "bbox": [float(v) for v in txt.get("bbox", [0.0, 0.0, 0.0, 0.0])],
            "nearest_line": None,
            "page": page_number,
        })
    return out


def _iter_geometry_lines(geometry_block: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """Yield the flat list of individual line-segment dicts stored under
    ``geometry_block["lines"]``. Each has ``p0``, ``p1``, ``orient``,
    ``length_pt`` at least."""
    yield from geometry_block.get("lines", []) or []


def extract_dimensions_adjacent_to_line(
    text_objects: Sequence[Dict[str, Any]],
    geometry_block: Dict[str, Any],
    page_number: int,
    proximity: float = DIM_LINE_PROXIMITY_PT,
) -> List[Dict[str, Any]]:
    """Heuristic (2): a bare positive number whose bbox centre is within
    ``proximity`` points of the midpoint of some horizontal/vertical line
    is treated as a dimension. ``unit`` is left as ``None`` since only
    proximity — not a suffix — establishes the reading.

    Only horizontal or vertical lines qualify (dimension lines are
    axis-aligned in almost every construction drawing).
    """
    lines = [
        ln for ln in _iter_geometry_lines(geometry_block)
        if ln.get("orient") in ("h", "v")
    ]
    if not lines:
        return []

    # Pre-compute midpoints once for O(N·M) scan.
    line_midpoints: List[Tuple[Tuple[float, float], Dict[str, Any]]] = []
    for ln in lines:
        p0 = ln.get("p0")
        p1 = ln.get("p1")
        if not p0 or not p1:
            continue
        mid = (0.5 * (p0[0] + p1[0]), 0.5 * (p0[1] + p1[1]))
        line_midpoints.append((mid, ln))

    out: List[Dict[str, Any]] = []
    for idx, txt in enumerate(text_objects):
        stripped = txt.get("text", "").strip()
        if not stripped:
            continue
        if not RE_DIM_BARE_NUMBER.match(stripped):
            continue
        try:
            value = float(stripped)
        except ValueError:
            continue
        if value <= 0:
            continue
        bbox = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
        centre = _bbox_center(bbox)

        best: Optional[Tuple[float, Dict[str, Any]]] = None
        for mid, ln in line_midpoints:
            d = _distance(centre, mid)
            if d <= proximity and (best is None or d < best[0]):
                best = (d, ln)
        if best is None:
            continue
        ln = best[1]
        endpoints = [ln["p0"][0], ln["p0"][1], ln["p1"][0], ln["p1"][1]]
        out.append({
            "value": value,
            "unit": None,
            "raw": stripped,
            "method": "adjacent-to-line",
            "text_object_index": idx,
            "bbox": [float(v) for v in bbox],
            "nearest_line": [float(v) for v in endpoints],
            "page": page_number,
        })
    return out


def _lines_are_collinear(
    ln_a: Dict[str, Any], ln_b: Dict[str, Any], angle_tol_deg: float = 3.0
) -> bool:
    """Two axis-aligned dimension arrowhead segments are collinear when
    they share orientation and either their common y-coord (horizontal)
    or x-coord (vertical) matches within a small tolerance."""
    if ln_a.get("orient") != ln_b.get("orient"):
        return False
    if ln_a.get("orient") == "h":
        ya = 0.5 * (ln_a["p0"][1] + ln_a["p1"][1])
        yb = 0.5 * (ln_b["p0"][1] + ln_b["p1"][1])
        return abs(ya - yb) <= 2.0
    if ln_a.get("orient") == "v":
        xa = 0.5 * (ln_a["p0"][0] + ln_a["p1"][0])
        xb = 0.5 * (ln_b["p0"][0] + ln_b["p1"][0])
        return abs(xa - xb) <= 2.0
    return False


def extract_dimensions_between_arrows(
    text_objects: Sequence[Dict[str, Any]],
    geometry_block: Dict[str, Any],
    page_number: int,
) -> List[Dict[str, Any]]:
    """Heuristic (3): a pair of short collinear line segments (dimension
    arrowheads pointing at each other) enclosing exactly one numeric
    text object.

    Because arrowheads on a typical dimension line are short (<20 pt),
    we filter candidate lines by length before pairing. For each pair
    of same-orientation short collinear segments, we take their combined
    bbox and check if it contains exactly one bare-number text token.
    """
    lines = list(_iter_geometry_lines(geometry_block))
    short = [
        ln for ln in lines
        if ln.get("orient") in ("h", "v")
        and float(ln.get("length_pt", 0.0)) <= ARROW_MAX_LENGTH_PT
    ]
    if len(short) < 2:
        return []

    # Pre-index numeric text tokens with their bbox centres.
    numeric_tokens: List[Tuple[int, Dict[str, Any], Tuple[float, float]]] = []
    for idx, txt in enumerate(text_objects):
        s = txt.get("text", "").strip()
        if RE_DIM_BARE_NUMBER.match(s):
            bbox = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
            numeric_tokens.append((idx, txt, _bbox_center(bbox)))
    if not numeric_tokens:
        return []

    out: List[Dict[str, Any]] = []
    consumed_pairs: set = set()

    for i in range(len(short)):
        for j in range(i + 1, len(short)):
            a, b = short[i], short[j]
            if not _lines_are_collinear(a, b):
                continue
            # Combined bbox of the two arrowhead segments.
            xs = [a["p0"][0], a["p1"][0], b["p0"][0], b["p1"][0]]
            ys = [a["p0"][1], a["p1"][1], b["p0"][1], b["p1"][1]]
            comb_bbox = (min(xs), min(ys), max(xs), max(ys))
            # For the pair to represent an outward-pointing dimension,
            # the horizontal (or vertical) separation must be > 2× arrow
            # length — otherwise we're pairing the two ends of the same
            # tiny mark.
            if a.get("orient") == "h":
                span = comb_bbox[2] - comb_bbox[0]
            else:
                span = comb_bbox[3] - comb_bbox[1]
            if span < 2 * ARROW_MAX_LENGTH_PT:
                continue

            enclosed: List[Tuple[int, Dict[str, Any]]] = []
            for tok_idx, tok, centre in numeric_tokens:
                if (comb_bbox[0] <= centre[0] <= comb_bbox[2]
                        and comb_bbox[1] <= centre[1] <= comb_bbox[3]):
                    enclosed.append((tok_idx, tok))
            if len(enclosed) != 1:
                continue

            tok_idx, tok = enclosed[0]
            pair_key = (tok_idx, i, j)
            if pair_key in consumed_pairs:
                continue
            consumed_pairs.add(pair_key)

            stripped = tok.get("text", "").strip()
            try:
                value = float(stripped)
            except ValueError:
                continue

            # Line endpoints straddling the token — pick the segment
            # whose bbox is longest along the shared axis as the primary
            # "nearest line" record.
            near = a if float(a.get("length_pt", 0.0)) >= float(b.get("length_pt", 0.0)) else b
            near_endpoints = [
                near["p0"][0], near["p0"][1], near["p1"][0], near["p1"][1],
            ]

            out.append({
                "value": value,
                "unit": None,
                "raw": stripped,
                "method": "between-arrows",
                "text_object_index": tok_idx,
                "bbox": [float(v) for v in tok.get("bbox", [0, 0, 0, 0])],
                "nearest_line": [float(v) for v in near_endpoints],
                "page": page_number,
            })
    return out


def deduplicate_dimensions(records: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Dedup key is ``(round(bbox[0],1), round(bbox[1],1), value)``.
    On collision, keep the highest-confidence method
    (between-arrows > unit-suffix > adjacent-to-line)."""
    best_by_key: Dict[Tuple[float, float, float], Dict[str, Any]] = {}
    for r in records:
        bbox = r.get("bbox", [0.0, 0.0, 0.0, 0.0])
        key = (round(float(bbox[0]), 1), round(float(bbox[1]), 1), float(r["value"]))
        prev = best_by_key.get(key)
        if prev is None:
            best_by_key[key] = r
            continue
        if _DIM_METHOD_PRIORITY.get(r["method"], 0) > _DIM_METHOD_PRIORITY.get(prev["method"], 0):
            best_by_key[key] = r
    return list(best_by_key.values())


# ---------------------------------------------------------------------------
# Scale detection — three independent methods + cross-validation
# ---------------------------------------------------------------------------


def _title_block_region(width: float, height: float) -> Tuple[Tuple[float, float, float, float], ...]:
    """Two candidate rectangles: right 25% and bottom 20%.

    Per research/drawing-conventions.md § Standard title block content
    the title block is nearly always in the bottom-right corner of UK/EU
    drawings; a two-region search catches both landscape and portrait
    orientations without a false-positive-prone corner intersection.
    """
    right = (0.75 * width, 0.0, width, height)
    bottom = (0.0, 0.80 * height, width, height)
    return (right, bottom)


def _bbox_intersects_region(bbox: Sequence[float], region: Sequence[float]) -> bool:
    return not (
        bbox[2] < region[0]
        or bbox[0] > region[2]
        or bbox[3] < region[1]
        or bbox[1] > region[3]
    )


def detect_scale_from_text(
    text_objects: Sequence[Dict[str, Any]],
    page_width: float,
    page_height: float,
    profile_allow_list: Sequence[int],
    warnings: List[str],
) -> Dict[str, Any]:
    """Method (a): scan the title-block region for ``1:<denom>`` or NTS.

    Returns ``{"scale": "1:100"|"NTS"|None, "bbox": [...], "notes": ...}``.
    Non-standard denominators (outside ``profile_allow_list``) are still
    emitted but flagged in ``notes``.
    """
    regions = _title_block_region(page_width, page_height)
    result: Dict[str, Any] = {"scale": None, "bbox": None, "notes": None}

    def _in_title_block(bbox: Sequence[float]) -> bool:
        return any(_bbox_intersects_region(bbox, r) for r in regions)

    # First pass: NTS wins over a numeric ratio (per spec, NTS is a
    # legitimate reported_scale, and its presence explicitly overrides
    # any denominator-based reading). Prefer a title-block hit; fall back
    # to any NTS stamp on the page.
    nts_title_block: Optional[Sequence[float]] = None
    nts_fallback: Optional[Sequence[float]] = None
    for txt in text_objects:
        stripped = txt.get("text", "").strip()
        if not stripped:
            continue
        bbox = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
        if not RE_NTS.search(stripped):
            continue
        if _in_title_block(bbox):
            nts_title_block = bbox
            break
        if nts_fallback is None:
            nts_fallback = bbox
    if nts_title_block is not None or nts_fallback is not None:
        bbox = nts_title_block or nts_fallback
        result["scale"] = "NTS"
        result["bbox"] = [float(v) for v in bbox]  # type: ignore[arg-type]
        result["notes"] = (
            "text: NTS ('Not to Scale') stamp detected"
            if nts_title_block is not None
            else "text: NTS ('Not to Scale') stamp detected outside title-block region"
        )
        return result

    # Prefer a title-block hit, but fall back to any "Scale 1:N" match on the
    # page so drawings that place the scale near a scale-bar or in body text
    # (common on Irish/UK contract drawings) are still resolved.
    title_block_hit: Optional[Dict[str, Any]] = None
    fallback_hit: Optional[Dict[str, Any]] = None
    for txt in text_objects:
        stripped = txt.get("text", "").strip()
        if not stripped:
            continue
        bbox = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
        m = RE_SCALE_TEXT.search(stripped)
        if not m:
            continue
        try:
            denom = int(m.group(1))
        except ValueError:
            continue
        if denom <= 0:
            continue
        hit = {
            "scale": f"1:{denom}",
            "bbox": [float(v) for v in bbox],
            "denom": denom,
            "in_title_block": _in_title_block(bbox),
        }
        if hit["in_title_block"] and title_block_hit is None:
            title_block_hit = hit
        elif fallback_hit is None:
            fallback_hit = hit

    chosen = title_block_hit or fallback_hit
    if chosen is not None:
        result["scale"] = chosen["scale"]
        result["bbox"] = chosen["bbox"]
        if not chosen["in_title_block"]:
            result["notes"] = "text: scale found outside title-block region"
        if chosen["denom"] not in profile_allow_list:
            note = f"text: non-standard denominator {chosen['scale']} (outside profile allow-list)"
            result["notes"] = (result["notes"] + "; " if result["notes"] else "") + note
            warnings.append(f"scale-text: {note}")
        return result

    return result


def detect_scale_from_grid(
    geometry_block: Dict[str, Any],
    profile_allow_list: Sequence[int],
    warnings: List[str],
) -> Dict[str, Any]:
    """Method (b): infer scale from detected structural grid spacing.

    Formula: the physical grid module (metres) at scale ``1:D`` occupies
    ``module_m * 1000 / D`` millimetres on paper, i.e. ``spacing_pt *
    PT_TO_MM`` mm. Solve ``D = module_m * 1000 / (spacing_pt * PT_TO_MM)``.
    """
    result: Dict[str, Any] = {
        "scale": None,
        "evidence": None,
        "notes": None,
    }
    grid = geometry_block.get("grid_lines") or {}
    spacing = grid.get("spacing_pt") or {}
    h_spacing = spacing.get("h")
    v_spacing = spacing.get("v")

    # Prefer the square-grid case; if only one axis has spacing, use it.
    chosen_spacing: Optional[float] = None
    if h_spacing and v_spacing:
        avg = 0.5 * (h_spacing + v_spacing)
        if avg <= 0:
            return result
        rel = abs(h_spacing - v_spacing) / avg
        if rel <= GRID_SQUARE_TOLERANCE:
            chosen_spacing = avg
        else:
            # Non-square grid — use the shorter side (typically the
            # bay spacing, not the beam spacing).
            chosen_spacing = min(h_spacing, v_spacing)
            warnings.append(
                f"scale-grid: horizontal ({h_spacing:.2f} pt) and vertical "
                f"({v_spacing:.2f} pt) grid spacings differ by {rel*100:.1f}%"
            )
    elif h_spacing:
        chosen_spacing = h_spacing
    elif v_spacing:
        chosen_spacing = v_spacing

    if not chosen_spacing or chosen_spacing <= 0:
        return result

    spacing_mm_on_paper = chosen_spacing * PT_TO_MM

    # Try each assumed grid module, keeping the candidate whose denominator
    # snaps cleanest to the profile allow-list.
    best: Optional[Tuple[float, float, int]] = None  # (rel, module_m, denom)
    for module_m in ASSUMED_GRID_MODULES_M:
        module_mm = module_m * 1000.0
        denom_raw = module_mm / spacing_mm_on_paper
        snapped = _round_denominator_to_allow_list(denom_raw, profile_allow_list, tolerance=0.10)
        if snapped is None:
            continue
        rel = abs(denom_raw - snapped) / snapped
        if best is None or rel < best[0]:
            best = (rel, module_m, snapped)

    if best is None:
        # No allow-list match — still report the raw best guess (using
        # the first module) but flag as non-standard.
        module_m = ASSUMED_GRID_MODULES_M[0]
        module_mm = module_m * 1000.0
        denom_raw = module_mm / spacing_mm_on_paper
        denom_int = int(round(denom_raw))
        if denom_int <= 0:
            return result
        result["scale"] = f"1:{denom_int}"
        result["evidence"] = {
            "spacing_pt": float(chosen_spacing),
            "assumed_grid_m": float(module_m),
        }
        result["notes"] = f"grid: non-standard denominator 1:{denom_int}"
        warnings.append(result["notes"])
        return result

    _, module_m, denom = best
    result["scale"] = f"1:{denom}"
    result["evidence"] = {
        "spacing_pt": float(chosen_spacing),
        "assumed_grid_m": float(module_m),
    }
    return result


def _find_scale_bar_search_region(
    text_objects: Sequence[Dict[str, Any]],
    page_width: float,
    page_height: float,
) -> Sequence[float]:
    """A region 100pt below/right of any 'SCALE' text; else bottom 15%
    of the page. Per research/drawing-conventions.md § Scale-bar detection.
    """
    for txt in text_objects:
        s = txt.get("text", "").strip()
        if RE_SCALE_KEYWORD.search(s):
            b = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
            return (
                float(b[0]) - 20.0,
                float(b[1]) - 20.0,
                min(page_width, float(b[2]) + 300.0),
                min(page_height, float(b[3]) + 100.0),
            )
    return (0.0, 0.85 * page_height, page_width, page_height)


def detect_scale_from_bar(
    text_objects: Sequence[Dict[str, Any]],
    geometry_block: Dict[str, Any],
    page_width: float,
    page_height: float,
    profile_allow_list: Sequence[int],
    warnings: List[str],
) -> Dict[str, Any]:
    """Method (c): find a horizontal group of 5-10 small rectangles
    (the classic ruler pattern) near a 'SCALE' text token; pair with
    metric numeric labels to derive scale.

    Per research/drawing-conventions.md § Scale-bar detection.
    """
    result: Dict[str, Any] = {
        "scale": None,
        "bbox": None,
        "notes": None,
    }

    region = _find_scale_bar_search_region(text_objects, page_width, page_height)

    # Candidate rectangles: closed-area polygons in geometry with small
    # bbox height and any width, contained within the search region.
    closed_areas = geometry_block.get("closed_areas", []) or []
    candidates: List[Sequence[float]] = []
    for area in closed_areas:
        bb = area.get("bbox")
        if not bb:
            continue
        if not _bbox_intersects_region(bb, region):
            continue
        width = bb[2] - bb[0]
        height = bb[3] - bb[1]
        # Scale-bar segments: thin, wider than tall, small vertical extent.
        if height <= 0 or width <= 0:
            continue
        if height > 15.0 or width < 2.0 or width > 200.0:
            continue
        if width / height < 1.2:  # roughly landscape-oriented
            continue
        candidates.append(bb)

    if len(candidates) < 5:
        # Not enough candidate rectangles for a scale bar. Not fatal.
        return result

    # Sort by x, then group into contiguous horizontal runs sharing the
    # same y-range.
    candidates.sort(key=lambda b: (round(0.5 * (b[1] + b[3]), 0), b[0]))
    groups: List[List[Sequence[float]]] = []
    current: List[Sequence[float]] = []
    for bb in candidates:
        if not current:
            current = [bb]
            continue
        prev = current[-1]
        prev_cy = 0.5 * (prev[1] + prev[3])
        cy = 0.5 * (bb[1] + bb[3])
        # Same row? Within ~5 pt vertical centre.
        if abs(cy - prev_cy) <= 5.0 and bb[0] - prev[2] <= 5.0:
            current.append(bb)
        else:
            if len(current) >= 5:
                groups.append(current)
            current = [bb]
    if len(current) >= 5:
        groups.append(current)

    if not groups:
        warnings.append("scale-bar-detection: no contiguous rectangle group found")
        return result

    # Pick the largest contiguous group.
    group = max(groups, key=len)
    if len(group) > 10:
        group = group[:10]  # take the leading run, per spec heuristic

    # Group bbox (paper-space width in points).
    xs0 = min(b[0] for b in group)
    xs1 = max(b[2] for b in group)
    ys0 = min(b[1] for b in group)
    ys1 = max(b[3] for b in group)
    total_width_pt = xs1 - xs0
    if total_width_pt <= 0:
        return result

    # Find numeric labels within 40 pt margin of the group.
    label_region = (xs0 - 40.0, ys0 - 40.0, xs1 + 40.0, ys1 + 40.0)
    numbers: List[Tuple[float, bool]] = []  # (value, is_mm)
    for txt in text_objects:
        s = txt.get("text", "").strip()
        if not s:
            continue
        b = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
        if not _bbox_intersects_region(b, label_region):
            continue
        m = re.match(r"^(\d+(?:\.\d+)?)\s*(mm|m)?$", s)
        if not m:
            continue
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        is_mm = (m.group(2) or "").lower() == "mm"
        if int(v) in SCALE_BAR_LABEL_NUMBERS or v in SCALE_BAR_LABEL_NUMBERS:
            numbers.append((v, is_mm))

    if not numbers:
        warnings.append("scale-bar-detection: rectangle group found but no numeric labels nearby")
        return result

    # Assume the largest numeric label is the total distance the bar
    # represents; unit follows the label if present, else default metric
    # metres for construction drawings.
    numbers.sort(key=lambda t: t[0])
    total_value, is_mm = numbers[-1]
    real_world_mm = total_value if is_mm else (total_value * 1000.0)
    if real_world_mm <= 0:
        return result

    paper_width_mm = total_width_pt * PT_TO_MM
    if paper_width_mm <= 0:
        return result
    denom_raw = real_world_mm / paper_width_mm
    snapped = _round_denominator_to_allow_list(denom_raw, profile_allow_list, tolerance=0.15)
    if snapped is None:
        denom_int = int(round(denom_raw))
        note = f"scale-bar: non-standard denominator 1:{denom_int}"
        warnings.append(note)
        result["notes"] = note
        if denom_int <= 0:
            return result
        result["scale"] = f"1:{denom_int}"
    else:
        result["scale"] = f"1:{snapped}"

    result["bbox"] = [xs0, ys0, xs1, ys1]
    return result


def _denominator_of(scale_str: Optional[str]) -> Optional[int]:
    if not scale_str or not scale_str.startswith("1:"):
        return None
    try:
        return int(scale_str.split(":", 1)[1])
    except ValueError:
        return None


def cross_validate_scale(
    text_result: Dict[str, Any],
    grid_result: Dict[str, Any],
    bar_result: Dict[str, Any],
    warnings: List[str],
) -> Dict[str, Any]:
    """Combine the three method results into the final ``scale`` dict.

    Rules (per spec):

    * If any two methods agree within ``SCALE_AGREEMENT_TOLERANCE`` (10%)
      → ``confidence: "high"``.
    * Exactly one method fires → ``confidence: "medium"``.
    * Two fire but disagree → ``confidence: "low"``; ``reported_scale``
      picks text > grid > scale-bar (unless text is NTS, then next-best).
    * Always record ``methods_agreeing`` explicitly.
    """
    combined: Dict[str, Any] = {
        "text_scale": text_result.get("scale"),
        "text_scale_bbox": text_result.get("bbox"),
        "grid_scale": grid_result.get("scale"),
        "grid_evidence": grid_result.get("evidence"),
        "scale_bar_scale": bar_result.get("scale"),
        "scale_bar_bbox": bar_result.get("bbox"),
        "reported_scale": None,
        "confidence": "low",
        "methods_agreeing": [],
        "notes": None,
    }

    # Collect firing methods by (name, denom); NTS is a special text case.
    method_denoms: List[Tuple[str, Optional[int], str]] = []
    for name, res in (
        ("text", text_result),
        ("grid", grid_result),
        ("scale-bar", bar_result),
    ):
        sc = res.get("scale")
        if sc is None:
            continue
        denom = _denominator_of(sc)
        method_denoms.append((name, denom, sc))

    if not method_denoms:
        combined["notes"] = "no scale detected by any method"
        return combined

    # Special-case NTS: if text method returned NTS, that's the record —
    # confidence is medium unless another method also fires (in which
    # case we still call out the NTS stamp in notes).
    text_scale = text_result.get("scale")
    if text_scale == "NTS":
        combined["reported_scale"] = "NTS"
        # NTS blocks reliable measurement; treat as medium confidence
        # regardless of what geometry says.
        combined["confidence"] = "medium"
        combined["methods_agreeing"] = ["text"]
        note_parts = ["text stamp: NTS (Not to Scale)"]
        if grid_result.get("scale"):
            note_parts.append(f"grid method produced {grid_result['scale']} but is superseded by NTS")
        if bar_result.get("scale"):
            note_parts.append(f"scale-bar produced {bar_result['scale']} but is superseded by NTS")
        combined["notes"] = "; ".join(note_parts)
        return combined

    # Filter to numeric methods only.
    numeric_methods: List[Tuple[str, int, str]] = [
        (n, d, s) for (n, d, s) in method_denoms if d is not None and d > 0
    ]

    if len(numeric_methods) == 1:
        n, d, s = numeric_methods[0]
        combined["reported_scale"] = s
        combined["confidence"] = "medium"
        combined["methods_agreeing"] = [n]
        combined["notes"] = f"only {n} method fired"
        return combined

    # Check pairwise agreement within tolerance.
    agreeing: List[str] = []
    for i in range(len(numeric_methods)):
        for j in range(i + 1, len(numeric_methods)):
            ni, di, _ = numeric_methods[i]
            nj, dj, _ = numeric_methods[j]
            ref = max(di, dj)
            if abs(di - dj) / ref <= SCALE_AGREEMENT_TOLERANCE:
                if ni not in agreeing:
                    agreeing.append(ni)
                if nj not in agreeing:
                    agreeing.append(nj)

    priority_order = {"text": 0, "grid": 1, "scale-bar": 2}
    sorted_methods = sorted(numeric_methods, key=lambda t: priority_order.get(t[0], 99))

    if agreeing:
        # Pick reported_scale from an agreeing method in priority order.
        agreeing_sorted = sorted(agreeing, key=lambda n: priority_order.get(n, 99))
        chosen_name = agreeing_sorted[0]
        chosen = next((m for m in numeric_methods if m[0] == chosen_name), sorted_methods[0])
        combined["reported_scale"] = chosen[2]
        combined["confidence"] = "high"
        combined["methods_agreeing"] = agreeing_sorted
        combined["notes"] = (
            f"{' and '.join(agreeing_sorted)} within "
            f"{int(SCALE_AGREEMENT_TOLERANCE * 100)}% — high confidence"
        )
        return combined

    # Two or more methods, none agree.
    chosen = sorted_methods[0]
    combined["reported_scale"] = chosen[2]
    combined["confidence"] = "low"
    combined["methods_agreeing"] = []
    disagreement_desc = "; ".join(f"{n}={s}" for (n, _, s) in numeric_methods)
    combined["notes"] = f"methods disagree ({disagreement_desc}); using {chosen[0]} per priority"
    warnings.append(f"scale-cross-validate: methods disagree ({disagreement_desc})")
    return combined


# ---------------------------------------------------------------------------
# Legend detection
# ---------------------------------------------------------------------------


def _small_geometry_clusters(
    geometry_block: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Small geometry clusters — circles, closed polygons, and polylines
    with bbox no larger than ``LEGEND_SYMBOL_MAX_SIZE_PT`` on the longer
    side. Suitable candidates for legend "symbol" columns."""
    small: List[Dict[str, Any]] = []
    for coll_key in ("circles", "closed_areas", "polylines"):
        for item in geometry_block.get(coll_key, []) or []:
            bb = item.get("bbox")
            if not bb:
                continue
            w = bb[2] - bb[0]
            h = bb[3] - bb[1]
            if max(w, h) > LEGEND_SYMBOL_MAX_SIZE_PT:
                continue
            small.append({"bbox": bb, "kind": coll_key})
    return small


def detect_legends(
    text_objects: Sequence[Dict[str, Any]],
    geometry_block: Dict[str, Any],
    warnings: List[str],
) -> List[Dict[str, Any]]:
    """Detect legend regions anchored on ``LEGEND`` / ``KEY`` / ``SYMBOLS``
    / ``NOTATION``. Each region is a downward/rightward-growing pattern of
    ``symbol + short text`` rows.

    A region requires >= LEGEND_MIN_ROWS such rows to reduce false
    positives.  If the anchor is found but no rows fit, the region is
    still emitted with ``entries: []`` and a warning is logged.
    """
    legends: List[Dict[str, Any]] = []
    small_symbols = _small_geometry_clusters(geometry_block)

    for anchor_idx, anchor in enumerate(text_objects):
        stripped = anchor.get("text", "").strip().upper()
        if stripped not in LEGEND_ANCHORS:
            continue

        anchor_bbox = anchor.get("bbox", [0.0, 0.0, 0.0, 0.0])
        anchor_x0 = float(anchor_bbox[0])
        anchor_y_top = float(anchor_bbox[3])  # rows begin below anchor bottom

        # Candidate rows: pairs of (symbol bbox, text object) where the
        # symbol is on the left, and the text object begins within
        # LEGEND_SYMBOL_TO_TEXT_MAX_GAP_PT to the right, at approximately
        # the same y range, below the anchor.
        rows: List[Dict[str, Any]] = []
        for sym in small_symbols:
            sb = sym["bbox"]
            sym_cy = 0.5 * (sb[1] + sb[3])
            sym_height = sb[3] - sb[1]
            if sym_cy <= anchor_y_top:
                continue
            # Must be roughly under-or-right-of the anchor
            if sb[2] < anchor_x0 - 50.0:
                continue
            if sym_height < LEGEND_ROW_MIN_HEIGHT_PT * 0.5:
                pass  # tiny symbols still count; row height comes from the text
            # Find text object to the right of the symbol.
            best_text: Optional[Tuple[int, Dict[str, Any], float]] = None
            for t_idx, txt in enumerate(text_objects):
                if t_idx == anchor_idx:
                    continue
                if not txt.get("text", "").strip():
                    continue
                tb = txt.get("bbox", [0.0, 0.0, 0.0, 0.0])
                tcy = 0.5 * (tb[1] + tb[3])
                if abs(tcy - sym_cy) > max(sym_height, LEGEND_ROW_MAX_HEIGHT_PT) * 0.5:
                    continue
                if tb[0] < sb[2] - 2.0:
                    continue
                gap = tb[0] - sb[2]
                if gap > LEGEND_SYMBOL_TO_TEXT_MAX_GAP_PT:
                    continue
                if best_text is None or gap < best_text[2]:
                    best_text = (t_idx, txt, gap)
            if best_text is None:
                continue
            t_idx, txt, _gap = best_text
            row_height = max(sb[3], txt.get("bbox", [0, 0, 0, 0])[3]) - min(
                sb[1], txt.get("bbox", [0, 0, 0, 0])[1]
            )
            if row_height < LEGEND_ROW_MIN_HEIGHT_PT or row_height > LEGEND_ROW_MAX_HEIGHT_PT:
                continue
            rows.append({
                "symbol_bbox": [float(v) for v in sb],
                "text": txt.get("text", "").strip(),
                "text_bbox": [float(v) for v in txt.get("bbox", [0, 0, 0, 0])],
                "text_object_index": t_idx,
                "symbol_cy": sym_cy,
            })

        # Sort rows top-to-bottom.
        rows.sort(key=lambda r: r["symbol_cy"])

        # Check vertical stacking regularity — spacing ±25%.
        if len(rows) >= LEGEND_MIN_ROWS:
            spacings = [
                rows[k + 1]["symbol_cy"] - rows[k]["symbol_cy"]
                for k in range(len(rows) - 1)
            ]
            if spacings:
                mean_s = statistics.fmean(spacings)
                if mean_s > 0:
                    filtered_rows: List[Dict[str, Any]] = [rows[0]]
                    for k in range(1, len(rows)):
                        gap = rows[k]["symbol_cy"] - filtered_rows[-1]["symbol_cy"]
                        if abs(gap - mean_s) / mean_s <= LEGEND_ROW_SPACING_TOLERANCE:
                            filtered_rows.append(rows[k])
                        else:
                            # Stop growing the region on first irregular gap.
                            break
                    if len(filtered_rows) >= LEGEND_MIN_ROWS:
                        rows = filtered_rows
                    else:
                        rows = []

        entries: List[Dict[str, Any]] = []
        if len(rows) >= LEGEND_MIN_ROWS:
            for row_index, r in enumerate(rows):
                entries.append({
                    "symbol_bbox": r["symbol_bbox"],
                    "text": r["text"],
                    "text_bbox": r["text_bbox"],
                    "row_index": row_index,
                })

        # Compute the enclosing rect for the legend region.
        if entries:
            all_bboxes: List[Sequence[float]] = [anchor_bbox]
            for e in entries:
                all_bboxes.append(e["symbol_bbox"])
                all_bboxes.append(e["text_bbox"])
            region_bbox = _bbox_union(all_bboxes)
        else:
            # Anchor present but no rows fit — spec: warn and still emit
            # the anchor region for manual review.
            region_bbox = list(anchor_bbox)
            warnings.append(
                f"legend: anchor '{stripped}' at idx {anchor_idx} present but "
                "no rows matched the pattern"
            )

        legends.append({
            "bbox": [float(v) for v in region_bbox] if region_bbox else None,
            "anchor_keyword": stripped,
            "anchor_text_object_index": anchor_idx,
            "entries": entries,
        })

    return legends


# ---------------------------------------------------------------------------
# Geometry adapter — call sibling geometry module, reshape to the spec
# ---------------------------------------------------------------------------


def _drawings_from_page(page: "fitz.Page") -> List[Dict[str, Any]]:
    """Return raw ``page.get_drawings()`` output. See PyMuPDF documentation
    for the schema.  On failure, return an empty list and let downstream
    heuristics degrade to empty."""
    try:
        return list(page.get_drawings())
    except Exception as exc:  # pragma: no cover - PyMuPDF internal
        sys.stderr.write(f"extract.py: page.get_drawings() failed: {exc}\n")
        return []


def _individual_lines_from_drawings(
    drawings: Sequence[Dict[str, Any]],
    page_number: int,
) -> List[Dict[str, Any]]:
    """Enumerate individual ``"l"`` line-segment items across all paths.
    Used both for dimension heuristics and for the ``geometry.lines``
    field in the output JSON. This is *not* geometric reconstruction —
    it's a flat pass, so it does not overlap with the geometry module."""
    out: List[Dict[str, Any]] = []
    for path in drawings:
        if path.get("type") == "clip":
            continue
        items = path.get("items", []) or []
        for item in items:
            if not item or item[0] != "l":
                continue
            try:
                p0 = item[1]
                p1 = item[2]
                x0, y0 = float(p0[0]) if hasattr(p0, "__getitem__") else float(p0.x), (
                    float(p0[1]) if hasattr(p0, "__getitem__") else float(p0.y)
                )
                x1, y1 = float(p1[0]) if hasattr(p1, "__getitem__") else float(p1.x), (
                    float(p1[1]) if hasattr(p1, "__getitem__") else float(p1.y)
                )
            except Exception:
                continue
            dx = x1 - x0
            dy = y1 - y0
            length = math.hypot(dx, dy)
            if length <= 0:
                continue
            if abs(dy) < 0.5 and abs(dx) >= 0.5:
                orient = "h"
            elif abs(dx) < 0.5 and abs(dy) >= 0.5:
                orient = "v"
            else:
                orient = "d"  # diagonal / non-axis-aligned
            out.append({
                "p0": [x0, y0],
                "p1": [x1, y1],
                "orient": orient,
                "length_pt": length,
                "page": page_number,
            })
    return out


def _reshape_geometry_output(
    drawings: Sequence[Dict[str, Any]],
    page: "fitz.Page",
    page_number: int,
    warnings: List[str],
) -> Dict[str, Any]:
    """Delegate to ``geometry`` module for higher-level shape detection,
    then adapt to the JSON schema required by this file's spec."""

    lines_flat = _individual_lines_from_drawings(drawings, page_number)

    circles_out: List[Dict[str, Any]] = []
    polylines_out: List[Dict[str, Any]] = []
    closed_out: List[Dict[str, Any]] = []
    grid_out: Dict[str, Any] = {
        "horizontal": [],
        "vertical": [],
        "spacing_pt": {"h": None, "v": None},
    }

    # Circles.
    try:
        for c in geometry.find_circles(drawings):
            center = c.get("center", [0.0, 0.0])
            radius = float(c.get("radius", 0.0))
            bbox = c.get("bbox") or [
                center[0] - radius, center[1] - radius,
                center[0] + radius, center[1] + radius,
            ]
            circles_out.append({
                "center": [float(center[0]), float(center[1])],
                "radius_pt": radius,
                "bbox": [float(v) for v in bbox],
                "confidence": float(c.get("confidence", 0.0)),
                "page": page_number,
            })
    except Exception as exc:
        warnings.append(f"geometry.find_circles: {exc}")

    # Polylines and closed areas. geometry.find_polylines returns
    # polylines, and find_closed_areas returns only closed ones. To
    # avoid double-counting we ask for polylines, then split them by
    # their "closed" flag.
    try:
        polylines_raw = list(geometry.find_polylines(drawings))
    except Exception as exc:
        polylines_raw = []
        warnings.append(f"geometry.find_polylines: {exc}")

    try:
        closed_raw = list(geometry.find_closed_areas(drawings))
    except Exception as exc:
        closed_raw = []
        warnings.append(f"geometry.find_closed_areas: {exc}")

    # Emit closed areas from the dedicated closed-areas detector; drop
    # any polyline whose points match a closed area to avoid duplicates.
    closed_signatures: set = set()
    for a in closed_raw:
        pts = a.get("points", []) or []
        if len(pts) < 3:
            continue
        sig = tuple((round(p[0], 1), round(p[1], 1)) for p in pts[:6])
        closed_signatures.add(sig)
        bbox = a.get("bbox") or _bbox_union([
            [p[0], p[1], p[0], p[1]] for p in pts
        ])
        closed_out.append({
            "points": [[float(p[0]), float(p[1])] for p in pts],
            "area_pt2": float(a.get("area_pts2", a.get("area", 0.0))),
            "bbox": [float(v) for v in (bbox or [0, 0, 0, 0])],
            "page": page_number,
        })

    for pl in polylines_raw:
        pts = pl.get("points", []) or []
        if len(pts) < 2:
            continue
        sig = tuple((round(p[0], 1), round(p[1], 1)) for p in pts[:6])
        if pl.get("closed") and sig in closed_signatures:
            continue
        bbox = pl.get("bbox") or _bbox_union([
            [p[0], p[1], p[0], p[1]] for p in pts
        ])
        polylines_out.append({
            "points": [[float(p[0]), float(p[1])] for p in pts],
            "closed": bool(pl.get("closed", False)),
            "bbox": [float(v) for v in (bbox or [0, 0, 0, 0])],
            "page": page_number,
        })

    # Grid lines. geometry.find_grid_lines returns a single dict with
    # "vertical", "horizontal" arrays and the raw spacing lists;
    # reshape to h/v arrays with per-line bbox and a scalar spacing.
    try:
        page_rect = page.rect
        grid_raw = geometry.find_grid_lines(
            drawings,
            (float(page_rect.width), float(page_rect.height)),
        )
    except Exception as exc:
        grid_raw = None
        warnings.append(f"geometry.find_grid_lines: {exc}")

    if grid_raw:
        h_list: List[Dict[str, Any]] = []
        for h in grid_raw.get("horizontal", []) or []:
            y = float(h.get("y", 0.0))
            x0 = float(h.get("x0", 0.0))
            x1 = float(h.get("x1", 0.0))
            length = float(h.get("length", abs(x1 - x0)))
            h_list.append({
                "y": y,
                "length_pt": length,
                "bbox": [min(x0, x1), y - 0.5, max(x0, x1), y + 0.5],
            })
        v_list: List[Dict[str, Any]] = []
        for v in grid_raw.get("vertical", []) or []:
            x = float(v.get("x", 0.0))
            y0 = float(v.get("y0", 0.0))
            y1 = float(v.get("y1", 0.0))
            length = float(v.get("length", abs(y1 - y0)))
            v_list.append({
                "x": x,
                "length_pt": length,
                "bbox": [x - 0.5, min(y0, y1), x + 0.5, max(y0, y1)],
            })

        # Reduce spacing arrays to a single representative value —
        # median is robust to occasional missed grid lines.
        h_spacings = grid_raw.get("horizontal_spacing_pts") or []
        v_spacings = grid_raw.get("vertical_spacing_pts") or []
        h_scalar = float(statistics.median(h_spacings)) if h_spacings else None
        v_scalar = float(statistics.median(v_spacings)) if v_spacings else None

        grid_out = {
            "horizontal": h_list,
            "vertical": v_list,
            "spacing_pt": {"h": h_scalar, "v": v_scalar},
        }

    return {
        "lines": lines_flat,
        "circles": circles_out,
        "polylines": polylines_out,
        "closed_areas": closed_out,
        "grid_lines": grid_out,
    }


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_extraction(
    pdf_path: Path,
    page_number: int,
    profile: str,
) -> Dict[str, Any]:
    """Open the PDF, extract the requested page, and assemble the JSON blob.

    Sub-extractors are wrapped so a crash in one section does not lose
    the others. Warnings are collected on ``ailtir_metadata.warnings``.
    """
    warnings: List[str] = []

    # Compute the PDF SHA-256 once, up front — this is provenance metadata
    # (ISO 19650-1:2018 container concept: every downstream artefact must
    # be traceable to the exact byte stream it came from).
    sha256 = _sha256_of_file(pdf_path)

    with fitz.open(str(pdf_path)) as doc:
        page_count = doc.page_count
        if page_number < 1 or page_number > page_count:
            raise IndexError(
                f"--page {page_number} out of range (1..{page_count})"
            )
        page = doc[page_number - 1]

        page_rect = page.rect
        width_pt = float(page_rect.width)
        height_pt = float(page_rect.height)
        orientation = "landscape" if width_pt >= height_pt else "portrait"
        page_size_class = _classify_page_size(width_pt, height_pt)

        page_info = {
            "page_index": page_number - 1,
            "page_number": page_number,
            "page_width_pt": width_pt,
            "page_height_pt": height_pt,
            "orientation": orientation,
            "page_size_class": page_size_class,
            "rotation": int(getattr(page, "rotation", 0) or 0),
        }

        # Text objects.
        try:
            text_objects = extract_text_objects(page, page_number)
        except Exception as exc:
            warnings.append(f"text-extraction: {exc}")
            text_objects = []

        # Raw drawings + geometry reconstruction.
        drawings = _drawings_from_page(page)
        try:
            geometry_block = _reshape_geometry_output(
                drawings, page, page_number, warnings
            )
        except Exception as exc:
            warnings.append(f"geometry: {exc}")
            geometry_block = {
                "lines": [],
                "circles": [],
                "polylines": [],
                "closed_areas": [],
                "grid_lines": {
                    "horizontal": [],
                    "vertical": [],
                    "spacing_pt": {"h": None, "v": None},
                },
            }

        # Tags.
        try:
            tag_patterns = load_tag_patterns(warnings)
            tags = match_tags(text_objects, tag_patterns, page_number, warnings)
        except Exception as exc:
            warnings.append(f"tag-matching: {exc}")
            tags = []

        # Dimensions.
        try:
            d1 = extract_dimensions_unit_suffix(text_objects, page_number)
        except Exception as exc:
            warnings.append(f"dimensions unit-suffix: {exc}")
            d1 = []
        try:
            d2 = extract_dimensions_adjacent_to_line(
                text_objects, geometry_block, page_number
            )
        except Exception as exc:
            warnings.append(f"dimensions adjacent-to-line: {exc}")
            d2 = []
        try:
            d3 = extract_dimensions_between_arrows(
                text_objects, geometry_block, page_number
            )
        except Exception as exc:
            warnings.append(f"dimensions between-arrows: {exc}")
            d3 = []

        try:
            dimensions = deduplicate_dimensions(list(d1) + list(d2) + list(d3))
        except Exception as exc:
            warnings.append(f"dimensions dedup: {exc}")
            dimensions = list(d1) + list(d2) + list(d3)

        # Scale.
        allow_list = SCALE_ALLOW_LISTS.get(profile, SCALE_ALLOW_LISTS[DEFAULT_PROFILE])
        try:
            text_res = detect_scale_from_text(
                text_objects, width_pt, height_pt, allow_list, warnings
            )
        except Exception as exc:
            warnings.append(f"scale-text: {exc}")
            text_res = {"scale": None, "bbox": None, "notes": None}
        try:
            grid_res = detect_scale_from_grid(geometry_block, allow_list, warnings)
        except Exception as exc:
            warnings.append(f"scale-grid: {exc}")
            grid_res = {"scale": None, "evidence": None, "notes": None}
        try:
            bar_res = detect_scale_from_bar(
                text_objects, geometry_block, width_pt, height_pt,
                allow_list, warnings,
            )
        except Exception as exc:
            warnings.append(f"scale-bar: {exc}")
            bar_res = {"scale": None, "bbox": None, "notes": None}

        try:
            scale = cross_validate_scale(text_res, grid_res, bar_res, warnings)
        except Exception as exc:
            warnings.append(f"scale cross-validate: {exc}")
            scale = {
                "text_scale": None, "text_scale_bbox": None,
                "grid_scale": None, "grid_evidence": None,
                "scale_bar_scale": None, "scale_bar_bbox": None,
                "reported_scale": None, "confidence": "low",
                "methods_agreeing": [], "notes": str(exc),
            }

        # Legends.
        try:
            legends = detect_legends(text_objects, geometry_block, warnings)
        except Exception as exc:
            warnings.append(f"legend: {exc}")
            legends = []

    metadata = {
        "source_pdf": str(pdf_path.resolve()),
        "source_pdf_sha256": sha256,
        "source_page": page_number,
        "extracted_at": _now_iso_utc(),
        "extractor_version": EXTRACTOR_VERSION,
        "profile": profile,
        "warnings": warnings,
    }

    return {
        "ailtir_metadata": metadata,
        "page_info": page_info,
        "text_objects": text_objects,
        "tags": tags,
        "dimensions": dimensions,
        "scale": scale,
        "legend": legends,
        "geometry": geometry_block,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="extract.py",
        description=(
            "Ailtir takeoff: extract structured signals (text, tags, "
            "dimensions, scale, legends, geometry) from a single-page "
            "construction drawing PDF."
        ),
    )
    p.add_argument("pdf_path", help="Path to the input PDF.")
    p.add_argument(
        "-o", "--output",
        help="Write JSON to this path (default: stdout).",
    )
    p.add_argument(
        "--page", type=int, default=1,
        help="1-indexed page number to extract (default: 1).",
    )
    p.add_argument(
        "--pretty", action="store_true",
        help="Pretty-print JSON (indent=2, sorted keys).",
    )
    p.add_argument(
        "--profile", choices=sorted(SCALE_ALLOW_LISTS.keys()),
        default=None,
        help=(
            "Ailtir profile controlling the scale-denominator allow-list. "
            "Falls back to $AILTIR_PROFILE, then 'ireland-gc'."
        ),
    )
    p.add_argument(
        "--dry-run", action="store_true",
        help=(
            "Print per-section counts and the first three entries of each "
            "section instead of the full JSON."
        ),
    )
    return p


def _dry_run_dump(payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    meta = payload.get("ailtir_metadata", {})
    lines.append(f"source_pdf: {meta.get('source_pdf')}")
    lines.append(f"source_pdf_sha256: {meta.get('source_pdf_sha256')}")
    lines.append(f"source_page: {meta.get('source_page')}")
    lines.append(f"profile: {meta.get('profile')}")
    lines.append(f"warnings: {len(meta.get('warnings', []))}")
    for section in ("text_objects", "tags", "dimensions", "legend"):
        items = payload.get(section, [])
        lines.append(f"\n== {section} (count={len(items)}) ==")
        for entry in items[:3]:
            lines.append(json.dumps(entry, default=str)[:400])
    scale = payload.get("scale", {})
    lines.append(f"\n== scale ==")
    lines.append(json.dumps(scale, default=str)[:600])
    geom = payload.get("geometry", {})
    lines.append(
        "\n== geometry (counts) ==\n"
        f"lines={len(geom.get('lines', []))}, "
        f"circles={len(geom.get('circles', []))}, "
        f"polylines={len(geom.get('polylines', []))}, "
        f"closed_areas={len(geom.get('closed_areas', []))}, "
        f"grid.h={len(geom.get('grid_lines', {}).get('horizontal', []))}, "
        f"grid.v={len(geom.get('grid_lines', {}).get('vertical', []))}"
    )
    sys.stdout.write("\n".join(lines) + "\n")


def _write_output(payload: Dict[str, Any], out_path: Optional[str], pretty: bool) -> None:
    if pretty:
        text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    else:
        text = json.dumps(payload, separators=(",", ":"), default=str)
    if out_path is None:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    out = Path(out_path)
    if out.exists() and out.is_dir():
        raise IsADirectoryError(f"--output path is a directory: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists() or not pdf_path.is_file():
        sys.stderr.write(f"extract.py: PDF not found or unreadable: {pdf_path}\n")
        return 2

    # Basic sniff for PDF magic — cheap way to reject non-PDF inputs before
    # PyMuPDF's own error paths.
    try:
        with open(pdf_path, "rb") as fh:
            magic = fh.read(5)
        if not magic.startswith(b"%PDF-"):
            sys.stderr.write(f"extract.py: not a PDF (missing %PDF- header): {pdf_path}\n")
            return 2
    except OSError as exc:
        sys.stderr.write(f"extract.py: cannot read PDF: {exc}\n")
        return 2

    profile = _resolve_profile(args.profile)

    try:
        payload = run_extraction(pdf_path, args.page, profile)
    except IndexError as exc:
        sys.stderr.write(f"extract.py: {exc}\n")
        return 4
    except fitz.FileDataError as exc:  # type: ignore[attr-defined]
        sys.stderr.write(f"extract.py: invalid PDF: {exc}\n")
        return 2
    except Exception as exc:
        sys.stderr.write(
            f"extract.py: internal extraction failure: {exc}\n"
            + traceback.format_exc()
        )
        return 5

    if args.dry_run:
        _dry_run_dump(payload)
        return 0

    try:
        _write_output(payload, args.output, args.pretty)
    except IsADirectoryError as exc:
        sys.stderr.write(f"extract.py: {exc}\n")
        return 3
    except OSError as exc:
        sys.stderr.write(f"extract.py: cannot write output: {exc}\n")
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
