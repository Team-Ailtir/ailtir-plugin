"""Ailtir takeoff — assembly expansion engine.

Expands a small set of directly-measured primary quantities into a full
NRM2/NRM1-aligned Bill of Quantities by looking up trade assemblies in
``data/assemblies/<discipline>.json`` and emitting the secondary
components (leaf + frame + hinges + labour, slab + formwork + rebar,
socket + back-box + cable + containment, and so on) that a quantity
surveyor would book alongside every primary.

Design references (public sources only):

- NRM1 element hierarchy (0..8, plus group codes such as 2.8 Internal
  Doors, 5.8 Electrical installations) — ``research/nrm2-measurement.md``
  section 1.
- Material waste-allowance defaults — ``research/nrm2-measurement.md``
  section 9 (WRAP Net Waste Method benchmarks; SMM7-inherited practice).
- Rounding conventions (line-level, banker's rounding) —
  ``research/nrm2-measurement.md`` section 14.
- Composite line-tag convention ``E{element}/A{assembly}/L{seq}`` —
  ``research/nrm2-measurement.md`` section 13.
- Discipline / role codes for the ``--discipline`` filter and per-file
  routing — ``research/drawing-conventions.md`` role-code table.

The engine is deterministic, offline, and mutation-free with respect to
its inputs.  No pricing is applied — rates are the job of
``ailtir_estimating-workflow``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

ENGINE_VERSION = "assembly_engine/1.0"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Discipline letter (ISO 19650 role code, see research/drawing-conventions.md)
# -> assembly-file basename inside data/assemblies/.
DISCIPLINE_FILES: dict[str, str] = {
    "A": "architectural.json",   # Architect
    "S": "structural.json",      # Structural Engineer
    "M": "mechanical.json",      # Mechanical Engineer
    "H": "mechanical.json",      # HVAC / Mechanical Services (same trade)
    "E": "electrical.json",      # Electrical Engineer
    "P": "plumbing.json",        # Public Health / Plumbing
    "C": "civil.json",           # Civil Engineer
    "D": "civil.json",           # Drainage / Highways (civil family)
    "L": "landscape.json",       # Landscape Architect
    "F": "fire.json",            # Fire (US NCS) — Facilities in some UK schemes
    "Q": None,                   # Quantity Surveyor (no trade file)
}

# NRM1 element codes considered valid.  Sourced from
# research/nrm2-measurement.md §1 — top-level elements 0..8 and their
# published group elements.
VALID_NRM_ELEMENTS: frozenset[str] = frozenset(
    {
        # Top-level headers (allowed as coarse tags)
        "0", "1", "2", "3", "4", "5", "6", "7", "8",
        # Group codes
        "0.1", "0.2", "0.3", "0.4", "0.5", "0.6",
        "1.1",
        "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
        "3.1", "3.2", "3.3",
        "4.1",
        "5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7",
        "5.8", "5.9", "5.10", "5.11", "5.12", "5.13", "5.14",
        "6.1",
        "7.1", "7.2", "7.3", "7.4", "7.5", "7.6",
        "8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8",
    }
)

# Canonical NRM2 units (research/nrm2-measurement.md §11).
CANONICAL_UNITS: frozenset[str] = frozenset(
    {"m", "m²", "m2", "m³", "m3", "nr", "kg", "tonne", "Item", "sum"}
)

# Material waste-fraction defaults — keyword-matched against the
# component description when the assembly does not set an explicit
# waste value.  Ordered patterns; first hit wins so more specific
# keywords (e.g. "roof tile") take priority over generic ones ("tile").
# Source: research/nrm2-measurement.md §9.
WASTE_TABLE: list[tuple[re.Pattern[str], float]] = [
    (re.compile(r"\broof tile\b|\bslate\b", re.I),                     0.075),
    (re.compile(r"\bmesh\b|\bfabric reinforcement\b", re.I),           0.125),
    (re.compile(r"\bplasterboard\b|\bMF ceiling\b", re.I),             0.10),
    (re.compile(r"\bplaster\b|\bskim\b|\brender\b", re.I),             0.10),
    (re.compile(r"\bboard\b", re.I),                                    0.10),
    (re.compile(r"\btile\b", re.I),                                     0.125),
    (re.compile(r"\btimber\b|\bjoist\b|\bstud\b|\brafter\b|\btruss\b", re.I), 0.125),
    (re.compile(r"\binsulation\b.*\b(rigid|board|PIR|PUR|XPS|EPS)\b|\brigid.*insulation\b", re.I), 0.075),
    (re.compile(r"\binsulation\b.*\b(mineral wool|rock wool|roll)\b|\bmineral wool\b", re.I),      0.05),
    (re.compile(r"\binsulation\b", re.I),                              0.075),
    (re.compile(r"\bconcrete\b|\bready-?mix\b", re.I),                 0.05),
    (re.compile(r"\bblockwork\b|\bblock\b", re.I),                     0.05),
    (re.compile(r"\bbrick(work)?\b", re.I),                            0.05),
    (re.compile(r"\bmortar\b", re.I),                                  0.05),
    (re.compile(r"\bpipe(work)?\b|\bduct\b", re.I),                    0.05),
    (re.compile(r"\bcable\b|\bcontainment\b|\btray\b|\btrunking\b|\bconduit\b", re.I), 0.05),
    (re.compile(r"\bpaint\b|\bcoating\b", re.I),                       0.075),
]

# Fallback when the description matches nothing above.  Warned per §9.
DEFAULT_UNKNOWN_WASTE = 0.05

# Regional overrides for the material waste table.  Currently the
# ARM 5 (Ireland) profile mirrors UK practice — SCSI has not yet
# published numeric divergences (see research/ireland-gc-reference.md
# §4).  The plumbing exists so a user can extend this at any time.
PROFILE_WASTE_OVERRIDES: dict[str, dict[str, float]] = {
    "nrm2-uk": {},
    "arm5-ie": {},
}

VALID_PROFILES: frozenset[str] = frozenset({"nrm2-uk", "arm5-ie"})


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Component:
    description: str
    unit: str
    ratio: float
    waste: Optional[float] = None
    element_nrm2_ref: Optional[str] = None


@dataclass(frozen=True)
class Assembly:
    id: str
    trigger_element: str
    description_matches: tuple[str, ...]
    element_nrm2_ref: str
    primary_unit: str
    components: tuple[Component, ...]
    source_file: str


@dataclass
class PrimaryItem:
    element: str
    description: str
    quantity: float
    unit: str
    discipline: str
    source_ref: dict[str, Any] = field(default_factory=dict)
    nrm2_element_ref: Optional[str] = None
    extras: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _warn(warnings: list[str], msg: str) -> None:
    """Append a warning and echo it to stderr for visibility."""
    warnings.append(msg)
    print(f"[assembly_engine] warning: {msg}", file=sys.stderr)


def normalize_element(value: str) -> str:
    """Case-fold and trim; tolerate a single trailing plural 's'."""
    if value is None:
        return ""
    v = value.strip().lower()
    # Collapse whitespace
    v = re.sub(r"\s+", " ", v)
    if v.endswith("s") and len(v) > 3:
        v = v[:-1]
    return v


def canonicalise_unit(unit: str) -> str:
    """Return a canonical NRM2 unit string ('m2' -> 'm²' etc.)."""
    if unit is None:
        return ""
    u = unit.strip()
    if u == "m2":
        return "m²"
    if u == "m3":
        return "m³"
    return u


def bankers_round(value: float, ndigits: int = 0) -> float:
    """Round-half-to-even; matches Python's built-in round semantics
    which the spec calls for at line level (§14)."""
    if math.isnan(value) or math.isinf(value):
        return value
    return round(value, ndigits)


def round_quantity(qty: float, unit: str) -> float:
    """Line-level rounding per research/nrm2-measurement.md §14."""
    u = canonicalise_unit(unit)
    if u in ("m", "m²", "m³"):
        return bankers_round(qty, 2)
    if u == "nr":
        # NRM2 forbids fractional counts (§11); banker's round to int.
        return float(bankers_round(qty, 0))
    if u == "kg":
        return bankers_round(qty, 0)
    if u == "tonne":
        return bankers_round(qty, 3)
    if u in ("Item", "sum"):
        # Item/sum carries no measured quantity; convention is 1.
        return 1.0
    # Unknown unit — keep two decimals as a safe default.
    return bankers_round(qty, 2)


def resolve_waste(
    component: Component,
    profile: str,
    warnings: list[str],
    assembly_id: str,
) -> tuple[float, Optional[str]]:
    """Determine the base waste fraction for a component.

    Precedence (spec §Waste-factor application, §7):
      1. Explicit component override (including 0.0).
      2. Material-keyword table lookup.
      3. Fallback default (0.05) with a warning.
    """
    if component.waste is not None:
        return float(component.waste), None

    overrides = PROFILE_WASTE_OVERRIDES.get(profile, {})
    for pattern, waste in WASTE_TABLE:
        if pattern.search(component.description):
            # Optional profile override, matched by the regex source string
            key = pattern.pattern
            if key in overrides:
                return float(overrides[key]), None
            return float(waste), None

    note = (
        f"waste fallback (0.05) applied — no keyword match for "
        f"'{component.description}' in {assembly_id}"
    )
    _warn(warnings, note)
    return DEFAULT_UNKNOWN_WASTE, note


# ---------------------------------------------------------------------------
# Assembly loading
# ---------------------------------------------------------------------------


def _default_assemblies_dir() -> Path:
    """Built-in assemblies directory next to this script's parent."""
    return Path(__file__).resolve().parent.parent / "data" / "assemblies"


