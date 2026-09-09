"""Minimal operator control for the Study Mode OSC state.

This process is intentionally independent of live vision/tracking and layout
generation.  It only publishes the four Study Mode channels to TouchDesigner.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Protocol

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Bitte installiere python-osc mit: pip install python-osc")
    raise SystemExit(1)


DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 9000


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
    """The complete, integer-backed state shared with TouchDesigner."""

    mode: StudyMode = StudyMode.TRACKING
    condition: StudyCondition = StudyCondition.FLOOR_ONLY
    phase: StudyPhase = StudyPhase.HOME
    target_overlap: bool = False

    def osc_messages(self) -> tuple[tuple[str, int], ...]:
        """Return the complete state as integer OSC values."""
        return (
            ("/study/mode", int(self.mode)),
            ("/study/condition", int(self.condition)),
            ("/study/phase", int(self.phase)),
            ("/study/target_overlap", int(self.target_overlap)),
        )


class OscMessageClient(Protocol):
    def send_message(self, address: str, value: int) -> None:
        """Send one OSC message."""


class StudyStatePublisher:
    """Publish a complete StudyState via the repository's python-osc client."""

    def __init__(self, client: OscMessageClient) -> None:
        self._client = client

    def publish(self, state: StudyState) -> None:
        for address, value in state.osc_messages():
            self._client.send_message(address, value)


class StudyStateController:
    """Own StudyState and republish the complete state after every change."""

    def __init__(self, publisher: StudyStatePublisher, state: StudyState | None = None) -> None:
        self._publisher = publisher
        self.state = state or StudyState()

    def publish_current(self) -> None:
        self._publisher.publish(self.state)

    def set_mode(self, mode: StudyMode) -> bool:
        return self._update(replace(self.state, mode=StudyMode(mode)))

    def set_condition(self, condition: StudyCondition) -> bool:
        return self._update(replace(self.state, condition=StudyCondition(condition)))

    def set_phase(self, phase: StudyPhase) -> bool:
        return self._update(replace(self.state, phase=StudyPhase(phase)))

    def set_target_overlap(self, target_overlap: bool) -> bool:
        return self._update(replace(self.state, target_overlap=bool(target_overlap)))

    def _update(self, updated: StudyState) -> bool:
        if updated == self.state:
            return False
        self.state = updated
        self.publish_current()
        return True


class StudyControlUi:
    """Small Tkinter operator UI; imported only when an interactive UI is used."""

    def __init__(self, controller: StudyStateController) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._tk = tk
        self._controller = controller
        self.root = tk.Tk()
        self.root.title("AISI Study Control")
        self.root.resizable(False, False)

        self._mode = tk.IntVar(value=int(controller.state.mode))
        self._condition = tk.IntVar(value=int(controller.state.condition))
        self._phase = tk.IntVar(value=int(controller.state.phase))
        self._summary = tk.StringVar()

        container = ttk.Frame(self.root, padding=12)
        container.grid(sticky="nsew")
        self._add_radio_group(
            container, "MODE", self._mode,
            (
                ("Tracking", StudyMode.TRACKING),
                ("Study", StudyMode.STUDY),
                ("AISI", StudyMode.AISI),
            ),
            self._on_mode,
            row=0,
        )
        self._add_radio_group(
            container, "STUDY CONDITION", self._condition,
            (("Floor Only", StudyCondition.FLOOR_ONLY), ("Dual Surface", StudyCondition.DUAL_SURFACE)),
            self._on_condition,
            row=1,
        )
        self._add_radio_group(
            container, "PHASE", self._phase,
            (
                ("Home", StudyPhase.HOME),
                ("Ready", StudyPhase.READY),
                ("Start", StudyPhase.ACTIVE),
                ("Complete", StudyPhase.COMPLETE),
            ),
            self._on_phase,
            row=2,
        )
        ttk.Separator(container, orient="horizontal").grid(row=3, column=0, columnspan=4, sticky="ew", pady=8)
        ttk.Label(container, textvariable=self._summary, justify="left").grid(
            row=4, column=0, columnspan=4, sticky="w"
        )
        self._refresh_summary()

    def _add_radio_group(self, parent, title, variable, choices, command, row: int) -> None:
        from tkinter import ttk

        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        for column, (label, value) in enumerate(choices, start=1):
            ttk.Radiobutton(parent, text=label, variable=variable, value=int(value), command=command).grid(
                row=row, column=column, sticky="w", padx=(0, 8), pady=3
            )

    def _on_mode(self) -> None:
        self._controller.set_mode(StudyMode(self._mode.get()))
        self._refresh_summary()

    def _on_condition(self) -> None:
        self._controller.set_condition(StudyCondition(self._condition.get()))
        self._refresh_summary()

    def _on_phase(self) -> None:
        self._controller.set_phase(StudyPhase(self._phase.get()))
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        state = self._controller.state
        self._summary.set(
            "Current values\n"
            f"mode: {state.mode.name} ({int(state.mode)})\n"
            f"condition: {state.condition.name} ({int(state.condition)})\n"
            f"phase: {state.phase.name} ({int(state.phase)})\n"
            f"target_overlap: {int(state.target_overlap)}"
        )

    def run(self) -> None:
        self.root.mainloop()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_OSC_HOST, help="OSC target host (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=DEFAULT_OSC_PORT, help="OSC target port (default: 9000).")
    parser.add_argument("--mode", type=int, choices=[0, 1, 2], default=0, help="Initial mode (0=TRACKING, 1=STUDY, 2=AISI).")
    parser.add_argument("--condition", type=int, choices=[0, 1], default=0, help="Initial condition (0=FLOOR_ONLY, 1=DUAL_SURFACE).")
    parser.add_argument("--phase", type=int, choices=[0, 1, 2, 3], default=0, help="Initial phase (0=HOME through 3=COMPLETE).")
    parser.add_argument("--target-overlap", type=int, choices=[0, 1], default=0, help="Development/test initial target overlap value.")
    parser.add_argument("--no-ui", action="store_true", help="Publish the initial state once and exit.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    initial_state = StudyState(
        mode=StudyMode(args.mode),
        condition=StudyCondition(args.condition),
        phase=StudyPhase(args.phase),
        target_overlap=bool(args.target_overlap),
    )
    controller = StudyStateController(
        StudyStatePublisher(SimpleUDPClient(args.host, args.port)),
        initial_state,
    )
    controller.publish_current()
    print(
        f"Study Control OSC target: {args.host}:{args.port}; "
        f"mode={initial_state.mode.name}, condition={initial_state.condition.name}, "
        f"phase={initial_state.phase.name}, target_overlap={int(initial_state.target_overlap)}"
    )
    if args.no_ui:
        return

    try:
        StudyControlUi(controller).run()
    except ImportError as error:
        raise SystemExit("Tkinter is required for the Study Control UI.") from error


if __name__ == "__main__":
    main()
