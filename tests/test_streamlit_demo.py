import unittest
from pathlib import Path

from streamlit_app import CASE_OPTIONS, build_demo_model, load_case_result


ROOT = Path(__file__).resolve().parents[1]


class StreamlitDemoTests(unittest.TestCase):
    def test_case_selector_exposes_the_three_requested_scenarios(self):
        self.assertEqual(tuple(CASE_OPTIONS), ('C01', 'C03', 'C04'))
        self.assertEqual(CASE_OPTIONS['C01']['label'], 'C01 — Provider PTO')
        self.assertEqual(CASE_OPTIONS['C03']['label'], 'C03 — Weather / Clinic Closure')
        self.assertEqual(CASE_OPTIONS['C04']['label'], 'C04 — Unresolved Volume Miss')

    def test_view_model_reuses_engine_and_narrative_boundaries(self):
        for case_id, expected in {
            'C01': ('Demand & Volume', 'Temporary'),
            'C03': ('Demand & Volume', 'Temporary'),
            'C04': (None, 'Unresolved'),
        }.items():
            with self.subTest(case_id=case_id):
                result = load_case_result(case_id, ROOT / 'data/synthetic_benchmark')
                model = build_demo_model(result)
                self.assertEqual(model['primary_driver'], expected[0])
                self.assertEqual(model['timing'], expected[1])
                self.assertTrue(model['review_required'])
                self.assertTrue(model['narrative']['sections'])

    def test_c03_view_model_keeps_weather_upstream_context(self):
        model = build_demo_model(load_case_result('C03', ROOT / 'data/synthetic_benchmark'))
        self.assertNotIn('External Disruption', model['primary_driver'] or '')
        self.assertIn('External Disruption', model['upstream_context'])
        self.assertIn('weather', model['evidence_text'].lower())

    def test_c04_view_model_makes_insufficient_evidence_visible(self):
        model = build_demo_model(load_case_result('C04', ROOT / 'data/synthetic_benchmark'))
        self.assertTrue(model['unresolved'])
        self.assertIn('insufficient', model['evidence_text'].lower())
        self.assertIn('before changing the forecast', model['narrative_text'].lower())


if __name__ == '__main__':
    unittest.main()
