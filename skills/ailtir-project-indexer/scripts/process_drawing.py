#!/usr/bin/env python3
"""
Process a single drawing PDF for project-indexer.

For every page of the input PDF, produces three artefacts in the output dir:
  1. A single-sheet PDF (durable — saved alongside the project for later use)
  2. A high-DPI PNG render of the page (for vision analysis)
  3. A JSON file with extracted text, title-block hints, and vector stats

The split single-sheet PDFs are the persisted output. The PNGs and JSON are
inputs to the per-sheet analysis step and can be discarded after drawings.md
is written if disk space matters.

Usage:
    # Persisted split (one PDF per sheet) + render + extract:
    python process_drawing.py drawing.pdf -o "<project>/0. AI Context/drawings_split/<source_stem>" --dpi 200
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install pymupdf --break-system-packages", file=sys.stderr)
    sys.exit(1)


def extract_page_info(page) -> dict:
    """Light vector extraction — enough to populate a drawing description."""
    info = {
        "page_number": page.number + 1,
        "width_pts": round(page.rect.width, 1),
        "height_pts": round(page.rect.height, 1),
        "text_blocks": [],
        "title_block_candidates": [],
        "all_text": "",
    }

    # Collect text blocks with positions
    try:
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])
    except Exception:
        blocks = []

    all_text_parts = []
    page_w = page.rect.width
    page_h = page.rect.height

    for block in blocks:
        if block.get("type") != 0:  # 0 = text
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                bbox = span.get("bbox", [0, 0, 0, 0])
                all_text_parts.append(text)

                # Title blocks are typically bottom-right or right edge
                x_frac = (bbox[0] / page_w) if page_w else 0
                y_frac = (bbox[1] / page_h) if page_h else 0
                in_title_zone = (x_frac > 0.65) and (y_frac > 0.55)

                entry = {
                    "text": text,
                    "size": round(span.get("size", 0), 1),
                    "bbox": [round(b, 1) for b in bbox],
                    "in_title_zone": in_title_zone,
                }
                info["text_blocks"].append(entry)
                if in_title_zone:
                    info["title_block_candidates"].append(entry)

    info["all_text"] = "\n".join(all_text_parts)

    # Count vector drawings as a sanity check
    try:
        info["vector_drawing_count"] = len(page.get_drawings())
    except Exception:
        info["vector_drawing_count"] = None

    return info


def process(pdf_path: str, output_dir: str, dpi: int = 200) -> dict:
    doc = fitz.open(pdf_path)
    os.makedirs(output_dir, exist_ok=True)
    source_name = Path(pdf_path).stem

    manifest = {
        "source_file": Path(pdf_path).name,
        "source_path": str(pdf_path),
        "total_pages": len(doc),
        "dpi": dpi,
        "output_dir": output_dir,
        "sheets": [],
    }

    try:
        for idx in range(len(doc)):
            page = doc[idx]
            sheet_num = idx + 1
            stem = f"{source_name}_sheet{sheet_num}"

            # Persisted single-sheet PDF (durable artefact)
            pdf_out_path = os.path.join(output_dir, f"{stem}.pdf")
            single = fitz.open()
            single.insert_pdf(doc, from_page=idx, to_page=idx)
            single.save(pdf_out_path)
            single.close()

            # Render high-DPI image for vision analysis
            img_path = os.path.join(output_dir, f"{stem}.png")
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            pix.save(img_path)

            # Extract vector/text info
            page_info = extract_page_info(page)
            json_path = os.path.join(output_dir, f"{stem}.json")
            with open(json_path, "w") as f:
                json.dump(page_info, f, indent=2)

            manifest["sheets"].append({
                "sheet_number": sheet_num,
                "pdf_path": pdf_out_path,
                "image_path": img_path,
                "image_size": {"width": pix.width, "height": pix.height},
                "extraction_path": json_path,
                "title_block_candidates": page_info["title_block_candidates"][:20],
                "text_sample": page_info["all_text"][:500],
            })
    finally:
        doc.close()

    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest


def main():
    ap = argparse.ArgumentParser(description="Split a drawing PDF into per-sheet PDFs + per-sheet PNG + per-sheet JSON for analysis.")
    ap.add_argument("pdf_path")
    ap.add_argument("-o", "--output-dir", required=True)
    ap.add_argument("--dpi", type=int, default=200)
    args = ap.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"ERROR: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    manifest = process(args.pdf_path, args.output_dir, args.dpi)
    print(f"Split {manifest['total_pages']} sheets from {manifest['source_file']} -> {args.output_dir}", file=sys.stderr)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
