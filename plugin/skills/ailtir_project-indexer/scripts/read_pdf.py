#!/usr/bin/env python3
"""Extract text from a document PDF for downstream summarisation.

Handles vector-text PDFs directly; flags scanned/image-only PDFs so the
caller can dispatch them to an OCR or vision pipeline.

References:
- PyMuPDF Page.get_text  — https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_text
- PyMuPDF Page.get_images — https://pymupdf.readthedocs.io/en/latest/page.html#Page.get_images

Exit codes: 0 success | 2 unreadable | 3 PyMuPDF missing | 4 image-only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import List, Tuple

DEFAULT_MAX_PAGES = 500
IMAGE_ONLY_TEXT_THRESHOLD = 100  # chars below which we suspect a scan


def _tidy(text: str) -> str:
    """Strip trailing whitespace per line; collapse >2 blank lines to 2."""
    lines = [ln.rstrip() for ln in text.splitlines()]
    tidied = "\n".join(lines)
    return re.sub(r"\n{4,}", "\n\n\n", tidied)


def _extract(doc, max_pages: int) -> Tuple[List[dict], int, bool, int]:
    """Return (pages, total_chars, has_any_image, total_image_count)."""
    pages: List[dict] = []
    total_chars = 0
    total_images = 0
    has_any_image = False
    limit = min(len(doc), max_pages)
    for idx in range(limit):
        page = doc.load_page(idx)
        text = _tidy(page.get_text("text") or "")
        try:
            images = page.get_images(full=True)
        except Exception:
            images = []
        if images:
            has_any_image = True
            total_images += len(images)
        pages.append({"page": idx + 1, "chars": len(text), "text": text})
        total_chars += len(text)
    return pages, total_chars, has_any_image, total_images


def _emit_text(pages: List[dict], page_count: int) -> str:
    chunks: List[str] = []
    for entry in pages:
        chunks.append(f"=== Page {entry['page']} of {page_count} ===")
        chunks.append(entry["text"])
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def _emit_json(pdf_path, page_count, pages, truncated, has_text_layer) -> str:
    payload = {
        "pdf_path": os.path.abspath(pdf_path),
        "page_count": page_count,
        "pages_read": len(pages),
        "truncated": truncated,
        "has_text_layer": has_text_layer,
        "pages": pages,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract vector text from a PDF; flag image-only PDFs for OCR."
    )
    parser.add_argument("pdf_path", help="Path to source PDF.")
    parser.add_argument("-o", "--output", default=None,
                        help="Destination file (default: stdout).")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES,
                        help=f"Read only the first N pages (default {DEFAULT_MAX_PAGES}).")
    parser.add_argument("--json", action="store_true",
                        help="Emit structured JSON instead of plain text.")
    args = parser.parse_args(argv)

    try:
        import fitz  # PyMuPDF
    except ImportError:
        sys.stderr.write("read_pdf.py: PyMuPDF (pymupdf/fitz) is required. "
                         "Install with `pip install pymupdf`.\n")
        return 3

    if not os.path.isfile(args.pdf_path):
        sys.stderr.write(f"read_pdf.py: cannot read {args.pdf_path}: not a file.\n")
        return 2
    try:
        doc = fitz.open(args.pdf_path)
    except Exception as exc:
        sys.stderr.write(f"read_pdf.py: failed to open {args.pdf_path}: {exc}\n")
        return 2

    try:
        page_count = len(doc)
        max_pages = max(1, int(args.max_pages))
        truncated = page_count > max_pages
        if truncated:
            sys.stderr.write(
                f"read_pdf.py: warning - {page_count} pages exceeds --max-pages "
                f"{max_pages}; reading first {max_pages} only.\n"
            )

        pages, total_chars, has_any_image, image_count = _extract(doc, max_pages)

        if total_chars < IMAGE_ONLY_TEXT_THRESHOLD and has_any_image:
            sys.stderr.write(
                f"read_pdf.py: {args.pdf_path} appears image-only "
                f"({image_count} images, {total_chars} characters of text).\n"
                "Recommend running OCR - e.g. tesseract or a vision-based pipeline -\n"
                "before treating this document as text.\n"
            )
            return 4

        has_text_layer = total_chars > 0
        if args.json:
            body = _emit_json(args.pdf_path, page_count, pages, truncated, has_text_layer)
        else:
            body = _emit_text(pages, page_count)

        if args.output:
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(body)
        else:
            sys.stdout.write(body)
            if not body.endswith("\n"):
                sys.stdout.write("\n")
        return 0
    finally:
        try:
            doc.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())
