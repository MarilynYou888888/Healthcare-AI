"""Evidence-gated business mechanisms; independent of case IDs and gold answers."""

from dataclasses import dataclass, replace
from decimal import Decimal
import re

from provider_fpa.models import (
    ContributionEstimate, Driver, DriverFamily as F, EpistemicState as S,
    OperatingEvent, SourceReference, TimingEvidence, Value,
)
from provider_fpa.timing import add_months


@dataclass(frozen=True)
class DriverAssessment:
    drivers: tuple[Driver, ...]
    timing_evidence: tuple[TimingEvidence, ...]
    questions: tuple[str, ...]
    additional_values: tuple[Value, ...] = ()
    contribution: ContributionEstimate | None = None


def references(*items: Value | OperatingEvent) -> tuple[SourceReference, ...]:
    return tuple(dict.fromkeys(item.evidence for item in items))


def delta(value: Value | None) -> Decimal | None:
    if value is None or value.actual is None or value.comparator is None or value.data_quality_issues:
        return None
    return value.actual - value.comparator


def assign_roles(drivers: tuple[Driver, ...], direct_families: tuple[F, ...]) -> tuple[Driver, ...]:
    """A unique supported direct mechanism wins; an upstream event never wins.

    Competing direct mechanisms remain unranked until evidence resolves their
    precedence. Role=None is also used for rejected and unresolved hypotheses.
    """
    supported = [d for d in drivers if d.epistemic_state == S.SUPPORTED
                 and d.driver_family in direct_families]
    if len(supported) != 1:
        return drivers
    primary = supported[0]
    return tuple(replace(d, role='primary' if d == primary else 'contributing')
                 if d.epistemic_state == S.SUPPORTED and d.role != 'upstream_context' else d
                 for d in drivers)


def event_timing(event: OperatingEvent) -> TimingEvidence:
    """Only recognized finite mechanisms or explicit persistence statements qualify.

    An arbitrary end_date is not a general claim that a business baseline recovers.
    These event types are the local input vocabulary for documented conditions.
    """
    ref = (event.evidence,)
    if event.end_date is None:
        return TimingEvidence(None, None, event.event_type == 'seasonal_pattern', ref)
    end = event.end_date[:7]
    if event.event_type in {'provider_departure', 'payer_contract_change'}:
        return TimingEvidence(None, end, False, ref)
    if event.event_type in {'provider_pto', 'clinic_closure', 'equipment_outage',
                            'temporary_staffing_vacancy', 'seasonal_pattern'}:
        return TimingEvidence(add_months(end, 1), None, event.event_type == 'seasonal_pattern', ref)
    if event.event_type == 'accrual_timing':
        return TimingEvidence(end, None, False, ref)
    return TimingEvidence(None, None, False, ref)


