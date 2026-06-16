#!/usr/bin/env python3
"""
Assembly Engine — Primary to Secondary Quantity Derivation

This is the core of the QS methodology: measure a small set of primary quantities
directly from drawings, then derive complete bills of quantities using trade-specific
assembly definitions and industry ratios.

Professional QS firms work this way. This module encodes their methodology.

Assembly definitions are loaded from data/assemblies/*.json — editable by the user
to match their local conditions, rates, and preferences.
"""

import json
import math
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
ASSEMBLIES_DIR = DATA_DIR / "assemblies"


TRADE_TO_FILE = {
    "piling": "marine",
    "marine_furniture": "marine",
    "marine_structures": "marine",
    "rail": "marine",
    "dredging": "marine",
    "revetment": "marine",
    "fencing": "marine",
    "pavement": "marine",
    "coatings": "marine",
    "earthworks": "civil",
}


def load_assembly_file(trade):
    """Load assembly definitions for a trade.

    Args:
        trade: trade name (e.g., 'electrical', 'plumbing', 'piling', 'marine_furniture')

    Returns:
        dict with full assembly file contents
    """
    # Map trade names to assembly files (some trades share a file)
    file_trade = TRADE_TO_FILE.get(trade, trade)
    path = ASSEMBLIES_DIR / f"{file_trade}.json"
    if not path.exists():
        raise FileNotFoundError(f"Assembly file not found: {path} (trade={trade})")
    with open(path) as f:
        return json.load(f)


def load_waste_factors():
    """Load waste factor definitions."""
    path = DATA_DIR / "waste_factors.json"
    with open(path) as f:
        data = json.load(f)
    # Remove metadata key
    return {k: v for k, v in data.items() if not k.startswith("_")}


def get_waste_factor(waste_factors, trade, waste_key):
    """Look up a waste factor by trade and key.

    Args:
        waste_factors: dict from load_waste_factors()
        trade: trade name
        waste_key: specific waste key (e.g., 'cable', 'concrete_slab_on_ground')

    Returns:
        float waste factor (e.g., 0.05 for 5%) or 0.0 if not found
    """
    trade_factors = waste_factors.get(trade, {})
    return trade_factors.get(waste_key, 0.0)


def apply_waste(quantity, waste_factor):
    """Apply a waste factor to a quantity.

    Args:
        quantity: net quantity
        waste_factor: decimal factor (e.g., 0.05 for 5%)

    Returns:
        gross quantity with waste applied
    """
    return round(quantity * (1.0 + waste_factor), 2)


def derive_from_assembly(primary_qty, primary_unit, assembly_def, waste_factors, trade,
                          parameters=None, overrides=None):
    """Derive secondary quantities from a primary quantity using an assembly definition.

    Args:
        primary_qty: measured primary quantity (e.g., 24 GPOs, 150 M2 slab)
        primary_unit: unit of primary (EA, M2, LM, M3)
        assembly_def: single assembly dict from the trade file
        waste_factors: dict from load_waste_factors()
        trade: trade name for waste factor lookup
        parameters: optional dict of parameters (e.g., {"width_mm": 400, "depth_mm": 600})
        overrides: optional dict of ratio overrides {"item_name": new_ratio}

    Returns:
        list of dicts: [{"item": str, "quantity": float, "unit": str, "net_qty": float,
                         "waste_pct": float, "note": str, "method": str}]
    """
    if parameters is None:
        parameters = {}
    if overrides is None:
        overrides = {}

    results = []

    for secondary in assembly_def.get("secondaries", []):
        item_name = secondary["item"]
        unit = secondary["unit"]
        note = secondary.get("note", "")
        is_conditional = secondary.get("conditional", False)

        # Check for ratio override
        ratio = overrides.get(item_name, secondary.get("ratio"))

        # Handle formula-based ratios
        if ratio is None and "ratio_formula" in secondary:
            ratio = _evaluate_ratio_formula(
                secondary["ratio_formula"], primary_qty, parameters, assembly_def
            )

        if ratio is None:
            # Skip items where ratio can't be determined (e.g., formula with missing params)
            results.append({
                "item": item_name,
                "quantity": None,
                "unit": unit,
                "net_qty": None,
                "waste_pct": 0,
                "note": f"REQUIRES INPUT: {note}",
                "method": "manual_required",
                "conditional": is_conditional,
            })
            continue

        # Calculate net quantity
        net_qty = round(primary_qty * ratio, 2)

        # Apply waste factor
        waste_key = secondary.get("waste_key")
        waste_pct = 0.0
        if waste_key:
            waste_pct = get_waste_factor(waste_factors, trade, waste_key)

        gross_qty = apply_waste(net_qty, waste_pct)

        results.append({
            "item": item_name,
            "quantity": gross_qty,
            "unit": unit,
            "net_qty": net_qty,
            "waste_pct": round(waste_pct * 100, 1),
            "note": note,
            "method": "assembly_derivation",
            "conditional": is_conditional,
            "ratio_used": ratio,
        })

    return results


