#!/usr/bin/env python3
"""
PDF Splitter & Per-Page Extractor for Construction Drawings (v2)

Splits a multi-page PDF into individual page PDFs and images,
then runs enhanced vector extraction (with geometry analysis) on each page.

Working files (per-page PDFs, PNGs, extraction JSONs) go into a _working/
subdirectory. The output directory itself only contains deliverables:
  - manifest.json (the extraction summary)
  - contact_sheet.jpg (thumbnail grid)

Usage:
    python split_and_extract.py drawing.pdf -o output_dir
    python split_and_extract.py drawing.pdf -o output_dir --dpi 200
    python split_and_extract.py drawing.pdf -o output_dir --pages 1,3,5
    python split_and_extract.py drawing.pdf -o output_dir --trade electrical
"""

import sys
import json
import os
import argparse
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    Image = None

# Import the extraction module
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))
from extract import extract_page


def generate_contact_sheet(doc, output_path, max_pages=50, thumb_size=200, cols=5):
    """Generate a thumbnail grid of all pages for quick visual scanning.

    Produces a single JPEG with all pages laid out in a grid, so the AI can
    quickly identify drawing types, schedules, legends, and blank pages
    before doing any extraction.
    """
    if Image is None:
        print("WARNING: Pillow not installed — skipping contact sheet. Install with: pip install Pillow", file=sys.stderr)
        return None

    page_count = min(len(doc), max_pages)
    images = []

    for page_num in range(page_count):
        page = doc.load_page(page_num)
        mat = fitz.Matrix(0.2, 0.2)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((thumb_size, thumb_size))
        images.append(img)

    rows = (page_count + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb_size, rows * thumb_size), "white")

    for idx, img in enumerate(images):
        x = (idx % cols) * thumb_size
        y = (idx // cols) * thumb_size
        sheet.paste(img, (x, y))

    sheet.save(output_path, "JPEG", quality=85)
    print(f"  Contact sheet: {output_path} ({page_count} pages, {cols}x{rows} grid)", file=sys.stderr)
    return output_path


def split_pdf(
    pdf_path: str,
    output_dir: str,
    dpi: int = 150,
    pages: list = None,
    render_images: bool = True,
    trade_filter: str = None,
) -> dict:
    """
    Split a multi-page PDF into individual pages with extraction.

    Working files (per-page PDFs, PNGs, extraction JSONs) are written to
    output_dir/_working/. The output directory itself only gets deliverables:
    manifest.json and the contact sheet.

    Args:
        pdf_path: Path to source PDF
        output_dir: Directory for deliverables (manifest, contact sheet)
        dpi: Resolution for rendered page images (default 150)
        pages: Optional list of 1-based page numbers to process
        render_images: Whether to render PNG images
        trade_filter: Optional trade name to filter results (e.g., "electrical")

    Returns:
        Manifest dict with metadata and per-page file paths
    """
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    source_name = Path(pdf_path).stem

    os.makedirs(output_dir, exist_ok=True)
    working_dir = os.path.join(output_dir, "_working")
    os.makedirs(working_dir, exist_ok=True)

    # Determine which pages to process
    if pages:
        page_indices = [p - 1 for p in pages if 0 < p <= total_pages]
    else:
        page_indices = list(range(total_pages))

    # Generate contact sheet thumbnail grid (deliverable — goes in output_dir)
    contact_sheet_path = os.path.join(output_dir, f"{source_name}_contact_sheet.jpg")
    generate_contact_sheet(doc, contact_sheet_path)

    manifest = {
        "source_file": Path(pdf_path).name,
        "total_pages": total_pages,
        "pages_processed": len(page_indices),
        "output_dir": str(output_dir),
        "working_dir": str(working_dir),
        "dpi": dpi,
        "trade_filter": trade_filter,
        "contact_sheet": contact_sheet_path,
        "legends": [],  # Collected from all pages for cross-reference
        "pages": [],
    }

    for idx in page_indices:
        page_num = idx + 1
        page = doc[idx]
        page_info = {
            "page_number": page_num,
            "files": {},
        }

        # --- 1. Single-page PDF (working file) ---
        single_pdf_path = os.path.join(working_dir, f"{source_name}_page{page_num}.pdf")
        single_doc = fitz.open()
        single_doc.insert_pdf(doc, from_page=idx, to_page=idx)
        single_doc.save(single_pdf_path)
        single_doc.close()
        page_info["files"]["pdf"] = single_pdf_path

        # --- 2. Page image (working file) ---
        if render_images:
            img_path = os.path.join(working_dir, f"{source_name}_page{page_num}.png")
            zoom = dpi / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            pix.save(img_path)
            page_info["files"]["image"] = img_path
            page_info["image_size"] = {
                "width": pix.width,
                "height": pix.height,
            }

        # --- 3. Vector extraction (working file) ---
        extraction = extract_page(page, page_num)
        json_path = os.path.join(working_dir, f"{source_name}_page{page_num}_extraction.json")
        with open(json_path, "w") as f:
            json.dump(extraction, f, indent=2)
        page_info["files"]["extraction_json"] = json_path

        # Include key summary info in manifest
        page_info["scale"] = extraction.get("scale", {})
        page_info["title_block"] = extraction.get("title_block", {})
        page_info["tag_counts"] = extraction.get("tag_counts", {})
        page_info["stats"] = extraction.get("raw_stats", {})
        page_info["legend"] = extraction.get("legend", {})

        # Geometry summary
        geometry = extraction.get("geometry")
        if geometry:
            page_info["geometry_summary"] = geometry.get("summary", {})

        # Flag rasterised/scanned pages — 0 text objects means vector extraction
        # can't help. These pages require AI vision for all extraction.
        text_count = page_info["stats"].get("text_objects", 0)
        paths_count = extraction.get("paths_summary", {}).get("total_paths", 0)
        if text_count == 0 and paths_count == 0:
            page_info["rasterised"] = True
            page_info["note"] = "Rasterised/scanned page — no vector data. Requires AI vision for extraction."
        elif text_count == 0 and paths_count > 0:
            page_info["rasterised"] = False
            page_info["note"] = "Vector paths present but no text — drawing may use embedded fonts or symbols only."

        # Collect legends for cross-page reference
        legend = extraction.get("legend", {})
        if legend.get("detected"):
            manifest["legends"].append({
                "page": page_num,
                "texts": legend.get("texts", []),
            })

        # Apply trade filter if specified
        if trade_filter:
            filtered_tags = {
                tag: data for tag, data in page_info["tag_counts"].items()
                if data.get("category", "").lower() == trade_filter.lower()
            }
            page_info["filtered_tag_counts"] = filtered_tags
            page_info["trade_filter_applied"] = trade_filter

        manifest["pages"].append(page_info)

        # Progress output
        tag_count = len(page_info["tag_counts"])
        geo_circles = page_info.get("geometry_summary", {}).get("circles_found", 0)
        geo_areas = page_info.get("geometry_summary", {}).get("closed_areas_found", 0)
        print(
            f"  Page {page_num}/{total_pages}: "
            f"{page_info['stats'].get('text_objects', 0)} text objects, "
            f"{tag_count} tag types, "
            f"{geo_circles} circles, "
            f"{geo_areas} areas",
            file=sys.stderr,
        )

    doc.close()

    # Write manifest (deliverable — goes in output_dir)
    manifest_path = os.path.join(output_dir, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    manifest["manifest_path"] = manifest_path

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Split construction PDF into individual pages for reliable analysis (v2)"
    )
    parser.add_argument("pdf_path", help="Path to multi-page PDF")
    parser.add_argument("-o", "--output-dir", required=True, help="Output directory")
    parser.add_argument("--dpi", type=int, default=150,
                        help="Image resolution (default 150, use 200+ for detailed drawings)")
    parser.add_argument("--pages", type=str, default=None,
                        help="Comma-separated page numbers to process (default: all)")
    parser.add_argument("--no-images", action="store_true",
                        help="Skip PNG image rendering (vector extraction only)")
    parser.add_argument("--trade", type=str, default=None,
                        help="Filter results by trade (electrical, plumbing, structural, etc.)")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"ERROR: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    pages = None
    if args.pages:
        pages = [int(p.strip()) for p in args.pages.split(",")]

    print(f"Splitting: {args.pdf_path}", file=sys.stderr)
    manifest = split_pdf(
        args.pdf_path,
        args.output_dir,
        dpi=args.dpi,
        pages=pages,
        render_images=not args.no_images,
        trade_filter=args.trade,
    )

    print(f"\nDone. Processed {manifest['pages_processed']} pages.", file=sys.stderr)
    if manifest["legends"]:
        print(f"Legends found on {len(manifest['legends'])} page(s).", file=sys.stderr)
    print(f"Manifest: {manifest['manifest_path']}", file=sys.stderr)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
