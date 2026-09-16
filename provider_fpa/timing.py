"""Horizon-relative timing; recurrence does not determine persistence."""

import re

from provider_fpa.models import ForecastHorizon, TimingAssessment, TimingEvidence


def month_index(month: str) -> int:
    if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', month):
        raise ValueError('Calendar Month must be YYYY-MM')
    year, number = map(int, month.split('-'))
    return year * 12 + number - 1


def add_months(month: str, count: int) -> str:
    year, number = divmod(month_index(month) + count, 12)
    return f'{year:04d}-{number + 1:02d}'


def fallback_horizon(month: str) -> ForecastHorizon:
    return ForecastHorizon(add_months(month, 1), add_months(month, 3), 'next_3_month_fallback')


def classify_timing(horizon: ForecastHorizon, signals: tuple[TimingEvidence, ...],
                    *, material_fraction: float = 0.5) -> TimingAssessment:
    """Explicit policy: persistence over >= half of remaining months is material.

    Unknown duration dominates mixed evidence so it cannot be hidden by a
    temporary or structural co-driver. Normalization at horizon end is unknown.
    """
    start, end = month_index(horizon.start), month_index(horizon.end)
    if end < start or not 0 < material_fraction <= 1:
        raise ValueError('Invalid horizon or material fraction')
    states = []
    for signal in signals:
        normal = month_index(signal.normalization_month) if signal.normalization_month else None
        through = month_index(signal.persists_through) if signal.persists_through else None
        if not signal.evidence or (normal is not None and through is not None and normal <= through):
            states.append('unresolved')
        elif through is not None and (min(through, end) - start + 1) / (end - start + 1) >= material_fraction:
            states.append('structural')
        elif normal is not None and normal < end:
            states.append('temporary')
        else:
            states.append('unresolved')
    classification = ('unresolved' if not states or 'unresolved' in states else
                      'structural' if 'structural' in states else 'temporary')
    evidence = tuple(dict.fromkeys(ref for signal in signals for ref in signal.evidence))
    return TimingAssessment(classification, any(s.recurring for s in signals),
                            classification == 'structural', horizon, evidence)
