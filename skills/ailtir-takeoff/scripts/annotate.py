#!/usr/bin/env python3
"""
PDF Markup and Annotation Engine for Construction Takeoffs

Generates annotated PDFs showing exactly where quantities were measured.
Uses PyMuPDF annotation API with OCG layers for per-trade toggle-ability
in Bluebeam, Adobe Acrobat, and other PDF viewers.

Design goals:
- Annotations must be IMMEDIATELY visible on real construction drawings
- Circle markers large enough to stand out from drawing symbology
- Text callouts next to every marker showing what was counted
- High contrast colours that don't blend with drawing content
- Summary legend page with trade totals and colour key
"""

import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


# ── Colour Definitions ──
# High-contrast colours designed to NOT blend with common drawing content.
# Plumbing drawings are blue, so plumbing annotations use bright green.
# Electrical drawings are often red, so electrical annotations use bright magenta.

ANNOTATION_COLORS = {
    "electrical":    {"rgb": [0.85, 0.0, 0.5],  "name": "Magenta"},
    "plumbing":      {"rgb": [0.0, 0.75, 0.2],  "name": "Green"},
    "fire":          {"rgb": [1.0, 0.0, 0.0],   "name": "Red"},
    "structural":    {"rgb": [1.0, 0.45, 0.0],  "name": "Orange"},
    "civil":         {"rgb": [0.55, 0.27, 0.07], "name": "Brown"},
    "civil_marine":  {"rgb": [0.55, 0.27, 0.07], "name": "Brown"},
    "mechanical":    {"rgb": [0.0, 0.6, 0.9],   "name": "Cyan"},
    "architectural": {"rgb": [0.6, 0.0, 0.8],   "name": "Purple"},
    "unknown":       {"rgb": [0.9, 0.1, 0.1],   "name": "Red"},
}

# Marker sizing — must be visible on A1/ARCH D sheets viewed at full size
MARKER_RADIUS = 14        # Circle radius in PDF points (~5mm)
MARKER_BORDER_WIDTH = 2.5  # Bold border
MARKER_OPACITY = 0.7       # High visibility

# Text callout sizing
LABEL_FONT_SIZE = 8
LABEL_OPACITY = 0.9
LABEL_BG_COLOR = (1, 1, 1)  # White background for readability

# Confidence border styles
CONFIDENCE_STYLES = {
    "HIGH":   {"width": 2.5, "dashes": None},
    "MEDIUM": {"width": 2.0, "dashes": [4, 2]},
    "LOW":    {"width": 2.0, "dashes": [2, 2]},
}


def get_color(trade):
    """Get RGB colour tuple for a trade."""
    trade_lower = trade.lower()
    if trade_lower in ANNOTATION_COLORS:
        return ANNOTATION_COLORS[trade_lower]["rgb"]
    return ANNOTATION_COLORS["unknown"]["rgb"]


def get_border_style(confidence):
    """Get border width and dash pattern for confidence level."""
    return CONFIDENCE_STYLES.get(confidence, CONFIDENCE_STYLES["MEDIUM"])


# ── OCG Layer Management ──

def create_trade_layers(doc, trades):
    """Create OCG (Optional Content Group) layers per trade.

    These appear as toggleable layers in Bluebeam/Acrobat.
    """
    ocg_map = {}
    for trade in trades:
        layer_name = f"Takeoff — {trade.title()}"
        xref = doc.add_ocg(layer_name, on=True)
        ocg_map[trade.lower()] = xref
    return ocg_map


# ── Annotation Functions ──

def annotate_count_item(page, center_x, center_y, trade, tag, confidence,
                        ocg_xref=None):
    """Mark a counted item with a bold circle marker and text label.

    The circle is large and high-contrast so it's immediately visible
    over the original drawing content. A text callout with the tag name
    sits above-right of the marker.
    """
    color = get_color(trade)
    border = get_border_style(confidence)

    # Bold circle marker
    rect = fitz.Rect(
        center_x - MARKER_RADIUS, center_y - MARKER_RADIUS,
        center_x + MARKER_RADIUS, center_y + MARKER_RADIUS,
    )

    annot = page.add_circle_annot(rect)
    annot.set_colors(stroke=color)
    annot.set_opacity(MARKER_OPACITY)
    annot.set_border(width=border["width"], dashes=border.get("dashes"))
    annot.info["content"] = f"{tag} [{confidence}]"
    annot.info["title"] = f"Takeoff — {trade.title()}"

    if ocg_xref:
        annot.set_oc(ocg_xref)

    annot.update()

    # Text callout above-right of marker
    label_text = tag if tag else trade[:3].upper()
    text_x = center_x + MARKER_RADIUS + 2
    text_y = center_y - MARKER_RADIUS
    text_width = max(len(label_text) * LABEL_FONT_SIZE * 0.55, 25)

    label_rect = fitz.Rect(
        text_x, text_y - 2,
        text_x + text_width + 6, text_y + LABEL_FONT_SIZE + 4,
    )

    label_annot = page.add_freetext_annot(
        label_rect,
        label_text,
        fontsize=LABEL_FONT_SIZE,
        fontname="Helvetica-Bold",
        text_color=color,
        fill_color=LABEL_BG_COLOR,
        border_color=color,
    )
    label_annot.set_opacity(LABEL_OPACITY)

    if ocg_xref:
        label_annot.set_oc(ocg_xref)

    label_annot.update()


