"""Clinic-Month investigation orchestration over immutable datasets."""

from dataclasses import replace

from provider_fpa.calculations import calculate_variance
from provider_fpa.drivers import assess_drivers
from provider_fpa.models import (
    Datasets, ForecastHorizon, InvestigationResult, ObservedFact, ObservedVariance, Value,
)
from provider_fpa.review import evaluate_review
from provider_fpa.timing import add_months, classify_timing, fallback_horizon, month_index


def observed_variance(value: Value) -> ObservedVariance:
    calculation = calculate_variance(value.actual, value.comparator)
    change = calculation.absolute
    lower_is_better = value.item_id.startswith('EXP_') or value.item_id in {
        'OVERTIME_HOURS', 'CLINIC_CLOSURE_DAYS', 'PROVIDER_PTO_DAYS',
    }
    known_direction = lower_is_better or value.item_id in {
        'REV_NET_PATIENT', 'PATIENT_VISITS', 'PROVIDER_AVAILABLE_DAYS', 'NET_REVENUE_PER_VISIT',
    }
    direction = ('undefined' if change is None else 'on_plan' if change == 0 else
                 'unclassified' if not known_direction else
                 'unfavorable' if (change > 0 if lower_is_better else change < 0) else 'favorable')
    return ObservedVariance(value.item_id, value.variance_type, calculation, direction,
                            value.unit, value.currency, (value.evidence,))


def investigate(data: Datasets, clinic_id: str, month: str, target_id: str,
                target_type: str = 'financial_variance', *, analyst_override: bool = False) -> InvestigationResult:
    month_index(month)
    clinics = [c for c in data.clinics if c.clinic_id == clinic_id]
    if len(clinics) != 1 or month < clinics[0].active_from or (clinics[0].active_to and month > clinics[0].active_to):
        raise ValueError('Investigation requires one active Clinic')
    if target_type not in {'financial_variance', 'operational_metric_variance', 'forecast_assumption_variance'}:
        raise ValueError('Unknown variance type')
    financial = tuple(v for v in data.financial_values if v.clinic_id == clinic_id)
    operating = tuple(v for v in data.operational_values if v.clinic_id == clinic_id)
    monthly = tuple(v for v in operating if v.month == month)
    pool = financial if target_type == 'financial_variance' else operating
    targets = [v for v in pool if v.month == month and v.item_id == target_id]
    if len(targets) != 1:
        raise ValueError('Investigation requires exactly one target value')
    target = replace(targets[0], variance_type=target_type)
    all_events = tuple(e for e in data.operating_events if e.clinic_id == clinic_id)
    events = tuple(e for e in all_events if e.event_type != 'forecast_horizon'
                   and e.start_date[:7] <= month and (e.end_date is None or e.end_date[:7] >= month))
    horizons = [e for e in all_events if e.event_type == 'forecast_horizon'
                and e.end_date is not None and e.end_date[:7] > month]
    if len(horizons) > 1:
        raise ValueError('Latest Approved Forecast horizon is ambiguous')
    if horizons:
        event = horizons[0]
        horizon = ForecastHorizon(max(add_months(month, 1), event.start_date[:7]), event.end_date[:7],
                                  'latest_approved_forecast', (event.evidence,))
    else:
        horizon = fallback_horizon(month)

    assessment = assess_drivers(target, monthly, events, financial, operating)
    target_variance = observed_variance(target)
    values = [target, *(v for v in monthly if v.item_id != target_id), *assessment.additional_values]
    facts = [ObservedFact('clinic_identity', clinic_id, (('clinic_name', clinics[0].clinic_name),), (clinics[0].evidence,))]
    facts.extend(ObservedFact('value_comparison', v.item_id,
                              (('month', v.month), ('actual', str(v.actual) if v.actual is not None else None),
                               ('comparator', str(v.comparator) if v.comparator is not None else None)), (v.evidence,))
                 for v in values)
    facts.extend(ObservedFact('reported_event', e.event_id,
                              (('event_type', e.event_type), ('description', e.description),
                               ('start_date', e.start_date), ('end_date', e.end_date)), (e.evidence,))
                 for e in events)
    variances = [target_variance]
    for value in monthly:
        if value.item_id == target_id:
            continue
        variances.append(observed_variance(value))
        # The local MVP contract treats the expected revenue-per-visit value as
        # an embedded forecast assumption when paired with approved revenue.
        if value.item_id == 'NET_REVENUE_PER_VISIT' and target_type == 'financial_variance':
            variances.append(observed_variance(replace(value, variance_type='forecast_assumption_variance')))
    return InvestigationResult(
        clinic_id, month, target_variance,
        evaluate_review(target_id, month, target_variance.calculation, data.review_rules, analyst_override=analyst_override),
        tuple(variances), tuple(facts), assessment.drivers,
        classify_timing(horizon, assessment.timing_evidence), assessment.questions, assessment.contribution,
    )


def investigate_clinic_month(data: Datasets, clinic_id: str, month: str) -> tuple[InvestigationResult, ...]:
    """All financial and operational targets, each carrying its review decision."""
    return tuple(investigate(data, clinic_id, month, v.item_id, v.variance_type)
                 for v in (*data.financial_values, *data.operational_values)
                 if v.clinic_id == clinic_id and v.month == month)
