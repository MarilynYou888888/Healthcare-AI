# 03: Evidence-Backed Investigation

Status: needs-info
Review state: Draft ticket for user review; milestone direction and parent specification approved. Implementation has not been authorized.

## Parent

[Approved Healthcare Provider FP&A Copilot specification](../spec-proposed.md), approved 2026-09-15. This ticket supersedes the earlier provisional content; prior versions remain in Git history.

**What to build:** From the selected variance, inspect sources, supported or unresolved drivers and timing in the same investigation workflow, prioritizing C01, C04 and C03.

**Blocked by:** 02 — Variance Review Workspace

## Acceptance criteria

- [ ] Expose the recovered public InvestigationResult rather than rebuilding classification rules for the UI. Facts, evidence, drivers, conclusions and Source References remain separately identifiable.
- [ ] C01: show Demand & Volume as primary and Provider Availability as contributing; never claim PTO explains 100% of the revenue decline.
- [ ] C04: show unresolved operating cause/timing, no supported primary cause, and evidence rejecting reduced provider availability; do not infer temporary recovery or fabricate a root cause.
- [ ] C03: weather remains upstream context; Clinic Capacity & Operations contributes; Demand & Volume is the direct primary financial driver. No unsupported full attribution to weather or closure.
- [ ] Preserve the seven Driver Families plus fallback states. Candidate, Supported, Rejected and Unresolved remain explicit; the system does not automatically assign Analyst-Confirmed Cause.
- [ ] Preserve lineage to exact input records and available timestamps. Prevent cross-Clinic-Month contamination and distinguish retrospective snapshot evidence from as-of analysis.
- [ ] Retain the historical configurable 50% forecast-horizon threshold as a demo heuristic; document that it is not a universal healthcare FP&A standard and production should support business-specific configuration. Preserve Temporary/Structural/Unresolved, separate recurrence and labeled fallback horizons.
- [ ] Cover provider departure, labor, payer mix, accounting timing, seasonality, missing data and multiple drivers using the same benchmark entry point. These are regression cases, not separate UI features.
- [ ] Run the ten-case deterministic evaluator, including forbidden conclusions, with gold data isolated from investigation. Unknown or unsupported evaluator checks must not silently pass. Keep C01/C04/C03 as the first visible paths.

## Requirement coverage

FR06–FR07; AC04–AC08; seven-dimensional benchmark evaluation.

## Shared constraints

Product Vision: **Healthcare Provider FP&A Copilot**.
MVP: **Evidence-aware clinic-month variance investigation**.
Workflow: **clinic-month → variance → evidence → driver → AI commentary → human review**.
Primary recruiting cases: **C01 supported; C04 unresolved/refusal; C03 upstream versus direct driver**.

The offline fallback is the approved default and fully satisfies MVP narration when accurately disclosed. Live generation is optional future scope. Review is session-only. Driver-specific scenarios are benchmark cases within one workflow. No real-data integration, PHI, RAG, external healthcare APIs, database, authentication, browser-local persistence or production infrastructure. Preserve compatible Phase 3/4 architecture and report conflicts before modifying business logic.

Use reversible Git snapshots before edits and working commits after verification. Test observable behavior using the public investigation/narrative boundaries and focused UI checks, not implementation layout. No code recovery or implementation begins until explicitly authorized by the user.

## Comments

2026-09-15: Regenerated under the approved five-milestone plan and resolved product decisions. Awaiting review of ticket detail and dependencies; no task is claimed or implemented.
