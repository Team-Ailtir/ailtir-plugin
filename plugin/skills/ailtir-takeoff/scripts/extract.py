#!/usr/bin/env python3
"""
Enhanced Vector Data Extraction for Construction Drawings (v2)

Extracts text objects, construction tags, dimensions, scale information,
geometric shapes, and legend data from PDF drawing pages using PyMuPDF.

Enhancements over v1:
- Geometric analysis (circles, rectangles, polylines, areas via geometry.py)
- Externalised tag patterns from data/tags.json (AU/NZ + North American)
- Multi-method scale detection with cross-validation
- Legend region detection and symbol extraction
- All coordinates preserved for downstream annotation

Each extracted item includes x,y coordinates for markup and traceability.

Usage:
    python extract.py drawing.pdf -o extracted.json --pretty
    python extract.py drawing.pdf --page 1 -o page1.json
"""

import sys
import json
import re
import argparse
from pathlib import Path
from collections import defaultdict

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: PyMuPDF required. Install with: pip install pymupdf", file=sys.stderr)
    sys.exit(1)

# Import geometry module
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
try:
    from geometry import analyze_drawings
except ImportError:
    analyze_drawings = None
    print("WARNING: geometry.py not found — geometric analysis disabled", file=sys.stderr)

skill_dir = script_dir.parent
data_dir = skill_dir / "data"


# ── Load External Data ──

def load_tag_patterns():
    """Load tag patterns from data/tags.json."""
    tags_file = data_dir / "tags.json"
    if not tags_file.exists():
        print(f"WARNING: {tags_file} not found — using built-in patterns", file=sys.stderr)
        return _builtin_tag_patterns()

    with open(tags_file) as f:
        data = json.load(f)

    patterns = {}
    for category, tags in data.items():
        if category.startswith("_"):
            continue
        for tag_key, info in tags.items():
            pattern = info.get("pattern")
            if pattern:
                patterns[pattern] = {
                    "category": category,
                    "description": info.get("description", tag_key),
                    "unit": info.get("unit"),
                }
    return patterns


def load_standard_scales():
    """Load standard scales from data/standard_scales.json."""
    scales_file = data_dir / "standard_scales.json"
    if not scales_file.exists():
        return {"metric": [1, 2, 5, 10, 20, 25, 50, 75, 100, 200, 250, 500, 1000]}
    with open(scales_file) as f:
        return json.load(f)


def _builtin_tag_patterns():
    """Fallback tag patterns if data/tags.json is not available."""
    return {
        r'\bL(\d{1,3})\b':  {'category': 'electrical', 'description': 'Light fitting'},
        r'\bGPO\b':          {'category': 'electrical', 'description': 'General power outlet'},
        r'\bDB\b':           {'category': 'electrical', 'description': 'Distribution board'},
        r'\bWC\b':           {'category': 'plumbing',   'description': 'Toilet'},
        r'\bWHB\b':          {'category': 'plumbing',   'description': 'Wall hung basin'},
        r'\bD(\d{1,3})\b':   {'category': 'architectural', 'description': 'Door'},
        r'\bW(\d{1,3})\b':   {'category': 'architectural', 'description': 'Window'},
    }


# Dimension patterns: match things like "6000", "3500mm", "2.4m", "12'-6\""
DIMENSION_PATTERNS = [
    r'(\d{3,6})\s*(?:mm)?(?:\s|$)',        # 6000 or 6000mm (metric, no decimal)
    r'(\d+\.\d+)\s*m(?:\s|$)',              # 3.5m
    r'(\d+)\s*m(?:\s|$)',                   # 12m
    r"(\d+)['\u2019]-?\s*(\d+)[\"″]?",     # 12'-6" (imperial)
]

# Scale patterns in title blocks
SCALE_PATTERNS = [
    r'SCALE\s*[:=]?\s*1\s*:\s*(\d+)',        # SCALE: 1:100 (most specific, check first)
    r'1\s*:\s*(\d+)',                        # 1:100, 1:50
    r'(\d+)\s*:\s*1',                        # 100:1 (less common)
]