def _parse_component(raw: dict[str, Any], assembly_id: str, source: str) -> Component:
    for key in ("description", "unit", "ratio"):
        if key not in raw:
            raise ValueError(
                f"assembly '{assembly_id}' in {source}: component missing '{key}'"
            )
    unit = canonicalise_unit(str(raw["unit"]))
    if unit not in CANONICAL_UNITS:
        raise ValueError(
            f"assembly '{assembly_id}' in {source}: unknown unit '{raw['unit']}'"
        )
    waste = raw.get("waste", None)
    if waste is not None:
        waste = float(waste)
        if waste < 0.0 or waste > 1.0:
            raise ValueError(
                f"assembly '{assembly_id}': component waste {waste} out of range 0..1"
            )
    element_ref = raw.get("element_nrm2_ref")
    if element_ref is not None and str(element_ref) not in VALID_NRM_ELEMENTS:
        raise ValueError(
            f"assembly '{assembly_id}' in {source}: unknown component "
            f"element_nrm2_ref '{element_ref}'"
        )
    return Component(
        description=str(raw["description"]),
        unit=unit,
        ratio=float(raw["ratio"]),
        waste=waste,
        element_nrm2_ref=str(element_ref) if element_ref is not None else None,
    )


def _parse_assembly(raw: dict[str, Any], source: str) -> Assembly:
    aid = str(raw.get("id", "")).strip()
    if not aid:
        raise ValueError(f"assembly in {source}: missing 'id'")
    trigger = raw.get("trigger") or {}
    trig_element = str(trigger.get("element", "")).strip()
    if not trig_element:
        raise ValueError(f"assembly '{aid}' in {source}: missing trigger.element")
    matches_raw = trigger.get("description_matches") or []
    if not isinstance(matches_raw, list):
        raise ValueError(f"assembly '{aid}': trigger.description_matches must be a list")
    matches = tuple(str(m) for m in matches_raw)
    element_ref = str(raw.get("element_nrm2_ref", "")).strip()
    if element_ref not in VALID_NRM_ELEMENTS:
        raise ValueError(
            f"assembly '{aid}' in {source}: element_nrm2_ref '{element_ref}' not "
            f"a recognised NRM1 code"
        )
    primary_unit = canonicalise_unit(str(raw.get("primary_unit", "")))
    if primary_unit not in CANONICAL_UNITS:
        raise ValueError(
            f"assembly '{aid}' in {source}: primary_unit '{primary_unit}' invalid"
        )
    comps_raw = raw.get("components") or []
    if not isinstance(comps_raw, list) or not comps_raw:
        raise ValueError(f"assembly '{aid}' in {source}: no components defined")
    components = tuple(_parse_component(c, aid, source) for c in comps_raw)
    return Assembly(
        id=aid,
        trigger_element=trig_element,
        description_matches=matches,
        element_nrm2_ref=element_ref,
        primary_unit=primary_unit,
        components=components,
        source_file=source,
    )