def _evaluate_ratio_formula(formula, primary_qty, parameters, assembly_def):
    """Evaluate a ratio formula string with available parameters.

    Supports simple formulas like:
    - "area_m2 * thickness_m" → uses primary_qty as area_m2
    - "concrete_m3 * rebar_kg_per_m3" → looks up rebar ratio from assembly file
    - Fixed numeric expressions

    Returns:
        float ratio, or None if parameters are missing
    """
    # Common parameter mappings
    p = parameters.copy()

    # Convert mm parameters to m
    for key in list(p.keys()):
        if key.endswith("_mm"):
            m_key = key.replace("_mm", "_m")
            p[m_key] = p[key] / 1000.0

    # Make primary quantity available under common names
    p["primary_qty"] = primary_qty
    p["area_m2"] = primary_qty  # When primary is area
    p["length_m"] = primary_qty  # When primary is length
    p["volume_m3"] = primary_qty  # When primary is volume

    # Add assembly-level data (like rebar ratios)
    if "rebar_kg_per_m3" in formula:
        rebar_key = parameters.get("rebar_element_type", "general_purpose")
        rebar_data = assembly_def.get("rebar_kg_per_m3", {}).get(rebar_key)
        if rebar_data:
            p["rebar_kg_per_m3"] = rebar_data.get("typical", 140)
        else:
            p["rebar_kg_per_m3"] = 140  # General purpose fallback

    # Handle default values from the assembly
    for key, val in assembly_def.items():
        if key.startswith("default_") and key not in p:
            clean_key = key.replace("default_", "")
            p[clean_key] = val

    # For secondaries that reference their own defaults
    if "thickness_m" not in p:
        # Check for default in assembly
        for sec in assembly_def.get("secondaries", []):
            if "default_thickness_m" in sec:
                p["thickness_m"] = sec["default_thickness_m"]
                break

    try:
        # Safe eval with only math operations and our parameters
        allowed = {**p, "math": math, "abs": abs, "round": round, "max": max, "min": min}
        result = eval(formula, {"__builtins__": {}}, allowed)
        return float(result) if result is not None else None
    except (NameError, TypeError, ZeroDivisionError):
        return None


def derive_all_quantities(primary_items, building_type=None):
    """Process a full list of primary quantities through the assembly engine.

    Args:
        primary_items: list of dicts with keys:
            - tag: str (e.g., "GPO", "L1")
            - description: str
            - trade: str (e.g., "electrical")
            - quantity: float
            - unit: str
            - assembly_type: str (key into trade's assemblies, e.g., "power_outlet")
            - parameters: dict (optional, for parametric assemblies)
            - drawing_ref: str (source drawing reference)
            - confidence: str (HIGH/MEDIUM/LOW)
        building_type: optional str for benchmark validation context

    Returns:
        dict with:
            - "primary_items": original primaries with assembly results attached
            - "all_quantities": flat list of all items (primary + secondary)
            - "summary_by_trade": dict of trade totals
    """
    waste_factors = load_waste_factors()
    all_quantities = []
    assembly_cache = {}

    for item in primary_items:
        trade = item["trade"]
        assembly_type = item.get("assembly_type")

        # Add the primary item itself
        primary_entry = {
            "item_type": "primary",
            "tag": item.get("tag", ""),
            "description": item["description"],
            "trade": trade,
            "quantity": item["quantity"],
            "unit": item["unit"],
            "drawing_ref": item.get("drawing_ref", ""),
            "confidence": item.get("confidence", "MEDIUM"),
            "method": item.get("method", "vector_extraction"),
            "note": "",
            "assembly_source": None,
        }
        all_quantities.append(primary_entry)

        # Derive secondaries if assembly type is specified
        if assembly_type:
            # Load assembly file (cached)
            if trade not in assembly_cache:
                try:
                    assembly_cache[trade] = load_assembly_file(trade)
                except FileNotFoundError:
                    continue

            trade_data = assembly_cache[trade]
            assemblies = trade_data.get("assemblies", {})

            if assembly_type in assemblies:
                assembly_def = assemblies[assembly_type]

                # Merge assembly-level data (like rebar ratios) into the assembly def for formula eval
                for key in trade_data:
                    if key not in ("trade", "assemblies") and key not in assembly_def:
                        assembly_def[key] = trade_data[key]

                secondaries = derive_from_assembly(
                    primary_qty=item["quantity"],
                    primary_unit=item["unit"],
                    assembly_def=assembly_def,
                    waste_factors=waste_factors,
                    trade=trade,
                    parameters=item.get("parameters", {}),
                    overrides=item.get("overrides", {}),
                )

                for sec in secondaries:
                    sec_entry = {
                        "item_type": "secondary",
                        "tag": "",
                        "description": sec["item"],
                        "trade": trade,
                        "quantity": sec["quantity"],
                        "unit": sec["unit"],
                        "drawing_ref": item.get("drawing_ref", ""),
                        "confidence": "MEDIUM" if sec["method"] == "assembly_derivation" else "LOW",
                        "method": sec["method"],
                        "note": sec["note"],
                        "net_qty": sec.get("net_qty"),
                        "waste_pct": sec.get("waste_pct", 0),
                        "assembly_source": f"{trade}/{assembly_type}",
                        "ratio_used": sec.get("ratio_used"),
                        "conditional": sec.get("conditional", False),
                    }
                    all_quantities.append(sec_entry)

    # Build summary by trade
    summary = {}
    for q in all_quantities:
        trade = q["trade"]
        if trade not in summary:
            summary[trade] = {"primary_count": 0, "secondary_count": 0, "items": []}
        if q["item_type"] == "primary":
            summary[trade]["primary_count"] += 1
        else:
            summary[trade]["secondary_count"] += 1

    return {
        "all_quantities": all_quantities,
        "summary_by_trade": summary,
        "total_items": len(all_quantities),
        "primary_count": sum(1 for q in all_quantities if q["item_type"] == "primary"),
        "secondary_count": sum(1 for q in all_quantities if q["item_type"] == "secondary"),
    }
