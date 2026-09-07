"""Simple top-down room simulator for editing a CV-like scene without a real room.

This version uses only the Python standard library plus tkinter.
It provides editable tables, chairs, and persons in a 500 cm x 500 cm ROI and
writes the current scene to data/aisi/scenes/simulated/live_scene.json every
0.2 seconds.
"""

from __future__ import annotations

import copy
import json
import os
import platform
import random
import time
from pathlib import Path

if platform.system() == "Darwin":
    import matplotlib

    matplotlib.use("TkAgg")

from aisi.core.table_geometry import (
    TABLE_TYPE_NAMES,
    clamp_table_center_to_roi,
    get_table_geometry,
    world_footprint,
)

try:
    import tkinter as tk
except ImportError:
    print("Bitte installiere tkinter bzw. nutze eine Python-Installation mit tkinter-Unterstützung.")
    raise SystemExit(1)


ROI_WIDTH_CM = 500
ROI_HEIGHT_CM = 500
SCALE_PX_PER_CM = 2
WINDOW_WIDTH_PX = ROI_WIDTH_CM * SCALE_PX_PER_CM
WINDOW_HEIGHT_PX = ROI_HEIGHT_CM * SCALE_PX_PER_CM
MACOS_SCALE_PX_PER_CM = 1.4
MACOS_INITIAL_WINDOW_WIDTH_PX = 1000
MACOS_INITIAL_WINDOW_HEIGHT_PX = 800
MACOS_MINIMUM_WINDOW_WIDTH_PX = 760
MACOS_MINIMUM_WINDOW_HEIGHT_PX = 760
PERSON_RADIUS_CM = 40
CHAIR_RADIUS_CM = 30
SAVE_INTERVAL_SECONDS = 0.2
JITTER_RANGE_CM = 5.0
OCCLUSION_DROPOUT_PROBABILITY = 0.1

BG_COLOR = "#171717"
ROI_BORDER_COLOR = "#666666"
TABLE_COLOR = "#e8e8e8"
TABLE_SELECTED_COLOR = "#ffd36b"
CROSS_COLOR = "#97e597"
MARKER_COLOR = "#ff8f8f"
PERSON_COLOR = "#4bd46a"
PERSON_SELECTED_COLOR = "#89f0a0"
CHAIR_COLOR = "#b9b9b9"
CHAIR_SELECTED_COLOR = "#ffffff"
TEXT_COLOR = "#e6e6e6"


def repo_root() -> Path:
    """Return the repository root based on this file location."""
    return Path(__file__).resolve().parents[3]


def scene_file_path() -> Path:
    """Return the path for the continuously written scene JSON."""
    out_dir = repo_root() / "data" / "aisi" / "scenes" / "simulated"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / "live_scene.json"


def get_table_type_by_index(index: int) -> str:
    """Return the deterministic table type based on index.
    
    Cycles through: summit, sprint, rect
    """
    return TABLE_TYPE_NAMES[index % len(TABLE_TYPE_NAMES)]


def make_default_table(table_id: str, x_cm: float, y_cm: float, index: int) -> dict:
    """Create one default table from its canonical type geometry."""
    table_type = get_table_type_by_index(index)
    geometry = get_table_geometry(table_type)
    return {
        "id": table_id,
        "x_cm": x_cm,
        "y_cm": y_cm,
        "width_cm": geometry.nominal_width,
        "height_cm": geometry.nominal_depth,
        "rotation_deg": 0,
        "type": table_type,
    }


def make_default_tables() -> list[dict]:
    """Create the initial table layout."""
    return [
        make_default_table("table_0", 100, 100, 0),
        make_default_table("table_1", 290, 100, 1),
        make_default_table("table_2", 100, 320, 2),
        make_default_table("table_3", 290, 320, 3),
    ]


