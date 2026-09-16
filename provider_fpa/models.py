"""Immutable domain records and canonical vocabulary."""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Literal

from provider_fpa.calculations import Calculation


class DriverFamily(str, Enum):
    DEMAND = 'Demand & Volume'
    PROVIDER = 'Provider Availability'
    CAPACITY = 'Clinic Capacity & Operations'
    REVENUE = 'Revenue Realization'
    WORKFORCE = 'Workforce & Operating Expense'
    ACCOUNTING = 'Accounting & Timing'
    EXTERNAL = 'External Disruption'
    OTHER = 'Other'
    UNRESOLVED = 'Unresolved'
    DATA_QUALITY = 'Data Quality Issue'


class EpistemicState(str, Enum):
    OBSERVED = 'observed_fact'
    CANDIDATE = 'candidate_driver'
    SUPPORTED = 'supported_driver'
    CONFIRMED = 'analyst_confirmed_cause'
    REJECTED = 'rejected_driver'
    UNRESOLVED = 'unresolved_driver'


@dataclass(frozen=True)
class SourceReference:
    input_file: str
    row_selector: tuple[tuple[str, str], ...]
    source: str
    recorded_at: str | None = None

    def __post_init__(self):
        if not self.source or not self.input_file or not self.row_selector:
            raise ValueError('Evidence requires a file, row identity, and source')


@dataclass(frozen=True)
class ReviewRule:
    rule_id: str
    target_id: str
    absolute_threshold: Decimal | None
    percentage_threshold: Decimal | None
    always_review: bool
    effective_from: str
    effective_to: str | None
    evidence: SourceReference

    def __post_init__(self):
        for value in (self.absolute_threshold, self.percentage_threshold):
            if value is not None and (not value.is_finite() or value < 0):
                raise ValueError('Thresholds must be finite and nonnegative')


@dataclass(frozen=True)
class ReviewDecision:
    required: bool
    reasons: tuple[str, ...]
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class HumanDecision:
    review_reference: str
    recorded_at: str
    rationale: str

    def __post_init__(self):
        if not all((self.review_reference, self.recorded_at, self.rationale)):
            raise ValueError('Human confirmation requires an explicit review record')


@dataclass(frozen=True)
class Driver:
    driver_family: DriverFamily
    role: Literal['primary', 'contributing', 'upstream_context'] | None
    epistemic_state: EpistemicState
    mechanism: str
    evidence: tuple[SourceReference, ...]
    human_decision: HumanDecision | None = None

    def __post_init__(self):
        if self.epistemic_state in (EpistemicState.SUPPORTED, EpistemicState.CONFIRMED) and not self.evidence:
            raise ValueError('Supported conclusions require evidence')
        if self.role in ('primary', 'contributing') and self.epistemic_state not in (
                EpistemicState.SUPPORTED, EpistemicState.CONFIRMED):
            raise ValueError('Primary and contributing mechanisms require support')
        if self.epistemic_state == EpistemicState.CONFIRMED and self.human_decision is None:
            raise ValueError('Confirmation requires a human decision')


@dataclass(frozen=True)
class ForecastHorizon:
    start: str
    end: str
    basis: Literal['latest_approved_forecast', 'next_3_month_fallback']
    evidence: tuple[SourceReference, ...] = ()


@dataclass(frozen=True)
class TimingEvidence:
    normalization_month: str | None
    persists_through: str | None
    recurring: bool
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class TimingAssessment:
    classification: Literal['temporary', 'structural', 'unresolved']
    recurring: bool
    structural: bool
    horizon: ForecastHorizon
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class Clinic:
    clinic_id: str
    clinic_name: str
    market_id: str
    specialty: str
    active_from: str
    active_to: str | None
    evidence: SourceReference


@dataclass(frozen=True)
class Value:
    clinic_id: str
    month: str
    item_id: str
    name: str
    actual: Decimal | None
    comparator: Decimal | None
    variance_type: Literal['financial_variance', 'operational_metric_variance', 'forecast_assumption_variance']
    unit: str
    currency: str | None
    evidence: SourceReference
    data_quality_issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class OperatingEvent:
    event_id: str
    clinic_id: str
    event_type: str
    start_date: str
    end_date: str | None
    description: str
    evidence: SourceReference


@dataclass(frozen=True)
class Datasets:
    clinics: tuple[Clinic, ...]
    financial_values: tuple[Value, ...]
    operational_values: tuple[Value, ...]
    operating_events: tuple[OperatingEvent, ...]
    review_rules: tuple[ReviewRule, ...]


@dataclass(frozen=True)
class ObservedVariance:
    item_id: str
    variance_type: str
    calculation: Calculation
    direction: str
    unit: str
    currency: str | None
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class ObservedFact:
    fact_type: str
    subject_id: str
    values: tuple[tuple[str, str | None], ...]
    evidence: tuple[SourceReference, ...]
    epistemic_state: EpistemicState = EpistemicState.OBSERVED


@dataclass(frozen=True)
class ContributionEstimate:
    amount: Decimal
    unit: str
    basis: str
    evidence: tuple[SourceReference, ...]


@dataclass(frozen=True)
class InvestigationResult:
    clinic_id: str
    month: str
    variance: ObservedVariance
    review: ReviewDecision
    observed_variances: tuple[ObservedVariance, ...]
    observed_facts: tuple[ObservedFact, ...]
    drivers: tuple[Driver, ...]
    timing: TimingAssessment
    unresolved_questions: tuple[str, ...]
    contribution_estimate: ContributionEstimate | None = None
    material_undisclosed_issue: bool = False
    analyst_status: str = 'pending'

    def __post_init__(self):
        if sum(d.role == 'primary' for d in self.drivers) > 1:
            raise ValueError('An investigation may have at most one primary driver')
        if not self.variance.evidence or any(not f.evidence for f in self.observed_facts):
            raise ValueError('Observed facts and variances require lineage')

    @property
    def primary_driver(self) -> DriverFamily | None:
        return next((d.driver_family for d in self.drivers if d.role == 'primary'), None)

    @property
    def contributing_drivers(self) -> tuple[DriverFamily, ...]:
        return tuple(d.driver_family for d in self.drivers if d.role == 'contributing')

    @property
    def upstream_context(self) -> tuple[DriverFamily, ...]:
        return tuple(d.driver_family for d in self.drivers if d.role == 'upstream_context')

    @property
    def review_required(self) -> bool:
        return self.review.required

    @property
    def human_review_required(self) -> bool:
        return self.review.required or bool(self.drivers)

    @property
    def successful_investigation(self) -> bool:
        # This is workflow completion, not an independent evaluation score.
        return (self.variance.calculation.absolute is not None
                and not self.material_undisclosed_issue
                and (self.primary_driver is not None or bool(self.unresolved_questions)
                     or self.variance.calculation.absolute == 0))

    @property
    def successfully_explained_variance(self) -> bool:
        from provider_fpa.evidence import is_successfully_explained

        return is_successfully_explained(self.successful_investigation, self.drivers,
                                        self.material_undisclosed_issue)
