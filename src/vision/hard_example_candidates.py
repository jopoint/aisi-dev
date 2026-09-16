"""Deterministically select diverse representatives from hard-example bursts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
import re
import shutil
from typing import Iterable

import cv2
import numpy as np


DEFAULT_BURST_GAP_SECONDS = 1.0
THUMBNAIL_SIZE = (64, 36)
_HARD_EXAMPLE_NAME = re.compile(
    r"^hard_example_(?P<timestamp>\d{8}_\d{6}_\d{3})_f(?P<frame>\d+)_(?P<sequence>\d+)\.png$"
)


@dataclass(frozen=True)
class HardExampleFrame:
    path: Path
    timestamp: datetime
    frame_id: int
    sequence: int


@dataclass(frozen=True)
class CandidateDecision:
    frame: HardExampleFrame
    burst_id: str
    selected: bool
    similarity_to_previous: float | None
    selection_score: float | None
    reason: str


def parse_hard_example_filename(path: Path) -> HardExampleFrame | None:
    """Parse one capture filename, returning ``None`` for unrelated images."""

    match = _HARD_EXAMPLE_NAME.match(path.name)
    if match is None:
        return None
    return HardExampleFrame(
        path=path,
        timestamp=datetime.strptime(match.group("timestamp"), "%Y%m%d_%H%M%S_%f"),
        frame_id=int(match.group("frame")),
        sequence=int(match.group("sequence")),
    )


def discover_hard_examples(input_dir: Path) -> list[HardExampleFrame]:
    """Return deterministically ordered hard-example PNGs under one directory."""

    frames = [
        parsed
        for path in input_dir.glob("*.png")
        if (parsed := parse_hard_example_filename(path)) is not None
    ]
    return sorted(frames, key=lambda frame: (frame.timestamp, frame.sequence, frame.path.name))


def group_capture_bursts(
    frames: Iterable[HardExampleFrame],
    *,
    gap_seconds: float = DEFAULT_BURST_GAP_SECONDS,
) -> list[list[HardExampleFrame]]:
    """Group timestamp-contiguous capture files into user-triggered bursts."""

    if gap_seconds <= 0.0:
        raise ValueError("gap_seconds must be positive")
    groups: list[list[HardExampleFrame]] = []
    for frame in sorted(frames, key=lambda item: (item.timestamp, item.sequence, item.path.name)):
        if not groups:
            groups.append([frame])
            continue
        previous = groups[-1][-1]
        if (frame.timestamp - previous.timestamp).total_seconds() > gap_seconds:
            groups.append([frame])
        else:
            groups[-1].append(frame)
    return groups


def burst_id(frames: list[HardExampleFrame]) -> str:
    """Return a stable, human-readable identifier based on the first capture."""

    if not frames:
        raise ValueError("a burst must contain at least one frame")
    return frames[0].timestamp.strftime("%Y%m%d_%H%M%S_%f")[:-3]


def image_feature(path: Path) -> np.ndarray | None:
    """Return a compact luminance thumbnail in [0, 1], without model inference."""

    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        return None
    return cv2.resize(image, THUMBNAIL_SIZE, interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0


def image_similarity(left: np.ndarray, right: np.ndarray) -> float:
    """Return deterministic luminance similarity: one minus mean absolute error."""

    if left.shape != right.shape:
        raise ValueError("image features must have matching shapes")
    return float(np.clip(1.0 - np.mean(np.abs(left - right)), 0.0, 1.0))


def select_diverse_indices(features: list[np.ndarray], representatives: int) -> tuple[set[int], dict[int, float]]:
    """Keep the first frame plus maximin-different frames, deterministically."""

    if representatives < 1:
        raise ValueError("representatives must be at least one")
    if not features:
        return set(), {}
    selected = {0}
    scores = {0: None}
    while len(selected) < min(representatives, len(features)):
        choices = []
        for index, feature in enumerate(features):
            if index in selected:
                continue
            novelty = min(1.0 - image_similarity(feature, features[chosen]) for chosen in selected)
            choices.append((novelty, -index, index))
        novelty, _earlier_index, chosen = max(choices)
        selected.add(chosen)
        scores[chosen] = novelty
    return selected, scores


def decisions_for_burst(
    frames: list[HardExampleFrame],
    *,
    representatives: int,
) -> list[CandidateDecision]:
    """Score one burst and select visually distinct readable frames."""

    identifier = burst_id(frames)
    features = [image_feature(frame.path) for frame in frames]
    readable_indices = [index for index, feature in enumerate(features) if feature is not None]
    readable_features = [features[index] for index in readable_indices]
    selected_readable, novelty_scores = select_diverse_indices(readable_features, representatives)
    selected_indices = {readable_indices[index] for index in selected_readable}
    readable_position = {source_index: index for index, source_index in enumerate(readable_indices)}

    decisions: list[CandidateDecision] = []
    for index, frame in enumerate(frames):
        feature = features[index]
        if feature is None:
            decisions.append(CandidateDecision(frame, identifier, False, None, None, "unreadable_image"))
            continue
        previous_feature = next((features[previous] for previous in range(index - 1, -1, -1) if features[previous] is not None), None)
        similarity = None if previous_feature is None else image_similarity(previous_feature, feature)
        if index not in selected_indices:
            decisions.append(CandidateDecision(frame, identifier, False, similarity, None, "not_selected"))
            continue
        position = readable_position[index]
        if position == 0:
            reason, score = "burst_first", None
        else:
            score = novelty_scores[position]
            reason = "maximin_visual_difference"
        decisions.append(CandidateDecision(frame, identifier, True, similarity, score, reason))
    return decisions


def write_candidate_subset(
    input_dir: Path,
    output_dir: Path,
    *,
    representatives: int = 3,
    burst_gap_seconds: float = DEFAULT_BURST_GAP_SECONDS,
) -> tuple[list[CandidateDecision], Path]:
    """Copy selected frames and write a full CSV manifest; source files stay intact."""

    if representatives < 1:
        raise ValueError("representatives must be at least one")
    if not input_dir.is_dir():
        raise ValueError(f"input directory does not exist: {input_dir}")
    frames = discover_hard_examples(input_dir)
    decisions = [
        decision
        for group in group_capture_bursts(frames, gap_seconds=burst_gap_seconds)
        for decision in decisions_for_burst(group, representatives=representatives)
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    for decision in decisions:
        if decision.selected:
            shutil.copy2(decision.frame.path, output_dir / decision.frame.path.name)
    manifest = output_dir / "manifest.csv"
    with manifest.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "source_filename", "burst_id", "selected", "similarity_to_previous",
                "selection_score", "reason",
            ),
        )
        writer.writeheader()
        for decision in decisions:
            writer.writerow({
                "source_filename": decision.frame.path.name,
                "burst_id": decision.burst_id,
                "selected": "yes" if decision.selected else "no",
                "similarity_to_previous": "" if decision.similarity_to_previous is None else f"{decision.similarity_to_previous:.6f}",
                "selection_score": "" if decision.selection_score is None else f"{decision.selection_score:.6f}",
                "reason": decision.reason,
            })
    return decisions, manifest