def annotate_area(page, boundary_points, trade, quantity_text, confidence,
                  ocg_xref=None):
    """Mark a measured area with a filled polygon."""
    if len(boundary_points) < 3:
        return

    color = get_color(trade)
    border = get_border_style(confidence)

    points = [fitz.Point(p[0], p[1]) for p in boundary_points]

    annot = page.add_polygon_annot(points)
    annot.set_colors(stroke=color, fill=color)
    annot.set_opacity(0.2)  # Area fills stay subtle
    annot.set_border(width=border["width"], dashes=border.get("dashes"))
    annot.info["content"] = quantity_text
    annot.info["title"] = f"Takeoff — {trade.title()}"

    if ocg_xref:
        annot.set_oc(ocg_xref)

    annot.update()


def annotate_linear(page, path_points, trade, quantity_text, confidence,
                    ocg_xref=None):
    """Mark a linear measurement with a bold polyline stroke."""
    if len(path_points) < 2:
        return

    color = get_color(trade)
    border = get_border_style(confidence)

    points = [fitz.Point(p[0], p[1]) for p in path_points]

    annot = page.add_polyline_annot(points)
    annot.set_colors(stroke=color)
    annot.set_opacity(0.8)
    annot.set_border(width=border["width"] + 1.5, dashes=border.get("dashes"))
    annot.info["content"] = quantity_text
    annot.info["title"] = f"Takeoff — {trade.title()}"

    if ocg_xref:
        annot.set_oc(ocg_xref)

    annot.update()


# ── Legend Page ──

def add_legend_page(doc, trade_counts, page_counts):
    """Add a summary legend page at the end of the document.

    Shows colour key with counts, confidence explanation, and per-page summary.
    """
    page = doc.new_page(width=595, height=842)  # A4

    # Title
    title_rect = fitz.Rect(50, 40, 545, 70)
    page.insert_textbox(title_rect, "QUANTITY TAKEOFF — MARKUP SUMMARY",
                        fontsize=16, fontname="Helvetica-Bold", color=(0.12, 0.12, 0.12))

    sub_rect = fitz.Rect(50, 72, 545, 90)
    page.insert_textbox(sub_rect, "Construction Takeoff Skill",
                        fontsize=9, fontname="Helvetica", color=(0.5, 0.5, 0.5))

    y = 110

    # Trade colour key with counts
    page.insert_textbox(fitz.Rect(50, y, 300, y + 18), "TRADE COLOURS",
                        fontsize=11, fontname="Helvetica-Bold", color=(0.12, 0.12, 0.12))
    y += 24

    for trade in sorted(trade_counts.keys()):
        color = get_color(trade)
        count = trade_counts[trade]
        color_name = ANNOTATION_COLORS.get(trade, {}).get("name", "")

        # Colour swatch
        swatch_rect = fitz.Rect(60, y + 1, 80, y + 13)
        page.draw_rect(swatch_rect, color=color, fill=color)
        page.draw_rect(swatch_rect, color=(0.3, 0.3, 0.3), width=0.5)

        # Trade name and count
        page.insert_textbox(fitz.Rect(88, y, 350, y + 15),
                            f"{trade.title()} ({color_name}) — {count} markers",
                            fontsize=9, fontname="Helvetica", color=(0.15, 0.15, 0.15))
        y += 18

    y += 20

    # Confidence key
    page.insert_textbox(fitz.Rect(50, y, 300, y + 18), "CONFIDENCE LEVELS",
                        fontsize=11, fontname="Helvetica-Bold", color=(0.12, 0.12, 0.12))
    y += 24

    confidence_items = [
        ("HIGH", "Solid border", "Vector-extracted, cross-referenced"),
        ("MEDIUM", "Dashed border", "Single-source or vision-verified"),
        ("LOW", "Dotted border", "Estimated, unverified, or flagged for review"),
    ]

    for level, border_desc, explanation in confidence_items:
        page.insert_textbox(fitz.Rect(60, y, 120, y + 14),
                            f"{level}:", fontsize=9, fontname="Helvetica-Bold",
                            color=(0.15, 0.15, 0.15))
        page.insert_textbox(fitz.Rect(120, y, 545, y + 14),
                            f"{border_desc} — {explanation}",
                            fontsize=8, fontname="Helvetica", color=(0.35, 0.35, 0.35))
        y += 16

    y += 20

    # Per-page summary
    if page_counts:
        page.insert_textbox(fitz.Rect(50, y, 300, y + 18), "PAGES ANNOTATED",
                            fontsize=11, fontname="Helvetica-Bold", color=(0.12, 0.12, 0.12))
        y += 24

        for pg_num in sorted(page_counts.keys()):
            count = page_counts[pg_num]
            page.insert_textbox(fitz.Rect(60, y, 545, y + 14),
                                f"Page {pg_num}: {count} items marked",
                                fontsize=8, fontname="Helvetica", color=(0.3, 0.3, 0.3))
            y += 14
            if y > 780:  # Don't overflow the page
                break

    y += 20

    # Notes
    page.insert_textbox(fitz.Rect(50, y, 300, y + 18), "NOTES",
                        fontsize=11, fontname="Helvetica-Bold", color=(0.12, 0.12, 0.12))
    y += 24

    notes = [
        "Annotations are on OCG layers — toggle by trade in Bluebeam or Acrobat.",
        "Click annotations to see details in the popup note.",
        "All quantities must be verified by a qualified estimator before use.",
        "The Excel register is the definitive output — this markup shows what was measured.",
    ]

    for note in notes:
        page.insert_textbox(fitz.Rect(60, y, 545, y + 14),
                            f"  {note}",
                            fontsize=8, fontname="Helvetica", color=(0.35, 0.35, 0.35))
        y += 14


