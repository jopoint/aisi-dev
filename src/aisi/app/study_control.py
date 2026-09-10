"""Minimal experiment control and OSC state publisher for AISI Study Mode."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from enum import IntEnum
from pathlib import Path
from typing import Any, Protocol

from aisi.app.study_logging import JsonlEventLogger, LiveSceneSourcePoseProvider, SourcePoseProvider
from aisi.app.study_trials import (
    ParticipantStartSpec,
    PoseSpec,
    StudyTask,
    StudyVariant,
    TrialSpec,
    load_trial_definitions,
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
DEFAULT_LOG_DIRECTORY = PROJECT_ROOT / "data" / "aisi" / "study" / "logs"
DEFAULT_SOURCE_SCENE_PATH = PROJECT_ROOT / "data" / "aisi" / "scenes" / "live" / "vision_live_scene.json"
ACTIVE_POSE_LOG_INTERVAL_MS = 100


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

    def __init__(self, publisher: StudyStatePublisher, state: StudyState | None = None, *, event_logger: EventLogger | None = None, source_pose_provider: SourcePoseProvider | None = None) -> None:
        self._publisher = publisher
        self._event_logger = event_logger
        self._source_pose_provider = source_pose_provider
        self.state = state or StudyState()
        self.trial_started_at_iso: str | None = None
        self.trial_completed_at_iso: str | None = None

    def publish_current(self) -> None:
        self._publisher.publish(self.state)

    def start_session(self) -> None:
        self._log_event("session_started")

    def set_mode(self, mode: StudyMode) -> bool:
        return self._update(replace(self.state, mode=StudyMode(mode)), "mode_changed")

    def set_condition(self, condition: StudyCondition) -> bool:
        return self._update(replace(self.state, condition=StudyCondition(condition)), "condition_changed")

    def set_phase(self, phase: StudyPhase) -> bool:
        phase = StudyPhase(phase)
        return self._update(replace(self.state, phase=phase), {StudyPhase.HOME: "phase_home", StudyPhase.READY: "phase_ready", StudyPhase.ACTIVE: "trial_started", StudyPhase.COMPLETE: "trial_completed"}[phase])

    def home(self) -> bool:
        return self.set_phase(StudyPhase.HOME)

    def ready(self) -> bool:
        return self.set_phase(StudyPhase.READY)

    def start_trial(self) -> bool:
        if self.state.phase == StudyPhase.ACTIVE:
            return False
        self.trial_started_at_iso, self.trial_completed_at_iso = _utc_iso_now(), None
        return self._update(replace(self.state, phase=StudyPhase.ACTIVE), "trial_started", {"trial_started_at_iso": self.trial_started_at_iso})

    def complete_trial(self) -> bool:
        if self.state.phase == StudyPhase.COMPLETE:
            return False
        self.trial_completed_at_iso = _utc_iso_now()
        return self._update(replace(self.state, phase=StudyPhase.COMPLETE), "trial_completed", {"trial_started_at_iso": self.trial_started_at_iso, "trial_completed_at_iso": self.trial_completed_at_iso})

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
        return self._update(replace(self.state, **updates), "trial_loaded", {"trial_notes": trial.notes})

    def record_active_pose(self) -> bool:
        if self.state.phase != StudyPhase.ACTIVE:
            return False
        self._log_event("active_pose_sample")
        return True

    def _update(self, updated: StudyState, event_type: str | None = None, extra: dict[str, Any] | None = None) -> bool:
        if updated == self.state:
            return False
        self.state = updated
        self.publish_current()
        if event_type:
            self._log_event(event_type, extra)
        return True

    def _log_event(self, event_type: str, extra: dict[str, Any] | None = None) -> None:
        if self._event_logger is None:
            return
        try:
            source_pose = self._source_pose_provider() if self._source_pose_provider else None
        except Exception:
            source_pose = None
        state = self.state
        event: dict[str, Any] = {"event_type": event_type, "mode": int(state.mode), "condition": int(state.condition), "phase": int(state.phase), "task_id": state.task.name, "task": int(state.task), "variant": state.variant.name, "variant_id": int(state.variant), "target_x_cm": state.target_x, "target_y_cm": state.target_y, "target_rotation_deg": state.target_rot, "source_pose": source_pose}
        if extra:
            event.update(extra)
        self._event_logger.log(event)


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
        self._target_x = tk.StringVar(value=str(controller.state.target_x)); self._target_y = tk.StringVar(value=str(controller.state.target_y)); self._target_rot = tk.StringVar(value=str(controller.state.target_rot)); self._summary = tk.StringVar()
        container = ttk.Frame(self.root, padding=12); container.grid(sticky="nsew")
        self._add_radio_group(container, "MODE", self._mode, (("Tracking", StudyMode.TRACKING), ("Study", StudyMode.STUDY), ("AISI", StudyMode.AISI)), self._on_mode, 0)
        self._add_radio_group(container, "TASK", self._task, (("T1", StudyTask.T1), ("T2", StudyTask.T2), ("T3", StudyTask.T3), ("T4", StudyTask.T4)), self._on_trial_selection, 1)
        self._add_radio_group(container, "VARIANT", self._variant, (("A", StudyVariant.A), ("B", StudyVariant.B)), self._on_trial_selection, 2)
        self._add_radio_group(container, "STUDY CONDITION", self._condition, (("Floor Only", StudyCondition.FLOOR_ONLY), ("Dual Surface", StudyCondition.DUAL_SURFACE)), self._on_condition, 3)
        ttk.Label(container, text="PHASE").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, callback) in enumerate((("Home", self._on_home), ("Start", self._on_start), ("Complete", self._on_complete)), start=1):
            ttk.Button(container, text=label, command=callback).grid(row=4, column=column, sticky="w", padx=(0, 6), pady=3)
        ttk.Label(container, text="STUDY TARGET (cm / deg)").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, variable) in enumerate((("X", self._target_x), ("Y", self._target_y), ("Rotation", self._target_rot)), start=1):
            ttk.Label(container, text=label).grid(row=6, column=column, sticky="w", padx=(0, 3), pady=2); ttk.Entry(container, textvariable=variable, width=10).grid(row=7, column=column, sticky="w", padx=(0, 6), pady=2)
        ttk.Button(container, text="Set Target", command=self._on_target_pose).grid(row=7, column=0, sticky="w", pady=2)
        ttk.Separator(container, orient="horizontal").grid(row=8, column=0, columnspan=5, sticky="ew", pady=8); ttk.Label(container, textvariable=self._summary, justify="left").grid(row=9, column=0, columnspan=5, sticky="w")
        self._status = ""
        self._on_trial_selection(); self._sample_active_pose()

    def _add_radio_group(self, parent, title, variable, choices, command, row: int) -> None:
        from tkinter import ttk
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, value) in enumerate(choices, start=1):
            ttk.Radiobutton(parent, text=label, variable=variable, value=int(value), command=command).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=3)

    def _on_mode(self) -> None: self._controller.set_mode(StudyMode(self._mode.get())); self._refresh_summary()
    def _on_condition(self) -> None: self._controller.set_condition(StudyCondition(self._condition.get())); self._refresh_summary()
    def _on_home(self) -> None: self._controller.home(); self._refresh_summary()
    def _on_start(self) -> None: self._controller.start_trial(); self._refresh_summary()
    def _on_complete(self) -> None: self._controller.complete_trial(); self._refresh_summary()

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
        self._summary.set("Current values\n" + f"mode: {state.mode.name} ({int(state.mode)})\n" + f"task: {state.task.name}, variant: {state.variant.name}\n" + f"condition: {state.condition.name} ({int(state.condition)})\n" + f"phase: {state.phase.name} ({int(state.phase)})\n" + f"target_overlap: {int(state.target_overlap)}\n" + f"target: x={state.target_x:g} cm, y={state.target_y:g} cm, rot={state.target_rot:g} deg" + (f"\n{self._status}" if self._status else ""))

    def run(self) -> None: self.root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_OSC_HOST); parser.add_argument("--port", type=int, default=DEFAULT_OSC_PORT)
    parser.add_argument("--mode", type=int, choices=[0, 1, 2], default=0); parser.add_argument("--condition", type=int, choices=[0, 1], default=0); parser.add_argument("--phase", type=int, choices=[0, 1, 2, 3], default=0)
    parser.add_argument("--task", type=int, choices=[1, 2, 3, 4], default=1); parser.add_argument("--variant", type=int, choices=[0, 1], default=0); parser.add_argument("--target-overlap", type=int, choices=[0, 1], default=0)
    parser.add_argument("--target-x", type=float, default=DEFAULT_TARGET_X_CM); parser.add_argument("--target-y", type=float, default=DEFAULT_TARGET_Y_CM); parser.add_argument("--target-rot", type=float, default=DEFAULT_TARGET_ROT_DEG)
    parser.add_argument("--trials", type=Path, default=DEFAULT_TRIALS_PATH); parser.add_argument("--log-dir", type=Path, default=DEFAULT_LOG_DIRECTORY); parser.add_argument("--session-name")
    parser.add_argument("--source-scene", type=Path, default=DEFAULT_SOURCE_SCENE_PATH); parser.add_argument("--source-table-id", default="table_00"); parser.add_argument("--no-ui", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = StudyState(mode=StudyMode(args.mode), condition=StudyCondition(args.condition), phase=StudyPhase(args.phase), task=StudyTask(args.task), variant=StudyVariant(args.variant), target_overlap=bool(args.target_overlap), target_x=args.target_x, target_y=args.target_y, target_rot=args.target_rot)
    logger = JsonlEventLogger(args.log_dir, session_name=args.session_name)
    controller = StudyStateController(StudyStatePublisher(SimpleUDPClient(args.host, args.port)), state, event_logger=logger, source_pose_provider=LiveSceneSourcePoseProvider(args.source_scene, args.source_table_id))
    try:
        controller.start_session(); controller.publish_current(); print(f"Study Control OSC target: {args.host}:{args.port}; task={state.task.name}/{state.variant.name}; log={logger.path}")
        if not args.no_ui: StudyControlUi(controller, load_trial_definitions(args.trials)).run()
    except ImportError as error:
        raise SystemExit("Tkinter is required for the Study Control UI.") from error
    finally:
        logger.close()


if __name__ == "__main__": main()
