"""Non-blocking JSONL event logging for the minimal Study controller."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import queue
import threading
import time
import uuid
from typing import Any, Callable


SourcePoseProvider = Callable[[], dict[str, Any] | None]


class JsonlEventLogger:
    """Append events on a dedicated thread and flush every JSONL record."""

    def __init__(self, directory: str | Path, *, session_name: str | None = None) -> None:
        target_directory = Path(directory)
        target_directory.mkdir(parents=True, exist_ok=True)
        name = session_name or datetime.now(timezone.utc).strftime("study_%Y%m%dT%H%M%SZ")
        self.path = target_directory / f"{name}.jsonl"
        self._session_monotonic = time.monotonic()
        self._queue: queue.Queue[dict[str, Any] | None] = queue.Queue()
        self._thread = threading.Thread(target=self._write_loop, name="aisi-study-jsonl", daemon=True)
        self._thread.start()

    def log(self, event: dict[str, Any]) -> None:
        record = dict(event)
        record.setdefault("timestamp_iso", datetime.now(timezone.utc).isoformat())
        monotonic = time.monotonic()
        record.setdefault("monotonic_s", monotonic)
        record.setdefault("elapsed_s", monotonic - self._session_monotonic)
        self._queue.put(record)

    def close(self) -> None:
        self._queue.put(None)
        self._thread.join(timeout=2.0)

    def _write_loop(self) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            while True:
                record = self._queue.get()
                if record is None:
                    return
                handle.write(json.dumps(record, sort_keys=True) + "\n")
                handle.flush()


class StudySessionLogger(JsonlEventLogger):
    """Append-only event logger owned by one participant-facing Study session."""

    def __init__(self, runs_directory: str | Path, *, session_id: str | None = None) -> None:
        self.session_id = session_id or (
            datetime.now(timezone.utc).strftime("study_%Y%m%dT%H%M%SZ")
            + "_" + uuid.uuid4().hex[:8]
        )
        self.session_directory = Path(runs_directory) / self.session_id
        self.session_directory.mkdir(parents=True, exist_ok=False)
        # Keep the existing asynchronous, flushed JSONL implementation; only
        # its canonical destination changes for participant sessions.
        super().__init__(self.session_directory, session_name="events")
        self.manifest_path = self.session_directory / "manifest.json"
        self._manifest: dict[str, Any] = {"session_id": self.session_id}

    def update_manifest(self, updates: dict[str, Any]) -> None:
        self._manifest.update(updates)
        temporary = self.manifest_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(self._manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.manifest_path)


class LiveSceneSourcePoseProvider:
    """Best-effort source pose reader; unavailable/live-locked scenes yield None."""

    def __init__(self, scene_path: str | Path, table_id: str = "table_00") -> None:
        self.scene_path = Path(scene_path)
        self.table_id = table_id

    def __call__(self) -> dict[str, Any] | None:
        try:
            with self.scene_path.open("r", encoding="utf-8") as handle:
                scene = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        tables = scene.get("tables") if isinstance(scene, dict) else None
        if not isinstance(tables, list):
            return None
        for table in tables:
            if isinstance(table, dict) and str(table.get("id")) == self.table_id:
                try:
                    return {
                        "id": self.table_id,
                        "x_cm": float(table["x_cm"]),
                        "y_cm": float(table["y_cm"]),
                        "rotation_deg": float(table["rotation_deg"]),
                    }
                except (KeyError, TypeError, ValueError):
                    return None
        return None
