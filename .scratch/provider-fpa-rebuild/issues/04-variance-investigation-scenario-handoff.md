# 04: Variance Investigation + Scenario Handoff

Status: ready-for-human
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: Ticket 4 explicitly authorized after Ticket 3 approval. Stop for user review after this ticket; Ticket 5 is not authorized.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Investigate a synthetic actual-versus-forecast variance, inspect evidence, review the cause and open a related scenario assumption without automatic changes.

## Dependencies

Blocked by: 02 — Change One Driver and See Financial Impact

## Acceptance criteria

- [x] Selectively recover compatible Phase 3 investigation and Phase 4 guarded investigation narrative plus tests. Inspect recovered code against the approved spec, rerun the complete recovered suite and report conflicts before changing business logic. Do not rebuild working finance rules or restore the old UI indiscriminately.
- [x] Expose one secondary workflow: Clinic-Month comparison and rule-selected Review Queue → facts/sources → driver/state/timing → disclosed fallback commentary → human review. Preserve critical rules and Analyst Override.
- [x] C01 supports Demand & Volume as primary and Provider Availability as contributing without unsupported 100% attribution. C04 retains unresolved cause/timing and refuses fabricated reduced-availability explanations. C03 keeps weather upstream, capacity contributing and volume primary.
- [x] Preserve all ten benchmark cases, seven Driver Families, evidence/source lineage, forbidden conclusions and distinct investigation/explanation success measures. Keep gold answers inaccessible to analysis and narration.
- [x] Retain the configurable historical 50% horizon threshold as a disclosed demo heuristic, not an industry standard. Keep recurrence distinct from Temporary/Structural classification.
- [x] Provide four in-session investigation actions: confirm supported cause, reject cause, keep unresolved, request further investigation. No autonomous confirmation or persistent audit infrastructure.
- [x] Explore related assumption navigates to Scenario Modeling with source context and a highlighted field. Do not infer FTE numerically from PTO, change an assumption automatically or mix investigation forecasts with scenario baselines. C04 offers investigation, not a fabricated prefilled causal scenario.
- [x] Share compatible recovered components without duplicate implementations. Ticket 3 scenario commentary is not a blocker; scenario interpretation remains a distinct contract.

## Tests

- [x] Run the complete recovered suite and ten-case evaluator; record actual failures and compatibility findings before business-rule changes.
- [x] Check threshold boundaries, evidence states, timing, lineage, gold isolation and C01/C04/C03 expected/prohibited conclusions.
- [x] Test four investigation actions and isolation from scenario decisions.
- [x] Browser-check C04 refusal and a supported-case handoff preserving context without numeric or approval leakage.

## Demo relevance

Provides the short C04 trust demonstration and supports deeper interview walkthroughs of C01/C03.

## Requirement coverage

A08–A10, A12, A15.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Implementation authorized by the subsequent Ticket 4 request.


Implementation and acceptance checks completed. See [Ticket 4 validation and review](../ticket-04-review.md). Standards and specification reviews complete; one accessibility finding fixed and verified. All 108 tests and 10/10 benchmark cases pass. Ready for user acceptance review; Ticket 5 has not started.
