# 05: Recordable Recruiting Demo

Status: ready-for-human
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: Ticket 5 explicitly authorized after Ticket 4 approval. Stop for user review after completion.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Deliver a polished, repeatable 85-second web demonstration with complete validation and honest portfolio messaging.

## Dependencies

Blocked by: 03 — Scenario Interpretation + Analyst Judgment; 04 — Variance Investigation + Scenario Handoff

## Acceptance criteria

- [x] Run the complete sequence: HCA/Tenet context → synthetic baseline → FTE 4.0→3.5 → automatic outputs → disclosed fallback commentary → C04 unresolved → human judgment. No hidden operator edits.
- [x] Keep inputs and outputs legible together on the recording viewport; polish loading, validation, empty/stale states, labels, source access and reset without adding new product scope.
- [x] Rerun the complete recovered and new tests and all ten investigation benchmarks after integration. All reported results must come from actual runs, not old reports or mocked live-generation claims.
- [x] Complete a timed 60–90 second rehearsal targeting 85 seconds. The first 60 seconds explain the user, manual pain, public/synthetic separation, dependency model, narrative limits and human authority.
- [x] Provide startup/reset/demo instructions and accurate model/source limitations. The application must be screen-recordable; a CLI, mockup or script alone does not satisfy delivery.
- [x] Demo works without an API key, live public-filing fetch or production services. Public data stays immutable and synthetic data is never presented as proprietary company data.
- [x] No claims of live AI, HCA/Tenet affiliation, real clinic forecast accuracy, measured ROI or production readiness. Record actual rehearsal feedback; do not claim hiring-manager validation unless conducted.

## Tests

- [x] Execute full regression and focused browser end-to-end checks, including one-input cascade, all data labels, narrative/review state and C04.
- [x] Verify offline startup, reset/repeatability, company-switch independence and no stale cross-module approvals.
- [x] Measure recalculation latency and timed rehearsal; inspect the recording viewport for readable values/disclosures.
- [x] Check all approved acceptance criteria and report any remaining failure rather than mark the project done.

## Demo relevance

Turns working outcomes into a clear recruiting portfolio demonstration: deterministic calculations → disclosed interpretation → human judgment.

## Requirement coverage

A01–A18 and Definition of Done.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Ticket 5 implementation explicitly authorized in the subsequent user request.


Ticket 5 visual clarifications implemented within the approved outcome: charcoal/gold system, shared-result charts, dependency trace, normalized public comparison, responsive layout and demo flow. [Validation and review](../ticket-05-review.md). Standards and specification review completed; one chart-range edge case fixed. Final suite: 115 tests; benchmark: 10/10 cases, 70/70 checks; timed UI rehearsal: 85.0 seconds. Stopped for user acceptance review.