def next_object_number(items: list[dict], kind: str) -> int:
    """Return the next available numeric suffix for one scene object kind.

    IDs intentionally do not reuse a removed object's numeric suffix. This
    keeps an editor session deterministic and avoids an old object identity
    being silently assigned to a newly added object.
    """
    prefix = f"{kind}_"
    used_numbers = {
        int(str(item.get("id", ""))[len(prefix) :])
        for item in items
        if str(item.get("id", "")).startswith(prefix)
        and str(item.get("id", ""))[len(prefix) :].isdigit()
    }
    return max(used_numbers, default=-1) + 1


def next_object_id(items: list[dict], kind: str) -> str:
    """Return the next available ID for one scene object kind."""
    return f"{kind}_{next_object_number(items, kind)}"


def addition_offset(index: int) -> tuple[float, float]:
    """Return a small deterministic center-relative offset for a new item."""
    offsets = (
        (0.0, 0.0),
        (30.0, 0.0),
        (0.0, 30.0),
        (-30.0, 0.0),
        (0.0, -30.0),
        (30.0, 30.0),
        (-30.0, 30.0),
        (-30.0, -30.0),
        (30.0, -30.0),
    )
    return offsets[index % len(offsets)]


def make_added_table(tables: list[dict], table_id: str | None = None) -> dict:
    """Create a new rectangular table at a deterministic valid ROI position."""
    table_id = table_id or next_object_id(tables, "table")
    table_number = int(table_id.rsplit("_", 1)[1])
    offset_x, offset_y = addition_offset(table_number)
    x_cm, y_cm = clamp_table_center_to_roi("rect", 250.0 + offset_x, 250.0 + offset_y, 0.0)
    geometry = get_table_geometry("rect")
    return {
        "id": table_id,
        "x_cm": x_cm,
        "y_cm": y_cm,
        "width_cm": geometry.nominal_width,
        "height_cm": geometry.nominal_depth,
        "rotation_deg": 0.0,
        "type": "rect",
    }


def make_default_persons() -> list[dict]:
    """Create four simple person markers."""
    return [
        {"id": "person_0", "x_cm": 180, "y_cm": 260, "radius_cm": PERSON_RADIUS_CM},
        {"id": "person_1", "x_cm": 320, "y_cm": 260, "radius_cm": PERSON_RADIUS_CM},
        {"id": "person_2", "x_cm": 180, "y_cm": 380, "radius_cm": PERSON_RADIUS_CM},
        {"id": "person_3", "x_cm": 320, "y_cm": 380, "radius_cm": PERSON_RADIUS_CM},
    ]


def make_default_chairs() -> list[dict]:
    """Create four simple chair markers."""
    return [
        {"id": "chair_0", "x_cm": 120, "y_cm": 220, "radius_cm": CHAIR_RADIUS_CM},
        {"id": "chair_1", "x_cm": 380, "y_cm": 220, "radius_cm": CHAIR_RADIUS_CM},
        {"id": "chair_2", "x_cm": 120, "y_cm": 340, "radius_cm": CHAIR_RADIUS_CM},
        {"id": "chair_3", "x_cm": 380, "y_cm": 340, "radius_cm": CHAIR_RADIUS_CM},
    ]


