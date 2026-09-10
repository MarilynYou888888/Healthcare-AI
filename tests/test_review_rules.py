import unittest
from decimal import Decimal as D

from provider_fpa.calculations import calculate_variance
from provider_fpa.models import ReviewRule, SourceReference
from provider_fpa.review import evaluate_review


SOURCE = SourceReference('review_rules.csv', (('rule_id', 'R1'),), 'synthetic:policy')


class ReviewRuleTests(unittest.TestCase):
    def rule(self, **changes):
        fields = dict(rule_id='R1', target_id='REV', absolute_threshold=D(100),
                      percentage_threshold=D('.1'), always_review=False,
                      effective_from='2026-01', effective_to=None, evidence=SOURCE)
        return ReviewRule(**(fields | changes))

    def test_either_threshold_triggers_and_retains_rule_lineage(self):
        for actual, expected, reason in [(1201, 1000, 'absolute_threshold'), (12, 10, 'percentage_threshold')]:
            result = evaluate_review('REV', '2026-06', calculate_variance(actual, expected), (self.rule(),))
            self.assertTrue(result.required)
            self.assertIn(reason, result.reasons)
            self.assertEqual(result.evidence, (SOURCE,))

    def test_locked_exceeds_semantics_do_not_trigger_at_equality(self):
        self.assertFalse(evaluate_review('REV', '2026-06', calculate_variance(1100, 1000), (self.rule(),)).required)

    def test_critical_rule_and_analyst_override(self):
        self.assertTrue(evaluate_review('REV', '2026-06', calculate_variance(0, 0), (self.rule(always_review=True),)).required)
        self.assertTrue(evaluate_review('REV', '2026-06', calculate_variance(0, 0), (), analyst_override=True).required)

    def test_zero_denominator_uses_absolute_rule_only(self):
        result = evaluate_review('REV', '2026-06', calculate_variance(101, 0), (self.rule(),))
        self.assertEqual(result.reasons, ('absolute_threshold',))

    def test_scope_dates_and_missing_values(self):
        for target, month in [('OTHER', '2026-06'), ('REV', '2025-12'), ('REV', '2026-08')]:
            self.assertFalse(evaluate_review(target, month, calculate_variance(1000, 1),
                                            (self.rule(effective_to='2026-07'),)).required)
        self.assertFalse(evaluate_review('REV', '2026-06', calculate_variance(None, 1), (self.rule(),)).required)

    def test_negative_threshold_rejected(self):
        with self.assertRaises(ValueError):
            self.rule(absolute_threshold=D(-1))
