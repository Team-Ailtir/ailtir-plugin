#!/usr/bin/env python3
"""
Read text from a document PDF for project-indexer.

Uses PyMuPDF text extraction. If the PDF is scanned (no extractable text),
reports that so the caller can fall back to vision or the pdf-reading skill.

Usage:
    python read_pdf.py document.pdf
    python read_pdf.py document.pdf --max-chars 50000
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install pymupdf --break-system-packages", file=sys.stderr)
    sys.exit(1)


def read_pdf(pdf_path: str, max_chars: int = None) -> dict:
    doc = fitz.open(pdf_path)
    try:
        pages = []
        total_chars = 0
        for i in range(len(doc)):
            page = doc[i]
            text = page.get_text("text")
            pages.append({"page": i + 1, "text": text, "char_count": len(text)})
            total_chars += len(text)
            if max_chars and total_chars >= max_chars:
                break

        scanned_likely = total_chars == 0 and len(doc) > 0

        return {
            "source_file": Path(pdf_path).name,
            "source_path": str(pdf_path),
            "total_pages": len(doc),
            "pages_read": len(pages),
            "total_chars": total_chars,
            "scanned_likely": scanned_likely,
            "pages": pages,
        }
    finally:
        doc.close()


def main():
    ap = argparse.ArgumentParser(description="Extract text from a document PDF.")
    ap.add_argument("pdf_path")
    ap.add_argument("--max-chars", type=int, default=None,
                    help="Stop after approximately this many characters")
    ap.add_argument("--plain", action="store_true", help="Output plain text instead of JSON")
    args = ap.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"ERROR: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    data = read_pdf(args.pdf_path, args.max_chars)

    if args.plain:
        if data["scanned_likely"]:
            print(f"[No extractable text in {data['source_file']} — likely scanned. "
                  f"Use the pdf-reading skill for OCR.]", file=sys.stderr)
        for p in data["pages"]:
            print(f"\n--- Page {p['page']} ---\n{p['text']}")
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
