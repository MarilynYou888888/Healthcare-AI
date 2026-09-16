"""Public investigation workspace contract, independent of benchmark gold answers."""
import unittest
from provider_fpa.investigation import investigation_view


class InvestigationWorkspaceTests(unittest.TestCase):
    def test_supported_unresolved_and_upstream_cases_keep_their_boundaries(self):
        supported = investigation_view('C01')
        self.assertEqual(supported['system']['primary_driver'], 'Demand & Volume')
        self.assertEqual(supported['handoffs'][0]['assumption'], 'provider_fte')
        self.assertIsNone(supported['system']['contribution_estimate'])
        unresolved = investigation_view('C04')
        self.assertIsNone(unresolved['system']['primary_driver'])
        self.assertEqual(unresolved['system']['timing_classification'], 'unresolved')
        self.assertEqual(unresolved['handoffs'], [])
        self.assertIn('insufficient evidence', str(unresolved['narrative']).lower())
        weather = investigation_view('C03')
        self.assertEqual(weather['system']['primary_driver'], 'Demand & Volume')
        self.assertIn('Clinic Capacity & Operations', weather['system']['contributing_drivers'])
        external = next(d for d in weather['system']['drivers'] if d['driver_family'] == 'External Disruption')
        self.assertEqual((external['role'], external['epistemic_state']), ('upstream_context', 'observed_fact'))
        self.assertEqual(weather['handoffs'][0]['assumption'], 'clinic_days')
        self.assertIn('offline', weather['narrative_disclosure'].lower())

    def test_human_decisions_are_explicit_scoped_and_do_not_rewrite_system_output(self):
        from provider_fpa.investigation import review_investigation
        base = investigation_view('C01')
        provider = next(i for i, d in enumerate(base['system']['drivers']) if d['driver_family'] == 'Provider Availability')
        def review(action):
            return review_investigation(base['context'], base['snapshot_id'],
                                       {str(provider): {'action': action, 'rationale': 'Reviewed schedule evidence.'}})
        confirmed = review('confirm')
        self.assertEqual(confirmed['reviewed']['drivers'][provider]['epistemic_state'], 'analyst_confirmed_cause')
        self.assertTrue(confirmed['reviewed']['successfully_explained_variance'])
        self.assertTrue(confirmed['reviewed']['drivers'][provider]['human_decision']['review_reference'])
        self.assertEqual(confirmed['system'], base['system'])
        self.assertEqual(confirmed['narrative'], base['narrative'])
        rejected = review('reject')
        self.assertEqual(rejected['reviewed']['drivers'][provider]['epistemic_state'], 'rejected_driver')
        self.assertEqual(rejected['handoffs'], [])
        unresolved = review('keep_unresolved')
        self.assertEqual(unresolved['reviewed']['drivers'][provider]['epistemic_state'], 'unresolved_driver')
        self.assertEqual(unresolved['handoffs'], [])
        requested = review('request_investigation')
        self.assertEqual(requested['reviewed']['drivers'][provider]['epistemic_state'], 'supported_driver')
        self.assertEqual(requested['decisions'][str(provider)]['action'], 'request_investigation')
        self.assertFalse(requested['reviewed']['successfully_explained_variance'])
        self.assertEqual(investigation_view('C01')['system'], base['system'])
        with self.assertRaises(ValueError):
            review_investigation(base['context'], 'stale', {str(provider): {'action': 'confirm'}})
        c04 = investigation_view('C04')
        for index in range(len(c04['system']['drivers'])):
            with self.assertRaises(ValueError):
                review_investigation(c04['context'], c04['snapshot_id'], {str(index): {'action': 'confirm'}})
        c03 = investigation_view('C03')
        external = next(i for i,d in enumerate(c03['system']['drivers']) if d['driver_family'] == 'External Disruption')
        with self.assertRaises(ValueError):
            review_investigation(c03['context'], c03['snapshot_id'], {str(external): {'action': 'confirm'}})

    def test_queue_lineage_all_cases_and_configurable_policy(self):
        from provider_fpa.investigation import investigation_catalog
        catalog = investigation_catalog()
        self.assertEqual(len(catalog), 10)
        self.assertTrue(all('review_queue' not in case for case in catalog))
        for case in catalog:
            view = investigation_view(case['case_id'])
            self.assertTrue(view['system']['review_required'])
            for fact in view['system']['observed_facts']:
                self.assertTrue(fact['evidence'])
                self.assertTrue(all(e['source'] and e['input_file'] and e['row_selector'] for e in fact['evidence']))
        view = investigation_view('C01')
        excluded = next(t for t in view['targets'] if not t['required'])
        overridden = investigation_view('C01', excluded['id'], excluded['type'], True)
        self.assertIn('analyst_override', overridden['system']['review']['reasons'])
        self.assertTrue(overridden['system']['review_required'])
        self.assertEqual(view['policy']['structural_horizon_fraction'], .5)
        self.assertIn('not a universal', view['policy']['disclosure'])

    def test_horizon_policy_is_forwarded_without_changing_historical_default(self):
        from provider_fpa.engine import investigate
        from provider_fpa.loading import load_datasets
        from pathlib import Path
        data = load_datasets(Path('data/synthetic_benchmark/inputs'))
        horizon = next(e for e in data.operating_events if e.clinic_id == 'CL002' and e.event_type == 'forecast_horizon')
        # The recovered classifier's exact 50% boundary is checked independently.
        from provider_fpa.models import ForecastHorizon, TimingEvidence
        from provider_fpa.timing import classify_timing
        signal = TimingEvidence(None, '2026-06', False, (horizon.evidence,))
        four_months = ForecastHorizon('2026-05', '2026-08', 'latest_approved_forecast', (horizon.evidence,))
        self.assertEqual(classify_timing(four_months, (signal,), material_fraction=.5).classification, 'structural')
        self.assertEqual(classify_timing(four_months, (signal,), material_fraction=.5001).classification, 'unresolved')
        with self.assertRaises(ValueError):
            investigate(data, 'CL002', '2026-04', 'REV_NET_PATIENT', material_fraction=0)

    def test_web_analysis_needs_no_gold_files(self):
        import shutil
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from provider_fpa.investigation import BENCHMARK
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(BENCHMARK / 'inputs', root / 'inputs')
            shutil.copyfile(BENCHMARK / 'cases.json', root / 'cases.json')
            with patch('provider_fpa.investigation.BENCHMARK', root):
                self.assertIsNone(investigation_view('C04')['system']['primary_driver'])

    def test_guarded_commentary_failure_does_not_hide_facts_or_analyst_override(self):
        view = investigation_view('C01', 'CLINIC_CLOSURE_DAYS', 'operational_metric_variance')
        self.assertFalse(view['system']['review_required'])
        self.assertEqual(view['narrative_status'], 'withheld')
        self.assertEqual(view['narrative']['sections'], [])
        overridden = investigation_view('C01', 'CLINIC_CLOSURE_DAYS', 'operational_metric_variance', True)
        self.assertTrue(overridden['system']['review_required'])
        self.assertEqual(overridden['system']['variance']['absolute'], '0')
        self.assertEqual(overridden['narrative_status'], 'withheld')
        guarded = investigation_view('C04', 'PROVIDER_AVAILABLE_DAYS', 'operational_metric_variance')
        self.assertEqual(guarded['narrative_status'], 'withheld')
        self.assertTrue(guarded['system']['observed_facts'])
