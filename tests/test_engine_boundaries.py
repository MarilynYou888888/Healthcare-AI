import shutil
import tempfile
import unittest
from dataclasses import replace
from decimal import Decimal as D
from pathlib import Path

from provider_fpa.drivers import assign_roles
from provider_fpa.engine import investigate, investigate_clinic_month
from provider_fpa.loading import load_datasets
from provider_fpa.models import Driver, DriverFamily as F, EpistemicState as S


ROOT = Path(__file__).resolve().parents[1] / 'data/synthetic_benchmark'


class EngineBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_datasets(ROOT / 'inputs')

    def update_metric(self, data, item_id, **changes):
        return replace(data, operational_values=tuple(
            replace(v, **changes) if (v.clinic_id, v.month, v.item_id) == ('CL001', '2026-03', item_id) else v
            for v in data.operational_values))

    def test_engine_runs_with_only_five_input_files_and_no_gold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(ROOT / 'inputs', root / 'inputs')
            result = investigate(load_datasets(root / 'inputs'), 'CL001', '2026-03', 'REV_NET_PATIENT')
            self.assertEqual(result.primary_driver, F.DEMAND)

    def test_reconciliation_failure_is_disclosed_without_supported_cause(self):
        data = self.update_metric(self.data, 'NET_REVENUE_PER_VISIT', actual=D(194))
        result = investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertIn(F.DATA_QUALITY, result.upstream_context)
        self.assertIsNone(result.primary_driver)
        self.assertEqual(result.timing.classification, 'unresolved')
        self.assertIn('reconcile_revenue_bridge', result.unresolved_questions)

    def test_invalid_or_missing_operating_input_does_not_become_zero(self):
        data = self.update_metric(self.data, 'PATIENT_VISITS', actual=None, data_quality_issues=('invalid',))
        result = investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertIn(F.DATA_QUALITY, result.upstream_context)
        visits = next(v for v in result.observed_variances if v.item_id == 'PATIENT_VISITS')
        self.assertIsNone(visits.calculation.actual)
        self.assertIsNone(visits.calculation.percentage)

    def test_missing_financial_value_is_not_a_successfully_identified_variance(self):
        data = replace(self.data, financial_values=tuple(replace(v, actual=None)
            if (v.clinic_id, v.month, v.item_id) == ('CL001', '2026-03', 'REV_NET_PATIENT') else v
            for v in self.data.financial_values))
        result = investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertFalse(result.successful_investigation)
        self.assertFalse(result.successfully_explained_variance)

    def test_no_forecast_horizon_uses_labeled_three_month_fallback(self):
        data = replace(self.data, operating_events=tuple(e for e in self.data.operating_events if e.event_type != 'forecast_horizon'))
        result = investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertEqual(result.timing.horizon.basis, 'next_3_month_fallback')
        self.assertEqual((result.timing.horizon.start, result.timing.horizon.end), ('2026-04', '2026-06'))

    def test_ambiguous_forecast_horizon_is_rejected(self):
        event = next(e for e in self.data.operating_events if e.event_type == 'forecast_horizon')
        data = replace(self.data, operating_events=(*self.data.operating_events, replace(event, event_id='F2')))
        with self.assertRaises(ValueError):
            investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')

    def test_operational_target_uses_its_direct_mechanism(self):
        result = investigate(self.data, 'CL001', '2026-03', 'PROVIDER_AVAILABLE_DAYS', 'operational_metric_variance')
        self.assertEqual(result.primary_driver, F.PROVIDER)
        self.assertTrue(result.review_required)
        self.assertEqual(result.variance.calculation.absolute, -2)

    def test_investigates_each_financial_and_operational_variance(self):
        results = investigate_clinic_month(self.data, 'CL001', '2026-03')
        self.assertEqual(len(results), 9)
        self.assertTrue(all(r.clinic_id == 'CL001' and r.month == '2026-03' for r in results))

    def test_primary_selection_does_not_promote_upstream_or_choose_an_arbitrary_tie(self):
        ref = (self.data.financial_values[0].evidence,)
        provider = Driver(F.PROVIDER, None, S.SUPPORTED, 'availability_constrains_visits', ref)
        volume = Driver(F.DEMAND, None, S.SUPPORTED, 'visits_reduce_revenue', ref)
        rate = Driver(F.REVENUE, None, S.SUPPORTED, 'rate_and_mix_reduce_revenue', ref)
        self.assertFalse(any(d.role == 'primary' for d in assign_roles((provider,), (F.DEMAND, F.REVENUE))))
        self.assertFalse(any(d.role == 'primary' for d in assign_roles((volume, rate, provider), (F.DEMAND, F.REVENUE))))
        ranked = assign_roles((provider, volume), (F.DEMAND, F.REVENUE))
        self.assertEqual([(d.driver_family, d.role) for d in ranked], [(F.PROVIDER, 'contributing'), (F.DEMAND, 'primary')])

    def test_adverse_volume_driver_does_not_explain_a_net_favorable_revenue_variance(self):
        data = self.update_metric(self.data, 'NET_REVENUE_PER_VISIT', actual=D(300))
        data = replace(data, financial_values=tuple(replace(v, actual=D(237600))
            if (v.clinic_id, v.month, v.item_id) == ('CL001', '2026-03', 'REV_NET_PATIENT') else v
            for v in data.financial_values))
        result = investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertIsNone(result.primary_driver)
        self.assertTrue(result.unresolved_questions)

    def test_unknown_event_end_does_not_create_temporary_timing(self):
        data = replace(self.data, operating_events=tuple(replace(e, end_date=None)
            if e.event_type == 'provider_pto' and e.clinic_id == 'CL001' else e
            for e in self.data.operating_events))
        self.assertEqual(investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT').timing.classification, 'unresolved')
