from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

from aisi.app.study_trials import StudyTask, StudyVariant, load_trial_definitions, trial_definition_metadata
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
            (234.84473024735843, 404.1752983481141, -91.7400727688127),
        )

    def test_pilot_v1_through_v6_snapshots_preserve_their_respective_frozen_layouts(self) -> None:
        study_directory = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study"
        active_path = study_directory / "trials.json"
        prior_snapshot_path = study_directory / "trials_pilot_v1.json"
        snapshot_path = study_directory / "trials_pilot_v2.json"
        current_snapshot_path = study_directory / "trials_pilot_v3.json"
        final_snapshot_path = study_directory / "trials_pilot_v4.json"
        prior_final_snapshot_path = study_directory / "trials_pilot_v5.json"
        newest_snapshot_path = study_directory / "trials_pilot_v6.json"
        self.assertTrue(prior_snapshot_path.is_file())
        self.assertTrue(snapshot_path.is_file())
        self.assertTrue(current_snapshot_path.is_file())
        self.assertTrue(final_snapshot_path.is_file())
        self.assertTrue(prior_final_snapshot_path.is_file())
        self.assertTrue(newest_snapshot_path.is_file())
        active_payload = json.loads(active_path.read_text(encoding="utf-8"))
        prior_snapshot_payload = json.loads(prior_snapshot_path.read_text(encoding="utf-8"))
        snapshot_payload = json.loads(snapshot_path.read_text(encoding="utf-8"))
        current_snapshot_payload = json.loads(current_snapshot_path.read_text(encoding="utf-8"))
        final_snapshot_payload = json.loads(final_snapshot_path.read_text(encoding="utf-8"))
        prior_final_snapshot_payload = json.loads(prior_final_snapshot_path.read_text(encoding="utf-8"))
        newest_snapshot_payload = json.loads(newest_snapshot_path.read_text(encoding="utf-8"))
        expected_active_metadata = {
            "version": "pilot_v6",
            "status": "frozen_for_study",
            "description": "Frozen final T1-T4 geometry with task-specific A/B counterbalancing",
        }
        self.assertEqual({key: active_payload.get(key) for key in expected_active_metadata}, expected_active_metadata)
        self.assertEqual({key: newest_snapshot_payload.get(key) for key in expected_active_metadata}, expected_active_metadata)
        self.assertEqual(prior_final_snapshot_payload["version"], "pilot_v5")
        self.assertEqual(final_snapshot_payload["version"], "pilot_v4")
        self.assertEqual(current_snapshot_payload["version"], "pilot_v3")
        self.assertEqual(snapshot_payload["version"], "pilot_v2")
        self.assertEqual(load_trial_definitions(active_path), load_trial_definitions(newest_snapshot_path))
        self.assertNotEqual(load_trial_definitions(active_path), load_trial_definitions(prior_final_snapshot_path))
        self.assertNotEqual(load_trial_definitions(active_path), load_trial_definitions(current_snapshot_path))
        self.assertNotEqual(load_trial_definitions(active_path), load_trial_definitions(snapshot_path))
        self.assertNotEqual(load_trial_definitions(active_path), load_trial_definitions(prior_snapshot_path))
        self.assertEqual(len(trial_definition_metadata(active_path)["trial_definitions_sha256"]), 64)
        self.assertEqual(len(trial_definition_metadata(newest_snapshot_path)["trial_definitions_sha256"]), 64)

    def test_finalized_trials_have_required_setup_table_counts_and_one_active_source(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        for task in (StudyTask.T1, StudyTask.T2):
            for variant in StudyVariant:
                trial = trials[(task, variant)]
                self.assertIsNotNone(trial.source_pose)
                self.assertEqual(len(trial.distractor_tables), 0)
                self.assertEqual(len((trial.source_pose, *trial.distractor_tables)), 1)
        for task in (StudyTask.T3, StudyTask.T4):
            for variant in StudyVariant:
                trial = trials[(task, variant)]
                self.assertIsNotNone(trial.source_pose)
                self.assertEqual(len(trial.distractor_tables), 2)
                self.assertEqual(len((trial.source_pose, *trial.distractor_tables)), 3)

    def test_current_trials_include_exact_frozen_geometry(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        expected = {
            "T1A": ((73, 204, -100), (427, 283, 95), ()),
            "T1B": ((73, 296, -80), (427, 217, 85), ()),
            "T2A": ((167, 74.5, 10), (254.1, 436, 175), ()),
            "T2B": ((333, 74.5, -10), (245.9, 436, -175), ()),
            "T3A": ((87.44109878029548, 271.7760216418562, 101.15960012857052), (397.2182816800569, 237.33178597669993, -96.01579621441935), ((197.4417669961654, 194.69924154574431, 99.75089545617918), (295.01593705427456, 228.7988341653692, -91.69820657021306))),
            "T3B": ((87.44109878029548, 228.2239783581438, 78.84039987142948), (397.2182816800569, 262.66821402330007, -83.98420378558065), ((197.4417669961654, 305.3007584542557, 80.24910454382082), (295.01593705427456, 271.2011658346308, -88.30179342978694))),
            "T4A": ((265.37464310054287, 53.30026150452769, 179.1565691228634), (234.84473024735843, 404.1752983481141, -91.7400727688127), ((200.27976364082878, 154.83289474640358, 173.23873712478508), (330.79043090699105, 393.6398110955178, -101.87692619306351))),
            "T4B": ((234.62535689945713, 53.30026150452769, -179.1565691228634), (265.1552697526416, 404.1752983481141, 91.7400727688127), ((299.7202363591712, 154.83289474640358, -173.23873712478508), (169.20956909300895, 393.6398110955178, 101.87692619306351))),
        }
        for task in StudyTask:
            for variant in StudyVariant:
                trial = trials[(task, variant)]
                source, target, distractors = expected[task.name + variant.name]
                self.assertEqual((trial.source_pose.x_cm, trial.source_pose.y_cm, trial.source_pose.rotation_deg), source)
                self.assertEqual((trial.target_x_cm, trial.target_y_cm, trial.target_rotation_deg), target)
                self.assertEqual(tuple((pose.x_cm, pose.y_cm, pose.rotation_deg) for pose in trial.distractor_tables), distractors)

    def test_all_b_variants_follow_the_projector_axis_transform_and_are_involutions(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        def transform(task, pose):
            if task in (StudyTask.T1, StudyTask.T3):
                return (pose.x_cm, 500.0 - pose.y_cm, (180.0 - pose.rotation_deg + 180.0) % 360.0 - 180.0)
            return (500.0 - pose.x_cm, pose.y_cm, (-pose.rotation_deg + 180.0) % 360.0 - 180.0)
        def assert_pose(actual, expected):
            for actual_value, expected_value in zip(actual, expected):
                self.assertAlmostEqual(actual_value, expected_value, places=10)
        for task in StudyTask:
            a = trials[(task, StudyVariant.A)]
            b = trials[(task, StudyVariant.B)]
            assert_pose(
                (b.source_pose.x_cm, b.source_pose.y_cm, b.source_pose.rotation_deg),
                transform(task, a.source_pose),
            )
            assert_pose(
                (b.target_x_cm, b.target_y_cm, b.target_rotation_deg),
                transform(task, type("Pose", (), {"x_cm": a.target_x_cm, "y_cm": a.target_y_cm, "rotation_deg": a.target_rotation_deg})()),
            )
            for actual, expected in zip(b.distractor_tables, a.distractor_tables):
                assert_pose((actual.x_cm, actual.y_cm, actual.rotation_deg), transform(task, expected))
            assert_pose(transform(task, type("Pose", (), {"x_cm": b.source_pose.x_cm, "y_cm": b.source_pose.y_cm, "rotation_deg": b.source_pose.rotation_deg})()), (a.source_pose.x_cm, a.source_pose.y_cm, a.source_pose.rotation_deg))
            for actual, expected in zip(b.participant_start_positions, a.participant_start_positions):
                expected_position = (
                    expected.x_cm if task in (StudyTask.T1, StudyTask.T3) else 500.0 - expected.x_cm,
                    500.0 - expected.y_cm if task in (StudyTask.T1, StudyTask.T3) else expected.y_cm,
                )
                self.assertEqual((actual.x_cm, actual.y_cm), expected_position)
            a_tables = (a.source_pose, *a.distractor_tables)
            b_tables = (b.source_pose, *b.distractor_tables)
            for left in range(len(a_tables)):
                for right in range(left + 1, len(a_tables)):
                    self.assertAlmostEqual(
                        math.hypot(a_tables[left].x_cm - a_tables[right].x_cm, a_tables[left].y_cm - a_tables[right].y_cm),
                        math.hypot(b_tables[left].x_cm - b_tables[right].x_cm, b_tables[left].y_cm - b_tables[right].y_cm),
                        places=10,
                    )

    def test_final_layouts_have_expected_participant_starts(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        trials = load_trial_definitions(path)
        expected_a = {
            StudyTask.T1: (250.0, 450.0), StudyTask.T2: (450.0, 250.0),
            StudyTask.T3: (250.0, 445.0), StudyTask.T4: (55.0, 250.0),
        }
        expected_b = {
            StudyTask.T1: (250.0, 50.0), StudyTask.T2: (50.0, 250.0),
            StudyTask.T3: (250.0, 55.0), StudyTask.T4: (445.0, 250.0),
        }
        for task in StudyTask:
            a = trials[(task, StudyVariant.A)]
            b = trials[(task, StudyVariant.B)]
            self.assertEqual(
                tuple((marker.participant_id, marker.x_cm, marker.y_cm, marker.radius_cm)
                      for marker in a.participant_start_positions),
                (("P1", *expected_a[task], 40.0),),
            )
            self.assertEqual(
                tuple((marker.participant_id, marker.x_cm, marker.y_cm, marker.radius_cm)
                      for marker in b.participant_start_positions),
                (("P1", *expected_b[task], 40.0),),
            )

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

    def test_all_trial_rect_footprints_are_roi_safe(self) -> None:
        path = Path(__file__).resolve().parents[1] / "data" / "aisi" / "study" / "trials.json"
        for (task, variant), trial in load_trial_definitions(path).items():
            poses = (trial.source_pose, *trial.distractor_tables, type(trial.source_pose)(
                trial.target_x_cm, trial.target_y_cm, trial.target_rotation_deg,
            ))
            for pose in poses:
                self.assertTrue(
                    polygon_inside_roi(world_footprint("rect", pose.x_cm, pose.y_cm, pose.rotation_deg)),
                    f"{task.name}{variant.name}: {pose}",
                )
