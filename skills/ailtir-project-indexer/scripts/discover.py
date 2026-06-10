#!/usr/bin/env python3
"""
Project folder discovery — walks a construction project folder and produces
a JSON inventory of every file, grouped by folder, with quick PDF stats
used downstream by classify.py to split drawings from documents.

Usage:
    python discover.py "/path/to/project" -o /tmp/inventory.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except ImportError:
    HAVE_FITZ = False


DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".xlsm", ".csv", ".txt", ".md",
    ".rtf", ".odt", ".ppt", ".pptx",
}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
CAD_EXTENSIONS = {".dwg", ".dxf", ".rvt", ".ifc", ".skp", ".nwd", ".nwc", ".nwf"}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".rar", ".tar", ".gz"}


def pdf_quick_stats(pdf_path: str) -> dict:
    """
    Fast per-PDF stats used by the classifier. Opens only the first few
    pages for speed; full analysis happens later for confirmed drawings.
    """
    if not HAVE_FITZ:
        return {"error": "pymupdf_not_installed"}

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return {"error": f"open_failed: {e}"}

    try:
        total_pages = len(doc)
        # Sample up to 3 pages to keep this fast
        sample_count = min(3, total_pages)
        widths, heights, text_chars, drawings_counts = [], [], [], []
        for i in range(sample_count):
            page = doc[i]
            rect = page.rect
            widths.append(rect.width)
            heights.append(rect.height)
            text_chars.append(len(page.get_text("text")))
            try:
                drawings_counts.append(len(page.get_drawings()))
            except Exception:
                drawings_counts.append(0)

        avg_w = sum(widths) / len(widths) if widths else 0
        avg_h = sum(heights) / len(heights) if heights else 0
        aspect = (avg_w / avg_h) if avg_h else 0
        orientation = "landscape" if aspect > 1.1 else ("portrait" if aspect < 0.9 else "square")

        return {
            "total_pages": total_pages,
            "sampled_pages": sample_count,
            "avg_width_pts": round(avg_w, 1),
            "avg_height_pts": round(avg_h, 1),
            "aspect_ratio": round(aspect, 2),
            "orientation": orientation,
            "avg_text_chars_per_page": round(sum(text_chars) / sample_count) if sample_count else 0,
            "avg_vector_drawings_per_page": round(sum(drawings_counts) / sample_count) if sample_count else 0,
        }
    finally:
        doc.close()


def categorise_extension(ext: str) -> str:
    ext = ext.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in DOCUMENT_EXTENSIONS:
        return "document"
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in CAD_EXTENSIONS:
        return "cad"
    if ext in ARCHIVE_EXTENSIONS:
        return "archive"
    return "other"


def walk_project(root: str) -> dict:
    root_path = Path(root).resolve()
    if not root_path.exists():
        raise FileNotFoundError(root)

    inventory = {
        "project_root": str(root_path),
        "project_name_guess": root_path.name,
        "folders": {},
        "files": [],
        "counts": {"total": 0, "pdf": 0, "document": 0, "image": 0, "cad": 0, "archive": 0, "other": 0},
    }

    for dirpath, dirnames, filenames in os.walk(root_path):
        # Skip hidden folders and the output folder itself to avoid self-indexing loops
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d.lower() != "ai context"
                       and not (d[:3].strip(" .").isdigit() and "ai context" in d.lower())]

        rel_folder = os.path.relpath(dirpath, root_path)
        if rel_folder == ".":
            rel_folder = ""

        folder_entry = inventory["folders"].setdefault(rel_folder, {
            "relative_path": rel_folder,
            "file_count": 0,
            "file_types": {},
        })

        for fname in filenames:
            if fname.startswith("."):
                continue
            fpath = os.path.join(dirpath, fname)
            ext = os.path.splitext(fname)[1].lower()
            category = categorise_extension(ext)

            try:
                size = os.path.getsize(fpath)
            except OSError:
                size = None

            file_entry = {
                "name": fname,
                "relative_path": os.path.relpath(fpath, root_path),
                "folder": rel_folder,
                "extension": ext,
                "category": category,
                "size_bytes": size,
            }

            if category == "pdf":
                file_entry["pdf_stats"] = pdf_quick_stats(fpath)

            inventory["files"].append(file_entry)
            inventory["counts"]["total"] += 1
            inventory["counts"][category] = inventory["counts"].get(category, 0) + 1
            folder_entry["file_count"] += 1
            folder_entry["file_types"][category] = folder_entry["file_types"].get(category, 0) + 1

    return inventory


def main():
    ap = argparse.ArgumentParser(description="Walk a construction project folder and produce a file inventory.")
    ap.add_argument("root", help="Path to the project root folder")
    ap.add_argument("-o", "--output", required=True, help="Output JSON path")
    args = ap.parse_args()

    if not HAVE_FITZ:
        print("WARNING: PyMuPDF not installed — PDF stats will be empty. Install with: pip install pymupdf --break-system-packages",
              file=sys.stderr)

    inv = walk_project(args.root)
    with open(args.output, "w") as f:
        json.dump(inv, f, indent=2)

    c = inv["counts"]
    print(f"Inventory written: {args.output}", file=sys.stderr)
    print(f"  Total files: {c['total']} | PDFs: {c['pdf']} | Docs: {c['document']} | "
          f"Images: {c['image']} | CAD: {c['cad']} | Other: {c['other']}", file=sys.stderr)
    print(f"  Top-level folders: {len([f for f in inv['folders'] if f and '/' not in f and '\\\\' not in f])}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
