from __future__ import annotations

import unittest

from aisi.app.study_control import (
    StudyCondition,
    StudyMode,
    StudyPhase,
    StudyState,
    StudyStateController,
    StudyStatePublisher,
)


class _RecordingOscClient:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int | float]] = []

    def send_message(self, address: str, value: int | float) -> None:
        self.messages.append((address, value))


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
            ("/study/target_overlap", 0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
        ))

    def test_each_change_publishes_the_complete_state(self) -> None:
        self.controller.set_mode(StudyMode.STUDY)
        self.assertEqual(self.client.messages, [
            ("/study/mode", 1),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/target_overlap", 0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
        ])

        self.client.messages.clear()
        self.controller.set_condition(StudyCondition.DUAL_SURFACE)
        self.controller.set_phase(StudyPhase.ACTIVE)
        self.controller.set_target_overlap(True)
        self.assertEqual(len(self.client.messages), 21)
        self.assertEqual(self.client.messages[-7:], [
            ("/study/mode", 1),
            ("/study/condition", 1),
            ("/study/phase", 2),
            ("/study/target_overlap", 1),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
        ])

    def test_aisi_mode_publishes_value_two_without_changing_addresses(self) -> None:
        self.controller.set_mode(StudyMode.AISI)
        self.assertEqual(self.client.messages, [
            ("/study/mode", 2),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/target_overlap", 0),
            ("/study/target_x", 250.0),
            ("/study/target_y", 250.0),
            ("/study/target_rot", 0.0),
        ])

    def test_unchanged_value_does_not_republish(self) -> None:
        self.assertFalse(self.controller.set_mode(StudyMode.TRACKING))
        self.assertEqual(self.client.messages, [])

    def test_explicit_publish_resends_complete_state(self) -> None:
        self.controller.publish_current()
        self.assertEqual(len(self.client.messages), 7)

    def test_setting_fixed_target_pose_republishes_target_channels(self) -> None:
        self.assertTrue(self.controller.set_target_pose(310.5, 220.25, 45.0))
        self.assertEqual(self.controller.state.target_x, 310.5)
        self.assertEqual(self.controller.state.target_y, 220.25)
        self.assertEqual(self.controller.state.target_rot, 45.0)
        self.assertEqual(self.client.messages[-3:], [
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


if __name__ == "__main__":
    unittest.main()
