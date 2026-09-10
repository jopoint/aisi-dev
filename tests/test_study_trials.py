from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

from aisi.app.study_trials import StudyTask, StudyVariant, load_trial_definitions
from aisi.core.table_geometry import convex_polygons_intersect, polygon_inside_roi, world_footprint


class StudyTrialTests(unittest.TestCase):
    def _write(self, payload: object) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "trials.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_valid_definition_loads_task_variant_and_pose(self) -> None:
        trials = load_trial_definitions(self._write({"schema_version": 1, "home_positions": {"P_left": {"x_cm": 190, "y_cm": 395}}, "trials": [{"task_id": "T2", "variant": "B", "source_pose": {"x_cm": 100, "y_cm": 200, "rotation_deg": 90}, "target_pose": {"x_cm": 321, "y_cm": 123, "rotation_deg": 90}, "home_pose_reference": "P_left", "distractor_tables": [{"x_cm": 1, "y_cm": 2, "rotation_deg": 3}], "participant_start_positions": [{"id": "P1", "x_cm": 190, "y_cm": 395, "radius_cm": 40}], "notes": "example"}]}))
        trial = trials[(StudyTask.T2, StudyVariant.B)]
        self.assertEqual((trial.target_x_cm, trial.target_y_cm, trial.target_rotation_deg), (321.0, 123.0, 90.0))
        self.assertEqual((trial.source_pose.x_cm, trial.source_pose.y_cm), (100.0, 200.0))
        self.assertEqual((trial.home_pose_reference, trial.home_pose.x_cm), ("P_left", 190.0))
        self.assertEqual(len(trial.distractor_tables), 1)
        self.assertEqual(
            (trial.participant_start_positions[0].participant_id,
             trial.participant_start_positions[0].radius_cm),
            ("P1", 40.0),
        )
        self.assertEqual(trial.notes, "example")

    def test_malformed_definition_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "target_pose.x_cm"):
            load_trial_definitions(self._write({"schema_version": 1, "trials": [{"task_id": "T1", "variant": "A", "source_pose": {"x_cm": 1, "y_cm": 2, "rotation_deg": 3}, "target_pose": {"y_cm": 1, "rotation_deg": 2}}]}))

    def test_malformed_participant_start_position_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "participant_start_positions\\[0\\].radius_cm"):
            load_trial_definitions(self._write({"schema_version": 1, "trials": [{"task_id": "T1", "variant": "A", "source_pose": {"x_cm": 1, "y_cm": 2, "rotation_deg": 3}, "target_pose": {"x_cm": 4, "y_cm": 5, "rotation_deg": 6}, "participant_start_positions": [{"id": "P1", "x_cm": 10, "y_cm": 20, "radius_cm": 0}]}]}))

    def test_task_and_variant_integer_mappings_are_stable(self) -> None:
        self.assertEqual([int(task) for task in StudyTask], [1, 2, 3, 4])
        self.assertEqual((int(StudyVariant.A), int(StudyVariant.B)), (0, 1))

    def test_confirmed_layouts_include_every_t1_to_t4_variant(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        self.assertEqual(set(trials), {
            (StudyTask.T1, StudyVariant.A), (StudyTask.T1, StudyVariant.B),
            (StudyTask.T2, StudyVariant.A), (StudyTask.T2, StudyVariant.B),
            (StudyTask.T3, StudyVariant.A), (StudyTask.T3, StudyVariant.B),
            (StudyTask.T4, StudyVariant.A), (StudyTask.T4, StudyVariant.B),
        })
        self.assertEqual((trials[(StudyTask.T3, StudyVariant.B)].target_x_cm, trials[(StudyTask.T3, StudyVariant.B)].target_rotation_deg), (384.0, 130.0))
        t4a = trials[(StudyTask.T4, StudyVariant.A)]
        t4b = trials[(StudyTask.T4, StudyVariant.B)]
        self.assertEqual((t4a.target_x_cm, t4a.target_y_cm, t4a.target_rotation_deg), (380.0, 375.0, 65.0))
        self.assertEqual((t4b.source_pose.x_cm, t4b.source_pose.rotation_deg), (380.0, 65.0))
        self.assertEqual((len(t4a.distractor_tables), len(t4b.distractor_tables)), (3, 3))

    def test_every_finalized_trial_has_the_same_neutral_participant_markers(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        expected = (("P1", 200.0, 440.0, 40.0), ("P2", 300.0, 440.0, 40.0))
        for trial in trials.values():
            self.assertEqual(
                tuple(
                    (marker.participant_id, marker.x_cm, marker.y_cm, marker.radius_cm)
                    for marker in trial.participant_start_positions
                ),
                expected,
            )

    def test_participant_markers_are_roi_safe_and_record_the_known_t4_conflicts(self) -> None:
        """Validate marker disks with the canonical polygon/SAT geometry helpers."""

        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        collisions: set[tuple[str, str, str]] = set()
        for (task, variant), trial in trials.items():
            tables = (("source", trial.source_pose),) + tuple(
                (f"distractor_{index}", pose)
                for index, pose in enumerate(trial.distractor_tables, start=1)
            )
            for marker in trial.participant_start_positions:
                marker_disk = tuple(
                    (
                        marker.x_cm + marker.radius_cm * math.cos(2.0 * math.pi * index / 96),
                        marker.y_cm + marker.radius_cm * math.sin(2.0 * math.pi * index / 96),
                    )
                    for index in range(96)
                )
                self.assertTrue(polygon_inside_roi(marker_disk), f"{task.name}{variant.name}/{marker.participant_id}")
                for table_name, pose in tables:
                    if convex_polygons_intersect(
                        marker_disk,
                        world_footprint("rect", pose.x_cm, pose.y_cm, pose.rotation_deg),
                    ):
                        collisions.add((task.name + variant.name, marker.participant_id, table_name))
        self.assertEqual(
            collisions,
            {("T4A", "P1", "distractor_2"), ("T4B", "P2", "distractor_2")},
        )