def load_assemblies(
    disciplines: Iterable[str],
    override_dir: Optional[Path],
    warnings: list[str],
) -> dict[str, list[Assembly]]:
    """Load assemblies keyed by discipline letter.

    Per-discipline fallback: if a file is present in the override
    directory it wins; otherwise the built-in file is used.  If a
    file is missing from both, that discipline resolves to an empty
    list and a warning is recorded (primaries pass through unchanged).
    """
    builtin = _default_assemblies_dir()
    out: dict[str, list[Assembly]] = {}
    seen_ids: dict[str, str] = {}

    if not builtin.exists() and override_dir is None:
        _warn(
            warnings,
            f"built-in assemblies dir not found at {builtin}; "
            f"all primaries will pass through unchanged",
        )

    for disc in disciplines:
        fname = DISCIPLINE_FILES.get(disc)
        if fname is None:
            out[disc] = []
            continue

        chosen: Optional[Path] = None
        if override_dir is not None:
            candidate = override_dir / fname
            if candidate.is_file():
                chosen = candidate
        if chosen is None:
            candidate = builtin / fname
            if candidate.is_file():
                chosen = candidate

        if chosen is None:
            _warn(
                warnings,
                f"no assemblies file for discipline '{disc}' "
                f"(looked for {fname}); primaries will pass through",
            )
            out[disc] = []
            continue

        try:
            data = json.loads(chosen.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"failed to read assemblies file {chosen}: {exc}") from exc

        raw_assemblies = data.get("assemblies") or []
        parsed: list[Assembly] = []
        for raw in raw_assemblies:
            asm = _parse_assembly(raw, str(chosen))
            if asm.id in seen_ids:
                raise SystemExit(
                    f"duplicate assembly id '{asm.id}' in {chosen} "
                    f"(already defined in {seen_ids[asm.id]})"
                )
            seen_ids[asm.id] = str(chosen)
            parsed.append(asm)
        out[disc] = parsed

    return out


