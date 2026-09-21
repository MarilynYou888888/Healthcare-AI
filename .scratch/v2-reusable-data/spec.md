# Healthcare Provider FP&A Copilot — narrow V2 specification

Status: needs-triage
Approval: PROPOSED — awaiting explicit user approval; not ready for implementation or ticket creation.
Date: 2026-09-21
V1 reference: closed commit `843c554`; pre-spec snapshot `ee35bfb`.

## Problem Statement

V1 demonstrates deterministic planning and evidence-aware variance review with fixed public benchmarks and synthetic Clinic-Month inputs. A Provider FP&A Analyst cannot use an ordinary spreadsheet without adapting it to developer-facing contracts. V2 makes those existing workflows reusable with aggregated user data and concise professional commentary, without code editing, accounts, paid APIs, or LLM tokens.

The governing sequence remains deterministic financial calculations → automated interpretation → human analyst judgment. Reusability does not establish causal evidence, comparability, or forecast approval.

## Solution

### Proposed experience

The landing page offers **Explore Demo** and **Use My Data**. Explore Demo preserves HCA/Tenet public context, the synthetic planning baseline, and C01–C10. Use My Data presents seven visible steps: Upload → Identify dataset type → Map columns → Validate → Preview normalized data → Confirm import → Open available workflows.

Show before file selection: **“Use aggregated, de-identified financial and operational data only. Do not upload PHI or other sensitive personal information.”**

Accept CSV and XLSX containing one rectangular table per selected sheet, with a user-selectable header row. List Excel sheets and preview each before assigning Planning, Actual vs Forecast, Operating Events, or Custom Benchmark roles. Multiple sheets and successive files may supply different roles. Do not require all roles in one file. Skip unselected sheets; identify hidden sheets explicitly. Totals, merged data cells, and multiple separate tables within a sheet require correction or a clean exported table; do not silently interpret them.

Mapping shows Uploaded Column → Expected FP&A Field, required/optional status, sample values, and explanatory units. Deterministic aliases suggest mappings; the analyst confirms them. Missing required values block confirmation. Optional columns can remain unmapped, and discarded columns are listed. Users can go back without losing their draft; changing mapping invalidates subsequent validation and preview approval.

Confirm import atomically publishes only the selected, valid dataset roles. A failed replacement leaves the prior confirmed data intact. Other valid roles may be imported by explicitly deselecting a failing role; never silently skip bad rows. Replacing an existing role requires a clear replacement confirmation and invalidates dependent scenarios and reviews. V2 replaces whole roles rather than merging overlapping versions.

Entity, Calendar Month, and uploaded scenario-name selectors initialize one planning row. Scenario edits create a separate draft; the uploaded baseline stays immutable. Switching selection starts from that row's baseline and warns before discarding an edited scenario. V2 does not save a library of scenario drafts.

Scenario-only data enables Scenario Model and Executive Summary. Performance-only data enables Variance Investigation. Missing events leave evidence-dependent conclusions unresolved. Missing benchmarks never block analysis. Events-only or benchmark-only imports may be previewed, with a clear explanation that analytical inputs are still needed.

### Established approach and research basis

