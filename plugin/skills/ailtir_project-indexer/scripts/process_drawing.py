"""Split a multi-page drawing PDF into per-sheet artefacts.

For each page of the input PDF this produces a single-sheet PDF (vector,
via PyMuPDF ``Document.select``), a high-DPI PNG render (via
``page.get_pixmap``), and a JSON blob of extracted text plus ISO 19650
title-block hints. A ``manifest.json`` summarises the run.

Refs:
    - PyMuPDF: Document.select, page.get_pixmap, page.get_text("dict").
    - ISO 19650 status (S0-S7, A/B) and revision (P/C) codes:
      research/drawing-conventions.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

# --- Regex library -----------------------------------------------------------
# All patterns are best-effort. Downstream vision analysis validates them.
SHEET_NUMBER_RE = re.compile(r"\b([A-Z]{1,3}[-_]?\d{2,4}(?:[-_]?\d{2,4})?)\b")
SCALE_RE = re.compile(r"\b(1\s*[:/]\s*\d{1,4}|NTS)\b", re.IGNORECASE)
# ISO 19650 revision: P01, C02, P01.02
REV_ISO_RE = re.compile(r"\b([PC]\d{2}(?:\.\d{2})?)\b")
REV_LEGACY_RE = re.compile(r"\bRev(?:ision)?\s*[:.\-]?\s*([A-Z0-9]{1,3})\b", re.IGNORECASE)
DATE_RE = re.compile(
    r"\b("
    r"\d{4}-\d{2}-\d{2}"
    r"|\d{2}[/-]\d{2}[/-]\d{2,4}"
    r"|\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{2,4}"
    r")\b",
    re.IGNORECASE,
)
STATUS_RE = re.compile(r"\b(S[0-7]|A\d{1,2}|B\d{1,2}|CR)\b")
DRAWING_SIZE_RE = re.compile(r"\b(A[0-4])\b")

TITLE_ANCHORS = (
    "SCALE", "REVISION", "REV", "DATE", "DRAWN", "CHECKED", "APPROVED",
    "SHEET", "DRAWING NO", "PROJECT", "TITLE", "STATUS", "SUITABILITY", "SIZE",
)

# Cross-reference patterns.
XREF_PATTERNS = [
    ("sheet", re.compile(r"(?:See|Refer(?:\s+to)?)\s+(?:Sheet\s+)?([A-Z]-?\d{2,4})", re.IGNORECASE)),
    ("sheet", re.compile(r"\bSheet\s+([A-Z]-?\d{2,4})\b", re.IGNORECASE)),
    ("spec",  re.compile(r"\bSpec(?:ification)?\s+(\d{2}\s?\d{2}\s?\d{2,4})", re.IGNORECASE)),
    ("spec",  re.compile(r"\bSection\s+(\d{2}\s?\d{2}\s?\d{2,4})", re.IGNORECASE)),
    ("rfi",   re.compile(r"\bRFI\s?[-#]?\s?(\d{1,5})\b", re.IGNORECASE)),
    ("revcloud", re.compile(r"\b(RC-\d{1,3}|revision cloud|NCR-\d{1,4})\b", re.IGNORECASE)),
]


def classify_page_size(width_pt: float, height_pt: float) -> tuple[str, str]:
    """Map (w, h) in PDF points to ISO A-series size + orientation.

    Uses long-edge classification, tolerant of ~5% rotation/margin drift.
    """
    long_edge = max(width_pt, height_pt)
    orientation = "landscape" if width_pt >= height_pt else "portrait"
    # A-series long edges (mm): A4=297, A3=420, A2=594, A1=841, A0=1189.
    for name, mm in (("A0", 1189), ("A1", 841), ("A2", 594), ("A3", 420), ("A4", 297)):
        pt = mm * 72.0 / 25.4
        if long_edge >= pt * 0.95:
            return name, orientation
    return "sub-A4", orientation


def extract_text_blocks(page: fitz.Page) -> list[dict[str, Any]]:
    """Collapse ``get_text('dict')`` into flat ``{bbox, text}`` entries."""
    out: list[dict[str, Any]] = []
    try:
        raw = page.get_text("dict")
    except Exception as exc:  # pragma: no cover
        print(f"[warn] text extraction failed on page {page.number + 1}: {exc}", file=sys.stderr)
        return out
    for block in raw.get("blocks", []):
        if block.get("type") != 0:  # skip images
            continue
        lines: list[str] = []
        for line in block.get("lines", []):
            spans = [s.get("text", "") for s in line.get("spans", [])]
            joined = "".join(spans).strip()
            if joined:
                lines.append(joined)
        if lines:
            out.append({"bbox": list(block.get("bbox", (0, 0, 0, 0))), "text": "\n".join(lines)})
    return out


def _region_hits(blocks: list[dict[str, Any]], region: tuple[float, float, float, float]) -> list[dict[str, Any]]:
    x0, y0, x1, y1 = region
    hits = []
    for b in blocks:
        bx0, by0, bx1, by1 = b["bbox"]
        # accept if the block's centre falls inside the region
        cx, cy = (bx0 + bx1) / 2, (by0 + by1) / 2
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            hits.append(b)
    return hits


def detect_title_block(
    blocks: list[dict[str, Any]], width: float, height: float
) -> tuple[bool, list[float] | None, str]:
    """Two-region heuristic: right 25% strip or bottom 20% strip.

    Prefer the right strip when both regions carry >=3 anchor keywords.
    Returns (detected, region_bbox, joined_text).
    """
    right = (width * 0.75, 0.0, width, height)
    bottom = (0.0, height * 0.80, width, height)

    def score(region: tuple[float, float, float, float]) -> tuple[int, str]:
        text = "\n".join(b["text"] for b in _region_hits(blocks, region))
        upper = text.upper()
        anchors = sum(1 for kw in TITLE_ANCHORS if kw in upper)
        return anchors, text

    right_anchors, right_text = score(right)
    bottom_anchors, bottom_text = score(bottom)

    if right_anchors >= 3:
        return True, list(right), right_text
    if bottom_anchors >= 3:
        return True, list(bottom), bottom_text
    return False, None, ""


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def extract_title_hints(tb_text: str, page_size_class: str) -> dict[str, str]:
    """Pull ISO 19650 status/revision + free-text hints from title-block text."""
    hints: dict[str, str] = {}
    sheet = _first(SHEET_NUMBER_RE, tb_text)
    if sheet:
        hints["sheet_number"] = sheet
    scale = _first(SCALE_RE, tb_text)
    if scale:
        hints["scale"] = re.sub(r"\s+", "", scale).upper() if scale.upper() == "NTS" else re.sub(r"\s*[/]\s*", ":", scale).replace(" ", "")
    rev = _first(REV_ISO_RE, tb_text) or _first(REV_LEGACY_RE, tb_text)
    if rev:
        hints["revision"] = rev
    date = _first(DATE_RE, tb_text)
    if date:
        hints["date"] = date
    status = _first(STATUS_RE, tb_text)
    if status:
        hints["status"] = status
    size = _first(DRAWING_SIZE_RE, tb_text) or (page_size_class if page_size_class.startswith("A") else None)
    if size:
        hints["drawing_size"] = size
    # Sheet title heuristic: first CAPS line following a "TITLE" anchor.
    m = re.search(r"TITLE[^\n]*\n\s*([A-Z0-9 ,.\-/&]{4,})", tb_text, re.IGNORECASE)
    if m:
        hints["sheet_title"] = m.group(1).strip()
    m = re.search(r"PROJECT[^\n]*\n\s*([A-Za-z0-9 ,.\-/&]{4,})", tb_text, re.IGNORECASE)
    if m:
        hints["project_name"] = m.group(1).strip()
    return hints


def extract_cross_references(full_text: str) -> list[dict[str, str]]:
    """Pull sheet / spec / RFI / revision-cloud references with 40-char context."""
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for kind, pat in XREF_PATTERNS:
        for m in pat.finditer(full_text):
            value = m.group(1).strip()
            key = (kind, value.upper())
            if key in seen:
                continue
            seen.add(key)
            start = max(0, m.start() - 20)
            end = min(len(full_text), m.end() + 20)
            context = re.sub(r"\s+", " ", full_text[start:end]).strip()[:40]
            out.append({"kind": kind, "value": value, "context": context})
    return out


def _sheet_stem(stem: str, page_idx: int, total: int) -> str:
    width = max(2, len(str(total)))
    return f"{stem}_sheet{page_idx:0{width}d}"


def process_sheet(
    doc: fitz.Document, source_pdf: Path, page_num: int, total: int,
    out_dir: Path, dpi: int, overwrite: bool, dry_run: bool,
) -> tuple[dict[str, Any], bool]:
    """Return (manifest_entry, skipped_existing)."""
    page = doc.load_page(page_num - 1)
    base = _sheet_stem(source_pdf.stem, page_num, total)
    pdf_path = out_dir / f"{base}.pdf"
    png_path = out_dir / f"{base}.png"
    json_path = out_dir / f"{base}.json"

    blocks = extract_text_blocks(page)
    width, height = page.rect.width, page.rect.height
    size_class, orientation = classify_page_size(width, height)
    detected, region, tb_text = detect_title_block(blocks, width, height)
    hints = extract_title_hints(tb_text, size_class) if detected else {}
    full_text = "\n".join(b["text"] for b in blocks)
    xrefs = extract_cross_references(full_text)

    if dry_run:
        anchors = sum(1 for kw in TITLE_ANCHORS if kw in tb_text.upper())
        print(f"  page {page_num}: {size_class} {orientation} "
              f"({width:.0f}x{height:.0f}pt) title_anchors={anchors} hints={len(hints)} xrefs={len(xrefs)}")
        return {"page": page_num, "sheet_pdf": pdf_path.name, "sheet_png": png_path.name,
                "sheet_json": json_path.name, "sheet_number_hint": hints.get("sheet_number", "")}, False

    skipped = False
    if pdf_path.exists() and not overwrite:
        skipped = True
    else:
        try:
            single = fitz.open()
            single.insert_pdf(doc, from_page=page_num - 1, to_page=page_num - 1)
            single.save(pdf_path, deflate=True, garbage=3)
            single.close()
        except Exception as exc:
            print(f"[warn] single-sheet PDF failed for page {page_num}: {exc}", file=sys.stderr)

    try:
        pix = page.get_pixmap(dpi=dpi)
        pix.save(png_path)
    except Exception as exc:
        print(f"[warn] PNG render failed for page {page_num}: {exc}", file=sys.stderr)

    sheet_record = {
        "source_pdf": str(source_pdf), "source_page": page_num,
        "sheet_pdf": pdf_path.name, "sheet_png": png_path.name, "dpi": dpi,
        "page_width_pt": round(width, 2), "page_height_pt": round(height, 2),
        "page_size_class": size_class, "orientation": orientation,
        "text_blocks": blocks,
        "title_block": {"detected": detected, "region": region, "hints": hints},
        "cross_references": xrefs,
    }
    try:
        json_path.write_text(json.dumps(sheet_record, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[warn] JSON write failed for page {page_num}: {exc}", file=sys.stderr)

    return ({"page": page_num, "sheet_pdf": pdf_path.name, "sheet_png": png_path.name,
             "sheet_json": json_path.name, "sheet_number_hint": hints.get("sheet_number", "")}, skipped)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Split a drawing PDF into per-sheet artefacts.")
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--dpi", type=int, default=200)
    parser.add_argument("--start-page", type=int, default=None)
    parser.add_argument("--end-page", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if not (72 <= args.dpi <= 600):
        print("error: --dpi must be between 72 and 600", file=sys.stderr)
        return 4
    if not args.input_pdf.is_file():
        print(f"error: input PDF not found: {args.input_pdf}", file=sys.stderr)
        return 2

    try:
        doc = fitz.open(args.input_pdf)
    except Exception as exc:
        print(f"error: cannot open PDF ({exc})", file=sys.stderr)
        return 2

    total = doc.page_count
    start = args.start_page or 1
    end = args.end_page or total
    if not (1 <= start <= end <= total):
        print(f"error: page range {start}-{end} invalid for {total}-page PDF", file=sys.stderr)
        doc.close()
        return 4

    if not args.dry_run:
        try:
            args.output.mkdir(parents=True, exist_ok=True)
            probe = args.output / ".write_probe"
            probe.write_text("ok"); probe.unlink()
        except Exception as exc:
            print(f"error: output dir not writable ({exc})", file=sys.stderr)
            doc.close()
            return 3

    sheets: list[dict[str, Any]] = []
    skipped_count = 0
    for page_num in range(start, end + 1):
        try:
            entry, skipped = process_sheet(doc, args.input_pdf, page_num, total,
                                           args.output, args.dpi, args.overwrite, args.dry_run)
            sheets.append(entry)
            if skipped:
                skipped_count += 1
        except Exception as exc:  # never fatal — spec differentiator #3
            print(f"[warn] page {page_num} raised {type(exc).__name__}: {exc}", file=sys.stderr)

    if not args.dry_run:
        manifest = {
            "source_pdf": str(args.input_pdf),
            "output_dir": str(args.output.resolve()),
            "dpi": args.dpi,
            "processed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source_page_count": total,
            "sheets_produced": len(sheets),
            "skipped_existing": skipped_count,
            "sheets": sheets,
        }
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    doc.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
