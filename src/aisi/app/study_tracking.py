"""Study-only binding of one live Rect track to a trial's nominal source."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import os
from pathlib import Path
import tempfile
import time
from typing import Any

from aisi.app.study_trials import PoseSpec


SOURCE_MATCH_MAX_DISTANCE_CM = 60.0
SOURCE_MATCH_MAX_ROTATION_DEG = 35.0
SOURCE_MATCH_ROTATION_WEIGHT_CM_PER_DEG = 0.5
STUDY_BINDING_RETRY_DELAYS_SECONDS = (0.005, 0.010, 0.020)


def _is_transient_windows_file_lock(error: OSError) -> bool:
    """Return whether Windows reported an ordinary sharing/replace race."""

    return isinstance(error, PermissionError) or getattr(error, "winerror", None) in {5, 32}


def _replace_with_retry(temp_path: str, destination: Path) -> None:
    """Atomically replace ``destination`` with bounded Windows lock retries."""

    for delay in (*STUDY_BINDING_RETRY_DELAYS_SECONDS, None):
        try:
            os.replace(temp_path, destination)
            return
        except OSError as error:
            if not _is_transient_windows_file_lock(error) or delay is None:
                raise
            time.sleep(delay)


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
            _replace_with_retry(temp_name, self.path)
        except Exception:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            raise

    def clear(self, _trial_id: str | None = None) -> None:
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

    def clear(self, _trial_id: str | None = None) -> None:
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

    @property
    def bindings(self) -> dict[int, str]:
        return {} if self.active_track_id is None else {0: self.active_track_id}

    def resolve_setup(self, _trial_id: str, setup_poses: tuple[PoseSpec, ...]) -> dict[int, ActiveTrackMatch]:
        # Legacy one-table adapter; retained for callers with the old selector.
        if len(setup_poses) != 1:
            self.clear()
            return {}
        match = self.resolve(setup_poses[0])
        return {} if match is None else {0: match}

    def current_poses(self) -> dict[int, TrackedTablePose]:
        if self.active_track_id is None:
            return {}
        return {0: track for track in load_confirmed_rect_tracks(self.scene_path) if track.track_id == self.active_track_id}

    def __call__(self) -> dict[str, float | str] | None:
        if self.active_track_id is None:
            return None
        return next(
            (track.as_source_pose() for track in load_confirmed_rect_tracks(self.scene_path) if track.track_id == self.active_track_id),
            None,
        )


def select_study_setup_tracks(
    tracks: list[TrackedTablePose], setup_poses: tuple[PoseSpec, ...]
) -> dict[int, ActiveTrackMatch]:
    """Globally assign feasible live tracks to nominal setup poses.

    With at most six tables an exhaustive assignment is deliberately simpler
    and safer than independent greedy matching: it maximizes bindings first,
    then minimizes the existing deterministic score, and never reuses an ID.
    """
    # A single physical Rect has no identity ambiguity. During T1/T2 HOME it
    # may begin anywhere in the ROI, so bind it without making the global
    # proximity/yaw gates weaker for every other situation.
    if len(setup_poses) == 1 and len(tracks) == 1:
        track, pose = tracks[0], setup_poses[0]
        xy_distance = math.hypot(track.x_cm - pose.x_cm, track.y_cm - pose.y_cm)
        rotation_difference = rect_rotation_difference_deg(track.rotation_deg, pose.rotation_deg)
        return {0: ActiveTrackMatch(
            track, xy_distance, rotation_difference,
            xy_distance + SOURCE_MATCH_ROTATION_WEIGHT_CM_PER_DEG * rotation_difference,
        )}

    candidates = {
        index: [
            match for track in tracks
            if (match := select_active_study_track([track], pose)) is not None
        ]
        for index, pose in enumerate(setup_poses)
    }
    best: tuple[int, float, tuple[str, ...], dict[int, ActiveTrackMatch]] | None = None

    def visit(index: int, used: set[str], chosen: dict[int, ActiveTrackMatch]) -> None:
        nonlocal best
        if index == len(setup_poses):
            ids = tuple(chosen[key].track.track_id if key in chosen else "~" for key in range(len(setup_poses)))
            value = (-len(chosen), sum(item.score for item in chosen.values()), ids, dict(chosen))
            if best is None or value[:3] < best[:3]:
                best = value
            return
        visit(index + 1, used, chosen)
        for match in candidates[index]:
            if match.track.track_id not in used:
                used.add(match.track.track_id); chosen[index] = match
                visit(index + 1, used, chosen)
                del chosen[index]; used.remove(match.track.track_id)
    visit(0, set(), {})
    return {} if best is None else best[3]


class StudyTableTrackBindingStore:
    """Atomic trial-scoped setup-index -> vision-track ID registry."""

    def __init__(self, path: str | Path, active_store: StudyActiveTrackBindingStore) -> None:
        self.path = Path(path); self.active_store = active_store

    def write(self, trial_id: str | None, bindings: dict[int, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary: str | None = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as handle:
                temporary = handle.name
                json.dump({"trial_id": trial_id, "bindings": {str(k): v for k, v in sorted(bindings.items())}}, handle)
                handle.flush(); os.fsync(handle.fileno())
            _replace_with_retry(temporary, self.path)
        except Exception:
            if temporary: Path(temporary).unlink(missing_ok=True)
            raise
        self.active_store.write(bindings.get(0))

    def clear(self, trial_id: str | None = None) -> None:
        self.write(trial_id, {})

    def remove(self) -> None:
        self.path.unlink(missing_ok=True); self.active_store.remove()

    def read(self) -> tuple[bool, str | None, dict[int, str]]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                return False, None, {}
            bindings = {int(k): str(v) for k, v in payload.get("bindings", {}).items() if str(v).strip()}
            return True, payload.get("trial_id"), bindings
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return False, None, {}


class StudyTableTrackSelector:
    """Latch all setup bindings, while always reading their poses fresh."""

    def __init__(self, scene_path: str | Path, binding_store: StudyTableTrackBindingStore) -> None:
        self.scene_path = Path(scene_path); self.binding_store = binding_store
        _present, self.trial_id, self.bindings = binding_store.read()

    def clear(self, trial_id: str | None = None) -> None:
        self.trial_id = trial_id; self.bindings = {}; self.binding_store.clear(trial_id)

    def disable(self) -> None:
        self.trial_id = None; self.bindings = {}; self.binding_store.remove()

    def resolve_setup(self, trial_id: str, setup_poses: tuple[PoseSpec, ...]) -> dict[int, ActiveTrackMatch]:
        if self.trial_id != trial_id:
            self.clear(trial_id)
        tracks = load_confirmed_rect_tracks(self.scene_path)
        live = {track.track_id: track for track in tracks}
        self.bindings = {index: track_id for index, track_id in self.bindings.items() if index < len(setup_poses) and track_id in live}
        remaining_tracks = [track for track in tracks if track.track_id not in self.bindings.values()]
        remaining_poses = tuple(pose for index, pose in enumerate(setup_poses) if index not in self.bindings)
        remaining_indices = [index for index in range(len(setup_poses)) if index not in self.bindings]
        matches = select_study_setup_tracks(remaining_tracks, remaining_poses)
        resolved: dict[int, ActiveTrackMatch] = {}
        for index, track_id in self.bindings.items():
            resolved[index] = ActiveTrackMatch(live[track_id], 0.0, 0.0, 0.0)
        for local_index, match in matches.items():
            index = remaining_indices[local_index]; self.bindings[index] = match.track.track_id; resolved[index] = match
        self.binding_store.write(self.trial_id, self.bindings)
        return resolved

    def current_poses(self) -> dict[int, TrackedTablePose]:
        tracks = {track.track_id: track for track in load_confirmed_rect_tracks(self.scene_path)}
        return {index: tracks[track_id] for index, track_id in self.bindings.items() if track_id in tracks}

    def __call__(self) -> dict[str, float | str] | None:
        pose = self.current_poses().get(0)
        return pose.as_source_pose() if pose else None
