"""Minimal experiment control and OSC state publisher for AISI Study Mode."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from enum import IntEnum
from pathlib import Path
import time
from typing import Any, Callable, Protocol

from aisi.app.study_logging import JsonlEventLogger, LiveSceneSourcePoseProvider, SourcePoseProvider, StudySessionLogger
from aisi.app.study_tracking import (
    StudyActiveTrackBindingStore,
    StudyTableTrackBindingStore,
    StudyTableTrackSelector,
    rect_rotation_difference_deg,
)
from aisi.app.study_trials import (
    ParticipantStartSpec,
    PoseSpec,
    StudyTask,
    StudyVariant,
    TrialSpec,
    load_trial_definitions,
    trial_definition_metadata,
)

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Bitte installiere python-osc mit: pip install python-osc")
    raise SystemExit(1)


DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 9000
DEFAULT_TARGET_X_CM = 250.0
DEFAULT_TARGET_Y_CM = 250.0
DEFAULT_TARGET_ROT_DEG = 0.0
DEFAULT_SOURCE_X_CM = 250.0
DEFAULT_SOURCE_Y_CM = 250.0
DEFAULT_SOURCE_ROT_DEG = 0.0
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_TRIALS_PATH = PROJECT_ROOT / "data" / "aisi" / "study" / "trials.json"
DEFAULT_LOG_DIRECTORY = PROJECT_ROOT / "data" / "aisi" / "study" / "runs"
DEFAULT_SOURCE_SCENE_PATH = PROJECT_ROOT / "data" / "aisi" / "scenes" / "live" / "vision_live_scene.json"
DEFAULT_ACTIVE_TRACK_BINDING_PATH = PROJECT_ROOT / "data" / "aisi" / "state" / "study_active_track.json"
DEFAULT_TABLE_TRACKS_BINDING_PATH = PROJECT_ROOT / "data" / "aisi" / "state" / "study_table_tracks.json"
ACTIVE_POSE_LOG_INTERVAL_MS = 100
OBJECTIVE_ARRIVAL_TRANSLATION_TOLERANCE_CM = 8.0
OBJECTIVE_ARRIVAL_ROTATION_TOLERANCE_DEG = 5.0
OBJECTIVE_ARRIVAL_CONFIRMATION_SECONDS = 0.5
_UNSET = object()


class StudyMode(IntEnum):
    TRACKING = 0
    STUDY = 1
    AISI = 2


class StudyCondition(IntEnum):
    FLOOR_ONLY = 0
    DUAL_SURFACE = 1


class StudyPhase(IntEnum):
    HOME = 0
    READY = 1
    ACTIVE = 2
    COMPLETE = 3


@dataclass(frozen=True)
class StudyState:
    """The complete Study state shared with TouchDesigner."""

    mode: StudyMode = StudyMode.TRACKING
    condition: StudyCondition = StudyCondition.FLOOR_ONLY
    phase: StudyPhase = StudyPhase.HOME
    task: StudyTask = StudyTask.T1
    variant: StudyVariant = StudyVariant.A
    target_overlap: bool = False
    source_x: float = DEFAULT_SOURCE_X_CM
    source_y: float = DEFAULT_SOURCE_Y_CM
    source_rot: float = DEFAULT_SOURCE_ROT_DEG
    target_x: float = DEFAULT_TARGET_X_CM
    target_y: float = DEFAULT_TARGET_Y_CM
    target_rot: float = DEFAULT_TARGET_ROT_DEG
    setup_table_poses: tuple[PoseSpec, ...] = ()
    participant_start_positions: tuple[ParticipantStartSpec, ...] = ()
    active_track_id: str | None = None

    def osc_messages(self) -> tuple[tuple[str, int | float], ...]:
        messages: list[tuple[str, int | float]] = [
            ("/study/mode", int(self.mode)),
            ("/study/condition", int(self.condition)),
            ("/study/phase", int(self.phase)),
            ("/study/task", int(self.task)),
            ("/study/variant", int(self.variant)),
            ("/study/target_overlap", int(self.target_overlap)),
            ("/study/source_x", self.source_x),
            ("/study/source_y", self.source_y),
            ("/study/source_rot", self.source_rot),
            ("/study/target_x", self.target_x),
            ("/study/target_y", self.target_y),
            ("/study/target_rot", self.target_rot),
            ("/study/setup_table_count", len(self.setup_table_poses)),
            ("/study/participant_start_count", len(self.participant_start_positions)),
        ]
        for index, pose in enumerate(self.setup_table_poses):
            messages.extend((
                (f"/study/setup_table/{index}/x", pose.x_cm),
                (f"/study/setup_table/{index}/y", pose.y_cm),
                (f"/study/setup_table/{index}/rot", pose.rotation_deg),
            ))
        for index, marker in enumerate(self.participant_start_positions):
            messages.extend((
                (f"/study/participant_start/{index}/x", marker.x_cm),
                (f"/study/participant_start/{index}/y", marker.y_cm),
                (f"/study/participant_start/{index}/radius", marker.radius_cm),
            ))
        return tuple(messages)


class OscMessageClient(Protocol):
    def send_message(self, address: str, value: int | float) -> None: ...


class EventLogger(Protocol):
    def log(self, event: dict[str, Any]) -> None: ...


class StudyStatePublisher:
    def __init__(self, client: OscMessageClient) -> None:
        self._client = client

    def publish(self, state: StudyState) -> None:
        for address, value in state.osc_messages():
            self._client.send_message(address, value)


def apply_selected_trial(
    controller: "StudyStateController",
    trials: dict[tuple[StudyTask, StudyVariant], TrialSpec],
    task: StudyTask,
    variant: StudyVariant,
) -> TrialSpec | None:
    """Apply a selected trial when defined; never mutate state for a miss."""

    trial = trials.get((StudyTask(task), StudyVariant(variant)))
    if trial is not None:
        controller.apply_trial(trial)
    return trial


class StudyStateController:
    """Own Study state, trial transitions, and non-blocking event logging."""

    def __init__(self, publisher: StudyStatePublisher, state: StudyState | None = None, *, event_logger: EventLogger | None = None, session_logger_factory: Callable[[], StudySessionLogger] | None = None, source_pose_provider: SourcePoseProvider | None = None, active_track_selector: StudyTableTrackSelector | None = None) -> None:
        self._publisher = publisher
        self._event_logger = event_logger
        self._session_logger_factory = session_logger_factory
        self._active_track_selector = active_track_selector
        self._source_pose_provider = active_track_selector or source_pose_provider
        self.state = state or StudyState()
        self.trial_started_at_iso: str | None = None
        self.trial_completed_at_iso: str | None = None
        self.participant_id = ""
        self.session_id = getattr(event_logger, "session_id", None)
        self.attempt = 0
        self.run_index = 0
        self._attempts_by_trial_identity: dict[tuple[str, str, str], int] = {}
        self.start_block_reason = "participant ID missing"
        self._arrival_entered_monotonic_s: float | None = None
        self._arrival_confirmed = False
        self._tracking_lost_monotonic_s: float | None = None
        self._tracking_last_valid_pose: dict[str, Any] | None = None
        self._completed_attempts: list[dict[str, Any]] = []
        self._aborted_attempts: list[dict[str, Any]] = []
        self._conditions_run: set[str] = set()
        self._variants_run: set[str] = set()
        self._session_started = False
        self._session_metadata: dict[str, Any] = {}

    def publish_current(self) -> None:
        self._publisher.publish(self.state)

    def start_session(self, metadata: dict[str, Any] | None = None) -> None:
        self._session_metadata = dict(metadata or self._session_metadata)
        if self._session_started or not self.participant_id:
            return
        details = self._session_metadata | {"participant_id": self.participant_id, "session_id": self.session_id}
        self._log_event("session_started", details)
        self._update_manifest(details | {"session_started_at_iso": _utc_iso_now()})
        self._session_started = True

    def set_participant_id(self, participant_id: str) -> bool:
        """Set the participant only by opening a new immutable session boundary."""

        normalized = str(participant_id).strip()
        if not normalized:
            self.start_block_reason = "participant ID missing"
            return False
        if normalized == self.participant_id:
            return False
        if self.participant_id and self.session_id is not None:
            self.close_session()
            self._reset_for_new_participant()
        if self._session_logger_factory is not None:
            logger = self._session_logger_factory()
            self._event_logger = logger
            self.session_id = logger.session_id
        self.participant_id = normalized
        if self._session_metadata:
            self.start_session()
        self._log_event("participant_id_set", {"participant_id": normalized})
        return True

    def participant_switch_requires_confirmation(self, participant_id: str) -> bool:
        """UI helper: only prompt if the current session contains an attempt."""

        return (
            bool(str(participant_id).strip())
            and str(participant_id).strip() != self.participant_id
            and self.session_id is not None
            and self.run_index > 0
        )

    def close_session(self) -> None:
        """Finalize the active logger without altering its append-only records."""

        if self._event_logger is None or self.session_id is None:
            return
        self._update_manifest({"session_ended_at_iso": _utc_iso_now()})
        close = getattr(self._event_logger, "close", None)
        if callable(close):
            close()
        self._event_logger = None
        self.session_id = None
        self._session_started = False

    def _reset_for_new_participant(self) -> None:
        self.attempt = 0
        self.run_index = 0
        self._attempts_by_trial_identity = {}
        self._clear_trial_local_state()
        self._completed_attempts = []
        self._aborted_attempts = []
        self._conditions_run = set()
        self._variants_run = set()
        if self._active_track_selector is not None:
            self._active_track_selector.clear(f"{self.state.task.name}{self.state.variant.name}")
        self.state = replace(self.state, phase=StudyPhase.HOME, active_track_id=None)
        self.publish_current()

    def can_start(self) -> tuple[bool, str]:
        if not self.participant_id:
            return False, "participant ID missing"
        if self.state.mode != StudyMode.STUDY:
            return False, "Study mode is not selected"
        if self.state.phase == StudyPhase.ACTIVE:
            return False, "trial is already ACTIVE"
        if self._active_track_selector is not None:
            expected = len(self.state.setup_table_poses)
            actual = len(self._active_track_selector.bindings)
            if actual != expected:
                return False, f"setup bindings incomplete ({actual}/{expected})"
            if self._active_track_selector.bindings.get(0) is None:
                return False, "no active table binding"
        return True, "ready"

    def set_mode(self, mode: StudyMode) -> bool:
        mode = StudyMode(mode)
        changed = self._update(replace(self.state, mode=mode), "mode_changed")
        if not changed or self._active_track_selector is None:
            return changed
        if mode == StudyMode.STUDY:
            self.resolve_setup_tracks()
        else:
            self._active_track_selector.disable()
            self._update(replace(self.state, active_track_id=None))
        return changed

    def set_condition(self, condition: StudyCondition) -> bool:
        return self._update(replace(self.state, condition=StudyCondition(condition)), "condition_changed")

    def set_phase(self, phase: StudyPhase) -> bool:
        phase = StudyPhase(phase)
        return self._update(replace(self.state, phase=phase), {StudyPhase.HOME: "phase_home", StudyPhase.READY: "phase_ready", StudyPhase.ACTIVE: "trial_started", StudyPhase.COMPLETE: "trial_completed"}[phase])

    def home(self) -> bool:
        phase_changed = self.set_phase(StudyPhase.HOME)
        # HOME is the physical setup phase. A trial may have been loaded
        # before the tables reached their nominal start poses, so resolve only
        # an unresolved binding here; never replace an already latched ID.
        resolved = False
        if self._active_track_selector is not None and self.state.mode == StudyMode.STUDY:
            resolved = self.resolve_setup_tracks()
        return phase_changed or resolved

    def reset_to_home(self) -> bool:
        """Return the current attempt to physical setup without discarding data."""

        if self.state.phase == StudyPhase.ACTIVE:
            self.start_block_reason = "ABORT the ACTIVE attempt before resetting setup"
            return False
        self._clear_trial_local_state()
        changed = self._update(replace(self.state, phase=StudyPhase.HOME), "trial_reset_to_home")
        if not changed:
            self._log_event("trial_reset_to_home")
        if self._active_track_selector is not None and self.state.mode == StudyMode.STUDY:
            self.resolve_setup_tracks()
        return changed

    def abort_trial(self, reason: str = "other") -> bool:
        if self.state.phase != StudyPhase.ACTIVE:
            return False
        source_pose = self._read_source_pose()
        self._close_open_tracking_loss("aborted")
        changed = self._update(
            replace(self.state, phase=StudyPhase.HOME), "trial_aborted",
            {"abort_reason": str(reason).strip() or "other", "trial_started_at_iso": self.trial_started_at_iso},
            source_pose=source_pose,
        )
        if changed:
            self._record_manifest_attempt("aborted")
        return changed

    def ready(self) -> bool:
        return self.set_phase(StudyPhase.READY)

    def start_trial(self) -> bool:
        if self.state.phase == StudyPhase.ACTIVE:
            self.start_block_reason = "trial is already ACTIVE"
            return False
        if self._active_track_selector is not None:
            self.resolve_setup_tracks()
        allowed, reason = self.can_start()
        self.start_block_reason = reason
        if not allowed:
            self._log_event("trial_start_blocked", {"start_block_reason": reason})
            return False
        # ``run_index`` is session-global; ``attempt`` is local to the exact
        # task/variant/condition identity. Earlier records stay append-only.
        identity = (self.state.task.name, self.state.variant.name, self.state.condition.name)
        self.run_index += 1
        self.attempt = self._attempts_by_trial_identity.get(identity, 0) + 1
        self._attempts_by_trial_identity[identity] = self.attempt
        self._clear_trial_local_state()
        self.trial_started_at_iso, self.trial_completed_at_iso = _utc_iso_now(), None
        return self._update(replace(self.state, phase=StudyPhase.ACTIVE), "trial_started", {"trial_started_at_iso": self.trial_started_at_iso})

    def complete_trial(self) -> bool:
        """Record participant-declared completion without requiring arrival."""

        if self.state.phase != StudyPhase.ACTIVE:
            return False
        self.trial_completed_at_iso = _utc_iso_now()
        source_pose = self._read_source_pose()
        self._close_open_tracking_loss("completed")
        arrival = self._objective_arrival_measurements(source_pose)
        completion = {
            "trial_started_at_iso": self.trial_started_at_iso,
            "trial_completed_at_iso": self.trial_completed_at_iso,
            "participant_declared_completion_at_iso": self.trial_completed_at_iso,
            **(arrival or {"objective_arrival_available": False}),
        }
        changed = self._update(
            replace(self.state, phase=StudyPhase.COMPLETE),
            "trial_completed",
            completion,
            source_pose=source_pose,
        )
        if changed:
            self._record_manifest_attempt("completed")
        return changed

    def set_target_overlap(self, target_overlap: bool) -> bool:
        return self._update(replace(self.state, target_overlap=bool(target_overlap)))

    def set_target_pose(self, target_x: float, target_y: float, target_rot: float) -> bool:
        return self._update(replace(self.state, target_x=float(target_x), target_y=float(target_y), target_rot=float(target_rot)), "target_changed")

    def set_source_pose(self, source_x: float, source_y: float, source_rot: float) -> bool:
        """Set the fixed, trial-owned HOME/READY reference pose only."""
        return self._update(
            replace(self.state, source_x=float(source_x), source_y=float(source_y), source_rot=float(source_rot)),
            "start_pose_changed",
        )

    def apply_trial(self, trial: TrialSpec) -> bool:
        """Apply a selected fixed target without changing phase or timing."""
        updates: dict[str, Any] = {
            "task": trial.task,
            "variant": trial.variant,
            "target_x": trial.target_x_cm,
            "target_y": trial.target_y_cm,
            "target_rot": trial.target_rotation_deg,
        }
        if trial.source_pose is not None:
            updates.update(
                source_x=trial.source_pose.x_cm,
                source_y=trial.source_pose.y_cm,
                source_rot=trial.source_pose.rotation_deg,
            )
        setup_tables = (() if trial.source_pose is None else (trial.source_pose,)) + trial.distractor_tables
        updates.update(
            setup_table_poses=setup_tables,
            participant_start_positions=trial.participant_start_positions,
        )
        active_track_match = None
        if self._active_track_selector is not None:
            trial_id = f"{trial.task.name}{trial.variant.name}"
            if self.state.mode == StudyMode.STUDY and trial.source_pose is not None:
                self._active_track_selector.clear(trial_id)
                matches = self._active_track_selector.resolve_setup(trial_id, setup_tables)
                active_track_match = matches.get(0)
            elif getattr(self._active_track_selector, "trial_id", None) not in (None, trial_id):
                # A restored hand-off belongs to a different trial. Remove it
                # before normal TRACKING can accidentally route that stale ID.
                self._active_track_selector.disable()
            updates["active_track_id"] = (
                active_track_match.track.track_id if active_track_match is not None
                else (self._active_track_selector.bindings.get(0) if self.state.mode != StudyMode.STUDY else None)
            )
        extra: dict[str, Any] = {"trial_notes": trial.notes}
        if self._active_track_selector is not None:
            extra.update(_active_track_match_event_fields(active_track_match))
        return self._update(replace(self.state, **updates), "trial_loaded", extra)

    def resolve_setup_tracks(self) -> bool:
        """Resolve an unresolved HOME binding; never reselect during ACTIVE."""

        if self._active_track_selector is None:
            return False
        if self.state.mode != StudyMode.STUDY:
            self._active_track_selector.disable()
            return self._update(replace(self.state, active_track_id=None))
        if self.state.phase == StudyPhase.ACTIVE:
            return False
        trial_id = f"{self.state.task.name}{self.state.variant.name}"
        matches = self._active_track_selector.resolve_setup(trial_id, self.state.setup_table_poses)
        live = self._active_track_selector.current_poses()
        updated = replace(self.state,
            active_track_id=self._active_track_selector.bindings.get(0),
        )
        match = matches.get(0)
        event_type = "setup_tracks_bound" if len(self._active_track_selector.bindings) == len(self.state.setup_table_poses) else "setup_tracks_unresolved"
        extra = _active_track_match_event_fields(match) | {"study_table_bindings": dict(self._active_track_selector.bindings)}
        if updated == self.state:
            self._log_event(event_type, extra)
            return False
        return self._update(updated, event_type, extra)

    # Compatibility name used by older integrations/tests; it now resolves the
    # complete HOME setup atomically.
    def resolve_active_track(self) -> bool:
        return self.resolve_setup_tracks()

    def _clear_unavailable_home_track(self) -> bool:
        """Release a pre-ACTIVE binding only after its live ID has vanished."""

        if (
            self._active_track_selector is None
            or self.state.phase == StudyPhase.ACTIVE
            or self.state.active_track_id is None
            or self._active_track_selector() is not None
        ):
            return False
        missing_track_id = self.state.active_track_id
        self._active_track_selector.clear()
        return self._update(
            replace(self.state, active_track_id=None),
            "active_track_lost",
            {"active_track_id": missing_track_id},
        )

    def record_active_pose(self) -> bool:
        if self.state.phase != StudyPhase.ACTIVE:
            return False
        source_pose = self._read_source_pose()
        arrival = self._objective_arrival_measurements(source_pose)
        self._log_event(
            "active_pose_sample",
            arrival or {"objective_arrival_available": False},
            source_pose=source_pose,
        )
        self._update_arrival_state(arrival, source_pose)
        self._update_tracking_state(source_pose)
        return True

    def _update_tracking_state(self, source_pose: dict[str, Any] | None) -> None:
        if source_pose is None:
            if self._tracking_lost_monotonic_s is None:
                self._tracking_lost_monotonic_s = time.monotonic()
                self._log_event("tracking_lost", {"last_valid_pose": self._tracking_last_valid_pose})
            return
        if self._tracking_lost_monotonic_s is not None:
            now = time.monotonic()
            self._log_event("tracking_recovered", {
                "tracking_missing_duration_s": now - self._tracking_lost_monotonic_s,
                "recovered_pose": source_pose,
            }, source_pose=source_pose)
            self._tracking_lost_monotonic_s = None
        self._tracking_last_valid_pose = dict(source_pose)

    def _close_open_tracking_loss(self, terminal_status: str) -> None:
        if self._tracking_lost_monotonic_s is None:
            return
        now = time.monotonic()
        self._log_event("tracking_loss_ended", {
            "tracking_missing_duration_s": now - self._tracking_lost_monotonic_s,
            "tracking_loss_terminal_status": terminal_status,
        })
        self._tracking_lost_monotonic_s = None

    def _clear_trial_local_state(self) -> None:
        self.trial_started_at_iso = None
        self.trial_completed_at_iso = None
        self._arrival_entered_monotonic_s = None
        self._arrival_confirmed = False
        self._tracking_lost_monotonic_s = None
        self._tracking_last_valid_pose = None

    def _update(self, updated: StudyState, event_type: str | None = None, extra: dict[str, Any] | None = None, *, source_pose: dict[str, Any] | None | object = _UNSET) -> bool:
        if updated == self.state:
            return False
        self.state = updated
        self.publish_current()
        if event_type:
            self._log_event(event_type, extra, source_pose=source_pose)
        return True

    def _read_source_pose(self) -> dict[str, Any] | None:
        try:
            return self._source_pose_provider() if self._source_pose_provider else None
        except Exception:
            return None

    def _objective_arrival_measurements(self, source_pose: dict[str, Any] | None) -> dict[str, Any] | None:
        """Evaluate the live active pose without altering participant control."""

        if not isinstance(source_pose, dict):
            return None
        try:
            source_x = float(source_pose["x_cm"])
            source_y = float(source_pose["y_cm"])
            source_rotation = float(source_pose["rotation_deg"])
        except (KeyError, TypeError, ValueError):
            return None
        translation_error = ((source_x - self.state.target_x) ** 2 + (source_y - self.state.target_y) ** 2) ** 0.5
        rotation_error = rect_rotation_difference_deg(source_rotation, self.state.target_rot)
        within_tolerance = (
            translation_error <= OBJECTIVE_ARRIVAL_TRANSLATION_TOLERANCE_CM
            and rotation_error <= OBJECTIVE_ARRIVAL_ROTATION_TOLERANCE_DEG
        )
        return {
            "objective_arrival_available": True,
            "objective_translation_error_cm": translation_error,
            "objective_rotation_error_deg": rotation_error,
            "objective_within_tolerance": within_tolerance,
        }

    def _update_arrival_state(self, arrival: dict[str, Any] | None, source_pose: dict[str, Any] | None) -> None:
        """Log raw entry/exit/confirmation events; never change Study phase."""

        now = time.monotonic()
        if arrival is None:
            # Missing tracking is unknown, not evidence that the table left
            # the target. A merely-entered interval cannot span that gap.
            if not self._arrival_confirmed:
                self._arrival_entered_monotonic_s = None
            return
        within_tolerance = bool(arrival["objective_within_tolerance"])
        if within_tolerance:
            if self._arrival_entered_monotonic_s is None:
                self._arrival_entered_monotonic_s = now
                self._arrival_confirmed = False
                self._log_event("arrival_entered", arrival, source_pose=source_pose)
            elif (
                not self._arrival_confirmed
                and now - self._arrival_entered_monotonic_s >= OBJECTIVE_ARRIVAL_CONFIRMATION_SECONDS
            ):
                self._arrival_confirmed = True
                self._log_event(
                    "arrival_confirmed",
                    arrival | {"arrival_continuous_duration_s": now - self._arrival_entered_monotonic_s},
                    source_pose=source_pose,
                )
            return
        if self._arrival_entered_monotonic_s is not None:
            exit_details = arrival | {
                "arrival_continuous_duration_s": now - self._arrival_entered_monotonic_s,
                "arrival_was_confirmed": self._arrival_confirmed,
            }
            self._log_event("arrival_exited", exit_details, source_pose=source_pose)
            self._arrival_entered_monotonic_s = None
            self._arrival_confirmed = False

    def _log_event(self, event_type: str, extra: dict[str, Any] | None = None, *, source_pose: dict[str, Any] | None | object = _UNSET) -> None:
        if self._event_logger is None:
            return
        if source_pose is _UNSET:
            source_pose = self._read_source_pose()
        state = self.state
        event: dict[str, Any] = {"event_type": event_type, "participant_id": self.participant_id, "session_id": self.session_id, "run_index": self.run_index, "attempt": self.attempt, "mode": int(state.mode), "condition": int(state.condition), "phase": int(state.phase), "task_id": state.task.name, "task": int(state.task), "variant": state.variant.name, "variant_id": int(state.variant), "active_track_id": state.active_track_id, "target_x_cm": state.target_x, "target_y_cm": state.target_y, "target_rotation_deg": state.target_rot, "source_pose": source_pose}
        if extra:
            event.update(extra)
        self._event_logger.log(event)

    def _update_manifest(self, updates: dict[str, Any]) -> None:
        update = getattr(self._event_logger, "update_manifest", None)
        if callable(update):
            update(updates)

    def _record_manifest_attempt(self, status: str) -> None:
        attempt = {
            "trial_id": self.state.task.name,
            "variant": self.state.variant.name,
            "condition": self.state.condition.name,
            "attempt": self.attempt,
            "run_index": self.run_index,
            "status": status,
        }
        (self._completed_attempts if status == "completed" else self._aborted_attempts).append(attempt)
        self._conditions_run.add(self.state.condition.name)
        self._variants_run.add(self.state.variant.name)
        self._update_manifest({
            "last_updated_at_iso": _utc_iso_now(),
            "last_attempt": attempt,
            "completed_attempts": self._completed_attempts,
            "aborted_attempts": self._aborted_attempts,
            "conditions_run": sorted(self._conditions_run),
            "variants_run": sorted(self._variants_run),
        })


def _active_track_match_event_fields(match: Any) -> dict[str, Any]:
    """Serialize the selection provenance without adding a new OSC contract."""

    if match is None:
        return {"active_track_status": "unresolved", "active_track_id": None}
    return {
        "active_track_status": "bound",
        "active_track_id": match.track.track_id,
        "active_track_xy_distance_cm": match.xy_distance_cm,
        "active_track_rotation_difference_deg": match.rotation_difference_deg,
        "active_track_score": match.score,
    }


def _utc_iso_now() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


class StudyControlUi:
    """Small Tkinter operator UI; imported only for interactive use."""

    def __init__(self, controller: StudyStateController, trials: dict[tuple[StudyTask, StudyVariant], TrialSpec]) -> None:
        import tkinter as tk
        from tkinter import ttk
        self._controller, self._trials, self._tk = controller, trials, tk
        self.root = tk.Tk(); self.root.title("AISI Study Control"); self.root.resizable(False, False)
        self._mode = tk.IntVar(value=int(controller.state.mode)); self._condition = tk.IntVar(value=int(controller.state.condition))
        self._task = tk.IntVar(value=int(controller.state.task)); self._variant = tk.IntVar(value=int(controller.state.variant))
        self._participant_id = tk.StringVar(value=controller.participant_id)
        self._target_x = tk.StringVar(value=str(controller.state.target_x)); self._target_y = tk.StringVar(value=str(controller.state.target_y)); self._target_rot = tk.StringVar(value=str(controller.state.target_rot)); self._summary = tk.StringVar()
        container = ttk.Frame(self.root, padding=12); container.grid(sticky="nsew")
        ttk.Label(container, text="PARTICIPANT ID").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(container, textvariable=self._participant_id, width=20).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Button(container, text="Set", command=self._on_participant).grid(row=0, column=2, sticky="w", padx=4)
        self._add_radio_group(container, "MODE", self._mode, (("Tracking", StudyMode.TRACKING), ("Study", StudyMode.STUDY), ("AISI", StudyMode.AISI)), self._on_mode, 1)
        self._add_radio_group(container, "TASK", self._task, (("T1", StudyTask.T1), ("T2", StudyTask.T2), ("T3", StudyTask.T3), ("T4", StudyTask.T4)), self._on_trial_selection, 2)
        self._add_radio_group(container, "VARIANT", self._variant, (("A", StudyVariant.A), ("B", StudyVariant.B)), self._on_trial_selection, 3)
        self._add_radio_group(container, "STUDY CONDITION", self._condition, (("Floor Only", StudyCondition.FLOOR_ONLY), ("Dual Surface", StudyCondition.DUAL_SURFACE)), self._on_condition, 4)
        ttk.Label(container, text="PHASE").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, callback) in enumerate((("Home", self._on_home), ("Start", self._on_start), ("Complete", self._on_complete), ("Reset", self._on_reset), ("Abort", self._on_abort)), start=1):
            ttk.Button(container, text=label, command=callback).grid(row=5, column=column, sticky="w", padx=(0, 6), pady=3)
        ttk.Label(container, text="STUDY TARGET (cm / deg)").grid(row=6, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, variable) in enumerate((("X", self._target_x), ("Y", self._target_y), ("Rotation", self._target_rot)), start=1):
            ttk.Label(container, text=label).grid(row=7, column=column, sticky="w", padx=(0, 3), pady=2); ttk.Entry(container, textvariable=variable, width=10).grid(row=8, column=column, sticky="w", padx=(0, 6), pady=2)
        ttk.Button(container, text="Set Target", command=self._on_target_pose).grid(row=8, column=0, sticky="w", pady=2)
        ttk.Separator(container, orient="horizontal").grid(row=9, column=0, columnspan=7, sticky="ew", pady=8); ttk.Label(container, textvariable=self._summary, justify="left").grid(row=10, column=0, columnspan=7, sticky="w")
        self._status = ""
        self._on_trial_selection(); self._sample_active_pose()

    def _add_radio_group(self, parent, title, variable, choices, command, row: int) -> None:
        from tkinter import ttk
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, value) in enumerate(choices, start=1):
            ttk.Radiobutton(parent, text=label, variable=variable, value=int(value), command=command).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=3)

    def _on_mode(self) -> None: self._controller.set_mode(StudyMode(self._mode.get())); self._refresh_summary()
    def _on_participant(self) -> None:
        participant_id = self._participant_id.get().strip()
        if self._controller.participant_switch_requires_confirmation(participant_id):
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Switch participant session",
                f"End session for {self._controller.participant_id} and start a new session for {participant_id}?",
                parent=self.root,
            ):
                self._participant_id.set(self._controller.participant_id)
                return
        if not self._controller.set_participant_id(participant_id):
            self._status = "Participant ID is required; unchanged IDs keep the current session."
        else:
            self._status = f"Participant {self._controller.participant_id} session started."
        self._refresh_summary()
    def _on_condition(self) -> None: self._controller.set_condition(StudyCondition(self._condition.get())); self._refresh_summary()
    def _on_home(self) -> None: self._controller.home(); self._refresh_summary()
    def _on_start(self) -> None: self._controller.start_trial(); self._refresh_summary()
    def _on_complete(self) -> None: self._controller.complete_trial(); self._refresh_summary()
    def _on_reset(self) -> None: self._controller.reset_to_home(); self._refresh_summary()
    def _on_abort(self) -> None: self._controller.abort_trial(); self._refresh_summary()

    def _on_trial_selection(self) -> None:
        task, variant = StudyTask(self._task.get()), StudyVariant(self._variant.get())
        trial = apply_selected_trial(self._controller, self._trials, task, variant)
        if trial is None:
            self._status = f"No definition for {task.name}/{variant.name}; current trial is unchanged."
            self._refresh_summary(); return
        self._status = f"Loaded {task.name}/{variant.name}."
        self._target_x.set(str(trial.target_x_cm)); self._target_y.set(str(trial.target_y_cm)); self._target_rot.set(str(trial.target_rotation_deg)); self._refresh_summary()

    def _on_target_pose(self) -> None:
        try: target_x, target_y, target_rot = float(self._target_x.get()), float(self._target_y.get()), float(self._target_rot.get())
        except ValueError: self._summary.set("Target X, Y, and Rotation must be numeric."); return
        self._controller.set_target_pose(target_x, target_y, target_rot); self._refresh_summary()

    def _sample_active_pose(self) -> None:
        self._controller.record_active_pose(); self.root.after(ACTIVE_POSE_LOG_INTERVAL_MS, self._sample_active_pose)

    def _refresh_summary(self) -> None:
        state = self._controller.state
        bindings = getattr(self._controller._active_track_selector, "bindings", {})
        arrival = "confirmed" if self._controller._arrival_confirmed else ("inside" if self._controller._arrival_entered_monotonic_s is not None else "outside/unavailable")
        allowed, reason = self._controller.can_start()
        self._summary.set("Current values\n" + f"participant: {self._controller.participant_id or 'MISSING'}\n" + f"session: {self._controller.session_id or 'not started'}\n" + f"task: {state.task.name}, variant: {state.variant.name}, condition: {state.condition.name}\n" + f"phase: {state.phase.name}, attempt: {self._controller.attempt or 1}\n" + f"setup bindings: {len(bindings)}/{len(state.setup_table_poses)}; active: {state.active_track_id or 'unresolved'}\n" + f"tracking: {'lost' if self._controller._tracking_lost_monotonic_s is not None else 'available'}; objective arrival: {arrival}\n" + f"START: {'available' if allowed else reason}\n" + f"target: x={state.target_x:g} cm, y={state.target_y:g} cm, rot={state.target_rot:g} deg" + (f"\n{self._status}" if self._status else ""))

    def run(self) -> None: self.root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_OSC_HOST); parser.add_argument("--port", type=int, default=DEFAULT_OSC_PORT)
    parser.add_argument("--mode", type=int, choices=[0, 1, 2], default=0); parser.add_argument("--condition", type=int, choices=[0, 1], default=0); parser.add_argument("--phase", type=int, choices=[0, 1, 2, 3], default=0)
    parser.add_argument("--task", type=int, choices=[1, 2, 3, 4], default=1); parser.add_argument("--variant", type=int, choices=[0, 1], default=0); parser.add_argument("--target-overlap", type=int, choices=[0, 1], default=0)
    parser.add_argument("--target-x", type=float, default=DEFAULT_TARGET_X_CM); parser.add_argument("--target-y", type=float, default=DEFAULT_TARGET_Y_CM); parser.add_argument("--target-rot", type=float, default=DEFAULT_TARGET_ROT_DEG)
    parser.add_argument("--trials", type=Path, default=DEFAULT_TRIALS_PATH); parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIRECTORY); parser.add_argument("--session-name"); parser.add_argument("--participant-id", default="")
    parser.add_argument("--source-scene", type=Path, default=DEFAULT_SOURCE_SCENE_PATH); parser.add_argument("--source-table-id", default="table_00"); parser.add_argument("--active-track-binding", type=Path, default=DEFAULT_ACTIVE_TRACK_BINDING_PATH); parser.add_argument("--table-tracks-binding", type=Path, default=DEFAULT_TABLE_TRACKS_BINDING_PATH); parser.add_argument("--no-ui", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = StudyState(mode=StudyMode(args.mode), condition=StudyCondition(args.condition), phase=StudyPhase(args.phase), task=StudyTask(args.task), variant=StudyVariant(args.variant), target_overlap=bool(args.target_overlap), target_x=args.target_x, target_y=args.target_y, target_rot=args.target_rot)
    active_track_selector = StudyTableTrackSelector(
        args.source_scene,
        StudyTableTrackBindingStore(args.table_tracks_binding, StudyActiveTrackBindingStore(args.active_track_binding)),
    )
    requested_session_name = args.session_name
    def create_session_logger() -> StudySessionLogger:
        nonlocal requested_session_name
        session_name, requested_session_name = requested_session_name, None
        return StudySessionLogger(args.log_dir, session_id=session_name)
    controller = StudyStateController(StudyStatePublisher(SimpleUDPClient(args.host, args.port)), state, session_logger_factory=create_session_logger, source_pose_provider=LiveSceneSourcePoseProvider(args.source_scene, args.source_table_id), active_track_selector=active_track_selector)
    try:
        controller.start_session(trial_definition_metadata(args.trials)); controller.set_participant_id(args.participant_id); controller.publish_current(); print(f"Study Control OSC target: {args.host}:{args.port}; task={state.task.name}/{state.variant.name}; log={args.log_dir}")
        if not args.no_ui: StudyControlUi(controller, load_trial_definitions(args.trials)).run()
    except ImportError as error:
        raise SystemExit("Tkinter is required for the Study Control UI.") from error
    finally:
        active_track_selector.disable()
        controller.close_session()


if __name__ == "__main__": main()
