# 03: Custom Benchmarks + Zero-Token FP&A Commentary

Status: needs-triage
Approval: Ticket scope and publication approved by the user. Implementation is NOT authorized; stop for review after publication.
Blocked by: 02 — Run Existing FP&A Workflows on User Data; transitively reuses the importer delivered by 01.
Specification: Approved narrow V2 specification, including the fully free product clarification.

## What to build

A Provider FP&A Analyst can select optional benchmark context and receive concise professional Automated FP&A Commentary directly from calculated scenario/investigation results and their recorded evidence states, fully free and without an LLM.

## Acceptance criteria

- [ ] Offer HCA Healthcare, Tenet Healthcare, Custom Benchmark, and No Benchmark. Default user-data mode to No Benchmark; missing benchmarks never block analysis.
- [ ] HCA and Tenet remain read-only built-in public benchmarks with their existing source lineage. They are public context, not clinic budgets, targets, or automatic assumption inputs.
- [ ] Custom Benchmark uses Ticket 1's shared CSV/XLSX import, mapping, validation, normalization preview, and explicit confirmation. Display submitted company, period, segment, metric, unit, source, notes, and optional URL without fabricating verified-filing metadata.
- [ ] Clearly distinguish BUILT-IN PUBLIC, USER UPLOADED, and SYNTHETIC provenance. A user-provided source label does not make an upload verified public data. Show scope/period/currency differences and prevent unsupported monetary comparisons.
- [ ] Benchmark selection never changes assumptions, fills missing inputs, or sets performance targets. Source URLs are opened only by user action, never automatically fetched.
- [ ] Rename misleading “AI Commentary” labels to **Automated FP&A Commentary**. Disclose: “Rule-based commentary from calculated results and recorded evidence. No LLM or external API is used.”
- [ ] Scenario and investigation composers select reusable deterministic statement components to produce generally 3–5 concise professional sentences. Avoid a single fixed paragraph, filler, unsupported recommendations, and repetitive wording.
- [ ] Every numerical financial claim traces to the current ScenarioResult or InvestigationResult. The composer formats already-computed values and recorded evidence states; it does not independently calculate financial results or classify evidence.
- [ ] Scenario wording covers changed assumptions, modeled operating impact, financial impact, variable-cost offsets/amplification, fixed-cost behavior, and defined margin changes. No-change and multiple-driver scenarios avoid invented effects or uncomputed primary-driver attribution.
- [ ] Investigation wording respects favorable/unfavorable direction, primary/contributing roles, timing, missing evidence, rejected drivers, and supported versus explicitly human-confirmed states. Unsupported causes remain Unresolved; no forecast update is claimed.
- [ ] Commentary binds to the current valid revision/snapshot and updates with results or explicit human decisions. Invalid/stale results cannot produce current commentary. Analyst Notes stay separate and do not enter causal composition.
- [ ] Deterministic commentary is the default and complete solution. No LLM, token usage, API keys, external AI-provider accounts, paid API calls, paid cloud inference, or external AI dependency is required or invoked.

## Tests and validation

- Browser cases import/select a custom benchmark, select No Benchmark, and switch HCA/Tenet; assert readable provenance and unchanged scenario assumptions/results.
- Verify built-in reference files remain unchanged, custom data never acquires fabricated public lineage, and mismatched units/currencies/scopes cannot produce misleading comparisons.
- Composer cases cover no change, favorable/unfavorable changes, offsets/amplification, fixed expense changes, margin availability, multiple changed assumptions, and current-result changes.
- Verify all numerical claims trace to computed result fields, unsupported drivers/recommendations are absent, and supported/confirmed/rejected/unresolved wording follows actual evidence and human-review state.
- Verify notes cannot influence support, stale commentary is withheld, and concise narrative fixtures meet the professional 3–5 sentence target.
- Run with external networking blocked and no AI credentials. Check relevant V1 reference, narrative, and human-review regressions.

## Demo relevance

Switch among public, custom, and no benchmark context without changing modeled results. Edit a scenario assumption and show professional commentary updating. Show an imported unresolved variance described accurately without implying a confirmed cause or updated forecast.

## Boundaries and handoff

Do not duplicate formulas in commentary or benchmark views. No authentication, databases, PHI/EHR support, RAG, autonomous decisions, or generative implementation. If future prose is mentioned, use only “Optional future enhancement: local or user-hosted open-source generative narrative layer.” It is an optional experiment outside V2 and never a core dependency. Ticket 4 integrates export and complete-product acceptance; no low-level ticket expansion is authorized.

## Comments

The user approved publication of exactly four tickets in dependency order 1 → 2 → 3 → 4. Publication does not authorize implementation. The holding status preserves that review gate and does not indicate unresolved scope.
