"""Focused retries for the live vision scene writer/OSC reader hand-off."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from aisi.app.sim_scene_to_osc import RetainingSceneReader, load_scene
from aisi.app.vision_live_to_aisi_scene import atomic_write_scene


class LiveSceneFileContentionTests(unittest.TestCase):
    def test_writer_recovers_from_transient_permission_error_on_replace(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "vision_live_scene.json"
            real_replace = __import__("os").replace
            calls = 0

            def replace_once_locked(source: str, target: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise PermissionError("temporarily locked")
                real_replace(source, target)

            with patch("aisi.app.vision_live_to_aisi_scene.os.replace", side_effect=replace_once_locked), patch(
                "aisi.app.vision_live_to_aisi_scene.time.sleep"
            ) as sleep:
                atomic_write_scene(destination, {"tables": [{"id": "table_00"}]})

            self.assertEqual(calls, 2)
            sleep.assert_called_once_with(0.005)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["tables"][0]["id"], "table_00")
            self.assertEqual(list(destination.parent.glob("*.tmp")), [])

    def test_writer_cleans_temp_file_when_replace_retries_are_exhausted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "vision_live_scene.json"

            with patch(
                "aisi.app.vision_live_to_aisi_scene.os.replace",
                side_effect=PermissionError("still locked"),
            ), patch("aisi.app.vision_live_to_aisi_scene.time.sleep"):
                with self.assertRaises(PermissionError):
                    atomic_write_scene(destination, {"tables": []})

            self.assertEqual(list(destination.parent.glob("*.tmp")), [])

    def test_reader_recovers_from_transient_permission_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            scene_path = Path(temporary_directory) / "vision_live_scene.json"
            scene_path.write_text('{"tables": [{"id": "table_00"}]}', encoding="utf-8")
            real_open = Path.open
            calls = 0

            def open_once_locked(path: Path, *args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise PermissionError("temporarily locked")
                return real_open(path, *args, **kwargs)

            with patch("aisi.app.sim_scene_to_osc.Path.open", new=open_once_locked):
                loaded = load_scene(scene_path, sleep=lambda _delay: None)

            self.assertEqual(calls, 2)
            self.assertEqual(loaded["tables"][0]["id"], "table_00")

    def test_exhausted_read_retries_preserve_the_previous_valid_scene(self) -> None:
        previous_scene = {"tables": [{"id": "table_00"}]}
        scene_path = Path("vision_live_scene.json")
        reader = RetainingSceneReader()

        with patch("aisi.app.sim_scene_to_osc.load_scene", side_effect=[previous_scene, PermissionError("still locked")]):
            self.assertEqual(reader.load(scene_path), previous_scene)
            self.assertIsNone(reader.load(scene_path))

        self.assertEqual(reader.last_valid_scene, previous_scene)


if __name__ == "__main__":
    unittest.main()
