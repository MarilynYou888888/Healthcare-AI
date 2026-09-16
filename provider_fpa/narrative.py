"""AI Narrative Layer for validated Clinic-Month InvestigationResults.

The deterministic engine owns every value, classification, evidence state, and
timing decision. This module may only render those decisions into commentary.
Provider output is treated as untrusted wording and is accepted only after the
same result-bound guardrails pass.
"""

from dataclasses import dataclass
import json
import re
from typing import Any, Callable, Protocol

from provider_fpa.models import DriverFamily as F, EpistemicState as S, InvestigationResult
from provider_fpa.presentation import QUESTIONS, investigation_payload


SECTION_TITLES = (
    'Executive Summary', 'Key Variances', 'Supported Drivers',
    'Evidence Gaps / Unresolved Drivers', 'Questions for Operations',
    'Forecast Considerations', 'Human Review Required',
)
_NUMBER = re.compile(r'(?<![A-Za-z])[-+]?\d+(?:\.\d+)?%?')
_ATTRIBUTION = re.compile(r'\b(?:caused|contributed|attributable|explains?)\b[^.\n]{0,100}\b\d+(?:\.\d+)?%', re.I)
_CONFIRMED = re.compile(r'analyst[- ]confirmed\s+cause|confirmed\s+(?:cause|driver)', re.I)
_FORECAST_WRITE = re.compile(r'\b(?:forecast|assumption)[^.\n]{0,40}\b(?:will|should|must)\s+(?:be\s+)?(?:changed|updated|modified|approved)\b', re.I)


class NarrativeGuardrailError(ValueError):
    """Raised when provider wording violates the deterministic contract."""


@dataclass(frozen=True)
class NarrativeInput:
    investigation: InvestigationResult


@dataclass(frozen=True)
class NarrativeSection:
    title: str
    body: str

    def __post_init__(self):
        if not self.title or not self.body.strip():
            raise ValueError('Narrative sections require a title and body')

    def to_dict(self) -> dict[str, str]:
        return {'title': self.title, 'body': self.body}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> 'NarrativeSection':
        if not isinstance(value, dict) or not isinstance(value.get('title'), str) or not isinstance(value.get('body'), str):
            raise ValueError('Invalid narrative section')
        return cls(value['title'], value['body'])


