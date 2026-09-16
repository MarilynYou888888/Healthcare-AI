import unittest

from provider_fpa.evidence import transition_driver, confirm_driver, is_successfully_explained
from provider_fpa.models import Driver, DriverFamily as F, EpistemicState as S, HumanDecision, SourceReference


REF = SourceReference('operating_events.csv', (('event_id', 'E1'),), 'synthetic:events')


class EvidenceStateTests(unittest.TestCase):
    def candidate(self):
        return Driver(F.DEMAND, None, S.CANDIDATE, 'volume_mechanism', (REF,))

    def test_supported_transition_requires_evidence(self):
        supported = transition_driver(self.candidate(), S.SUPPORTED, evidence=(REF,))
        self.assertEqual(supported.epistemic_state, S.SUPPORTED)
        with self.assertRaises(ValueError):
            transition_driver(self.candidate(), S.SUPPORTED, evidence=())

    def test_autonomous_confirmation_is_never_allowed(self):
        for state in [S.CANDIDATE, S.SUPPORTED, S.UNRESOLVED, S.REJECTED]:
            driver = Driver(F.DEMAND, None, state, 'volume_mechanism', (REF,))
            with self.assertRaises(ValueError):
                transition_driver(driver, S.CONFIRMED, evidence=(REF,))

    def test_only_supported_driver_can_receive_explicit_human_confirmation(self):
        decision = HumanDecision('synthetic:analyst-review-1', '2026-09-10T12:00:00Z', 'Confirmed after review')
        with self.assertRaises(ValueError):
            confirm_driver(self.candidate(), decision)
        supported = transition_driver(self.candidate(), S.SUPPORTED, evidence=(REF,))
        confirmed = confirm_driver(supported, decision)
        self.assertEqual(confirmed.epistemic_state, S.CONFIRMED)
        self.assertEqual(confirmed.human_decision, decision)
        self.assertTrue(is_successfully_explained(True, (confirmed,), False))
        self.assertFalse(is_successfully_explained(False, (confirmed,), False))
        self.assertFalse(is_successfully_explained(True, (confirmed,), True))
        self.assertFalse(is_successfully_explained(True, (supported,), False))

    def test_rejection_and_unresolved_are_distinct(self):
        self.assertEqual(transition_driver(self.candidate(), S.UNRESOLVED).epistemic_state, S.UNRESOLVED)
        self.assertEqual(transition_driver(self.candidate(), S.REJECTED, evidence=(REF,)).epistemic_state, S.REJECTED)
        with self.assertRaises(ValueError):
            transition_driver(self.candidate(), S.REJECTED, evidence=())

    def test_primary_requires_support_and_confirmation_requires_human_record(self):
        with self.assertRaises(ValueError):
            Driver(F.DEMAND, 'primary', S.CANDIDATE, 'volume_mechanism', (REF,))
        with self.assertRaises(ValueError):
            Driver(F.DEMAND, 'primary', S.CONFIRMED, 'volume_mechanism', (REF,))
