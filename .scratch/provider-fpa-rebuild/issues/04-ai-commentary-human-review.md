# 04: AI Commentary + Human Review

Status: needs-info
Review state: Draft ticket for user review; milestone direction and parent specification approved. Implementation has not been authorized.

## Parent

[Approved Healthcare Provider FP&A Copilot specification](../spec-proposed.md), approved 2026-09-15. This ticket supersedes the earlier provisional content; prior versions remain in Git history.

**What to build:** Turn the selected investigation into explicitly disclosed offline commentary and demonstrate human judgment through four review actions in the current session.

**Blocked by:** 03 — Evidence-Backed Investigation

## Acceptance criteria

- [ ] Default to the recovered deterministic fallback narrative with the seven documented commentary sections. It consumes the validated investigation result and preserves numbers, roles, sources and unresolved boundaries.
- [ ] Disclose synthetic benchmark data and offline deterministic fallback behavior in the UI and demo. Run without API keys or live model/network calls. No live LLM integration task or live-AI completion gate.
- [ ] Preserve compatible guarded narrative contracts and injected-response tests. Do not change substantive rejection semantics to silently show rejected output as valid commentary. Invalid fallback output must also fail visibly.
- [ ] Provide exactly the four required session review actions: confirm cause, reject cause, keep unresolved, request further investigation. Confirmation applies only to supported drivers; unsupported C04 causes remain unconfirmable.
- [ ] Keep the system result and human decision distinguishable. Rejection retains evidence; keep unresolved does not invent a cause; a further-investigation request does not confirm an explanation.
- [ ] Use in-memory session-only review state scoped to the investigation/input snapshot. Reset/session end discards decisions; no localStorage, sessionStorage, database, authentication or production state management. No refresh-survival guarantee.
- [ ] Assumption proposals remain advisory and final management interpretation remains human-owned. No separate proposal-approval editor, forecast write or final narrative editor is required.
- [ ] Test all four actions, supported-only transitions, reset/session isolation, stale-result prevention and unchanged source/forecast values. Distinguish Successful Investigation from Successfully Explained Variance.
- [ ] Verify C01 supported review, C04 keep-unresolved/request-investigation, and C03 role-preserving commentary through the same UI flow. Label this milestone as AI-boundary demonstration with offline output, never live generation.

## Requirement coverage

FR08–FR10; AC02, AC08–AC11.

## Shared constraints

Product Vision: **Healthcare Provider FP&A Copilot**.
MVP: **Evidence-aware clinic-month variance investigation**.
Workflow: **clinic-month → variance → evidence → driver → AI commentary → human review**.
Primary recruiting cases: **C01 supported; C04 unresolved/refusal; C03 upstream versus direct driver**.

The offline fallback is the approved default and fully satisfies MVP narration when accurately disclosed. Live generation is optional future scope. Review is session-only. Driver-specific scenarios are benchmark cases within one workflow. No real-data integration, PHI, RAG, external healthcare APIs, database, authentication, browser-local persistence or production infrastructure. Preserve compatible Phase 3/4 architecture and report conflicts before modifying business logic.

Use reversible Git snapshots before edits and working commits after verification. Test observable behavior using the public investigation/narrative boundaries and focused UI checks, not implementation layout. No code recovery or implementation begins until explicitly authorized by the user.

## Comments

2026-09-15: Regenerated under the approved five-milestone plan and resolved product decisions. Awaiting review of ticket detail and dependencies; no task is claimed or implemented.