The industry-standard pattern relevant here is a staged import boundary: preserve raw cells, map into a canonical schema, validate types/constraints/keys, show corrections, then commit an immutable analytical snapshot. File parsing does not establish business meaning. Frictionless Table Schema documents physical versus logical values and explicit types, constraints, primary keys, and foreign keys. V2 adopts these concepts without adding a data-platform framework. [Table Schema](https://specs.frictionlessdata.io/table-schema/)

Browser-local spreadsheet reading is supported by SheetJS; Papa Parse supports local CSV parsing, parse errors, and formula-safe export. Proposed dependency choice: locally bundled, pinned open-source SheetJS Community Edition for XLSX and Papa Parse for CSV, with licenses retained. No CDN or network download at runtime. Pin and verify supported versions during approved implementation. [SheetJS local files](https://docs.sheetjs.com/docs/demos/local/file/), [Papa Parse documentation](https://www.papaparse.com/docs)

Spreadsheet byte size alone does not bound memory use; library documentation and repository issues describe large-workbook limits. Therefore impose explicit byte, expanded-data, cell, and time limits rather than promising arbitrary workbook support. [SheetJS troubleshooting](https://docs.sheetjs.com/docs/miscellany/errors/), [repository issue 2908](https://git.sheetjs.com/sheetjs/sheetjs/issues/2908)

The durable solution is a shared normalized import boundary and adapters into the existing engines. Its cost is a parser dependency, validation/mapping UX, a request-local investigation adapter, and provenance-aware views. A direct spreadsheet-to-view shortcut would leave each workflow interpreting inputs differently and is not proposed.

## User Stories

1. As a Provider FP&A Analyst, I want a working example before importing, so that I can learn the workflow.
2. As an analyst, I want CSV/XLSX selection without code, so that I can use ordinary analyst files.
3. As an analyst, I want sheet previews and role assignment, so that one workbook can supply several datasets.
4. As an analyst, I want familiar headers suggested and editable, so that I need not rename every column.
5. As an analyst, I want field definitions and units, so that I do not mistake headcount for FTE or daily clinic visits for visits per provider-day.
6. As an analyst, I want required-field errors with row, column, and correction guidance, so that I can repair my file.
7. As an analyst, I want explicit percentage, date, currency, and numeric-format choices, so that ambiguous values are not guessed.
8. As an analyst, I want original and normalized previews plus every transformation, so that I can approve exactly what enters the model.
9. As an analyst, I want duplicate and entity-link checks, so that results do not double count or mix entities.
10. As an analyst, I want multiple entities, months, and named planning rows, so that I can reuse one import across analyses.
11. As an analyst, I want a protected baseline and Reset Scenario, so that experiments do not change source data.
12. As an analyst, I want every dependent output and chart to update from one result, so that Executive Summary reconciles to Scenario Model.
13. As an analyst, I want performance-only imports to work, so that scenario assumptions are not a prerequisite for variance review.
14. As an analyst, I want review-rule reasons displayed, so that materiality is transparent.
15. As an analyst, I want traceable operating evidence, so that I can distinguish observed facts from supported explanations.
16. As an analyst, I want insufficient evidence to remain Unresolved, so that the tool does not fabricate causes.
17. As an analyst, I want explicit human confirmation separate from notes, so that free text cannot approve a cause.
18. As an analyst, I want public, uploaded, and synthetic data labeled distinctly, so that their provenance is clear.
19. As an analyst, I want optional custom benchmarks and No Benchmark, so that context does not become a required model input.
20. As an analyst, I want concise professional deterministic commentary, so that no API key or token spend is needed.
21. As an analyst, I want commentary tied to the current result and evidence state, so that stale or unsupported conclusions are withheld.
22. As an analyst, I want a separate Analyst Note, so that I can record context without changing system evidence.
23. As an analyst, I want a downloadable scenario summary, so that I can share assumptions, outputs, changes, and disclosures.
24. As an analyst, I want Clear Uploaded Data, so that I can end the local session without changing built-in examples.
25. As an analyst, I want usable empty and partial states, so that unavailable datasets do not block unrelated workflows.
26. As an analyst, I want predictable local processing limits and readable failures, so that a malformed workbook does not destroy my current work.

## Implementation Decisions

All decisions below are proposals for approval. No V1 source, contracts, ADRs, or fixtures are changed by this specification.

### 1. Inspected V1 architecture and exact reuse boundary

V1 uses native browser JavaScript modules served by a lightweight Python HTTP server. The sole scenario calculator is browser-side Decimal arithmetic; Python loads its synthetic baseline but does not recalculate scenarios. Python owns the investigation arithmetic, review rules, causal assessment, timing, and evidence transitions. Browser charts consume a shared scenario presentation. The investigation web wrapper currently selects synthetic cases. Commentary already runs deterministically, although an injectable OpenAI narrative adapter exists outside the required UI flow.

| Existing component | Reuse unchanged | Required V2 adaptation |
|---|---|---|
| Scenario dependency graph and `calculate` arithmetic | All nine assumptions and eight output formulas; Decimal precision and rounding | None to financial formulas |
| Scenario `change` calculation | Amount, percent, and undefined-percent behavior | None |
| Scenario store protections | Clone/freeze baseline, revisions, invalid-draft/last-valid behavior, reset semantics | Accept validated uploaded baseline envelope and selection lifecycle |
| Synthetic baseline loader and built-in JSON | Entire demo loader and fixture | New upload adapter bypasses demo-only loader |
| Public HCA/Tenet loader, normalized files, source lineage | Entire built-in data path | Add a separate custom-reference path; never impersonate verified public records |
| Python variance arithmetic and review evaluator | Existing functions and threshold semantics | New normalized-input adapter and user review settings |
| Python core investigation orchestration | Existing `Datasets` → `investigate` path | Map entity-month inputs to its clinic-month interface; conservative evidence gating |
| Driver-role selection, evidence transitions, causal boundaries | Existing supported/confirmed distinction and no arbitrary primary-driver tie-break | Imported events need typed semantics; see evidence restrictions below |
| V1 synthetic driver/timing rules and C01–C10 | Existing behavior and expected answers | Do not broaden fixture rules by guessing new aliases |
| Executive Summary, charts, trace | Existing workflow, chart geometry, reconciliation relationships | Provenance, currency, lifecycle, result fields; cannot claim entire modules are unchanged |
| Interpretation and narrative | Result-bound formatter pattern and guarded human review | New concise components and current reviewed-state commentary |
| Investigation web wrapper | Existing demo endpoints and case selection | New stateless local endpoint, uploaded identity, snapshot-bound review |

V1 closeout records 116 passing tests and 10/10 investigation cases with 70/70 evaluated dimensions. These are historical inspection findings, not newly rerun results.

### 2. Canonical datasets and mapping

Preserve these user-facing normalized fields:

| Role | Fields |
|---|---|
| Planning — required | `entity_id`, `entity_name`, `period`, `provider_fte`, `operating_days`, `visits_per_provider_day`, `utilization_rate`, `net_revenue_per_visit`, `variable_labor_cost_per_visit`, `variable_supply_cost_per_visit`, `fixed_operating_expense`, `reimbursement_factor` |
| Planning — optional | `market`, `specialty`, `business_unit`, `scenario_name`, `currency`, `source`, `notes` |
| Actual vs Forecast | `entity_id`, `entity_name`, `period`, `metric_id`, `metric_name`, `actual_value`, `forecast_value`, `unit`, `currency`, `source` |
| Operating Events | `entity_id`, `period`, `event_type`, `start_date`, `end_date`, `description`, `observed_value`, `unit`, `source`, `reported_at` |
| Custom Benchmark | `company`, `period`, `business_segment`, `metric_id`, `metric_name`, `value`, `unit`, `source`, `notes`; optional `source_url` |

For performance, identity, metric, actual/forecast values, unit, and lineage must be populated; currency is required for monetary metrics and blank for nonmonetary metrics. For events, identity, period, type, start date, description, and source are required. End date, observed value/unit, and reported-at may be unknown; a supplied observed value requires its unit. Benchmark notes may be empty; other nonoptional benchmark fields must be populated. Monetary benchmark units must identify currency, e.g. `USD`, since that schema has no currency column.

Required normalized fields need not all be spreadsheet columns. Explicit setup choices can supply an entity, month, currency, metric, or constant assumption, but every constant is labeled analyst-entered and shown in preview. Never silently default a financial input, including utilization or reimbursement factor. A missing entity ID can be created as a disclosed session identifier after the analyst confirms the name-to-identity table; cross-file name matches require confirmation. Same-named entities are never silently merged. Metric names can come from the explicitly selected registry. Missing source text can use the visible file/sheet/row locator, not an invented external source. Missing scenario name becomes the disclosed metadata label “Uploaded baseline.”

Planning adapter renames only: `operating_days` → `clinic_days`; `utilization_rate` → `utilization`; `variable_labor_cost_per_visit` → `labor_per_visit`; `variable_supply_cost_per_visit` → `supplies_per_visit`; `fixed_operating_expense` → `fixed_expense`; `period` → `month`. Other financial fields retain their names. No arithmetic belongs in this adapter beyond explicit input-unit normalization.

Alias dictionary includes `fte`, `provider fte`, `fte count`, `provider count`; `clinic days`, `operating days`, `work days`; `rev per visit`, `revenue per visit`, `net revenue per encounter`, `rev / visit`. Normalize case, spacing, and punctuation deterministically. Suggest `provider count` only with a warning to confirm FTE rather than headcount. Likewise “Visits Per Day” requires confirmation of per-provider units. One uploaded column cannot satisfy unrelated required fields; competing suggestions require selection. Column mapping cannot infer missing metrics.

Performance is long-form: one row per entity/month/metric. V2 does not automatically unpivot arbitrary cross-tabs. Provide a downloadable example and a clear long-form explanation; a single-metric table may use an explicit metric selection without adding a column.

### 3. Validation contract

- **ERROR:** blocks the selected role's import. **WARNING:** requires review acknowledgment. **INFO:** explains unambiguous normalization. Each issue records original row/cell, source column, normalized field, original value, problem, and correction. Never display Python exceptions or stack traces.
- Preserve original values alongside normalized decimal strings and transformation records. No binary floating-point financial arithmetic. Blank is not zero. Reject NaN, infinity, malformed numeric values, and inputs outside existing calculator limits; validate derived model range before confirming planning rows.
- Provider FTE and visits per provider-day ≥ 0; all planning revenue/cost inputs ≥ 0. Uploaded operating days must be whole days, > 0, and no greater than days in the selected month. Reimbursement factor > 0. These stricter imported-row checks do not change V1's existing scenario ability to test zero operating days or zero reimbursement.
- Utilization normalizes to [0,1]. The analyst explicitly selects fraction or percentage-point encoding for unmarked numeric columns. `90` in percentage mode becomes `0.90`, with a reviewed normalization warning; `90%` is unambiguous. Excel numeric cells with percent formatting use the stored fractional value, not another division by 100. Mixed ambiguous scales block import. Apply the same discipline to benchmark ratios: `0.42` with a “percent” label must be explicitly resolved as fraction encoding or 0.42 percentage points.
- Normalize months to `YYYY-MM`. Accept explicit month strings, chosen date formats, and Excel serial dates using workbook date-system metadata. Ambiguous day/month dates require a format choice. Display any date-to-month conversion. Planning supports Calendar Months, not fiscal weeks or annual allocations; benchmark `FY2026` remains an annual context label.
- A selected decimal/group separator convention governs numeric strings. No locale guessing for ambiguous amounts. Parenthesized negative values may normalize with disclosure where signed values are permitted.
- Metric registry specifies variance type, compatible units, sign policy, and favorable direction. Visits/FTE/counts cannot be negative. Operating income may be signed; net revenue and expense adjustments may be signed with a warning that the submitted sign convention must be positive revenue/positive expense. A credit-sign ledger export must be corrected or explicitly normalized before import; never silently flip signs. Undefined direction remains neutral, never a guessed favorable result.
- Proposed currency scope: one explicitly selected ISO currency per confirmed user-data session; no FX conversion. Monetary rows must agree. `$` alone does not establish USD. Explicit USD formatting may suggest USD, but the analyst confirms the currency. Public USD references stay separate; cross-currency monetary comparisons are disabled. Generic scenario arithmetic is currency-independent; labels/formatters must cease hard-coding USD. V1 USD-only causal mechanisms remain unavailable for other currencies rather than relabeling them.
- Keys: planning `(entity_id, period, scenario_name)`; performance `(entity_id, period, metric_id)`; benchmark `(company, period, business_segment, metric_id)`. Exact and conflicting duplicates block; do not sum, keep-first, or deduplicate silently. Repeated event records are flagged and block until corrected; different events for one entity-month are allowed.
- Cross-role entity IDs/names must agree. Events must reference known analytical entities by the time investigation is run. Event start/end must be valid and ordered; event period must overlap its interval. Unknown end date means unknown, not recovered. User-entered active intervals for the internal clinic interface are not required: the adapter labels imported month coverage as dataset coverage, not actual clinic opening/closure dates.
- Proposed local limits: 10 MiB per file, 50,000 selected rows total, 100 columns per sheet, 500,000 populated cells, 100 MiB expanded XLSX content, and a cancellable 15-second parse budget. Validate compressed-container expansion before unrestricted workbook parsing, and parse in a worker so cancellation remains responsive. Reject oversized/malformed, encrypted, macro-enabled, or mislabeled files clearly. These are product limits, not promises about arbitrary spreadsheets.
- Do not execute formulas, macros, or external workbook links. Cached formula values may be imported only after a warning/acknowledgment that freshness is unverified; missing cached values require exporting values first. Render all user text as text. Reject clearly prohibited patient/employee identifier columns and explain removal before retrying; this guard is not a PHI detector or de-identification service.

### 4. Session-local architecture and lifecycle

Raw CSV/XLSX bytes, previews, mappings, confirmed datasets, scenario drafts, notes, and human decisions reside in page/worker memory. No localStorage, sessionStorage, IndexedDB, upload directory, database, analytics, or server-side session cache. Browser refresh or tab closure ends the session; disclose this before import. Export is the only intentional user-data file write, initiated by the analyst.

The existing Python investigation engine cannot execute natively in the browser. Reuse it through a **stateless loopback-only request**: send the necessary normalized selected-entity records/history, related events, review settings, and snapshot identity to the local Python server. Raw workbooks are never sent. The server validates the payload, builds immutable in-memory `Datasets`, calculates and formats the result, and releases request references after responding. No upload payload or result logging, file-backed cache, temporary upload files, external calls, or background retention. This is local-process transmission, not an external API. State this accurately in the upload disclosure.

Bind user-data mode to loopback; validate host/origin and JSON requests, cap request bodies, use no-store responses, and restrict connections to self. Do not offer remote-hosted upload mode in V2. Bundle all dependencies locally. A new request recomputes review state against the submitted immutable dataset fingerprint and decisions; browser memory owns continuity. Reject stale review snapshots. Clear cancels workers/requests, increments a session generation, drops all dataset/result/decision/note references, revokes download object URLs, and returns to the landing page. Late responses from an old generation cannot repopulate the UI. Built-in files remain untouched. Clearing means application-reference removal, not a promise to securely erase OS memory or downloaded exports.

Reset Scenario affects only the selected scenario draft and its review decision. Clear Uploaded Data affects the entire user-data session. Switching to Explore Demo uses a separate demo state with visible provenance and never mixes inputs.

### 5. Scenario and Executive Summary contracts

Allow validated planning provenance `user_uploaded` in the scenario result envelope while continuing to reject public benchmark inputs. Preserve immutable baseline/draft separation and result revision checks. Add entity ID/name, normalized period, scenario name, currency, upload snapshot identity, and source lineage. Reimporting or selecting a baseline creates a new identity; prior review decisions do not transfer.

The dependency equations remain exactly V1: capacity = FTE × operating days × visits per provider-day; visits = capacity × utilization; revenue = visits × net revenue per visit × reimbursement; labor/supplies = visits × each variable cost; contribution = revenue − variable expense; operating income = contribution − fixed expense. No hospital inpatient/case-mix/bed-capacity model is implied. Hospitals may use this tool only for a visit-based aggregate unit that fits these assumptions.

V1 currently derives margin, bridge, and expense shares in its shared presentation adapter. To satisfy the stricter V2 numeric-source requirement, move those existing derivations once into a versioned shared result-assembly layer alongside the existing calculator. Expose operating-margin baseline/scenario/change in percentage points, signed bridge contributions, expense shares, and computed offset amounts in `ScenarioResult`. This relocates existing financial derivations; it does not introduce a second model or change formulas. Charts, commentary, and export then only format the same result fields. Preserve V1 zero-revenue margin and nonpositive-baseline percent behavior. Retain Python variance-percentage conventions separately and label denominators; do not silently unify different V1 percentage policies.

Keep Expected Visits, Modeled Net Patient Revenue, Contribution Margin, Modeled Operating Income, Operating Margin, Operating Income Bridge, Baseline vs Scenario, Expense Mix, and Calculation Trace. Invalid drafts visibly retain stale last-valid charts but disable current commentary, export, and review until corrected.

### 6. Actual vs Forecast and evidence adaptation

The analyst confirms that selected months are closed and the comparator is the Latest Approved Forecast. V2 does not support budget, prior-year, multiple forecast versions, or open-month actuals under that label. Capture this as explicit import metadata, not inferred approval.

Split normalized performance rows into V1 financial/operational `Value` objects using an explicit registry. Map `VISITS` → `PATIENT_VISITS`, and `LABOR_EXPENSE` → `EXP_CLINICAL_LABOR` only when the analyst confirms clinical-labor scope; otherwise retain a generic labor metric without that mechanism. `PROVIDER_FTE` is **not** `PROVIDER_AVAILABLE_DAYS`. Support supply expense, operating expense, operating income, and other registered metrics for deterministic variance display; absent driver rules remain Unresolved. Add favorable-direction registry entries for these supported V2 metrics without fabricating causal rules.

The same performance schema can also contain the existing supporting metrics `NET_REVENUE_PER_VISIT`, `PROVIDER_AVAILABLE_DAYS`, `CLINIC_CLOSURE_DAYS`, `OVERTIME_HOURS`, and `COMMERCIAL_PAYER_MIX`. Their actual/forecast pairs and units must be supplied. Do not back-solve missing revenue-per-visit or availability from other data. Revenue explanation keeps V1's exact revenue/visits/rate reconciliation requirement; rounding mismatch is disclosed and unresolved, not silently repaired.

All proposed event names are accepted as reported evidence. Exact supported vocabulary may reach existing rules. `staffing_shortage` does not imply temporary vacancy; `reimbursement_change` does not prove a payer-contract change; overtime without a comparison is not an overtime variance. Ambiguous aliases require a specific semantic selection or remain context-only. An event's observed value/unit is retained as an observed fact, never treated as an actual/forecast pair.

Imported free-text descriptions and Analyst Notes are not rule inputs. In particular, do not reuse V1's fixture-specific extraction of a labor accrual amount from description text for uploads. Until a structured mechanism is explicitly supported, an accrual event is context/candidate evidence with an unresolved contribution. Do not generate synthetic prose to trigger V1 regex rules.

An event end date alone does not establish recovery or persistence. For imported events, timing stays Unresolved unless the analyst explicitly supplies structured timing evidence in the evidence-review UI: expected normalization month or persistence-through month with Source Reference. This is an optional validated evidence extension, not a new financial input or automatic causal confirmation. Feed those signals to the existing timing classifier. Show the existing next-three-month fallback horizon when an approved horizon is not supplied; optionally accept an explicit forecast-end month. Never infer “temporary” from a generic event ending or “structural” from provider departure alone.

Use existing review evaluation with user-visible, session-only per-metric absolute/percentage thresholds and always-review choices. Missing thresholds mean “No automatic materiality rule configured.” Selecting **Investigate this variance** records an explicit Analyst Override; do not reuse synthetic financial thresholds as user policy. Percent thresholds are normalized fractions at the Python boundary. Review selection never establishes a cause.

Evidence, system assessment, human decisions, and notes remain separate. Only Supported Drivers can become Analyst-Confirmed Causes under existing transition rules; unresolved drivers require evidence, not a confirm shortcut. Forecast approval and automatic forecast writes remain absent.

### 7. Custom benchmarks and provenance

Offer HCA Healthcare, Tenet Healthcare, Custom Benchmark, and No Benchmark. Default user-data mode to No Benchmark. HCA/Tenet retain **BUILT-IN PUBLIC — Public benchmark context**. User benchmarks retain **USER UPLOADED — Unverified external context**, even when a source name says “Public filing.” Demo assumptions and investigation fixtures retain **SYNTHETIC**.

Custom benchmark schema is deliberately lighter than the verified public-filing contract. Use a separate reference view model; do not invent filing hashes, audited definitions, URLs, or extraction locators. Show submitted company, segment, period, units, source, and notes. Optional source URLs are user-opened links only, never automatically fetched. Different scopes/periods are labeled, not aligned through annualization or implicit clinic comparability. No reference selection changes model assumptions, establishes target performance, or fills missing inputs.

### 8. Deterministic professional commentary

Visible name: **Automated FP&A Commentary**. Disclosure: **“Rule-based commentary from calculated results and recorded evidence. No LLM or external API is used.”** No model selection, key field, provider fallback, or invocation of the existing OpenAI adapter in V2 user-data paths.

Use two composers appropriate to the existing runtimes: browser scenario composer and local Python investigation composer. They share a documented statement/evidence contract, not a cross-language financial calculation engine. Each returns 3–5 sentences plus internal statement IDs, numeric source paths, result/snapshot revision, and provenance. Formatting may round/display a provided value, but cannot derive a new financial number, rank numeric contributions through hidden calculations, or classify evidence independently.

Reusable components: headline, changed-driver statement, operating-volume statement, financial-impact statement, expense-offset/fixed-cost statement, margin statement, evidence statement, and next-step statement. Deterministic priority selects concise nonrepetitive combinations. Detail tables retain all changed inputs when several cannot fit in five sentences. A no-change scenario gets a factual no-change narrative rather than invented impact.

Scenario rules cover increases/decreases, zero impact, multi-driver changes, revenue downside/upside, variable-cost offset/amplification, changed/unchanged fixed expense, and operating-margin movement when defined. State a single-driver modeled mechanism only when the dependency graph supports it. For multiple changes, say “the combined assumption changes”; never claim an uncomputed primary-driver attribution. Use result-provided signed bridge/offset values. Questions are selected from a finite approved assumption-review catalog, e.g. validating capacity or cost flexibility; they do not assert a staffing plan, recovery date, or forecast recommendation that lacks evidence.

Variance rules read the computed variance direction, primary/contributing roles, timing, evidence gaps, and current human decisions. Supported means supported, not confirmed. No sufficient evidence produces an explicit Unresolved sentence and a bounded request for operational context. A human confirmation updates only that snapshot's commentary; it does not update a forecast. Rejected drivers are excluded from supported explanations. All numbers come from the corresponding result, including any contribution estimate. Never substitute zeros for unavailable values.

Example shape, using placeholders rather than promised output values: “Provider FTE decreased from {baseline FTE} to {scenario FTE}, with modeled visits decreasing by {computed visits change}. Modeled revenue is {computed revenue change} below baseline. Lower variable expense provides a {computed offset} partial offset, resulting in {computed operating-income change} lower operating income; fixed expense is unchanged. Review whether the availability assumption should be reflected in the next forecast discussion.” Only select sentences whose predicates hold.

Analyst Note is displayed separately, scoped to the selected entity/month/scenario or investigation snapshot, retained only in memory, and limited to plain text. It is not ingested by the composer or promoted to evidence.

### 9. Lightweight export

Provide **Export Scenario Summary** as UTF-8 CSV for the selected valid result. Use a consistent row-based format containing section, field/metric, unit, baseline, scenario, change, change percent, and unavailable reason, with repeated entity/period/scenario/currency/revision metadata. Include all baseline/scenario assumptions, outputs, margin/bridge measures, automated commentary, separately labeled Analyst Note if present, and source disclosure. Percentage units must be explicit; undefined percentages remain blank with a reason. Values come from the same current result used by the screen. Escape textual spreadsheet-formula prefixes, quote fields correctly, and retain genuine numeric values as numbers. Export does not create server files or an enterprise reporting engine.

### 10. Contract conflicts requiring approval

| Existing constraint | Proposed explicit resolution |
|---|---|
| Domain glossary/ADR-0002 limits scope to specialty-provider Clinic-Month | Generalize external identity to Entity-Month but retain monthly visit-based model and closed-month forecast comparison. Hospital-specific modeling remains excluded. Update domain docs/ADR only after approval. |
| Synthetic-only scenario/interpretation/presentation guards | Permit validated uploaded planning provenance; continue rejecting benchmark provenance. |
| V1 names differ from proposed normalized schema | One explicit renaming adapter; no model fork. |
| V1 numeric validator permits zero days/reimbursement | Stricter import baseline rules only; preserve V1 scenario experiment behavior. |
| USD units and currency-specific causal checks | Currency-aware labels and a single currency per session; keep unsupported currency mechanisms unresolved. |
| V1 investigation requires five logical input groups, not one performance table | Construct identities, split financial/operational metrics, and supply explicit session review settings; no fake financial inputs. |
| User event names/values cannot satisfy all V1 rule prerequisites | Preserve reported evidence, explicit semantic mapping, typed timing evidence, no free-text inference. |
| Margin/bridge/share calculations currently live outside ScenarioResult | Relocate existing derived measures into shared result assembly, leaving formulas unchanged. |
| Custom reference schema lacks verified public-source metadata | Separate uploaded-reference contract, never fake public lineage. |
| “Currency assumed USD” example conflicts with no silent ambiguous inference | Suggest when supported by metadata; require explicit currency confirmation. |
| Session-local reuse of Python requires local transfer | Browser owns session; normalized investigation data is request-local in the loopback Python process. No external transfer. |

## Testing Decisions

Proposed highest test boundary: the real browser workflow from file selection through import, analysis, review, export, and clear, exercised against the local server. Reuse V1's Playwright-backed Python tests and deterministic C01–C10 evaluator. Add focused normalized-import and composer contract cases only where UI tests would obscure validation edge cases. Reuse existing scenario and investigation engine entry points rather than adding a second calculator or testing implementation internals. This test boundary is part of the requested specification approval.

| Outcome | Required verification |
|---|---|
| Reliable import | CSV quoting/BOM/errors; XLSX sheet selection and multiple roles; aliases/collisions; required fields; bad numerics; percentages including Excel percent cells; date formats; negative rules; duplicate keys; units/currencies; formula-cache handling; bounded/cancelled malformed input |
| Protected analysis | Baseline immutability; recalculation against existing engine outputs; multiple entity/period/scenario selections; no cross-entity leakage; identical result revision across summary/charts/commentary/export; stale draft disabled states |
| Honest investigation | Actual/Forecast and event imports; metric IDs/units; missing rate and supporting metrics; unsupported events; provider FTE not availability days; incomplete evidence Unresolved; typed timing only; notes never cause support; review thresholds/override; stale confirmation rejection |
| Optional context | Custom benchmark import; HCA/Tenet read-only; public/uploaded/synthetic labeling; No Benchmark; no reference-to-assumption mutation |
| Local lifecycle | Scenario-only and variance-only workflows; clear/reset distinction; failure preserves prior import; refresh loses data; delayed responses cannot restore cleared data; no persistence, payload logging, external requests, or required API keys |
| Trustworthy commentary | Values trace to current computed result; changes produce updated text; favorable/unfavorable/zero and offsets; multiple changes avoid false attribution; supported versus confirmed; no unsupported drivers or independent financial arithmetic; 3–5 sentence quality fixtures |
| V1 compatibility | Existing formulas/output fixtures, source checks, engine/evidence boundaries, C01–C10 expected answers and browser regression checks remain passing; navigation tests enter Explore Demo where needed |

### Primary acceptance demonstration

After approval, create an explicitly synthetic sample XLSX with Planning, Actual vs Forecast, and optional Events sheets. Include multiple entities/months, including Nashville Specialty Clinic in August 2026. Supply all nine planning assumptions; the three demonstration mappings alone are not sufficient input. Tag the provided sample as synthetic demo content even though it enters through the upload workflow.

Open → Use My Data → choose workbook → Planning → map FTE Count, Work Days, and Rev / Visit → validate → compare original/normalized previews → confirm → select Nashville/August → change FTE 4.0 to 3.5 → verify all dependent outputs, Executive Summary, and commentary. Import/confirm the performance sheet in the same workflow so Variance Investigation is available. Open a revenue variance with insufficient evidence and demonstrate Unresolved. Export summary, reset scenario, clear uploads, then open Explore Demo and verify it still works.

Demonstrate with external networking blocked and no API credentials. No benchmark or event import is required for the planning portion. The sample's financial expectations are calculated/tested after approval from declared assumptions; illustrative figures in the request are not hard-coded as commentary.

V2 is done only when a new analyst can perform the above without code assistance, all required validation and partial states work, custom benchmarks are optional, session clearing works, commentary is deterministic, and V1 regression checks pass.

## Out of Scope

Authentication, accounts, multi-user permissions, cloud/production databases, persistent uploads, audit-log infrastructure, PHI/employee PII/patient/claim ingestion, EHR/Epic/Cerner/ERP integration, live feeds, external analytics, RAG, vector databases, fine-tuning, paid or free LLM inference, API keys, autonomous approvals, and automatic forecast changes.

Also excluded to keep V2 narrow: inpatient/case-mix or hospital-wide financial engines, consolidation, currency conversion, fiscal-calendar conversion, automatic annualization, arbitrary Excel formula recalculation, complex workbook reshaping, mapping-template persistence, multiple approved-forecast versions, scenario libraries, and an enterprise reporting engine. Optional model-generated prose belongs to a separately approved future version and is not needed for any V2 acceptance criterion.

## Further Notes

### Recommended future ticket outcomes — proposals only

Recommend **four** outcome-oriented tickets after specification approval; no ticket files or implementation status are created now:

1. **Import trusted session data:** guided CSV/XLSX import, all role schemas, mapping, normalization, provenance, validation/preview, session lifecycle, and representative samples.
2. **Model and communicate my scenario:** imported immutable baseline, selectors, shared result extensions, Executive Summary, deterministic scenario commentary, notes, reset, and CSV export.
3. **Investigate my performance with evidence:** request-local Python adapter, review settings, metric/event mapping, conservative timing, snapshot-bound human decisions, deterministic variance commentary, and partial states.
4. **Preserve context and prove the complete experience:** custom/public/no benchmark selection, V1 compatibility, privacy/network checks, full acceptance rehearsal, and regression closure. Public/uploaded separation is enforced throughout earlier outcomes, not deferred until this final ticket.

The main cost lies in trustworthy import and evidence adaptation, not new finance formulas. No implementation estimate is implied by the four-ticket grouping.

**Zero-token confirmation:** V2 uses deterministic local parsing, mapping, validation, calculations, evidence rules, and narrative templates. It requires zero external LLM tokens, zero paid API calls, no API key, no account, and no cloud database.

**Approval gate:** Approve or revise this specification—including the proposed contract resolutions and browser-level test boundary—before to-tickets or implementation. Until then V1 remains closed and unchanged.
