#!/usr/bin/env python3
"""Classify PDFs discovered by discover.py as drawing / document / unsure.

Reads the JSON inventory emitted by discover.py, scores each PDF against a
set of weighted structural and filename signals, and writes an enriched
inventory with a `classification` sub-object per PDF and a top-level
`classification` summary.

Filename parsing follows the BS EN ISO 19650 information container
convention (hyphen-delimited: Project-Originator-Volume-Level-Type-Role-
Number, with optional Suitability and Revision tokens). This module also
accepts underscore-separated variants because pre-2019 tools (and some
current authoring pipelines) emit them - see research/drawing-conventions.md.

Sources: ISO 19650-2 file-naming convention; UK Annex role/type/status
code aggregations reproduced across public consultant summaries.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import PurePosixPath
from typing import Any, Iterable


# ---------------------------------------------------------------------------
# Signal weights (calibrated - do not tweak without recalibrating tests)
# ---------------------------------------------------------------------------

# Structural (drawn from the pdf sub-object populated by discover.py)
W_LARGE_SHEET = 0.35            # A0/A1/A2/tabloid
W_A3 = 0.15
W_A4_OR_LETTER = -0.30
W_LANDSCAPE = 0.10
W_LOW_TEXT = 0.25               # < 400 chars first page
W_HIGH_TEXT = -0.25              # > 3000 chars first page
W_MANY_PAGES = -0.15             # > 30 pages
W_SINGLE_PAGE = 0.10

# Filename / folder-context (higher weight - filenames encode intent)
W_ISO_TYPE_DR = 0.60
W_ISO_TYPE_NON_DRAWING = -0.60
W_DWG_HINT = 0.30                # `.dwg.pdf`, `-Drawings.pdf`, ` GA `, `_GA_`, `-GA-`
W_SHEET_NUMBER = 0.30            # A-101, S201, EL-101 etc.
W_FOLDER_DRAWING = 0.20
W_FOLDER_NON_DRAWING = -0.30
W_FILENAME_NON_DRAWING = -0.25
W_LEGACY_UNDERSCORE_DISC = 0.20  # _A123_, _S045_ etc.

# Decision thresholds
DRAWING_THRESHOLD = 0.7
DOCUMENT_THRESHOLD = 0.3

# ISO 19650 non-drawing type codes that pull hard toward `document`
NON_DRAWING_TYPES = {"SP", "RP", "SH", "MS", "HS"}


# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

# Tolerant ISO 19650 pattern. Accepts either a hyphen OR underscore as
# field separator (the strict standard mandates hyphens, but real projects
# emit the underscored variant too). `strict` in the output flags which.
ISO19650_RE = re.compile(
    r"""^
    (?P<project>[A-Z0-9]{2,6})[-_]
    (?P<originator>[A-Z0-9]{2,6})[-_]
    (?P<volume>[A-Z0-9]{1,2})[-_]
    (?P<level>[A-Z0-9]{2})[-_]
    (?P<type>[A-Z]{2})[-_]
    (?P<role>[A-Z]{1,2})[-_]
    (?:(?P<classification>[A-Z][0-9]{2}[A-Z0-9]*)[-_])?
    (?P<number>\d{4,6})
    (?:[-_](?P<status>[A-Z]\d{1,2}))?
    (?:[-_](?P<revision>[PC]\d{2}(?:\.\d{2})?))?
    $""",
    re.VERBOSE,
)

# Sheet-number-in-filename pattern, e.g. A-101, S201, EL-101, M-1004
SHEET_NUMBER_RE = re.compile(r"(?:^|[\s_\-])([A-Z]{1,2}-?\d{3,4})(?=$|[\s_\-\.])")

# Legacy underscored discipline+number, e.g. _A123_, _S045_
LEGACY_DISC_NUMBER_RE = re.compile(r"_([ABCDEFGHIKLMPQSTWXYZ])(\d{3})_")

# GA hint tokens (general-arrangement)
GA_TOKENS_RE = re.compile(r"(?:^|[\s_\-])GA(?=[\s_\-]|$)")

# Non-drawing words in filename, word-boundary
FILENAME_NON_DRAWING_RE = re.compile(
    r"\b(?:spec(?:ification)?s?|schedules?|reports?|programme|contracts?)\b",
    re.IGNORECASE,
)

# Folder tokens (case-insensitive substring match)
DRAWING_FOLDER_TOKENS = ("drawings", "dwgs", "dwg", "plans", "sheets")
NON_DRAWING_FOLDER_TOKENS = (
    "specifications", "specification", "spec",
    "schedules", "schedule",
    "reports", "report",
    "contracts", "contract",
    "programme",
    "correspondence",
    "emails", "email",
)

# Status suffix (ISO 19650 suitability): S0-S7, A1..An, B1..Bn, CR
STATUS_TAIL_RE = re.compile(r"(?:^|[\s_\-])(S[0-7]|A\d{1,2}|B\d{1,2}|CR)$")

# Revision hints
ISO_REVISION_RE = re.compile(r"(?:^|[\s_\-])([PC]\d{2}(?:\.\d{2})?)(?=$|[\s_\-])")
LEGACY_REV_WORD_RE = re.compile(r"Rev\s*([A-Z0-9])\b", re.IGNORECASE)
LONE_LETTER_TAIL_RE = re.compile(r"-([A-Z])$")

# Discipline prefixes at start of stem, mapped to canonical single letter
# (multi-letter tokens are collapsed to ISO 19650 equivalents).
DISCIPLINE_PREFIXES = [
    # Multi-letter first so they win over the single-letter fallback.
    ("MEP",   "M"),
    ("MECH",  "M"),
    ("ARCH",  "A"),
    ("STRU",  "S"),
    ("ELEC",  "E"),
    ("HYDR",  "P"),
    ("FIRE",  "F"),
    ("CIVIL", "C"),
    ("LAND",  "L"),
    ("AR",    "A"),
    ("ST",    "S"),
    ("HYD",   "P"),
    # Single-letter ISO 19650 role codes.
    ("A", "A"), ("S", "S"), ("M", "M"), ("E", "E"),
    ("P", "P"), ("C", "C"), ("L", "L"), ("H", "H"),
    ("Q", "Q"), ("F", "F"),
]

# Same set, in lowercase, for folder-name scanning.
_FOLDER_DISCIPLINE_TOKENS = [(t.lower(), canon) for t, canon in DISCIPLINE_PREFIXES
                             if len(t) >= 3]

# Fire-vs-Facilities disambiguation hints
FIRE_HINT_RE = re.compile(r"\b(?:fire|fa|fs|sprinkler)\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Signal collection
# ---------------------------------------------------------------------------

def _fire(signals: list[dict], label: str, weight: float) -> None:
    """Append a fired signal to the audit trail."""
    signals.append({"signal": label, "weight": round(weight, 3)})


def collect_structural_signals(pdf_stats: dict, signals: list[dict]) -> float:
    """Score contribution from the discover.py `pdf` sub-object."""
    if not pdf_stats or "error" in pdf_stats:
        # PDF stats unavailable - can't fire structural signals.
        return 0.0

    score = 0.0

    size_class = pdf_stats.get("page_size_class")
    if size_class in ("A0", "A1", "A2", "tabloid"):
        _fire(signals, f"{size_class} sheet", W_LARGE_SHEET)
        score += W_LARGE_SHEET
    elif size_class == "A3":
        _fire(signals, "A3 sheet", W_A3)
        score += W_A3
    elif size_class in ("A4", "letter"):
        _fire(signals, f"{size_class} page", W_A4_OR_LETTER)
        score += W_A4_OR_LETTER

    orientation = pdf_stats.get("first_page_orientation")
    if orientation == "landscape":
        _fire(signals, "landscape first page", W_LANDSCAPE)
        score += W_LANDSCAPE

    char_count = pdf_stats.get("char_count_first_page")
    if isinstance(char_count, int):
        if char_count < 400:
            _fire(signals, f"low text density (chars={char_count})", W_LOW_TEXT)
            score += W_LOW_TEXT
        elif char_count > 3000:
            _fire(signals, f"high text density (chars={char_count})", W_HIGH_TEXT)
            score += W_HIGH_TEXT

    page_count = pdf_stats.get("page_count")
    if isinstance(page_count, int):
        if page_count > 30:
            _fire(signals, f"many pages ({page_count})", W_MANY_PAGES)
            score += W_MANY_PAGES
        elif page_count == 1:
            _fire(signals, "single page", W_SINGLE_PAGE)
            score += W_SINGLE_PAGE

    return score


def collect_filename_signals(
    filename: str,
    stem: str,
    folder: str,
    iso19650: dict | None,
    signals: list[dict],
) -> float:
    """Score contribution from filename, folder and ISO 19650 parse."""
    score = 0.0
    lower_name = filename.lower()
    lower_folder = folder.lower()

    # ISO 19650 type-based push
    if iso19650:
        iso_type = iso19650.get("type")
        if iso_type == "DR":
            _fire(signals, "ISO 19650 type=DR", W_ISO_TYPE_DR)
            score += W_ISO_TYPE_DR
        elif iso_type in NON_DRAWING_TYPES:
            _fire(signals, f"ISO 19650 type={iso_type} (non-drawing)",
                  W_ISO_TYPE_NON_DRAWING)
            score += W_ISO_TYPE_NON_DRAWING

    # `.dwg.pdf`, `-Drawings.pdf`, GA tokens
    if (lower_name.endswith(".dwg.pdf")
            or lower_name.endswith("-drawings.pdf")
            or "_ga_" in lower_name
            or "-ga-" in lower_name
            or " ga " in lower_name):
        _fire(signals, "drawing filename hint (.dwg.pdf / -Drawings / GA)", W_DWG_HINT)
        score += W_DWG_HINT
    elif GA_TOKENS_RE.search(stem):
        # `GA` as a standalone token in the stem (case-sensitive - `Ga`
        # inside a word must not fire).
        _fire(signals, "GA token in filename", W_DWG_HINT)
        score += W_DWG_HINT

    # Sheet-number pattern in stem
    if SHEET_NUMBER_RE.search(stem):
        _fire(signals, "sheet-number pattern in filename", W_SHEET_NUMBER)
        score += W_SHEET_NUMBER

    # Folder context - drawing-ish
    if any(tok in lower_folder for tok in DRAWING_FOLDER_TOKENS):
        _fire(signals, "folder suggests drawings", W_FOLDER_DRAWING)
        score += W_FOLDER_DRAWING

    # Folder context - non-drawing
    if any(tok in lower_folder for tok in NON_DRAWING_FOLDER_TOKENS):
        _fire(signals, "folder suggests non-drawings", W_FOLDER_NON_DRAWING)
        score += W_FOLDER_NON_DRAWING

    # Filename word-boundary non-drawing terms
    if FILENAME_NON_DRAWING_RE.search(stem):
        _fire(signals, "filename contains non-drawing term",
              W_FILENAME_NON_DRAWING)
        score += W_FILENAME_NON_DRAWING

    # Legacy underscored discipline+number, e.g. _A123_
    if LEGACY_DISC_NUMBER_RE.search(f"_{stem}_"):
        _fire(signals, "legacy underscored discipline+number",
              W_LEGACY_UNDERSCORE_DISC)
        score += W_LEGACY_UNDERSCORE_DISC

    return score


# ---------------------------------------------------------------------------
# ISO 19650 parsing
# ---------------------------------------------------------------------------

def parse_iso19650(stem: str) -> dict | None:
    """Parse an ISO 19650 information-container filename stem.

    Returns None if the stem does not match. If it does, returns the parsed
    fields plus `strict` (True iff only hyphens were used as separators).
    """
    match = ISO19650_RE.match(stem)
    if not match:
        return None

    fields = match.groupdict()
    # Strict when every separator between fields is a hyphen. If any `_`
    # appears in the delimiter positions (i.e. inside the stem at all,
    # since the pattern doesn't allow `_` inside fields), it's non-strict.
    strict = "_" not in stem

    parsed = {
        "project": fields.get("project"),
        "originator": fields.get("originator"),
        "volume": fields.get("volume"),
        "level": fields.get("level"),
        "type": fields.get("type"),
        "role": fields.get("role"),
        "classification": fields.get("classification"),
        "number": fields.get("number"),
        "status": fields.get("status"),
        "revision": fields.get("revision"),
        "strict": strict,
    }
    return parsed


# ---------------------------------------------------------------------------
# Discipline detection
# ---------------------------------------------------------------------------

def detect_discipline(
    stem: str,
    folder: str,
    iso19650: dict | None,
    signals: list[dict],
) -> str | None:
    """Resolve a single-letter discipline code, favouring filename over folder.

    Priority (per spec):
      1. ISO 19650 parsed role.
      2. Known discipline prefix at the start of the stem.
      3. Same tokens inside the parent folder name.
      4. Otherwise None.
    """
    # 1. ISO 19650
    if iso19650 and iso19650.get("role"):
        role = iso19650["role"]
        canonical = _canonicalise_role(role)
        signals.append({"signal": f"discipline={canonical} (ISO 19650 role)",
                        "weight": 0.0})
        _annotate_f_ambiguity(canonical, stem, folder, signals)
        return canonical

    # 2. Filename prefix
    for token, canonical in DISCIPLINE_PREFIXES:
        # Must be followed by `-` or `_` (real prefix), not accidental
        # substring at word start.
        prefix_len = len(token)
        if stem[:prefix_len].upper() == token and len(stem) > prefix_len:
            sep = stem[prefix_len]
            if sep in ("-", "_"):
                signals.append({"signal": f"discipline={canonical} (filename prefix)",
                                "weight": 0.0})
                _annotate_f_ambiguity(canonical, stem, folder, signals)
                return canonical

    # 3. Folder tokens
    folder_lc = folder.lower()
    for token, canonical in _FOLDER_DISCIPLINE_TOKENS:
        if token in folder_lc:
            signals.append({"signal": f"discipline={canonical} (folder context)",
                            "weight": 0.0})
            _annotate_f_ambiguity(canonical, stem, folder, signals)
            return canonical

    return None


def _canonicalise_role(role: str) -> str:
    """Fold multi-letter role tokens down to their ISO 19650 equivalent."""
    mapping = {
        "AR": "A", "ARCH": "A",
        "ST": "S", "STRU": "S",
        "MECH": "M", "MEP": "M",
        "ELEC": "E",
        "HYDR": "P", "HYD": "P",
        "CIVIL": "C",
        "LAND": "L",
        "FIRE": "F",
    }
    return mapping.get(role.upper(), role.upper())


def _annotate_f_ambiguity(
    discipline: str,
    stem: str,
    folder: str,
    signals: list[dict],
) -> None:
    """Flag Fire-vs-Facilities ambiguity for `F` when unresolved.

    The BIMicon UK Annex reading assigns `F` to Facilities Manager; the
    US NCS and some UK implementations use `F` for Fire Protection.
    Prefer Fire when any nearby signal indicates fire (Fire / FA / FS /
    Sprinkler); otherwise annotate the ambiguity so downstream skills
    can prompt.
    """
    if discipline != "F":
        return

    combined = f"{stem} {folder}"
    if FIRE_HINT_RE.search(combined):
        signals.append(
            {"signal": "discipline=F (resolved to Fire via context)",
             "weight": 0.0}
        )
    else:
        signals.append(
            {"signal": "discipline=F (ambiguous: Fire vs Facilities)",
             "weight": 0.0}
        )


# ---------------------------------------------------------------------------
# Status / revision hints
# ---------------------------------------------------------------------------

def detect_status_hint(stem: str, iso19650: dict | None) -> str | None:
    """Extract an ISO 19650 suitability/status code from the filename."""
    if iso19650 and iso19650.get("status"):
        return iso19650["status"]

    match = STATUS_TAIL_RE.search(stem)
    if match:
        return match.group(1)
    # Also accept as the very last hyphen-delimited token even without
    # the trailing-position anchor - some pipelines drop suitability
    # before revision.
    tail_tokens = re.split(r"[-_\s]", stem)
    if tail_tokens:
        for token in reversed(tail_tokens):
            if re.fullmatch(r"S[0-7]|A\d{1,2}|B\d{1,2}|CR", token):
                return token
    return None


def detect_revision_hint(stem: str, iso19650: dict | None) -> str | None:
    """Extract a revision code - ISO 19650 (P01/C02) or legacy (Rev A / Rev 1)."""
    if iso19650 and iso19650.get("revision"):
        return iso19650["revision"]

    iso_match = ISO_REVISION_RE.search(stem)
    if iso_match:
        return iso_match.group(1)

    legacy_word = LEGACY_REV_WORD_RE.search(stem)
    if legacy_word:
        return f"Rev {legacy_word.group(1).upper()}"

    lone_tail = LONE_LETTER_TAIL_RE.search(stem)
    if lone_tail:
        # Only interpret as revision when the letter isn't the whole stem
        # and isn't itself a status token like `-A1`.
        letter = lone_tail.group(1)
        # A single trailing letter can't be a status - status has a digit.
        return f"Rev {letter}"

    return None


# ---------------------------------------------------------------------------
# Scoring & decision
# ---------------------------------------------------------------------------

def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def decide(score: float) -> tuple[str, float]:
    """Turn a drawing-ness score into (kind, confidence)."""
    clamped = clamp(score)
    if clamped > DRAWING_THRESHOLD:
        return "drawing", clamped
    if clamped < DOCUMENT_THRESHOLD:
        return "document", 1.0 - clamped
    # Straddles the middle band. Report a confidence that reflects how
    # borderline the score is: further from 0.5 -> higher confidence in
    # `unsure` being the honest verdict? No - a genuinely balanced score
    # is the *least* confident outcome. Model confidence as distance
    # from the midpoint, i.e. how strongly one side pulls.
    return "unsure", abs(clamped - 0.5) * 2.0


def classify_pdf_record(record: dict) -> dict:
    """Return a classification sub-object for a single PDF file record."""
    signals: list[dict] = []
    stem = record.get("stem", "") or ""
    filename = record.get("filename", "") or ""
    folder = record.get("folder", "") or ""

    iso19650 = parse_iso19650(stem)
    if iso19650:
        signals.append({"signal": "ISO 19650 filename"
                        + ("" if iso19650["strict"] else " (underscored)"),
                        "weight": 0.0})

    # Structural (from pdf sub-object)
    score = collect_structural_signals(record.get("pdf") or {}, signals)

    # Filename + folder context
    score += collect_filename_signals(filename, stem, folder, iso19650, signals)

    kind, confidence = decide(score)

    discipline = detect_discipline(stem, folder, iso19650, signals)
    status_hint = detect_status_hint(stem, iso19650)
    revision_hint = detect_revision_hint(stem, iso19650)

    return {
        "kind_pdf": kind,
        "confidence": round(confidence, 3),
        "raw_score": round(score, 3),
        "signals": signals,
        "iso19650": iso19650,
        "discipline": discipline,
        "status_hint": status_hint,
        "revision_hint": revision_hint,
    }


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------

def load_inventory(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict) or "files" not in data:
        raise ValueError("inventory JSON missing top-level `files` array")
    return data


def enrich_inventory(inventory: dict) -> dict:
    """Attach classification to every PDF and a top-level summary."""
    files = inventory.get("files", [])
    kind_counts: Counter[str] = Counter()
    discipline_counts: Counter[str] = Counter()

    for record in files:
        if record.get("kind") != "pdf":
            continue
        classification = classify_pdf_record(record)
        record["classification"] = classification
        kind_counts[classification["kind_pdf"]] += 1
        disc = classification.get("discipline")
        if disc:
            discipline_counts[disc] += 1

    inventory["classification"] = {
        "drawing_count": kind_counts.get("drawing", 0),
        "document_count": kind_counts.get("document", 0),
        "unsure_count": kind_counts.get("unsure", 0),
        "by_discipline": dict(sorted(discipline_counts.items())),
    }
    return inventory


def print_report(inventory: dict) -> None:
    summary = inventory.get("classification", {})
    print("--- kind_pdf ---")
    for label in ("drawing", "document", "unsure"):
        print(f"  {label}: {summary.get(label + '_count', 0)}")
    print("--- discipline ---")
    by_disc = summary.get("by_discipline", {})
    if not by_disc:
        print("  (none)")
    else:
        for code, count in by_disc.items():
            print(f"  {code}: {count}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify PDFs in a discover.py inventory as drawing / "
                    "document / unsure using a score-based signal engine.",
    )
    parser.add_argument("inventory_json",
                        help="Path to the inventory JSON produced by discover.py.")
    parser.add_argument("-o", "--output", required=True,
                        help="Path to write the enriched JSON.")
    parser.add_argument("--report", action="store_true",
                        help="After writing, print a two-column summary of "
                             "discipline and kind_pdf counts to stdout.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_arg_parser().parse_args(list(argv) if argv is not None else None)

    try:
        inventory = load_inventory(args.inventory_json)
    except FileNotFoundError:
        print(f"classify.py: inventory not found: {args.inventory_json}",
              file=sys.stderr)
        return 2
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"classify.py: inventory malformed: {exc}", file=sys.stderr)
        return 2

    enriched = enrich_inventory(inventory)

    try:
        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(enriched, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    except OSError as exc:
        print(f"classify.py: cannot write output: {exc}", file=sys.stderr)
        return 2

    if args.report:
        print_report(enriched)

    return 0


if __name__ == "__main__":
    sys.exit(main())
