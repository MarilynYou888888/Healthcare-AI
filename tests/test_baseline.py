"""Synthetic source boundary. Calculation regressions run in test_scenario.py."""
import json
import tempfile
import unittest
from pathlib import Path
from provider_fpa.scenario import load_baseline


class BaselineTests(unittest.TestCase):
    def test_baseline_source_is_immutable_and_payload_is_detached(self):
        baseline = load_baseline()
        with self.assertRaises(TypeError):
            baseline.assumptions['provider_fte'] = '0'
        payload = baseline.payload()
        payload['assumptions']['provider_fte'] = '0'
        self.assertEqual(baseline.assumptions['provider_fte'], '4.0')
        self.assertEqual(baseline.data_kind, 'synthetic')
        self.assertNotIn('outputs', baseline.payload())

    def test_public_data_cannot_be_loaded_as_a_synthetic_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'public.json'
            path.write_text(json.dumps({'data_kind':'public_benchmark'}))
            with self.assertRaises(ValueError):
                load_baseline(path)
