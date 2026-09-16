import json
import unittest
from dataclasses import replace
from pathlib import Path

from provider_fpa.engine import investigate
from provider_fpa.loading import load_datasets
from provider_fpa.narrative import (
    DeterministicNarrativeFormatter,
    NarrativeInput,
    NarrativeGuardrailError,
    NarrativeOutput,
    OpenAINarrativeProvider,
    build_prompt,
    generate_narrative,
    validate_narrative,
)


ROOT = Path(__file__).resolve().parents[1] / 'data/synthetic_benchmark'


class NarrativeLayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_datasets(ROOT / 'inputs')

    def result(self, clinic, month):
        return investigate(self.data, clinic, month, 'REV_NET_PATIENT')

    def test_typed_fallback_has_required_management_sections(self):
        result = self.result('CL001', '2026-03')
        output = generate_narrative(result)
        self.assertIsInstance(output, NarrativeOutput)
        self.assertEqual([section.title for section in output.sections], [
            'Executive Summary', 'Key Variances', 'Supported Drivers',
            'Evidence Gaps / Unresolved Drivers', 'Questions for Operations',
            'Forecast Considerations', 'Human Review Required',
        ])
        self.assertEqual(output.provider, 'deterministic-fallback')
        self.assertTrue(output.human_review_required)

    def test_c01_narrative_uses_supported_roles_and_temporary_timing(self):
        output = generate_narrative(self.result('CL001', '2026-03'))
        text = output.as_text()
        self.assertIn('Demand & Volume (primary, Supported Driver)', text)
        self.assertIn('Provider Availability (contributing, Supported Driver)', text)
        self.assertIn('temporary', text)
        self.assertIn('-21060', text)
        self.assertIn('-0.12', text)
        self.assertNotIn('Analyst-Confirmed Cause', text)

    def test_c03_weather_is_only_upstream_context(self):
        output = generate_narrative(self.result('CL003', '2026-05'))
        text = output.as_text()
        self.assertIn('Demand & Volume (primary, Supported Driver)', text)
        self.assertIn('Clinic Capacity & Operations (contributing, Supported Driver)', text)
        self.assertIn('External Disruption (upstream context)', text)
        self.assertNotIn('External Disruption (primary', text)
        self.assertNotIn('Weather is the primary driver', text)

    def test_c04_explicitly_preserves_unresolved_and_forecast_boundary(self):
        output = generate_narrative(self.result('CL004', '2026-06'))
        text = output.as_text()
        self.assertIn('unresolved', text.lower())
        self.assertIn('insufficient evidence', text.lower())
        self.assertIn('before changing the forecast', text.lower())
        self.assertFalse(output.successfully_explained_variance)

    def test_prompt_contains_only_structured_result_data(self):
        result = self.result('CL003', '2026-05')
        prompt = build_prompt(NarrativeInput(result))
        self.assertIn('InvestigationResult', prompt)
        self.assertIn('CL003', prompt)
        self.assertIn('Demand & Volume', prompt)
        self.assertNotIn('cases.json', prompt)
        self.assertNotIn('gold', prompt.lower())
        self.assertNotIn('Please infer', prompt)

    def test_mocked_provider_output_is_accepted_when_it_respects_contract(self):
        result = self.result('CL001', '2026-03')
        fallback = DeterministicNarrativeFormatter().format(NarrativeInput(result))
        provider = OpenAINarrativeProvider(transport=lambda prompt: fallback.to_dict())
        output = generate_narrative(result, provider=provider)
        self.assertEqual(output.provider, 'openai')
        self.assertEqual(output.sections, fallback.sections)

    def test_provider_output_cannot_change_numbers_or_roles(self):
        result = self.result('CL001', '2026-03')
        fallback = DeterministicNarrativeFormatter().format(NarrativeInput(result))
        bad = fallback.to_dict()
        bad['sections'][0]['body'] = 'Revenue was -999999 because Provider Availability caused 100% of it.'
        provider = OpenAINarrativeProvider(transport=lambda prompt: bad)
        with self.assertRaises(NarrativeGuardrailError):
            generate_narrative(result, provider=provider)

    def test_guardrails_reject_new_confirmation_attribution_percentage_and_unresolved_removal(self):
        result = self.result('CL004', '2026-06')
        fallback = DeterministicNarrativeFormatter().format(NarrativeInput(result))
        cases = [
            ('Analyst-Confirmed Cause: Provider Availability.', None),
            ('Provider Availability contributed 40% of the variance.', None),
            ('The cause is known and the forecast should be changed.', None),
        ]
        for injected, _ in cases:
            bad = fallback.to_dict()
            bad['sections'][2]['body'] += ' ' + injected
            with self.subTest(injected=injected), self.assertRaises(NarrativeGuardrailError):
                validate_narrative(result, NarrativeOutput.from_dict(bad))

    def test_guardrails_reject_any_new_percent_not_present_in_structured_result(self):
        result = self.result('CL001', '2026-03')
        fallback = DeterministicNarrativeFormatter().format(NarrativeInput(result))
        bad = fallback.to_dict()
        bad['sections'][0]['body'] += ' The decline was 12%.'
        with self.assertRaises(NarrativeGuardrailError):
            validate_narrative(result, NarrativeOutput.from_dict(bad))

    def test_guardrails_require_explicit_human_review(self):
        result = self.result('CL001', '2026-03')
        fallback = DeterministicNarrativeFormatter().format(NarrativeInput(result))
        with self.assertRaises(NarrativeGuardrailError):
            validate_narrative(result, replace(fallback, human_review_required=False))

    def test_only_one_provider_abstraction_is_exposed(self):
        self.assertEqual(OpenAINarrativeProvider.provider_name, 'openai')

    def test_output_round_trips_as_typed_json(self):
        output = generate_narrative(self.result('CL003', '2026-05'))
        self.assertEqual(NarrativeOutput.from_dict(json.loads(json.dumps(output.to_dict()))), output)


if __name__ == '__main__':
    unittest.main()