def assess_drivers(target: Value, operational: tuple[Value, ...], events: tuple[OperatingEvent, ...],
                   financial_history: tuple[Value, ...], operational_history: tuple[Value, ...]) -> DriverAssessment:
    metrics = {v.item_id: v for v in operational}
    drivers: list[Driver] = []
    timing: list[TimingEvidence] = []
    questions: list[str] = []
    additional: list[Value] = []
    contribution = None

    def add(family: F, state: S, mechanism: str, *items: Value | OperatingEvent,
            context: bool = False):
        drivers.append(Driver(family, 'upstream_context' if context else None,
                              state, mechanism, references(*items)))

    def unresolved(question: str):
        add(F.UNRESOLVED, S.UNRESOLVED, 'business_mechanism_unresolved', target)
        questions.append(question)

    def valid_metric(item_id: str) -> Value | None:
        value = metrics.get(item_id)
        return value if delta(value) is not None else None

    target_delta = delta(target)
    if target_delta is None:
        add(F.DATA_QUALITY, S.OBSERVED, 'invalid_target_input', target, context=True)
        unresolved('restore_target_input')
        return DriverAssessment(tuple(drivers), (), tuple(questions))
    if target_delta == 0:
        return DriverAssessment((), (), ())

    revenue = target.item_id == 'REV_NET_PATIENT' and target.variance_type == 'financial_variance'
    visits_target = target.item_id == 'PATIENT_VISITS'
    if revenue or visits_target:
        visits = valid_metric('PATIENT_VISITS')
        rate = valid_metric('NET_REVENUE_PER_VISIT')
        feed_failures = [e for e in events if e.event_type == 'data_feed_failure']
        if visits is None or (revenue and rate is None) or feed_failures:
            evidence = [target, *feed_failures]
            evidence.extend(v for key in ('PATIENT_VISITS', 'NET_REVENUE_PER_VISIT')
                            if (v := metrics.get(key)) is not None)
            add(F.DATA_QUALITY, S.OBSERVED, 'missing_or_invalid_operating_input', *evidence, context=True)
            unresolved('restore_operating_input')
            return DriverAssessment(tuple(drivers), (), tuple(questions))

        if revenue and (rate.unit != 'USD_per_visit' or target.currency != 'USD'
                        or visits.unit != 'visits'
                        or target.actual != visits.actual * rate.actual
                        or target.comparator != visits.comparator * rate.comparator):
            add(F.DATA_QUALITY, S.OBSERVED, 'revenue_bridge_does_not_reconcile', target, visits, rate, context=True)
            unresolved('reconcile_revenue_bridge')
            return DriverAssessment(tuple(drivers), (), tuple(questions))

        if revenue and target_delta > 0:
            # The first supported revenue rules explain adverse misses. A
            # shortfall in one component cannot become the primary explanation
            # for an overall favorable result driven by a different component.
            add(F.OTHER, S.CANDIDATE, 'unmodeled_business_mechanism', target, visits, rate)
            unresolved('resolve_primary_mechanism')
            return DriverAssessment(tuple(drivers), (), tuple(questions))

        visit_delta = delta(visits)
        availability = valid_metric('PROVIDER_AVAILABLE_DAYS')
        closure = valid_metric('CLINIC_CLOSURE_DAYS')
        providers = [e for e in events if e.event_type in {'provider_pto', 'provider_departure'}]
        capacity = [e for e in events if e.event_type in {'clinic_closure', 'equipment_outage'}]
        season = [e for e in events if e.event_type == 'seasonal_pattern']
        if visit_delta < 0:
            if providers and availability is not None and delta(availability) < 0:
                add(F.PROVIDER, S.SUPPORTED, 'availability_constrains_visits', target, visits, availability, *providers)
                timing.extend(event_timing(e) for e in providers)
                questions.append('verify_provider_recovery_or_replacement')
                additional.extend(v for v in operational_history if v.item_id == 'PROVIDER_AVAILABLE_DAYS'
                                  and v.month > target.month)
            elif availability is not None and delta(availability) == 0:
                add(F.PROVIDER, S.REJECTED, 'availability_on_plan', availability)
            elif providers or (availability is not None and delta(availability) < 0):
                add(F.PROVIDER, S.CANDIDATE, 'availability_needs_operating_evidence', target, *providers,
                    *([availability] if availability else []))
                questions.append('validate_provider_constraint')
            if capacity and closure is not None and delta(closure) > 0:
                add(F.CAPACITY, S.SUPPORTED, 'closure_constrains_visits', target, visits, closure, *capacity)
                timing.extend(event_timing(e) for e in capacity)
                questions.append('verify_deferred_visit_recovery')
                weather = [e for e in events if e.event_type == 'weather_disruption'
                           and any(c.start_date <= (e.end_date or e.start_date)
                                   and e.start_date <= (c.end_date or c.start_date) for c in capacity)]
                if weather:
                    add(F.EXTERNAL, S.OBSERVED, 'documented_external_context', *weather, *capacity, context=True)
            elif capacity:
                add(F.CAPACITY, S.CANDIDATE, 'capacity_needs_operating_evidence', target, *capacity)
                questions.append('validate_capacity_constraint')
            supported_upstream = any(d.epistemic_state == S.SUPPORTED for d in drivers)
            if supported_upstream or season:
                add(F.DEMAND, S.SUPPORTED, 'visits_reduce_revenue' if revenue else 'supported_visit_shortfall',
                    target, visits, *([rate] if revenue else []),
                    *providers, *capacity, *season)
                timing.extend(event_timing(e) for e in season)
                if season:
                    questions.append('verify_seasonal_recovery')
            else:
                unresolved('explain_visit_shortfall')
        elif revenue and visit_delta == 0:
            add(F.DEMAND, S.REJECTED, 'visits_on_plan', visits)

        if revenue and delta(rate) < 0:
            contracts = [e for e in events if e.event_type == 'payer_contract_change']
            mix = valid_metric('COMMERCIAL_PAYER_MIX')
            if contracts and mix is not None and delta(mix) < 0:
                add(F.REVENUE, S.SUPPORTED, 'rate_and_mix_reduce_revenue', target, visits, rate, mix, *contracts)
                timing.extend(event_timing(e) for e in contracts)
                questions.append('verify_rate_mix_persistence')
            else:
                add(F.REVENUE, S.CANDIDATE, 'rate_change_needs_evidence', target, rate)
                questions.append('validate_rate_change')
        direct = (F.DEMAND, F.REVENUE) if revenue else (F.DEMAND,)

    elif target.item_id == 'EXP_CLINICAL_LABOR':
        overtime = valid_metric('OVERTIME_HOURS')
        vacancies = [e for e in events if e.event_type == 'temporary_staffing_vacancy']
        accruals = [e for e in events if e.event_type == 'accrual_timing']
        if target_delta > 0 and overtime is not None and delta(overtime) > 0 and vacancies:
            add(F.WORKFORCE, S.SUPPORTED, 'overtime_increases_expense', target, overtime, *vacancies)
            timing.extend(event_timing(e) for e in vacancies)
            questions.extend(('verify_overtime_normalization', 'quantify_labor_rate_bridge'))
        for event in accruals:
            amount_match = re.search(r'USD ([\d,]+(?:\.\d+)?) labor accrual', event.description)
            amount = Decimal(amount_match.group(1).replace(',', '')) if amount_match else None
            reversals = [v for v in financial_history if v.item_id == target.item_id
                         and v.month == (event.end_date or '')[:7] and v.month > target.month
                         and v.currency == target.currency and delta(v) == -target_delta]
            if amount is not None and target.currency == 'USD' and amount == target_delta:
                add(F.ACCOUNTING, S.SUPPORTED, 'documented_accrual_timing', target, event, *reversals)
                timing.append(event_timing(event))
                additional.extend(reversals)
                contribution = ContributionEstimate(amount, 'USD', 'documented_accrual', references(target, event, *reversals))
                questions.append('verify_accrual_reversal')
            else:
                add(F.ACCOUNTING, S.CANDIDATE, 'accrual_needs_reconciliation', target, event)
                questions.append('reconcile_accrual')
        direct = (F.WORKFORCE, F.ACCOUNTING)
    else:
        metric_rules = {
            'PROVIDER_AVAILABLE_DAYS': (F.PROVIDER, {'provider_pto', 'provider_departure'}, -1),
            'CLINIC_CLOSURE_DAYS': (F.CAPACITY, {'clinic_closure', 'equipment_outage'}, 1),
            'OVERTIME_HOURS': (F.WORKFORCE, {'temporary_staffing_vacancy'}, 1),
            'NET_REVENUE_PER_VISIT': (F.REVENUE, {'payer_contract_change'}, -1),
        }
        rule = metric_rules.get(target.item_id)
        if rule:
            family, kinds, sign = rule
            related = [e for e in events if e.event_type in kinds]
            if related and target_delta * sign > 0:
                add(family, S.SUPPORTED, 'documented_operating_metric_change', target, *related)
                timing.extend(event_timing(e) for e in related)
                questions.append('verify_metric_persistence')
            direct = (family,)
        else:
            add(F.OTHER, S.CANDIDATE, 'unmodeled_business_mechanism', target, *events)
            direct = ()

    ranked = assign_roles(tuple(drivers), direct)
    if not any(d.role == 'primary' for d in ranked):
        if not any(d.epistemic_state == S.UNRESOLVED for d in drivers):
            unresolved('resolve_primary_mechanism')
        ranked = tuple(drivers)
        timing = []
    if sum(d.role == 'contributing' for d in ranked) > 1:
        questions.append('quantify_overlapping_constraints')
    return DriverAssessment(ranked, tuple(timing), tuple(dict.fromkeys(questions)),
                            tuple(dict.fromkeys(additional)), contribution)
