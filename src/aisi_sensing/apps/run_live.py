from __future__ import annotations

"""Live app pipeline (skeleton).

Camera → sensing → tracking → features → inference → overlays → show window.
"""

import argparse
from ..core.logging import get_logger
from ..core.config import load_yaml
from ..core.types import FrameEvent
from ..core.timebase import now_iso


def main() -> None:
    logger = get_logger(__name__)
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", default="configs/camera.example.yaml")
    parser.add_argument("--lab", default="configs/lab.example.yaml")
    parser.add_argument("--classes", default="configs/classes.example.yaml")
    args = parser.parse_args()

    cam_cfg = load_yaml(args.camera)
    lab_cfg = load_yaml(args.lab)
    cls_cfg = load_yaml(args.classes)
    logger.info("Starting live pipeline (skeleton)")
    logger.info("Camera config: %s", cam_cfg)
    logger.info("Lab config: %s", lab_cfg)
    logger.info("Classes config: %s", cls_cfg)
    logger.info("Not implemented end-to-end yet. Use run_replay instead.")


if __name__ == "__main__":
    main()