# Imperial scale patterns — fractional inch = 1'-0" format
# These match scale VALUE text like '3/32" = 1\'-0"' or '1/4" = 1\'-0"'
IMPERIAL_SCALE_PATTERNS = [
    # Standard: fraction" = 1'-0"  (handles smart quotes, escaped quotes, various dash styles)
    r"""(\d+(?:\s*/\s*\d+)?)\s*(?:"|″|'')\s*=\s*1\s*['\u2019\u2032]-?\s*0\s*(?:"|″|'')?""",
    # Reversed: 1'-0" = fraction"
    r"""1\s*['\u2019\u2032]-?\s*0\s*(?:"|″|'')?\s*=\s*(\d+(?:\s*/\s*\d+)?)\s*(?:"|″|'')""",
]

# Junk text patterns — scale-like text that is NOT an actual drawing scale
SCALE_JUNK_PATTERNS = [
    r'(?i)printed?\b.*full\s*size',           # "When sheet printed full size..."
    r'(?i)full\s*size.*scale\s*bar',          # "full size, the scale bar is..."
    r'(?i)scale\s*bar\s*is',                  # "the scale bar is 1:1"
    r'(?i)\bnote\s*:',                        # "NOTE: ..."
    r'(?i)check\s*scale',                     # "CHECK SCALE"
    r'(?i)do\s*not\s*scale',                  # "DO NOT SCALE"
    r'(?i)not\s+to\s+be\s+scaled',           # "THESE DRAWINGS ARE NOT TO BE SCALED"
    r'(?i)modulating\s+\d',                   # "MODULATING 2.5:1" (mechanical turndown ratio)
    r'(?i)turndown\s+\d',                     # "TURNDOWN 4:1"
    r'(?i)ratio\s+\d',                        # "RATIO 3:1"
    r'\d{1,2}:\d{2}:\d{2}\s*(AM|PM)?',       # Timestamps: "3:14:39 PM", "15:30:00"
    r'\d{1,2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}',  # Date-times: "18/03/2025 3:14"
]


def _parse_imperial_fraction(fraction_str):
    """Parse an imperial fraction string like '3/32' or '1/4' into a float."""
    fraction_str = fraction_str.strip()
    if '/' in fraction_str:
        parts = fraction_str.split('/')
        try:
            return float(parts[0].strip()) / float(parts[1].strip())
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(fraction_str)
    except ValueError:
        return None


def _imperial_to_factor(inches_per_foot):
    """Convert imperial scale (inches per foot) to scale factor.
    e.g. 1/4" = 1'-0" means 0.25 inches represents 12 inches → factor = 48
    """
    if not inches_per_foot or inches_per_foot <= 0:
        return None
    return round(12.0 / inches_per_foot)


# ── Extraction Functions ──

def extract_text_objects(page):
    """Extract all text objects with positions from a PDF page."""
    text_objects = []
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]

    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = span.get("text", "").strip()
                if not text:
                    continue
                bbox = span.get("bbox", [0, 0, 0, 0])
                text_objects.append({
                    "text": text,
                    "x": round(bbox[0], 1),
                    "y": round(bbox[1], 1),
                    "x2": round(bbox[2], 1),
                    "y2": round(bbox[3], 1),
                    "cx": round((bbox[0] + bbox[2]) / 2, 1),
                    "cy": round((bbox[1] + bbox[3]) / 2, 1),
                    "font_size": round(span.get("size", 0), 1),
                    "font": span.get("font", ""),
                })
    return text_objects


# Maximum text length for a tag label — real drawing tags are short callouts (e.g. "AC-1",
# "GPO", "L5", "HV-2"). Specification paragraphs and notes are much longer.
# This filters out matches in running text like "SUPPLY FAN", "CAM LATCH", "CO-ORDINATE".
TAG_MAX_TEXT_LENGTH = 25

# Patterns that indicate the text is a street address, not a tag
ADDRESS_PATTERNS = [
    r'(?i)\b(?:STREET|ST|AVE|AVENUE|ROAD|RD|BLVD|DRIVE|DR|WAY|CRESCENT|CR)\s+[NSEW]{1,2}\b',
]