@dataclass(frozen=True)
class NarrativeOutput:
    clinic_id: str
    month: str
    provider: str
    sections: tuple[NarrativeSection, ...]
    human_review_required: bool
    successfully_explained_variance: bool

    def __post_init__(self):
        if self.month == '' or not self.clinic_id:
            raise ValueError('Narrative output requires Clinic-Month identity')
        if tuple(section.title for section in self.sections) != SECTION_TITLES:
            raise ValueError('Narrative output must contain the seven required sections in order')

    def as_text(self) -> str:
        return '\n\n'.join(f'## {section.title}\n{section.body}' for section in self.sections)

    def to_dict(self) -> dict[str, Any]:
        return {
            'clinic_id': self.clinic_id, 'month': self.month, 'provider': self.provider,
            'sections': [section.to_dict() for section in self.sections],
            'human_review_required': self.human_review_required,
            'successfully_explained_variance': self.successfully_explained_variance,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> 'NarrativeOutput':
        try:
            sections = tuple(NarrativeSection.from_dict(item) for item in value['sections'])
            return cls(value['clinic_id'], value['month'], value.get('provider', 'openai'), sections,
                       value['human_review_required'], value['successfully_explained_variance'])
        except (KeyError, TypeError, ValueError) as exc:
            raise NarrativeGuardrailError(f'Invalid narrative output schema: {exc}') from exc


class NarrativeProvider(Protocol):
    provider_name: str

    def generate(self, prompt: str) -> NarrativeOutput:
        """Generate wording from a structured prompt."""


def _prompt_payload(input_data: NarrativeInput) -> dict[str, Any]:
    payload = investigation_payload(input_data.investigation)
    # The prompt must not ask the model to infer hidden benchmark contracts.
    payload.pop('successfully_explained_variance', None)
    return payload


def build_prompt(input_data: NarrativeInput) -> str:
    structured = json.dumps(_prompt_payload(input_data), sort_keys=True, separators=(',', ':'))
    return (
        'You are writing concise management-ready healthcare FP&A commentary. '
        'Use only the structured InvestigationResult JSON below. Preserve all numbers, '
        'driver roles, epistemic states, unresolved questions, timing, and explicit human review. '
        'Do not add causes, evidence, contribution percentages, analyst confirmation, or forecast writes. '
        'Return JSON with exactly seven sections: ' + ', '.join(SECTION_TITLES) + '.\n\n'
        'InvestigationResult JSON:\n' + structured
    )


def _fmt(value: Any) -> str:
    if value is None:
        return 'unavailable'
    # Management commentary does not need the engine's full Decimal expansion,
    # but it must retain the deterministic value. Four decimal places match the
    # benchmark contract and trailing zeroes are presentation-only.
    from decimal import Decimal
    if isinstance(value, Decimal):
        value = value.quantize(Decimal('0.0001')) if abs(value) < 1 else value.quantize(Decimal('0.01'))
        return format(value, 'f').rstrip('0').rstrip('.') or '0'
    return str(value)


def _driver_label(driver) -> str:
    state = driver.epistemic_state.value.replace('_', ' ').title()
    role = driver.role or 'unranked'
    if role == 'upstream_context':
        return f'{driver.driver_family.value} (upstream context) [{state}]'
    return f'{driver.driver_family.value} ({role}, {state})'


def _variance_label(variance_type: str) -> str:
    return {
        'financial_variance': 'Financial Variance',
        'operational_metric_variance': 'Operational Metric Variance',
        'forecast_assumption_variance': 'Forecast Assumption Variance',
    }.get(variance_type, variance_type)


class DeterministicNarrativeFormatter:
    provider_name = 'deterministic-fallback'

    def format(self, input_data: NarrativeInput) -> NarrativeOutput:
        result = input_data.investigation
        target = result.variance
        calc = target.calculation
        primary = result.primary_driver.value if result.primary_driver else 'No primary driver is supported'
        timing = result.timing.classification
        summary = (
            f'Clinic {result.clinic_id} for {result.month} has a {_variance_label(target.variance_type)} in '
            f'{target.item_id}: actual {_fmt(calc.actual)} versus approved comparator '
            f'{_fmt(calc.forecast_or_expected)}, absolute variance {_fmt(calc.absolute)} '
            f'and ratio {_fmt(calc.percentage)}. Primary assessment: {primary}. '
            f'Timing classification is {timing}. Human review is required.'
        )
        variance_lines = []
        for variance in result.observed_variances:
            c = variance.calculation
            variance_lines.append(
                f'{_variance_label(variance.variance_type)} {variance.item_id}: actual {_fmt(c.actual)} vs '
                f'comparator {_fmt(c.forecast_or_expected)}, absolute {_fmt(c.absolute)}, '
                f'ratio {_fmt(c.percentage)}, direction {variance.direction}.'
            )
        driver_lines = []
        for driver in result.drivers:
            if driver.epistemic_state == S.SUPPORTED or driver.role == 'upstream_context':
                driver_lines.append(f'{_driver_label(driver)}.')
        if F.EXTERNAL in result.upstream_context:
            weather_context = any(
                fact.fact_type == 'reported_event' and dict(fact.values).get('event_type') == 'weather_disruption'
                for fact in result.observed_facts
            )
            if weather_context:
                driver_lines.append('The reported weather event remains upstream context and is not the primary revenue driver.')
        if not driver_lines:
            driver_lines.append('No driver has sufficient evidence for a supported conclusion.')
        gaps = []
        if any(driver.epistemic_state in (S.UNRESOLVED, S.CANDIDATE) for driver in result.drivers):
            gaps.append('Insufficient evidence is available to establish an operating cause; the driver remains unresolved or candidate.')
        for driver in result.drivers:
            if driver.epistemic_state in (S.REJECTED, S.CANDIDATE, S.UNRESOLVED):
                gaps.append(f'{_driver_label(driver)} remains outside the supported conclusions.')
        if result.unresolved_questions:
            gaps.append('Unresolved questions remain: ' + '; '.join(QUESTIONS.get(q, q) for q in result.unresolved_questions) + '.')
        if not gaps:
            gaps.append('No additional evidence gap is recorded in the validated result.')
        questions = '; '.join(QUESTIONS.get(q, q) for q in result.unresolved_questions)
        if not questions:
            questions = 'No additional operations question is recorded.'
        if result.primary_driver is None or result.timing.classification == 'unresolved':
            forecast = 'Evidence is insufficient before changing the forecast; keep the current assumption pending analyst review.'
        else:
            forecast = f'Use the {timing} assessment as a forecast consideration only; an analyst must decide whether to retain, scenario-test, or review the assumption.'
        review = 'Human review required: pending. Allowed actions are confirm, reject, or request more evidence. No automatic forecast change has been made.'
        return NarrativeOutput(
            result.clinic_id, result.month, self.provider_name,
            tuple(NarrativeSection(title, body) for title, body in zip(SECTION_TITLES, (
                summary, '\n'.join(variance_lines), ' '.join(driver_lines), ' '.join(gaps),
                questions, forecast, review))),
            result.human_review_required, result.successfully_explained_variance,
        )


class OpenAINarrativeProvider:
    """The sole LLM adapter; transport is injectable so tests never call a service."""

    provider_name = 'openai'

    def __init__(self, transport: Callable[[str], dict[str, Any] | str] | None = None):
        self._transport = transport

    def generate(self, prompt: str) -> NarrativeOutput:
        if self._transport is None:
            raise RuntimeError('OpenAI transport is not configured; use the deterministic fallback')
        raw = self._transport(prompt)
        if isinstance(raw, str):
            raw = json.loads(raw)
        output = NarrativeOutput.from_dict(raw)
        return NarrativeOutput(output.clinic_id, output.month, self.provider_name, output.sections,
                               output.human_review_required, output.successfully_explained_variance)


def _numeric_tokens(result: InvestigationResult) -> set[str]:
    tokens = {result.clinic_id, result.month}
    payload = investigation_payload(result)
    def walk(value: Any):
        if isinstance(value, dict):
            for item in value.values():
                walk(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item)
        elif value is not None:
            for match in _NUMBER.findall(str(value)):
                tokens.add(match.rstrip('%'))
            from decimal import Decimal, InvalidOperation
            try:
                numeric = Decimal(str(value))
            except (InvalidOperation, ValueError):
                numeric = None
            if numeric is not None and numeric.is_finite():
                for match in _NUMBER.findall(_fmt(numeric)):
                    tokens.add(match.rstrip('%'))
    walk(payload)
    return tokens


def validate_narrative(result: InvestigationResult, output: NarrativeOutput) -> NarrativeOutput:
    if output.clinic_id != result.clinic_id or output.month != result.month:
        raise NarrativeGuardrailError('Narrative identity does not match InvestigationResult')
    if output.provider not in {'openai', 'deterministic-fallback'}:
        raise NarrativeGuardrailError('Unknown narrative provider')
    if output.human_review_required is not True or not result.human_review_required:
        raise NarrativeGuardrailError('Human review must remain explicit and required')
    if output.successfully_explained_variance != result.successfully_explained_variance:
        raise NarrativeGuardrailError('Narrative cannot change successfully explained status')
    text = output.as_text()
    allowed = _numeric_tokens(result)
    for token in _NUMBER.findall(text):
        if token.rstrip('%') not in allowed:
            raise NarrativeGuardrailError(f'Narrative introduced unsupported number: {token}')
    if '%' in text or _ATTRIBUTION.search(text):
        raise NarrativeGuardrailError('Narrative introduced an unsupported attribution percentage')
    if _CONFIRMED.search(text):
        raise NarrativeGuardrailError('Narrative introduced Analyst-Confirmed Cause')
    if _FORECAST_WRITE.search(text) or re.search(r'\b(?:automatically|autonomously)\b[^.\n]{0,30}\b(?:change|update|approve)', text, re.I):
        raise NarrativeGuardrailError('Narrative introduced an autonomous forecast change')
    for driver in result.drivers:
        label = _driver_label(driver)
        if label.lower() not in text.lower():
            raise NarrativeGuardrailError(f'Narrative changed driver classification: {label}')
    unresolved = result.primary_driver is None or result.timing.classification == 'unresolved'
    if unresolved:
        lower = text.lower()
        for phrase in ('unresolved', 'insufficient evidence', 'before changing the forecast'):
            if phrase not in lower:
                raise NarrativeGuardrailError('Narrative removed an unresolved evidence boundary')
    return output


def generate_narrative(result: InvestigationResult, *, provider: NarrativeProvider | None = None) -> NarrativeOutput:
    input_data = NarrativeInput(result)
    if provider is None:
        output = DeterministicNarrativeFormatter().format(input_data)
    else:
        try:
            output = provider.generate(build_prompt(input_data))
        except (RuntimeError, OSError, ValueError, json.JSONDecodeError):
            # A configured but unavailable provider must leave the demo usable.
            output = DeterministicNarrativeFormatter().format(input_data)
    return validate_narrative(result, output)
