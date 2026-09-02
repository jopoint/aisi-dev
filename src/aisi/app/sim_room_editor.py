"""Simple top-down room simulator for editing a CV-like scene without a real room.

This version uses only the Python standard library plus tkinter.
It shows four editable tables in a 500 cm x 500 cm ROI and writes the current
scene to data/aisi/scenes/simulated/live_scene.json every 0.2 seconds.
"""

from __future__ import annotations

import copy
import json
import math
import os
import random
import time
from pathlib import Path

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
TABLE_WIDTH_CM = 133
TABLE_HEIGHT_CM = 67
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
    return ["summit", "sprint", "rect"][index % 3]


def make_default_tables() -> list[dict]:
    """Create the initial table layout."""
    return [
        {
            "id": "table_0",
            "x_cm": 100,
            "y_cm": 100,
            "width_cm": TABLE_WIDTH_CM,
            "height_cm": TABLE_HEIGHT_CM,
            "rotation_deg": 0,
            "type": get_table_type_by_index(0),
        },
        {
            "id": "table_1",
            "x_cm": 290,
            "y_cm": 100,
            "width_cm": TABLE_WIDTH_CM,
            "height_cm": TABLE_HEIGHT_CM,
            "rotation_deg": 0,
            "type": get_table_type_by_index(1),
        },
        {
            "id": "table_2",
            "x_cm": 100,
            "y_cm": 320,
            "width_cm": TABLE_WIDTH_CM,
            "height_cm": TABLE_HEIGHT_CM,
            "rotation_deg": 0,
            "type": get_table_type_by_index(2),
        },
        {
            "id": "table_3",
            "x_cm": 290,
            "y_cm": 320,
            "width_cm": TABLE_WIDTH_CM,
            "height_cm": TABLE_HEIGHT_CM,
            "rotation_deg": 0,
            "type": get_table_type_by_index(3),
        },
    ]


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


def clamp(value: float, low: float, high: float) -> float:
    """Clamp a numeric value into a range."""
    return max(low, min(high, value))


def world_to_screen(x_cm: float, y_cm: float) -> tuple[float, float]:
    """Convert cm coordinates to screen pixels."""
    return x_cm * SCALE_PX_PER_CM, y_cm * SCALE_PX_PER_CM


def screen_to_world(x_px: float, y_px: float) -> tuple[float, float]:
    """Convert screen pixels to cm coordinates."""
    return x_px / SCALE_PX_PER_CM, y_px / SCALE_PX_PER_CM


def rotated_corners(table: dict) -> list[tuple[float, float]]:
    """Return the four table corners as canvas points in pixels."""
    cx, cy = world_to_screen(table["x_cm"], table["y_cm"])
    half_w = table["width_cm"] * SCALE_PX_PER_CM / 2.0
    half_h = table["height_cm"] * SCALE_PX_PER_CM / 2.0
    angle = math.radians(table["rotation_deg"])
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    local_points = [
        (-half_w, -half_h),
        (half_w, -half_h),
        (half_w, half_h),
        (-half_w, half_h),
    ]

    points = []
    for lx, ly in local_points:
        rx = lx * cos_a - ly * sin_a
        ry = lx * sin_a + ly * cos_a
        points.append((cx + rx, cy + ry))
    return points


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
    return {
        "scene_id": "simulated_live_scene",
        "source": "sim_room_editor",
        "roi": {
            "width_cm": ROI_WIDTH_CM,
            "height_cm": ROI_HEIGHT_CM,
        },
        "tables": [
            {
                "id": table["id"],
                "x_cm": round(table["x_cm"], 3),
                "y_cm": round(table["y_cm"], 3),
                "width_cm": table["width_cm"],
                "height_cm": table["height_cm"],
                "rotation_deg": round(table["rotation_deg"], 3),
                "type": table.get("type", "summit"),
            }
            for table in tables
        ],
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
    return table["id"]


class SimRoomEditor:
    """Small tkinter-based room editor."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("AISI Sim Room Editor")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_WIDTH_PX,
            height=WINDOW_HEIGHT_PX,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.tables = make_default_tables()
        self.chairs = make_default_chairs()
        self.persons = make_default_persons()
        self.initial_tables = copy.deepcopy(self.tables)
        self.initial_chairs = copy.deepcopy(self.chairs)
        self.initial_persons = copy.deepcopy(self.persons)
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

    def rotate_selected(self, delta_deg: float) -> None:
        """Rotate the selected table."""
        if self.selected_kind != "table" or self.selected_id is None:
            return
        for table in self.tables:
            if table["id"] == self.selected_id:
                table["rotation_deg"] += delta_deg
                break
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
            if point_in_polygon(mouse_point, rotated_corners(table)):
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

            half_w = table["width_cm"] / 2.0
            half_h = table["height_cm"] / 2.0
            table["x_cm"] = clamp(mouse_x_cm - self.drag_offset_x_cm, half_w, ROI_WIDTH_CM - half_w)
            table["y_cm"] = clamp(mouse_y_cm - self.drag_offset_y_cm, half_h, ROI_HEIGHT_CM - half_h)
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
            points = rotated_corners(table)
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
            text="LMB: select/drag   Q/E: rotate   R: reset   S: save   J/O: CV sim   ESC: quit",
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
