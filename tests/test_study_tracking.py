from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from aisi.app.study_control import StudyMode, StudyState, StudyStateController, StudyStatePublisher
from aisi.app.study_tracking import (
    StudyActiveTrackBindingStore,
    StudyActiveTrackSelector,
    TrackedTablePose,
    select_active_study_track,
)
from aisi.app.study_trials import PoseSpec, StudyTask, StudyVariant, TrialSpec


class _RecordingClient:
    def send_message(self, _address, _value) -> None:
        pass


class _RecordingLogger:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def log(self, event: dict) -> None:
        self.events.append(event)


def _track(track_id: str, x: float, y: float, rotation: float) -> dict:
    return {
        "id": track_id,
        "type": "rect",
        "x_cm": x,
        "y_cm": y,
        "rotation_deg": rotation,
    }


class StudyTrackingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self._temporary_directory.name)
        self.scene_path = root / "vision_live_scene.json"
        self.binding_store = StudyActiveTrackBindingStore(root / "study_active_track.json")
        self.selector = StudyActiveTrackSelector(self.scene_path, self.binding_store)

    def tearDown(self) -> None:
        self._temporary_directory.cleanup()

    def _write_scene(self, tables: list[dict]) -> None:
        self.scene_path.write_text(json.dumps({"tables": tables}), encoding="utf-8")

    def test_t1_t2_single_table_sources_resolve(self) -> None:
        for source in (PoseSpec(371.0, 220.0, 90.0), PoseSpec(100.5, 220.0, 90.0)):
            self._write_scene([_track("table_00", source.x_cm, source.y_cm, source.rotation_deg)])
            match = self.selector.resolve(source)
            self.assertIsNotNone(match)
            self.assertEqual(match.track.track_id, "table_00")

    def test_t3_and_t4_sources_select_the_correct_track_from_four_tables(self) -> None:
        self._write_scene([
            _track("table_00", 113.0, 432.5, -5.0),
            _track("table_01", 92.5, 273.0, -95.0),
            _track("table_02", 386.0, 132.0, 80.0),
            _track("table_03", 397.0, 411.0, -25.0),
        ])
        self.assertEqual(self.selector.resolve(PoseSpec(113.0, 432.5, -5.0)).track.track_id, "table_00")
        self.assertEqual(self.selector.resolve(PoseSpec(386.0, 132.0, 80.0)).track.track_id, "table_02")

    def test_wrong_nearby_distractor_with_incompatible_rect_yaw_is_not_selected(self) -> None:
        match = select_active_study_track(
            [
                TrackedTablePose("wrong", 5.0, 0.0, 70.0),
                TrackedTablePose("active", 30.0, 0.0, 0.0),
            ],
            PoseSpec(0.0, 0.0, 0.0),
        )
        self.assertIsNotNone(match)
        self.assertEqual(match.track.track_id, "active")

    def test_binding_remains_latched_during_active_even_when_another_track_becomes_closer(self) -> None:
        self._write_scene([_track("table_00", 113.0, 432.5, -5.0), _track("table_01", 200.0, 200.0, 0.0)])
        controller = StudyStateController(
            StudyStatePublisher(_RecordingClient()),
            StudyState(mode=StudyMode.STUDY),
            active_track_selector=self.selector,
        )
        trial = TrialSpec(StudyTask.T3, StudyVariant.A, 282.5, 181.0, 65.0, source_pose=PoseSpec(113.0, 432.5, -5.0))
        controller.apply_trial(trial)
        self.assertEqual(controller.state.active_track_id, "table_00")
        self.assertTrue(controller.start_trial())

        self._write_scene([_track("table_00", 250.0, 250.0, 20.0), _track("table_01", 113.0, 432.5, -5.0)])
        self.assertEqual(self.selector()["id"], "table_00")
        self.assertEqual(controller.state.active_track_id, "table_00")
        self.assertFalse(controller.resolve_active_track())
        self.assertEqual(controller.state.active_track_id, "table_00")

    def test_home_retries_an_unresolved_trial_after_tables_reach_their_setup_pose(self) -> None:
        source = PoseSpec(113.0, 432.5, -5.0)
        self._write_scene([_track("table_00", 10.0, 10.0, 0.0)])
        controller = StudyStateController(
            StudyStatePublisher(_RecordingClient()), StudyState(mode=StudyMode.STUDY),
            active_track_selector=self.selector,
        )
        controller.apply_trial(TrialSpec(StudyTask.T3, StudyVariant.A, 282.5, 181.0, 65.0, source_pose=source))
        self.assertIsNone(controller.state.active_track_id)

        self._write_scene([_track("table_03", 113.0, 432.5, -5.0)])
        self.assertTrue(controller.home())
        self.assertEqual(controller.state.active_track_id, "table_03")
        self.assertEqual(self.binding_store.read(), (True, "table_03"))

    def test_home_replaces_a_lost_pre_active_track_id_only_after_it_vanishes(self) -> None:
        source = PoseSpec(113.0, 432.5, -5.0)
        self._write_scene([_track("table_02", 113.0, 432.5, -5.0)])
        controller = StudyStateController(
            StudyStatePublisher(_RecordingClient()), StudyState(mode=StudyMode.STUDY),
            active_track_selector=self.selector,
        )
        controller.apply_trial(TrialSpec(StudyTask.T3, StudyVariant.A, 282.5, 181.0, 65.0, source_pose=source))
        self.assertEqual(controller.state.active_track_id, "table_02")

        # The vision tracker recreated the physical table under a new ID while
        # the trial was still in HOME. Re-resolve only in HOME, never ACTIVE.
        self._write_scene([_track("table_01", 113.0, 432.5, -5.0)])
        self.assertTrue(controller.home())
        self.assertEqual(controller.state.active_track_id, "table_01")
        self.assertEqual(self.binding_store.read(), (True, "table_01"))

    def test_start_performs_one_final_resolution_attempt(self) -> None:
        source = PoseSpec(371.0, 220.0, 90.0)
        self._write_scene([_track("table_00", 0.0, 0.0, 0.0)])
        controller = StudyStateController(
            StudyStatePublisher(_RecordingClient()), StudyState(mode=StudyMode.STUDY),
            active_track_selector=self.selector,
        )
        controller.apply_trial(TrialSpec(StudyTask.T1, StudyVariant.A, 100.5, 220.0, 90.0, source_pose=source))
        self.assertIsNone(controller.state.active_track_id)

        self._write_scene([_track("table_07", 371.0, 220.0, -90.0)])
        self.assertTrue(controller.start_trial())
        self.assertEqual(controller.state.active_track_id, "table_07")

    def test_next_trial_rebinds_to_a_different_track(self) -> None:
        self._write_scene([_track("table_00", 113.0, 432.5, -5.0), _track("table_02", 386.0, 132.0, 80.0)])
        controller = StudyStateController(StudyStatePublisher(_RecordingClient()), StudyState(mode=StudyMode.STUDY), active_track_selector=self.selector)
        controller.apply_trial(TrialSpec(StudyTask.T3, StudyVariant.A, 282.5, 181.0, 65.0, source_pose=PoseSpec(113.0, 432.5, -5.0)))
        self.assertEqual(controller.state.active_track_id, "table_00")
        controller.apply_trial(TrialSpec(StudyTask.T4, StudyVariant.A, 207.5, 264.5, 75.0, source_pose=PoseSpec(386.0, 132.0, 80.0)))
        self.assertEqual(controller.state.active_track_id, "table_02")
        self.assertEqual(self.binding_store.read(), (True, "table_02"))

    def test_loading_a_new_trial_clears_an_old_binding_when_its_source_is_unresolved(self) -> None:
        self._write_scene([_track("table_00", 113.0, 432.5, -5.0)])
        controller = StudyStateController(StudyStatePublisher(_RecordingClient()), StudyState(mode=StudyMode.STUDY), active_track_selector=self.selector)
        controller.apply_trial(TrialSpec(StudyTask.T3, StudyVariant.A, 282.5, 181.0, 65.0, source_pose=PoseSpec(113.0, 432.5, -5.0)))
        self.assertEqual(controller.state.active_track_id, "table_00")
        controller.apply_trial(TrialSpec(StudyTask.T4, StudyVariant.A, 207.5, 264.5, 75.0, source_pose=PoseSpec(386.0, 132.0, 80.0)))
        self.assertIsNone(controller.state.active_track_id)
        self.assertEqual(self.binding_store.read(), (True, None))

    def test_rect_equivalent_rotation_matches_and_unresolved_source_never_binds(self) -> None:
        self._write_scene([_track("table_00", 100.0, 200.0, 95.0)])
        self.assertEqual(self.selector.resolve(PoseSpec(100.0, 200.0, -85.0)).track.track_id, "table_00")
        self.assertIsNone(self.selector.resolve(PoseSpec(300.0, 300.0, 0.0)))
        self.assertEqual(self.binding_store.read(), (True, None))

    def test_disabling_study_binding_restores_the_ordinary_tracking_fallback(self) -> None:
        self.selector.resolve(PoseSpec(300.0, 300.0, 0.0))
        self.assertEqual(self.binding_store.read(), (True, None))
        self.selector.disable()
        self.assertEqual(self.binding_store.read(), (False, None))

    def test_unresolved_trial_is_logged_and_cannot_start_active(self) -> None:
        self._write_scene([_track("table_00", 10.0, 10.0, 0.0)])
        logger = _RecordingLogger()
        controller = StudyStateController(
            StudyStatePublisher(_RecordingClient()), StudyState(mode=StudyMode.STUDY),
            event_logger=logger, active_track_selector=self.selector,
        )
        controller.apply_trial(
            TrialSpec(StudyTask.T3, StudyVariant.A, 282.5, 181.0, 65.0, source_pose=PoseSpec(386.0, 132.0, 80.0))
        )
        self.assertIsNone(controller.state.active_track_id)
        self.assertEqual(logger.events[-1]["active_track_status"], "unresolved")
        self.assertFalse(controller.start_trial())


if __name__ == "__main__":
    unittest.main()
