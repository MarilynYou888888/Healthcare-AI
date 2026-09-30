# 04: Reusable Product Flow & V2 Validation

Status: needs-triage
Approval: Ticket scope and publication approved by the user. Implementation is NOT authorized; stop for review after publication.
Blocked by: 03 — Custom Benchmarks + Zero-Token FP&A Commentary; transitively integrates completed tickets 01 and 02.
Specification: Approved narrow V2 specification, including the fully free product and events-only-state clarifications.

## What to build

A first-time Provider FP&A Analyst can complete the full local upload-to-analysis workflow, export a trustworthy summary, clear their data, and return to the preserved V1 demo. Deliver the coherent product flow, documentation/disclosures, acceptance evidence, and recruiting rehearsal.

## Acceptance criteria

- [ ] The landing experience clearly separates **Explore Demo** and **Use My Data**. Demo and uploaded states never silently mix, and no source-code editing is required for the user journey.
- [ ] Explore Demo retains HCA/Tenet public context, the synthetic planning baseline, and C01–C10 without requiring uploads.
- [ ] Use My Data exposes the complete guided import and optional downloadable sample/template workbook from Ticket 1. The template remains an onboarding aid; ordinary differently named analyst files work through mapping.
- [ ] Clear Uploaded Data removes session datasets, original/normalized previews, mappings, drafts, notes, results, and decisions; cancels pending workers/requests; revokes download references; and returns to the landing page. Late responses cannot restore cleared data. Built-in files are untouched.
- [ ] Reset Scenario affects only the selected draft/review state and remains clearly separate from Clear Uploaded Data. Refresh/tab closure ends the upload session as disclosed; downloaded exports are not claimed to be deleted.
- [ ] Scenario-only data enables Scenario Model/Executive Summary; Actual vs Forecast-only data enables Variance Investigation. Missing events and missing benchmarks do not block supported workflows. Events-only and benchmark-only states explain which analytical data is missing.
- [ ] **Operating Events / Evidence alone does not create a variance investigation.** When events exist but no Actual vs Forecast dataset is available, show: “Operating evidence is available, but Actual vs Forecast data is required to start a variance investigation.” Do not fabricate a variance, comparator, or investigation target from event data alone. Apply this availability check to the selected entity/period as well as the whole session.
- [ ] Export Scenario Summary as a lightweight CSV containing entity, period, scenario/currency/revision, baseline/scenario assumptions, outputs, changes, percentages or unavailable reasons, automated commentary, separately labeled Analyst Note when present, and data-source disclosure.
- [ ] Export uses the same current valid result as the screen, prevents stale-result export, quotes fields correctly, and protects textual cells from spreadsheet-formula injection without corrupting genuine numeric values. Downloads do not create server-side report files.
- [ ] README, user disclosures, examples, domain/decision documentation affected by the approved V2 contract changes, and recruiting instructions consistently explain the free, local, session-scoped product and its limits. Distinguish browser-memory uploads from request-local loopback investigation processing.
- [ ] Position Automated FP&A Commentary as complete deterministic functionality: zero LLM tokens, zero keys, zero paid APIs, zero external AI-provider account setup, and no paid cloud or external AI dependency. A local open-source generative experiment remains optional and outside V2 if mentioned at all.
- [ ] The full acceptance demonstration succeeds without developer assistance, external networking, or AI credentials. All V1 regression tests and the C01–C10 expected-answer evaluation remain passing.

## Tests and validation

- End-to-end browser flow: landing → own-file upload or optional sample → mapping → validation/preview → confirmation → entity/period selection → scenario edit → summary/commentary → imported variance review → export → reset/clear → Explore Demo.
- Partial-state matrix includes planning-only, performance-only, events-only, benchmark-only, missing events, no benchmark, and entity/period selections lacking performance rows. Assert events-only data cannot create a target or variance request.
- Verify Clear Uploaded Data versus Reset Scenario, cancelled work, delayed-response isolation, refresh behavior, memory-only session state, and immutable built-in files.
- Reconcile export values/commentary with the current shared result; test undefined percentages, stale drafts, CSV quoting, and formula-safe text.
- Verify no persistent upload storage, payload logging, external network requests, AI-provider accounts/keys, or inference charges are required.
- Run the complete relevant V1/V2 suite, existing browser regression checks, and C01–C10 evaluator; retain validation evidence and rehearse the final recruiting flow. Earlier tickets must already have their own tests—this is integration and regression closure, not deferred testing.

## Demo relevance

Use the clearly labeled synthetic sample workbook to select Nashville Specialty Clinic, August 2026, map “FTE Count,” “Work Days,” and “Rev / Visit,” confirm valid inputs, and change FTE 4.0 → 3.5. Show all dependent outputs, Executive Summary, and deterministic commentary updating. Open the imported performance sheet's insufficient-evidence variance and retain Unresolved. Export, clear the session, and demonstrate that Explore Demo still works. Include a brief events-only example showing the explicit Actual vs Forecast requirement.

## Boundaries and completion

No authentication, databases, PHI/employee PII/EHR ingestion, RAG, enterprise reporting infrastructure, automatic forecasts, paid AI services, or generative layer. The existing deterministic financial engine remains authoritative, with no import/commentary/export formula duplication. This completes the four approved outcome tickets; do not create additional low-level tickets.

## Comments

The user approved publication of exactly four tickets in dependency order 1 → 2 → 3 → 4 and explicitly required the events-only clarification. Publication does not authorize implementation. The holding status preserves that review gate and does not indicate unresolved scope.
