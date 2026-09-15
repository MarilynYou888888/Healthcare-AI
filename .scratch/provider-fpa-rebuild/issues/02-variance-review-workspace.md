# 02: Variance Review Workspace

Status: needs-info
Review state: Draft ticket for user review; milestone direction and parent specification approved. Implementation has not been authorized.

## Parent

[Approved Healthcare Provider FP&A Copilot specification](../spec-proposed.md), approved 2026-09-15. This ticket supersedes the earlier provisional content; prior versions remain in Git history.

**What to build:** Select a Clinic-Month, inspect actual-versus-forecast performance and open a rule-selected variance for investigation in a single workspace.

**Blocked by:** 01 — Data Intake & Validation

## Acceptance criteria

- [ ] Preserve authoritative historical arithmetic: actual minus comparator, decimal precision, undefined ratios and explicit direction. Display units, actual, comparator, signed difference and percentage or unavailable reason.
- [ ] Distinguish Financial Variance from relevant Operational Metric Variance and Forecast Assumption Variance without building separate KPI or forecast products.
- [ ] Expose Review Queue inclusion reasons using strict materiality thresholds, critical rules and Analyst Override. No LLM selection and no full rule-administration feature.
- [ ] Keep Clinic-Month, target and comparison identity consistent across selection and details; block calculations missing a usable comparator.
- [ ] Verify exact-threshold behavior, zero/missing denominator, rule inclusion, overrides and cross-case isolation through public results and a small visible workflow check.
- [ ] Check C01, C04 and C03 displayed revenue values against retained inputs; no hardcoded benchmark answers.

## Requirement coverage

FR03–FR05; AC02–AC03 foundations, AC08.

## Shared constraints

Product Vision: **Healthcare Provider FP&A Copilot**.
MVP: **Evidence-aware clinic-month variance investigation**.
Workflow: **clinic-month → variance → evidence → driver → AI commentary → human review**.
Primary recruiting cases: **C01 supported; C04 unresolved/refusal; C03 upstream versus direct driver**.

The offline fallback is the approved default and fully satisfies MVP narration when accurately disclosed. Live generation is optional future scope. Review is session-only. Driver-specific scenarios are benchmark cases within one workflow. No real-data integration, PHI, RAG, external healthcare APIs, database, authentication, browser-local persistence or production infrastructure. Preserve compatible Phase 3/4 architecture and report conflicts before modifying business logic.

Use reversible Git snapshots before edits and working commits after verification. Test observable behavior using the public investigation/narrative boundaries and focused UI checks, not implementation layout. No code recovery or implementation begins until explicitly authorized by the user.

## Comments

2026-09-15: Regenerated under the approved five-milestone plan and resolved product decisions. Awaiting review of ticket detail and dependencies; no task is claimed or implemented.
