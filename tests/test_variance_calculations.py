import unittest
from decimal import Decimal

from provider_fpa.calculations import calculate_variance


class VarianceCalculationTests(unittest.TestCase):
    def test_financial_shortfall_uses_exact_decimal_arithmetic(self):
        result = calculate_variance(Decimal('154440'), Decimal('175500'))
        self.assertEqual(result.absolute, Decimal('-21060'))
        self.assertEqual(result.percentage, Decimal('-0.12'))

    def test_zero_or_missing_comparator_has_no_percentage(self):
        for actual, comparator, absolute in [(10, 0, 10), (0, 0, 0), (10, None, None), (None, 10, None)]:
            with self.subTest(actual=actual, comparator=comparator):
                result = calculate_variance(actual, comparator)
                self.assertEqual(result.absolute, absolute)
                self.assertIsNone(result.percentage)
                self.assertIsNotNone(result.percentage_unavailable_reason)

    def test_negative_comparator_keeps_signed_ratio(self):
        result = calculate_variance(-80, -100)
        self.assertEqual(result.absolute, 20)
        self.assertEqual(result.percentage, Decimal('-0.2'))

    def test_invalid_numbers_are_not_reported_as_variances(self):
        for value in ['NaN', 'Infinity', '-Infinity', 'not a number']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                calculate_variance(value, 100)

    def test_decimal_fraction_and_on_plan(self):
        self.assertEqual(calculate_variance('0.3', '0.1').absolute, Decimal('0.2'))
        self.assertEqual(calculate_variance(100, 100).percentage, 0)
