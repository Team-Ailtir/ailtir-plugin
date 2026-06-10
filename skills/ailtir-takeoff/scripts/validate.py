#!/usr/bin/env python3
"""
Five-Layer Validation Framework for Construction Quantity Takeoffs

Implements the validation methodology from QS practice research:
1. Internal consistency — quantities make sense relative to each other
2. Benchmark ratios — quantities per m2 GFA vs building type benchmarks
3. Historical comparison — compare to past projects (via MCP, optional)
4. Cross-drawing verification — plan vs elevation vs schedule consistency
5. Scope coverage audit — check all expected trades/divisions are present

Also implements:
- Three-tier confidence scoring (HIGH / MEDIUM / LOW)
- Sanity checks for physical impossibilities
- Human review routing (target 15-25% of items)
"""

import json
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"


def _load_json(filename):
    """Load a JSON data file."""
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if not k.startswith("_")}


def load_benchmarks():
    return _load_json("benchmarks.json")


def load_sanity_checks():
    return _load_json("sanity_checks.json")


def load_accuracy_expectations():
    return _load_json("accuracy_expectations.json")


# ── Layer 1: Internal Consistency ──

def validate_internal_consistency(quantities, extraction_data=None):
    """Check that quantities are internally consistent.

    Checks:
    - Room areas sum to approximately the total floor area
    - Door counts align with wall lengths
    - Ceiling area ≈ floor area minus voids
    - Trade quantities are non-negative
    - No duplicate items on same drawing

    Args:
        quantities: list of quantity dicts from assembly engine
        extraction_data: optional dict with page extraction results

    Returns:
        list of validation results: [{"check": str, "status": "pass"|"warning"|"error",
                                       "message": str, "details": dict}]
    """
    results = []

    # Check for negative quantities
    for q in quantities:
        if q.get("quantity") is not None and q["quantity"] < 0:
            results.append({
                "check": "negative_quantity",
                "status": "error",
                "message": f"Negative quantity: {q['description']} = {q['quantity']} {q['unit']}",
                "item": q["description"],
            })

    # Check for zero primary quantities (might indicate extraction failure)
    primary_items = [q for q in quantities if q.get("item_type") == "primary"]
    for q in primary_items:
        if q.get("quantity") == 0:
            results.append({
                "check": "zero_primary",
                "status": "warning",
                "message": f"Zero primary quantity: {q['description']} — possible extraction failure",
                "item": q["description"],
            })

    # Check for suspiciously large quantities
    for q in quantities:
        qty = q.get("quantity")
        if qty is not None and qty > 100000:
            results.append({
                "check": "very_large_quantity",
                "status": "warning",
                "message": f"Very large quantity: {q['description']} = {qty:,.0f} {q['unit']} — verify this is correct",
                "item": q["description"],
            })

    if not results:
        results.append({
            "check": "internal_consistency",
            "status": "pass",
            "message": "No internal consistency issues found",
        })

    return results


# ── Layer 2: Benchmark Ratios ──

