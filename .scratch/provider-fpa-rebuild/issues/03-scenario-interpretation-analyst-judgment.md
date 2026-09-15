# 03: Scenario Interpretation + Analyst Judgment

Status: ready-for-human
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: Ticket 3 implemented and verified. Paused for user review; do not begin Ticket 4.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Read an explanation of the current scenario and record an analyst decision without changing financial calculations or an approved forecast.

## Dependencies

Blocked by: 02 — Change One Driver and See Financial Impact

## Acceptance criteria

- [x] Visibly distinguish three responsibilities: deterministic financial calculations; offline/demo fallback narrative commentary; human analyst judgment.
- [x] Label narrative explicitly as “Offline demo — deterministic fallback commentary; no live LLM used.” The UI, recording and portfolio wording must not imply that deterministic fallback text is live AI generation. No API key is required.
- [x] Commentary consumes the validated current ScenarioResult and formats its computed values; it cannot calculate authoritative numbers, overwrite results, invent assumptions, assert occurrence or change forecasts.
- [x] Explain changed assumptions, affected KPIs, conditional financial implications and analyst questions. Keep public context labeled and sourced; never describe the synthetic scenario as actual HCA/Tenet operations.
- [x] Provide session-only scenario decisions: Reviewed — retain baseline; Request further investigation; Mark for forecast-assumption review. These are not causal confirmation and do not update any approved forecast.
- [x] Bind commentary and review to the exact calculation revision. Editing assumptions invalidates prior review; reset/session end discards state. No browser persistence, database or authentication.
- [x] Reuse compatible historical Phase 4 guard/fallback patterns after inspection, but introduce only the narrow scenario contract needed. Do not pass hypothetical results as historical actuals or require recovery of unrelated investigation UI for this ticket.

## Tests

- [x] Check current-result numeric fidelity, conditional language, mode disclosure, source attribution and no unapproved state mutation.
- [x] Test changed/multiple assumptions and invalid/stale results so old commentary cannot explain new numbers.
- [x] Test each scenario review action, reset/session isolation and review invalidation after input changes.
- [x] Browser-check the visible distinction among calculations, fallback narration and human decision; run without live credentials.

## Demo relevance

Completes the primary benchmark → baseline → one-driver change → impact → interpretation → analyst-review vertical slice.

## Requirement coverage

A06–A07, A12–A15.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Implementation was subsequently authorized one ticket at a time.


### Implementation clarification

Approved addition: Executive Summary consumes the exact shared ScenarioResult. Four KPI cards (visits, revenue, contribution margin, operating income), a monthly impact section, comparison and expense detail, commentary and review form the page structure. Ticket 5 adds charts within these stable sections. No waterfall, donut, operating-margin derivation or graph calculation is introduced in Ticket 3. Calculation engine remains unchanged.

Research: W3C APG tabs pattern (https://www.w3.org/WAI/ARIA/apg/patterns/tabs/) informs keyboard/ARIA navigation. Inspected historical `40e4829:provider_fpa/narrative.py`: frozen structured input/output, deterministic formatter, result-bound numeric context and explicit human-review boundaries. Adapt these patterns to a narrow scenario contract; do not reuse investigation actual/comparator labels or restore unrelated historical UI.

Approved test seams: commentary from validated current result; revision-bound session review actions; synchronized browser model/summary interaction. Fallback accepts no external generated text and has no financial-write capability. Public benchmark attribution remains separate and source-linked; fallback commentary cites its synthetic baseline identity and result paths only.


### Completion — 2026-09-15

All acceptance criteria verified. Executive Summary opens first, with four KPI cards, a driver summary, operating-income impact, comparison/expense sections, explicitly disclosed offline commentary and three session-only analyst decisions. Accessible tab navigation preserves model/review state. Invalid drafts label numerical views stale, remove commentary and disable review; any edit/reset invalidates prior review. Reload discards the session.

Ticket 5 mounts are stable and documented in README: income-bridge-chart, expense-mix-chart, scenario-comparison-chart, summary-model-logic. Hidden empty chart mounts do not display mock visuals. Renderers consume the same ScenarioResult; no chart-derived measures or duplicated financial calculations were introduced.

Validation: 25 full-suite tests passed. Ticket 3 Chrome checks passed (keyboard navigation, matching table/KPI values and revision, offline operation, analyst decisions/invalidation, mobile layout). Existing Ticket 1–2 browser checks passed with maximum measured input-to-painted-frame latency 34.3 ms across ten edits and zero recalculation requests. Python compile and git whitespace checks passed. No static type checker is configured. Desktop/mobile screenshots inspected.

Review correction: offsetting FTE/daily-capacity edits now describe no net output change rather than inventing changed cost assumptions. Primary FTE commentary explains partial variable-cost offset only when existing computed signs and unchanged fixed costs support it. Regression tests cover both. See [review](../ticket-03-review.md).

Files changed: web/executive.js, web/interpretation.js, web/index.html, web/app.js, web/style.css; provider_fpa/web.py asset registration; tests/test_interpretation.py and shared browser test harness; scripts/check_interpretation.py and existing browser check navigation; README and ticket/review records.

Deviations: none from approved business formulas. web/scenario.js, public extracts and synthetic baseline remain unchanged (verified by Git diff). Historical Phase 4 patterns were adapted without restoring incompatible investigation contracts. No API keys, live LLM, persistence, production infrastructure or Ticket 4 work. Dark summary presentation is a foundation; final charts and cross-page styling remain Ticket 5.

Local demo: http://127.0.0.1:8501/. Refresh Chrome, open Scenario Model, edit FTE 4.0 to 3.5, return to Executive Summary, inspect commentary, and record an analyst decision.