# ---------------------------------------------------------------------------
# Matching & expansion
# ---------------------------------------------------------------------------


def find_matching_assembly(
    primary: PrimaryItem,
    candidates: list[Assembly],
    warnings: list[str],
) -> Optional[Assembly]:
    """Return the best-matching assembly for a primary, or None.

    Algorithm (spec §Assembly-matching):
      1. Element match, case-insensitive, plural-tolerant.
      2. Description substring match; empty matches list = automatic
         match with score 0.
      3. Rank by longest-matching substring; tie-break alphabetically
         by ``id``.
      4. Require unit compatibility.
    """
    p_element = normalize_element(primary.element)
    p_desc = (primary.description or "").lower()
    p_unit = canonicalise_unit(primary.unit)

    scored: list[tuple[int, str, Assembly]] = []
    for asm in candidates:
        if normalize_element(asm.trigger_element) != p_element:
            continue

        if not asm.description_matches:
            score = 0
        else:
            best = -1
            for sub in asm.description_matches:
                if sub and sub.lower() in p_desc:
                    if len(sub) > best:
                        best = len(sub)
            if best < 0:
                continue
            score = best

        if canonicalise_unit(asm.primary_unit) != p_unit:
            _warn(
                warnings,
                f"assembly '{asm.id}' matched element/description for "
                f"'{primary.element}' but unit '{primary.unit}' != "
                f"'{asm.primary_unit}'; skipping",
            )
            continue

        scored.append((score, asm.id, asm))

    if not scored:
        return None

    # Longest match wins; tie-break alphabetical by id (deterministic).
    scored.sort(key=lambda t: (-t[0], t[1]))
    return scored[0][2]


