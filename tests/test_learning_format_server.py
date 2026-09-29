from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from aisi.app.learning_format_server import build_html, default_state
from aisi.app.sim_scene_to_osc import SIMULATION_TRANSFORMATION_STRENGTH, load_learning_settings


class LearningFormatServerTests(unittest.TestCase):
    def test_interface_and_default_state_have_no_strength_control(self) -> None:
        state = default_state()
        html = build_html("groupwork", True, False)

        self.assertNotIn("transformation_strength", state)
        self.assertNotIn("Umbauintensität", html)
        self.assertNotIn('type="range"', html)
        self.assertEqual(SIMULATION_TRANSFORMATION_STRENGTH, 1.0)

    def test_sender_ignores_legacy_strength_in_saved_state(self) -> None:
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
            self.assertEqual(load_learning_settings(path), ("groupwork", False, True))
