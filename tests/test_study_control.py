from __future__ import annotations

import unittest
import inspect

from aisi.app.study_control import (
    StudyCondition,
    StudyControlUi,
    StudyMode,
    StudyPhase,
    StudyState,
    StudyStateController,
    StudyStatePublisher,
    apply_selected_trial,
)
from aisi.app.study_trials import (
    ParticipantStartSpec,
    PoseSpec,
    StudyTask,
    StudyVariant,
    TrialSpec,
)


class _RecordingOscClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int | float]] = []

    def send_message(self, address: str, value: int | float) -> None:
        self.messages.append((address, value))


class _RecordingLogger:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def log(self, event: dict) -> None:
        self.events.append(event)


class StudyControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = _RecordingOscClient()
        self.controller = StudyStateController(StudyStatePublisher(self.client))

    def test_default_state_uses_specified_integer_values(self) -> None:
        self.assertEqual(self.controller.state, StudyState())
        self.assertEqual(self.controller.state.osc_messages(), (
            ("/study/mode", 0),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/task", 1),
            ("/study/variant", 0),
            ("/study/target_overlap", 0),
            ("/study/source_x", 250.0),
            ("/study/source_y", 250.0),
            ("/study/source_rot", 0.0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
            ("/study/setup_table_count", 0),
            ("/study/participant_start_count", 0),
        ))

    def test_each_change_publishes_the_complete_state(self) -> None:
        self.controller.set_mode(StudyMode.STUDY)
        self.assertEqual(self.client.messages, [
            ("/study/mode", 1),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/task", 1),
            ("/study/variant", 0),
            ("/study/target_overlap", 0),
            ("/study/source_x", 250.0),
            ("/study/source_y", 250.0),
            ("/study/source_rot", 0.0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
            ("/study/setup_table_count", 0),
            ("/study/participant_start_count", 0),
        ])

        self.client.messages.clear()
        self.controller.set_condition(StudyCondition.DUAL_SURFACE)
        self.controller.set_phase(StudyPhase.ACTIVE)
        self.controller.set_target_overlap(True)
        self.assertEqual(len(self.client.messages), 42)
        self.assertEqual(self.client.messages[-14:], [
            ("/study/mode", 1),
            ("/study/condition", 1),
            ("/study/phase", 2),
            ("/study/task", 1),
            ("/study/variant", 0),
            ("/study/target_overlap", 1),
            ("/study/source_x", 250.0),
            ("/study/source_y", 250.0),
            ("/study/source_rot", 0.0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
            ("/study/setup_table_count", 0),
            ("/study/participant_start_count", 0),
        ])

    def test_aisi_mode_publishes_value_two_without_changing_addresses(self) -> None:
        self.controller.set_mode(StudyMode.AISI)
        self.assertEqual(self.client.messages, [
            ("/study/mode", 2),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/task", 1),
            ("/study/variant", 0),
            ("/study/target_overlap", 0),
            ("/study/source_x", 250.0),
            ("/study/source_y", 250.0),
            ("/study/source_rot", 0.0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
            ("/study/setup_table_count", 0),
            ("/study/participant_start_count", 0),
        ])

    def test_unchanged_value_does_not_republish(self) -> None:
        self.assertFalse(self.controller.set_mode(StudyMode.TRACKING))
        self.assertEqual(self.client.messages, [])

    def test_explicit_publish_resends_complete_state(self) -> None:
        self.controller.publish_current()
        self.assertEqual(len(self.client.messages), 14)

    def test_setting_fixed_target_pose_republishes_target_channels(self) -> None:
        self.assertTrue(self.controller.set_target_pose(310.5, 220.25, 45.0))
        self.assertEqual(self.controller.state.target_x, 310.5)
        self.assertEqual(self.controller.state.target_y, 220.25)
        self.assertEqual(self.controller.state.target_rot, 45.0)
        self.assertEqual(self.client.messages[-5:-2], [
            ("/study/target_x", 310.5),
            ("/study/target_y", 220.25),
            ("/study/target_rot", 45.0),
        ])

    def test_source_changes_cannot_change_study_owned_target_pose(self) -> None:
        self.controller.set_target_pose(300.0, 200.0, 30.0)
        target_before = (
            self.controller.state.target_x,
            self.controller.state.target_y,
            self.controller.state.target_rot,
        )
        self.controller.set_mode(StudyMode.STUDY)

        self.assertEqual(
            (self.controller.state.target_x, self.controller.state.target_y, self.controller.state.target_rot),
            target_before,
        )

    def test_apply_trial_sets_task_variant_and_fixed_target(self) -> None:
        logger = _RecordingLogger()
        controller = StudyStateController(StudyStatePublisher(self.client), event_logger=logger)
        trial = TrialSpec(StudyTask.T3, StudyVariant.B, 340.0, 340.0, 45.0)
        self.assertTrue(controller.apply_trial(trial))
        self.assertEqual(controller.state.task, StudyTask.T3)
        self.assertEqual(controller.state.variant, StudyVariant.B)
        self.assertEqual((controller.state.target_x, controller.state.target_y, controller.state.target_rot), (340.0, 340.0, 45.0))
        self.assertEqual(logger.events[-1]["event_type"], "trial_loaded")

    def test_apply_trial_republishes_the_trial_owned_start_pose(self) -> None:
        trial = TrialSpec(
            StudyTask.T1, StudyVariant.A, 380.0, 150.0, 90.0,
            source_pose=PoseSpec(120.0, 150.0, 90.0),
        )
        self.controller.apply_trial(trial)
        self.assertEqual((self.controller.state.source_x, self.controller.state.source_y, self.controller.state.source_rot), (120.0, 150.0, 90.0))
        self.assertEqual(self.client.messages[-11:-8], [("/study/source_x", 120.0), ("/study/source_y", 150.0), ("/study/source_rot", 90.0)])

    def test_task_and_variant_selection_automatically_apply_the_selected_trial(self) -> None:
        first = TrialSpec(StudyTask.T1, StudyVariant.A, 380.0, 150.0, 90.0, source_pose=PoseSpec(120.0, 150.0, 90.0))
        second = TrialSpec(StudyTask.T2, StudyVariant.B, 350.0, 285.0, 0.0, source_pose=PoseSpec(130.0, 145.0, 90.0))
        trials = {(StudyTask.T1, StudyVariant.A): first, (StudyTask.T2, StudyVariant.B): second}
        self.assertIs(apply_selected_trial(self.controller, trials, StudyTask.T1, StudyVariant.A), first)
        self.assertIs(apply_selected_trial(self.controller, trials, StudyTask.T2, StudyVariant.B), second)
        self.assertEqual((self.controller.state.task, self.controller.state.variant), (StudyTask.T2, StudyVariant.B))
        self.assertEqual((self.controller.state.source_x, self.controller.state.source_y, self.controller.state.source_rot), (130.0, 145.0, 90.0))
        self.assertEqual((self.controller.state.target_x, self.controller.state.target_y, self.controller.state.target_rot), (350.0, 285.0, 0.0))
        self.assertEqual(self.client.messages[-11:-5], [("/study/source_x", 130.0), ("/study/source_y", 145.0), ("/study/source_rot", 90.0), ("/study/target_x", 350.0), ("/study/target_y", 285.0), ("/study/target_rot", 0.0)])

    def test_trial_publishes_a_neutral_setup_list_and_optional_markers(self) -> None:
        trial = TrialSpec(
            StudyTask.T3, StudyVariant.A, 116.0, 270.0, -130.0,
            source_pose=PoseSpec(260.0, 180.0, -20.0),
            distractor_tables=(PoseSpec(185.0, 105.0, 150.0),),
            participant_start_positions=(ParticipantStartSpec("P1", 190.0, 395.0),),
        )
        self.assertTrue(self.controller.apply_trial(trial))
        self.assertEqual(self.controller.state.setup_table_poses, (
            trial.source_pose, *trial.distractor_tables,
        ))
        self.assertEqual(self.controller.state.participant_start_positions, trial.participant_start_positions)
        self.assertEqual(self.client.messages[-8:], [
            ("/study/setup_table_count", 2),
            ("/study/participant_start_count", 1),
            ("/study/setup_table/0/x", 260.0),
            ("/study/setup_table/0/y", 180.0),
            ("/study/setup_table/0/rot", -20.0),
            ("/study/setup_table/1/x", 185.0),
            ("/study/setup_table/1/y", 105.0),
            ("/study/setup_table/1/rot", 150.0),
            ("/study/participant_start/0/x", 190.0),
            ("/study/participant_start/0/y", 395.0),
            ("/study/participant_start/0/radius", 40.0),
        ][-8:])

    def test_missing_selected_trial_preserves_the_last_valid_state(self) -> None:
        valid = TrialSpec(StudyTask.T1, StudyVariant.A, 380.0, 150.0, 90.0, source_pose=PoseSpec(120.0, 150.0, 90.0))
        apply_selected_trial(self.controller, {(StudyTask.T1, StudyVariant.A): valid}, StudyTask.T1, StudyVariant.A)
        previous = self.controller.state
        self.assertIsNone(apply_selected_trial(self.controller, {}, StudyTask.T4, StudyVariant.B))
        self.assertEqual(self.controller.state, previous)

    def test_reselecting_an_effective_trial_does_not_duplicate_trial_loaded_event(self) -> None:
        logger = _RecordingLogger()
        controller = StudyStateController(StudyStatePublisher(self.client), event_logger=logger)
        trial = TrialSpec(StudyTask.T1, StudyVariant.A, 380.0, 150.0, 90.0, source_pose=PoseSpec(120.0, 150.0, 90.0))
        trials = {(StudyTask.T1, StudyVariant.A): trial}
        apply_selected_trial(controller, trials, StudyTask.T1, StudyVariant.A)
        apply_selected_trial(controller, trials, StudyTask.T1, StudyVariant.A)
        self.assertEqual([event["event_type"] for event in logger.events], ["trial_loaded"])

    def test_normal_phase_sequence_uses_home_active_complete(self) -> None:
        self.assertFalse(self.controller.home())
        self.assertTrue(self.controller.start_trial())
        self.assertTrue(self.controller.complete_trial())
        self.assertEqual(self.controller.state.phase, StudyPhase.COMPLETE)

    def test_ready_remains_internal_but_is_not_an_exposed_ui_button(self) -> None:
        self.assertTrue(self.controller.ready())
        self.assertEqual(self.controller.state.phase, StudyPhase.READY)
        self.assertNotIn('("Ready",', inspect.getsource(StudyControlUi))

    def test_trial_transitions_record_timestamps_and_active_pose(self) -> None:
        logger = _RecordingLogger()
        controller = StudyStateController(StudyStatePublisher(self.client), event_logger=logger, source_pose_provider=lambda: {"id": "table_00", "x_cm": 12.0})
        self.assertTrue(controller.ready())
        self.assertTrue(controller.start_trial())
        self.assertIsNotNone(controller.trial_started_at_iso)
        self.assertTrue(controller.record_active_pose())
        self.assertTrue(controller.complete_trial())
        self.assertIsNotNone(controller.trial_completed_at_iso)
        self.assertEqual([event["event_type"] for event in logger.events], ["phase_ready", "trial_started", "active_pose_sample", "trial_completed"])
        self.assertEqual(logger.events[2]["source_pose"]["id"], "table_00")

    def test_unavailable_source_pose_does_not_break_active_logging(self) -> None:
        logger = _RecordingLogger()
        controller = StudyStateController(StudyStatePublisher(self.client), event_logger=logger, source_pose_provider=lambda: None)
        controller.start_trial()
        self.assertTrue(controller.record_active_pose())
        self.assertIsNone(logger.events[-1]["source_pose"])


if __name__ == "__main__":
    unittest.main()
