# Ticket 4 validation and review

Scope: Variance Investigation + Scenario Handoff only. Fixed point: `c1ec18a` (user-created pre-recovery snapshot). Tickets 1–3 preserved; Ticket 5 remains deferred.

## Recovery and compatibility

Selectively restored Phase 3/4 from `ceb51b3`: immutable records, CSV loading, calculations, review rules, driver/evidence/timing classification, guarded narrative, presentation, CLI/evaluator, benchmark generator and 73 historical tests. Historical Streamlit UI and dependencies were not restored. All recovered files match the source commit byte-for-byte except `provider_fpa/engine.py`, which forwards the existing optional `material_fraction` parameter with unchanged 0.5 default. No driver, causal, variance, timing-classification or narrative-guard rules were changed.

Before integration: 73 historical tests passed in a pristine temporary archive; all 10 cases / 70 benchmark dimensions passed. After recovery: all 98 combined tests passed before adapter/UI work. Current product framing supersedes historical domain-document statements that variance investigation alone is the primary MVP.

Compatibility finding disclosed during implementation: the historical narrative guard rejects prose for some additional on-plan/unranked operational targets. The adapter withholds this prose and displays an explicit notice; deterministic facts, lineage, queue and Analyst Override remain available. All ten primary benchmark narratives pass unchanged. Human-reviewed results are not passed through the system-only narrative formatter; the UI clearly separates its pre-review commentary from human judgment.

## Implemented workflow

Clinic-Month actual vs Latest Approved Forecast → rule-selected Review Queue (plus below-threshold targets and Analyst Override) → observed facts/source details → drivers and six epistemic states → timing and unresolved questions → disclosed offline guarded narrative → session human review → optional related scenario assumption.

- C01: primary Demand & Volume, contributing Provider Availability; no guessed allocation. Provider FTE handoff.
- C04: unresolved cause/timing, on-plan availability rejected; no supported or prefilled causal handoff.
- C03: volume primary, clinic capacity contributing, weather upstream Observed Fact. Clinic operating days handoff.
- Four explicit human actions: confirm supported cause, reject cause, keep unresolved, request further investigation. Only supported drivers can be confirmed. Original system output remains intact. Decisions are snapshot/target-scoped in page memory; navigation retains them, reload clears them. A new choice replaces the prior choice for that driver; this is not a persisted/authenticated audit trail.
- Handoff retains case, Clinic-Month, driver/state and evidence references, opens and highlights an input, and makes no changes to values, baseline, scenario revision, scenario review or approved forecasts.
- Configurable 50% timing threshold is a disclosed demo heuristic; recurring remains separate.
- Case identities are projected from the manifest; fixture review expectations and gold answers do not enter analysis/narration. Explicit asset routes never serve gold.

## Validation

- Complete suite: 107 tests passed, including all recovered 73 tests and all Ticket 1–3 tests.
- Evaluator: 10/10 cases; 70/70 dimensions, including prohibited conclusions.
- Browser: source display, six-state controls, all four human decisions, reload clearing, C01/C03 non-mutating handoffs, C04 refusal, override, API confirmation/stale-snapshot rejection, no gold routes and isolated scenario review.
- Prior browser checks: public benchmarks, synthetic labels, one-input cascade, summary/commentary revision sharing, keyboard navigation, offline operation and review invalidation all pass.
- Visual checks: inspected desktop C04 and C01 handoff plus mobile; no horizontal overflow. Investigation-fetch failure leaves the scenario engine usable.
- FTE change regression remains model-derived −$21,740.40. Maximum measured local input-to-painted-frame latency across ten edits: 34.1 ms, with zero recalculation requests. Measurement is device-specific.
- Python compile and Git whitespace checks pass. No static type checker is configured.
- `web/scenario.js`, `web/interpretation.js`, scenario input data and public benchmark datasets have no diff from the snapshot.

## Standards

Pending required independent review.

## Spec

Pending required independent review.
