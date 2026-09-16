import unittest

from provider_fpa.models import ForecastHorizon, TimingEvidence, SourceReference
from provider_fpa.timing import classify_timing, fallback_horizon


REF = SourceReference('operating_events.csv', (('event_id', 'E1'),), 'synthetic:events')


class TimingTests(unittest.TestCase):
    def test_normalization_before_horizon_is_temporary_even_when_recurring(self):
        horizon = ForecastHorizon('2026-09', '2026-12', 'latest_approved_forecast', (REF,))
        result = classify_timing(horizon, (TimingEvidence('2026-09', None, True, (REF,)),))
        self.assertEqual(result.classification, 'temporary')
        self.assertTrue(result.recurring)
        self.assertFalse(result.structural)
        self.assertEqual(result.evidence, (REF,))

    def test_supported_persistence_over_material_horizon_is_structural(self):
        horizon = ForecastHorizon('2026-09', '2026-12', 'latest_approved_forecast', (REF,))
        self.assertEqual(classify_timing(horizon, (TimingEvidence(None, '2026-12', False, (REF,)),)).classification, 'structural')

    def test_missing_or_conflicting_duration_stays_unresolved(self):
        horizon = fallback_horizon('2026-08')
        self.assertEqual(classify_timing(horizon, ()).classification, 'unresolved')
        self.assertEqual(classify_timing(horizon, (TimingEvidence(None, None, True, (REF,)),)).classification, 'unresolved')
        self.assertEqual(classify_timing(horizon, (TimingEvidence('2026-09', '2026-11', False, (REF,)),)).classification, 'unresolved')

    def test_fallback_is_explicit_and_rolls_over_year_end(self):
        horizon = fallback_horizon('2026-11')
        self.assertEqual((horizon.start, horizon.end), ('2026-12', '2027-02'))
        self.assertEqual(horizon.basis, 'next_3_month_fallback')

    def test_unresolved_driver_does_not_disappear_in_mixed_timing(self):
        horizon = fallback_horizon('2026-08')
        result = classify_timing(horizon, (TimingEvidence('2026-09', None, False, (REF,)), TimingEvidence(None, None, False, (REF,))))
        self.assertEqual(result.classification, 'unresolved')
