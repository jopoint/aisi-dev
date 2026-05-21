"""Send the simulated room editor scene to TouchDesigner via OSC.

This script continuously reads data/aisi/scenes/simulated/live_scene.json and
sends the table values to TouchDesigner using python-osc.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:
    print("Bitte installiere python-osc mit: pip install python-osc")
    raise SystemExit(1)


DEFAULT_OSC_HOST = "127.0.0.1"
DEFAULT_OSC_PORT = 9000
DEFAULT_INTERVAL_SECONDS = 0.05

GROUPWORK_TARGETS = [
    {"x_cm": 150.0, "y_cm": 160.0, "rotation_deg": 0.0},
    {"x_cm": 350.0, "y_cm": 160.0, "rotation_deg": 0.0},
    {"x_cm": 150.0, "y_cm": 340.0, "rotation_deg": 0.0},
    {"x_cm": 350.0, "y_cm": 340.0, "rotation_deg": 0.0},
]

# TouchDesigner uses inverted Y coordinates, so rotation is inverted for visual consistency.


def repo_root() -> Path:
    """Return the repository root based on this file location."""
    return Path(__file__).resolve().parents[3]


def default_scene_path() -> Path:
    """Return the default path to the simulated live scene JSON."""
    return repo_root() / "data" / "aisi" / "scenes" / "simulated" / "live_scene.json"


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


def send_tables(client: SimpleUDPClient, tables: list[dict[str, Any]]) -> list[str]:
    """Send all tables via OSC and return short debug summaries."""
    summaries: list[str] = []
    for index, table in enumerate(tables):
        source_x = float(table.get("x_cm", 0.0))
        source_y = float(table.get("y_cm", 0.0))
        source_rot = float(table.get("rotation_deg", 0.0))
        td_source_rot = -source_rot
        width_cm = float(table.get("width_cm", 0.0))
        height_cm = float(table.get("height_cm", 0.0))

        if index < len(GROUPWORK_TARGETS):
            target_x = float(GROUPWORK_TARGETS[index]["x_cm"])
            target_y = float(GROUPWORK_TARGETS[index]["y_cm"])
            target_rot = float(GROUPWORK_TARGETS[index]["rotation_deg"])
        else:
            target_x = source_x
            target_y = source_y
            target_rot = source_rot
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


def main() -> None:
    """Main entry point."""
    args = parse_args()
    scene_path = Path(args.scene)
    client = SimpleUDPClient(args.host, args.port)

    print_startup(args, scene_path)

    last_missing_notice = 0.0
    last_bad_json_notice = 0.0

    try:
        while True:
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

            summaries = send_tables(client, tables)
            if summaries:
                print(f"sent {len(summaries)} tables | " + " | ".join(summaries))
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nBeendet.")


if __name__ == "__main__":
    main()
