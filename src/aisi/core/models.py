from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, field
import math
from typing import Any, Literal

LearningFormat = Literal["input", "groupwork", "discussion"]
StructureType = Literal["focus_point", "focus_line", "frontal_rows", "cluster_zones", "shared_field"]
SceneType = Literal["frontal", "grouped", "field_like", "unordered", "mixed"]


@dataclass(slots=True)
class ROI:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def width(self) -> float:
        return max(0.0, self.x_max - self.x_min)

    @property
    def height(self) -> float:
        return max(0.0, self.y_max - self.y_min)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x_min + self.width / 2.0, self.y_min + self.height / 2.0)


@dataclass(slots=True)
class TableState:
    table_id: str
    x: float
    y: float
    rot_deg: float = 0.0
    width: float = 110.0
    height: float = 70.0
    confidence: float | None = None

    @property
    def theta(self) -> float:
        """Compatibility alias for older MVP code."""
        return self.rot_deg

    @theta.setter
    def theta(self, value: float) -> None:
        self.rot_deg = value


@dataclass(slots=True)
class ChairState:
    chair_id: str
    x: float
    y: float
    width: float = 45.0
    height: float = 45.0
    confidence: float | None = None


@dataclass(slots=True)
class PersonState:
    person_id: str
    x: float
    y: float
    confidence: float | None = None


@dataclass(slots=True)
class SceneState:
    roi: ROI
    tables: list[TableState]
    learning_format: LearningFormat
    chairs: list[ChairState] = field(default_factory=list)
    people: list[PersonState] = field(default_factory=list)


@dataclass(slots=True)
class SceneFeatures:
    cluster_count: float
    cluster_compactness: float
    distribution_evenness: float
    frontal_alignment: float
    shared_field_centrality: float
    local_vs_global_focus: float
    scene_type: SceneType


@dataclass(slots=True)
class RangePreference:
    min_value: float
    target_value: float
    max_value: float
    weight: float = 1.0


@dataclass(slots=True)
class TargetProfile:
    learning_format: LearningFormat
    cluster_count: RangePreference
    cluster_compactness: RangePreference
    distribution_evenness: RangePreference
    frontal_alignment: RangePreference
    shared_field_centrality: RangePreference
    local_vs_global_focus: RangePreference
    target_area_orientation_fit: RangePreference


@dataclass(slots=True)
class Point2D:
    x: float
    y: float


@dataclass(slots=True)
class ClusterZone:
    center: Point2D
    radius: float


@dataclass(slots=True)
class TargetStructure:
    structure_type: StructureType
    focus_point: Point2D | None = None
    focus_direction: Point2D | None = None
    focus_line_start: Point2D | None = None
    focus_line_end: Point2D | None = None
    front_direction: Point2D | None = None
    row_centers: list[Point2D] = field(default_factory=list)
    row_layout: list[int] = field(default_factory=list)
    cluster_zones: list[ClusterZone] = field(default_factory=list)
    shared_field_center: Point2D | None = None


@dataclass(slots=True)
class TableTarget:
    table_id: str
    target_x: float
    target_y: float
    source_rot_deg: float = 0.0
    target_rot_deg: float = 0.0
    facing_target_x: float | None = None
    facing_target_y: float | None = None

    @property
    def source_theta(self) -> float:
        """Compatibility alias for older MVP code."""
        return self.source_rot_deg

    @property
    def target_theta(self) -> float:
        """Compatibility alias for older MVP code."""
        return self.target_rot_deg


@dataclass(slots=True)
class ChairTarget:
    chair_id: str
    target_x: float
    target_y: float


@dataclass(slots=True)
class LayoutProposal:
    table_targets: list[TableTarget]
    chair_targets: list[ChairTarget] = field(default_factory=list)
    generation_notes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProposalEvaluation:
    movement_cost: float
    rotation_cost: float
    fit_score: float
    total_score: float
    details: dict[str, float] = field(default_factory=dict)


@dataclass(slots=True)
class ProjectionTableItem:
    table_id: str
    source: Point2D
    target: Point2D
    source_rot_deg: float
    target_rot_deg: float

    @property
    def source_theta(self) -> float:
        return self.source_rot_deg

    @property
    def target_theta(self) -> float:
        return self.target_rot_deg


