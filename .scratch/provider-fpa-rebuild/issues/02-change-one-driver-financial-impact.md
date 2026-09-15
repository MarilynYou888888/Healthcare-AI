# 02: Change One Driver and See Financial Impact

Status: ready-for-agent
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: Explicitly authorized for Ticket 2 only. Stop for user review before Ticket 3.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Change Provider FTE from 4.0 to 3.5 and immediately see all dependent outputs update against the unchanged baseline.

## Dependencies

Blocked by: 01 — Public Benchmark + Synthetic Clinic Baseline

## Acceptance criteria

- [ ] Given the approved baseline assumptions, changing Provider FTE from 4.0 to 3.5 must deterministically produce the expected reference outputs, including the current reference operating-income impact of -$21,740.40. This value must be calculated from the model and must not be hard-coded.
- [ ] Automatically update available capacity, expected visits, revenue, variable labor expense, variable supply expense, total variable expense, contribution margin, operating income and scenario impact. Downstream outputs are read-only and require no manual edits.
- [ ] Treat all reference values as regression expectations for the specified fixture, not universal product constants. The same formulas must work for other valid FTE values and other assumption combinations.
- [ ] Expose the nine approved assumptions and deterministic dependency graph. Fixed expense affects operating income but not contribution margin; unit revenue/reimbursement affects revenue but not volume. Preserve separate variable labor and supplies.
- [ ] Update the coherent baseline/scenario/delta view automatically, targeting 200 ms after a valid committed input on the recording machine. No model/network call participates in arithmetic.
- [ ] Preserve baseline and public records. Support reset, changed-input highlighting, units, precision, invalid/blank input handling and N/A percentage reasons. Invalid/stale outputs cannot appear current or be reviewed.

## Tests

- [ ] Independently calculate the approved fixture, including the -$21,740.40 reference impact; assert all downstream outputs.
- [ ] Exercise other FTE values, all nine single-driver dependency paths, multiple edits, zero inputs and invalid values to detect hardcoded outputs.
- [ ] Check financial identities, precision, immutable baseline, reset and stale-state handling.
- [ ] Browser-edit only FTE and verify the entire cascade without downstream edits; measure actual update latency.

## Demo relevance

Highest-priority recruiting interaction: one editable assumption visibly drives a complete financial model.

## Requirement coverage

A02–A05, A13, A15.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Implementation has not started.


### Approved implementation clarification

Scenario Model and Executive Summary are two presentations of the same deterministic model. Ticket 2 provides the detailed editable analyst view and one revisioned, immutable ScenarioResult shared by later consumers. Ticket 3 adds commentary/review; Ticket 5 polishes Executive Summary and navigation. No additional tickets or spec reopening.

Workbook reference inspected read-only: `Hospital_FP&A_Hiring_Manager_Portfolio_EN.xlsx` in the supplied Desktop directory; a separate `(2)` copy was not available. Reuse explicit input-cell affordance (Assumptions!B5/B11/B16), traceable operating builds (Revenue!B5), and result-linked management views (HM_Dashboard!A3/E3/I3). Do not import hospital formulas, backfilled historical values, multiple years, or workbook narratives.

Implementation rationale: move Ticket 1's synthetic arithmetic from Python into one browser Decimal module to meet no-round-trip recalculation. Remove the Python formula implementation, preserve the nine formulas and 28-significant-digit/half-even policy, and run baseline/reference regression tests through the authoritative engine. Public benchmark loading stays Python and independent. Shared state holds draft inputs, immutable baseline, current result revision, changed drivers, last valid snapshot, and review eligibility. No summary or narrative duplicates arithmetic.

Approved test seams: deterministic scenario result, session state transitions, and browser input-to-output behavior, as specified in this ticket's test list.
