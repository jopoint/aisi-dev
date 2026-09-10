"""Validated, manually editable Trial definitions for the Study controller."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import json
import math
from pathlib import Path
from typing import Any


class StudyTask(IntEnum):
    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4


class StudyVariant(IntEnum):
    A = 0
    B = 1


@dataclass(frozen=True)
class PoseSpec:
    """A physical table pose in the shared 500 x 500 cm study world."""

    x_cm: float
    y_cm: float
    rotation_deg: float


@dataclass(frozen=True)
class HomePoseSpec:
    """A named home position; rotation is intentionally optional."""

    x_cm: float
    y_cm: float
    rotation_deg: float | None = None


@dataclass(frozen=True)
class ParticipantStartSpec:
    """An optional neutral participant floor marker for HOME/READY setup."""

    participant_id: str
    x_cm: float
    y_cm: float
    radius_cm: float = 40.0


@dataclass(frozen=True)
class TrialSpec:
    """One fixed target pose for a task/variant combination."""

    task: StudyTask
    variant: StudyVariant
    target_x_cm: float
    target_y_cm: float
    target_rotation_deg: float
    home_x_cm: float | None = None
    home_y_cm: float | None = None
    home_rotation_deg: float | None = None
    source_pose: PoseSpec | None = None
    home_pose_reference: str | None = None
    home_pose: HomePoseSpec | None = None
    distractor_tables: tuple[PoseSpec, ...] = ()
    participant_start_positions: tuple[ParticipantStartSpec, ...] = ()
    notes: str | None = None


def _finite_number(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be numeric")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field} must be numeric") from error
    if not math.isfinite(number):
        raise ValueError(f"{field} must be finite")
    return number


def _optional_number(record: dict[str, Any], field: str) -> float | None:
    value = record.get(field)
    return None if value is None else _finite_number(value, field)


def _pose(record: object, field: str) -> PoseSpec:
    if not isinstance(record, dict):
        raise ValueError(f"{field} must be an object")
    return PoseSpec(
        x_cm=_finite_number(record.get("x_cm"), f"{field}.x_cm"),
        y_cm=_finite_number(record.get("y_cm"), f"{field}.y_cm"),
        rotation_deg=_finite_number(record.get("rotation_deg"), f"{field}.rotation_deg"),
    )


def _home_poses(payload: dict[str, Any]) -> dict[str, HomePoseSpec]:
    records = payload.get("home_positions", {})
    if not isinstance(records, dict):
        raise ValueError("home_positions must be an object when present")
    homes: dict[str, HomePoseSpec] = {}
    for reference, record in records.items():
        if not isinstance(reference, str) or not reference or not isinstance(record, dict):
            raise ValueError("home_positions entries must have a name and object value")
        homes[reference] = HomePoseSpec(
            x_cm=_finite_number(record.get("x_cm"), f"home_positions.{reference}.x_cm"),
            y_cm=_finite_number(record.get("y_cm"), f"home_positions.{reference}.y_cm"),
            rotation_deg=_optional_number(record, "rotation_deg"),
        )
    return homes


def _participant_start_positions(record: dict[str, Any], field: str) -> tuple[ParticipantStartSpec, ...]:
    positions = record.get("participant_start_positions", [])
    if not isinstance(positions, list):
        raise ValueError(f"{field} must be a list when present")
    result: list[ParticipantStartSpec] = []
    identifiers: set[str] = set()
    for index, position in enumerate(positions):
        if not isinstance(position, dict):
            raise ValueError(f"{field}[{index}] must be an object")
        participant_id = position.get("id")
        if not isinstance(participant_id, str) or not participant_id or participant_id in identifiers:
            raise ValueError(f"{field}[{index}].id must be a unique non-empty string")
        identifiers.add(participant_id)
        radius_cm = _finite_number(position.get("radius_cm", 40.0), f"{field}[{index}].radius_cm")
        if radius_cm <= 0:
            raise ValueError(f"{field}[{index}].radius_cm must be positive")
        result.append(ParticipantStartSpec(
            participant_id=participant_id,
            x_cm=_finite_number(position.get("x_cm"), f"{field}[{index}].x_cm"),
            y_cm=_finite_number(position.get("y_cm"), f"{field}[{index}].y_cm"),
            radius_cm=radius_cm,
        ))
    return tuple(result)


def _task(value: object) -> StudyTask:
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized.startswith("T"):
            normalized = normalized[1:]
        value = normalized
    try:
        return StudyTask(int(value))
    except (TypeError, ValueError) as error:
        raise ValueError("task_id must be T1 through T4") from error


def _variant(value: object) -> StudyVariant:
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized in {"A", "B"}:
            return StudyVariant[normalized]
    try:
        return StudyVariant(int(value))
    except (TypeError, ValueError) as error:
        raise ValueError("variant must be A or B") from error


def load_trial_definitions(path: str | Path) -> dict[tuple[StudyTask, StudyVariant], TrialSpec]:
    """Load a schema-version-1 trial file and reject ambiguous definitions."""

    source = Path(path)
    try:
        with source.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Unable to load trial definitions {source}: {error}") from error
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Trial definitions must be an object with schema_version=1")
    records = payload.get("trials")
    if not isinstance(records, list) or not records:
        raise ValueError("Trial definitions must contain a non-empty trials list")

    homes = _home_poses(payload)
    result: dict[tuple[StudyTask, StudyVariant], TrialSpec] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"trials[{index}] must be an object")
        task = _task(record.get("task_id"))
        variant = _variant(record.get("variant"))
        key = (task, variant)
        if key in result:
            raise ValueError(f"Duplicate trial definition for {task.name}/{variant.name}")
        notes = record.get("notes")
        if notes is not None and not isinstance(notes, str):
            raise ValueError(f"trials[{index}].notes must be a string when present")
        home_reference = record.get("home_pose_reference")
        if home_reference is not None and (not isinstance(home_reference, str) or home_reference not in homes):
            raise ValueError(f"trials[{index}].home_pose_reference must name a configured home position")
        distractors = record.get("distractor_tables", [])
        if not isinstance(distractors, list):
            raise ValueError(f"trials[{index}].distractor_tables must be a list when present")
        target_pose = _pose(record.get("target_pose"), f"trials[{index}].target_pose")
        result[key] = TrialSpec(
            task=task,
            variant=variant,
            target_x_cm=target_pose.x_cm,
            target_y_cm=target_pose.y_cm,
            target_rotation_deg=target_pose.rotation_deg,
            source_pose=_pose(record.get("source_pose"), f"trials[{index}].source_pose"),
            home_pose_reference=home_reference,
            home_pose=homes.get(home_reference),
            distractor_tables=tuple(
                _pose(distractor, f"trials[{index}].distractor_tables[{distractor_index}]")
                for distractor_index, distractor in enumerate(distractors)
            ),
            participant_start_positions=_participant_start_positions(
                record, f"trials[{index}].participant_start_positions"
            ),
            notes=notes,
        )
    return result
