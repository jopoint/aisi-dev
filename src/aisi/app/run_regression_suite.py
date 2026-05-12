from __future__ import annotations

import argparse
import csv
import json
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from aisi.app.regression_utils import load_summary_json, normalize_csv_value, safe_get, write_text
from aisi.app.run_synthetic_test import run as run_single_synthetic_test


@dataclass(slots=True)
class RegressionCase:
    case_name: str
    scene_file: str
    learning_format: str


DEFAULT_CASES = [
    RegressionCase("input_clean_4tables__input", "data/aisi/scenes/input_clean_4tables.json", "input"),
    RegressionCase("input_messy_4tables__input", "data/aisi/scenes/input_messy_4tables.json", "input"),
    RegressionCase("groupwork_clean_4tables__groupwork", "data/aisi/scenes/groupwork_clean_4tables.json", "groupwork"),
    RegressionCase("groupwork_messy_4tables__groupwork", "data/aisi/scenes/groupwork_messy_4tables.json", "groupwork"),
    RegressionCase("discussion_clean_4tables__discussion", "data/aisi/scenes/discussion_clean_4tables.json", "discussion"),
    RegressionCase("random_4tables__input", "data/aisi/scenes/random_4tables.json", "input"),
    RegressionCase("random_4tables__groupwork", "data/aisi/scenes/random_4tables.json", "groupwork"),
    RegressionCase("random_4tables__discussion", "data/aisi/scenes/random_4tables.json", "discussion"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AISI regression suite over a fixed scene list.")
    parser.add_argument("--suite-name", default=None, help="Suite name; defaults to timestamp-based value.")
    parser.add_argument(
        "--outdir",
        default="data/aisi/regression",
        help="Base output directory for the suite.",
    )
    parser.add_argument(
        "--only-format",
        choices=["input", "groupwork", "discussion"],
        default=None,
        help="Filter test cases to a single learning format.",
    )
    parser.add_argument(
        "--only-scene",
        default=None,
        help="Filter test cases to one scene file name, e.g. input_clean_4tables.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    suite_name = args.suite_name or datetime.now().strftime("%Y%m%d_%H%M%S")
    base_outdir = Path(args.outdir)
    suite_dir = base_outdir / suite_name
    suite_dir.mkdir(parents=True, exist_ok=True)

    cases = _filter_cases(DEFAULT_CASES, only_format=args.only_format, only_scene=args.only_scene)
    print(f"Regression suite: {suite_name}")
    print(f"Output: {suite_dir.resolve()}")
    print(f"Cases: {len(cases)}")

    case_records: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        record = _run_case(case=case, suite_dir=suite_dir, index=index, total=len(cases))
        case_records.append(record)

    _write_suite_reports(suite_dir, case_records, suite_name=suite_name)
    _print_suite_summary(case_records)


def _filter_cases(
    cases: list[RegressionCase],
    *,
    only_format: str | None,
    only_scene: str | None,
) -> list[RegressionCase]:
    filtered = []
    for case in cases:
        if only_format and case.learning_format != only_format:
            continue
        if only_scene and Path(case.scene_file).name != only_scene:
            continue
        filtered.append(case)
    return filtered


def _run_case(
    *,
    case: RegressionCase,
    suite_dir: Path,
    index: int,
    total: int,
) -> dict[str, Any]:
    case_outdir = suite_dir / case.case_name
    case_outdir.mkdir(parents=True, exist_ok=True)
    scene_path = Path(case.scene_file)

    print(f"[{index}/{total}] {case.case_name} -> running")

    record: dict[str, Any] = {
        "case_name": case.case_name,
        "scene_file": case.scene_file,
        "learning_format": case.learning_format,
        "output_dir": str(case_outdir.resolve()),
        "success": False,
        "error": None,
        "total_score": None,
        "scene_type": None,
        "overlap_violations": None,
        "clearance_violations": None,
        "roi_violations": None,
        "repair_applied": None,
        "assignment_cost_total": None,
    }

    try:
        run_single_synthetic_test(scene_path=scene_path, learning_format=case.learning_format, outdir=case_outdir)
        summary = load_summary_json(case_outdir / "summary.json")
        flattened = _extract_case_metrics(summary)
        record.update(flattened)
        record["success"] = True
        print(
            f"[{index}/{total}] {case.case_name} -> ok | total_score={_fmt(record['total_score'])} "
            f"scene_type={_fmt(record['scene_type'])} overlap={_fmt(record['overlap_violations'])} "
            f"clearance={_fmt(record['clearance_violations'])} roi={_fmt(record['roi_violations'])}"
        )
    except Exception as exc:  # noqa: BLE001
        error_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        record["error"] = error_text
        _write_failure_summary(case_outdir, case, error_text)
        print(f"[{index}/{total}] {case.case_name} -> FAILED | {exc.__class__.__name__}: {exc}")

    return record


def _extract_case_metrics(summary: dict[str, Any]) -> dict[str, Any]:
    evaluation = summary.get("evaluation") if isinstance(summary.get("evaluation"), dict) else {}
    details = evaluation.get("details") if isinstance(evaluation.get("details"), dict) else {}

    assignment_cost_total = _extract_assignment_cost(summary)

    return {
        "total_score": safe_get(evaluation, ["total_score"]),
        "scene_type": safe_get(summary, ["scene_features", "scene_type"]),
        "overlap_violations": _coerce_number(summary.get("overlap_violations", safe_get(details, ["overlap_violations"]))),
        "clearance_violations": _coerce_number(summary.get("clearance_violations", safe_get(details, ["clearance_violations"]))),
        "roi_violations": _coerce_number(summary.get("roi_violations", safe_get(details, ["roi_violations"]))),
        "repair_applied": _coerce_bool(summary.get("repair_applied", safe_get(details, ["repair_applied"]))),
        "assignment_cost_total": assignment_cost_total,
        "input_shape_penalty": _coerce_number(summary.get("input_shape_penalty", safe_get(details, ["input_shape_penalty"]))),
    }


def _extract_assignment_cost(summary: dict[str, Any]) -> float | None:
    notes = safe_get(summary, ["layout_proposal", "generation_notes"], default=[])
    if not isinstance(notes, list):
        return None

    prefix = "assignment_cost_total="
    for note in notes:
        if not isinstance(note, str) or not note.startswith(prefix):
            continue
        try:
            return float(note[len(prefix) :])
        except ValueError:
            return None
    return None


def _write_failure_summary(case_outdir: Path, case: RegressionCase, error_text: str) -> None:
    payload = {
        "case_name": case.case_name,
        "scene_file": case.scene_file,
        "learning_format": case.learning_format,
        "success": False,
        "error": error_text,
    }
    write_text(case_outdir / "summary.json", json.dumps(payload, indent=2))
    write_text(case_outdir / "error.txt", error_text)


def _write_suite_reports(suite_dir: Path, case_records: list[dict[str, Any]], *, suite_name: str) -> None:
    json_path = suite_dir / "regression_summary.json"
    csv_path = suite_dir / "regression_summary.csv"
    md_path = suite_dir / "index.md"

    write_text(json_path, json.dumps({"suite_name": suite_name, "cases": case_records}, indent=2))
    _write_csv(csv_path, case_records)
    _write_markdown_report(md_path, suite_name, case_records)


def _write_csv(csv_path: Path, case_records: list[dict[str, Any]]) -> None:
    columns = [
        "case_name",
        "scene_file",
        "learning_format",
        "success",
        "total_score",
        "scene_type",
        "overlap_violations",
        "clearance_violations",
        "roi_violations",
        "repair_applied",
        "assignment_cost_total",
        "output_dir",
        "error",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in case_records:
            row = {column: normalize_csv_value(record.get(column)) for column in columns}
            writer.writerow(row)


def _write_markdown_report(suite_dir: Path, suite_name: str, case_records: list[dict[str, Any]]) -> None:
    lines = [f"# Regression Suite {suite_name}", "", "| Case | Success | Total Score | Scene Type | Overlap | Clearance | ROI | Repair | Assignment Cost |", "| --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: |"]
    for record in case_records:
        lines.append(
            "| {case} | {success} | {score} | {scene} | {overlap} | {clearance} | {roi} | {repair} | {assignment} |".format(
                case=record.get("case_name", ""),
                success="yes" if record.get("success") else "no",
                score=_fmt(record.get("total_score")),
                scene=_fmt(record.get("scene_type")),
                overlap=_fmt(record.get("overlap_violations")),
                clearance=_fmt(record.get("clearance_violations")),
                roi=_fmt(record.get("roi_violations")),
                repair=_fmt(record.get("repair_applied")),
                assignment=_fmt(record.get("assignment_cost_total")),
            )
        )
    write_text(suite_dir / "index.md", "\n".join(lines) + "\n")


def _print_suite_summary(case_records: list[dict[str, Any]]) -> None:
    print("Regression suite completed.")
    for record in case_records:
        status = "ok" if record.get("success") else "FAILED"
        print(
            f"{record.get('case_name')} | {status} | total_score={_fmt(record.get('total_score'))} "
            f"scene_type={_fmt(record.get('scene_type'))} overlap={_fmt(record.get('overlap_violations'))} "
            f"clearance={_fmt(record.get('clearance_violations'))} roi={_fmt(record.get('roi_violations'))}"
        )


def _coerce_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes"}:
            return True
        if lowered in {"0", "false", "no"}:
            return False
    return None


def _fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.3f}"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


if __name__ == "__main__":
    main()
