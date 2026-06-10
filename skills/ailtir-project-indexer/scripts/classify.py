#!/usr/bin/env python3
"""
Classify PDFs in a project inventory as drawings vs documents.

Uses heuristics based on PDF stats collected by discover.py:
 - Drawings tend to be landscape, large sheets (A1/A3), low text density,
   many vector drawings per page.
 - Documents tend to be portrait, A4-sized, high text density, few vectors.

Borderline cases are flagged for human review — never silently mis-classified.

Usage:
    python classify.py /tmp/inventory.json -o /tmp/classified.json
"""

import argparse
import json
import sys

# Thresholds were picked to be conservative — we'd rather flag a borderline case
# for the user than silently classify wrong.
# Units: points (1pt = 1/72 inch). A4 = 595 x 842 pts, A3 = 842 x 1191, A1 = 1684 x 2384.
LARGE_SHEET_MIN_DIM_PTS = 900   # anything with a dimension > ~A3 is likely a drawing
HIGH_TEXT_CHARS_PER_PAGE = 1500  # prose docs typically exceed this
LOW_TEXT_CHARS_PER_PAGE = 400    # drawings typically have less text than this per page
HIGH_VECTOR_DRAWINGS = 50        # drawings usually have many vector drawings per page


def classify_pdf(file_entry: dict) -> dict:
    """
    Return {'classification': 'drawing'|'document'|'borderline', 'confidence': 0-1, 'reasons': [...]}
    """
    stats = file_entry.get("pdf_stats") or {}
    if stats.get("error"):
        return {
            "classification": "borderline",
            "confidence": 0.0,
            "reasons": [f"Could not read PDF: {stats['error']}"],
        }

    avg_w = stats.get("avg_width_pts", 0)
    avg_h = stats.get("avg_height_pts", 0)
    orientation = stats.get("orientation", "")
    text_per_page = stats.get("avg_text_chars_per_page", 0)
    vectors_per_page = stats.get("avg_vector_drawings_per_page", 0)
    max_dim = max(avg_w, avg_h)

    drawing_score = 0
    document_score = 0
    reasons = []

    # Size — large sheets strongly suggest drawings
    if max_dim > LARGE_SHEET_MIN_DIM_PTS:
        drawing_score += 2
        reasons.append(f"Large sheet size ({max_dim:.0f}pt)")
    elif max_dim > 0 and max_dim < 900:
        document_score += 1
        reasons.append(f"Small sheet size ({max_dim:.0f}pt)")

    # Orientation
    if orientation == "landscape":
        drawing_score += 1
        reasons.append("Landscape orientation")
    elif orientation == "portrait":
        document_score += 1
        reasons.append("Portrait orientation")

    # Text density — low text per page suggests drawing, high suggests document
    if text_per_page > HIGH_TEXT_CHARS_PER_PAGE:
        document_score += 2
        reasons.append(f"High text density ({text_per_page} chars/page)")
    elif text_per_page < LOW_TEXT_CHARS_PER_PAGE and text_per_page > 0:
        drawing_score += 1
        reasons.append(f"Low text density ({text_per_page} chars/page)")
    elif text_per_page == 0:
        # Zero text = probably scanned, ambiguous
        reasons.append("No extractable text (possibly scanned)")

    # Vector density — drawings have many vector drawings
    if vectors_per_page > HIGH_VECTOR_DRAWINGS:
        drawing_score += 2
        reasons.append(f"High vector density ({vectors_per_page} drawings/page)")
    elif vectors_per_page < 10:
        document_score += 1
        reasons.append(f"Low vector density ({vectors_per_page} drawings/page)")

    # Decide
    total = drawing_score + document_score
    if total == 0:
        return {"classification": "borderline", "confidence": 0.0, "reasons": reasons or ["No signals"]}

    if drawing_score >= document_score + 2:
        confidence = drawing_score / (drawing_score + document_score)
        return {"classification": "drawing", "confidence": round(confidence, 2), "reasons": reasons}
    if document_score >= drawing_score + 2:
        confidence = document_score / (drawing_score + document_score)
        return {"classification": "document", "confidence": round(confidence, 2), "reasons": reasons}

    # Close call — flag for human
    return {
        "classification": "borderline",
        "confidence": round(max(drawing_score, document_score) / total, 2),
        "reasons": reasons + [f"Close call: drawing={drawing_score}, document={document_score}"],
    }


def main():
    ap = argparse.ArgumentParser(description="Classify PDFs as drawings or documents from inventory stats.")
    ap.add_argument("inventory", help="Path to inventory JSON from discover.py")
    ap.add_argument("-o", "--output", required=True, help="Output JSON path")
    args = ap.parse_args()

    with open(args.inventory) as f:
        inv = json.load(f)

    result = {
        "project_root": inv.get("project_root"),
        "project_name_guess": inv.get("project_name_guess"),
        "drawings": [],
        "documents": [],
        "borderline": [],
        "non_pdf_files": [],
    }

    for fe in inv.get("files", []):
        if fe.get("category") != "pdf":
            result["non_pdf_files"].append(fe)
            continue
        cls = classify_pdf(fe)
        fe["classification"] = cls["classification"]
        fe["classification_confidence"] = cls["confidence"]
        fe["classification_reasons"] = cls["reasons"]
        if cls["classification"] == "drawing":
            result["drawings"].append(fe)
        elif cls["classification"] == "document":
            result["documents"].append(fe)
        else:
            result["borderline"].append(fe)

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Classified: {len(result['drawings'])} drawings, "
          f"{len(result['documents'])} documents, "
          f"{len(result['borderline'])} borderline (need review)", file=sys.stderr)
    if result["borderline"]:
        print("\nBorderline cases:", file=sys.stderr)
        for fe in result["borderline"]:
            print(f"  - {fe['relative_path']}  [{fe.get('classification_confidence')}]",
                  file=sys.stderr)


if __name__ == "__main__":
    main()
