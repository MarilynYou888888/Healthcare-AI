# 01: Public Benchmark + Synthetic Clinic Baseline

Status: ready-for-agent
Approval: Ticket content and dependency order approved by user; finalized with the two requested clarifications.
Execution gate: Implementation remains on hold until explicitly authorized. This status indicates specification readiness, not permission to start coding.

## Parent

[Healthcare Provider FP&A Copilot — approved specification](../spec-proposed.md). The user's approval in this conversation governs even if historical document metadata still says proposed. These five tickets replace the earlier provisional breakdown; do not execute old versions.

## User-visible outcome

Open the product, inspect source-linked HCA/Tenet public context and a clearly separate synthetic Clinic-Month baseline.

## Dependencies

Blocked by: None

## Acceptance criteria

- [ ] Present Healthcare Provider FP&A Copilot with Scenario Modeling primary and Variance Investigation secondary. Identify the primary user as a healthcare provider FP&A / financial analyst.
- [ ] Load verified HCA and Tenet FY2025 metrics through one normalized read-only interface, retaining company, period, segment, reporting basis, definitions, units, source document/URL/type and transformation lineage.
- [ ] Display the company selector and compact benchmark panel. Keep public actuals uneditable, missing history missing with reasons, and company-specific scope/denominators intact. No corporate-total allocation into clinics.
- [ ] Display the approved synthetic baseline assumptions and calculated baseline values with PUBLIC versus SYNTHETIC disclosure. Public context and editable planning values must not share an ambiguous dataset.
- [ ] Validate inputs and preserve decimal precision. Make baseline formulas inspectable; later scenario edits use the same model. Benchmark switching cannot mutate the synthetic baseline.
- [ ] Use local verified public extracts for a reliable offline demo, with source links available. Do not require a live API or imply affiliation, internal access or sponsorship.

## Tests

- [ ] Check HCA and Tenet normalization, source retention, $mm scaling, ratio units, duplicate handling and missing-history behavior.
- [ ] Check Tenet same-hospital versus full-segment basis and HCA payer-mix denominator; derived benchmark ratios retain matching inputs.
- [ ] Browser-check public read-only controls, synthetic labeling, company switching and baseline integrity; independently verify baseline calculations.

## Demo relevance

Establishes the opening public-company credibility and transparent synthetic-model framing.

## Requirement coverage

A01, A04, A12–A18.

## Shared constraints

Product: Healthcare Provider FP&A Copilot. Primary: Driver-Based Scenario Modeling. Secondary: Evidence-Aware Variance Investigation. Public HCA/Tenet FY2025 benchmarks are read-only context; synthetic clinic assumptions alone drive the scenario model. No public-to-clinic allocation, fabricated historical values or inferred corporate affiliation.

No authentication, databases, enterprise permissions, PHI, EHR integrations, RAG, multi-user collaboration, real-time APIs, production infrastructure or browser persistence. Preserve compatible historical Phase 3/4 code and inspect/retest before reuse; report conflicts before changing business logic. Keep every change reversible with the required pre-edit snapshot and working commit.

## Comments

User approved the five outcome-level tickets and dependency order. Ticket 2's reference impact is a regression expectation calculated from the approved inputs, never a hardcoded product output. Ticket 3 explicitly distinguishes deterministic finance, offline/demo fallback narrative and human judgment. No additional low-level tickets are created. Implementation has not started.
