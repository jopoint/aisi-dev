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

## ADR-0004: Offline-first synthetic MVP pipeline
- Decision: Add a minimal, modular Python pipeline under src/aisi for offline scene loading, interpretation, target structure generation, proposal synthesis/evaluation, and debug plotting.
- Rationale: Enables fast, testable end-to-end iterations before adding live CV, external optimizers, or TouchDesigner integration.
- Consequences: Initial heuristics are intentionally simple and contain TODO stubs for adaptive/optimized behavior.