# Model/part number pattern — alphanumeric strings with hyphens that are product codes,
# not drawing tags. Examples: "YSC092H3-ZA-C1", "WATTS #SD-3", "PL-55"
# If a tag match is a substring of text matching this pattern, it's likely a model number.
MODEL_NUMBER_PATTERN = re.compile(
    r'[A-Z]{2,}\d{2,}[A-Z0-9]*[-][A-Z0-9]+'   # YSC092H3-ZA-C1, PL-55
    r'|#[A-Z]{1,4}-\d+'                         # #SD-3, #FD-10
    r'|(?:WATTS|GRUNDFOS|BELL\s+AND\s+GOSSETT|B&G|CARRIER|DAIKIN|TRANE|RHEEM'
    r'|HONEYWELL|JOHNSON\s+CONTROLS|SIEMENS|DANFOSS|WILO)\s+',  # Manufacturer prefixes
    re.IGNORECASE
)

# Room number context — B{n} tags that are actually room identifiers, not beams.
# Match when B{n} appears with room-context words nearby.
ROOM_NUMBER_CONTEXT = re.compile(
    r'(?:ROOM|ELECTRICAL|ELEC\.|IN\s+BASEMENT|BASEMENT|LEVEL|FLOOR|SUITE|UNIT)\s+B\d+'
    r'|B\d+\s+(?:ELEC\.?|ELECTRICAL|IN\s+BASEMENT|MECH\.?|MECHANICAL|STORAGE|JANITOR)',
    re.IGNORECASE,
)

# HVAC "Dry Bulb" context — DB in HVAC schedules means Dry Bulb temperature, not
# Distribution Board. Match when DB appears with temperature-context words.
HVAC_DB_CONTEXT = re.compile(
    r'(?:EAT|LAT|OAT|SAT|RAT|SUMMER|WINTER|LEAVING|ENTERING|OUTDOOR|SUPPLY|RETURN'
    r'|MIXED|AMBIENT|DESIGN|WET|DRY)\s+DB'
    r'|DB\s*\(?(?:DEG|°|TEMP)',
    re.IGNORECASE,
)

# Description-word patterns — words like "FAN TYPE", "FAN COIL" are labels/descriptions,
# not countable items. FAN should match "FAN", "FAN-1", "EF-1", not "FAN TYPE".
DESCRIPTION_CONTEXT = re.compile(
    r'(?:FAN|PUMP|VALVE|UNIT|PANEL)\s+(?:TYPE|COIL|DETAIL|DATA|CAPACITY|MODEL'
    r'|SIZE|RATING|SCHEDULE|SELECTION|CURVE|PERFORMANCE|SPECIFICATION)',
    re.IGNORECASE,
)


def _is_model_number(text, match_start, match_end):
    """Check if the tag match is embedded inside a model/part number string."""
    # If the match starts after position 0 and is preceded by alphanumeric or #, likely a model number
    if match_start > 0:
        preceding = text[:match_start]
        # Check for manufacturer prefix or model number pattern in the full text
        if MODEL_NUMBER_PATTERN.search(text):
            return True
        # Check if preceded by alphanumeric characters (embedded in longer code)
        if preceding and (preceding[-1].isalnum() or preceding[-1] in '#'):
            return True
    # Check if followed by alphanumeric that makes it part of a longer code
    if match_end < len(text):
        following = text[match_end:]
        if following and following[0].isalnum() and following[0] != ' ':
            return True
    return False


