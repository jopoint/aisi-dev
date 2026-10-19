"""Participant-aware v1 planning primitives.

This module is deliberately independent from OSC: every visible table keeps a
target pose, while only a selected subset is functional and receives seats.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal

from aisi.core.models import SceneState, TableState, TableTarget, long_axis_unit_vector
from aisi.core.table_geometry import convex_polygons_intersect, polygon_inside_roi, table_world_footprint

PresentationSide = Literal["north", "east", "south", "west"]

SEAT_RADIUS_CM = 25.0
INPUT_SEAT_DEPTH_CM = 70.0


class LayoutConstraintError(ValueError):
    """Raised when the requested participant layout cannot be realized."""


@dataclass(frozen=True, slots=True)
class ActivityParameters:
    participants: int
    number_of_groups: int | None = None
    presentation_side: PresentationSide | None = None

    def validate(self, learning_format: str) -> None:
        if self.participants < 1:
            raise LayoutConstraintError("Die Teilnehmerzahl muss mindestens 1 sein.")
        if learning_format == "groupwork":
            if self.number_of_groups is None or self.number_of_groups < 1:
                raise LayoutConstraintError("Groupwork benötigt mindestens eine Gruppe.")
            if self.number_of_groups > self.participants:
                raise LayoutConstraintError("Es kann nicht mehr Gruppen als Teilnehmende geben.")


@dataclass(frozen=True, slots=True)
class SeatPosition:
    seat_id: str
    x: float
    y: float
    facing_x: float
    facing_y: float
    table_id: str
    group_index: int | None = None
    density: Literal["regular", "dense"] = "regular"


@dataclass(slots=True)
class AdaptiveLayoutPlan:
    table_targets: list[TableTarget]
    active_table_ids: tuple[str, ...]
    parked_table_ids: tuple[str, ...]
    seats: list[SeatPosition]
    group_sizes: tuple[int, ...]
    notes: list[str]


def evenly_distribute(participants: int, groups: int) -> tuple[int, ...]:
    """Return a deterministic, difference-at-most-one group distribution."""
    return tuple(participants // groups + (1 if index < participants % groups else 0) for index in range(groups))


def input_table_capacity() -> int:
    """Two regular long-side places plus one explicitly dense place."""
    return 3


def groupwork_table_capacity() -> int:
    """Two long-side places per side and one at each end."""
    return 6


def required_active_table_count(learning_format: str, parameters: ActivityParameters) -> int:
    parameters.validate(learning_format)
    if learning_format == "input":
        return math.ceil(parameters.participants / input_table_capacity())
    if learning_format == "groupwork":
        return max(parameters.number_of_groups or 1, math.ceil(parameters.participants / groupwork_table_capacity()))
    return math.ceil(parameters.participants / input_table_capacity())


def choose_active_tables(
    scene: SceneState,
    required_count: int,
    previous_active_table_ids: tuple[str, ...] = (),
) -> list[TableState]:
    """Reuse prior active Rect tables first; identity is only a deterministic tie-break."""
    rects = [table for table in scene.tables if table.table_type == "rect"]
    if required_count > len(rects):
        raise LayoutConstraintError(
            f"Benötigt {required_count} funktionale Rect-Tische, verfügbar sind nur {len(rects)}."
        )
    previous = set(previous_active_table_ids)
    return sorted(rects, key=lambda table: (table.table_id not in previous, table.table_id))[:required_count]


def presentation_direction(side: PresentationSide | None) -> tuple[float, float] | None:
    return {"north": (0.0, -1.0), "east": (1.0, 0.0), "south": (0.0, 1.0), "west": (-1.0, 0.0)}.get(side)


def input_seats(
    table: TableState,
    target: TableTarget,
    count: int,
    facing: tuple[float, float],
    *,
    group_index: int | None = None,
) -> list[SeatPosition]:
    """Create one full-width Rect long-side seating row facing ``facing``."""
    if not 1 <= count <= input_table_capacity():
        raise LayoutConstraintError("Ein Input-Rect-Tisch trägt ein bis drei Sitzplätze.")
    long_axis = long_axis_unit_vector(target.target_rot_deg)
    normal = (-long_axis[1], long_axis[0])
    if normal[0] * facing[0] + normal[1] * facing[1] < 0.0:
        normal = (-normal[0], -normal[1])
    # Participants sit on the side opposite the direction they look.
    seat_normal = (-normal[0], -normal[1])
    offsets = {1: (0.0,), 2: (-40.0, 40.0), 3: (-52.0, 0.0, 52.0)}[count]
    distance = table.height * 0.5 + INPUT_SEAT_DEPTH_CM * 0.5
    return [
        SeatPosition(
            f"{table.table_id}:seat:{index}",
            target.target_x + long_axis[0] * offset + seat_normal[0] * distance,
            target.target_y + long_axis[1] * offset + seat_normal[1] * distance,
            target.target_x + normal[0] * 100.0,
            target.target_y + normal[1] * 100.0,
            table.table_id,
            group_index,
            "dense" if count == 3 and index == 1 else "regular",
        )
        for index, offset in enumerate(offsets)
    ]


def seats_are_valid(scene: SceneState, targets: list[TableTarget], seats: list[SeatPosition]) -> bool:
    """Check ROI, chair-radius separation, and table-footprint exclusion."""
    by_id = {table.table_id: table for table in scene.tables}
    footprints = [table_world_footprint(by_id[target.table_id], (target.target_x, target.target_y), target.target_rot_deg) for target in targets]
    for seat in seats:
        if not (scene.roi.x_min + SEAT_RADIUS_CM <= seat.x <= scene.roi.x_max - SEAT_RADIUS_CM and scene.roi.y_min + SEAT_RADIUS_CM <= seat.y <= scene.roi.y_max - SEAT_RADIUS_CM):
            return False
        if any(_point_in_convex_polygon((seat.x, seat.y), footprint) for footprint in footprints):
            return False
    return all(math.dist((first.x, first.y), (second.x, second.y)) >= SEAT_RADIUS_CM * 2.0 for index, first in enumerate(seats) for second in seats[index + 1 :])


def plan_adaptive_input(
    scene: SceneState,
    parameters: ActivityParameters,
    previous_active_table_ids: tuple[str, ...] = (),
) -> AdaptiveLayoutPlan:
    """Plan a complete Input layout, including parked but still visible tables."""
    required = required_active_table_count("input", parameters)
    active = choose_active_tables(scene, required, previous_active_table_ids)
    direction = presentation_direction(parameters.presentation_side) or (0.0, -1.0)
    targets = _input_targets(active, direction)
    remaining = parameters.participants
    seats: list[SeatPosition] = []
    for table, target in zip(active, targets):
        count = min(input_table_capacity(), remaining)
        seats.extend(input_seats(table, target, count, direction))
        remaining -= count
    parked = [table for table in scene.tables if table.table_id not in {table.table_id for table in active}]
    targets.extend(_park_targets(scene, parked, targets, seats, parameters.presentation_side))
    if remaining or not seats_are_valid(scene, targets, seats):
        raise LayoutConstraintError("Die angeforderten Input-Sitzplätze passen nicht konfliktfrei in die ROI.")
    return AdaptiveLayoutPlan(
        table_targets=targets,
        active_table_ids=tuple(table.table_id for table in active),
        parked_table_ids=tuple(table.table_id for table in parked),
        seats=seats,
        group_sizes=(parameters.participants,),
        notes=[
            "adaptive_layout_v1=input",
            f"participants={parameters.participants}",
            f"active_tables={','.join(table.table_id for table in active)}",
            f"presentation_side={parameters.presentation_side or 'automatic'}",
        ],
    )


def _input_targets(tables: list[TableState], direction: tuple[float, float]) -> list[TableTarget]:
    """Use an inward grid; its orientation follows the optional presentation side."""
    north_grid = ((84.0, 120.0), (250.0, 120.0), (416.0, 120.0), (167.0, 340.0), (333.0, 340.0))
    if direction == (0.0, -1.0):
        points, rotation = north_grid, 0.0
    elif direction == (0.0, 1.0):
        points, rotation = tuple((x, 500.0 - y) for x, y in north_grid), 0.0
    elif direction == (1.0, 0.0):
        points, rotation = tuple((500.0 - y, x) for x, y in north_grid), 90.0
    else:
        points, rotation = tuple((y, 500.0 - x) for x, y in north_grid), 90.0
    return [
        TableTarget(table.table_id, point[0], point[1], table.rot_deg, rotation,
                    point[0] + direction[0] * 100.0, point[1] + direction[1] * 100.0)
        for table, point in zip(tables, points)
    ]


def _park_targets(
    scene: SceneState,
    tables: list[TableState],
    existing: list[TableTarget],
    seats: list[SeatPosition],
    presentation_side: PresentationSide | None,
) -> list[TableTarget]:
    """Greedily use free edge bays, preferring the side opposite presentation."""
    by_id = {table.table_id: table for table in scene.tables}
    candidates = _parking_candidates(presentation_side)
    result: list[TableTarget] = []
    for table in tables:
        for x, y, rotation in candidates:
            target = TableTarget(table.table_id, x, y, table.rot_deg, rotation)
            footprint = table_world_footprint(table, (x, y), rotation)
            if not polygon_inside_roi(footprint, x_min=scene.roi.x_min, y_min=scene.roi.y_min, x_max=scene.roi.x_max, y_max=scene.roi.y_max):
                continue
            occupied = [table_world_footprint(by_id[item.table_id], (item.target_x, item.target_y), item.target_rot_deg) for item in [*existing, *result]]
            if any(convex_polygons_intersect(footprint, other) for other in occupied):
                continue
            if any(_point_in_convex_polygon((seat.x, seat.y), footprint) for seat in seats):
                continue
            result.append(target)
            break
        else:
            raise LayoutConstraintError("Keine konfliktfreie Parkbucht für einen inaktiven Tisch verfügbar.")
    return result


def _parking_candidates(side: PresentationSide | None) -> tuple[tuple[float, float, float], ...]:
    sides = {
        "north": ((80.0, 40.0, 0.0), (250.0, 40.0, 0.0), (420.0, 40.0, 0.0)),
        "south": ((80.0, 460.0, 0.0), (250.0, 460.0, 0.0), (420.0, 460.0, 0.0)),
        "west": ((40.0, 100.0, 90.0), (40.0, 250.0, 90.0), (40.0, 400.0, 90.0)),
        "east": ((460.0, 100.0, 90.0), (460.0, 250.0, 90.0), (460.0, 400.0, 90.0)),
    }
    opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}.get(side)
    order = ([opposite] if opposite else []) + [name for name in ("north", "east", "south", "west") if name != opposite]
    return tuple(candidate for name in order for candidate in sides[name])


def _point_in_convex_polygon(point: tuple[float, float], polygon: tuple[tuple[float, float], ...]) -> bool:
    signs = []
    for first, second in zip(polygon, polygon[1:] + polygon[:1]):
        signs.append((second[0] - first[0]) * (point[1] - first[1]) - (second[1] - first[1]) * (point[0] - first[0]))
    return min(signs) >= -1e-9 or max(signs) <= 1e-9
