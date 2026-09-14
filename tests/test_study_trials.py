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
        self.assertEqual(
            (trials[(StudyTask.T4, StudyVariant.A)].target_x_cm,
             trials[(StudyTask.T4, StudyVariant.A)].target_y_cm,
             trials[(StudyTask.T4, StudyVariant.A)].target_rotation_deg),
            (207.5, 264.5, 75.0),
        )

    def test_finalized_trials_have_required_setup_table_counts_and_one_active_source(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        for task in (StudyTask.T1, StudyTask.T2):
            for variant in StudyVariant:
                trial = trials[(task, variant)]
                self.assertIsNotNone(trial.source_pose)
                self.assertEqual(len(trial.distractor_tables), 0)
        for task in (StudyTask.T3, StudyTask.T4):
            for variant in StudyVariant:
                trial = trials[(task, variant)]
                self.assertIsNotNone(trial.source_pose)
                self.assertEqual(len(trial.distractor_tables), 3)

    def test_t1_targets_are_t2_sources(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        for variant in StudyVariant:
            t1 = trials[(StudyTask.T1, variant)]
            t2 = trials[(StudyTask.T2, variant)]
            self.assertEqual(
                (t1.target_x_cm, t1.target_y_cm, t1.target_rotation_deg),
                (t2.source_pose.x_cm, t2.source_pose.y_cm, t2.source_pose.rotation_deg),
            )

    def test_t3_target_state_equals_t4_start_state_and_preserves_table_identity_order(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        for variant in StudyVariant:
            t3 = trials[(StudyTask.T3, variant)]
            t4 = trials[(StudyTask.T4, variant)]
            pose = lambda item: (item.x_cm, item.y_cm, item.rotation_deg)
            target_pose = lambda trial: (
                trial.target_x_cm, trial.target_y_cm, trial.target_rotation_deg
            )
            self.assertEqual(
                {target_pose(t3), *(pose(item) for item in t3.distractor_tables)},
                {pose(item) for item in (t4.source_pose, *t4.distractor_tables)},
            )
            # M0 -> M1 -> M2 physical-table mapping in the fixed positional
            # schema: T3 active becomes T4 distractor 3; T3 distractor 2
            # becomes T4 active; the remaining static tables keep order.
            self.assertEqual(target_pose(t3), pose(t4.distractor_tables[2]))
            self.assertEqual(pose(t3.distractor_tables[0]), pose(t4.distractor_tables[0]))
            self.assertEqual(pose(t3.distractor_tables[1]), pose(t4.source_pose))
            self.assertEqual(pose(t3.distractor_tables[2]), pose(t4.distractor_tables[1]))

    def test_participant_starts_and_variant_coordinates_are_mirrored(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        def mirrored_rotation(a: float, b: float) -> bool:
            return abs(((a + b + 90.0) % 180.0) - 90.0) < 1e-6

        for task in StudyTask:
            a = trials[(task, StudyVariant.A)]
            b = trials[(task, StudyVariant.B)]
            self.assertEqual(
                tuple((marker.participant_id, marker.x_cm, marker.y_cm, marker.radius_cm)
                      for marker in a.participant_start_positions),
                (("P1", 234.5, 53.5, 40.0),),
            )
            self.assertEqual(
                tuple((marker.participant_id, marker.x_cm, marker.y_cm, marker.radius_cm)
                      for marker in b.participant_start_positions),
                (("P1", 265.5, 53.5, 40.0),),
            )
            pose = lambda item: (item.x_cm, item.y_cm, item.rotation_deg)
            target_pose = lambda trial: (
                trial.target_x_cm, trial.target_y_cm, trial.target_rotation_deg
            )
            a_poses = (pose(a.source_pose), target_pose(a), *(pose(item) for item in a.distractor_tables))
            b_poses = (pose(b.source_pose), target_pose(b), *(pose(item) for item in b.distractor_tables))
            self.assertEqual(len(a_poses), len(b_poses))
            for a_pose, b_pose in zip(a_poses, b_poses):
                self.assertAlmostEqual(b_pose[0], 500.0 - a_pose[0])
                self.assertEqual(b_pose[1], a_pose[1])
                self.assertTrue(mirrored_rotation(a_pose[2], b_pose[2]))

    def test_participant_markers_are_roi_safe_and_do_not_overlap_home_tables(self) -> None:
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
        self.assertEqual(collisions, set())
