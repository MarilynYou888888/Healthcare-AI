# 01: Self-Service Data Import & Validation

Status: needs-triage
Approval: Ticket 1 implementation authorized by the user and completed. Awaiting user review; Tickets 2–4 are not authorized to start.
Blocked by: None. Completion: implemented and validated; stopped for user review.
Specification: Approved narrow V2 specification, including the fully free product clarification and optional-template onboarding clarification.

## What to build

A Provider FP&A Analyst can upload an ordinary spreadsheet, map its columns, resolve validation issues, and explicitly confirm a trustworthy session-local dataset without editing source code. This is one complete, visible import outcome, not separate parser, schema, and UI tickets.

## Acceptance criteria

- [x] CSV and XLSX work through visible Upload → Identify dataset type → Map columns → Validate → Preview normalized data → Confirm import steps, followed by access to whichever analytical workflows are available.
- [x] Excel users can preview sheets, select the header row, and assign multiple sheets to dataset roles. Different files may supply different roles. Unsupported table layouts produce understandable guidance rather than guessed structure.
- [x] Planning Assumptions, Actual vs Forecast, Operating Events, and Custom Benchmark use the approved normalized schemas and a shared import workflow. Ticket 3 adds benchmark context selection/display using this importer.
- [x] An explicit deterministic alias dictionary suggests Uploaded Column → Expected FP&A Field mappings. Users can correct suggestions, see required versus optional fields, and resolve competing mappings. Ambiguous meanings such as provider headcount versus FTE require confirmation.
- [x] Required values, numeric types/ranges, dates/months, percentage encodings, negative-value rules, duplicate keys, supported units, currency consistency, and cross-role entity relationships follow the approved specification. Missing financial inputs are never silently inferred or filled.
- [x] Errors identify the source row/cell, column, problem, and suggested correction. ERROR blocks import; WARNING requires acknowledgment; INFO explains normalization. No stack traces appear in the user flow.
- [x] Original and normalized previews show every transformation and any explicitly entered constants. Changing a mapping invalidates subsequent validation/approval. Import requires explicit confirmation.
- [x] Confirmed roles publish atomically. Failed replacements preserve prior confirmed data; replacement is explicit and invalidates dependent results/reviews. Invalid rows are never silently dropped.
- [x] Raw files, previews, mappings, and confirmed datasets remain in browser/worker memory. Refresh or tab closure ends the session. No persistent browser storage, upload directory, database, external transmission, or analytics is introduced.
- [x] The upload notice states: “Use aggregated, de-identified financial and operational data only. Do not upload PHI or other sensitive personal information.” The UI also explains session loss and prohibits patient/employee identifiers as specified, without claiming to perform de-identification.
- [x] Parsing obeys the approved byte/expanded-content/row/cell/time limits, supports cancellation, and handles malformed/encrypted/macro-enabled files clearly. Formulas, macros, and external links are never executed; cached formula values follow the explicit warning policy.
- [x] Provide an optional downloadable sample/template XLSX workbook with simple **Planning Assumptions**, **Actual vs Forecast**, and **Operating Events** sheets. Label examples synthetic and supply short in-product guidance so a first-time user can understand the structure without reading documentation. This is an onboarding aid, never an input requirement.
- [x] Users can still upload their own differently named CSV/XLSX files and differently named columns using mapping. No template filename, sheet-name, or exact-header requirement is imposed.
- [x] The importer is reachable from the existing application without disrupting V1. Ticket 4 completes the landing experience. Include examples suitable for the later Nashville/August acceptance demo with all required planning assumptions, not only the three highlighted mappings.

## Tests and validation

- Browser workflow: select CSV/XLSX, choose sheets/roles, correct aliases, review issues and normalization, and explicitly confirm valid data.
- Contract cases: quoting/BOM/malformed CSV; XLSX date systems and percent cells; alias collisions; required fields; numeric bounds; blank versus zero; ambiguous dates/locales/scales; sign policies; duplicates; units/currencies; entity links; cached formulas; cancellation and resource limits.
- Verify failed replacements preserve confirmed data and refresh leaves no retained uploads or persistent storage.
- Download and import the synthetic template. Separately import a non-template workbook with alternate filename, sheet names, and headers to prove the template is optional.
- Exercise relevant V1 loading/browser regressions. Reuse the existing calculator only when checking derived planning range; no duplicated financial arithmetic in import code.

## Demo relevance

Download the optional example or select an analyst's own workbook, map “FTE Count,” “Work Days,” and “Rev / Visit,” inspect original versus normalized values, resolve a readable validation issue, and confirm the import.

## Boundaries and handoff

Preserve the V1 demo, deterministic engines, and provenance boundaries. No authentication, databases, PHI/EHR support, RAG, AI-provider accounts, keys, paid APIs, LLM tokens, or external AI dependencies. All approved specification constraints apply. Ticket 2 consumes the confirmed immutable datasets; do not split this ticket into low-level engineering tickets.

## Comments

The user approved publication of exactly four tickets in dependency order 1 → 2 → 3 → 4. The optional workbook is required as an available onboarding aid; using it is optional for the analyst. Publication does not authorize implementation. The holding status preserves that review gate and does not indicate unresolved scope.

2026-09-21 implementation review: Ticket 1 complete. 25 import tests and the full 141-test suite pass. Browser rehearsal covers all three optional sample sheets, corrected mappings, normalization, explicit confirmation, failed replacement protection, session loss, and desktop/mobile views. Two-axis code review findings were reproduced and fixed; focused rechecks found no remaining blockers. V1 formulas and benchmarks remain unchanged. See the Ticket 1 validation report for screenshots, scope boundaries, and file manifest. Do not start Ticket 2 without user authorization.
