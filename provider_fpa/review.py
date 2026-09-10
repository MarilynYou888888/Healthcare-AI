"""Provider-configured review selection, independent of causal interpretation."""

from provider_fpa.calculations import Calculation
from provider_fpa.models import ReviewDecision, ReviewRule


def evaluate_review(target_id: str, month: str, variance: Calculation,
                    rules: tuple[ReviewRule, ...], *, analyst_override: bool = False) -> ReviewDecision:
    reasons = ['analyst_override'] if analyst_override else []
    evidence = []
    for rule in rules:
        if (rule.target_id != target_id or month < rule.effective_from
                or (rule.effective_to is not None and month > rule.effective_to)):
            continue
        triggered = []
        if (variance.absolute is not None and rule.absolute_threshold is not None
                and abs(variance.absolute) > rule.absolute_threshold):
            triggered.append('absolute_threshold')
        if (variance.percentage is not None and rule.percentage_threshold is not None
                and abs(variance.percentage) > rule.percentage_threshold):
            triggered.append('percentage_threshold')
        if rule.always_review:
            triggered.append('always_review')
        if triggered:
            reasons.extend(triggered)
            evidence.append(rule.evidence)
    return ReviewDecision(bool(reasons), tuple(dict.fromkeys(reasons)), tuple(evidence))