def _line_id(element_ref: str, assembly_id: Optional[str], seq: int) -> str:
    short = "none"
    if assembly_id:
        # Take last segment of dotted id, trimmed.
        short = assembly_id.split(".")[-1][:12] or "asm"
    return f"E{element_ref}/A{short}/L{seq:03d}"


def expand_primary(
    primary: PrimaryItem,
    assembly: Optional[Assembly],
    seq_start: int,
    profile: str,
    waste_adjust: float,
    warnings: list[str],
) -> tuple[list[dict[str, Any]], int]:
    """Emit BoQ rows for one primary + its (optional) assembly.

    Returns (rows, next_seq)."""
    rows: list[dict[str, Any]] = []
    seq = seq_start

    # NRM2 element ref for the primary (§NRM2 element assignment):
    #   input override > assembly.element_nrm2_ref
    if primary.nrm2_element_ref:
        primary_ref = primary.nrm2_element_ref
    elif assembly is not None:
        primary_ref = assembly.element_nrm2_ref
    else:
        primary_ref = ""  # unmatched primary with no upstream tag

    if primary_ref and primary_ref not in VALID_NRM_ELEMENTS:
        _warn(
            warnings,
            f"primary '{primary.element}' has unrecognised "
            f"nrm2_element_ref '{primary_ref}' — retained verbatim",
        )

    primary_qty = round_quantity(float(primary.quantity), primary.unit)
    primary_line_id = _line_id(primary_ref or "?", assembly.id if assembly else None, seq)
    seq += 1

    primary_row: dict[str, Any] = {
        "id":                 primary_line_id,
        "line_id":            primary_line_id,
        "element_nrm2_ref":   primary_ref,
        "item_type":          "primary",
        "description":        primary.description,
        "quantity":           primary_qty,
        "unit":               canonicalise_unit(primary.unit),
        "waste_factor":       0.0,
        "waste_adjusted_qty": primary_qty,
        "source_ref":         dict(primary.source_ref),
        "primary_ref":        None,
        "assembly_id":        assembly.id if assembly else None,
        "discipline":         primary.discipline,
    }
    # Preserve any unknown fields from the input primary.
    for k, v in primary.extras.items():
        primary_row.setdefault(k, v)

    if assembly is None:
        primary_row["notes"] = (
            f"no assembly matched: {primary.element} / {primary.description[:80]}"
        )

    rows.append(primary_row)

    if assembly is None:
        return rows, seq

    # Secondaries — one row per component, in defined order.
    for component in assembly.components:
        # Element ref for the component (§NRM2 element assignment #3):
        #   component override > primary_ref (which may itself be
        #   the input override or the assembly default).
        comp_ref = component.element_nrm2_ref or primary_ref

        base_waste, waste_note = resolve_waste(component, profile, warnings, assembly.id)
        effective_waste = base_waste * waste_adjust

        raw_qty = float(primary.quantity) * component.ratio
        qty = round_quantity(raw_qty, component.unit)
        gross = round_quantity(raw_qty * (1.0 + effective_waste), component.unit)

        secondary_line_id = _line_id(comp_ref or "?", assembly.id, seq)
        row: dict[str, Any] = {
            "id":                 secondary_line_id,
            "line_id":            secondary_line_id,
            "element_nrm2_ref":   comp_ref,
            "item_type":          "secondary",
            "description":        component.description,
            "quantity":           qty,
            "unit":               component.unit,
            "waste_factor":       base_waste,
            "waste_adjusted_qty": gross,
            "source_ref":         dict(primary.source_ref),
            "primary_ref":        primary_line_id,
            "assembly_id":        assembly.id,
            "discipline":         primary.discipline,
        }
        if waste_note:
            row["notes"] = waste_note
        rows.append(row)
        seq += 1

    return rows, seq


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _read_primaries(path: Path) -> tuple[dict[str, Any], list[PrimaryItem]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(2) from exc

    if not isinstance(payload, dict):
        print("[assembly_engine] input JSON must be an object", file=sys.stderr)
        raise SystemExit(2)

    header = {
        "project_ref":  payload.get("project_ref", ""),
        "drawing_refs": list(payload.get("drawing_refs") or []),
    }

    known = {
        "element", "description", "quantity", "unit", "source_ref",
        "discipline", "nrm2_element_ref",
    }

    primaries: list[PrimaryItem] = []
    for i, raw in enumerate(payload.get("primary") or []):
        if not isinstance(raw, dict):
            print(f"[assembly_engine] primary[{i}] is not an object", file=sys.stderr)
            raise SystemExit(2)
        try:
            primaries.append(
                PrimaryItem(
                    element=str(raw["element"]),
                    description=str(raw.get("description", "")),
                    quantity=float(raw["quantity"]),
                    unit=canonicalise_unit(str(raw["unit"])),
                    discipline=str(raw.get("discipline", "")).strip().upper() or "A",
                    source_ref=dict(raw.get("source_ref") or {}),
                    nrm2_element_ref=(
                        str(raw["nrm2_element_ref"])
                        if raw.get("nrm2_element_ref") is not None
                        else None
                    ),
                    extras={k: v for k, v in raw.items() if k not in known},
                )
            )
        except (KeyError, ValueError, TypeError) as exc:
            print(
                f"[assembly_engine] primary[{i}] malformed: {exc}",
                file=sys.stderr,
            )
            raise SystemExit(2) from exc

    return header, primaries


def _load_profile(profile_arg: Optional[str]) -> str:
    """Read Context/profile.json if present; CLI value overrides."""
    if profile_arg:
        if profile_arg not in VALID_PROFILES:
            print(
                f"[assembly_engine] unknown --profile '{profile_arg}'; "
                f"valid: {sorted(VALID_PROFILES)}",
                file=sys.stderr,
            )
            raise SystemExit(2)
        return profile_arg

    ctx = Path.cwd() / "Context" / "profile.json"
    if ctx.is_file():
        try:
            data = json.loads(ctx.read_text(encoding="utf-8"))
            p = data.get("measurement_profile") or data.get("profile")
            if p and p in VALID_PROFILES:
                return p
        except (OSError, json.JSONDecodeError):
            pass
    return "nrm2-uk"


def write_boq(path: Path, boq: dict[str, Any]) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(boq, indent=2, ensure_ascii=False, sort_keys=False),
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"[assembly_engine] cannot write {path}: {exc}", file=sys.stderr)
        raise SystemExit(4) from exc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _element_sort_key(ref: str) -> tuple[int, int]:
    """Sort NRM1 codes numerically ('5.10' > '5.2', not lexically)."""
    if not ref:
        return (99, 99)
    parts = ref.split(".")
    try:
        major = int(parts[0])
    except ValueError:
        major = 99
    minor = 0
    if len(parts) > 1:
        try:
            minor = int(parts[1])
        except ValueError:
            minor = 99
    return (major, minor)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Expand primary quantities into an NRM2-aligned BoQ.",
    )
    parser.add_argument("input", help="primary_quantities.json path")
    parser.add_argument("-o", "--output", default=None)
    parser.add_argument("--profile", default=None,
                        help="nrm2-uk (default) | arm5-ie")
    parser.add_argument("--discipline", action="append", default=None,
                        help="restrict to discipline codes; repeatable")
    parser.add_argument("--waste-adjust", type=float, default=1.0)
    parser.add_argument("--assemblies-dir", default=None)
    parser.add_argument("--report", action="store_true")

    args = parser.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"[assembly_engine] input not found: {in_path}", file=sys.stderr)
        return 2

    out_path = (
        Path(args.output)
        if args.output
        else in_path.with_name(in_path.stem + "-boq.json")
    )

    profile = _load_profile(args.profile)
    warnings: list[str] = []

    header, primaries = _read_primaries(in_path)

    # Filter by discipline (if requested)
    if args.discipline:
        wanted = {d.strip().upper() for d in args.discipline if d}
        primaries = [p for p in primaries if p.discipline in wanted]

    disciplines_needed = sorted({p.discipline for p in primaries})
    override_dir = Path(args.assemblies_dir).resolve() if args.assemblies_dir else None
    assemblies_by_disc = load_assemblies(disciplines_needed, override_dir, warnings)

    total_assemblies = sum(len(v) for v in assemblies_by_disc.values())
    builtin_dir = _default_assemblies_dir()
    if total_assemblies == 0 and (
        (override_dir is not None and not override_dir.exists())
        and not builtin_dir.exists()
    ):
        # Neither a built-in nor an override dir exists at all.
        print(
            "[assembly_engine] no assembly definitions found; "
            "pass-through mode",
            file=sys.stderr,
        )

    # Expand
    rows: list[dict[str, Any]] = []
    seq_by_key: dict[tuple[str, str], int] = {}
    unmatched = 0

    for primary in primaries:
        candidates = assemblies_by_disc.get(primary.discipline, [])
        assembly = find_matching_assembly(primary, candidates, warnings) if candidates else None
        if assembly is None:
            unmatched += 1
            if candidates:
                _warn(
                    warnings,
                    f"no assembly matched: {primary.element} / "
                    f"{primary.description[:80]}",
                )

        # Sequence counter keyed by (discipline, element_nrm2_ref)
        elem_ref = (
            primary.nrm2_element_ref
            or (assembly.element_nrm2_ref if assembly else "")
        )
        key = (primary.discipline, elem_ref)
        seq = seq_by_key.get(key, 1)
        new_rows, next_seq = expand_primary(
            primary, assembly, seq, profile, args.waste_adjust, warnings
        )
        seq_by_key[key] = next_seq
        rows.extend(new_rows)

    # Ordering: discipline -> NRM element -> primary-then-secondaries
    # -> component order.  We tag each row with an index so stable sort
    # preserves emission order within a group.
    for i, r in enumerate(rows):
        r["_order"] = i

    def _sort_key(r: dict[str, Any]) -> tuple:
        return (
            r["discipline"],
            _element_sort_key(r.get("element_nrm2_ref") or ""),
            0 if r["item_type"] == "primary" else 1,
            r["_order"],
        )

    rows.sort(key=_sort_key)
    for r in rows:
        r.pop("_order", None)

    # Summary
    by_disc: dict[str, dict[str, int]] = {}
    primary_count = 0
    secondary_count = 0
    for r in rows:
        d = r["discipline"]
        slot = by_disc.setdefault(d, {"primary": 0, "secondary": 0})
        if r["item_type"] == "primary":
            slot["primary"] += 1
            primary_count += 1
        else:
            slot["secondary"] += 1
            secondary_count += 1

    boq = {
        "project_ref":     header["project_ref"],
        "drawing_refs":    header["drawing_refs"],
        "profile":         profile,
        "generated_at":    datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_version":  ENGINE_VERSION,
        "summary": {
            "primary_count":   primary_count,
            "secondary_count": secondary_count,
            "unmatched_count": unmatched,
            "by_discipline":   by_disc,
            "warnings":        list(warnings),
        },
        "items": rows,
    }

    write_boq(out_path, boq)

    if args.report:
        print(f"Wrote {out_path}")
        print(f"profile: {profile}")
        for d in sorted(by_disc):
            slot = by_disc[d]
            print(f"  {d}: {slot['primary']} primary / {slot['secondary']} secondary")
        print(f"warnings: {unmatched} unmatched, {len(warnings)} total")

    return 0


if __name__ == "__main__":
    sys.exit(main())