def make_added_circle_item(
    items: list[dict], kind: str, radius_cm: float, item_id: str | None = None
) -> dict:
    """Create a new chair or person at a deterministic valid ROI position."""
    item_id = item_id or next_object_id(items, kind)
    item_number = int(item_id.rsplit("_", 1)[1])
    offset_x, offset_y = addition_offset(item_number)
    return {
        "id": item_id,
        "x_cm": clamp(250.0 + offset_x, radius_cm, ROI_WIDTH_CM - radius_cm),
        "y_cm": clamp(250.0 + offset_y, radius_cm, ROI_HEIGHT_CM - radius_cm),
        "radius_cm": radius_cm,
    }


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value into a range."""
    return max(low, min(high, value))


def world_to_screen(x_cm: float, y_cm: float) -> tuple[float, float]:
    """Convert cm coordinates to screen pixels."""
    return x_cm * SCALE_PX_PER_CM, y_cm * SCALE_PX_PER_CM


def screen_to_world(x_px: float, y_px: float) -> tuple[float, float]:
    """Convert screen pixels to cm coordinates."""
    return x_px / SCALE_PX_PER_CM, y_px / SCALE_PX_PER_CM


def table_screen_polygon(table: dict) -> list[tuple[float, float]]:
    """Return the canonical table footprint as canvas points in pixels."""
    points = world_footprint(
        table["type"],
        float(table["x_cm"]),
        float(table["y_cm"]),
        float(table["rotation_deg"]),
    )
    return [world_to_screen(x_cm, y_cm) for x_cm, y_cm in points]


def circle_hit_test(point: tuple[float, float], item: dict) -> bool:
    """Return True if a point lies inside a circle item."""
    px, py = point
    cx, cy = world_to_screen(item["x_cm"], item["y_cm"])
    radius_px = float(item["radius_cm"]) * SCALE_PX_PER_CM
    return ((px - cx) ** 2 + (py - cy) ** 2) <= radius_px ** 2


def point_in_polygon(point: tuple[float, float], polygon: list[tuple[float, float]]) -> bool:
    """Return True if the point lies inside the polygon."""
    x, y = point
    inside = False
    previous_index = len(polygon) - 1

    for index, (px, py) in enumerate(polygon):
        qx, qy = polygon[previous_index]
        if ((py > y) != (qy > y)) and (qy - py) != 0:
            intersection_x = (qx - px) * (y - py) / (qy - py) + px
            if x < intersection_x:
                inside = not inside
        previous_index = index

    return inside


def scene_payload(tables: list[dict], chairs: list[dict], persons: list[dict]) -> dict:
    """Build the JSON scene structure."""
    serialized_tables = []
    for table in tables:
        table_type = str(table["type"])
        geometry = get_table_geometry(table_type)
        serialized_tables.append(
            {
                "id": table["id"],
                "x_cm": round(table["x_cm"], 3),
                "y_cm": round(table["y_cm"], 3),
                "width_cm": geometry.nominal_width,
                "height_cm": geometry.nominal_depth,
                "rotation_deg": round(table["rotation_deg"], 3),
                "type": table_type,
            }
        )

    return {
        "scene_id": "simulated_live_scene",
        "source": "sim_room_editor",
        "roi": {
            "width_cm": ROI_WIDTH_CM,
            "height_cm": ROI_HEIGHT_CM,
        },
        "tables": serialized_tables,
        "chairs": [
            {
                "id": chair["id"],
                "x_cm": round(chair["x_cm"], 3),
                "y_cm": round(chair["y_cm"], 3),
                "radius_cm": chair["radius_cm"],
            }
            for chair in chairs
        ],
        "persons": [
            {
                "id": person["id"],
                "x_cm": round(person["x_cm"], 3),
                "y_cm": round(person["y_cm"], 3),
                "radius_cm": person["radius_cm"],
            }
            for person in persons
        ],
    }


def export_circle_items(items: list[dict], jitter_enabled: bool, occlusion_enabled: bool) -> list[dict]:
    """Build exported circle items with optional CV-like instability.

    The editor state remains stable. Only the serialized JSON output gets
    optional jitter and occlusion dropout.
    """
    exported_items: list[dict] = []

    for item in items:
        if occlusion_enabled and random.random() < OCCLUSION_DROPOUT_PROBABILITY:
            continue

        export_x_cm = float(item["x_cm"])
        export_y_cm = float(item["y_cm"])
        if jitter_enabled:
            export_x_cm += random.uniform(-JITTER_RANGE_CM, JITTER_RANGE_CM)
            export_y_cm += random.uniform(-JITTER_RANGE_CM, JITTER_RANGE_CM)

        exported_items.append(
            {
                "id": item["id"],
                "x_cm": round(export_x_cm, 3),
                "y_cm": round(export_y_cm, 3),
                "radius_cm": item["radius_cm"],
            }
        )

    return exported_items


def save_scene(
    path: Path,
    tables: list[dict],
    chairs: list[dict],
    persons: list[dict],
    jitter_enabled: bool = False,
    occlusion_enabled: bool = False,
) -> None:
    """Write the current scene to disk."""
    payload = scene_payload(
        tables,
        export_circle_items(chairs, jitter_enabled=jitter_enabled, occlusion_enabled=occlusion_enabled),
        export_circle_items(persons, jitter_enabled=jitter_enabled, occlusion_enabled=occlusion_enabled),
    )
    temp_path = path.with_suffix(".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        os.replace(temp_path, path)
    except Exception as exc:
        print(f"Warnung: Szene konnte nicht gespeichert werden: {exc}")


def reset_tables(tables: list[dict], initial_tables: list[dict]) -> None:
    """Restore all tables to their original start positions."""
    tables[:] = copy.deepcopy(initial_tables)


def reset_items(items: list[dict], initial_items: list[dict]) -> None:
    """Restore circle-based items to their original start positions."""
    items[:] = copy.deepcopy(initial_items)


def print_help() -> None:
    """Print the keyboard and mouse controls."""
    print("Bedienung:")
    print("  T: Typ des ausgewählten Tischs wechseln")
    print("  A/C/P: Tisch/Stuhl/Person hinzufügen")
    print("  Entf/Backspace: ausgewähltes Objekt löschen")
    print("  Linksklick auf einen Tisch: auswählen")
    print("  Linksklick und ziehen: Tisch verschieben")
    print("  Q: ausgewählten Tisch um -5 Grad drehen")
    print("  E: ausgewählten Tisch um +5 Grad drehen")
    print("  R: alle Tische auf Startpositionen zurücksetzen")
    print("  S: sofort speichern")
    print("  J: Jitter für Personen/Stühle an/aus")
    print("  O: Occlusion-Dropout für Personen/Stühle an/aus")
    print("  ESC: beenden")
    print(f"Autosave: {scene_file_path()}")


def table_label(table: dict) -> str:
    """Return a short label for a table."""
    return f"{table['id']} [{table['type']}]"


def cycle_table_type(table: dict) -> str:
    """Advance one table to the next canonical type and keep its pose identity."""
    current_index = TABLE_TYPE_NAMES.index(table["type"])
    table["type"] = TABLE_TYPE_NAMES[(current_index + 1) % len(TABLE_TYPE_NAMES)]
    geometry = get_table_geometry(table["type"])
    table["width_cm"] = geometry.nominal_width
    table["height_cm"] = geometry.nominal_depth
    table["x_cm"], table["y_cm"] = clamp_table_center_to_roi(
        table["type"], table["x_cm"], table["y_cm"], table["rotation_deg"]
    )
    return table["type"]


class SimRoomEditor:
    """Small tkinter-based room editor."""

    def __init__(self) -> None:
        global SCALE_PX_PER_CM, WINDOW_WIDTH_PX, WINDOW_HEIGHT_PX

        self.root = tk.Tk()
        self.root.title("AISI Sim Room Editor")
        self.root.configure(bg=BG_COLOR)
        if self.root.tk.call("tk", "windowingsystem") == "aqua":
            # A fixed 1000 px square canvas exceeds the usable height of many
            # Mac displays once window chrome and the controls are included.
            # This is display scaling only; all scene coordinates remain cm.
            SCALE_PX_PER_CM = MACOS_SCALE_PX_PER_CM
            WINDOW_WIDTH_PX = round(ROI_WIDTH_CM * SCALE_PX_PER_CM)
            WINDOW_HEIGHT_PX = round(ROI_HEIGHT_CM * SCALE_PX_PER_CM)
            self.root.geometry(
                f"{MACOS_INITIAL_WINDOW_WIDTH_PX}x{MACOS_INITIAL_WINDOW_HEIGHT_PX}"
            )
            self.root.minsize(
                MACOS_MINIMUM_WINDOW_WIDTH_PX, MACOS_MINIMUM_WINDOW_HEIGHT_PX
            )
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH_PX,
            height=WINDOW_HEIGHT_PX,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.controls = tk.Frame(self.root, bg=BG_COLOR)
        self.controls.pack(fill="x", pady=(6, 0))
        tk.Button(self.controls, text="+ Table", command=self.add_table).pack(side="left", padx=(0, 4))
        tk.Button(self.controls, text="+ Chair", command=self.add_chair).pack(side="left", padx=4)
        tk.Button(self.controls, text="+ Person", command=self.add_person).pack(side="left", padx=4)
        tk.Button(self.controls, text="Remove selected", command=self.remove_selected).pack(side="left", padx=4)

        self.tables = make_default_tables()
        self.chairs = make_default_chairs()
        self.persons = make_default_persons()
        self.initial_tables = copy.deepcopy(self.tables)
        self.initial_chairs = copy.deepcopy(self.chairs)
        self.initial_persons = copy.deepcopy(self.persons)
        self.next_table_number = next_object_number(self.tables, "table")
        self.next_chair_number = next_object_number(self.chairs, "chair")
        self.next_person_number = next_object_number(self.persons, "person")
        self.selected_kind: str | None = None
        self.selected_id: str | None = None
        self.dragging = False
        self.drag_offset_x_cm = 0.0
        self.drag_offset_y_cm = 0.0
        self.last_save_time = 0.0
        self.jitter_enabled = False
        self.occlusion_enabled = False
        self.running = True

        self.root.bind("<Escape>", lambda event: self.close())
        self.root.bind("<q>", lambda event: self.rotate_selected(-5))
        self.root.bind("<Q>", lambda event: self.rotate_selected(-5))
        self.root.bind("<e>", lambda event: self.rotate_selected(5))
        self.root.bind("<E>", lambda event: self.rotate_selected(5))
        self.root.bind("<r>", lambda event: self.reset_all())
        self.root.bind("<R>", lambda event: self.reset_all())
        self.root.bind("<s>", lambda event: self.save_now())
        self.root.bind("<S>", lambda event: self.save_now())
        self.root.bind("<j>", lambda event: self.toggle_jitter())
        self.root.bind("<J>", lambda event: self.toggle_jitter())
        self.root.bind("<o>", lambda event: self.toggle_occlusion())
        self.root.bind("<O>", lambda event: self.toggle_occlusion())
        self.root.bind("<t>", lambda event: self.cycle_selected_table_type())
        self.root.bind("<T>", lambda event: self.cycle_selected_table_type())
        self.root.bind("<a>", lambda event: self.add_table())
        self.root.bind("<A>", lambda event: self.add_table())
        self.root.bind("<c>", lambda event: self.add_chair())
        self.root.bind("<C>", lambda event: self.add_chair())
        self.root.bind("<p>", lambda event: self.add_person())
        self.root.bind("<P>", lambda event: self.add_person())
        self.root.bind("<Delete>", lambda event: self.remove_selected())
        self.root.bind("<BackSpace>", lambda event: self.remove_selected())

        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

    def close(self) -> None:
        """Stop the app."""
        self.running = False
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def save_now(self) -> None:
        """Save immediately and refresh the autosave timer."""
        save_scene(
            scene_file_path(),
            self.tables,
            self.chairs,
            self.persons,
            jitter_enabled=self.jitter_enabled,
            occlusion_enabled=self.occlusion_enabled,
        )
        self.last_save_time = time.monotonic()

    def toggle_jitter(self) -> None:
        """Toggle export-only jitter for persons and chairs."""
        self.jitter_enabled = not self.jitter_enabled
        print(f"Jitter: {'on' if self.jitter_enabled else 'off'}")
        self.redraw()

    def toggle_occlusion(self) -> None:
        """Toggle export-only dropout for persons and chairs."""
        self.occlusion_enabled = not self.occlusion_enabled
        print(f"Occlusion: {'on' if self.occlusion_enabled else 'off'}")
        self.redraw()

    def reset_all(self) -> None:
        """Reset the tables to the initial layout."""
        reset_tables(self.tables, self.initial_tables)
        reset_items(self.chairs, self.initial_chairs)
        reset_items(self.persons, self.initial_persons)
        self.selected_kind = None
        self.selected_id = None
        self.dragging = False
        self.save_now()
        self.redraw()

    def select_item(self, kind: str, item_id: str) -> None:
        """Make one newly created or clicked object the explicit selection."""
        self.selected_kind = kind
        self.selected_id = item_id
        self.dragging = False

    def add_table(self) -> None:
        """Append and select one new canonical rectangular table."""
        table = make_added_table(self.tables, table_id=f"table_{self.next_table_number}")
        self.next_table_number += 1
        self.tables.append(table)
        self.select_item("table", table["id"])
        self.save_now()
        self.redraw()

    def add_chair(self) -> None:
        """Append and select one new chair."""
        chair = make_added_circle_item(
            self.chairs, "chair", CHAIR_RADIUS_CM, item_id=f"chair_{self.next_chair_number}"
        )
        self.next_chair_number += 1
        self.chairs.append(chair)
        self.select_item("chair", chair["id"])
        self.save_now()
        self.redraw()

    def add_person(self) -> None:
        """Append and select one new person."""
        person = make_added_circle_item(
            self.persons, "person", PERSON_RADIUS_CM, item_id=f"person_{self.next_person_number}"
        )
        self.next_person_number += 1
        self.persons.append(person)
        self.select_item("person", person["id"])
        self.save_now()
        self.redraw()

    def remove_selected(self) -> None:
        """Remove exactly the currently selected object, if it still exists."""
        if self.selected_id is None:
            return

        items: list[dict] | None = None
        if self.selected_kind == "table":
            items = self.tables
        elif self.selected_kind == "chair":
            items = self.chairs
        elif self.selected_kind == "person":
            items = self.persons
        if items is None:
            return

        for index, item in enumerate(items):
            if item["id"] == self.selected_id:
                del items[index]
                self.selected_kind = None
                self.selected_id = None
                self.dragging = False
                self.save_now()
                self.redraw()
                return

    def rotate_selected(self, delta_deg: float) -> None:
        """Rotate the selected table."""
        if self.selected_kind != "table" or self.selected_id is None:
            return
        for table in self.tables:
            if table["id"] == self.selected_id:
                table["rotation_deg"] += delta_deg
                table["x_cm"], table["y_cm"] = clamp_table_center_to_roi(
                    table["type"], table["x_cm"], table["y_cm"], table["rotation_deg"]
                )
                break
        self.save_now()
        self.redraw()

    def cycle_selected_table_type(self) -> None:
        """Cycle the selected table through the canonical table types."""
        table = self.selected_table()
        if table is None:
            return

        cycle_table_type(table)
        print(f"Tischtyp {table['id']}: {table['type']}")
        self.save_now()
        self.redraw()

    def selected_table(self) -> dict | None:
        """Return the currently selected table, if any."""
        for table in self.tables:
            if table["id"] == self.selected_id and self.selected_kind == "table":
                return table
        return None


    def selected_circle_item(self) -> dict | None:
        """Return the currently selected chair or person, if any."""
        if self.selected_kind == "person":
            for person in self.persons:
                if person["id"] == self.selected_id:
                    return person
        if self.selected_kind == "chair":
            for chair in self.chairs:
                if chair["id"] == self.selected_id:
                    return chair
        return None

    def on_mouse_down(self, event: tk.Event) -> None:
        """Select a table or start dragging it."""
        mouse_point = (event.x, event.y)

        self.selected_kind = None
        self.selected_id = None

        # Selection priority: persons > chairs > tables.
        for person in reversed(self.persons):
            if circle_hit_test(mouse_point, person):
                self.selected_kind = "person"
                self.selected_id = person["id"]
                mouse_x_cm, mouse_y_cm = screen_to_world(event.x, event.y)
                self.drag_offset_x_cm = mouse_x_cm - person["x_cm"]
                self.drag_offset_y_cm = mouse_y_cm - person["y_cm"]
                self.dragging = True
                self.redraw()
                return

        for chair in reversed(self.chairs):
            if circle_hit_test(mouse_point, chair):
                self.selected_kind = "chair"
                self.selected_id = chair["id"]
                mouse_x_cm, mouse_y_cm = screen_to_world(event.x, event.y)
                self.drag_offset_x_cm = mouse_x_cm - chair["x_cm"]
                self.drag_offset_y_cm = mouse_y_cm - chair["y_cm"]
                self.dragging = True
                self.redraw()
                return

        for table in reversed(self.tables):
            if point_in_polygon(mouse_point, table_screen_polygon(table)):
                self.selected_kind = "table"
                self.selected_id = table["id"]
                mouse_x_cm, mouse_y_cm = screen_to_world(event.x, event.y)
                self.drag_offset_x_cm = mouse_x_cm - table["x_cm"]
                self.drag_offset_y_cm = mouse_y_cm - table["y_cm"]
                self.dragging = True
                break

        self.redraw()

    def on_mouse_drag(self, event: tk.Event) -> None:
        """Move the currently selected item."""
        if not self.dragging or self.selected_id is None:
            return

        mouse_x_cm, mouse_y_cm = screen_to_world(event.x, event.y)
        if self.selected_kind == "table":
            table = self.selected_table()
            if table is None:
                return

            table["x_cm"], table["y_cm"] = clamp_table_center_to_roi(
                table["type"],
                mouse_x_cm - self.drag_offset_x_cm,
                mouse_y_cm - self.drag_offset_y_cm,
                table["rotation_deg"],
            )
        elif self.selected_kind == "person":
            person = self.selected_circle_item()
            if person is None:
                return
            radius = float(person["radius_cm"])
            person["x_cm"] = clamp(mouse_x_cm - self.drag_offset_x_cm, radius, ROI_WIDTH_CM - radius)
            person["y_cm"] = clamp(mouse_y_cm - self.drag_offset_y_cm, radius, ROI_HEIGHT_CM - radius)
        elif self.selected_kind == "chair":
            chair = self.selected_circle_item()
            if chair is None:
                return
            radius = float(chair["radius_cm"])
            chair["x_cm"] = clamp(mouse_x_cm - self.drag_offset_x_cm, radius, ROI_WIDTH_CM - radius)
            chair["y_cm"] = clamp(mouse_y_cm - self.drag_offset_y_cm, radius, ROI_HEIGHT_CM - radius)
        self.redraw()

    def on_mouse_up(self, event: tk.Event) -> None:
        """Stop dragging."""
        self.dragging = False

    def draw_rotated_polygon(self, points: list[tuple[float, float]], outline: str, width: int) -> None:
        """Draw a rotated polygon on the canvas."""
        flat_points: list[float] = []
        for x, y in points:
            flat_points.extend([x, y])
        self.canvas.create_polygon(*flat_points, fill="", outline=outline, width=width)

    def draw_cross(self, cx: float, cy: float, size: float, color: str, width: int = 2) -> None:
        """Draw a small cross."""
        self.canvas.create_line(cx - size, cy, cx + size, cy, fill=color, width=width)
        self.canvas.create_line(cx, cy - size, cx, cy + size, fill=color, width=width)

    def draw_circle_item(self, item: dict, outline_color: str, width: int = 2) -> None:
        """Draw a circle-based item such as a person or chair."""
        cx, cy = world_to_screen(item["x_cm"], item["y_cm"])
        radius_px = float(item["radius_cm"]) * SCALE_PX_PER_CM
        self.canvas.create_oval(
            cx - radius_px,
            cy - radius_px,
            cx + radius_px,
            cy + radius_px,
            outline=outline_color,
            width=width,
        )

    def redraw(self) -> None:
        """Redraw the entire scene."""
        self.canvas.delete("all")

        self.canvas.create_rectangle(
            0,
            0,
            WINDOW_WIDTH_PX,
            WINDOW_HEIGHT_PX,
            fill=BG_COLOR,
            outline=ROI_BORDER_COLOR,
            width=2,
        )

        for table in self.tables:
            points = table_screen_polygon(table)
            selected = self.selected_kind == "table" and table["id"] == self.selected_id
            outline_color = TABLE_SELECTED_COLOR if selected else TABLE_COLOR
            self.draw_rotated_polygon(points, outline=outline_color, width=3)

            cx, cy = world_to_screen(table["x_cm"], table["y_cm"])
            self.draw_cross(cx, cy, 14, CROSS_COLOR, width=2)

            for px, py in points:
                marker = 7
                self.canvas.create_line(px - marker, py, px + marker, py, fill=MARKER_COLOR, width=1)
                self.canvas.create_line(px, py - marker, px, py + marker, fill=MARKER_COLOR, width=1)

            self.canvas.create_text(
                cx,
                cy + 22,
                text=table_label(table),
                fill=TEXT_COLOR,
                font=("TkDefaultFont", 10, "bold"),
            )

        for chair in self.chairs:
            selected = self.selected_kind == "chair" and chair["id"] == self.selected_id
            outline_color = CHAIR_SELECTED_COLOR if selected else CHAIR_COLOR
            self.draw_circle_item(chair, outline_color=outline_color, width=3 if selected else 2)
            cx, cy = world_to_screen(chair["x_cm"], chair["y_cm"])
            # Keep chair labels centered exactly on the circle midpoint.
            self.canvas.create_text(cx, cy, text=chair["id"], fill=TEXT_COLOR, font=("TkDefaultFont", 9))

        for person in self.persons:
            selected = self.selected_kind == "person" and person["id"] == self.selected_id
            outline_color = PERSON_SELECTED_COLOR if selected else PERSON_COLOR
            self.draw_circle_item(person, outline_color=outline_color, width=3 if selected else 2)
            cx, cy = world_to_screen(person["x_cm"], person["y_cm"])
            # Keep person labels centered exactly on the circle midpoint.
            self.canvas.create_text(cx, cy, text=person["id"], fill=TEXT_COLOR, font=("TkDefaultFont", 9))

        self.canvas.create_text(
            8,
            8,
            anchor="nw",
            text="LMB: select/drag   A/C/P: add   Del: remove   Q/E: rotate   T: type   R: reset   S: save   J/O: CV sim   ESC: quit",
            fill=TEXT_COLOR,
            font=("TkDefaultFont", 10),
        )
        self.canvas.create_text(
            8,
            28,
            anchor="nw",
            text=f"Autosave: {scene_file_path().name}",
            fill=TEXT_COLOR,
            font=("TkDefaultFont", 10),
        )
        self.canvas.create_text(
            8,
            48,
            anchor="nw",
            text=(
                f"Jitter: {'on' if self.jitter_enabled else 'off'} | "
                f"Occlusion: {'on' if self.occlusion_enabled else 'off'}"
            ),
            fill=TEXT_COLOR,
            font=("TkDefaultFont", 10),
        )

    def autosave_tick(self) -> None:
        """Write the JSON file every 0.2 seconds."""
        if not self.running:
            return

        now = time.monotonic()
        if now - self.last_save_time >= SAVE_INTERVAL_SECONDS:
            save_scene(
                scene_file_path(),
                self.tables,
                self.chairs,
                self.persons,
                jitter_enabled=self.jitter_enabled,
                occlusion_enabled=self.occlusion_enabled,
            )
            self.last_save_time = now

        self.root.after(50, self.autosave_tick)

    def run(self) -> None:
        """Start the tkinter event loop."""
        print_help()
        self.save_now()
        self.redraw()
        self.autosave_tick()
        self.root.mainloop()


def main() -> None:
    """Run the room editor."""
    editor = SimRoomEditor()
    editor.run()


if __name__ == "__main__":
    main()