def detect_tags(text_objects, tag_patterns=None):
    """Match text objects against construction tag patterns.

    Filters:
    - Skips annotation-only tags (unit=null) like NTS, TYP, SIM, CLR, ABV, ADA, INV.
    - Skips long text spans (spec paragraphs, notes) — real tags are short callouts.
    - Skips street address text that contains directional abbreviations (SW, NE, etc.).
    - Skips tags embedded inside manufacturer model/part numbers.
    - Skips B{n} when context indicates a room number, not a beam.
    - Skips DB when context indicates HVAC "Dry Bulb", not Distribution Board.
    - Skips description-word matches (e.g. "FAN TYPE" is a label, not a countable item).
    """
    if tag_patterns is None:
        tag_patterns = load_tag_patterns()

    tag_instances = []
    tag_counts = defaultdict(lambda: {"count": 0, "description": "", "category": "", "unit": "", "locations": []})

    for obj in text_objects:
        text = obj["text"]

        # Skip long text — spec paragraphs, notes, general conditions are not tag labels
        if len(text) > TAG_MAX_TEXT_LENGTH:
            continue

        # Skip text that looks like a street address
        if any(re.search(p, text) for p in ADDRESS_PATTERNS):
            continue

        # Skip description-word combinations (labels, not items)
        if DESCRIPTION_CONTEXT.search(text):
            continue

        for pattern, info in tag_patterns.items():
            # Skip annotation-only patterns (unit is null) — not real takeoff items
            if info.get("unit") is None:
                continue
            match = re.search(pattern, text)
            if match:
                tag_text = match.group(0)

                # Filter: skip tags embedded inside model/part numbers
                if _is_model_number(text, match.start(), match.end()):
                    continue

                # Filter: skip B{n} that are room numbers, not beams
                if info["category"] == "structural" and re.match(r'^B\d+$', tag_text):
                    if ROOM_NUMBER_CONTEXT.search(text):
                        continue

                # Filter: skip DB when it means "Dry Bulb" in HVAC context
                if tag_text == "DB" and HVAC_DB_CONTEXT.search(text):
                    continue

                tag_instances.append({
                    "tag": tag_text,
                    "full_text": text,
                    "category": info["category"],
                    "description": info["description"],
                    "x": obj["x"], "y": obj["y"],
                    "cx": obj["cx"], "cy": obj["cy"],
                    "x2": obj["x2"], "y2": obj["y2"],
                })
                entry = tag_counts[tag_text]
                entry["count"] += 1
                entry["description"] = info["description"]
                entry["category"] = info["category"]
                entry["unit"] = info.get("unit", "EA")
                entry["locations"].append({"x": obj["cx"], "y": obj["cy"]})
                break

    return tag_instances, dict(tag_counts)


def detect_dimensions(text_objects):
    """Find dimension annotations in text objects."""
    dimensions = []
    for obj in text_objects:
        text = obj["text"]
        for pattern in DIMENSION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    if len(match.groups()) == 2:
                        feet = int(match.group(1))
                        inches = int(match.group(2))
                        value_mm = round((feet * 12 + inches) * 25.4, 1)
                    elif '.' in match.group(1):
                        value_mm = round(float(match.group(1)) * 1000, 1)
                    else:
                        val = int(match.group(1))
                        value_mm = val * 1000 if val < 100 else val
                except (ValueError, IndexError):
                    continue

                dimensions.append({
                    "text": text.strip(),
                    "value_mm": value_mm,
                    "x": obj["cx"],
                    "y": obj["cy"],
                })
                break
    return dimensions


def _find_nearby_text(text_objects, anchor_obj, max_dy=60, max_dx=200):
    """Find text objects near an anchor (e.g. text below a 'SCALE:' label)."""
    nearby = []
    for obj in text_objects:
        if obj is anchor_obj:
            continue
        dy = obj["cy"] - anchor_obj["cy"]
        dx = abs(obj["cx"] - anchor_obj["cx"])
        # Look below and slightly to the right (scale value is typically right below the label)
        if 5 < dy < max_dy and dx < max_dx:
            nearby.append((dy, obj))
    nearby.sort(key=lambda t: t[0])
    return [obj for _, obj in nearby]


def _try_imperial_scale(text, standard_scales):
    """Try to parse imperial scale from text like '3/32" = 1\\'-0"' or 'NTS'.
    Returns (factor, format_str) or (None, None).
    """
    text = text.strip()

    # Check for NTS / N.T.S. — explicitly not to scale
    if re.match(r'^N\.?T\.?S\.?$', text, re.IGNORECASE):
        return None, "NTS"

    # Try each imperial pattern
    for pattern in IMPERIAL_SCALE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            fraction_str = match.group(1)
            inches = _parse_imperial_fraction(fraction_str)
            factor = _imperial_to_factor(inches)
            if factor and factor > 1:
                # Snap to known imperial scales
                imperial_scales = standard_scales.get("imperial", {})
                imperial_factors = list(imperial_scales.values())
                if imperial_factors:
                    nearest = min(imperial_factors, key=lambda s: abs(s - factor))
                    tolerance = standard_scales.get("snap_tolerance_percent", 5)
                    if abs(nearest - factor) / max(nearest, 1) * 100 <= tolerance:
                        factor = nearest
                return factor, text
    return None, None


