from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from aisi.app.learning_format_server import (
    build_html,
    clamp_transformation_strength,
    default_state,
)
from aisi.app.sim_scene_to_osc import (
    DEFAULT_TRANSFORMATION_STRENGTH,
    load_learning_settings,
)


class LearningFormatServerTests(unittest.TestCase):
    def test_interface_and_default_state_restore_the_strength_control(self) -> None:
        state = default_state()
        html = build_html("groupwork", True, False, 0.25)

        self.assertEqual(state["transformation_strength"], 1.0)
        self.assertIn("Umbauintensität", html)
        self.assertIn('type="range"', html)
        self.assertIn('value="25"', html)
        self.assertEqual(clamp_transformation_strength("invalid"), 1.0)
        self.assertEqual(DEFAULT_TRANSFORMATION_STRENGTH, 1.0)

    def test_sender_uses_saved_strength_in_saved_state(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "learning_format.json"
            path.write_text(
                json.dumps(
                    {
                        "learning_format": "groupwork",
                        "show_persons": False,
                        "show_chairs": True,
                        "transformation_strength": 0.0,
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(load_learning_settings(path), ("groupwork", False, True, 0.0))

    def test_activity_parameters_are_persisted_and_only_relevant_controls_are_rendered(self) -> None:
        state = default_state()
        self.assertEqual(state["participants"], 4)
        self.assertEqual(state["number_of_groups"], 2)
        self.assertFalse(state["adaptive_layout_preview"])
        html = build_html("input", True, True, 1.0, participants=7, number_of_groups=3, presentation_side="north")
        self.assertIn('name="participants"', html)
        self.assertIn('name="number_of_groups"', html)
        self.assertIn('name="presentation_side"', html)
        self.assertIn('value="north" selected', html)
        self.assertIn('name="adaptive_layout_preview"', html)
