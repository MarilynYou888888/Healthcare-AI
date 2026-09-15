import unittest
from decimal import Decimal
from provider_fpa.scenario import load_baseline, calculate


class BaselineTests(unittest.TestCase):
    def test_approved_baseline_is_calculated_with_exact_financial_outputs(self):
        baseline = load_baseline()
        result = calculate(baseline.assumptions, baseline.month)
        self.assertEqual(result['capacity'], Decimal('1584'))
        self.assertEqual(result['visits'], Decimal('1425.60'))
        self.assertEqual(result['revenue'], Decimal('277992'))
        self.assertEqual(result['labor'], Decimal('78408'))
        self.assertEqual(result['supplies'], Decimal('25660.80'))
        self.assertEqual(result['contribution'], Decimal('173923.20'))
        self.assertEqual(result['operating_income'], Decimal('88923.20'))
        self.assertEqual(baseline.data_kind, 'synthetic')

    def test_invalid_assumptions_do_not_become_plausible_outputs(self):
        baseline=load_baseline()
        for key,value in [('provider_fte',''),('provider_fte','NaN'),('provider_fte','Infinity'),('clinic_days','31'),('clinic_days','1.5'),('utilization','1.01'),('labor_per_visit','-1')]:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                calculate(dict(baseline.assumptions,**{key:value}),baseline.month)
        for month in ['2026-13','bad','0000-01']:
            with self.assertRaises(ValueError):calculate(baseline.assumptions,month)

    def test_immutable_baseline_and_zero_volume(self):
        baseline=load_baseline()
        with self.assertRaises(TypeError):baseline.assumptions['provider_fte']='0'
        result=calculate(dict(baseline.assumptions,provider_fte='0'),baseline.month)
        self.assertEqual(result['operating_income'],Decimal('-85000'))
        self.assertEqual(result['revenue'],Decimal('0'))
        self.assertEqual(baseline.assumptions['provider_fte'],'4.0')

    def test_public_data_cannot_be_loaded_as_a_synthetic_baseline(self):
        import json,tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'public.json'
            path.write_text(json.dumps(dict(data_kind='public_benchmark')))
            with self.assertRaises(ValueError):load_baseline(path)