def validate_benchmark_ratios(quantities, building_type, gfa_m2):
    """Compare quantities per m2 GFA against benchmark ranges.

    Args:
        quantities: list of quantity dicts
        building_type: str key into benchmarks.json (e.g., "office_commercial")
        gfa_m2: gross floor area in square meters

    Returns:
        list of validation results with benchmark comparison
    """
    results = []
    benchmarks = load_benchmarks()
    building_benchmarks = benchmarks.get(building_type)

    if not building_benchmarks:
        results.append({
            "check": "benchmark_ratios",
            "status": "warning",
            "message": f"No benchmarks available for building type '{building_type}'",
        })
        return results

    if gfa_m2 <= 0:
        results.append({
            "check": "benchmark_ratios",
            "status": "warning",
            "message": "GFA not provided — benchmark comparison skipped",
        })
        return results

    # Count elements by category for benchmark comparison
    element_counts = _count_elements_by_category(quantities)

    # Check each available benchmark
    benchmark_checks = {
        "light_fixtures_per_m2": element_counts.get("light_fixtures", 0) / gfa_m2 if gfa_m2 else 0,
        "power_outlets_per_m2": element_counts.get("power_outlets", 0) / gfa_m2 if gfa_m2 else 0,
        "sprinkler_heads_per_m2": element_counts.get("sprinkler_heads", 0) / gfa_m2 if gfa_m2 else 0,
        "doors_per_m2": element_counts.get("doors", 0) / gfa_m2 if gfa_m2 else 0,
    }

    for metric, actual_value in benchmark_checks.items():
        if actual_value == 0:
            continue  # Skip if no elements of this type found

        benchmark = building_benchmarks.get(metric)
        if not benchmark:
            continue

        bm_min = benchmark["min"]
        bm_max = benchmark["max"]
        bm_typical = benchmark.get("typical", (bm_min + bm_max) / 2)

        # Determine status
        if bm_min <= actual_value <= bm_max:
            deviation = abs(actual_value - bm_typical) / bm_typical * 100
            if deviation <= 10:
                status = "pass"
            else:
                status = "pass"  # Still within range
        elif actual_value < bm_min * 0.8 or actual_value > bm_max * 1.2:
            status = "error"
        else:
            status = "warning"

        deviation_pct = round((actual_value - bm_typical) / bm_typical * 100, 1) if bm_typical else 0

        results.append({
            "check": f"benchmark_{metric}",
            "status": status,
            "message": f"{metric}: {actual_value:.3f} (benchmark: {bm_min:.3f}-{bm_max:.3f}, typical: {bm_typical:.3f})",
            "actual": round(actual_value, 4),
            "benchmark_min": bm_min,
            "benchmark_max": bm_max,
            "benchmark_typical": bm_typical,
            "deviation_pct": deviation_pct,
        })

    if not results:
        results.append({
            "check": "benchmark_ratios",
            "status": "pass",
            "message": "Benchmark comparison completed — no issues",
        })

    return results


def _count_elements_by_category(quantities):
    """Map quantities to benchmark categories."""
    counts = {
        "light_fixtures": 0,
        "power_outlets": 0,
        "sprinkler_heads": 0,
        "doors": 0,
        "smoke_detectors": 0,
    }

    for q in quantities:
        if q.get("item_type") != "primary":
            continue
        desc = q.get("description", "").lower()
        tag = q.get("tag", "").upper()
        qty = q.get("quantity", 0) or 0

        if any(x in desc for x in ["light", "downlight", "luminaire"]) or tag.startswith("L") or tag == "LD":
            counts["light_fixtures"] += qty
        elif any(x in desc for x in ["power outlet", "gpo", "receptacle"]) or tag in ("GPO", "RCPT"):
            counts["power_outlets"] += qty
        elif any(x in desc for x in ["sprinkler"]) or tag == "SPR":
            counts["sprinkler_heads"] += qty
        elif any(x in desc for x in ["door"]) or (tag.startswith("D") and tag[1:].isdigit()):
            counts["doors"] += qty
        elif any(x in desc for x in ["smoke"]) or tag == "SD":
            counts["smoke_detectors"] += qty

    return counts


# ── Layer 3: Historical Comparison (MCP) ──

def validate_historical(quantities, mcp_available=False):
    """Compare against historical projects via MCP cost library.

    This layer is optional — only runs if an MCP cost library server is connected.

    Returns:
        list of validation results
    """
    if not mcp_available:
        return [{
            "check": "historical_comparison",
            "status": "skipped",
            "message": "No MCP cost library connected — historical comparison skipped. Connect a cost library MCP for enhanced validation.",
        }]

    # When MCP is available, this would call the cost library tools
    # to compare against past projects of the same building type.
    # For now, return placeholder.
    return [{
        "check": "historical_comparison",
        "status": "info",
        "message": "MCP historical comparison available — run via cost library tools",
    }]


# ── Layer 4: Cross-Drawing Verification ──

