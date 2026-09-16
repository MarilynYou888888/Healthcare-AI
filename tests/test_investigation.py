import unittest
from dataclasses import replace
from pathlib import Path

from provider_fpa.engine import investigate
from provider_fpa.loading import load_datasets
from provider_fpa.models import DriverFamily as F, EpistemicState as S


INPUTS = Path(__file__).resolve().parents[1] / 'data/synthetic_benchmark/inputs'


class InvestigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_datasets(INPUTS)

    def test_c01_direct_volume_mechanism_and_provider_contributor(self):
        result = investigate(self.data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertEqual(result.primary_driver, F.DEMAND)
        self.assertEqual(result.contributing_drivers, (F.PROVIDER,))
        self.assertTrue(result.review_required)
        self.assertTrue(result.successful_investigation)
        self.assertFalse(result.successfully_explained_variance)
        self.assertTrue(all(d.evidence for d in result.drivers if d.epistemic_state == S.SUPPORTED))

    def test_c03_weather_cannot_be_primary_revenue_driver(self):
        result = investigate(self.data, 'CL003', '2026-05', 'REV_NET_PATIENT')
        self.assertEqual(result.primary_driver, F.DEMAND)
        self.assertEqual(result.contributing_drivers, (F.CAPACITY,))
        self.assertEqual(result.upstream_context, (F.EXTERNAL,))
        self.assertIsNone(result.contribution_estimate)
        self.assertEqual(result.timing.classification, 'temporary')

    def test_c04_remains_unresolved_and_rejects_provider_shortfall(self):
        result = investigate(self.data, 'CL004', '2026-06', 'REV_NET_PATIENT')
        self.assertIsNone(result.primary_driver)
        self.assertEqual(result.timing.classification, 'unresolved')
        self.assertIn((F.PROVIDER, S.REJECTED), {(d.driver_family, d.epistemic_state) for d in result.drivers})
        self.assertIn((F.UNRESOLVED, S.UNRESOLVED), {(d.driver_family, d.epistemic_state) for d in result.drivers})
        self.assertFalse(any(d.epistemic_state == S.SUPPORTED for d in result.drivers))
        self.assertTrue(result.unresolved_questions)
        self.assertTrue(result.successful_investigation)
        self.assertFalse(result.successfully_explained_variance)

    def test_c10_multiple_drivers_have_no_invented_allocation(self):
        result = investigate(self.data, 'CL005', '2026-08', 'REV_NET_PATIENT')
        self.assertEqual(result.primary_driver, F.DEMAND)
        self.assertEqual(set(result.contributing_drivers), {F.PROVIDER, F.CAPACITY})
        self.assertIsNone(result.contribution_estimate)

    def test_missing_visits_are_not_zero_and_block_cause(self):
        result = investigate(self.data, 'CL004', '2026-07', 'REV_NET_PATIENT')
        self.assertIsNone(result.primary_driver)
        self.assertIn(F.DATA_QUALITY, result.upstream_context)
        self.assertFalse(any(v.item_id == 'PATIENT_VISITS' for v in result.observed_variances))

    def test_removing_supporting_events_demotes_the_volume_explanation(self):
        data = replace(self.data, operating_events=tuple(e for e in self.data.operating_events if e.event_type == 'forecast_horizon'))
        result = investigate(data, 'CL001', '2026-03', 'REV_NET_PATIENT')
        self.assertIsNone(result.primary_driver)
        self.assertEqual(result.timing.classification, 'unresolved')

    def test_engine_does_not_depend_on_clinic_identity(self):
        data = replace(self.data,
                       clinics=tuple(replace(c, clinic_id='SYNTHETIC_NEW') for c in self.data.clinics if c.clinic_id == 'CL001'),
                       financial_values=tuple(replace(v, clinic_id='SYNTHETIC_NEW') for v in self.data.financial_values if v.clinic_id == 'CL001'),
                       operational_values=tuple(replace(v, clinic_id='SYNTHETIC_NEW') for v in self.data.operational_values if v.clinic_id == 'CL001'),
                       operating_events=tuple(replace(e, clinic_id='SYNTHETIC_NEW') for e in self.data.operating_events if e.clinic_id == 'CL001'))
        self.assertEqual(investigate(data, 'SYNTHETIC_NEW', '2026-03', 'REV_NET_PATIENT').primary_driver, F.DEMAND)
