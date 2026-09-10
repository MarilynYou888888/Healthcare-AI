"""Bounded human-readable templates and lossless JSON; no analytical decisions."""

from dataclasses import fields, is_dataclass
from decimal import Decimal
from enum import Enum

from provider_fpa.models import InvestigationResult, ObservedVariance, SourceReference


QUESTIONS = {
    'restore_target_input': 'Can the missing or invalid target value be restored and reconciled?',
    'restore_operating_input': 'Can the operating feed be restored and reconciled before causal review?',
    'reconcile_revenue_bridge': 'Why do revenue, visits, and revenue per visit fail to reconcile?',
    'verify_provider_recovery_or_replacement': 'Did availability and visits recover, or what replacement start date is approved?',
    'validate_provider_constraint': 'What operating evidence links provider availability to the visit shortfall?',
    'verify_deferred_visit_recovery': 'Did deferred visits return after the capacity interruption, or were they lost?',
    'validate_capacity_constraint': 'Can closure or capacity metrics substantiate the reported interruption?',
    'verify_seasonal_recovery': 'Do forward bookings support the expected seasonal recovery?',
    'explain_visit_shortfall': 'What operating event or schedule change explains the missing visits?',
    'verify_rate_mix_persistence': 'Is the documented rate and payer-mix shift expected to persist through the forecast horizon?',
    'validate_rate_change': 'What evidence explains the revenue-per-visit change?',
    'verify_overtime_normalization': 'Did overtime hours and expense normalize after the vacancy ended?',
    'quantify_labor_rate_bridge': 'Can an applicable labor-rate bridge quantify the overtime contribution?',
    'verify_accrual_reversal': 'Does the subsequent accounting close reconcile the documented accrual reversal?',
    'reconcile_accrual': 'Can the accrual amount, account, and reversal be reconciled?',
    'verify_metric_persistence': 'What evidence establishes recovery or persistence of this operating metric?',
    'resolve_primary_mechanism': 'What additional evidence establishes a unique primary business mechanism?',
    'quantify_overlapping_constraints': 'How did cancellations overlap across the documented capacity constraints?',
}
MECHANISMS = {
    'business_mechanism_unresolved': 'Available evidence does not establish the business mechanism.',
    'invalid_target_input': 'The target input is missing or invalid.',
    'missing_or_invalid_operating_input': 'Missing or invalid operating input prevents a supported interpretation.',
    'revenue_bridge_does_not_reconcile': 'Revenue does not reconcile to visits multiplied by revenue per visit.',
    'availability_constrains_visits': 'Documented provider constraints and lower availability support a constraint on visits.',
    'availability_on_plan': 'Provider availability was on plan; a measured availability shortfall is rejected.',
    'availability_needs_operating_evidence': 'A provider constraint is plausible but lacks sufficient operating evidence.',
    'closure_constrains_visits': 'Documented closure and closure-day metrics support a constraint on visits.',
    'documented_external_context': 'The reported external disruption is upstream operating context.',
    'capacity_needs_operating_evidence': 'The reported capacity interruption needs corroborating operating metrics.',
    'visits_reduce_revenue': 'Lower visits support the direct revenue mechanism; contribution allocation remains unquantified.',
    'supported_visit_shortfall': 'Documented operating evidence supports the visit shortfall.',
    'visits_on_plan': 'Visits were on plan; a measured volume shortfall is rejected.',
    'rate_and_mix_reduce_revenue': 'Lower revenue per visit and documented payer-mix changes support a revenue realization mechanism.',
    'rate_change_needs_evidence': 'The rate change is observed, but its business mechanism needs supporting evidence.',
    'overtime_increases_expense': 'Additional overtime and documented coverage needs support higher labor expense.',
    'documented_accrual_timing': 'The documented accrual supports an accounting timing mechanism.',
    'accrual_needs_reconciliation': 'The reported accrual needs reconciliation before it can be supported.',
    'documented_operating_metric_change': 'The operating metric change is supported by a corresponding documented event.',
    'unmodeled_business_mechanism': 'This metric has no configured deterministic business-mechanism rule.',
}


def json_value(value):
    """Decimals are JSON strings so financial precision survives serialization."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, SourceReference):
        return {'input_file': value.input_file, 'row_selector': dict(value.row_selector),
                'source': value.source, 'recorded_at': value.recorded_at}
    if is_dataclass(value):
        return {field.name: json_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, dict):
        return {key: json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(item) for item in value]
    return value


def variance_payload(variance: ObservedVariance) -> dict:
    return {'id': variance.item_id, 'variance_type': variance.variance_type,
            **json_value(variance.calculation), 'direction': variance.direction,
            'unit': variance.unit, 'currency': variance.currency, 'evidence': json_value(variance.evidence)}


def investigation_payload(result: InvestigationResult) -> dict:
    drivers = [{**json_value(d), 'explanation': MECHANISMS[d.mechanism]} for d in result.drivers]
    facts = [{**json_value(f), 'values': dict(f.values)} for f in result.observed_facts]
    return {
        'clinic_id': result.clinic_id, 'month': result.month,
        'variance': variance_payload(result.variance),
        'review_required': result.review_required, 'review': json_value(result.review),
        'observed_variances': [variance_payload(v) for v in result.observed_variances],
        'observed_facts': facts, 'drivers': drivers,
        'primary_driver': json_value(result.primary_driver),
        'contributing_drivers': json_value(result.contributing_drivers),
        'upstream_context': json_value(result.upstream_context),
        'timing_classification': result.timing.classification, 'timing': json_value(result.timing),
        'unresolved_questions': [QUESTIONS[q] for q in result.unresolved_questions],
        'contribution_estimate': json_value(result.contribution_estimate),
        'human_review_requirement': {'required': result.human_review_required,
                                     'analyst_status_at_system_output': result.analyst_status,
                                     'allowed_actions': ['confirm', 'reject', 'request_more_evidence']},
        'successful_investigation': result.successful_investigation,
        'successfully_explained_variance': result.successfully_explained_variance,
        'material_undisclosed_issue': result.material_undisclosed_issue,
    }