def detect_scale_multi_method(text_objects, page_rect, dimensions=None):
    """Multi-method scale detection with cross-validation.

    Method 1: Metric ratio in text (1:100)
    Method 2: Imperial scale in text (3/32" = 1'-0")
    Method 3: SCALE: label with nearby value text (handles split spans)

    Returns scale result with confidence based on agreement between methods.
    """
    page_h = page_rect.height
    page_w = page_rect.width
    standard_scales = load_standard_scales()
    methods = []

    # Index text objects that are SCALE: labels (for nearby-text search)
    scale_labels = []

    for obj in text_objects:
        text = obj["text"].strip()

        # Skip junk text
        is_junk = any(re.search(p, text) for p in SCALE_JUNK_PATTERNS)
        if is_junk:
            continue

        in_title_block = obj["cy"] > page_h * 0.7 and obj["cx"] > page_w * 0.5

        # Track standalone "SCALE:" labels for nearby-text search
        if re.match(r'^SCALE\s*:?\s*$', text, re.IGNORECASE):
            scale_labels.append(obj)

        # Method 1: Metric ratio patterns (1:100)
        for pattern in SCALE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    factor = int(match.group(1))
                    methods.append({
                        "method": "metric_ratio",
                        "factor": factor,
                        "confidence": "high" if in_title_block else "medium",
                        "source_text": text,
                        "location": {"x": obj["cx"], "y": obj["cy"]},
                    })
                except (ValueError, IndexError):
                    continue

        # Method 2: Imperial scale in same text object
        factor, fmt = _try_imperial_scale(text, standard_scales)
        if factor:
            methods.append({
                "method": "imperial_inline",
                "factor": factor,
                "confidence": "high" if in_title_block else "medium",
                "source_text": text,
                "location": {"x": obj["cx"], "y": obj["cy"]},
            })

    # Method 3: SCALE: label with value in nearby text object below
    for label_obj in scale_labels:
        nearby = _find_nearby_text(text_objects, label_obj)
        for near_obj in nearby[:3]:  # Check up to 3 nearby objects
            near_text = near_obj["text"].strip()

            # Skip NTS
            if re.match(r'^N\.?T\.?S\.?$', near_text, re.IGNORECASE):
                break  # This view is NTS, skip it

            # Try imperial
            factor, fmt = _try_imperial_scale(near_text, standard_scales)
            if factor:
                in_title_block = label_obj["cy"] > page_h * 0.7 and label_obj["cx"] > page_w * 0.5
                methods.append({
                    "method": "imperial_nearby",
                    "factor": factor,
                    "confidence": "high" if in_title_block else "medium",
                    "source_text": f"SCALE: {near_text}",
                    "location": {"x": label_obj["cx"], "y": label_obj["cy"]},
                })
                break

            # Try metric in nearby text
            for pattern in SCALE_PATTERNS:
                match = re.search(pattern, near_text, re.IGNORECASE)
                if match:
                    try:
                        factor = int(match.group(1))
                        in_title_block = label_obj["cy"] > page_h * 0.7 and label_obj["cx"] > page_w * 0.5
                        methods.append({
                            "method": "metric_nearby",
                            "factor": factor,
                            "confidence": "high" if in_title_block else "medium",
                            "source_text": f"SCALE: {near_text}",
                            "location": {"x": label_obj["cx"], "y": label_obj["cy"]},
                        })
                    except (ValueError, IndexError):
                        continue
                    break
            else:
                continue
            break

    # Snap metric methods to nearest standard scale
    metric_scales = standard_scales.get("metric", [])
    for m in methods:
        if m["method"].startswith("metric"):
            nearest = min(metric_scales, key=lambda s: abs(s - m["factor"])) if metric_scales else m["factor"]
            tolerance = standard_scales.get("snap_tolerance_percent", 5)
            if abs(nearest - m["factor"]) / max(nearest, 1) * 100 <= tolerance:
                m["snapped_to"] = nearest
                m["factor"] = nearest

    if not methods:
        return {
            "detected": False,
            "methods": [],
            "note": "No scale detected. Manual scale input required.",
        }

    # Filter out 1:1 (almost never a real drawing scale for construction)
    real_methods = [m for m in methods if m["factor"] > 1]
    if real_methods:
        working_methods = real_methods
    else:
        working_methods = methods

    # Pick the best scale — prefer the most common factor (the primary drawing scale)
    # rather than detail view scales, as the primary view covers most of the page
    from collections import Counter
    factor_counts = Counter(m["factor"] for m in working_methods)
    most_common_factor = factor_counts.most_common(1)[0][0]

    # Among methods with the most common factor, prefer high confidence
    primary_methods = [m for m in working_methods if m["factor"] == most_common_factor]
    high_conf = [m for m in primary_methods if m["confidence"] == "high"]
    best = high_conf[0] if high_conf else primary_methods[0]

    # Cross-validate
    factors = [m["factor"] for m in working_methods]
    unique_factors = set(factors)
    agreed = len(unique_factors) == 1

    # Confidence scoring
    if agreed and best["confidence"] == "high":
        final_confidence = "high"
    elif agreed:
        final_confidence = "medium"
    elif len(unique_factors) > 1:
        # Multiple scales is normal (main view + details) — confidence based on best match
        final_confidence = "medium" if best["confidence"] == "high" else "low"
    else:
        final_confidence = "medium"

    return {
        "detected": True,
        "factor": best["factor"],
        "methods": methods,
        "agreed": agreed,
        "unique_scales": sorted(unique_factors),
        "primary_scale": most_common_factor,
        "final_factor": best["factor"],
        "confidence": final_confidence,
        "source_text": best.get("source_text", ""),
    }


