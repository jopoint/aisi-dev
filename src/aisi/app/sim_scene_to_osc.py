"""Send the simulated room editor scene to TouchDesigner via OSC.

This script continuously reads data/aisi/scenes/simulated/live_scene.json and
sends the table values to TouchDesigner using python-osc.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path
from typing import Any

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Bitte installiere python-osc mit: pip install python-osc")
    raise SystemExit(1)

try:
    import msvcrt
except ImportError:
    msvcrt = None


DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 9000
DEFAULT_INTERVAL_SECONDS = 0.05
DEBUG_INTERVAL_SECONDS = 5.0
DEFAULT_LAYOUT_MODE = "groupwork"
LEARNING_FORMAT_POLL_SECONDS = 1.0

current_layout_mode = DEFAULT_LAYOUT_MODE
stop_event = threading.Event()

GROUPWORK_TARGETS = [
    {"x_cm": 150.0, "y_cm": 160.0, "rotation_deg": 0.0},
    {"x_cm": 350.0, "y_cm": 160.0, "rotation_deg": 0.0},
    {"x_cm": 150.0, "y_cm": 340.0, "rotation_deg": 0.0},
    {"x_cm": 350.0, "y_cm": 340.0, "rotation_deg": 0.0},
]

INPUT_TARGETS = [
    {"x_cm": 140.0, "y_cm": 150.0, "rotation_deg": 0.0},
    {"x_cm": 360.0, "y_cm": 150.0, "rotation_deg": 0.0},
    {"x_cm": 140.0, "y_cm": 260.0, "rotation_deg": 0.0},
    {"x_cm": 360.0, "y_cm": 260.0, "rotation_deg": 0.0},
]

DISCUSSION_TARGETS = [
    {"x_cm": 160.0, "y_cm": 180.0, "rotation_deg": 35.0},
    {"x_cm": 340.0, "y_cm": 180.0, "rotation_deg": -35.0},
    {"x_cm": 160.0, "y_cm": 330.0, "rotation_deg": -35.0},
    {"x_cm": 340.0, "y_cm": 330.0, "rotation_deg": 35.0},
]

LAYOUT_MODES = {
    "input": INPUT_TARGETS,
    "groupwork": GROUPWORK_TARGETS,
    "discussion": DISCUSSION_TARGETS,
}

# TouchDesigner uses inverted Y coordinates, so rotation is inverted for visual consistency.


def repo_root() -> Path:
    """Return the repository root based on this file location."""
    return Path(__file__).resolve().parents[3]


def default_scene_path() -> Path:
    """Return the default path to the simulated live scene JSON."""
    return repo_root() / "data" / "aisi" / "scenes" / "simulated" / "live_scene.json"


def learning_format_path() -> Path:
    """Return the path of the shared learning format JSON file."""
    return repo_root() / "data" / "aisi" / "state" / "learning_format.json"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Read the simulated room scene and send tables to TouchDesigner via OSC."
    )
    parser.add_argument(
        "--scene",
        default=str(default_scene_path()),
        help="Path to the live scene JSON (default: data/aisi/scenes/simulated/live_scene.json).",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_OSC_HOST,
        help="OSC target host (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_OSC_PORT,
        help="OSC target port (default: 9000).",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Send interval in seconds (default: 0.05).",
    )
    return parser.parse_args()


def load_scene(scene_path: Path) -> dict[str, Any]:
    """Load the live scene JSON file."""
    with scene_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_learning_format(path: Path) -> str | None:
    """Load a valid learning format from the shared JSON file."""
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

    value = data.get("learning_format")
    if value in LAYOUT_MODES:
        return str(value)
    return None


def get_target_for_index(index: int, source_table: dict[str, Any], layout_mode: str) -> tuple[float, float, float]:
    """Return the target pose for a table in the selected layout mode."""
    targets = LAYOUT_MODES.get(layout_mode, GROUPWORK_TARGETS)
    if index < len(targets):
        target = targets[index]
        return (
            float(target["x_cm"]),
            float(target["y_cm"]),
            float(target["rotation_deg"]),
        )

    return (
        float(source_table.get("x_cm", 0.0)),
        float(source_table.get("y_cm", 0.0)),
        float(source_table.get("rotation_deg", 0.0)),
    )


def send_tables(client: SimpleUDPClient, tables: list[dict[str, Any]], layout_mode: str) -> list[str]:
    """Send all tables via OSC and return short debug summaries."""
    summaries: list[str] = []
    for index, table in enumerate(tables):
        source_x = float(table.get("x_cm", 0.0))
        source_y = float(table.get("y_cm", 0.0))
        source_rot = float(table.get("rotation_deg", 0.0))
        td_source_rot = -source_rot
        width_cm = float(table.get("width_cm", 0.0))
        height_cm = float(table.get("height_cm", 0.0))

        target_x, target_y, target_rot = get_target_for_index(index, table, layout_mode)
        td_target_rot = -target_rot

        client.send_message(f"/table/{index}/source_x", source_x)
        client.send_message(f"/table/{index}/source_y", source_y)
        client.send_message(f"/table/{index}/source_rot", td_source_rot)
        client.send_message(f"/table/{index}/target_x", target_x)
        client.send_message(f"/table/{index}/target_y", target_y)
        client.send_message(f"/table/{index}/target_rot", td_target_rot)
        client.send_message(f"/table/{index}/x", source_x)
        client.send_message(f"/table/{index}/y", source_y)
        client.send_message(f"/table/{index}/rot", td_source_rot)
        client.send_message(f"/table/{index}/width", width_cm)
        client.send_message(f"/table/{index}/height", height_cm)

        table_id = str(table.get("id", f"table_{index}"))
        summaries.append(
            f"{table_id} source=({source_x:.3f}, {source_y:.3f}, {td_source_rot:.3f}) "
            f"target=({target_x:.3f}, {target_y:.3f}, {td_target_rot:.3f})"
        )

    return summaries


def print_startup(args: argparse.Namespace, scene_path: Path) -> None:
    """Print a short startup message."""
    print(f"OSC-Ziel: {args.host}:{args.port}")
    print(f"Scene-Datei: {scene_path}")
    print("Lese live Szene und sende Tabellen per OSC. Mit STRG+C beenden.")
    print(f"Layout mode: {DEFAULT_LAYOUT_MODE}")
    print("Controls: 1=input, 2=groupwork, 3=discussion, q=quit")


def print_layout_options() -> None:
    """Print the available layout mode options."""
    print("Controls: 1=input, 2=groupwork, 3=discussion, q=quit")


def set_layout_mode(mode: str, state_lock: threading.Lock, layout_state: dict[str, str]) -> None:
    """Set the current layout mode in a tiny shared state object."""
    global current_layout_mode
    with state_lock:
        current_layout_mode = mode
        layout_state["mode"] = mode
    print(f">>> Layout mode changed to: {mode}")


def apply_layout_mode_from_file(path: Path, state_lock: threading.Lock, layout_state: dict[str, str], last_file_mode: str | None) -> str | None:
    """Read the file and update the layout mode if it contains a valid value."""
    file_mode = load_learning_format(path)
    if file_mode is None or file_mode == last_file_mode:
        return last_file_mode

    global current_layout_mode
    with state_lock:
        current_layout_mode = file_mode
        layout_state["mode"] = file_mode
    print(f">>> Layout mode changed from file: {file_mode}")
    return file_mode


def input_thread(layout_state: dict[str, str], state_lock: threading.Lock) -> None:
    """Read layout mode changes from terminal input without blocking OSC sending."""
    print_layout_options()
    while True:
        if msvcrt is None:
            return

        if not msvcrt.kbhit():
            time.sleep(0.05)
            continue

        key = msvcrt.getwch()
        if key in ("\r", "\n", " ", "\t"):
            continue

        if key == "1":
            set_layout_mode("input", state_lock, layout_state)
        elif key == "2":
            set_layout_mode("groupwork", state_lock, layout_state)
        elif key == "3":
            set_layout_mode("discussion", state_lock, layout_state)
        elif key.lower() == "q":
            print("Beendet.")
            stop_event.set()
            return
        else:
            print_layout_options()


def main() -> None:
    """Main entry point."""
    args = parse_args()
    scene_path = Path(args.scene)
    client = SimpleUDPClient(args.host, args.port)
    layout_state = {"mode": DEFAULT_LAYOUT_MODE}
    state_lock = threading.Lock()
    file_path = learning_format_path()

    print_startup(args, scene_path)

    thread = threading.Thread(
        target=input_thread,
        args=(layout_state, state_lock),
        daemon=True,
    )
    thread.start()

    last_missing_notice = 0.0
    last_bad_json_notice = 0.0
    last_debug_print = 0.0
    last_learning_format_poll = 0.0
    last_file_mode: str | None = None

    try:
        while not stop_event.is_set():
            now = time.monotonic()
            if now - last_learning_format_poll >= LEARNING_FORMAT_POLL_SECONDS:
                last_file_mode = apply_layout_mode_from_file(
                    file_path,
                    state_lock,
                    layout_state,
                    last_file_mode,
                )
                last_learning_format_poll = now

            if not scene_path.exists():
                now = time.monotonic()
                if now - last_missing_notice >= 2.0:
                    print(f"Warte auf Datei: {scene_path}")
                    last_missing_notice = now
                time.sleep(args.interval)
                continue

            try:
                scene = load_scene(scene_path)
            except json.JSONDecodeError:
                now = time.monotonic()
                if now - last_bad_json_notice >= 1.0:
                    print("Scene-Datei ist gerade ungültig oder wird noch geschrieben, überspringe diesen Durchlauf.")
                    last_bad_json_notice = now
                time.sleep(args.interval)
                continue
            except OSError as exc:
                now = time.monotonic()
                if now - last_bad_json_notice >= 1.0:
                    print(f"Fehler beim Lesen der Scene-Datei: {exc}")
                    last_bad_json_notice = now
                time.sleep(args.interval)
                continue

            tables = scene.get("tables", [])
            if not isinstance(tables, list):
                tables = []

            with state_lock:
                layout_mode = current_layout_mode

            summaries = send_tables(client, tables, layout_mode)
            now = time.monotonic()
            if summaries and now - last_debug_print >= DEBUG_INTERVAL_SECONDS:
                print(f"mode={layout_mode} | sent {len(summaries)} tables | " + summaries[0])
                last_debug_print = now
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nBeendet.")


if __name__ == "__main__":
    main()
