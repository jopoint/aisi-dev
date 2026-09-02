"""Canonical physical footprints for AISI table types."""

from __future__ import annotations

from dataclasses import dataclass
import math

from aisi.core.models import TableState

Point2D = tuple[float, float]
Footprint = tuple[Point2D, ...]
ProjectionInterval = tuple[float, float]
Bounds = tuple[float, float, float, float]

GEOMETRY_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class TableGeometry:
    type_name: str
    type_id: int
    local_footprint: Footprint
    nominal_width: float
    nominal_depth: float


@dataclass(frozen=True, slots=True)
class ResolvedTableGeometry:
    """Footprint data resolved for a known or legacy table state."""

    local_footprint: Footprint
    nominal_width: float
    nominal_depth: float
    characteristic_diagonal: float


TABLE_GEOMETRIES: dict[str, TableGeometry] = {
    "summit": TableGeometry(
        type_name="summit",
        type_id=0,
        local_footprint=((-80.0, -35.0), (80.0, -35.0), (51.0, 35.0), (-51.0, 35.0)),
        nominal_width=160.0,
        nominal_depth=70.0,
    ),
    "sprint": TableGeometry(
        type_name="sprint",
        type_id=1,
        local_footprint=((-44.0, -30.0), (44.0, -30.0), (19.0, 30.0), (-19.0, 30.0)),
        nominal_width=88.0,
        nominal_depth=60.0,
    ),
    "rect": TableGeometry(
        type_name="rect",
        type_id=2,
        local_footprint=((-80.0, -40.0), (80.0, -40.0), (80.0, 40.0), (-80.0, 40.0)),
        nominal_width=160.0,
        nominal_depth=80.0,
    ),
}

TABLE_TYPE_NAMES = tuple(TABLE_GEOMETRIES)
TABLE_TYPE_IDS = {name: geometry.type_id for name, geometry in TABLE_GEOMETRIES.items()}


def get_table_geometry(table_type: str) -> TableGeometry:
    """Return canonical geometry; unknown types are rejected explicitly."""
    try:
        return TABLE_GEOMETRIES[table_type]
    except KeyError as exc:
        raise ValueError(f"Unknown table type: {table_type!r}") from exc


def normalize_table_type(value: object) -> str | None:
    """Normalize a serialized type while retaining unknown legacy type names."""
    if value is None:
        return None
    normalized = str(value).strip().lower()
    return normalized or None


def rectangle_footprint(width: float, depth: float) -> Footprint:
    """Return a centered local rectangular footprint."""
    half_width = float(width) * 0.5
    half_depth = float(depth) * 0.5
    return (
        (-half_width, -half_depth),
        (half_width, -half_depth),
        (half_width, half_depth),
        (-half_width, half_depth),
    )


def resolve_table_state_geometry(table: TableState) -> ResolvedTableGeometry:
    """Resolve canonical geometry or a width/height legacy rectangle."""
    table_type = normalize_table_type(table.table_type)
    if table_type in TABLE_GEOMETRIES:
        geometry = TABLE_GEOMETRIES[table_type]
        width = geometry.nominal_width
        depth = geometry.nominal_depth
        footprint = geometry.local_footprint
    else:
        width = float(table.width)
        depth = float(table.height)
        footprint = rectangle_footprint(width, depth)

    return ResolvedTableGeometry(
        local_footprint=footprint,
        nominal_width=width,
        nominal_depth=depth,
        characteristic_diagonal=math.hypot(width, depth),
    )


def table_world_footprint(
    table: TableState,
    center: Point2D,
    rotation_deg: float,
) -> Footprint:
    """Resolve and transform a TableState footprint into WORLD coordinates."""
    geometry = resolve_table_state_geometry(table)
    return transform_local_footprint(geometry.local_footprint, center[0], center[1], rotation_deg)


def table_projection_interval(
    table: TableState,
    rotation_deg: float,
    axis: Point2D,
) -> ProjectionInterval:
    """Project a rotated TableState footprint centered at the origin."""
    return project_polygon_onto_axis(table_world_footprint(table, (0.0, 0.0), rotation_deg), axis)


def table_support_distance(
    table: TableState,
    rotation_deg: float,
    direction: Point2D,
) -> float:
    """Return directional support for a rotated TableState footprint."""
    return support_distance(table_world_footprint(table, (0.0, 0.0), rotation_deg), direction)


def table_allowed_center_bounds(
    table: TableState,
    rotation_deg: float,
    *,
    x_min: float = 0.0,
    y_min: float = 0.0,
    x_max: float = 500.0,
    y_max: float = 500.0,
) -> Bounds:
    """Return ROI-safe center bounds for a rotated TableState footprint."""
    return allowed_table_center_bounds(
        resolve_table_state_geometry(table).local_footprint,
        rotation_deg,
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
    )


def required_table_center_separation(
    table_a: TableState,
    rotation_deg_a: float,
    table_b: TableState,
    rotation_deg_b: float,
    axis_from_a_to_b: Point2D,
    *,
    gap: float = 0.0,
) -> float:
    """Return support-based center separation for two rotated table footprints."""
    axis = _normalized_axis(axis_from_a_to_b)
    return (
        table_support_distance(table_a, rotation_deg_a, axis)
        + table_support_distance(table_b, rotation_deg_b, (-axis[0], -axis[1]))
        + max(0.0, float(gap))
    )


def transform_local_footprint(
    local_footprint: Footprint,
    x: float,
    y: float,
    rotation_deg: float,
) -> Footprint:
    """Rotate a local footprint around (0, 0), then translate it into WORLD."""
    angle = math.radians(rotation_deg)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return tuple(
        (
            x + local_x * cos_a - local_y * sin_a,
            y + local_x * sin_a + local_y * cos_a,
        )
        for local_x, local_y in local_footprint
    )