def detect_legend(text_objects, page_rect):
    """Detect the legend/key/schedule area on a drawing page.

    Covers both AU/NZ terminology (LEGEND, KEY) and North American (SCHEDULE,
    FIXTURE SCHEDULE, SYMBOL SCHEDULE, DEVICE SCHEDULE, etc.).
    """
    # Exact match markers
    EXACT_MARKERS = {
        "LEGEND", "KEY", "SYMBOL LEGEND", "SYMBOL KEY", "SYMBOLS",
        "ABBREVIATIONS", "LEGEND:", "KEY:",
        # North American schedule terminology
        "SYMBOL SCHEDULE", "DEVICE SCHEDULE", "FIXTURE SCHEDULE",
        "EQUIPMENT SCHEDULE", "LUMINAIRE SCHEDULE", "LIGHT FIXTURE SCHEDULE",
        "PANEL SCHEDULE", "PANEL SCHEDULES",
        "PLUMBING FIXTURE SCHEDULE", "PLUMBING SCHEDULE",
        "DOOR SCHEDULE", "WINDOW SCHEDULE", "FINISH SCHEDULE",
        "ROOM FINISH SCHEDULE", "HARDWARE SCHEDULE",
    }
    # Partial match patterns — text containing these phrases
    PARTIAL_MARKERS = [
        re.compile(r'(?i)^(?:SYMBOL|DEVICE|FIXTURE|EQUIPMENT|LUMINAIRE)\s+SCHEDULE'),
        re.compile(r'(?i)^(?:DRAWING\s+)?NOTES\s+AND\s+SYMBOL'),
    ]

    legend_markers = []
    for obj in text_objects:
        text_upper = obj["text"].upper().strip()
        if text_upper in EXACT_MARKERS:
            legend_markers.append(obj)
        elif any(p.search(text_upper) for p in PARTIAL_MARKERS):
            legend_markers.append(obj)

    if not legend_markers:
        return {"detected": False}

    marker = legend_markers[0]
    page_h = page_rect.height
    page_w = page_rect.width

    legend_region = {
        "x": max(0, marker["x"] - 20),
        "y": marker["y"],
        "width": min(400, page_w - marker["x"] + 20),
        "height": min(300, page_h - marker["y"]),
    }

    legend_texts = []
    for obj in text_objects:
        if (legend_region["x"] <= obj["cx"] <= legend_region["x"] + legend_region["width"] and
                legend_region["y"] <= obj["cy"] <= legend_region["y"] + legend_region["height"]):
            legend_texts.append(obj["text"])

    return {
        "detected": True,
        "marker_text": marker["text"],
        "region": legend_region,
        "texts": legend_texts[:30],
    }


