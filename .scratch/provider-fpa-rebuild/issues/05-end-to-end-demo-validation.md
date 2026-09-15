# 05: End-to-End Demo & Validation

Status: needs-info
Review state: Draft ticket for user review; milestone direction and parent specification approved. Implementation has not been authorized.

## Parent

[Approved Healthcare Provider FP&A Copilot specification](../spec-proposed.md), approved 2026-09-15. This ticket supersedes the earlier provisional content; prior versions remain in Git history.

**What to build:** Deliver a reproducible portfolio demonstration of the complete workflow and an honest validation record that a healthcare finance hiring manager can understand quickly.

**Blocked by:** 04 — AI Commentary + Human Review

## Acceptance criteria

- [ ] Run clinic-month → variance → evidence → driver → AI commentary → human review using C01, C04 and C03 in that order. No hidden data edits or operator-only steps.
- [ ] Rerun the complete recovered and newly added test suite after integration, plus all ten benchmark cases with seven-dimension results and forbidden-conclusion checks. Record actual results and remaining failures.
- [ ] Run a small browser suite for the three primary scenarios, input failures, offline commentary, four review actions and session reset/isolation. Verify the demo has no live API-key dependency.
- [ ] Confirm no autonomous Analyst-Confirmed Cause; correctly unresolved investigations may succeed as investigations but cannot be presented as successfully explained variances.
- [ ] Prepare a concise startup/demo/reset guide, primary scenario sequence and 60-second introduction covering user, problem, manual context gathering, system behavior, AI responsibilities/limits and human judgment.
- [ ] Time the introduction and record the actual evaluation method. A hiring-manager comprehension check must not be claimed unless conducted; report rehearsal-only evidence as such.
- [ ] Clearly distinguish the broader Healthcare Provider FP&A Copilot vision from the narrow Evidence-aware clinic-month variance investigation MVP, and label synthetic data and deterministic fallback throughout portfolio materials.
- [ ] Document the configurable 50% timing heuristic and bounded synthetic-data limitations. Do not claim real-data validation, live LLM generation, ROI, production readiness or customer adoption.
- [ ] Final acceptance does not require live APIs, credentials, persistence, production deployment or future workflows. All approved functional and evaluation criteria must be checked; no mock or old report may stand in for a current run.

## Requirement coverage

FR11; overall AC01–AC12 and Definition of done.

## Shared constraints

Product Vision: **Healthcare Provider FP&A Copilot**.
MVP: **Evidence-aware clinic-month variance investigation**.
Workflow: **clinic-month → variance → evidence → driver → AI commentary → human review**.
Primary recruiting cases: **C01 supported; C04 unresolved/refusal; C03 upstream versus direct driver**.

The offline fallback is the approved default and fully satisfies MVP narration when accurately disclosed. Live generation is optional future scope. Review is session-only. Driver-specific scenarios are benchmark cases within one workflow. No real-data integration, PHI, RAG, external healthcare APIs, database, authentication, browser-local persistence or production infrastructure. Preserve compatible Phase 3/4 architecture and report conflicts before modifying business logic.

Use reversible Git snapshots before edits and working commits after verification. Test observable behavior using the public investigation/narrative boundaries and focused UI checks, not implementation layout. No code recovery or implementation begins until explicitly authorized by the user.

## Comments

2026-09-15: Regenerated under the approved five-milestone plan and resolved product decisions. Awaiting review of ticket detail and dependencies; no task is claimed or implemented.