def project_polygon_onto_axis(polygon: Footprint, axis: Point2D) -> ProjectionInterval:
    """Project a polygon onto an axis, normalizing the supplied axis first."""
    if not polygon:
        raise ValueError("Polygon must contain at least one point")
    axis_x, axis_y = _normalized_axis(axis)
    projections = tuple(x * axis_x + y * axis_y for x, y in polygon)
    return min(projections), max(projections)


def support_distance(
    polygon: Footprint,
    direction: Point2D,
    *,
    center: Point2D = (0.0, 0.0),
) -> float:
    """Return the polygon support distance from center along direction."""
    axis_x, axis_y = _normalized_axis(direction)
    center_projection = center[0] * axis_x + center[1] * axis_y
    return project_polygon_onto_axis(polygon, (axis_x, axis_y))[1] - center_projection


def convex_polygons_intersect(
    polygon_a: Footprint,
    polygon_b: Footprint,
    *,
    minimum_gap: float = 0.0,
    tolerance: float = GEOMETRY_EPSILON,
) -> bool:
    """Return whether convex polygons overlap, touch, or violate minimum_gap."""
    if len(polygon_a) < 3 or len(polygon_b) < 3:
        raise ValueError("Convex polygons must contain at least three points")

    axes = tuple(_edge_normals(polygon_a)) + tuple(_edge_normals(polygon_b))
    if not axes:
        raise ValueError("Convex polygons must contain at least one non-degenerate edge")

    epsilon = max(0.0, float(tolerance))
    gap = max(0.0, float(minimum_gap))
    for axis in axes:
        min_a, max_a = project_polygon_onto_axis(polygon_a, axis)
        min_b, max_b = project_polygon_onto_axis(polygon_b, axis)
        if max_a + gap < min_b - epsilon or max_b + gap < min_a - epsilon:
            return False
    return True


def polygon_inside_roi(
    polygon: Footprint,
    *,
    x_min: float = 0.0,
    y_min: float = 0.0,
    x_max: float = 500.0,
    y_max: float = 500.0,
    tolerance: float = GEOMETRY_EPSILON,
) -> bool:
    """Return whether every polygon point lies inside or on the ROI boundary."""
    if not polygon:
        return False
    epsilon = max(0.0, float(tolerance))
    return all(
        x_min - epsilon <= x <= x_max + epsilon
        and y_min - epsilon <= y <= y_max + epsilon
        for x, y in polygon
    )


def allowed_table_center_bounds(
    local_footprint: Footprint,
    rotation_deg: float,
    *,
    x_min: float = 0.0,
    y_min: float = 0.0,
    x_max: float = 500.0,
    y_max: float = 500.0,
) -> Bounds:
    """Return inclusive center bounds that keep the rotated footprint in the ROI."""
    rotated = transform_local_footprint(local_footprint, 0.0, 0.0, rotation_deg)
    offset_min_x, offset_min_y, offset_max_x, offset_max_y = footprint_bounds(rotated)
    return (
        x_min - offset_min_x,
        y_min - offset_min_y,
        x_max - offset_max_x,
        y_max - offset_max_y,
    )


def world_footprint(table_type: str, x: float, y: float, rotation_deg: float) -> Footprint:
    """Return the canonical table footprint transformed into WORLD coordinates."""
    geometry = get_table_geometry(table_type)
    return transform_local_footprint(geometry.local_footprint, x, y, rotation_deg)


def footprint_bounds(footprint: Footprint) -> Bounds:
    """Return (min_x, min_y, max_x, max_y) for a non-empty footprint."""
    if not footprint:
        raise ValueError("Footprint must contain at least one point")
    xs = [point[0] for point in footprint]
    ys = [point[1] for point in footprint]
    return min(xs), min(ys), max(xs), max(ys)


def clamp_table_center_to_roi(
    table_type: str,
    x: float,
    y: float,
    rotation_deg: float,
    *,
    x_min: float = 0.0,
    y_min: float = 0.0,
    x_max: float = 500.0,
    y_max: float = 500.0,
) -> Point2D:
    """Clamp a table center so its complete rotated footprint stays in the ROI."""
    geometry = get_table_geometry(table_type)
    allowed_x_min, allowed_y_min, allowed_x_max, allowed_y_max = allowed_table_center_bounds(
        geometry.local_footprint,
        rotation_deg,
        x_min=x_min,
        y_min=y_min,
        x_max=x_max,
        y_max=y_max,
    )

    clamped_x = (x_min + x_max) * 0.5 if allowed_x_min > allowed_x_max else max(allowed_x_min, min(allowed_x_max, x))
    clamped_y = (y_min + y_max) * 0.5 if allowed_y_min > allowed_y_max else max(allowed_y_min, min(allowed_y_max, y))
    return clamped_x, clamped_y


def _normalized_axis(axis: Point2D) -> Point2D:
    length = math.hypot(axis[0], axis[1])
    if length <= GEOMETRY_EPSILON:
        raise ValueError("Axis must have non-zero length")
    return axis[0] / length, axis[1] / length


def _edge_normals(polygon: Footprint) -> tuple[Point2D, ...]:
    normals: list[Point2D] = []
    for index, point in enumerate(polygon):
        next_point = polygon[(index + 1) % len(polygon)]
        edge_x = next_point[0] - point[0]
        edge_y = next_point[1] - point[1]
        if math.hypot(edge_x, edge_y) <= GEOMETRY_EPSILON:
            continue
        normals.append(_normalized_axis((-edge_y, edge_x)))
    return tuple(normals)
