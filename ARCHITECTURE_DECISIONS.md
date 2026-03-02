# Architecture Decisions (ADRs)

Append-only short ADRs capturing key starting choices.

## ADR-0001: Marker-based tracking first
- Decision: Use ArUco markers (OpenCV) for furniture tracking initially.
- Rationale: Fast to bootstrap, stable IDs, easier debugging and calibration.
- Consequences: Requires printing/placing markers and optionally opencv-contrib. Can later replace with model-based detection.

## ADR-0002: Rule-based inference first
- Decision: Implement layout and social state detection using simple rules.
- Rationale: Transparent, debuggable, and easy to iterate with domain knowledge.
- Consequences: May be less robust initially; can evolve to ML later.

## ADR-0003: Record/Replay as a core capability
- Decision: Support JSONL event recording and replay from day one.
- Rationale: Essential for debugging sensing and inference deterministically.
- Consequences: Slight overhead to maintain event schema, but unlocks faster iteration.
