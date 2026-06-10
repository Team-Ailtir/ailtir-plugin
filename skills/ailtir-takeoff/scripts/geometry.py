#!/usr/bin/env python3
"""
Geometry Analysis Layer for Construction Drawings

Reconstructs construction-relevant shapes from PyMuPDF raw path data.
PyMuPDF's get_drawings() returns Bezier curves, lines, and rectangles —
this module identifies circles, arcs, polylines, closed areas, and grid lines
from that raw data.

Key insight from research: PyMuPDF represents circles as 4 connected Bezier
curves. The maintainers confirmed they won't add shape detection, so we do it
here using control point ratio analysis.
"""

import math
from collections import defaultdict


# ── Constants ──

# For a circle approximated by 4 cubic Bezier curves, the control point
# distance from the endpoint along the tangent is (4/3) * tan(pi/8) ≈ 0.5523
BEZIER_CIRCLE_RATIO = 4.0 / 3.0 * math.tan(math.pi / 8.0)  # ≈ 0.5523
CIRCLE_TOLERANCE = 0.15  # Allow 15% deviation from ideal ratio
ENDPOINT_TOLERANCE_PTS = 2.0  # Points must be within 2pts to be "connected"


def distance(p1, p2):
    """Euclidean distance between two points."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def midpoint(p1, p2):
    """Midpoint between two points."""
    return ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)


def pts_to_mm(value_pts, scale_factor):
    """Convert PDF points to real-world millimeters given scale factor.
    PDF points are 1/72 inch. scale_factor is the drawing scale (e.g., 100 for 1:100).
    """
    mm_on_paper = value_pts * 25.4 / 72.0
    return mm_on_paper * scale_factor


def area_pts_to_m2(area_pts2, scale_factor):
    """Convert area in PDF points² to square meters."""
    mm2 = area_pts2 * (25.4 / 72.0) ** 2 * scale_factor ** 2
    return mm2 / 1_000_000.0


def length_pts_to_m(length_pts, scale_factor):
    """Convert length in PDF points to meters."""
    return pts_to_mm(length_pts, scale_factor) / 1000.0


# ── Shape Detection ──

def _extract_bezier_curves(drawing):
    """Extract cubic Bezier curve items from a drawing path."""
    curves = []
    for item in drawing.get("items", []):
        if item[0] == "c":  # cubic Bezier
            # item = ("c", p1, c1, c2, p2)
            curves.append({
                "p1": (item[1].x, item[1].y),
                "c1": (item[2].x, item[2].y),
                "c2": (item[3].x, item[3].y),
                "p2": (item[4].x, item[4].y),
            })
    return curves


def _is_circle_bezier_group(curves):
    """Check if a group of 4 connected Bezier curves forms a circle.

    For a circle, each Bezier curve's control points should be at a distance
    of BEZIER_CIRCLE_RATIO * radius from the endpoints, perpendicular to the
    radius at that point.
    """
    if len(curves) != 4:
        return None

    # Check connectivity: end of each curve connects to start of next
    for i in range(4):
        next_i = (i + 1) % 4
        if distance(curves[i]["p2"], curves[next_i]["p1"]) > ENDPOINT_TOLERANCE_PTS:
            return None

    # Collect all endpoints (which should lie on the circle)
    endpoints = [curves[i]["p1"] for i in range(4)]

    # Calculate candidate center as average of midpoints of opposite endpoints
    cx = sum(p[0] for p in endpoints) / 4
    cy = sum(p[1] for p in endpoints) / 4

    # Calculate distances from center to each endpoint
    radii = [distance((cx, cy), p) for p in endpoints]
    avg_radius = sum(radii) / len(radii)

    if avg_radius < 1.0:  # Too small to be meaningful
        return None

    # Check radius consistency
    for r in radii:
        if abs(r - avg_radius) / avg_radius > CIRCLE_TOLERANCE:
            return None

    # Verify control point distances match circle approximation
    for curve in curves:
        chord_len = distance(curve["p1"], curve["p2"])
        expected_cp_dist = chord_len * BEZIER_CIRCLE_RATIO / math.sqrt(2)

        cp1_dist = distance(curve["p1"], curve["c1"])
        cp2_dist = distance(curve["p2"], curve["c2"])

        # Allow generous tolerance for construction drawing precision
        if expected_cp_dist > 0:
            if abs(cp1_dist - expected_cp_dist) / expected_cp_dist > 0.3:
                return None
            if abs(cp2_dist - expected_cp_dist) / expected_cp_dist > 0.3:
                return None

    return {
        "center": (round(cx, 1), round(cy, 1)),
        "radius_pts": round(avg_radius, 1),
    }


def detect_circles(drawings):
    """Identify circles from groups of 4 connected Bezier curves in drawings.

    Args:
        drawings: list of drawing dicts from page.get_drawings()

    Returns:
        list of {"center": (x, y), "radius_pts": float, "drawing_index": int,
                 "color": tuple, "width": float}
    """
    circles = []

    for idx, drawing in enumerate(drawings):
        curves = _extract_bezier_curves(drawing)
        if len(curves) < 4:
            continue

        # Try groups of 4 consecutive curves
        for start in range(0, len(curves) - 3):
            group = curves[start:start + 4]
            result = _is_circle_bezier_group(group)
            if result:
                result["drawing_index"] = idx
                result["color"] = drawing.get("color", None)
                result["width"] = drawing.get("width", 0)
                result["fill"] = drawing.get("fill", None)
                circles.append(result)

    return circles


def detect_rectangles(drawings):
    """Identify rectangles from 4-line closed paths.

    Args:
        drawings: list of drawing dicts from page.get_drawings()

    Returns:
        list of {"rect": (x0, y0, x1, y1), "width_pts": float, "height_pts": float,
                 "area_pts2": float, "drawing_index": int}
    """
    rectangles = []

    for idx, drawing in enumerate(drawings):
        items = drawing.get("items", [])

        # Check for explicit rectangle items
        for item in items:
            if item[0] == "re":  # rectangle
                rect = item[1]
                w = abs(rect.width)
                h = abs(rect.height)
                if w > 5 and h > 5:  # Filter tiny rectangles
                    rectangles.append({
                        "rect": (round(rect.x0, 1), round(rect.y0, 1),
                                 round(rect.x1, 1), round(rect.y1, 1)),
                        "width_pts": round(w, 1),
                        "height_pts": round(h, 1),
                        "area_pts2": round(w * h, 1),
                        "drawing_index": idx,
                        "color": drawing.get("color", None),
                    })

        # Check for 4-line closed paths that form rectangles
        lines = [item for item in items if item[0] == "l"]
        if len(lines) == 4:
            points = []
            for line in lines:
                points.append((line[1].x, line[1].y))
            points.append((lines[-1][2].x, lines[-1][2].y))

            # Check if first point == last point (closed)
            if distance(points[0], points[-1]) < ENDPOINT_TOLERANCE_PTS:
                # Check for right angles
                xs = sorted(set(round(p[0], 0) for p in points[:4]))
                ys = sorted(set(round(p[1], 0) for p in points[:4]))
                if len(xs) == 2 and len(ys) == 2:
                    w = abs(xs[1] - xs[0])
                    h = abs(ys[1] - ys[0])
                    if w > 5 and h > 5:
                        rectangles.append({
                            "rect": (xs[0], ys[0], xs[1], ys[1]),
                            "width_pts": round(w, 1),
                            "height_pts": round(h, 1),
                            "area_pts2": round(w * h, 1),
                            "drawing_index": idx,
                            "color": drawing.get("color", None),
                        })

    return rectangles


def measure_polyline(drawing):
    """Sum segment lengths in a connected path.

    Args:
        drawing: single drawing dict from page.get_drawings()

    Returns:
        {"total_length_pts": float, "segments": int, "points": list}
    """
    items = drawing.get("items", [])
    total_length = 0.0
    segments = 0
    points = []

    for item in items:
        if item[0] == "l":  # line
            p1 = (item[1].x, item[1].y)
            p2 = (item[2].x, item[2].y)
            total_length += distance(p1, p2)
            segments += 1
            if not points:
                points.append(p1)
            points.append(p2)

    return {
        "total_length_pts": round(total_length, 1),
        "segments": segments,
        "points": points,
    }


def calculate_closed_area(points):
    """Calculate area of a closed polygon using the Shoelace formula.

    Args:
        points: list of (x, y) tuples forming a closed polygon

    Returns:
        Absolute area in PDF points squared
    """
    n = len(points)
    if n < 3:
        return 0.0

    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]

    return abs(area) / 2.0


def detect_closed_areas(drawings):
    """Find closed paths and calculate their areas.

    Args:
        drawings: list of drawing dicts from page.get_drawings()

    Returns:
        list of {"area_pts2": float, "boundary_points": list, "drawing_index": int,
                 "is_filled": bool, "color": tuple}
    """
    areas = []

    for idx, drawing in enumerate(drawings):
        items = drawing.get("items", [])
        if not items:
            continue

        # Check if path is closed (has closePath or first point == last point)
        lines = [item for item in items if item[0] == "l"]
        if len(lines) < 3:
            continue

        # Collect all points
        points = [(lines[0][1].x, lines[0][1].y)]
        for line in lines:
            points.append((line[2].x, line[2].y))

        # Check closure
        if distance(points[0], points[-1]) < ENDPOINT_TOLERANCE_PTS:
            area = calculate_closed_area(points[:-1])  # Exclude duplicate closing point
            if area > 100:  # Filter tiny areas (less than ~10pt x 10pt)
                areas.append({
                    "area_pts2": round(area, 1),
                    "boundary_points": [(round(p[0], 1), round(p[1], 1)) for p in points[:-1]],
                    "centroid": (
                        round(sum(p[0] for p in points[:-1]) / len(points[:-1]), 1),
                        round(sum(p[1] for p in points[:-1]) / len(points[:-1]), 1),
                    ),
                    "drawing_index": idx,
                    "is_filled": drawing.get("fill") is not None,
                    "color": drawing.get("color", None),
                    "fill_color": drawing.get("fill", None),
                })

    return areas


def classify_line(drawing):
    """Classify a line/path by its visual properties.

    Categories based on construction drawing conventions:
    - wall: thick (>1.5pt) + solid
    - dimension: thin + has tick marks or arrows
    - hidden: dashed
    - centerline: dash-dot (long-short-long pattern)
    - grid: thin + solid + long spans
    - lightweight: thin + solid (default)

    Args:
        drawing: single drawing dict from page.get_drawings()

    Returns:
        str: classification label
    """
    width = drawing.get("width", 0.5)
    dashes = drawing.get("dashes", None)
    color = drawing.get("color", (0, 0, 0))

    # Dashed patterns
    if dashes:
        dash_str = str(dashes)
        # Centerline: alternating long-short dashes
        if len(dashes) >= 4:
            return "centerline"
        # Hidden line: uniform short dashes
        if len(dashes) >= 2:
            return "hidden"

    # Solid lines — classify by width
    if width is None:
        width = 0
    if width > 1.5:
        return "wall"
    if width > 0.8:
        return "medium"

    return "lightweight"


def find_grid_lines(drawings, page_rect):
    """Detect structural grid lines (long parallel lines spanning most of the page).

    Grid lines are typically thin, extend most of the page width/height,
    and appear in parallel sets at regular spacing.

    Args:
        drawings: list of drawing dicts from page.get_drawings()
        page_rect: fitz.Rect for the page

    Returns:
        {"horizontal": list of y-positions, "vertical": list of x-positions,
         "spacing_h_pts": float or None, "spacing_v_pts": float or None}
    """
    page_w = page_rect.width
    page_h = page_rect.height
    min_span = 0.6  # Line must span at least 60% of page dimension

    h_lines = []  # Horizontal grid candidates (y positions)
    v_lines = []  # Vertical grid candidates (x positions)

    for drawing in drawings:
        for item in drawing.get("items", []):
            if item[0] != "l":
                continue

            p1 = (item[1].x, item[1].y)
            p2 = (item[2].x, item[2].y)
            dx = abs(p2[0] - p1[0])
            dy = abs(p2[1] - p1[1])
            length = distance(p1, p2)

            # Horizontal line (spans most of page width)
            if dy < 2 and dx > page_w * min_span:
                h_lines.append(round((p1[1] + p2[1]) / 2, 0))

            # Vertical line (spans most of page height)
            if dx < 2 and dy > page_h * min_span:
                v_lines.append(round((p1[0] + p2[0]) / 2, 0))

    # Deduplicate nearby lines (within 5pts)
    h_lines = _deduplicate_positions(sorted(h_lines), tolerance=5)
    v_lines = _deduplicate_positions(sorted(v_lines), tolerance=5)

    # Calculate spacing
    spacing_h = _calculate_spacing(h_lines)
    spacing_v = _calculate_spacing(v_lines)

    return {
        "horizontal": h_lines,
        "vertical": v_lines,
        "horizontal_count": len(h_lines),
        "vertical_count": len(v_lines),
        "spacing_h_pts": spacing_h,
        "spacing_v_pts": spacing_v,
    }


def _deduplicate_positions(positions, tolerance=5):
    """Remove duplicate positions within tolerance."""
    if not positions:
        return []
    result = [positions[0]]
    for pos in positions[1:]:
        if pos - result[-1] > tolerance:
            result.append(pos)
    return result


def _calculate_spacing(positions):
    """Calculate average spacing between sorted positions."""
    if len(positions) < 2:
        return None
    gaps = [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]
    return round(sum(gaps) / len(gaps), 1)


def analyze_drawings(drawings, page_rect, scale_factor=None):
    """Run full geometric analysis on a page's drawings.

    This is the main entry point. Calls all detection functions and returns
    a consolidated geometry analysis result.

    Args:
        drawings: list from page.get_drawings()
        page_rect: fitz.Rect for the page
        scale_factor: drawing scale (e.g., 100 for 1:100). If None, results are in PDF points only.

    Returns:
        dict with all geometry analysis results
    """
    circles = detect_circles(drawings)
    rectangles = detect_rectangles(drawings)
    closed_areas = detect_closed_areas(drawings)
    grid = find_grid_lines(drawings, page_rect)

    # Measure all polylines
    polylines = []
    for idx, drawing in enumerate(drawings):
        result = measure_polyline(drawing)
        if result["total_length_pts"] > 10:  # Filter very short paths
            result["drawing_index"] = idx
            result["classification"] = classify_line(drawing)
            result["color"] = drawing.get("color", None)
            result["width"] = drawing.get("width", 0)
            polylines.append(result)

    # Add real-world measurements if scale is known
    if scale_factor:
        for c in circles:
            c["radius_mm"] = round(pts_to_mm(c["radius_pts"], scale_factor), 0)
            c["diameter_mm"] = round(c["radius_mm"] * 2, 0)
        for r in rectangles:
            r["width_mm"] = round(pts_to_mm(r["width_pts"], scale_factor), 0)
            r["height_mm"] = round(pts_to_mm(r["height_pts"], scale_factor), 0)
            r["area_m2"] = round(area_pts_to_m2(r["area_pts2"], scale_factor), 2)
        for a in closed_areas:
            a["area_m2"] = round(area_pts_to_m2(a["area_pts2"], scale_factor), 2)
        for p in polylines:
            p["total_length_mm"] = round(pts_to_mm(p["total_length_pts"], scale_factor), 0)
            p["total_length_m"] = round(length_pts_to_m(p["total_length_pts"], scale_factor), 2)
        if grid["spacing_h_pts"]:
            grid["spacing_h_mm"] = round(pts_to_mm(grid["spacing_h_pts"], scale_factor), 0)
        if grid["spacing_v_pts"]:
            grid["spacing_v_mm"] = round(pts_to_mm(grid["spacing_v_pts"], scale_factor), 0)

    return {
        "circles": circles,
        "rectangles": rectangles,
        "closed_areas": closed_areas,
        "polylines": [p for p in polylines if p["total_length_pts"] > 50],  # Filter noise
        "grid_lines": grid,
        "summary": {
            "circles_found": len(circles),
            "rectangles_found": len(rectangles),
            "closed_areas_found": len(closed_areas),
            "polylines_found": len([p for p in polylines if p["total_length_pts"] > 50]),
            "grid_h": grid["horizontal_count"],
            "grid_v": grid["vertical_count"],
        },
    }
