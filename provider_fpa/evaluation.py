"""Independent gold-contract evaluator. This module is never imported by the engine."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_EVEN
import json
from pathlib import Path
from typing import Callable

from provider_fpa.engine import investigate
from provider_fpa.loading import load_datasets
from provider_fpa.models import Datasets, DriverFamily as F, EpistemicState as S, InvestigationResult


@dataclass(frozen=True)
class EvaluationReport:
    case_id: str
    dimensions: tuple[tuple[str, bool], ...]
    mismatches: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return all(passed for _, passed in self.dimensions)


def _active(result: InvestigationResult, family: F) -> bool:
    return any(d.driver_family == family and d.epistemic_state in (S.SUPPORTED, S.CONFIRMED)
               for d in result.drivers)


# Each prohibited claim has a structural predicate. This catches semantic errors
# even when a forbidden sentence never appears. New gold prohibitions fail closed
# until explicitly supported here, rather than silently receiving a passing score.
FORBIDDEN: dict[str, Callable[[InvestigationResult], bool]] = {
    'Provider PTO caused 100% of the revenue decline.': lambda r: r.contribution_estimate is not None,
    'Revenue will permanently remain at the April level.': lambda r: any('permanent' in d.mechanism.lower() for d in r.drivers),
    'Weather is the primary driver of the revenue variance.': lambda r: r.primary_driver == F.EXTERNAL,
    'The closure caused 100% of the revenue decline.': lambda r: r.contribution_estimate is not None,
    'Lower provider availability caused the decline.': lambda r: _active(r, F.PROVIDER),
    'The volume miss is temporary.': lambda r: r.timing.classification == 'temporary',
    'Overtime explains the entire expense variance without an applicable labor-rate bridge.': lambda r: r.contribution_estimate is not None,
    'Lower visit volume caused the revenue variance.': lambda r: _active(r, F.DEMAND),
    'The July expense variance reflects a permanent labor run-rate increase.': lambda r: r.timing.structural or _active(r, F.WORKFORCE),
    'The missing visit record means patient volume was zero.': lambda r: any(v.item_id == 'PATIENT_VISITS' and v.calculation.actual == 0 for v in r.observed_variances),
    'Provider availability caused the revenue decline.': lambda r: _active(r, F.PROVIDER),
    'The recurring August decline is a structural demand reduction.': lambda r: r.timing.structural,
    'Provider availability caused 60% of the revenue decline.': lambda r: r.contribution_estimate is not None,
    'The equipment outage caused 40% of the revenue decline.': lambda r: r.contribution_estimate is not None,
}


def _observed_subject(result: InvestigationResult, subject: str) -> bool:
    def comparison(item_id: str, relation: str) -> bool:
        for fact in result.observed_facts:
            if fact.fact_type == 'value_comparison' and fact.subject_id == item_id:
                values = dict(fact.values)
                if values.get('actual') is None or values.get('comparator') is None:
                    continue
                actual, comparator = Decimal(values['actual']), Decimal(values['comparator'])
                if (actual < comparator if relation == 'less' else actual == comparator):
                    return True
        return False

    if subject == 'Patient visits below expected':
        return comparison('PATIENT_VISITS', 'less')
    if subject == 'Provider availability was on plan':
        return comparison('PROVIDER_AVAILABLE_DAYS', 'equal')
    if subject == 'Weather closed the clinic for two days':
        return any(f.fact_type == 'reported_event' and dict(f.values).get('event_type') == 'clinic_closure'
                   and 'two days' in dict(f.values).get('description', '')
                   and 'weather' in dict(f.values).get('description', '') for f in result.observed_facts)
    if subject == 'July patient-visit input is missing':
        return (not any(v.item_id == 'PATIENT_VISITS' for v in result.observed_variances)
                and any(dict(f.values).get('event_type') == 'data_feed_failure' for f in result.observed_facts))
    return False


def _lineage_valid(result: InvestigationResult, expected: dict, data: Datasets) -> bool:
    records = (*data.clinics, *data.financial_values, *data.operational_values,
               *data.operating_events, *data.review_rules)
    known = {record.evidence for record in records}
    refs = set(result.variance.evidence + result.review.evidence + result.timing.horizon.evidence + result.timing.evidence)
    for item in (*result.observed_facts, *result.observed_variances, *result.drivers):
        if not item.evidence:
            return False
        refs.update(item.evidence)
    if result.contribution_estimate:
        refs.update(result.contribution_estimate.evidence)
    if not refs.issubset(known):
        return False
    for gold in expected['supporting_evidence']:
        if not any(ref.input_file == gold['input_file'] and ref.source == gold['source']
                   and dict(ref.row_selector) == gold['row_selector'] for ref in refs):
            return False
    # Source existence alone is insufficient: verify the factual payload too.
    values = {v.evidence: v for v in (*data.financial_values, *data.operational_values)}
    events = {e.evidence: e for e in data.operating_events}
    for fact in result.observed_facts:
        payload = dict(fact.values)
        if fact.fact_type == 'value_comparison':
            value = values.get(fact.evidence[0])
            if value is None or payload != {
                'month': value.month, 'actual': str(value.actual) if value.actual is not None else None,
                'comparator': str(value.comparator) if value.comparator is not None else None,
            } or fact.subject_id != value.item_id:
                return False
        elif fact.fact_type == 'reported_event':
            event = events.get(fact.evidence[0])
            if event is None or payload != {
                'event_type': event.event_type, 'description': event.description,
                'start_date': event.start_date, 'end_date': event.end_date,
            } or fact.subject_id != event.event_id:
                return False
    return True


def evaluate(result: InvestigationResult, fixture: dict, data: Datasets) -> EvaluationReport:
    expected = fixture['expected']
    checks: dict[str, bool] = {}
    lookup = {(v.variance_type, v.item_id): v for v in result.observed_variances}
    observed_ok = result.variance == lookup.get((result.variance.variance_type, result.variance.item_id))
    observed_ok &= (result.clinic_id == fixture['target']['clinic_id'] and result.month == fixture['target']['month']
                    and result.variance.item_id == fixture['target']['target_id'])
    source_values = {v.evidence: v for v in (*data.financial_values, *data.operational_values)}
    observed_ok &= len(lookup) == len(result.observed_variances)
    for actual in result.observed_variances:
        source = source_values.get(actual.evidence[0]) if actual.evidence else None
        if (source is None or source.clinic_id != result.clinic_id or source.month != result.month
                or source.item_id != actual.item_id):
            observed_ok = False
            continue
        expected_absolute = (source.actual - source.comparator
                             if source.actual is not None and source.comparator is not None else None)
        expected_percentage = (expected_absolute / source.comparator
                               if expected_absolute is not None and source.comparator != 0 else None)
        calculation = actual.calculation
        observed_ok &= (calculation.actual == source.actual and calculation.forecast_or_expected == source.comparator
                        and calculation.absolute == expected_absolute and calculation.percentage == expected_percentage
                        and actual.unit == source.unit and actual.currency == source.currency)
    for gold in expected['observed_variance']:
        actual = lookup.get((gold['variance_type'], gold['id']))
        if actual is None:
            observed_ok = False
            continue
        calculation = actual.calculation
        for key in ('actual', 'forecast_or_expected', 'absolute', 'percentage'):
            value = getattr(calculation, key)
            comparator = Decimal(str(gold[key])) if gold[key] is not None else None
            if key == 'percentage' and value is not None:
                value = value.quantize(Decimal('.0001'), rounding=ROUND_HALF_EVEN)
            observed_ok &= value == comparator
        observed_ok &= actual.direction == gold['direction']
    checks['observed_variance'] = bool(observed_ok)

    families = {d.driver_family.value for d in result.drivers
                if d.role is not None and d.epistemic_state != S.REJECTED}
    if not families:
        families = {d.driver_family.value for d in result.drivers if d.epistemic_state == S.UNRESOLVED}
    checks['expected_driver_family'] = families == set(expected['expected_driver_family'])
    roles = expected['driver_roles']
    checks['driver_roles'] = (result.primary_driver == roles['primary']
                              and set(result.contributing_drivers) == set(roles['contributing'])
                              and set(result.upstream_context) == set(roles['upstream_context']))
    timing = expected['timing_classification']
    horizon_source = timing['forecast_horizon_source']
    checks['timing_classification'] = (
        result.timing.classification == timing['classification']
        and result.timing.recurring == timing['recurring']
        and result.timing.structural == timing['structural']
        and result.timing.horizon.end == timing['forecast_horizon_end']
        and result.timing.horizon.basis == 'latest_approved_forecast'
        and any(dict(ref.row_selector).get('event_id') == horizon_source['event_id']
                and ref.source == horizon_source['source'] for ref in result.timing.horizon.evidence)
    )
    pairs = {(d.driver_family.value, d.epistemic_state.value) for d in result.drivers}
    epistemic_ok = not any(d.epistemic_state == S.CONFIRMED for d in result.drivers)
    for state in expected['epistemic_state']:
        if 'driver_family' in state:
            epistemic_ok &= (state['driver_family'], state['state']) in pairs
        else:
            epistemic_ok &= state['state'] == 'observed_fact' and _observed_subject(result, state['subject'])
    epistemic_ok &= all(f.epistemic_state == S.OBSERVED for f in result.observed_facts)
    epistemic_ok &= _lineage_valid(result, expected, data)
    success = expected['success_criteria']
    epistemic_ok &= result.successful_investigation == success['successful_investigation']
    epistemic_ok &= result.successfully_explained_variance == success['successfully_explained_variance_before_human_review']
    checks['epistemic_state'] = bool(epistemic_ok)
    human = expected['human_review_requirement']
    checks['human_review_requirement'] = (result.human_review_required == human['required']
                                           and result.review_required
                                           and result.analyst_status == human['analyst_status_at_system_output'])
    forbidden_ok = True
    for claim in expected['forbidden_conclusion']:
        predicate = FORBIDDEN.get(claim)
        forbidden_ok &= predicate is not None and not predicate(result)
        # No unconstrained narrative is generated. Still reject verbatim claims
        # if an altered producer puts one in a conclusion/mechanism field.
        forbidden_ok &= not any(claim.lower() in d.mechanism.lower() for d in result.drivers
                                if d.epistemic_state not in (S.REJECTED, S.UNRESOLVED))
    checks['forbidden_conclusions'] = bool(forbidden_ok)
    return EvaluationReport(fixture['case_id'], tuple(checks.items()),
                            tuple(f'{name}: contract mismatch' for name, passed in checks.items() if not passed))


def run_benchmark(directory: str | Path) -> tuple[EvaluationReport, ...]:
    root = Path(directory)
    data = load_datasets(root / 'inputs')
    cases = json.loads((root / 'cases.json').read_text())
    reports = []
    for case in cases:
        # Selection metadata and gold content are never passed to the engine.
        result = investigate(data, case['clinic_id'], case['month'], case['target_id'], case['target_type'])
        gold = json.loads((root / 'gold' / f"{case['case_id']}.json").read_text())
        reports.append(evaluate(result, gold, data))
    return tuple(reports)
