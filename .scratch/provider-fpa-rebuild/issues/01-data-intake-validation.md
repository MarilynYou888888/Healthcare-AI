# 01: Data Intake & Validation

Status: needs-info
Review state: Draft ticket for user review; milestone direction and parent specification approved. Implementation has not been authorized.

## Parent

[Approved Healthcare Provider FP&A Copilot specification](../spec-proposed.md), approved 2026-09-15. This ticket supersedes the earlier provisional content; prior versions remain in Git history.

**What to build:** Open Healthcare Provider FP&A Copilot, explicitly load the synthetic dataset, inspect validation results and select a Clinic-Month using a recovered, verified analytical baseline.

**Blocked by:** None; implementation authorization is still required.

## Acceptance criteria

- [ ] Selectively recover the historical Phase 3 deterministic investigation engine, Phase 4 guarded narrative layer and compatible tests from Git history rather than rebuild. Historical snapshot 40e4829 is a candidate baseline; inspect contents before recovery and avoid restoring the old UI indiscriminately.
- [ ] Before integration, inspect recovered behavior against the approved specification and rerun the complete recovered test suite. Record actual commands/results and failures; old reports do not count as current verification.
- [ ] Report any conflicts before changing business logic, including threshold equality or narrative guard behavior. Preserve only compatible code; document any proposed business-logic correction and its reason before applying it. No broad engine redesign.
- [ ] Present the product name Healthcare Provider FP&A Copilot and MVP subtitle Evidence-aware clinic-month variance investigation. Default empty state explains the demo; selecting synthetic data is explicit.
- [ ] Load the five known logical input groups and show validation/source status. Use known synthetic inputs only; no real-data mapping or generalized uploader is needed.
- [ ] Validate identity, months, duplicates, units, references and sources. Structural errors block loading; representable missing operating values remain unavailable for Data Quality Issue behavior. Do not substitute zero.
- [ ] Display available Clinic-Month selections and the disclosed synthetic comparison basis. No invented production approval metadata or personal-level identifiers.
- [ ] Verify loading, empty state, malformed records and the intentional missing-input benchmark through public input behavior. Recovery and UI foundation are one bounded milestone; if recovery reveals a major conflict, report it rather than expanding scope silently.

## Requirement coverage

FR01–FR03 foundations; AC03, AC07, AC08 foundations.

## Shared constraints

Product Vision: **Healthcare Provider FP&A Copilot**.
MVP: **Evidence-aware clinic-month variance investigation**.
Workflow: **clinic-month → variance → evidence → driver → AI commentary → human review**.
Primary recruiting cases: **C01 supported; C04 unresolved/refusal; C03 upstream versus direct driver**.

The offline fallback is the approved default and fully satisfies MVP narration when accurately disclosed. Live generation is optional future scope. Review is session-only. Driver-specific scenarios are benchmark cases within one workflow. No real-data integration, PHI, RAG, external healthcare APIs, database, authentication, browser-local persistence or production infrastructure. Preserve compatible Phase 3/4 architecture and report conflicts before modifying business logic.

Use reversible Git snapshots before edits and working commits after verification. Test observable behavior using the public investigation/narrative boundaries and focused UI checks, not implementation layout. No code recovery or implementation begins until explicitly authorized by the user.

## Comments

2026-09-15: Regenerated under the approved five-milestone plan and resolved product decisions. Awaiting review of ticket detail and dependencies; no task is claimed or implemented.