def detect_title_block(text_objects, page_rect):
    """Extract structured title block info using font size and position heuristics.

    Strategy:
    1. Find the title strip — a cluster of large text in the margin area (bottom or left side).
       Many drawings rotate the title block into a left-margin strip with y > page height.
    2. Use font size to identify the drawing title (usually the largest text in the strip).
    3. Parse drawing number, revision, date, scale from nearby text using targeted regexes.
    """
    page_h = page_rect.height
    page_w = page_rect.width

    # Drawing number patterns — matches standalone codes like A102, E-2, M1.07, S-101, C3.1
    DWG_NUM_PATTERN = re.compile(
        r'^[A-Z]{1,2}[-.]?\d{1,4}(?:[-.]\d{1,3})?$', re.IGNORECASE
    )

    # Date patterns
    DATE_PATTERN = re.compile(
        r'(?:\d{1,2}\s+(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\w*\s+\d{4})'
        r'|(?:(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)\w*\s+\d{1,2},?\s+\d{4})'
        r'|(?:\d{4}[-/]\d{2}[-/]\d{2})',
        re.IGNORECASE
    )

    # Collect title strip candidates from multiple zones:
    # Zone A: bottom-right (traditional — bottom 25%, right 45%)
    # Zone B: left-margin strip (rotated — x < 10%, y > 100% of page height)
    # Zone C: right-margin strip (x > 90%, y > 100%)
    # Zone D: bottom strip (y > 90%, any x)
    strip_texts = []
    for obj in text_objects:
        in_strip = False
        # Zone A: traditional bottom-right
        if obj["cy"] > page_h * 0.85 and obj["cx"] > page_w * 0.55:
            in_strip = True
        # Zone B: left margin strip (common in rotated drawings)
        if obj["cx"] < page_w * 0.15 and obj["cy"] > page_h * 1.0:
            in_strip = True
        # Zone C: right margin strip
        if obj["cx"] > page_w * 0.85 and obj["cy"] > page_h * 1.0:
            in_strip = True
        # Zone D: bottom area beyond page
        if obj["cy"] > page_h * 1.2:
            in_strip = True

        if in_strip:
            strip_texts.append(obj)

    # If we found nothing in extended zones, fall back to a broader bottom-right
    if not strip_texts:
        strip_texts = [
            obj for obj in text_objects
            if obj["cy"] > page_h * 0.75 and obj["cx"] > page_w * 0.50
        ]

    title_block = {}

    if not strip_texts:
        return {"title": "", "drawing_number": "", "revision": "", "date": "", "scale_text": ""}

    # Sort by font size descending to find the most prominent text
    by_size = sorted(strip_texts, key=lambda o: o["font_size"], reverse=True)

    # Find drawing title — the largest text that looks like a title
    # (not a single character, not a number, not a date, not a firm name)
    title_candidates = []
    for obj in by_size:
        text = obj["text"].strip()
        # Skip very short text (single chars, single digits)
        if len(text) <= 2:
            continue
        # Skip pure numbers (project numbers, dates)
        if re.match(r'^\d+$', text):
            continue
        # Skip dates
        if DATE_PATTERN.search(text):
            continue
        # Skip drawing numbers
        if DWG_NUM_PATTERN.match(text):
            continue
        title_candidates.append(obj)

    # The drawing title is typically the largest non-trivial text
    # Often there are multiple title lines — group text at the same font size
    if title_candidates:
        top_size = title_candidates[0]["font_size"]
        # Collect all text at the top font size (within 1pt tolerance)
        title_parts = [
            obj["text"].strip() for obj in title_candidates
            if abs(obj["font_size"] - top_size) < 1.5
        ]
        # But limit to 3 parts max — beyond that we're picking up other content
        title_block["title"] = " - ".join(title_parts[:3])
    else:
        title_block["title"] = ""

    # Find drawing number — standalone alphanumeric code, usually large font
    for obj in by_size:
        text = obj["text"].strip()
        if DWG_NUM_PATTERN.match(text) and len(text) >= 2:
            title_block["drawing_number"] = text.upper()
            break

    # Also try DWG/DRG prefix pattern in any text
    if "drawing_number" not in title_block:
        for obj in strip_texts:
            dwg_match = re.search(
                r'(?:DWG|DRG|DRAWING)[\s.:#-]*([A-Z0-9][-A-Z0-9./]+)',
                obj["text"], re.IGNORECASE
            )
            if dwg_match:
                title_block["drawing_number"] = dwg_match.group(1)
                break
        else:
            title_block["drawing_number"] = ""

    # Find revision
    title_block["revision"] = ""
    for obj in strip_texts:
        text = obj["text"].strip()
        rev_match = re.search(r'(?:REV|REVISION)[\s.:#-]*([A-Z0-9]+)', text, re.IGNORECASE)
        if rev_match:
            title_block["revision"] = rev_match.group(1)
            break

    # Find date
    title_block["date"] = ""
    for obj in strip_texts:
        date_match = DATE_PATTERN.search(obj["text"])
        if date_match:
            title_block["date"] = date_match.group(0)
            break

    # Find scale text
    title_block["scale_text"] = ""
    for obj in strip_texts:
        scale_match = re.search(r'(?:SCALE[\s:]*)?(\d+\s*:\s*\d+|(?:\d+/\d+)?\s*"?\s*=\s*1)', obj["text"], re.IGNORECASE)
        if scale_match:
            title_block["scale_text"] = scale_match.group(0).strip()
            break

    return title_block


