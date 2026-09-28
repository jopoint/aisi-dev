# AISI TODO / Handoff Checklist

Last updated: 2026-09-28

This list separates immediate repository hygiene, current layout work, Study readiness, and deferred research work. Do not execute all items automatically; use it to select a coherent next task.

## P0 — Preserve and understand the current worktree

- [ ] Inspect `git status` and the complete diff before editing.
- [ ] Review the uncommitted Rect Input implementation in:
  - `src/aisi/generation/layout_synthesizer.py`
  - `tests/test_rect_template_layouts.py`
  - `scripts/generate_rect_layout_debug_plots.py`
  - `NOTES.md`
- [ ] Re-run the focused Rect layout tests in the actual repository environment.
- [ ] Re-run `git diff --check`.
- [ ] Inspect the final count-1–5 Input plots, especially counts 3 and 5.
- [ ] Decide whether generated debug directories should remain untracked, be archived elsewhere, or be intentionally committed.
- [ ] Commit the Rect Input block only after explicit user approval.

Done when:

- the dirty diff is understood;
- tests are current rather than only history-reported;
- no unrelated/runtime artifacts are staged;
- Input counts 1–5 are either deliberately committed or deliberately left as work in progress.

## P0 — Finalize Rect Groupwork counts 1–5

- [ ] Treat full seat/movement clearance inside the ROI as an explicit acceptance criterion, or record a deliberate contrary decision.
- [ ] Decide whether the `4 cm` pair seam is intentional and sufficiently tolerant.
- [ ] Find final count-3 geometry with a Pair + Singleton and more than the current `40 cm` inter-island footprint gap where feasible.
- [ ] Find final count-4 geometry with two readable islands and sufficient movement space.
- [ ] Solve count 5 (`2 Pairs + Singleton`) under full clearance-in-ROI requirements.
- [ ] If count 5 is infeasible under current semantics, document the geometric proof/limitations before changing constraints.
- [ ] Remove unreachable six-table Groupwork template data after the five-table capacity decision is finalized.
- [ ] Add exact coordinate, pair membership, rotation/facing, overlap, clearance, ROI, and full-clearance-in-ROI tests.
- [ ] Regenerate and inspect comparison plots for counts 1–5.
- [ ] Do not change Input, Discussion, Study Mode, tracking, calibration, or TouchDesigner during this block.

Done when:

- all counts 1–5 have explicit, defensible geometry;
- hard constraints and full clearance-in-ROI checks pass;
- the pair seam and singleton meaning are documented;
- plots and focused tests agree with the implementation.

## P0 — Pilot/Study readiness review

- [ ] Physically run all eight `pilot_v6` trials in both conditions.
- [ ] Verify HOME, READY, ACTIVE, and COMPLETE transitions in the authoritative TouchDesigner project.
- [ ] Verify floor-only and dual-surface visuals match the written method description.
- [ ] Verify active-table binding and distractor binding for T3/T4 under real tracking.
- [ ] Verify objective arrival (`8 cm`, `5°`, `0.5 s`) behaves acceptably with real tracking jitter.
- [ ] Verify participant-declared completion remains independent from objective arrival.
- [ ] Verify logs, session manifest, attempt/run indices, tracking-loss intervals, and trial-definition hash.
- [ ] Review `trials.json` human-readable notes for consistency with numeric poses.
- [ ] If geometry changes are required, create `trials_pilot_v7.json` before updating the active file.

Done when:

- a complete participant-like session can be run without manual data repair;
- visuals, tracking, controller state, and logs stay synchronized;
- every physical deviation is either fixed or documented.

## P1 — Freeze the analysis plan before data collection

- [ ] State one primary research question comparing Floor-only and Dual-surface.
- [ ] State a secondary/exploratory question about task-specific differences.
- [ ] Describe T1–T4 as a 2×2 design structure without claiming unverified orthogonality.
- [ ] Define exactly what information appears on each surface in each condition.
- [ ] Choose primary, secondary, and exploratory outcomes.
- [ ] Decide whether the small sample is framed as pilot/exploratory.
- [ ] Predefine treatment of aborted trials, tracking loss, missing objective arrival, and repeated attempts.
- [ ] Document apparatus accuracy, tracking frequency/latency, projection, and calibration sufficiently for the paper.

Done when:

- implementation, Study protocol, and paper language use the same definitions;
- metrics are prioritized before inspecting participant outcomes.

## P1 — Documentation sync

- [ ] Update the root `README.md`; its current prototype-status, vision, geometry, and priority sections are outdated.
- [ ] Mark `docs/PROJECT_STATE_2026-05.md` clearly as historical or replace it with a dated current state.
- [ ] Link `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, and `TODO.md` from the README.
- [ ] Ensure macOS and Windows launch instructions reflect actual supported workflows.
- [ ] Document the current Study controller, active trial version, logging, and metrics commands.
- [ ] Keep physically confirmed facts separate from repository-only verification.

## P1 — Focused regression commands to establish

There is no canonical repository-wide command. Confirm and document the narrowest working commands for:

- [ ] Rect template layouts and geometry;
- [ ] Study trial definitions;
- [ ] Study control/state transitions;
- [ ] Study tracking/binding;
- [ ] Study logging and metrics;
- [ ] TouchDesigner builder structure tests;
- [ ] vision table association and tracking-only OSC.

Do not install optional dependencies merely to expand test scope.

## P2 — General layout follow-up

- [ ] Visually review Discussion counts 1–5 after the five-table capacity change.
- [ ] Verify mixed Summit/Sprint/Rect layouts after current Rect-specific work is stable.
- [ ] Design Scout-specific seating and Groupwork semantics as a dedicated task.
- [ ] Decide which Summit/Sprint sides may pair and how seating zones are derived.
- [ ] Preserve generic polygon support so the decision does not require a geometry rewrite.

## P2 — Tracking follow-up

- [ ] Keep the current tracking baseline frozen until a reproducible failure is recorded.
- [ ] If tuning resumes, capture the failing scene/log first and compare against the successful reacquisition baseline.
- [ ] Separate table detection, association, smoothing, projection alignment, and Study binding when diagnosing failures.

## P2 — Repository hygiene

- [ ] Decide whether `.gitignore` should cover recurring debug/runtime folders.
- [ ] Never blanket-ignore data that is intentionally versioned, such as frozen trial definitions.
- [ ] Keep model files, calibration captures, run logs, and generated plots under explicit policy rather than ad hoc staging.

## Open decisions requiring Johannes

- [ ] Is the Rect Groupwork pair seam exactly `4 cm`, or should it include a physical/tracking tolerance?
- [ ] Must every Groupwork seat/movement zone lie completely inside the `500 × 500 cm` ROI?
- [ ] Is a Groupwork singleton an individual station or part of an open group?
- [ ] Is `pilot_v6` ready for data collection, or still a pre-pilot geometry?
- [ ] Which measures are formally primary versus exploratory?
- [ ] Should the current dirty Rect Input block be committed before Groupwork implementation starts?