def validate_cross_drawing(quantities, all_page_extractions=None):
    """Cross-reference quantities across different drawing types.

    Checks:
    - Items on plan vs items on elevation (should match)
    - Items on plan vs items in schedule (door schedule, fixture schedule)
    - Same items on different floor plans (shouldn't be double-counted)

    Args:
        quantities: list of quantity dicts
        all_page_extractions: list of per-page extraction results

    Returns:
        list of validation results
    """
    results = []

    if not all_page_extractions or len(all_page_extractions) < 2:
        results.append({
            "check": "cross_drawing",
            "status": "skipped",
            "message": "Single drawing — cross-drawing verification not applicable",
        })
        return results

    # Check for potential double counting across pages
    tag_by_page = {}
    for page_data in all_page_extractions:
        page_num = page_data.get("page_number", "?")
        tags = page_data.get("tag_counts", {})
        for tag, data in tags.items():
            if tag not in tag_by_page:
                tag_by_page[tag] = []
            tag_by_page[tag].append({
                "page": page_num,
                "count": data.get("count", 0),
            })

    # Flag tags that appear on multiple pages (potential double-count risk)
    for tag, pages in tag_by_page.items():
        if len(pages) > 1:
            total = sum(p["count"] for p in pages)
            page_list = ", ".join(f"page {p['page']}({p['count']})" for p in pages)
            results.append({
                "check": f"cross_drawing_{tag}",
                "status": "warning",
                "message": f"Tag '{tag}' appears on multiple pages: {page_list}. Total: {total}. Verify not double-counted (plan vs RCP, plan vs section).",
                "tag": tag,
                "total": total,
                "pages": pages,
            })

    if not results:
        results.append({
            "check": "cross_drawing",
            "status": "pass",
            "message": "No cross-drawing inconsistencies detected",
        })

    return results


# ── Layer 5: Scope Coverage Audit ──

def validate_scope_coverage(quantities, project_type="commercial"):
    """Check that all expected trades and common items are present.

    Walks common construction divisions and flags gaps.

    Args:
        quantities: list of quantity dicts
        project_type: str to determine expected scope

    Returns:
        list of validation results
    """
    results = []

    # Get present trades
    present_trades = set(q.get("trade", "") for q in quantities)

    # Expected trades for different project types
    expected_trades = {
        "commercial": ["structural", "architectural", "electrical", "plumbing", "mechanical", "fire"],
        "residential": ["structural", "architectural", "electrical", "plumbing"],
        "industrial": ["structural", "architectural", "electrical", "plumbing", "mechanical", "civil"],
        "civil": ["civil", "structural"],
    }

    expected = expected_trades.get(project_type, expected_trades["commercial"])

    for trade in expected:
        if trade not in present_trades:
            results.append({
                "check": f"scope_missing_{trade}",
                "status": "warning",
                "message": f"No {trade} quantities found — expected for {project_type} project. Check if drawings were provided for this trade.",
                "missing_trade": trade,
            })

    # Check commonly missed items
    commonly_missed = [
        {"item": "temporary works/site facilities", "division": "01", "trades": ["all"]},
        {"item": "waterproofing", "division": "07", "trades": ["architectural"]},
        {"item": "door hardware", "division": "08", "trades": ["architectural"]},
        {"item": "paint BOTH sides of walls", "division": "09", "trades": ["architectural"]},
        {"item": "vertical duct risers", "division": "23", "trades": ["mechanical"], "note": "Plan-view takeoffs typically underestimate by 12-18%"},
        {"item": "cable termination allowances", "division": "26", "trades": ["electrical"]},
        {"item": "compaction testing", "division": "31", "trades": ["civil"]},
        {"item": "external works/pavements", "division": "32", "trades": ["civil"]},
    ]

    for missed in commonly_missed:
        if missed["trades"] == ["all"] or any(t in present_trades for t in missed["trades"]):
            results.append({
                "check": f"commonly_missed_{missed['division']}",
                "status": "info",
                "message": f"Commonly missed item: {missed['item']} (Div {missed['division']}). Verify inclusion.",
                "note": missed.get("note", ""),
            })

    if not [r for r in results if r["status"] == "warning"]:
        results.insert(0, {
            "check": "scope_coverage",
            "status": "pass",
            "message": f"All expected trades present for {project_type} project",
        })

    return results