# ── Main Annotation Pipeline ──

def annotate_takeoff(pdf_path, takeoff_results, output_path, page_extractions=None):
    """Main entry point: annotate a PDF with takeoff results.

    Args:
        pdf_path: path to original drawing PDF
        takeoff_results: list of quantity dicts (from assembly engine or manual)
            Each item should have: tag, description, trade, quantity, unit,
            confidence, drawing_ref (page number)
        output_path: where to save the annotated PDF
        page_extractions: list of per-page extraction results (for coordinate data)

    Returns:
        str: path to annotated PDF
    """
    doc = fitz.open(pdf_path)

    # Determine which trades are present
    trades_present = set()
    for item in takeoff_results:
        trade = item.get("trade", "unknown")
        trades_present.add(trade.lower())

    # Create OCG layers
    ocg_map = create_trade_layers(doc, sorted(trades_present))

    # Track counts for legend
    trade_counts = {}
    page_counts = {}

    # Annotate counted items using coordinates from page extractions
    if page_extractions:
        for page_data in page_extractions:
            page_num = page_data.get("page_number", 1)
            if page_num > len(doc):
                continue

            page = doc[page_num - 1]
            tag_counts = page_data.get("tag_counts", {})

            for tag, tag_data in tag_counts.items():
                trade = tag_data.get("category", "unknown").lower()
                ocg_xref = ocg_map.get(trade)
                locations = tag_data.get("locations", [])

                if not locations:
                    continue

                for loc in locations:
                    annotate_count_item(
                        page=page,
                        center_x=loc["x"],
                        center_y=loc["y"],
                        trade=trade,
                        tag=tag,
                        confidence="HIGH",  # Vector-extracted items are HIGH
                        ocg_xref=ocg_xref,
                    )

                    # Track counts
                    trade_counts[trade] = trade_counts.get(trade, 0) + 1
                    page_counts[page_num] = page_counts.get(page_num, 0) + 1

    # Also annotate items from takeoff_results that have explicit coordinates
    for item in takeoff_results:
        if item.get("item_type") != "primary":
            continue

        locations = item.get("locations", [])
        if not locations:
            continue

        trade = item.get("trade", "unknown").lower()
        tag = item.get("tag", "")
        confidence = item.get("confidence", "MEDIUM")
        ocg_xref = ocg_map.get(trade)

        # Parse page number from drawing_ref
        drawing_ref = item.get("drawing_ref", "")
        page_num = None
        if "page" in drawing_ref.lower():
            import re
            match = re.search(r'page\s*(\d+)', drawing_ref, re.IGNORECASE)
            if match:
                page_num = int(match.group(1))

        if page_num and page_num <= len(doc):
            page = doc[page_num - 1]
            for loc in locations:
                annotate_count_item(
                    page=page,
                    center_x=loc["x"],
                    center_y=loc["y"],
                    trade=trade,
                    tag=tag,
                    confidence=confidence,
                    ocg_xref=ocg_xref,
                )
                trade_counts[trade] = trade_counts.get(trade, 0) + 1
                page_counts[page_num] = page_counts.get(page_num, 0) + 1

    # Add legend page
    add_legend_page(doc, trade_counts, page_counts)

    # Save
    doc.save(output_path)
    doc.close()

    total_markers = sum(trade_counts.values())
    print(f"Annotated PDF saved to: {output_path} ({total_markers} markers across {len(page_counts)} pages)", file=sys.stderr)
    return output_path