@dataclass(slots=True)
class ProjectionChairItem:
    chair_id: str
    source: Point2D
    target: Point2D


@dataclass(slots=True)
class ProjectionPayload:
    fade_out_seconds: float
    show_chairs: bool
    tables: list[ProjectionTableItem]
    chairs: list[ProjectionChairItem] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


def to_serializable(value: Any) -> Any:
    """Convert dataclasses and nested values into JSON-serializable structures."""
    if is_dataclass(value):
        return {k: to_serializable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_serializable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_serializable(v) for v in value]
    if isinstance(value, tuple):
        return [to_serializable(v) for v in value]
    return value


def dataclass_to_dict(instance: Any) -> dict[str, Any]:
    """Serialize a dataclass instance to a plain dictionary."""
    serialized = to_serializable(instance)
    if not isinstance(serialized, dict):
        raise TypeError("Expected dataclass-like object to serialize into dict")
    return serialized


def normalize_rotation_deg(value: float) -> float:
    """Normalize a rotation angle to the range [-180, 180)."""
    return ((value + 180.0) % 360.0) - 180.0


def normalize_angle_deg(value: float) -> float:
    """Compatibility alias for angle normalization in orientation helpers."""
    return normalize_rotation_deg(value)


def angle_deg_from_points(origin_x: float, origin_y: float, target_x: float, target_y: float) -> float:
    """Return the angle from origin to target in degrees."""
    return math.degrees(math.atan2(target_y - origin_y, target_x - origin_x))


def long_axis_unit_vector(rot_deg: float) -> tuple[float, float]:
    """Return the unit vector of the table long axis described by rot_deg."""
    theta = math.radians(normalize_rotation_deg(rot_deg))
    return math.cos(theta), math.sin(theta)


def candidate_facing_normals(rot_deg: float) -> tuple[tuple[float, float], tuple[float, float]]:
    """Return both candidate facing normals orthogonal to the long axis.

    Because the long axis has two side normals, facing is ambiguous without a target.
    """
    axis_x, axis_y = long_axis_unit_vector(rot_deg)
    normal_a = (-axis_y, axis_x)
    normal_b = (axis_y, -axis_x)
    return normal_a, normal_b


def choose_facing_normal_toward_target(
    table_center: tuple[float, float],
    target_point: tuple[float, float],
    rot_deg: float,
) -> tuple[float, float]:
    """Pick the side-normal that points more towards target_point."""
    to_target_x = target_point[0] - table_center[0]
    to_target_y = target_point[1] - table_center[1]

    normal_a, normal_b = candidate_facing_normals(rot_deg)
    score_a = normal_a[0] * to_target_x + normal_a[1] * to_target_y
    score_b = normal_b[0] * to_target_x + normal_b[1] * to_target_y
    return normal_a if score_a >= score_b else normal_b


def long_axis_rotation_from_facing_vector(
    facing_vector: tuple[float, float],
    reference_rot_deg: float | None = None,
) -> float:
    """Convert desired facing direction into long-axis rotation.

    The long axis is perpendicular to facing direction, so two axis angles are valid
    (difference 180 deg). If reference_rot_deg is provided, we keep the closer one
    for stable rotation continuity.
    """
    fx, fy = facing_vector
    if abs(fx) < 1e-9 and abs(fy) < 1e-9:
        return normalize_rotation_deg(reference_rot_deg or 0.0)

    facing_angle = angle_deg_from_points(0.0, 0.0, fx, fy)
    candidate_a = normalize_rotation_deg(facing_angle - 90.0)
    candidate_b = normalize_rotation_deg(candidate_a + 180.0)

    if reference_rot_deg is None:
        return candidate_a

    ref = normalize_rotation_deg(reference_rot_deg)
    delta_a = abs(normalize_rotation_deg(candidate_a - ref))
    delta_b = abs(normalize_rotation_deg(candidate_b - ref))
    return candidate_a if delta_a <= delta_b else candidate_b