def extract_paths_summary(page):
    """Get a summary of vector paths on the page."""
    drawings = page.get_drawings()
    line_count = 0
    rect_count = 0
    curve_count = 0

    for d in drawings:
        for item in d.get("items", []):
            kind = item[0]
            if kind == "l":
                line_count += 1
            elif kind == "re":
                rect_count += 1
            elif kind in ("c", "qu"):
                curve_count += 1

    return {
        "total_paths": len(drawings),
        "lines": line_count,
        "rectangles": rect_count,
        "curves": curve_count,
    }


# ── Main Extraction Pipeline ──

def extract_page(page, page_num=1):
    """Full extraction pipeline for a single PDF page."""
    rect = page.rect
    tag_patterns = load_tag_patterns()
    text_objects = extract_text_objects(page)
    tag_instances, tag_counts = detect_tags(text_objects, tag_patterns)
    dimensions = detect_dimensions(text_objects)
    scale = detect_scale_multi_method(text_objects, rect, dimensions)
    title_block = detect_title_block(text_objects, rect)
    legend = detect_legend(text_objects, rect)
    paths_summary = extract_paths_summary(page)

    # Geometric analysis
    geometry = None
    if analyze_drawings is not None:
        drawings = page.get_drawings()
        scale_factor = scale.get("final_factor") if scale.get("detected") else None
        geometry = analyze_drawings(drawings, rect, scale_factor)

    result = {
        "page_number": page_num,
        "page_size": {
            "width_pts": round(rect.width, 1),
            "height_pts": round(rect.height, 1),
            "width_mm": round(rect.width * 25.4 / 72, 1),
            "height_mm": round(rect.height * 25.4 / 72, 1),
        },
        "scale": scale,
        "title_block": title_block,
        "legend": legend,
        "tag_counts": tag_counts,
        "tag_instances": tag_instances,
        "dimensions_found": dimensions,
        "text_objects": text_objects,
        "paths_summary": paths_summary,
        "raw_stats": {
            "text_objects": len(text_objects),
            "tag_instances": len(tag_instances),
            "unique_tags": len(tag_counts),
            "dimensions": len(dimensions),
        },
    }

    if geometry:
        result["geometry"] = geometry
        result["raw_stats"]["circles"] = geometry["summary"]["circles_found"]
        result["raw_stats"]["rectangles"] = geometry["summary"]["rectangles_found"]
        result["raw_stats"]["closed_areas"] = geometry["summary"]["closed_areas_found"]

    return result


def extract_pdf(pdf_path, page_num=None, output_path=None, pretty=False):
    """Extract from a PDF file."""
    doc = fitz.open(pdf_path)

    if page_num:
        if page_num < 1 or page_num > len(doc):
            print(f"ERROR: Page {page_num} out of range (1-{len(doc)})", file=sys.stderr)
            sys.exit(1)
        pages_to_process = [page_num - 1]
    else:
        pages_to_process = list(range(len(doc)))

    results = []
    for idx in pages_to_process:
        page = doc[idx]
        result = extract_page(page, idx + 1)
        results.append(result)

    doc.close()

    output = results[0] if len(results) == 1 else {"pages": results}

    if output_path:
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2 if pretty else None)
        print(f"Extraction saved to: {output_path}", file=sys.stderr)
    else:
        print(json.dumps(output, indent=2 if pretty else None))

    return output


def main():
    parser = argparse.ArgumentParser(description="Extract vector data from construction drawing PDF (v2)")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output JSON file path")
    parser.add_argument("--page", type=int, help="Extract specific page (1-based)")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"ERROR: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    extract_pdf(args.pdf_path, page_num=args.page, output_path=args.output, pretty=args.pretty)


if __name__ == "__main__":
    main()
