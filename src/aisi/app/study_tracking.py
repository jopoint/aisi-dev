"""Study-only binding of one live Rect track to a trial's nominal source."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any

from aisi.app.study_trials import PoseSpec


SOURCE_MATCH_MAX_DISTANCE_CM = 60.0
SOURCE_MATCH_MAX_ROTATION_DEG = 35.0
SOURCE_MATCH_ROTATION_WEIGHT_CM_PER_DEG = 0.5


@dataclass(frozen=True)
class TrackedTablePose:
    """One confirmed Rect-table pose from the live vision scene."""

    track_id: str
    x_cm: float
    y_cm: float
    rotation_deg: float

    def as_source_pose(self) -> dict[str, float | str]:
        return {
            "id": self.track_id,
            "x_cm": self.x_cm,
            "y_cm": self.y_cm,
            "rotation_deg": self.rotation_deg,
        }


@dataclass(frozen=True)
class ActiveTrackMatch:
    """A source-gated, deterministic live-track binding result."""

    track: TrackedTablePose
    xy_distance_cm: float
    rotation_difference_deg: float
    score: float


def rect_rotation_difference_deg(first_deg: float, second_deg: float) -> float:
    """Return the smallest orientation difference for a 180-degree Rect."""

    return abs((first_deg - second_deg + 90.0) % 180.0 - 90.0)


def select_active_study_track(
    tracks: list[TrackedTablePose],
    source_pose: PoseSpec,
    *,
    max_xy_distance_cm: float = SOURCE_MATCH_MAX_DISTANCE_CM,
    max_rotation_difference_deg: float = SOURCE_MATCH_MAX_ROTATION_DEG,
    rotation_weight_cm_per_deg: float = SOURCE_MATCH_ROTATION_WEIGHT_CM_PER_DEG,
) -> ActiveTrackMatch | None:
    """Select one plausible source track, deterministically, or leave unresolved.

    The score is XY distance plus the Rect-symmetric yaw error converted to a
    small centimetre-equivalent penalty. Both components are independently
    gated, so a nearby but wrongly oriented distractor cannot silently bind.
    """

    candidates: list[ActiveTrackMatch] = []
    for track in tracks:
        xy_distance = math.hypot(track.x_cm - source_pose.x_cm, track.y_cm - source_pose.y_cm)
        rotation_difference = rect_rotation_difference_deg(track.rotation_deg, source_pose.rotation_deg)
        if xy_distance > max_xy_distance_cm or rotation_difference > max_rotation_difference_deg:
            continue
        candidates.append(
            ActiveTrackMatch(
                track=track,
                xy_distance_cm=xy_distance,
                rotation_difference_deg=rotation_difference,
                score=xy_distance + rotation_weight_cm_per_deg * rotation_difference,
            )
        )
    return min(candidates, key=lambda item: (item.score, item.xy_distance_cm, item.rotation_difference_deg, item.track.track_id), default=None)


def load_confirmed_rect_tracks(scene_path: str | Path) -> list[TrackedTablePose]:
    """Read currently published Rect tracks from the vision-scene adapter."""

    try:
        with Path(scene_path).open("r", encoding="utf-8") as handle:
            scene = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return []
    tables = scene.get("tables") if isinstance(scene, dict) else None
    if not isinstance(tables, list):
        return []
    tracks: list[TrackedTablePose] = []
    for table in tables:
        if not isinstance(table, dict) or str(table.get("type", "")).strip().lower() != "rect":
            continue
        try:
            track_id = str(table["id"]).strip()
            if not track_id:
                continue
            tracks.append(TrackedTablePose(track_id, float(table["x_cm"]), float(table["y_cm"]), float(table["rotation_deg"])))
        except (KeyError, TypeError, ValueError):
            continue
    return tracks


class StudyActiveTrackBindingStore:
    """Small atomic hand-off from Study Control to the tracking-only sender."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def write(self, active_track_id: str | None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
                temp_name = handle.name
                json.dump({"active_track_id": active_track_id}, handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self.path)
        except Exception:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            raise

    def clear(self) -> None:
        self.write(None)

    def remove(self) -> None:
        """Remove the optional binding so ordinary tracking falls back to table_00."""

        self.path.unlink(missing_ok=True)

    def read(self) -> tuple[bool, str | None]:
        """Return ``(present, ID)``; malformed/transient content is ignored."""

        try:
            with self.path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except FileNotFoundError:
            return False, None
        except (OSError, json.JSONDecodeError):
            return False, None
        if not isinstance(payload, dict):
            return False, None
        value = payload.get("active_track_id")
        if value is None:
            return True, None
        value = str(value).strip()
        return True, value or None


class StudyActiveTrackSelector:
    """Resolve once from a trial source and expose only that latched live track."""

    def __init__(self, scene_path: str | Path, binding_store: StudyActiveTrackBindingStore) -> None:
        self.scene_path = Path(scene_path)
        self.binding_store = binding_store
        self.active_track_id: str | None = None

    def clear(self) -> None:
        self.active_track_id = None
        self.binding_store.clear()

    def disable(self) -> None:
        """Release Study ownership and restore ordinary tracking-only routing."""

        self.active_track_id = None
        self.binding_store.remove()

    def resolve(self, source_pose: PoseSpec) -> ActiveTrackMatch | None:
        self.clear()
        match = select_active_study_track(load_confirmed_rect_tracks(self.scene_path), source_pose)
        if match is not None:
            self.active_track_id = match.track.track_id
            self.binding_store.write(self.active_track_id)
        return match

    def __call__(self) -> dict[str, float | str] | None:
        if self.active_track_id is None:
            return None
        return next(
            (track.as_source_pose() for track in load_confirmed_rect_tracks(self.scene_path) if track.track_id == self.active_track_id),
            None,
        )
