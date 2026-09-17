from pathlib import Path
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class CurrentRoomCaptureModeLauncherTests(unittest.TestCase):
    def test_rect_vision_defaults_to_latest_and_forwards_explicit_mode(self) -> None:
        source = (REPOSITORY_ROOT / "scripts" / "run_current_room_rect_vision.ps1").read_text(encoding="utf-8")
        self.assertIn('[string]$CameraCaptureMode = "latest"', source)
        self.assertIn('"--camera-capture-mode", $CameraCaptureMode', source)

    def test_tracking_launcher_forwards_mode_and_keeps_perflog_combinable(self) -> None:
        source = (REPOSITORY_ROOT / "scripts" / "run_current_room_tracking_only.ps1").read_text(encoding="utf-8")
        self.assertIn('[string]$CameraCaptureMode = "latest"', source)
        self.assertIn(' -CameraCaptureMode $CameraCaptureMode', source)
        self.assertIn(' -PerfLog', source)
