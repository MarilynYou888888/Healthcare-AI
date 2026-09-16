import json
import unittest
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from provider_fpa.engine import investigate
from provider_fpa.evaluation import evaluate, run_benchmark
from provider_fpa.loading import load_datasets
from provider_fpa.models import Driver, DriverFamily as F, EpistemicState as S, HumanDecision


ROOT = Path(__file__).resolve().parents[1] / 'data/synthetic_benchmark'


class BenchmarkEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_datasets(ROOT / 'inputs')

    def case(self, case_id):
        gold = json.loads((ROOT / 'gold' / f'{case_id}.json').read_text())
        target = gold['target']
        return investigate(self.data, target['clinic_id'], target['month'], target['target_id']), gold

    def test_all_ten_cases_pass_all_seven_dimensions(self):
        reports = run_benchmark(ROOT)
        self.assertEqual(len(reports), 10)
        for report in reports:
            with self.subTest(case=report.case_id):
                self.assertEqual(len(report.dimensions), 7)
                self.assertTrue(report.passed, report.mismatches)

    def test_evaluator_detects_corrupted_variance_timing_and_review(self):
        result, gold = self.case('C01')
        bad_variance = replace(result.variance, calculation=replace(result.variance.calculation, absolute=Decimal(99)))
        corrupted = replace(result, variance=bad_variance,
                            observed_variances=(bad_variance, *result.observed_variances[1:]),
                            timing=replace(result.timing, classification='structural', structural=True),
                            review=replace(result.review, required=False))
        report = evaluate(corrupted, gold, self.data)
        for dimension in ['observed_variance', 'timing_classification', 'human_review_requirement']:
            self.assertFalse(dict(report.dimensions)[dimension])

    def test_evaluator_detects_weather_as_primary_even_without_forbidden_sentence(self):
        result, gold = self.case('C03')
        drivers = tuple(replace(d, role=None) for d in result.drivers if d.driver_family != F.EXTERNAL)
        weather = next(d for d in result.drivers if d.driver_family == F.EXTERNAL)
        corrupted = replace(result, drivers=(*drivers, replace(weather, role='primary', epistemic_state=S.SUPPORTED)))
        report = evaluate(corrupted, gold, self.data)
        self.assertFalse(dict(report.dimensions)['driver_roles'])
        self.assertFalse(dict(report.dimensions)['forbidden_conclusions'])

    def test_evaluator_detects_fabricated_c04_cause(self):
        result, gold = self.case('C04')
        fabricated = Driver(F.PROVIDER, 'primary', S.SUPPORTED, 'availability_constrains_visits', result.variance.evidence)
        report = evaluate(replace(result, drivers=(fabricated,)), gold, self.data)
        self.assertFalse(dict(report.dimensions)['epistemic_state'])
        self.assertFalse(dict(report.dimensions)['forbidden_conclusions'])

    def test_evaluator_rejects_confirmation_in_autonomous_output(self):
        result, gold = self.case('C01')
        drivers = tuple(replace(d, epistemic_state=S.CONFIRMED,
                                human_decision=HumanDecision('synthetic:review', '2026-09-10', 'reviewed'))
                        if d.role == 'primary' else d for d in result.drivers)
        report = evaluate(replace(result, drivers=drivers), gold, self.data)
        self.assertFalse(dict(report.dimensions)['epistemic_state'])

    def test_evaluator_detects_missing_required_fact_and_lineage(self):
        result, gold = self.case('C01')
        corrupted = replace(result, observed_facts=tuple(f for f in result.observed_facts if f.subject_id != 'PATIENT_VISITS'))
        self.assertFalse(dict(evaluate(corrupted, gold, self.data).dimensions)['epistemic_state'])

    def test_unknown_forbidden_contract_fails_closed(self):
        result, gold = self.case('C01')
        gold['expected']['forbidden_conclusion'].append('A new unsupported claim without an evaluator predicate.')
        self.assertFalse(dict(evaluate(result, gold, self.data).dimensions)['forbidden_conclusions'])

    def test_evaluator_checks_extra_variances_including_undefined_percentages(self):
        result, gold = self.case('C03')
        variances = tuple(replace(v, calculation=replace(v.calculation, percentage=Decimal(0)))
                          if v.item_id == 'CLINIC_CLOSURE_DAYS' else v for v in result.observed_variances)
        report = evaluate(replace(result, observed_variances=variances), gold, self.data)
        self.assertFalse(dict(report.dimensions)['observed_variance'])

    def test_evaluator_rejects_forged_source_even_when_numbers_match(self):
        result, gold = self.case('C01')
        driver = next(d for d in result.drivers if d.role == 'primary')
        forged = replace(driver, evidence=(replace(driver.evidence[0], source='synthetic:nonexistent'),))
        corrupted = replace(result, drivers=tuple(forged if d == driver else d for d in result.drivers))
        self.assertFalse(dict(evaluate(corrupted, gold, self.data).dimensions)['epistemic_state'])
