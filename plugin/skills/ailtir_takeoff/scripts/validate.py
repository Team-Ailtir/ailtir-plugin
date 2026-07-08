#!/usr/bin/env python3
"""validate.py — Quality-gate an NRM2-aligned Bill of Quantities.

The script reads the BoQ JSON produced by ``assembly_engine.py`` and runs
a five-layer validation framework over every line, attaching a per-item
confidence score and a top-level summary. It never edits a quantity — it
only flags. The design target is a review-queue population of 15–25% of
items so a QS's attention is spent well without the flag list becoming
noise.

Ailtir differentiators worth calling out explicitly:

1. Profile-aware benchmarks — the ``--profile ireland-gc | uk-gc``
   selector chooses between SCSI/Buildcost figures and BCIS bands.
   Placeholder rows are engineering defaults exposed as constants so
   an estimator can tune them per client; SCSI / BCIS bands are pulled
   from ``research/ireland-gc-reference.md`` §5 and
   ``research/uk-gc-reference.md`` §4 respectively. BCIS £/m² bands are
   paywalled and MUST NOT be fabricated — see the note on the
   ``BENCHMARK_TABLE`` constant.
2. NRM2 coverage audit is first-class — Layer 5 references the NRM1
   element codes exactly as they appear in
   ``research/nrm2-measurement.md`` §1 and produces
   ``coverage_gaps`` at the top of the summary.
3. Explicit target-flag band, not a magic threshold — the adaptive
   routine tunes confidence thresholds toward the ``--target-flag-min``
   / ``--target-flag-max`` band (defaults 0.15 / 0.25).
4. ``--building-type`` picks a column of the benchmark table — the same
   BoQ validated as a school and as an office produces different flags.
5. Audit trail preserved — every layer records ``delta_pct``, the
   benchmark source and the sheet refs used for cross-drawing checks.

Sources cited in code comments below:

- NRM1 elemental hierarchy + NRM2 unit list — research/nrm2-measurement.md §1, §11.
- SCSI cost benchmarks (Ireland) — research/ireland-gc-reference.md §5.
- BCIS cost benchmarks (UK) — research/uk-gc-reference.md §4.
- WRAP Net Waste Method — research/nrm2-measurement.md §9.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants and tuning defaults
# ---------------------------------------------------------------------------

# Layer 1 tolerances. Exposed as constants so a downstream skill can override
# by monkey-patching for a bespoke client profile.
TOL_DOOR_COUNT = 0.10          # ±10%
TOL_WINDOW_COUNT = 0.10        # ±10%
TOL_FLOOR_AREA = 0.02          # ±2%
TOL_WALL_LENGTH = 0.05         # ±5%
TOL_CEILING_AREA = 0.05        # ±5%
TOL_ROOF_AREA = 0.05           # ±5%
REBAR_WARN_LO_KG_PER_M3 = 80.0
REBAR_WARN_HI_KG_PER_M3 = 200.0
REBAR_SANITY_LO_KG_PER_M3 = 60.0
REBAR_SANITY_HI_KG_PER_M3 = 250.0

# Layer 2 — a warn becomes a fail once the ratio deviates by more than half
# the mid-range from its bounds.
BENCHMARK_FAIL_DEVIATION = 0.50

# Layer 4 — count tolerance rules.
CROSS_DRAWING_TOL = 0.05       # ±5% for counts ≥ 10
CROSS_DRAWING_EXACT_UNDER = 10

# Human-review band and adaptive routine.
DEFAULT_FLAG_BAND_MIN = 0.15
DEFAULT_FLAG_BAND_MAX = 0.25
MAX_ADAPTIVE_PASSES = 3

# Canonical NRM2 units — anything else earns a sanity flag.
CANONICAL_UNITS = {"m", "m2", "m3", "nr", "kg", "tonne", "Item", "sum"}

# Sanity envelopes.
DOOR_LEAF_MAX_WIDTH_M = 3.0
STRUCTURAL_SLAB_MIN_MM = 100.0
ASSUMED_STOREY_HEIGHT_M = 4.0
WINDOW_ELEVATION_AREA_PER_OPENING_M2 = 0.5

# ---------------------------------------------------------------------------
# NRM1 element structure — from research/nrm2-measurement.md §1.
# ---------------------------------------------------------------------------

NRM1_ELEMENT_NAMES: Dict[str, str] = {
    "0": "Facilitating works",
    "1": "Substructure",
    "2": "Superstructure",
    "3": "Internal Finishes",
    "4": "Fittings, Furnishings & Equipment",
    "5": "Services",
    "6": "Prefabricated buildings & units",
    "7": "Work to existing buildings",
    "8": "External Works",
    "prelims": "Preliminaries",
}

# scope_type → element_ref → status.
# status is one of: "required", "optional", "not-expected",
# or "required-if-below-DPC" (special-cased for extension substructure).
COVERAGE_MATRIX: Dict[str, Dict[str, str]] = {
    "new-build": {
        "0": "optional", "1": "required", "2": "required", "3": "required",
        "4": "optional", "5": "required", "6": "optional",
        "7": "not-expected", "8": "required", "prelims": "required",
    },
    "fit-out": {
        "0": "optional", "1": "optional", "2": "optional", "3": "required",
        "4": "required", "5": "required", "6": "optional",
        "7": "optional", "8": "optional", "prelims": "required",
    },
    "refurb": {
        "0": "optional", "1": "optional", "2": "optional", "3": "required",
        "4": "optional", "5": "required", "6": "optional",
        "7": "required", "8": "optional", "prelims": "required",
    },
    "extension": {
        "0": "optional", "1": "required-if-below-DPC", "2": "required",
        "3": "required", "4": "optional", "5": "required", "6": "optional",
        "7": "required", "8": "required", "prelims": "required",
    },
}

# ---------------------------------------------------------------------------
# Layer 2 — benchmark lookup.
#
# Ranges tagged ``placeholder`` are engineering defaults for the validator's
# cold-start. Ranges tagged ``SCSI`` or ``BCIS`` are drawn from
# research/ireland-gc-reference.md §5 or research/uk-gc-reference.md §4
# respectively. The public BCIS £/m² bands are paywalled and MUST NOT be
# fabricated; do not add BCIS-tagged rows until they are read from a
# licensed source. See research/uk-gc-reference.md §4 for the rationale.
#
# Table shape:
#   BENCHMARK_TABLE[element_ref][building_type] = (low, high, source)
# with entries per building type; ``None`` means no defensible band exists
# for that combination.
# ---------------------------------------------------------------------------

_PLACEHOLDER = "placeholder"

BENCHMARK_TABLE: Dict[str, Dict[str, Tuple[float, float, str]]] = {
    # 2.8 Internal doors — nr per m² of GFA.
    "2.8": {
        "school":     (0.010, 0.020, _PLACEHOLDER),
        "office":     (0.008, 0.015, _PLACEHOLDER),
        "apartment":  (0.015, 0.030, _PLACEHOLDER),
        "industrial": (0.002, 0.006, _PLACEHOLDER),
        "healthcare": (0.020, 0.040, _PLACEHOLDER),
    },
    # 2.6 Windows and External Doors — split into two probes so we can flag
    # external-door counts and window counts independently. The lookup keys
    # embed a discriminator suffix.
    "2.6/external-doors": {
        "school":     (0.001, 0.003, _PLACEHOLDER),
        "office":     (0.001, 0.003, _PLACEHOLDER),
        "apartment":  (0.001, 0.003, _PLACEHOLDER),
        "industrial": (0.001, 0.005, _PLACEHOLDER),
        "healthcare": (0.001, 0.003, _PLACEHOLDER),
    },
    "2.6/windows": {
        "school":     (0.020, 0.040, _PLACEHOLDER),
        "office":     (0.015, 0.030, _PLACEHOLDER),
        "apartment":  (0.020, 0.050, _PLACEHOLDER),
        "industrial": (0.005, 0.015, _PLACEHOLDER),
        "healthcare": (0.020, 0.040, _PLACEHOLDER),
    },
    # 3.3 Ceiling area — m² per m².
    "3.3": {
        "school":     (0.85, 0.95, _PLACEHOLDER),
        "office":     (0.85, 0.95, _PLACEHOLDER),
        "apartment":  (0.80, 0.95, _PLACEHOLDER),
        "industrial": (0.60, 0.90, _PLACEHOLDER),
        "healthcare": (0.85, 0.95, _PLACEHOLDER),
    },
    # 1.1 Concrete volume — m³ per m² of GFA.
    "1.1": {
        "school":     (0.15, 0.30, _PLACEHOLDER),
        "office":     (0.20, 0.35, _PLACEHOLDER),
        "apartment":  (0.25, 0.45, _PLACEHOLDER),
        "industrial": (0.15, 0.25, _PLACEHOLDER),
        "healthcare": (0.25, 0.45, _PLACEHOLDER),
    },
    # 2.5 Blockwork/masonry — m² per m².
    "2.5": {
        "school":     (0.60, 1.20, _PLACEHOLDER),
        "office":     (0.40, 0.90, _PLACEHOLDER),
        "apartment":  (0.80, 1.50, _PLACEHOLDER),
        "industrial": (0.20, 0.60, _PLACEHOLDER),
        "healthcare": (0.70, 1.30, _PLACEHOLDER),
    },
}

# Profile → set of preferred sources. When a row is tagged with a source that
# matches, the range is used directly. Otherwise the row is used only if it
# is a placeholder (fallback).
PROFILE_PREFERRED_SOURCES: Dict[str, Tuple[str, ...]] = {
    "ireland-gc": ("SCSI", "Buildcost"),
    "uk-gc":      ("BCIS",),
}


# Item selectors — a small vocabulary for identifying which items feed each
# benchmark probe. Kept as functions so future tuning does not require
# touching the layer implementation.
def _is_internal_door(item: Dict[str, Any]) -> bool:
    return item.get("element_ref") == "2.8" and item.get("unit") == "nr"


def _is_external_door(item: Dict[str, Any]) -> bool:
    if item.get("element_ref") != "2.6" or item.get("unit") != "nr":
        return False
    subs = " ".join(item.get("sub_classifications") or []).lower()
    principal = (item.get("principal_item") or "").lower()
    return "external door" in subs or "external door" in principal

def _is_window(item: Dict[str, Any]) -> bool:
    if item.get("element_ref") != "2.6" or item.get("unit") != "nr":
        return False
    subs = " ".join(item.get("sub_classifications") or []).lower()
    principal = (item.get("principal_item") or "").lower()
    if "window" in subs or "window" in principal:
        return True
    # If nothing distinguishes internal vs external, treat as windows — the
    # benchmark table entry for windows is broader and will pick up most 2.6
    # items in the wild.
    return "external door" not in subs and "external door" not in principal


BENCHMARK_ITEM_SELECTORS = {
    "2.8":                  _is_internal_door,
    "2.6/external-doors":   _is_external_door,
    "2.6/windows":           _is_window,
    "3.3": lambda it: it.get("element_ref") == "3.3" and it.get("unit") == "m2",
    "1.1": lambda it: it.get("element_ref") == "1.1" and it.get("unit") == "m3",
    "2.5": lambda it: it.get("element_ref") == "2.5" and it.get("unit") == "m2",
}


# ---------------------------------------------------------------------------
# Time hook — deterministic when AILTIR_VALIDATE_STABLE_TIME=1.
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    if os.environ.get("AILTIR_VALIDATE_STABLE_TIME") == "1":
        return "1970-01-01T00:00:00+00:00"
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Small helpers.
# ---------------------------------------------------------------------------

def _pct_delta(actual: float, target: float) -> Optional[float]:
    if target == 0:
        return None
    return (actual - target) / target


def _empty_validation() -> Dict[str, Any]:
    return {
        "confidence": "HIGH",
        "review_required": False,
        "layer_results": {
            "internal_consistency": {"status": "pass", "checks": []},
            "benchmark_ratio": {
                "status": "pass",
                "expected_per_m2": None,
                "actual_per_m2": None,
                "delta_pct": None,
                "source": None,
            },
            "historical": {"status": "skipped", "delta_pct": None,
                           "comparator_project": None},
            "cross_drawing": {"status": "pass", "checks": []},
            "coverage_audit": {"status": "pass", "detail": None},
        },
        "sanity_flags": [],
        "notes": [],
    }


def _storey_of(item: Dict[str, Any]) -> str:
    return (item.get("location_qualifier") or "unknown").strip().lower()


def _sub_class_str(item: Dict[str, Any]) -> str:
    return " ".join(item.get("sub_classifications") or []).lower()


def _extract_first_float(text: str, tokens: Iterable[str]) -> Optional[float]:
    """Find the first number after any of the tokens (case-insensitive)."""
    lower = text.lower()
    for tok in tokens:
        idx = lower.find(tok)
        if idx < 0:
            continue
        tail = lower[idx + len(tok):]
        buf = ""
        started = False
        for ch in tail:
            if ch.isdigit() or ch == ".":
                buf += ch
                started = True
            elif started:
                break
        if buf:
            try:
                return float(buf)
            except ValueError:
                continue
    return None


# ---------------------------------------------------------------------------
# Layer 1 — Internal consistency
# ---------------------------------------------------------------------------

def _attach(validation_by_id: Dict[str, Dict[str, Any]], item_id: str,
            layer: str, check: Dict[str, Any]) -> None:
    v = validation_by_id[item_id]
    v["layer_results"][layer]["checks"].append(check)
    # promote worst status
    cur = v["layer_results"][layer]["status"]
    new = check["status"]
    order = {"pass": 0, "warn": 1, "fail": 2}
    if order.get(new, 0) > order.get(cur, 0):
        v["layer_results"][layer]["status"] = new


def layer1_internal_consistency(items: List[Dict[str, Any]],
                                validation_by_id: Dict[str, Dict[str, Any]]) -> None:
    """Run cross-item consistency checks and attach findings to each item."""

    # 1. Door count vs opening count in internal walls (element 2.8 vs 2.7).
    door_count = sum(float(it.get("quantity") or 0)
                     for it in items if _is_internal_door(it))
    opening_count = 0.0
    contributing_wall_ids: List[str] = []
    for it in items:
        if it.get("element_ref") == "2.7":
            n = _extract_first_float(_sub_class_str(it),
                                     ("door opening", "door openings"))
            if n is not None:
                opening_count += n
                contributing_wall_ids.append(it["id"])
    if door_count > 0 and opening_count > 0:
        delta = _pct_delta(door_count, opening_count)
        status = "pass" if delta is not None and abs(delta) <= TOL_DOOR_COUNT else "warn"
        check = {"name": "internal_doors_vs_wall_openings",
                 "status": status, "delta_pct": delta,
                 "detail": (f"doors={door_count:g}, wall openings={opening_count:g}, "
                            f"tol=±{TOL_DOOR_COUNT * 100:g}%")}
        touch_ids = [it["id"] for it in items if _is_internal_door(it)] + contributing_wall_ids
        for iid in touch_ids:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 2. Window count vs external-wall openings (2.6 windows vs 2.5).
    window_count = sum(float(it.get("quantity") or 0)
                       for it in items if _is_window(it))
    ext_opening_count = 0.0
    ext_wall_ids: List[str] = []
    for it in items:
        if it.get("element_ref") == "2.5":
            n = _extract_first_float(_sub_class_str(it),
                                     ("window opening", "openings"))
            if n is not None:
                ext_opening_count += n
                ext_wall_ids.append(it["id"])
    if window_count > 0 and ext_opening_count > 0:
        delta = _pct_delta(window_count, ext_opening_count)
        status = "pass" if delta is not None and abs(delta) <= TOL_WINDOW_COUNT else "warn"
        check = {"name": "windows_vs_external_wall_openings",
                 "status": status, "delta_pct": delta,
                 "detail": (f"windows={window_count:g}, ext openings={ext_opening_count:g}, "
                            f"tol=±{TOL_WINDOW_COUNT * 100:g}%")}
        touch_ids = [it["id"] for it in items if _is_window(it)] + ext_wall_ids
        for iid in touch_ids:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 3. Floor area consistency — sum 3.2 floor finishes per storey vs
    #    declared whole-floor items (1.1 ground slab / 2.2 upper floor).
    floor_finish_by_storey: Dict[str, float] = defaultdict(float)
    finish_ids_by_storey: Dict[str, List[str]] = defaultdict(list)
    for it in items:
        if it.get("element_ref") == "3.2" and it.get("unit") == "m2":
            s = _storey_of(it)
            floor_finish_by_storey[s] += float(it.get("quantity") or 0)
            finish_ids_by_storey[s].append(it["id"])
    whole_floor_by_storey: Dict[str, float] = defaultdict(float)
    whole_floor_ids: Dict[str, List[str]] = defaultdict(list)
    for it in items:
        if it.get("element_ref") in ("1.1", "2.2") and it.get("unit") == "m2":
            s = _storey_of(it)
            whole_floor_by_storey[s] += float(it.get("quantity") or 0)
            whole_floor_ids[s].append(it["id"])
    for storey, finish_area in floor_finish_by_storey.items():
        declared = whole_floor_by_storey.get(storey, 0.0)
        if declared <= 0 or finish_area <= 0:
            continue
        delta = _pct_delta(finish_area, declared)
        status = "pass" if delta is not None and abs(delta) <= TOL_FLOOR_AREA else "warn"
        check = {"name": f"floor_area_consistency[{storey}]",
                 "status": status, "delta_pct": delta,
                 "detail": (f"finishes={finish_area:g}m² vs declared={declared:g}m², "
                            f"tol=±{TOL_FLOOR_AREA * 100:g}%")}
        for iid in finish_ids_by_storey[storey] + whole_floor_ids[storey]:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 4. Wall length coherence per storey.
    wall_len_by_storey: Dict[str, float] = defaultdict(float)
    wall_ids_by_storey: Dict[str, List[str]] = defaultdict(list)
    for it in items:
        if it.get("element_ref") in ("2.5", "2.7") and it.get("unit") == "m":
            s = _storey_of(it)
            wall_len_by_storey[s] += float(it.get("quantity") or 0)
            wall_ids_by_storey[s].append(it["id"])
    declared_wall_len: Dict[str, float] = defaultdict(float)
    declared_wall_ids: Dict[str, List[str]] = defaultdict(list)
    for it in items:
        subs = _sub_class_str(it)
        if "wall length by storey" in subs or "declared wall length" in subs:
            s = _storey_of(it)
            declared_wall_len[s] += float(it.get("quantity") or 0)
            declared_wall_ids[s].append(it["id"])
    for storey, ln in wall_len_by_storey.items():
        declared = declared_wall_len.get(storey, 0.0)
        if declared <= 0 or ln <= 0:
            continue
        delta = _pct_delta(ln, declared)
        status = "pass" if delta is not None and abs(delta) <= TOL_WALL_LENGTH else "warn"
        check = {"name": f"wall_length_coherence[{storey}]",
                 "status": status, "delta_pct": delta,
                 "detail": (f"summed={ln:g}m vs declared={declared:g}m, "
                            f"tol=±{TOL_WALL_LENGTH * 100:g}%")}
        for iid in wall_ids_by_storey[storey] + declared_wall_ids[storey]:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 5. Ceiling area vs floor area per storey (unless voids declared).
    ceiling_by_storey: Dict[str, float] = defaultdict(float)
    ceiling_ids_by_storey: Dict[str, List[str]] = defaultdict(list)
    void_flag_by_storey: Dict[str, bool] = defaultdict(bool)
    for it in items:
        if it.get("element_ref") == "3.3" and it.get("unit") == "m2":
            s = _storey_of(it)
            ceiling_by_storey[s] += float(it.get("quantity") or 0)
            ceiling_ids_by_storey[s].append(it["id"])
            subs = _sub_class_str(it)
            if "void" in subs or "double height" in subs or "double-height" in subs:
                void_flag_by_storey[s] = True
    for storey, ca in ceiling_by_storey.items():
        floor_ref = whole_floor_by_storey.get(storey, 0.0) or floor_finish_by_storey.get(storey, 0.0)
        if floor_ref <= 0 or ca <= 0:
            continue
        if void_flag_by_storey.get(storey):
            continue
        delta = _pct_delta(ca, floor_ref)
        status = "pass" if delta is not None and abs(delta) <= TOL_CEILING_AREA else "warn"
        check = {"name": f"ceiling_area_vs_floor_area[{storey}]",
                 "status": status, "delta_pct": delta,
                 "detail": (f"ceiling={ca:g}m² vs floor={floor_ref:g}m², "
                            f"tol=±{TOL_CEILING_AREA * 100:g}%")}
        for iid in ceiling_ids_by_storey[storey]:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 6. Reinforcement vs concrete volume — grouped by location_qualifier or
    #    explicit assembly_of references. See research/nrm2-measurement.md §11.
    concrete_by_key: Dict[str, float] = defaultdict(float)
    concrete_ids_by_key: Dict[str, List[str]] = defaultdict(list)
    rebar_by_key: Dict[str, float] = defaultdict(float)
    rebar_ids_by_key: Dict[str, List[str]] = defaultdict(list)
    for it in items:
        er = it.get("element_ref") or ""
        # Consider concrete lines under element 1 (substructure) or 2.1 frame /
        # 2.2 upper floors with unit m³.
        if it.get("unit") == "m3" and (er.startswith("1") or er in ("2.1", "2.2")):
            key = _storey_of(it) + "|" + er
            concrete_by_key[key] += float(it.get("quantity") or 0)
            concrete_ids_by_key[key].append(it["id"])
        if it.get("unit") == "tonne" and ("reinforc" in (it.get("principal_item") or "").lower()
                                          or "rebar" in _sub_class_str(it)):
            # Rebar tonnes attach to the concrete they belong to via
            # location_qualifier plus (optionally) an assembly_of reference.
            key = _storey_of(it) + "|" + er
            rebar_by_key[key] += float(it.get("quantity") or 0)
            rebar_ids_by_key[key].append(it["id"])
            # Fallback: any assembly_of concrete keys.
            for parent in (it.get("assembly_of") or []):
                for it2 in items:
                    if it2.get("id") == parent and it2.get("unit") == "m3":
                        k2 = _storey_of(it2) + "|" + (it2.get("element_ref") or "")
                        rebar_by_key[k2] += float(it.get("quantity") or 0)
                        rebar_ids_by_key[k2].append(it["id"])
                        break
    for key, cvol in concrete_by_key.items():
        rebar_tonne = rebar_by_key.get(key, 0.0)
        if cvol <= 0 or rebar_tonne <= 0:
            continue
        kg_per_m3 = (rebar_tonne * 1000.0) / cvol
        if REBAR_WARN_LO_KG_PER_M3 <= kg_per_m3 <= REBAR_WARN_HI_KG_PER_M3:
            status = "pass"
        else:
            status = "warn"
        delta = _pct_delta(kg_per_m3, (REBAR_WARN_LO_KG_PER_M3 + REBAR_WARN_HI_KG_PER_M3) / 2.0)
        check = {"name": f"rebar_ratio[{key}]",
                 "status": status, "delta_pct": delta,
                 "detail": (f"{kg_per_m3:.1f} kg/m³ (band "
                            f"{REBAR_WARN_LO_KG_PER_M3:g}–{REBAR_WARN_HI_KG_PER_M3:g})")}
        for iid in concrete_ids_by_key[key] + rebar_ids_by_key[key]:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 7. Blockwork/brickwork area vs elevation area.
    masonry_area = 0.0
    masonry_ids: List[str] = []
    elevation_area = 0.0
    elevation_ids: List[str] = []
    for it in items:
        if it.get("element_ref") == "2.5" and it.get("unit") == "m2":
            masonry_area += float(it.get("quantity") or 0)
            masonry_ids.append(it["id"])
            ea = _extract_first_float(_sub_class_str(it),
                                      ("elevation area", "elevation"))
            if ea is not None:
                elevation_area += ea
                elevation_ids.append(it["id"])
    if masonry_area > 0 and elevation_area > 0:
        delta = _pct_delta(masonry_area, elevation_area)
        if masonry_area > elevation_area:
            status = "fail"
        else:
            status = "pass"
        check = {"name": "masonry_area_vs_elevation_area",
                 "status": status, "delta_pct": delta,
                 "detail": (f"masonry={masonry_area:g}m² vs elevation="
                            f"{elevation_area:g}m² "
                            "(masonry > elevation is impossible)")}
        for iid in masonry_ids:
            if iid in validation_by_id:
                _attach(validation_by_id, iid, "internal_consistency", check)

    # 8. Roof area vs footprint × secant(pitch).
    for it in items:
        if it.get("element_ref") != "2.3" or it.get("unit") != "m2":
            continue
        subs = _sub_class_str(it)
        pitch = _extract_first_float(subs, ("pitch", "roof pitch"))
        footprint = _extract_first_float(subs, ("footprint", "plan area"))
        if pitch is None or footprint is None or footprint <= 0:
            continue
        try:
            expected = footprint / math.cos(math.radians(pitch))
        except Exception:
            continue
        actual = float(it.get("quantity") or 0)
        if actual <= 0 or expected <= 0:
            continue
        delta = _pct_delta(actual, expected)
        status = "pass" if delta is not None and abs(delta) <= TOL_ROOF_AREA else "warn"
        check = {"name": "roof_slope_area_vs_footprint",
                 "status": status, "delta_pct": delta,
                 "detail": (f"actual={actual:g}m² vs footprint×sec(pitch)"
                            f"={expected:g}m², pitch={pitch:g}°")}
        _attach(validation_by_id, it["id"], "internal_consistency", check)


# ---------------------------------------------------------------------------
# Layer 2 — Benchmark ratios (profile-aware).
# ---------------------------------------------------------------------------

def benchmark_range(profile: str, building_type: Optional[str],
                    element_ref: str) -> Optional[Tuple[float, float, str]]:
    """Return (low, high, source) for the profile/building-type/element combo.

    Preference order:
      1. A row tagged with a source in ``PROFILE_PREFERRED_SOURCES[profile]``.
      2. A row tagged ``placeholder``.
    Returns ``None`` if no defensible band exists for the combination.
    """
    if not building_type:
        return None
    element = BENCHMARK_TABLE.get(element_ref)
    if not element:
        return None
    row = element.get(building_type)
    if not row:
        return None
    lo, hi, source = row
    preferred = PROFILE_PREFERRED_SOURCES.get(profile, ())
    # Currently every populated row is placeholder; when SCSI/BCIS rows are
    # added the same lookup will just work — a preferred-source row overrides.
    if source in preferred or source == _PLACEHOLDER:
        return (lo, hi, source)
    return None


def layer2_benchmark_ratio(items: List[Dict[str, Any]],
                           validation_by_id: Dict[str, Dict[str, Any]],
                           profile: str, building_type: Optional[str],
                           gfa: Optional[float],
                           summary_deltas: List[Dict[str, Any]],
                           summary_notes: List[str]) -> None:
    """Element-level benchmark ratios, flagged against the profile."""
    if not gfa or gfa <= 0:
        summary_notes.append(
            "Layer 2 skipped: GFA not provided; benchmark ratios require GFA."
        )
        return
    if not building_type:
        summary_notes.append(
            "Layer 2 skipped: --building-type not provided; benchmark ratios "
            "require a building-type column."
        )
        return

    for probe_key in sorted(BENCHMARK_TABLE.keys()):
        selector = BENCHMARK_ITEM_SELECTORS.get(probe_key)
        if selector is None:
            continue
        contributing = [it for it in items if selector(it)]
        if not contributing:
            continue
        band = benchmark_range(profile, building_type, probe_key)
        if band is None:
            per_item_note = {
                "status": "warn",
                "expected_per_m2": None,
                "actual_per_m2": None,
                "delta_pct": None,
                "source": None,
                "detail": (f"benchmark_missing for element {probe_key} / "
                           f"{building_type}"),
            }
            for it in contributing:
                v = validation_by_id[it["id"]]
                v["layer_results"]["benchmark_ratio"].update(per_item_note)
                v["notes"].append(
                    f"benchmark_missing: no {profile}/{building_type} band "
                    f"for {probe_key}"
                )
            continue
        lo, hi, source = band
        total = sum(float(it.get("quantity") or 0) for it in contributing)
        actual = total / gfa
        mid = (lo + hi) / 2.0
        half = (hi - lo) / 2.0
        # Delta relative to the nearest bound (0 inside band, signed outside).
        if lo <= actual <= hi:
            status = "pass"
            delta = 0.0
        else:
            if actual < lo:
                delta = _pct_delta(actual, lo)
            else:
                delta = _pct_delta(actual, hi)
            # Fail when the deviation exceeds half the mid-range.
            if half > 0 and abs(actual - mid) > BENCHMARK_FAIL_DEVIATION * mid:
                status = "fail"
            else:
                status = "warn"

        summary_deltas.append({
            "element_ref": probe_key,
            "actual_per_m2": actual,
            "expected_range": [lo, hi],
            "delta_pct": delta,
            "source": source,
        })

        per_item = {
            "status": status,
            "expected_per_m2": [lo, hi],
            "actual_per_m2": actual,
            "delta_pct": delta,
            "source": source,
        }
        for it in contributing:
            v = validation_by_id[it["id"]]
            v["layer_results"]["benchmark_ratio"] = per_item.copy()


# ---------------------------------------------------------------------------
# Layer 3 — Historical comparison (optional).
# ---------------------------------------------------------------------------

def _try_import_history_tool():
    """Best-effort loader for an MCP-registered history.lookup_takeoff.

    Returns a callable ``fn(project_id) -> comparator_dict`` or None. This
    layer never crashes the run — the try/except swallows every failure.
    """
    try:  # pragma: no cover - environment-specific
        import importlib
        for candidate in ("mcp_tools.history", "history_lookup_takeoff",
                          "ailtir_mcp.history"):
            try:
                mod = importlib.import_module(candidate)
            except Exception:
                continue
            fn = getattr(mod, "lookup_takeoff", None) or \
                 getattr(mod, "history_lookup_takeoff", None)
            if callable(fn):
                return fn
    except Exception:
        return None
    return None


def layer3_historical(items: List[Dict[str, Any]],
                      validation_by_id: Dict[str, Dict[str, Any]],
                      historical_project_id: Optional[str],
                      summary_historical: Dict[str, Any]) -> None:
    """Compare per-element totals to a historical comparator BoQ."""

    if not historical_project_id:
        summary_historical.update({
            "available": False,
            "note": ("Historical comparison skipped: no --historical-project-id "
                     "supplied."),
        })
        return

    fn = _try_import_history_tool()
    if fn is None:
        summary_historical.update({
            "available": False,
            "note": ("Historical comparison skipped: no history.lookup_takeoff "
                     "MCP tool registered."),
        })
        return

    try:
        comparator = fn(historical_project_id)
    except Exception as exc:
        summary_historical.update({
            "available": False,
            "note": (f"Historical comparison skipped: MCP tool raised "
                     f"{type(exc).__name__}: {exc}"),
        })
        return

    if not isinstance(comparator, dict) or "items" not in comparator:
        summary_historical.update({
            "available": False,
            "note": ("Historical comparison skipped: comparator payload lacks "
                     "an items list."),
        })
        return

    # Sum per-element quantities in the comparator.
    comp_totals: Dict[str, float] = defaultdict(float)
    for it in comparator.get("items", []):
        er = it.get("element_ref") or ""
        comp_totals[er] += float(it.get("quantity") or 0)

    our_totals: Dict[str, float] = defaultdict(float)
    for it in items:
        er = it.get("element_ref") or ""
        our_totals[er] += float(it.get("quantity") or 0)

    comparator_name = comparator.get("project", {}).get("name") or historical_project_id
    summary_historical.update({
        "available": True,
        "note": f"Historical comparison against {comparator_name}.",
    })

    for it in items:
        er = it.get("element_ref") or ""
        ours = our_totals.get(er, 0.0)
        theirs = comp_totals.get(er, 0.0)
        if theirs <= 0 or ours <= 0:
            continue
        delta = _pct_delta(ours, theirs)
        if delta is None:
            continue
        adelta = abs(delta)
        if adelta <= 0.25:
            status = "pass"
        elif adelta <= 0.50:
            status = "warn"
        else:
            status = "fail"
        validation_by_id[it["id"]]["layer_results"]["historical"] = {
            "status": status,
            "delta_pct": delta,
            "comparator_project": comparator_name,
        }


# ---------------------------------------------------------------------------
# Layer 4 — Cross-drawing verification.
# ---------------------------------------------------------------------------

_SCHEDULE_TOKENS = ("schedule", "sched")

def _is_schedule_sheet(ref: str) -> bool:
    r = (ref or "").lower()
    if any(tok in r for tok in _SCHEDULE_TOKENS):
        return True
    # ISO 19650 sheet-numbering convention: schedules live in the 9xx block.
    # Match a trailing three-digit segment 900–999.
    import re
    return bool(re.search(r"-9\d{2}(?:$|[^0-9])", r))


def layer4_cross_drawing(items: List[Dict[str, Any]],
                         drawing_set: List[str],
                         validation_by_id: Dict[str, Dict[str, Any]]) -> None:
    """Compare plan counts to schedule-sheet counts for the same element."""

    # Group nr-unit items by (element_ref, source_sheet).
    by_element_sheet: Dict[Tuple[str, str], float] = defaultdict(float)
    ids_by_element_sheet: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    for it in items:
        if it.get("unit") != "nr":
            continue
        sheet = it.get("source_sheet") or ""
        er = it.get("element_ref") or ""
        if not sheet or not er:
            continue
        by_element_sheet[(er, sheet)] += float(it.get("quantity") or 0)
        ids_by_element_sheet[(er, sheet)].append(it["id"])

    # Group by element_ref across sheets for a totals view.
    plan_totals: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for (er, sheet), total in by_element_sheet.items():
        plan_totals[er].append((sheet, total))

    schedule_sheets = [s for s in drawing_set if _is_schedule_sheet(s)]

    for er, entries in plan_totals.items():
        # Sum plan totals for this element across non-schedule sheets.
        plan_sheets = [e for e in entries if not _is_schedule_sheet(e[0])]
        if not plan_sheets:
            continue
        plan_sum = sum(x[1] for x in plan_sheets)
        # Look for a schedule count for the same element.
        schedule_hits = [e for e in entries if _is_schedule_sheet(e[0])]
        if not schedule_hits and not schedule_sheets:
            # No schedule sheet at all — pass with a note (see spec).
            for _, ids in ((s, ids_by_element_sheet[(er, s)]) for s, _ in plan_sheets):
                for iid in ids:
                    v = validation_by_id[iid]
                    v["layer_results"]["cross_drawing"]["checks"].append({
                        "sheet_a": ",".join(s for s, _ in plan_sheets),
                        "sheet_b": None,
                        "count_a": int(plan_sum),
                        "count_b": None,
                        "delta_pct": None,
                        "detail": "no schedule sheet found",
                    })
            continue

        # If our items didn't include the schedule sheet directly, we assume
        # the schedule count is not available at the JSON level and only flag
        # when there is a genuine mismatch across plan sheets themselves —
        # this covers "sheet_a says 12 doors, sheet_b says 15 doors".
        if schedule_hits:
            sched_sum = sum(x[1] for x in schedule_hits)
            sheet_a = ",".join(s for s, _ in plan_sheets)
            sheet_b = ",".join(s for s, _ in schedule_hits)
            if plan_sum >= CROSS_DRAWING_EXACT_UNDER:
                tol_ok = abs(plan_sum - sched_sum) / max(sched_sum, 1e-9) \
                         <= CROSS_DRAWING_TOL
            else:
                tol_ok = plan_sum == sched_sum
            status = "pass" if tol_ok else "warn"
            delta = _pct_delta(plan_sum, sched_sum) if sched_sum > 0 else None
            check = {"sheet_a": sheet_a, "sheet_b": sheet_b,
                     "count_a": int(plan_sum), "count_b": int(sched_sum),
                     "delta_pct": delta,
                     "detail": (f"plan-vs-schedule count for element {er} "
                                f"(tol=±{CROSS_DRAWING_TOL * 100:g}% ≥10, "
                                "exact <10)")}
            touch = []
            for s, _ in plan_sheets + schedule_hits:
                touch.extend(ids_by_element_sheet.get((er, s), []))
            for iid in touch:
                v = validation_by_id[iid]
                v["layer_results"]["cross_drawing"]["checks"].append(check)
                cur = v["layer_results"]["cross_drawing"]["status"]
                order = {"pass": 0, "warn": 1, "fail": 2}
                if order.get(status, 0) > order.get(cur, 0):
                    v["layer_results"]["cross_drawing"]["status"] = status


# ---------------------------------------------------------------------------
# Layer 5 — Coverage audit against NRM1 element structure.
# ---------------------------------------------------------------------------

def _element_top(item: Dict[str, Any]) -> str:
    er = (item.get("element_ref") or "").strip()
    if not er:
        return ""
    # NRM1 uses top-level codes 0..8 and a preliminaries group. See §1.
    if er.lower().startswith("prelim"):
        return "prelims"
    top = er.split(".")[0]
    return top


def layer5_coverage_audit(items: List[Dict[str, Any]], scope_type: str,
                          summary: Dict[str, Any]) -> bool:
    """Populate ``summary['coverage_gaps']`` and return True if a hard fail
    was raised (a ``required`` element is missing for a new-build scope)."""
    matrix = COVERAGE_MATRIX.get(scope_type)
    if matrix is None:
        summary["coverage_gaps"] = []
        return False
    present_top = {_element_top(it) for it in items if _element_top(it)}
    # Preliminaries can be booked either under a "prelims" pseudo-code or
    # NRM2 Section 1 (see research/nrm2-measurement.md §8) — accept both.
    if any(_element_top(it) == "prelims" for it in items):
        present_top.add("prelims")

    gaps: List[Dict[str, Any]] = []
    hard_fail = False
    for er in sorted(matrix.keys(), key=lambda k: (k != "prelims", k)):
        rule = matrix[er]
        is_present = er in present_top
        severity: str
        if rule == "not-expected":
            if is_present:
                severity = "warn"
                gaps.append({"element_ref": er,
                             "element_name": NRM1_ELEMENT_NAMES.get(er, er),
                             "expected": False, "present": True,
                             "severity": severity})
            continue
        if rule == "required":
            expected = True
        elif rule == "optional":
            expected = False
        elif rule == "required-if-below-DPC":
            expected = True  # conservative default
        else:
            expected = False

        if is_present:
            # No gap; only emit an entry when an unusual condition applies.
            continue
        if rule == "required":
            severity = "fail"
            if scope_type == "new-build":
                hard_fail = True
        elif rule == "optional":
            severity = "info"
        elif rule == "required-if-below-DPC":
            severity = "warn"
        else:
            severity = "info"
        gaps.append({"element_ref": er,
                     "element_name": NRM1_ELEMENT_NAMES.get(er, er),
                     "expected": expected, "present": False,
                     "severity": severity})

    summary["coverage_gaps"] = gaps

    # Attach an item-level touch: any item whose element is in a
    # warn/fail gap gets an audit note.
    return hard_fail


def annotate_items_from_gaps(items: List[Dict[str, Any]],
                             validation_by_id: Dict[str, Dict[str, Any]],
                             gaps: List[Dict[str, Any]]) -> None:
    warn_elements = {g["element_ref"] for g in gaps
                     if g["severity"] in ("warn", "fail")}
    for it in items:
        top = _element_top(it)
        if top in warn_elements:
            v = validation_by_id[it["id"]]
            v["layer_results"]["coverage_audit"] = {
                "status": "warn",
                "detail": (f"element {top} flagged by coverage audit "
                           f"(see validation_summary.coverage_gaps)"),
            }


# ---------------------------------------------------------------------------
# Sanity checks — envelope checks that populate ``sanity_flags``.
# ---------------------------------------------------------------------------

def run_sanity_checks(items: List[Dict[str, Any]],
                      validation_by_id: Dict[str, Dict[str, Any]],
                      gfa: Optional[float]) -> None:
    # Reinforcement ratios keyed for the harder sanity envelope.
    concrete_by_key: Dict[str, float] = defaultdict(float)
    rebar_by_key: Dict[str, float] = defaultdict(float)
    concrete_ids_by_key: Dict[str, List[str]] = defaultdict(list)
    rebar_ids_by_key: Dict[str, List[str]] = defaultdict(list)
    for it in items:
        er = it.get("element_ref") or ""
        if it.get("unit") == "m3" and (er.startswith("1") or er in ("2.1", "2.2")):
            key = _storey_of(it) + "|" + er
            concrete_by_key[key] += float(it.get("quantity") or 0)
            concrete_ids_by_key[key].append(it["id"])
        if it.get("unit") == "tonne" and ("reinforc" in (it.get("principal_item") or "").lower()
                                          or "rebar" in _sub_class_str(it)):
            key = _storey_of(it) + "|" + er
            rebar_by_key[key] += float(it.get("quantity") or 0)
            rebar_ids_by_key[key].append(it["id"])
    for key, cvol in concrete_by_key.items():
        rtonne = rebar_by_key.get(key, 0.0)
        if cvol <= 0 or rtonne <= 0:
            continue
        kg = (rtonne * 1000.0) / cvol
        if kg < REBAR_SANITY_LO_KG_PER_M3 or kg > REBAR_SANITY_HI_KG_PER_M3:
            flag = (f"reinforcement ratio {kg:.0f} kg/m³ outside sanity band "
                    f"{REBAR_SANITY_LO_KG_PER_M3:g}–{REBAR_SANITY_HI_KG_PER_M3:g}")
            for iid in concrete_ids_by_key[key] + rebar_ids_by_key[key]:
                if iid in validation_by_id:
                    validation_by_id[iid]["sanity_flags"].append(flag)

    # Concrete envelope: gfa × 4 m storey height × 0.6 upper bound per line.
    envelope_ceiling = None
    if gfa and gfa > 0:
        envelope_ceiling = 0.6 * gfa * ASSUMED_STOREY_HEIGHT_M

    # Elevation-area from external walls (for the window sanity check).
    elevation_area = 0.0
    for it in items:
        if it.get("element_ref") == "2.5" and it.get("unit") == "m2":
            ea = _extract_first_float(_sub_class_str(it),
                                      ("elevation area", "elevation"))
            if ea is not None:
                elevation_area += ea

    for it in items:
        v = validation_by_id[it["id"]]
        unit = it.get("unit")
        qty = it.get("quantity")

        # Unit is not in the canonical NRM2 list. See §11.
        if unit not in CANONICAL_UNITS:
            v["sanity_flags"].append(f"non-canonical unit '{unit}'")

        # Quantity validity.
        try:
            qval = float(qty)
        except (TypeError, ValueError):
            qval = None
        if unit == "nr":
            if qval is None or qval <= 0:
                v["sanity_flags"].append("nr item with zero/negative quantity")
            elif qval != int(qval):
                # NRM2 §11: enumerated items must have integer quantities.
                v["sanity_flags"].append(
                    f"fractional count on nr line ({qval})")

        # Door leaf width > 3 m (single leaf).
        if _is_internal_door(it) or (it.get("element_ref") == "2.6"
                                     and it.get("unit") == "nr"):
            subs = _sub_class_str(it)
            width_mm = _extract_first_float(subs, ("leaf width", "width"))
            if width_mm is not None:
                # If the number looks like millimetres (>10), convert.
                w_m = width_mm / 1000.0 if width_mm > 10 else width_mm
                if w_m > DOOR_LEAF_MAX_WIDTH_M and "double" not in subs \
                        and "leaves" not in subs:
                    v["sanity_flags"].append(
                        f"door width > {DOOR_LEAF_MAX_WIDTH_M:g} m ({w_m:g} m)"
                    )

        # Slab thickness < 100 mm on a structural slab.
        principal = (it.get("principal_item") or "").lower()
        if "slab" in principal and it.get("element_ref") in ("1.1", "2.2"):
            subs = _sub_class_str(it)
            t = _extract_first_float(subs, ("thickness",))
            if t is not None:
                t_mm = t if t > 10 else t * 1000.0
                if t_mm < STRUCTURAL_SLAB_MIN_MM:
                    v["sanity_flags"].append(
                        f"slab thickness < {STRUCTURAL_SLAB_MIN_MM:g} mm "
                        f"({t_mm:g} mm)"
                    )

        # Concrete volume exceeds plausible envelope on a single line.
        if envelope_ceiling is not None and unit == "m3" and qval is not None:
            if qval > envelope_ceiling:
                v["sanity_flags"].append(
                    "concrete volume exceeds plausible building envelope")

        # Window count on a single elevation > area / 0.5 m².
        if _is_window(it) and qval is not None and elevation_area > 0:
            max_windows = elevation_area / WINDOW_ELEVATION_AREA_PER_OPENING_M2
            if qval > max_windows:
                v["sanity_flags"].append(
                    f"window count exceeds elevation capacity "
                    f"({qval:g} > {max_windows:.0f})")


# ---------------------------------------------------------------------------
# Confidence scoring and adaptive threshold.
# ---------------------------------------------------------------------------

_LAYER1_WARN_DELTA_MEDIUM_MAX = 0.10  # a Layer 1 warn with |delta| ≤ 10%
_LAYER2_WARN_DELTA_MEDIUM_MAX = 0.25  # a Layer 2 warn with |delta| < 25%


def score_from_layer_results(layer_results: Dict[str, Any],
                             sanity_flags: List[str]) -> str:
    """Aggregate layer results into HIGH / MEDIUM / LOW. Pure function."""

    def status_of(layer: str) -> str:
        return layer_results.get(layer, {}).get("status", "pass")

    l1 = status_of("internal_consistency")
    l2 = status_of("benchmark_ratio")
    l3 = status_of("historical")
    l4 = status_of("cross_drawing")
    l5 = status_of("coverage_audit")

    # Count layers with warn or fail (skipped and pass count as neutral).
    non_pass_layers = [s for s in (l1, l2, l3, l4, l5)
                       if s in ("warn", "fail")]
    # Any layer 'fail' pushes to LOW.
    if any(s == "fail" for s in (l1, l2, l3, l4, l5)):
        return "LOW"
    if len(non_pass_layers) >= 2:
        return "LOW"
    if sanity_flags:
        return "LOW"
    if l3 == "warn" and (layer_results.get("historical", {}) or {}).get(
            "delta_pct") is not None:
        if abs(layer_results["historical"]["delta_pct"]) > 0.50:
            return "LOW"

    # Medium demotions.
    # Layer 2 warn with |delta| < 25%.
    l2_delta = layer_results.get("benchmark_ratio", {}).get("delta_pct")
    if l2 == "warn" and l2_delta is not None \
            and abs(l2_delta) < _LAYER2_WARN_DELTA_MEDIUM_MAX:
        return "MEDIUM"
    # Layer 4: exactly one cross-drawing mismatch.
    l4_checks = layer_results.get("cross_drawing", {}).get("checks", [])
    l4_warns = [c for c in l4_checks if c.get("delta_pct") is not None
                and c.get("detail") and (c.get("count_b") is not None)
                and c.get("delta_pct") not in (0, None)]
    if l4 == "warn" and len(l4_warns) == 1:
        return "MEDIUM"
    # Layer 1 single check with warn and delta ≤ 10%.
    l1_checks = layer_results.get("internal_consistency", {}).get("checks", [])
    warn_checks = [c for c in l1_checks if c.get("status") == "warn"
                   and c.get("delta_pct") is not None
                   and abs(c["delta_pct"]) <= _LAYER1_WARN_DELTA_MEDIUM_MAX]
    if l1 == "warn" and warn_checks:
        return "MEDIUM"

    if l1 == "warn" or l2 == "warn" or l4 == "warn":
        return "MEDIUM"

    return "HIGH"


def _intensifiers(item: Dict[str, Any], v: Dict[str, Any],
                  active: Dict[str, bool]) -> bool:
    """Return True when at least one active intensifier applies."""
    if active.get("sanity", True) and v.get("sanity_flags"):
        return True
    if active.get("coverage_touch", True):
        if v["layer_results"].get("coverage_audit", {}).get("status") == "warn":
            return True
    if active.get("assembly_empty", True):
        assembly = item.get("assembly_of")
        if assembly is not None and len(assembly) == 0:
            return True
    return False


def _decide_review(item: Dict[str, Any], v: Dict[str, Any],
                   active: Dict[str, bool]) -> bool:
    if v["confidence"] == "LOW":
        return True
    if v["confidence"] == "MEDIUM" and _intensifiers(item, v, active):
        return True
    return False


def apply_adaptive_threshold(items: List[Dict[str, Any]],
                             validation_by_id: Dict[str, Dict[str, Any]],
                             band: Tuple[float, float]) -> Dict[str, Any]:
    """Tune review-queue population toward the ``band``. Pure over inputs."""
    lo, hi = band
    total = len(items)
    if total == 0:
        return {"target_band": [lo, hi], "initial_flagged_fraction": 0.0,
                "final_flagged_fraction": 0.0, "adjustments": 0}

    # 1. Score every item.
    for it in items:
        v = validation_by_id[it["id"]]
        v["confidence"] = score_from_layer_results(v["layer_results"],
                                                   v["sanity_flags"])

    # 2. Initial pass with all intensifiers active.
    active = {"sanity": True, "coverage_touch": True, "assembly_empty": True}
    flagged = 0
    for it in items:
        v = validation_by_id[it["id"]]
        v["review_required"] = _decide_review(it, v, active)
        if v["review_required"]:
            flagged += 1
    initial_fraction = flagged / total
    adjustments = 0

    # 3. Loosen if too many flags.
    loosen_order = ("assembly_empty", "coverage_touch", "sanity")
    for name in loosen_order:
        cur_fraction = sum(1 for it in items
                           if validation_by_id[it["id"]]["review_required"]) / total
        if cur_fraction <= hi:
            break
        active[name] = False
        for it in items:
            v = validation_by_id[it["id"]]
            v["review_required"] = _decide_review(it, v, active)
        adjustments += 1
        if adjustments >= MAX_ADAPTIVE_PASSES:
            break

    # 4. Tighten if too few flags — promote MEDIUM items ordered by |delta_pct|.
    for _ in range(MAX_ADAPTIVE_PASSES):
        cur_fraction = sum(1 for it in items
                           if validation_by_id[it["id"]]["review_required"]) / total
        if cur_fraction >= lo:
            break
        # Rank MEDIUM, currently-unflagged items by their largest |delta_pct|.
        candidates: List[Tuple[float, str]] = []
        for it in items:
            v = validation_by_id[it["id"]]
            if v["confidence"] != "MEDIUM" or v["review_required"]:
                continue
            deltas: List[float] = []
            for layer_name, layer in v["layer_results"].items():
                d = layer.get("delta_pct")
                if isinstance(d, (int, float)):
                    deltas.append(abs(d))
                for c in layer.get("checks", []) or []:
                    d2 = c.get("delta_pct")
                    if isinstance(d2, (int, float)):
                        deltas.append(abs(d2))
            score = max(deltas) if deltas else 0.0
            candidates.append((score, it["id"]))
        if not candidates:
            break
        candidates.sort(reverse=True)
        # Promote the top slice until we hit the low band (or run out).
        need = math.ceil(lo * total) - int(round(cur_fraction * total))
        for _, iid in candidates[:max(need, 1)]:
            validation_by_id[iid]["review_required"] = True
        adjustments += 1

    final_flagged = sum(1 for it in items
                        if validation_by_id[it["id"]]["review_required"])
    return {
        "target_band": [lo, hi],
        "initial_flagged_fraction": initial_fraction,
        "final_flagged_fraction": final_flagged / total,
        "adjustments": adjustments,
    }


# ---------------------------------------------------------------------------
# Orchestration.
# ---------------------------------------------------------------------------

def validate_boq(boq: Dict[str, Any], profile: str,
                 building_type: Optional[str], gfa: Optional[float],
                 historical_project_id: Optional[str],
                 flag_band: Tuple[float, float]) -> Tuple[Dict[str, Any], bool]:
    """Return (enriched_boq, hard_fail)."""

    project = boq.get("project") or {}
    items: List[Dict[str, Any]] = list(boq.get("items") or [])
    # Bit-for-bit preservation: we deep-copy the input, then annotate.
    output = copy.deepcopy(boq)
    out_items = output.get("items") or []

    # id -> validation block. Attach immediately so layers can annotate.
    validation_by_id: Dict[str, Dict[str, Any]] = {}
    for it in out_items:
        it["validation"] = _empty_validation()
        validation_by_id[it["id"]] = it["validation"]

    summary_notes: List[str] = []
    summary_deltas: List[Dict[str, Any]] = []
    summary_historical: Dict[str, Any] = {"available": False, "note": ""}

    layer1_internal_consistency(out_items, validation_by_id)
    layer2_benchmark_ratio(out_items, validation_by_id, profile, building_type,
                           gfa, summary_deltas, summary_notes)
    layer3_historical(out_items, validation_by_id, historical_project_id,
                      summary_historical)

    drawing_set = ((project.get("source") or {}).get("drawing_set") or [])
    layer4_cross_drawing(out_items, drawing_set, validation_by_id)

    scope_type = project.get("scope_type") or "new-build"
    top_summary: Dict[str, Any] = {"coverage_gaps": []}
    hard_fail = layer5_coverage_audit(out_items, scope_type, top_summary)
    annotate_items_from_gaps(out_items, validation_by_id,
                             top_summary["coverage_gaps"])

    run_sanity_checks(out_items, validation_by_id, gfa)

    threshold_report = apply_adaptive_threshold(
        out_items, validation_by_id, flag_band
    )

    # Totals.
    high = sum(1 for it in out_items if it["validation"]["confidence"] == "HIGH")
    medium = sum(1 for it in out_items if it["validation"]["confidence"] == "MEDIUM")
    low = sum(1 for it in out_items if it["validation"]["confidence"] == "LOW")
    flagged = sum(1 for it in out_items if it["validation"]["review_required"])
    total = len(out_items)

    output["validation_summary"] = {
        "profile": profile,
        "building_type": building_type,
        "gfa_m2": gfa,
        "totals": {
            "items": total,
            "high": high,
            "medium": medium,
            "low": low,
            "flagged": flagged,
            "flagged_fraction": (flagged / total) if total else 0.0,
        },
        "coverage_gaps": top_summary["coverage_gaps"],
        "benchmark_deltas": summary_deltas,
        "historical": summary_historical,
        "threshold_adjustment": threshold_report,
        "notes": summary_notes,
        "generated_at": _now_iso(),
    }
    return output, hard_fail


# ---------------------------------------------------------------------------
# --report renderer.
# ---------------------------------------------------------------------------

def render_report(summary: Dict[str, Any]) -> str:
    tot = summary["totals"]
    lines = []
    lines.append("=== Ailtir validate.py — summary ===")
    lines.append(
        f"profile={summary['profile']} building_type={summary['building_type']} "
        f"gfa={summary['gfa_m2']}"
    )
    lines.append(
        f"items={tot['items']} HIGH={tot['high']} MEDIUM={tot['medium']} "
        f"LOW={tot['low']} flagged={tot['flagged']} "
        f"({tot['flagged_fraction'] * 100:.1f}%)"
    )
    lines.append("--- coverage gaps ---")
    for g in summary["coverage_gaps"]:
        lines.append(
            f"  [{g['severity']}] {g['element_ref']} "
            f"{g['element_name']} expected={g['expected']} present={g['present']}"
        )
    lines.append("--- top-5 benchmark deltas ---")
    sorted_deltas = sorted(summary["benchmark_deltas"],
                           key=lambda d: abs(d.get("delta_pct") or 0),
                           reverse=True)[:5]
    for d in sorted_deltas:
        delta_pct = d.get("delta_pct") or 0
        lo, hi = d["expected_range"]
        lines.append(
            f"  {d['element_ref']}: actual={d['actual_per_m2']:.4f} "
            f"expected=[{lo:g},{hi:g}] delta={delta_pct * 100:+.1f}% "
            f"src={d['source']}"
        )
    thr = summary["threshold_adjustment"]
    lines.append(
        f"--- adaptive threshold: band={thr['target_band']} "
        f"initial={thr['initial_flagged_fraction'] * 100:.1f}% "
        f"final={thr['final_flagged_fraction'] * 100:.1f}% "
        f"passes={thr['adjustments']}"
    )
    if summary.get("notes"):
        lines.append("--- notes ---")
        for n in summary["notes"]:
            lines.append(f"  {n}")
    lines.append(f"historical: available={summary['historical']['available']} "
                 f"— {summary['historical']['note']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="validate.py",
        description="Quality-gate the NRM2-aligned BoQ JSON emitted by "
                    "assembly_engine.py.",
    )
    p.add_argument("boq_path", help="Input BoQ JSON path.")
    p.add_argument("-o", "--output", default=None,
                   help="Output JSON path. Defaults to <input>.validated.json.")
    p.add_argument("--profile", choices=("ireland-gc", "uk-gc"),
                   default="ireland-gc",
                   help="Benchmark profile: SCSI/Buildcost for Ireland, "
                        "BCIS for UK.")
    p.add_argument("--building-type", default=None,
                   help="Building type column of the benchmark table "
                        "(school | office | apartment | industrial | healthcare).")
    p.add_argument("--gfa", type=float, default=None,
                   help="Gross Floor Area in m². Falls back to "
                        "project.gfa_m2 in the input JSON.")
    p.add_argument("--historical-project-id", default=None,
                   help="Project id for the MCP history.lookup_takeoff tool "
                        "(silently skipped if the tool is not registered).")
    p.add_argument("--target-flag-min", type=float,
                   default=DEFAULT_FLAG_BAND_MIN,
                   help="Lower bound of the flagged-fraction band "
                        f"(default {DEFAULT_FLAG_BAND_MIN}).")
    p.add_argument("--target-flag-max", type=float,
                   default=DEFAULT_FLAG_BAND_MAX,
                   help="Upper bound of the flagged-fraction band "
                        f"(default {DEFAULT_FLAG_BAND_MAX}).")
    p.add_argument("--report", action="store_true",
                   help="Print a stdout summary after writing the output.")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_arg_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        # argparse exits with 2 on parse errors; the spec asks for 3.
        return 3 if exc.code not in (0, None) else int(exc.code or 0)

    # CLI validation.
    if args.gfa is not None and args.gfa < 0:
        print("error: --gfa must be non-negative", file=sys.stderr)
        return 3
    if not (0.0 <= args.target_flag_min <= args.target_flag_max <= 1.0):
        print("error: --target-flag-min / --target-flag-max must satisfy "
              "0 <= min <= max <= 1", file=sys.stderr)
        return 3

    # Read input JSON.
    try:
        with open(args.boq_path, "r", encoding="utf-8") as fh:
            boq = json.load(fh)
    except FileNotFoundError:
        print(f"error: input JSON not found: {args.boq_path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: malformed JSON in {args.boq_path}: {exc}",
              file=sys.stderr)
        return 2

    if not isinstance(boq, dict) or "items" not in boq:
        print("error: BoQ JSON must have a top-level 'items' list.",
              file=sys.stderr)
        return 2

    project = boq.get("project") or {}
    building_type = args.building_type or project.get("building_type")
    profile = args.profile or project.get("profile") or "ireland-gc"
    gfa = args.gfa
    if gfa is None:
        raw_gfa = project.get("gfa_m2")
        try:
            gfa = float(raw_gfa) if raw_gfa is not None else None
        except (TypeError, ValueError):
            gfa = None

    band = (args.target_flag_min, args.target_flag_max)

    output, hard_fail = validate_boq(
        boq=boq,
        profile=profile,
        building_type=building_type,
        gfa=gfa,
        historical_project_id=args.historical_project_id,
        flag_band=band,
    )

    out_path = args.output
    if out_path is None:
        base, _ = os.path.splitext(args.boq_path)
        out_path = base + ".validated.json"
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)

    if args.report:
        print(render_report(output["validation_summary"]))

    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