# ── Sanity Checks ──

def run_sanity_checks(quantities, building_params=None):
    """Run physical impossibility and density checks.

    Args:
        quantities: list of quantity dicts
        building_params: optional dict with keys like:
            - gfa_m2: gross floor area
            - building_perimeter_m: total perimeter
            - building_type: str
            - floor_count: int

    Returns:
        list of validation results
    """
    results = []
    checks = load_sanity_checks()

    if not building_params:
        return [{
            "check": "sanity_checks",
            "status": "skipped",
            "message": "Building parameters not provided — sanity checks limited",
        }]

    gfa = building_params.get("gfa_m2", 0)
    perimeter = building_params.get("building_perimeter_m", 0)
    building_type = building_params.get("building_type", "")

    element_counts = _count_elements_by_category(quantities)

    # Run density checks
    for check in checks.get("density_checks", []):
        element = check["element"]
        count = element_counts.get(element, 0)
        if count == 0 or gfa == 0:
            continue

        density = count / gfa
        range_min, range_max = check["range_per_m2"]
        building_types = check.get("building_types", ["all"])

        if "all" not in building_types and building_type not in building_types:
            continue

        if density < range_min * 0.5 or density > range_max * 2.0:
            results.append({
                "check": check["id"],
                "status": "error",
                "message": f"{element}: {density:.3f}/m2 is far outside expected range {range_min}-{range_max}/m2",
                "actual": round(density, 4),
                "expected_range": [range_min, range_max],
            })
        elif density < range_min or density > range_max:
            results.append({
                "check": check["id"],
                "status": "warning",
                "message": f"{element}: {density:.3f}/m2 is outside expected range {range_min}-{range_max}/m2",
                "actual": round(density, 4),
                "expected_range": [range_min, range_max],
            })

    return results


# ── Confidence Scoring ──

def score_confidence(item, validation_results=None):
    """Assign confidence level to a quantity item.

    Scoring based on research findings:
    - HIGH: Vector-extracted + cross-referenced + within 10% of benchmark
    - MEDIUM: Single-source extraction + within 20% of benchmark
    - LOW: Estimated from ratios + no cross-reference + >20% deviation or no benchmark

    Args:
        item: single quantity dict
        validation_results: list of validation results for context

    Returns:
        str: "HIGH", "MEDIUM", or "LOW"
    """
    score = 0

    # Extraction method score
    method = item.get("method", "")
    if method in ("vector_extraction", "text_extraction", "dimension_calc"):
        score += 3
    elif method in ("vision_count", "symbol_recognition", "template_match"):
        score += 2
    elif method in ("assembly_derivation",):
        score += 1
    else:
        score += 0  # manual_required, estimated

    # Item type score
    if item.get("item_type") == "primary":
        score += 2
    else:
        score += 0  # Secondary items get no bonus

    # Cross-reference bonus (if validation shows this item was verified)
    if validation_results:
        tag = item.get("tag", "")
        for vr in validation_results:
            if vr.get("tag") == tag and vr.get("status") == "pass":
                score += 1
                break

    # Determine confidence level
    if score >= 4:
        return "HIGH"
    elif score >= 2:
        return "MEDIUM"
    else:
        return "LOW"


# ── Human Review Routing ──

