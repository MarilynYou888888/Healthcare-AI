import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InvestigationCliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'provider_fpa', *args], cwd=ROOT,
                              capture_output=True, text=True)

    def test_investigate_emits_structured_traceable_result(self):
        process = self.run_cli('investigate', '--inputs', 'data/synthetic_benchmark/inputs',
                               '--clinic', 'CL003', '--month', '2026-05', '--target', 'REV_NET_PATIENT')
        self.assertEqual(process.returncode, 0, process.stderr)
        result = json.loads(process.stdout)
        self.assertEqual(result['primary_driver'], 'Demand & Volume')
        self.assertEqual(result['variance']['absolute'], '-31155')
        self.assertEqual(result['timing_classification'], 'temporary')
        self.assertTrue(result['successful_investigation'])
        self.assertFalse(result['successfully_explained_variance'])
        self.assertTrue(result['drivers'][0]['evidence'][0]['row_selector'])
        closure = next(v for v in result['observed_variances'] if v['id'] == 'CLINIC_CLOSURE_DAYS')
        self.assertIsNone(closure['percentage'])
        self.assertEqual(closure['percentage_unavailable_reason'], 'zero_comparator')

    def test_benchmark_emits_ten_seven_dimension_reports(self):
        process = self.run_cli('benchmark', '--directory', 'data/synthetic_benchmark')
        self.assertEqual(process.returncode, 0, process.stderr)
        report = json.loads(process.stdout)
        self.assertEqual(report['passed_cases'], 10)
        self.assertEqual(report['passed_dimensions'], 70)

    def test_invalid_investigation_has_nonzero_exit(self):
        process = self.run_cli('investigate', '--inputs', 'data/synthetic_benchmark/inputs',
                               '--clinic', 'UNKNOWN', '--month', '2026-05', '--target', 'REV_NET_PATIENT')
        self.assertNotEqual(process.returncode, 0)
