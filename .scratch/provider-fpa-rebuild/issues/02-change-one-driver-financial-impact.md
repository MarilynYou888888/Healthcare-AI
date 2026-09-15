# 02: Change One Driver and See Financial Impact

Status: ready-for-human
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: Ticket 2 implemented and verified. Paused for user review; do not begin Ticket 3.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Change Provider FTE from 4.0 to 3.5 and immediately see all dependent outputs update against the unchanged baseline.

## Dependencies

Blocked by: 01 — Public Benchmark + Synthetic Clinic Baseline

## Acceptance criteria

- [x] Given the approved baseline assumptions, changing Provider FTE from 4.0 to 3.5 must deterministically produce the expected reference outputs, including the current reference operating-income impact of -$21,740.40. This value must be calculated from the model and must not be hard-coded.
- [x] Automatically update available capacity, expected visits, revenue, variable labor expense, variable supply expense, total variable expense, contribution margin, operating income and scenario impact. Downstream outputs are read-only and require no manual edits.
- [x] Treat all reference values as regression expectations for the specified fixture, not universal product constants. The same formulas must work for other valid FTE values and other assumption combinations.
- [x] Expose the nine approved assumptions and deterministic dependency graph. Fixed expense affects operating income but not contribution margin; unit revenue/reimbursement affects revenue but not volume. Preserve separate variable labor and supplies.
- [x] Update the coherent baseline/scenario/delta view automatically, targeting 200 ms after a valid committed input on the recording machine. No model/network call participates in arithmetic.
- [x] Preserve baseline and public records. Support reset, changed-input highlighting, units, precision, invalid/blank input handling and N/A percentage reasons. Invalid/stale outputs cannot appear current or be reviewed.

## Tests

- [x] Independently calculate the approved fixture, including the -$21,740.40 reference impact; assert all downstream outputs.
- [x] Exercise other FTE values, all nine single-driver dependency paths, multiple edits, zero inputs and invalid values to detect hardcoded outputs.
- [x] Check financial identities, precision, immutable baseline, reset and stale-state handling.
- [x] Browser-edit only FTE and verify the entire cascade without downstream edits; measure actual update latency.

## Demo relevance

Highest-priority recruiting interaction: one editable assumption visibly drives a complete financial model.

## Requirement coverage

A02–A05, A13, A15.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Implementation was subsequently authorized one ticket at a time.


### Approved implementation clarification

Scenario Model and Executive Summary are two presentations of the same deterministic model. Ticket 2 provides the detailed editable analyst view and one revisioned, immutable ScenarioResult shared by later consumers. Ticket 3 adds commentary/review; Ticket 5 polishes Executive Summary and navigation. No additional tickets or spec reopening.

Workbook reference inspected read-only: `Hospital_FP&A_Hiring_Manager_Portfolio_EN.xlsx` in the supplied Desktop directory; a separate `(2)` copy was not available. Reuse explicit input-cell affordance (Assumptions!B5/B11/B16), traceable operating builds (Revenue!B5), and result-linked management views (HM_Dashboard!A3/E3/I3). Do not import hospital formulas, backfilled historical values, multiple years, or workbook narratives.

Implementation rationale: move Ticket 1's synthetic arithmetic from Python into one browser Decimal module to meet no-round-trip recalculation. Remove the Python formula implementation, preserve the nine formulas and 28-significant-digit/half-even policy, and run baseline/reference regression tests through the authoritative engine. Public benchmark loading stays Python and independent. Shared state holds draft inputs, immutable baseline, current result revision, changed drivers, last valid snapshot, and review eligibility. No summary or narrative duplicates arithmetic.

Approved test seams: deterministic scenario result, session state transitions, and browser input-to-output behavior, as specified in this ticket's test list.


### Completion — 2026-09-15

All acceptance criteria verified. The nine assumption cells drive one Decimal graph, with visible formulas, immutable baseline, scenario/dollar/percentage comparison, changed-driver highlighting, reset and stale invalid drafts. The shared result includes validation, source identity, units and revision; two subscribers receive the same immutable result. Programmatic state changes also synchronize visible inputs.

FTE-only reference outputs: capacity 1,386; visits 1,247.4; revenue $243,243.00; labor $68,607.00; supplies $22,453.20; total variable expense $91,060.20; contribution margin $152,182.80; operating income $67,182.80; impact −$21,740.40. All derived, with the reference impact appearing only in regression assertions/documentation.

Validation: full suite 18 tests passed, plus Chrome desktop/mobile browser acceptance. Ten input-to-painted-frame measurements were 26.5–34.2 ms, with zero recalculation requests; requests were blocked during this test. Source switching preserves the scenario and baseline, missing public references remain isolated, and invalid drafts retain explicitly stale results. Python compile and git whitespace checks passed; browser imports/execution verify JS syntax. No static type checker is configured.

Changed files: web/scenario.js, web/scenario-view.js, web/app.js, web/index.html, web/style.css, vendored Decimal/license; provider_fpa/scenario/__init__.py and provider_fpa/web.py; tests/test_scenario.py and tests/test_baseline.py; scripts/check_browser.py; README and this completion/review record. Public extracts and the original Excel workbook were not modified.

Deviation report: calculation location moved from Python to the browser for immediate offline interaction; duplicate Python formulas were removed. This was documented before implementation and preserves the approved formulas/precision. No new business logic, production services or historical Phase 3/4 investigation changes. Executive Summary remains Ticket 5; narrative/review remains Ticket 3. The available EN workbook was inspected for UX only; a separate `(2)` attachment was not found locally.

See [Ticket 2 review](../ticket-02-review.md). Local demo: http://127.0.0.1:8501/.
