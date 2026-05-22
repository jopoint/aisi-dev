"""Simple layout rules for the AISI simulation pipeline.

This module is an adapter layer between the live scene and the target layout.
For now, it only returns the previous static presets.
Later, responsive layout logic can be added here.
"""


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


def compute_target_layout(scene: dict, learning_format: str) -> list[dict]:
    """Return target table layout for the selected learning format."""

    if learning_format not in LAYOUT_MODES:
        learning_format = "input"

    return LAYOUT_MODES[learning_format]