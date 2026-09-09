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
        self.messages: list[tuple[str, int]] = []

    def send_message(self, address: str, value: int) -> None:
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
        ))

    def test_each_change_publishes_the_complete_state(self) -> None:
        self.controller.set_mode(StudyMode.STUDY)
        self.assertEqual(self.client.messages, [
            ("/study/mode", 1),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/target_overlap", 0),
        ])

        self.client.messages.clear()
        self.controller.set_condition(StudyCondition.DUAL_SURFACE)
        self.controller.set_phase(StudyPhase.ACTIVE)
        self.controller.set_target_overlap(True)
        self.assertEqual(len(self.client.messages), 12)
        self.assertEqual(self.client.messages[-4:], [
            ("/study/mode", 1),
            ("/study/condition", 1),
            ("/study/phase", 2),
            ("/study/target_overlap", 1),
        ])

    def test_aisi_mode_publishes_value_two_without_changing_addresses(self) -> None:
        self.controller.set_mode(StudyMode.AISI)
        self.assertEqual(self.client.messages, [
            ("/study/mode", 2),
            ("/study/condition", 0),
            ("/study/phase", 0),
            ("/study/target_overlap", 0),
        ])

    def test_unchanged_value_does_not_republish(self) -> None:
        self.assertFalse(self.controller.set_mode(StudyMode.TRACKING))
        self.assertEqual(self.client.messages, [])

    def test_explicit_publish_resends_complete_state(self) -> None:
        self.controller.publish_current()
        self.assertEqual(len(self.client.messages), 4)


if __name__ == "__main__":
    unittest.main()