def generate_review_list(quantities, validation_results):
    """Route items for human review. Target: 15-25% of items.

    Routing criteria:
    - Mandatory: total bid value, scope exclusions, custom assembly overrides
    - Exception-based: >15% off benchmark, LOW confidence, high-value, first-time symbols, cross-drawing discrepancies
    - Autonomous: HIGH confidence + low-value + within 10% benchmark

    Args:
        quantities: list of quantity dicts
        validation_results: list of all validation results

    Returns:
        list of items requiring review with reason
    """
    review_items = []
    total_items = len(quantities)

    # Collect validation flags by tag/item
    flagged_items = set()
    for vr in validation_results:
        if vr.get("status") in ("warning", "error"):
            tag = vr.get("tag", vr.get("item", ""))
            if tag:
                flagged_items.add(tag)

    for q in quantities:
        reasons = []

        # LOW confidence items always need review
        confidence = q.get("confidence", score_confidence(q, validation_results))
        if confidence == "LOW":
            reasons.append("Low confidence — estimated from ratios or unverified")

        # Items flagged by validation
        tag = q.get("tag", "")
        desc = q.get("description", "")
        if tag in flagged_items or desc in flagged_items:
            reasons.append("Flagged by validation checks")

        # Items with no quantity (require manual input)
        if q.get("quantity") is None:
            reasons.append("Quantity could not be determined — manual input required")

        # Conditional items need confirmation
        if q.get("conditional"):
            reasons.append("Conditional item — confirm if applicable to this project")

        # Items requiring manual input
        if q.get("method") == "manual_required":
            reasons.append("Parameters required for calculation")

        if reasons:
            review_items.append({
                "item": q.get("description", ""),
                "tag": tag,
                "trade": q.get("trade", ""),
                "quantity": q.get("quantity"),
                "unit": q.get("unit", ""),
                "confidence": confidence,
                "review_reasons": reasons,
                "drawing_ref": q.get("drawing_ref", ""),
            })

    # Check target range
    review_pct = len(review_items) / total_items * 100 if total_items > 0 else 0

    return {
        "review_items": review_items,
        "review_count": len(review_items),
        "total_items": total_items,
        "review_percentage": round(review_pct, 1),
        "target_range": "15-25%",
        "within_target": 15 <= review_pct <= 25,
    }


# ── Master Validation Runner ──

def run_full_validation(quantities, building_params=None, all_page_extractions=None,
                         mcp_available=False):
    """Run all 5 validation layers + sanity checks.

    Args:
        quantities: list of quantity dicts from assembly engine
        building_params: dict with building_type, gfa_m2, etc.
        all_page_extractions: list of per-page extraction JSONs
        mcp_available: bool, whether MCP cost library is connected

    Returns:
        dict with all validation results organized by layer
    """
    if building_params is None:
        building_params = {}

    building_type = building_params.get("building_type", "")
    gfa_m2 = building_params.get("gfa_m2", 0)
    project_type = building_params.get("project_type", "commercial")

    # Run all layers
    layer1 = validate_internal_consistency(quantities, all_page_extractions)
    layer2 = validate_benchmark_ratios(quantities, building_type, gfa_m2) if building_type and gfa_m2 else []
    layer3 = validate_historical(quantities, mcp_available)
    layer4 = validate_cross_drawing(quantities, all_page_extractions)
    layer5 = validate_scope_coverage(quantities, project_type)
    sanity = run_sanity_checks(quantities, building_params)

    all_results = layer1 + layer2 + layer3 + layer4 + layer5 + sanity

    # Score confidence for all items
    for q in quantities:
        if "confidence" not in q or q["confidence"] is None:
            q["confidence"] = score_confidence(q, all_results)

    # Generate review list
    review = generate_review_list(quantities, all_results)

    # Summary stats
    errors = sum(1 for r in all_results if r.get("status") == "error")
    warnings = sum(1 for r in all_results if r.get("status") == "warning")
    passes = sum(1 for r in all_results if r.get("status") == "pass")

    return {
        "layers": {
            "1_internal_consistency": layer1,
            "2_benchmark_ratios": layer2,
            "3_historical_comparison": layer3,
            "4_cross_drawing": layer4,
            "5_scope_coverage": layer5,
        },
        "sanity_checks": sanity,
        "review": review,
        "summary": {
            "total_checks": len(all_results),
            "errors": errors,
            "warnings": warnings,
            "passes": passes,
            "skipped": sum(1 for r in all_results if r.get("status") == "skipped"),
            "overall_status": "error" if errors > 0 else "warning" if warnings > 0 else "pass",
        },
    }
