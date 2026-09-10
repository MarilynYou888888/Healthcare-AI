"""State transitions. Human confirmation has a separate explicit entry point."""

from dataclasses import replace

from provider_fpa.models import Driver, EpistemicState as S, HumanDecision, SourceReference


def transition_driver(driver: Driver, state: S, *,
                      evidence: tuple[SourceReference, ...] = ()) -> Driver:
    allowed = {
        S.CANDIDATE: {S.SUPPORTED, S.REJECTED, S.UNRESOLVED},
        S.SUPPORTED: {S.REJECTED, S.UNRESOLVED},
        S.UNRESOLVED: {S.CANDIDATE, S.SUPPORTED, S.REJECTED},
        S.REJECTED: {S.CANDIDATE},
    }
    if state not in allowed.get(driver.epistemic_state, set()):
        raise ValueError('Invalid autonomous evidence-state transition')
    if state in (S.SUPPORTED, S.REJECTED) and not evidence:
        raise ValueError('Support or rejection requires traceable evidence')
    return replace(driver, epistemic_state=state, evidence=evidence or driver.evidence,
                   role=driver.role if state == S.SUPPORTED else None)


def confirm_driver(driver: Driver, decision: HumanDecision) -> Driver:
    """Caller must be a trusted human-review boundary, never engine inference."""
    if driver.epistemic_state != S.SUPPORTED or not isinstance(decision, HumanDecision):
        raise ValueError('A human may confirm only a supported driver')
    return replace(driver, epistemic_state=S.CONFIRMED, human_decision=decision)


def is_successfully_explained(successful_investigation: bool, drivers: tuple[Driver, ...],
                             material_undisclosed_issue: bool) -> bool:
    return (successful_investigation and not material_undisclosed_issue
            and any(d.epistemic_state == S.CONFIRMED and d.human_decision is not None for d in drivers))
