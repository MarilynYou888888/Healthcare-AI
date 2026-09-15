# 03: Scenario Interpretation + Analyst Judgment

Status: ready-for-agent
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: User explicitly authorized Ticket 3 only. Stop for review before Ticket 4.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Read an explanation of the current scenario and record an analyst decision without changing financial calculations or an approved forecast.

## Dependencies

Blocked by: 02 — Change One Driver and See Financial Impact

## Acceptance criteria

- [ ] Visibly distinguish three responsibilities: deterministic financial calculations; offline/demo fallback narrative commentary; human analyst judgment.
- [ ] Label narrative explicitly as “Offline demo — deterministic fallback commentary; no live LLM used.” The UI, recording and portfolio wording must not imply that deterministic fallback text is live AI generation. No API key is required.
- [ ] Commentary consumes the validated current ScenarioResult and formats its computed values; it cannot calculate authoritative numbers, overwrite results, invent assumptions, assert occurrence or change forecasts.
- [ ] Explain changed assumptions, affected KPIs, conditional financial implications and analyst questions. Keep public context labeled and sourced; never describe the synthetic scenario as actual HCA/Tenet operations.
- [ ] Provide session-only scenario decisions: Reviewed — retain baseline; Request further investigation; Mark for forecast-assumption review. These are not causal confirmation and do not update any approved forecast.
- [ ] Bind commentary and review to the exact calculation revision. Editing assumptions invalidates prior review; reset/session end discards state. No browser persistence, database or authentication.
- [ ] Reuse compatible historical Phase 4 guard/fallback patterns after inspection, but introduce only the narrow scenario contract needed. Do not pass hypothetical results as historical actuals or require recovery of unrelated investigation UI for this ticket.

## Tests

- [ ] Check current-result numeric fidelity, conditional language, mode disclosure, source attribution and no unapproved state mutation.
- [ ] Test changed/multiple assumptions and invalid/stale results so old commentary cannot explain new numbers.
- [ ] Test each scenario review action, reset/session isolation and review invalidation after input changes.
- [ ] Browser-check the visible distinction among calculations, fallback narration and human decision; run without live credentials.

## Demo relevance

Completes the primary benchmark → baseline → one-driver change → impact → interpretation → analyst-review vertical slice.

## Requirement coverage

A06–A07, A12–A15.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Implementation has not started.


### Implementation clarification

Approved addition: Executive Summary consumes the exact shared ScenarioResult. Four KPI cards (visits, revenue, contribution margin, operating income), a monthly impact section, comparison and expense detail, commentary and review form the page structure. Ticket 5 adds charts within these stable sections. No waterfall, donut, operating-margin derivation or graph calculation is introduced in Ticket 3. Calculation engine remains unchanged.

Research: W3C APG tabs pattern (https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) informs keyboard/ARIA navigation. Inspected historical `40e4829:provider_fpa/narrative.py`: frozen structured input/output, deterministic formatter, result-bound numeric context and explicit human-review boundaries. Adapt these patterns to a narrow scenario contract; do not reuse investigation actual/comparator labels or restore unrelated historical UI.

Approved test seams: commentary from validated current result; revision-bound session review actions; synchronized browser model/summary interaction. Fallback accepts no external generated text and has no financial-write capability. Public benchmark attribution remains separate and source-linked; fallback commentary cites its synthetic baseline identity and result paths only.
