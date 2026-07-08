"""Pure-math shape reconstruction over PyMuPDF drawing primitives.

Rebuilds higher-level construction-drawing shapes -- circles, arcs,
polylines, closed polygons and structural grid lines -- from the raw
line / cubic-Bezier / rectangle items returned by PyMuPDF's
``page.get_drawings()``. It exists because PyMuPDF's maintainers have
publicly and repeatedly declined to bundle shape-recognition inside the
library: their position (documented on the PyMuPDF issue tracker) is
that ``get_drawings()`` is a faithful projection of the PDF content
stream and that reconstructing semantically-meaningful shapes --
circles, arcs, closed rooms, structural grids -- is out-of-scope
downstream work. Every construction-tech tool that consumes vector
drawings therefore has to write this layer itself; this module is
Ailtir's canonical implementation of it.

Design rules:

* Standard library only (``math``, ``collections``, ``typing``). No
  PyMuPDF runtime import; only ``TYPE_CHECKING`` references.
* Every public function is pure: same input list -> same output list;
  no I/O, no globals, no mutation of the caller's dicts.
* Every list-shaped output is deterministically ordered by bbox
  top-left, so takeoff runs against the same PDF produce byte-identical
  intermediate JSON -- an Ailtir differentiator for audit trails.
* Fitted detections (circle, arc) carry a ``confidence`` score in
  ``[0.0, 1.0]`` so callers can gate on quality.

Public references (cited here, not in every function):

* PyMuPDF ``Page.get_drawings()`` -- raw-data source.
* Circle-to-cubic-Bezier constant ``kappa = (4/3) * tan(pi/8)``.
* Shoelace formula for polygon area.
* ``research/drawing-conventions.md`` -- scale conventions for
  ``points_to_metres``.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
)

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pymupdf  # noqa: F401

# ---- Module constants -----------------------------------------------------

#: kappa = (4/3) * tan(pi/8) ~= 0.5522847 -- cubic-Bezier control-point
#: offset (as a fraction of the radius) for a quarter-circle arc.
BEZIER_CIRCLE_RATIO: float = 4.0 * math.tan(math.pi / 8.0) / 3.0

#: Relative tolerance on the kappa match; absorbs PDF export rounding.
CIRCLE_TOLERANCE: float = 0.15

#: Points; endpoints closer than this are treated as coincident.
ENDPOINT_TOLERANCE_PTS: float = 2.0

#: Closed polygons smaller than this pt^2 are discarded (glyph noise).
MIN_CLOSED_AREA_PTS2: float = 100.0

#: Minimum grid-line length as a fraction of the shorter page side.
GRID_LINE_MIN_LENGTH_FRACTION: float = 0.35

#: Degrees of slack when classifying a line as horizontal or vertical.
GRID_ANGLE_TOLERANCE_DEG: float = 1.0

#: Relative stdev/mean below which grid spacings count as regular.
GRID_SPACING_TOLERANCE: float = 0.05

#: Relative tolerance for arc-Bezier perpendicular symmetry.
ARC_MIDPOINT_TOLERANCE: float = 0.10

Point = Tuple[float, float]
Shape = Dict[str, Any]
BBox = Tuple[float, float, float, float]

# ---- Coordinate / helper primitives --------------------------------------

def _as_point(value: Any) -> Point:
    """Return ``(x, y)`` floats for a PyMuPDF ``Point`` or a 2-tuple."""
    if value is None:
        raise TypeError("point value is None")
    if hasattr(value, "x") and hasattr(value, "y"):
        return float(value.x), float(value.y)
    try:
        x, y = value  # type: ignore[misc]
    except Exception as exc:  # noqa: BLE001
        raise TypeError(f"cannot interpret {value!r} as a 2D point") from exc
    return float(x), float(y)

def _as_rect(value: Any) -> BBox:
    """Return ``(x0, y0, x1, y1)`` for a PyMuPDF ``Rect`` or a 4-tuple."""
    if hasattr(value, "x0") and hasattr(value, "y1"):
        return float(value.x0), float(value.y0), float(value.x1), float(value.y1)
    try:
        x0, y0, x1, y1 = value
    except Exception as exc:  # noqa: BLE001
        raise TypeError(f"cannot interpret {value!r} as a rectangle") from exc
    return float(x0), float(y0), float(x1), float(y1)

def point_distance(p: Any, q: Any) -> float:
    """Euclidean distance between two 2D points (tuple or ``.x/.y`` object)."""
    px, py = _as_point(p)
    qx, qy = _as_point(q)
    return math.hypot(px - qx, py - qy)

def polygon_area(points: Iterable[Any]) -> float:
    """Absolute area of a simple polygon via the shoelace formula.

    A trailing duplicate closing vertex is tolerated. Fewer than three
    distinct points returns ``0.0``.
    """
    coords: List[Point] = [_as_point(pt) for pt in points]
    if len(coords) >= 2 and coords[0] == coords[-1]:
        coords = coords[:-1]
    if len(coords) < 3:
        return 0.0
    doubled = 0.0
    for i in range(len(coords)):
        x0, y0 = coords[i]
        x1, y1 = coords[(i + 1) % len(coords)]
        doubled += x0 * y1 - x1 * y0
    return abs(doubled) * 0.5

def points_to_metres(
    value_pts: float,
    scale_denominator: float,
    dpi: float = 72.0,
) -> float:
    """Convert a PDF-point length to metres at a drawing scale.

    ``value_pts * (25.4/dpi) * scale_denominator / 1000``. With the PDF
    native DPI of 72 this collapses to ``value_pts * 0.3528e-3 *
    scale_denominator``. See ``research/drawing-conventions.md`` for
    typical scales.

    Raises:
        ValueError: ``scale_denominator`` or ``dpi`` is not > 0.
    """
    if scale_denominator <= 0:
        raise ValueError(f"scale_denominator must be > 0, got {scale_denominator!r}")
    if dpi <= 0:
        raise ValueError(f"dpi must be > 0, got {dpi!r}")
    return value_pts * (25.4 / dpi) * scale_denominator / 1000.0

# ---- Path traversal -------------------------------------------------------

def _iter_valid_paths(drawings: Iterable[Any]) -> Iterator[Dict[str, Any]]:
    """Yield non-clip drawing paths from a ``get_drawings()`` result."""
    for path in drawings or []:
        if not isinstance(path, dict):
            continue
        if path.get("type") == "clip":
            continue
        yield path

def _iter_path_items(
    path: Dict[str, Any],
) -> Iterator[Tuple[str, Tuple[Any, ...]]]:
    """Yield well-formed geometry items from a single path dict."""
    for item in path.get("items") or ():
        if not item:
            continue
        op = item[0]
        try:
            if op == "l" and len(item) >= 3:
                p0 = _as_point(item[1])
                p1 = _as_point(item[2])
                if point_distance(p0, p1) == 0.0:
                    continue
                yield "line", (p0, p1)
            elif op == "c" and len(item) >= 5:
                p0 = _as_point(item[1])
                c1 = _as_point(item[2])
                c2 = _as_point(item[3])
                p1 = _as_point(item[4])
                if (
                    point_distance(p0, p1) == 0.0
                    and point_distance(p0, c1) == 0.0
                    and point_distance(p0, c2) == 0.0
                ):
                    continue
                yield "bezier", (p0, c1, c2, p1)
            elif op == "re" and len(item) >= 2:
                x0, y0, x1, y1 = _as_rect(item[1])
                if x0 == x1 or y0 == y1:
                    continue
                yield "rect", (x0, y0, x1, y1)
            # "qu" (quad) and unknown ops are ignored.
        except TypeError:
            # Malformed items are skipped so one bad path doesn't abort
            # a whole drawing's takeoff.
            continue

def iter_primitives(drawings: Iterable[Any]) -> Iterator[Tuple[str, Tuple[Any, ...]]]:
    """Flattened view of every well-formed line / bezier / rect item.

    Emits ``("line", (p0, p1))``, ``("bezier", (p0, c1, c2, p1))`` and
    ``("rect", (x0, y0, x1, y1))``. Zero-length and unknown items are
    silently skipped so downstream code can trust every tuple.
    """
    for path in _iter_valid_paths(drawings):
        for op, pts in _iter_path_items(path):
            yield op, pts

def _path_beziers(path: Dict[str, Any]) -> List[Tuple[Point, Point, Point, Point]]:
    """Return the cubic Beziers in a path, in item order."""
    result: List[Tuple[Point, Point, Point, Point]] = []
    for op, pts in _iter_path_items(path):
        if op == "bezier":
            result.append(pts)  # type: ignore[arg-type]
    return result

def _shape_bbox_key(shape: Shape) -> Tuple[float, float, float, float]:
    """Sort key: order shapes deterministically by bbox top-left."""
    x0, y0, x1, y1 = shape.get("bbox") or (0.0, 0.0, 0.0, 0.0)
    return (float(y0), float(x0), float(x1), float(y1))

def _bbox_from_points(points: Sequence[Point]) -> List[float]:
    """Axis-aligned bbox of a point sequence, or a zero bbox if empty."""
    if not points:
        return [0.0, 0.0, 0.0, 0.0]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]

# ---- Circle detection -----------------------------------------------------

def find_circles(
    drawings: Iterable[Any],
    *,
    tolerance: float = CIRCLE_TOLERANCE,
) -> List[Shape]:
    """Detect circles emitted as four-Bezier groups.

    A path with exactly four chained cubic Beziers whose control-point
    offsets all match ``BEZIER_CIRCLE_RATIO * r`` within ``tolerance``
    is a circle. Confidence linearly interpolates between the perfect
    match and the tolerance limit.
    """
    circles: List[Shape] = []
    for path in _iter_valid_paths(drawings):
        beziers = _path_beziers(path)
        if len(beziers) != 4:
            continue
        # Refuse mixed paths: four Beziers only, no interleaved lines.
        item_ops = [it[0] for it in (path.get("items") or ()) if it]
        if item_ops.count("c") != 4:
            continue

        # End-to-end chain check.
        chained = True
        for i in range(4):
            if point_distance(beziers[i][3], beziers[(i + 1) % 4][0]) > ENDPOINT_TOLERANCE_PTS:
                chained = False
                break
        if not chained:
            continue

        endpoints = [b[0] for b in beziers]
        cx = sum(pt[0] for pt in endpoints) / 4.0
        cy = sum(pt[1] for pt in endpoints) / 4.0
        radii = [point_distance((cx, cy), pt) for pt in endpoints]
        r_candidate = sum(radii) / 4.0
        if r_candidate <= 0.0:
            continue

        # Rule out ellipses: all four endpoint radii must agree.
        radius_dev = max(abs(rr - r_candidate) for rr in radii) / r_candidate
        if radius_dev > tolerance:
            continue

        expected = BEZIER_CIRCLE_RATIO * r_candidate
        max_dev = 0.0
        ok = True
        for p0, c1, c2, p1 in beziers:
            for d in (point_distance(p0, c1), point_distance(p1, c2)):
                dev = abs(d - expected) / expected
                if dev > tolerance:
                    ok = False
                    break
                if dev > max_dev:
                    max_dev = dev
            if not ok:
                break
        if not ok:
            continue

        confidence = max(0.0, min(1.0, 1.0 - (max_dev / tolerance)))
        circles.append(
            {
                "kind": "circle",
                "center": [cx, cy],
                "radius": r_candidate,
                "bbox": [
                    cx - r_candidate, cy - r_candidate,
                    cx + r_candidate, cy + r_candidate,
                ],
                "confidence": confidence,
            }
        )

    circles.sort(key=_shape_bbox_key)
    return circles

def _paths_claimed_by_circles(drawings: Iterable[Any]) -> set:
    """``id()`` of every path whose four Beziers chain end-to-end.

    Used to suppress arc detection on paths that circle-detection either
    accepted or considered. Overshooting a bit is safer than double-
    counting a circle as four arcs.
    """
    claimed: set = set()
    for path in _iter_valid_paths(drawings):
        beziers = _path_beziers(path)
        if len(beziers) != 4:
            continue
        chained = True
        for i in range(4):
            if point_distance(beziers[i][3], beziers[(i + 1) % 4][0]) > ENDPOINT_TOLERANCE_PTS:
                chained = False
                break
        if chained:
            claimed.add(id(path))
    return claimed

# ---- Arc detection --------------------------------------------------------

def find_arcs(
    drawings: Iterable[Any],
    *,
    tolerance: float = CIRCLE_TOLERANCE,
) -> List[Shape]:
    """Detect circular arcs emitted as single cubic Beziers.

    Requires the two control points to sit at equal-and-opposite
    perpendicular offsets from the chord midpoint (within
    ``ARC_MIDPOINT_TOLERANCE``); centre and radius are recovered from
    the sagitta relation. Arcs subtending < 5 or >= 355 degrees are
    dropped as noise / near-full circles respectively.
    """
    claimed = _paths_claimed_by_circles(drawings)
    arcs: List[Shape] = []
    for path in _iter_valid_paths(drawings):
        if id(path) in claimed:
            continue
        for bezier in _path_beziers(path):
            arc = _fit_bezier_arc(bezier, tolerance=tolerance)
            if arc is not None:
                arcs.append(arc)
    arcs.sort(key=_shape_bbox_key)
    return arcs

def _fit_bezier_arc(
    bezier: Tuple[Point, Point, Point, Point],
    *,
    tolerance: float,
) -> Optional[Shape]:
    """Return an arc dict fitted to one cubic Bezier, or ``None``."""
    p0, c1, c2, p3 = bezier
    chord_len = point_distance(p0, p3)
    if chord_len <= ENDPOINT_TOLERANCE_PTS:
        return None

    # Unit chord direction and perpendicular.
    dx = (p3[0] - p0[0]) / chord_len
    dy = (p3[1] - p0[1]) / chord_len
    nx, ny = -dy, dx

    off_c1 = (c1[0] - p0[0]) * nx + (c1[1] - p0[1]) * ny
    off_c2 = (c2[0] - p0[0]) * nx + (c2[1] - p0[1]) * ny
    if off_c1 == 0.0 and off_c2 == 0.0:
        return None
    if (off_c1 > 0.0) != (off_c2 > 0.0):
        return None
    avg_off = 0.5 * (abs(off_c1) + abs(off_c2))
    if avg_off <= 0.0:
        return None
    if abs(abs(off_c1) - abs(off_c2)) / avg_off > ARC_MIDPOINT_TOLERANCE:
        return None

    along_c1 = (c1[0] - p0[0]) * dx + (c1[1] - p0[1]) * dy
    along_c2 = (c2[0] - p0[0]) * dx + (c2[1] - p0[1]) * dy
    if not (0.0 <= along_c1 <= chord_len and 0.0 <= along_c2 <= chord_len):
        return None

    # Sagitta at t=1/2 of a cubic-Bezier arc is (3/4) * control offset.
    sagitta = (3.0 / 4.0) * avg_off
    if abs(sagitta) < 1e-9:
        return None
    half_chord = chord_len / 2.0
    radius = (half_chord * half_chord + sagitta * sagitta) / (2.0 * abs(sagitta))
    d_centre = radius - abs(sagitta)
    side = -1.0 if off_c1 > 0.0 else 1.0
    mid_x = 0.5 * (p0[0] + p3[0])
    mid_y = 0.5 * (p0[1] + p3[1])
    cx = mid_x + side * nx * d_centre
    cy = mid_y + side * ny * d_centre

    r0 = point_distance((cx, cy), p0)
    r1 = point_distance((cx, cy), p3)
    if radius <= 0.0:
        return None
    if abs(r0 - radius) / radius > tolerance or abs(r1 - radius) / radius > tolerance:
        return None

    start_angle = math.degrees(math.atan2(p0[1] - cy, p0[0] - cx)) % 360.0
    end_angle = math.degrees(math.atan2(p3[1] - cy, p3[0] - cx)) % 360.0
    subtended = (end_angle - start_angle) % 360.0
    if subtended < 1e-6:
        subtended = 360.0
    if subtended < 5.0 or subtended >= 355.0:
        return None

    offset_dev = abs(abs(off_c1) - abs(off_c2)) / avg_off
    confidence = max(0.0, min(1.0, 1.0 - (offset_dev / ARC_MIDPOINT_TOLERANCE)))

    return {
        "kind": "arc",
        "center": [cx, cy],
        "radius": radius,
        "start_angle_deg": start_angle,
        "end_angle_deg": end_angle,
        "chord": [[p0[0], p0[1]], [p3[0], p3[1]]],
        "bbox": _bbox_from_points([p0, p3]),
        "confidence": confidence,
    }

# ---- Polyline / closed-area reconstruction --------------------------------

def _quantise(pt: Point, tol: float) -> Tuple[int, int]:
    """Snap a point onto an integer grid keyed by ``tol``."""
    if tol <= 0.0:
        tol = ENDPOINT_TOLERANCE_PTS
    return (int(round(pt[0] / tol)), int(round(pt[1] / tol)))

def find_polylines(
    drawings: Iterable[Any],
    *,
    endpoint_tol: float = ENDPOINT_TOLERANCE_PTS,
) -> List[Shape]:
    """Chain connected line segments into open polylines.

    Endpoints are quantised onto an ``endpoint_tol``-spaced grid; greedy
    walks start at degree-1 nodes and follow degree-2 chains through the
    adjacency map. Closed loops are not returned here -- see
    ``find_closed_areas``.
    """
    return _chain_line_segments(drawings, endpoint_tol=endpoint_tol, include_closed=False)

def find_closed_areas(
    drawings: Iterable[Any],
    *,
    endpoint_tol: float = ENDPOINT_TOLERANCE_PTS,
    min_area: float = MIN_CLOSED_AREA_PTS2,
) -> List[Shape]:
    """Return closed polygons formed by connected line segments.

    Runs the same chaining as ``find_polylines`` but keeps only chains
    whose start / end coincide, computes area via ``polygon_area``, and
    discards anything smaller than ``min_area`` (typically glyph noise).
    """
    polylines = _chain_line_segments(drawings, endpoint_tol=endpoint_tol, include_closed=True)
    closed: List[Shape] = []
    for pl in polylines:
        if not pl.get("closed"):
            continue
        pts = [tuple(p) for p in pl["points"]]
        area = polygon_area(pts)
        if area < min_area:
            continue
        closed.append(
            {
                "kind": "closed_area",
                "points": [[p[0], p[1]] for p in pts],
                "area_pts2": area,
                "perimeter_pts": pl["length"],
                "bbox": pl["bbox"],
                "closed": True,
            }
        )
    closed.sort(key=_shape_bbox_key)
    return closed

def _chain_line_segments(
    drawings: Iterable[Any],
    *,
    endpoint_tol: float,
    include_closed: bool,
) -> List[Shape]:
    """Greedy end-to-end chaining shared by open / closed detectors."""
    segments: List[Tuple[Point, Point]] = []
    for op, pts in iter_primitives(drawings):
        if op != "line":
            continue
        p0, p1 = pts
        if point_distance(p0, p1) <= endpoint_tol:
            continue
        segments.append((p0, p1))
    if not segments:
        return []

    adjacency: Dict[Tuple[int, int], List[Tuple[int, Tuple[int, int]]]] = defaultdict(list)
    node_points: Dict[Tuple[int, int], Point] = {}
    seg_endpoints: List[Tuple[Tuple[int, int], Tuple[int, int]]] = []

    for seg_index, (p0, p1) in enumerate(segments):
        n0 = _quantise(p0, endpoint_tol)
        n1 = _quantise(p1, endpoint_tol)
        node_points.setdefault(n0, p0)
        node_points.setdefault(n1, p1)
        adjacency[n0].append((seg_index, n1))
        adjacency[n1].append((seg_index, n0))
        seg_endpoints.append((n0, n1))

    used = [False] * len(segments)

    def _walk(start_node: Tuple[int, int]) -> List[int]:
        chain: List[int] = []
        current = start_node
        while True:
            next_choice: Optional[Tuple[int, Tuple[int, int]]] = None
            for seg_index, other in adjacency[current]:
                if not used[seg_index]:
                    next_choice = (seg_index, other)
                    break
            if next_choice is None:
                break
            seg_index, other = next_choice
            used[seg_index] = True
            chain.append(seg_index)
            current = other
            if len(adjacency[current]) != 2:
                break
            if current == start_node:
                break
        return chain

    polylines: List[Shape] = []

    # Pass 1: open chains beginning at degree-1 nodes.
    open_starts = [n for n, edges in adjacency.items() if len(edges) == 1]
    open_starts.sort(key=lambda n: (node_points[n][1], node_points[n][0]))
    for start in open_starts:
        if all(used[si] for si, _ in adjacency[start]):
            continue
        chain = _walk(start)
        pl = _finish_chain(chain, seg_endpoints, node_points, endpoint_tol)
        if pl is None:
            continue
        if pl["closed"]:
            pl["closed"] = False  # degree-1 start cannot really be closed
        polylines.append(pl)

    # Pass 2: any remaining segments belong to pure cycles.
    for seg_index in range(len(segments)):
        if used[seg_index]:
            continue
        n0, _ = seg_endpoints[seg_index]
        chain = _walk(n0)
        pl = _finish_chain(chain, seg_endpoints, node_points, endpoint_tol)
        if pl is None:
            continue
        polylines.append(pl)

    result: List[Shape] = []
    for pl in polylines:
        if not include_closed and pl["closed"]:
            continue
        result.append(pl)
    result.sort(key=_shape_bbox_key)
    return result

def _finish_chain(
    chain: List[int],
    seg_endpoints: List[Tuple[Tuple[int, int], Tuple[int, int]]],
    node_points: Dict[Tuple[int, int], Point],
    endpoint_tol: float,
) -> Optional[Shape]:
    """Turn an ordered list of segment indices into a polyline shape dict."""
    if not chain:
        return None
    n_a, n_b = seg_endpoints[chain[0]]
    if len(chain) == 1:
        nodes: List[Tuple[int, int]] = [n_a, n_b]
    else:
        s2a, s2b = seg_endpoints[chain[1]]
        nodes = [n_a, n_b] if n_b in (s2a, s2b) else [n_b, n_a]
        for seg_index in chain[1:]:
            a, b = seg_endpoints[seg_index]
            last = nodes[-1]
            if a == last:
                nodes.append(b)
            elif b == last:
                nodes.append(a)
            else:
                return None  # chain broken

    points: List[Point] = [node_points[n] for n in nodes]
    if len(points) < 2:
        return None
    total_length = sum(
        point_distance(points[i], points[i + 1]) for i in range(len(points) - 1)
    )
    if len(points) == 2 and total_length <= endpoint_tol:
        return None
    closed = point_distance(points[0], points[-1]) <= endpoint_tol and len(points) >= 3
    return {
        "kind": "polyline",
        "points": [[p[0], p[1]] for p in points],
        "length": total_length,
        "bbox": _bbox_from_points(points),
        "closed": closed,
    }

# ---- Grid-line detection --------------------------------------------------

def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0

def _stdev(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / len(values))

def _merge_ranges(ranges: List[Tuple[float, float]], tol: float) -> List[Tuple[float, float]]:
    """Merge overlapping / abutting 1D ranges (proximity ``tol``)."""
    if not ranges:
        return []
    ordered = sorted((min(a, b), max(a, b)) for a, b in ranges)
    merged: List[Tuple[float, float]] = [ordered[0]]
    for lo, hi in ordered[1:]:
        prev_lo, prev_hi = merged[-1]
        if lo <= prev_hi + tol:
            merged[-1] = (prev_lo, max(prev_hi, hi))
        else:
            merged.append((lo, hi))
    return merged

def find_grid_lines(
    drawings: Iterable[Any],
    page_size: Tuple[float, float],
    *,
    min_length: Optional[float] = None,
    angle_tol_deg: float = GRID_ANGLE_TOLERANCE_DEG,
) -> Shape:
    """Identify long near-orthogonal lines that plausibly form a grid.

    Vertical lines are within ``angle_tol_deg`` of 90 degrees;
    horizontal lines are within tolerance of 0 (both taken mod 180).
    Collinear segments at the same ordinate are merged so a grid line
    interrupted by dimensioning is not double-counted. ``min_length``
    defaults to ``GRID_LINE_MIN_LENGTH_FRACTION`` of the shorter page
    side. ``regular`` is ``True`` only when both axes carry >= 3 lines
    with relative-stdev spacings under ``GRID_SPACING_TOLERANCE``.
    """
    width, height = float(page_size[0]), float(page_size[1])
    shorter = min(width, height) if (width > 0 and height > 0) else 0.0
    if min_length is None:
        min_length = shorter * GRID_LINE_MIN_LENGTH_FRACTION
    if min_length < 0:
        min_length = 0.0

    v_raw: Dict[int, List[Tuple[float, float]]] = defaultdict(list)
    h_raw: Dict[int, List[Tuple[float, float]]] = defaultdict(list)
    v_x: Dict[int, float] = {}
    h_y: Dict[int, float] = {}

    for op, pts in iter_primitives(drawings):
        if op != "line":
            continue
        p0, p1 = pts
        length = point_distance(p0, p1)
        if length < min_length:
            continue
        angle = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0])) % 180.0
        if angle <= angle_tol_deg or angle >= 180.0 - angle_tol_deg:
            y_mean = 0.5 * (p0[1] + p1[1])
            key = int(round(y_mean / ENDPOINT_TOLERANCE_PTS))
            h_raw[key].append((p0[0], p1[0]))
            h_y.setdefault(key, y_mean)
        elif abs(angle - 90.0) <= angle_tol_deg:
            x_mean = 0.5 * (p0[0] + p1[0])
            key = int(round(x_mean / ENDPOINT_TOLERANCE_PTS))
            v_raw[key].append((p0[1], p1[1]))
            v_x.setdefault(key, x_mean)

    verticals: List[Dict[str, float]] = []
    for key, ranges in v_raw.items():
        for y0, y1 in _merge_ranges(ranges, ENDPOINT_TOLERANCE_PTS):
            span = abs(y1 - y0)
            if span < min_length:
                continue
            verticals.append({"x": v_x[key], "y0": y0, "y1": y1, "length": span})

    horizontals: List[Dict[str, float]] = []
    for key, ranges in h_raw.items():
        for x0, x1 in _merge_ranges(ranges, ENDPOINT_TOLERANCE_PTS):
            span = abs(x1 - x0)
            if span < min_length:
                continue
            horizontals.append({"y": h_y[key], "x0": x0, "x1": x1, "length": span})

    verticals.sort(key=lambda g: g["x"])
    horizontals.sort(key=lambda g: g["y"])

    v_spacings = [
        verticals[i + 1]["x"] - verticals[i]["x"] for i in range(len(verticals) - 1)
    ]
    h_spacings = [
        horizontals[i + 1]["y"] - horizontals[i]["y"] for i in range(len(horizontals) - 1)
    ]

    regular = _is_regular(v_spacings) and _is_regular(h_spacings)

    return {
        "kind": "grid",
        "vertical": verticals,
        "horizontal": horizontals,
        "vertical_spacing_pts": v_spacings,
        "horizontal_spacing_pts": h_spacings,
        "regular": regular,
    }

def _is_regular(spacings: Sequence[float]) -> bool:
    """Uniform spacings within ``GRID_SPACING_TOLERANCE``; needs >= 2 gaps."""
    if len(spacings) < 2:
        return False
    mu = _mean(spacings)
    if mu <= 0.0:
        return False
    return _stdev(spacings) / mu <= GRID_SPACING_TOLERANCE
