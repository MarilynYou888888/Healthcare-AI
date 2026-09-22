# 02: Run Existing FP&A Workflows on User Data

Status: ready-for-human
Approval: Ticket 2 implementation completed and awaiting user review. Ticket 3 and Ticket 4 have not started.
Blocked by: 01 — Self-Service Data Import & Validation.
Specification: Approved narrow V2 specification, including the fully free product clarification.

## What to build

A Provider FP&A Analyst can select an imported entity and Calendar Month, model a protected scenario, view the Executive Summary, and investigate imported Actual vs Forecast performance with traceable evidence and explicit human judgment.

## Acceptance criteria

- [ ] Entity, period, and uploaded scenario-name selectors initialize the correct planning row. Selection changes cannot mix entities/periods or transfer prior review decisions; warn before discarding an edited draft.
- [ ] Imported baselines remain immutable. Scenario edits and Reset Scenario affect only the selected draft and its review state. Reimport/selection creates a new baseline identity.
- [ ] The existing deterministic scenario engine retains its nine assumptions, dependency formulas, Decimal precision, and rounding behavior. The upload adapter maps fields rather than duplicating financial calculations. Public benchmarks remain invalid scenario inputs.
- [ ] Changing an assumption recalculates all dependent outputs through the existing model. Executive Summary preserves Expected Visits, Modeled Net Patient Revenue, Contribution Margin, Modeled Operating Income, Operating Margin, bridge, baseline/scenario comparison, expense mix, and calculation trace.
- [ ] Summary, charts, and trace consume the same current result/revision. Existing margin, bridge, and expense-share derivations move once into shared result assembly; formulas are not duplicated in views, imports, or future commentary. Preserve undefined-percentage and zero-revenue behavior.
- [ ] Invalid drafts visibly mark last-valid outputs stale and prevent current commentary, export, or review. Currency, source, entity, and period labels correctly describe the selected uploaded data.
- [ ] Imported Actual vs Forecast and Operating Events adapt to the existing investigation contracts. Confirm closed months and Latest Approved Forecast comparator explicitly. Metric meanings/units are validated; provider FTE is never substituted for provider availability days.
- [ ] The existing Python investigation engine receives only necessary normalized data through a validated stateless loopback request. Raw workbooks remain in the browser. No payload/result logging, persistent cache, temporary upload files, or external calls are introduced; browser memory owns session continuity.
- [ ] Show user-configured session review thresholds, always-review choices, and explicit Analyst Override. Missing rules are disclosed; synthetic thresholds are not silently applied to uploaded data.
- [ ] Missing supporting metrics, failed reconciliation, unsupported mechanisms, ambiguous evidence, and insufficient causal evidence remain Unresolved. Do not back-solve missing operating inputs or fabricate contribution estimates.
- [ ] Event descriptions and Analyst Notes do not trigger free-text causal extraction. Event end dates alone do not establish recovery/persistence. Optional structured timing evidence and an explicit forecast horizon follow the approved contract; otherwise use unresolved timing and the labeled fallback horizon as applicable.
- [ ] Observed Facts, Supporting Evidence, system assessment, and human decisions remain distinct. Only eligible Supported Drivers can be explicitly human-confirmed. Reject stale snapshot decisions; no automatic forecast update or approval occurs.
- [ ] Provide a separate plain-text Analyst Note scoped to the selected analysis. It never becomes evidence or a confirmed cause automatically.
- [ ] Scenario-only and performance-only data enable their respective workflows. Operating events alone supply context and never create an investigation target; Ticket 4 finalizes partial-state presentation.

## Tests and validation

- Reuse V1 scenario reference outputs and dependency tests to verify imported recalculation, shared result identity, baseline immutability, invalid drafts, and Reset Scenario.
- Browser tests select multiple entities, periods, and planning scenarios; verify no data/review leakage and correct currency/provenance labels.
- Investigation contract cases cover performance/event adaptation, unsupported metric/event semantics, FTE versus available days, missing rate/volume inputs, failed bridges, unsupported currency mechanisms, review settings/override, and unresolved outcomes.
- Verify structured timing requirements, note isolation, Supported versus Confirmed transitions, and stale snapshot rejection.
- Verify normalized inputs are request-local, not persisted/logged/transmitted externally. Exercise existing causal-boundary tests and C01–C10 regressions.

## Demo relevance

Select Nashville Specialty Clinic, August 2026, change FTE from 4.0 to 3.5, and show dependent financial outputs and Executive Summary updating while the baseline stays protected. Open an imported variance with insufficient evidence and demonstrate Unresolved rather than an invented cause.

## Boundaries and handoff

Reuse the V1 visit-based model; do not add hospital-specific engines, consolidation, FX conversion, forecast versioning, or automatic forecasts. Apply the approved identity/currency/contract adaptations without weakening V1. No authentication, databases, PHI/EHR support, RAG, keys, paid APIs, LLM tokens, or external AI dependencies. Ticket 3 consumes the current calculated results and evidence states; no new low-level tickets are authorized.

## Completion evidence

Implemented in commit `a3f6844` plus the provenance follow-up. Confirmed Planning Assumptions now initialize the existing Decimal scenario engine for selected entity, period, and uploaded scenario; baseline data is immutable and scenario edits remain draft-only. Executive Summary, charts, and calculation trace consume the same immutable `ScenarioResult` revision.

Imported Actual vs Forecast records use a bounded, same-origin loopback request to the local Python process. Review thresholds, closed-month and Latest Approved Forecast confirmations, Analyst Override, structured timing evidence, and human driver decisions remain session-only. Operating Events alone never create a variance target. Unsupported mechanisms, missing reconciliation, FTE/available-days ambiguity, unsupported currency mechanisms, and insufficient evidence remain Unresolved. Mixed user/synthetic evidence retains provenance in each Source Reference and the UI label.

Validation: `python -m unittest discover -s tests -q` — **158 passed**. Ticket 2 browser acceptance rehearsal passed at 1440×1000 and 390×844 with no browser errors, external requests, or raw upload requests. Focused uploaded-investigation tests: **10 passed**. Python compile and `git diff --check` passed. V1 scenario, benchmark, and investigation regressions remain green.

## Comments

The user approved publication of exactly four tickets in dependency order 1 → 2 → 3 → 4. Publication does not authorize implementation. The holding status preserves that review gate and does not indicate unresolved scope.
