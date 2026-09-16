"""CSV adapter for the five logical datasets. Never reads cases or gold answers."""

import csv
from datetime import date, datetime
from pathlib import Path

from provider_fpa.calculations import decimal_value
from provider_fpa.models import Clinic, Datasets, OperatingEvent, ReviewRule, SourceReference, Value
from provider_fpa.timing import month_index


HEADERS = {
    'clinics.csv': 'clinic_id clinic_name market_id specialty active_from active_to source',
    'financial_values.csv': 'clinic_id month account_id account_name actual_value forecast_value unit currency source loaded_at',
    'operational_values.csv': 'clinic_id month metric_id metric_name actual_value expected_value unit source loaded_at',
    'operating_events.csv': 'event_id clinic_id event_type start_date end_date description source reported_at',
    'review_rules.csv': 'rule_id account_or_metric_id absolute_threshold percentage_threshold always_review effective_from effective_to source',
}
KEYS = {
    'clinics.csv': ('clinic_id',),
    'financial_values.csv': ('clinic_id', 'month', 'account_id'),
    'operational_values.csv': ('clinic_id', 'month', 'metric_id'),
    'operating_events.csv': ('event_id',),
    'review_rules.csv': ('rule_id',),
}


def _read(root: Path, filename: str) -> list[dict[str, str]]:
    with (root / filename).open(newline='', encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != HEADERS[filename].split():
            raise ValueError(f'{filename}: expected the aggregate-only MVP schema')
        rows = list(reader)
    seen = set()
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f'{filename}: malformed CSV row')
        key = tuple(row[field] for field in KEYS[filename])
        if not all(key) or key in seen:
            raise ValueError(f'{filename}: missing or duplicate row identity {key}')
        seen.add(key)
        if not row['source'].strip():
            raise ValueError(f'{filename}: missing source')
        for field in ('month', 'active_from', 'effective_from'):
            if field in row:
                month_index(row[field])
        for first, last in [('active_from', 'active_to'), ('effective_from', 'effective_to')]:
            if row.get(last):
                month_index(row[last])
                if row[last] < row[first]:
                    raise ValueError(f'{filename}: reversed effective interval')
        for field in ('loaded_at', 'reported_at'):
            if field in row:
                datetime.fromisoformat(row[field].replace('Z', '+00:00'))
    return rows


def _reference(filename: str, row: dict[str, str]) -> SourceReference:
    return SourceReference(filename, tuple((field, row[field]) for field in KEYS[filename]),
                           row['source'], row.get('loaded_at', row.get('reported_at')))


def _value(filename: str, row: dict[str, str]) -> Value:
    financial = filename == 'financial_values.csv'
    prefix = 'account' if financial else 'metric'
    problems = []
    numbers = []
    for field in ('actual_value', 'forecast_value' if financial else 'expected_value'):
        try:
            number = decimal_value(row[field])
        except ValueError:
            number = None
        if number is None:
            problems.append(f'{field}_missing_or_invalid')
        numbers.append(number)
    if not row['unit'] or (financial and not row['currency']):
        raise ValueError('Values require units and financial currency')
    return Value(row['clinic_id'], row['month'], row[f'{prefix}_id'], row[f'{prefix}_name'],
                 *numbers, 'financial_variance' if financial else 'operational_metric_variance',
                 row['unit'], row.get('currency'), _reference(filename, row), tuple(problems))


def load_datasets(inputs_directory: str | Path) -> Datasets:
    root = Path(inputs_directory)
    tables = {filename: _read(root, filename) for filename in HEADERS}
    clinic_ids = {r['clinic_id'] for r in tables['clinics.csv']}
    for filename, rows in tables.items():
        for row in rows:
            if 'clinic_id' in row and row['clinic_id'] not in clinic_ids:
                raise ValueError(f'{filename}: unknown Clinic')
    clinics = tuple(Clinic(r['clinic_id'], r['clinic_name'], r['market_id'], r['specialty'],
                          r['active_from'], r['active_to'] or None, _reference('clinics.csv', r))
                    for r in tables['clinics.csv'])
    events = []
    for r in tables['operating_events.csv']:
        date.fromisoformat(r['start_date'])
        if r['end_date']:
            date.fromisoformat(r['end_date'])
            if r['end_date'] < r['start_date']:
                raise ValueError('Reversed event interval')
        events.append(OperatingEvent(r['event_id'], r['clinic_id'], r['event_type'], r['start_date'],
                                     r['end_date'] or None, r['description'], _reference('operating_events.csv', r)))
    rules = []
    for r in tables['review_rules.csv']:
        if r['always_review'] not in ('true', 'false'):
            raise ValueError('always_review must be true or false')
        rules.append(ReviewRule(r['rule_id'], r['account_or_metric_id'], decimal_value(r['absolute_threshold']),
                                decimal_value(r['percentage_threshold']), r['always_review'] == 'true',
                                r['effective_from'], r['effective_to'] or None, _reference('review_rules.csv', r)))
    return Datasets(clinics, tuple(_value('financial_values.csv', r) for r in tables['financial_values.csv']),
                    tuple(_value('operational_values.csv', r) for r in tables['operational_values.csv']),
                    tuple(events), tuple(rules))
