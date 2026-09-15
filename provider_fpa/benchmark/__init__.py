"""Immutable, normalized public references. No scenario inputs are accepted here."""
import csv
import json
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parents[2] / 'data/public_benchmarks'
COMPANIES = {'HCA': 'hca', 'THC': 'tenet'}


@dataclass(frozen=True)
class Metric:
    company: str
    ticker: str
    period: str
    business_segment: str
    reporting_basis: str
    metric_id: str
    metric_name: str
    value: Decimal | None
    unit: str
    raw_value: str
    raw_unit: str
    metric_definition: str
    source_document: str
    source_url: str
    source_type: str
    source_locator: str
    extraction_reference: str
    source_sha256: str
    provenance_kind: str
    missing_reason: str
    notes: str
    group: str
    parent_metric_ids: tuple[str, ...] = ()
    derivation: str = ''

    def payload(self):
        result = asdict(self)
        result['value'] = None if self.value is None else str(self.value)
        return result


@dataclass(frozen=True)
class Company:
    company: str
    ticker: str
    notes: str
    metrics: tuple[Metric, ...]

    def payload(self):
        return dict(company=self.company, ticker=self.ticker, notes=self.notes,
                    data_kind='public_benchmark', metrics=[m.payload() for m in self.metrics])


def normalize_records(records):
    """Validate source records at the public ingestion boundary; never infer missing values."""
    output, seen = [], set()
    required = ('company', 'ticker', 'period', 'business_segment', 'reporting_basis',
                'metric_id', 'metric_name', 'unit', 'raw_unit', 'metric_definition',
                'source_document', 'source_url', 'source_type', 'source_locator',
                'extraction_reference', 'source_sha256', 'provenance_kind', 'group')
    for record in records:
        row = dict(record)
        if any(not row.get(key) for key in required):
            raise ValueError('Public record missing identity, definition or source lineage')
        if not row['source_url'].startswith('https://') or row['provenance_kind'] != 'reported':
            raise ValueError('Invalid public source or provenance')
        key = tuple(row[k] for k in ('ticker','period','metric_id','business_segment','reporting_basis'))
        if key in seen:
            raise ValueError('Duplicate or conflicting public metric')
        seen.add(key)
        raw = row['raw_value']
        if raw == '':
            if not row.get('missing_reason') or row['value'] != '':
                raise ValueError('Missing value must remain missing with a reason')
            value = None
        else:
            try:
                source_value = Decimal(raw)
                value = Decimal(row['value'])
            except InvalidOperation as exc:
                raise ValueError('Invalid public number') from exc
            if not source_value.is_finite() or not value.is_finite() or row.get('missing_reason'):
                raise ValueError('Invalid public value/missing state')
            expected_unit = {'USD millions':'USD','percent':'ratio'}.get(row['raw_unit'],row['raw_unit'])
            scale = {'USD millions':Decimal(1000000),'percent':Decimal('.01')}.get(row['raw_unit'],Decimal(1))
            if row['unit'] != expected_unit or value != source_value * scale:
                raise ValueError('Public unit conversion does not reconcile')
        row['value'] = value
        output.append(Metric(**row))
    return tuple(output)


def derived_ratio(numerator, denominator, metric_id, name):
    """Ratios require the same company, period, segment and reporting population."""
    fields = ('ticker','period','business_segment','reporting_basis','unit')
    if any(getattr(numerator,k) != getattr(denominator,k) for k in fields):
        raise ValueError('Ratio inputs have incompatible scope or units')
    missing = numerator.value is None or denominator.value is None or denominator.value == 0
    with localcontext() as ctx:
        ctx.prec = 28
        value = None if missing else numerator.value / denominator.value
    return replace(numerator, metric_id=metric_id, metric_name=name, value=value, unit='ratio',
                   raw_value='', raw_unit='derived ratio', provenance_kind='derived',
                   metric_definition=f'{numerator.metric_name} / {denominator.metric_name}; same reporting basis.',
                   missing_reason='Missing numerator or missing/zero denominator' if missing else '',
                   parent_metric_ids=(numerator.metric_id, denominator.metric_id),
                   derivation=f'{numerator.metric_id} / {denominator.metric_id}',
                   source_locator=f'{numerator.source_locator}; denominator: {denominator.source_locator}',
                   extraction_reference=f'{numerator.extraction_reference}; denominator: {denominator.extraction_reference}')


def load_company(ticker, root=DATA_ROOT):
    if ticker not in COMPANIES:
        raise ValueError('Unknown public benchmark company')
    folder = root / COMPANIES[ticker]
    metadata = json.loads((folder/'metadata.json').read_text())
    records = []
    for path in sorted(folder.glob('*_metrics.csv')):
        with path.open(newline='') as handle:
            records.extend(csv.DictReader(handle))
    metrics = normalize_records(records)
    if not metrics or any(m.ticker != ticker or m.company != metadata['company'] or
                          m.source_sha256 != metadata['source_sha256'] for m in metrics):
        raise ValueError('Company/source identity mismatch')
    ratios = []
    for denominator in metrics:
        if denominator.metric_id not in ('REVENUE','SEGMENT_REVENUE'):
            continue
        ids = ('LABOR','SUPPLIES') if denominator.metric_id == 'REVENUE' else ('SEGMENT_LABOR','SEGMENT_SUPPLIES','SEGMENT_ADJUSTED_EBITDA')
        for numerator in metrics:
            if numerator.metric_id in ids and all(getattr(numerator,k)==getattr(denominator,k) for k in ('period','business_segment','reporting_basis')):
                label = {'LABOR':'Labor / revenue','SUPPLIES':'Supplies / revenue','SEGMENT_LABOR':'Labor / segment revenue','SEGMENT_SUPPLIES':'Supplies / segment revenue','SEGMENT_ADJUSTED_EBITDA':'Adjusted EBITDA margin'}[numerator.metric_id]
                ratios.append(derived_ratio(numerator,denominator,numerator.metric_id+'_RATIO',label))
    return Company(metadata['company'],ticker,metadata['notes'],metrics+tuple(ratios))
