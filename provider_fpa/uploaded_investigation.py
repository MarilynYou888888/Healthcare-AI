"""Stateless normalized-upload adapter. No files, cache, notes, or free-text rules.

The existing engine owns variance, materiality, causal rules and timing arithmetic.
Only this adapter knows the uploaded schema and its stricter evidence boundary.
"""
import hashlib
import json
import re
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from provider_fpa.engine import investigate
from provider_fpa.models import (Clinic, Datasets, Driver, DriverFamily, EpistemicState,
                                ForecastHorizon, ObservedFact, OperatingEvent, ReviewRule,
                                SourceReference, TimingEvidence, Value)
from provider_fpa.presentation import investigation_payload
from provider_fpa.timing import add_months, classify_timing, fallback_horizon, month_index
from provider_fpa.investigation import apply_review_decisions

# No speculative semantic aliases: FTE never maps to provider days.
METRICS = {
    'REV_NET_PATIENT': ('REV_NET_PATIENT', 'money', False),
    'VISITS': ('PATIENT_VISITS', 'visits', False),
    'PATIENT_VISITS': ('PATIENT_VISITS', 'visits', False),
    'PROVIDER_FTE': ('PROVIDER_FTE', 'FTE', False),
    'LABOR_EXPENSE': ('LABOR_EXPENSE', 'money', True),
    'EXP_CLINICAL_LABOR': ('EXP_CLINICAL_LABOR', 'money', True),
    'SUPPLY_EXPENSE': ('SUPPLY_EXPENSE', 'money', True),
    'OPERATING_EXPENSE': ('OPERATING_EXPENSE', 'money', True),
    'OPERATING_INCOME': ('OPERATING_INCOME', 'money', False),
    'NET_REVENUE_PER_VISIT': ('NET_REVENUE_PER_VISIT', 'rate', False),
    'PROVIDER_AVAILABLE_DAYS': ('PROVIDER_AVAILABLE_DAYS', 'days', False),
    'CLINIC_CLOSURE_DAYS': ('CLINIC_CLOSURE_DAYS', 'days', True),
    'OVERTIME_HOURS': ('OVERTIME_HOURS', 'hours', True),
    'COMMERCIAL_PAYER_MIX': ('COMMERCIAL_PAYER_MIX', 'ratio', False),
}


def text(value, limit=2000, required=False):
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError('Invalid text field')
    return value


def number(value, optional=False):
    if optional and value == '':
        return None
    text(value, 128, True)
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError('Invalid numeric field') from exc
    if not result.is_finite() or abs(result.adjusted()) > 1000:
        raise ValueError('Numeric field exceeds supported range')
    return result


def boolean(value):
    if type(value) is not bool:
        raise ValueError('An explicit choice is required')
    return value


def reference(row, dataset, identity):
    loc = row.get('_lineage')
    if not isinstance(loc, dict) or set(loc) != {'file','sheet','row','kind'}:
        raise ValueError('Source lineage required')
    for field in ('file','sheet'):
        text(loc[field], 256, True)
    if type(loc['row']) is not int or not 1 <= loc['row'] <= 50001 or loc['kind'] not in ('user_uploaded','synthetic'):
        raise ValueError('Invalid source row')
    return SourceReference(dataset, (('file',loc['file']),('sheet',loc['sheet']),('row',str(loc['row'])),*identity),
                           text(row.get('source',''), 2000, True), row.get('reported_at') or None)


def _build(payload):
    expected={'selection','import_revision','performance','events','confirmations','rule','analyst_override','timing','snapshot_id','decisions'}
    if not isinstance(payload,dict) or set(payload) != expected:
        raise ValueError('Invalid investigation request')
    selection=payload['selection']
    if not isinstance(selection,dict) or set(selection) != {'entity_id','period','metric_id'}:
        raise ValueError('Select entity, period and metric')
    entity=text(selection['entity_id'],256,True)
    period=text(selection['period'],7,True)
    month_index(period)
    target=text(selection['metric_id'],100,True)
    if target not in METRICS:
        raise ValueError('Unsupported metric')
    if type(payload['import_revision']) is not int or payload['import_revision'] < 1:
        raise ValueError('Confirmed import required')
    confirmations=payload['confirmations']
    if not isinstance(confirmations,dict) or set(confirmations) != {'closed_month','latest_approved_forecast','clinical_labor'}:
        raise ValueError('Confirm the closed month and Latest Approved Forecast')
    if not boolean(confirmations['closed_month']) or not boolean(confirmations['latest_approved_forecast']):
        raise ValueError('Confirm the closed month and Latest Approved Forecast')
    clinical=boolean(confirmations['clinical_labor'])
    override=boolean(payload['analyst_override'])
    rows=payload['performance']; event_rows=payload['events']
    if not isinstance(rows,list) or not 1 <= len(rows) <= 1000 or not isinstance(event_rows,list) or len(event_rows)>1000:
        raise ValueError('Selected records exceed request limit')
    values=[]; seen=set(); currencies=set(); name=None
    for row in rows:
        if not isinstance(row,dict) or set(row) != {'entity_id','entity_name','period','metric_id','metric_name','actual_value','forecast_value','unit','currency','source','_lineage'}:
            raise ValueError('Only normalized performance fields are accepted')
        if row['entity_id'] != entity or row['period'] != period:
            raise ValueError('Request must contain only the selected entity and month')
        current_name=text(row['entity_name'],256,True)
        if name is not None and name != current_name:
            raise ValueError('Conflicting entity names')
        name=current_name
        metric=row['metric_id']
        if metric not in METRICS:
            raise ValueError('Unsupported metric')
        internal, kind, _ = METRICS[metric]
        if metric == 'LABOR_EXPENSE' and clinical:
            internal='EXP_CLINICAL_LABOR'
        if internal in seen:
            raise ValueError('Duplicate or ambiguous mapped metrics')
        seen.add(internal)
        currency=text(row['currency'],3)
        if kind in ('money','rate'):
            if not re.fullmatch('[A-Z]{3}',currency):
                raise ValueError('Explicit currency required')
            currencies.add(currency)
            unit=currency if kind=='money' else currency+'_per_visit'
        else:
            if currency:
                raise ValueError('Nonmonetary metrics cannot carry currency')
            unit=kind
        if row['unit'] != unit:
            raise ValueError('Unsupported metric unit')
        actual,forecast=number(row['actual_value']),number(row['forecast_value'])
        if kind != 'money' and (actual < 0 or forecast < 0 or (kind=='ratio' and max(actual,forecast)>1)):
            raise ValueError('Metric outside allowed range')
        ref=reference(row,'uploaded_performance',(('entity_id',entity),('period',period),('metric_id',metric)))
        values.append(Value(entity,period,internal,text(row['metric_name'],256,True),actual,forecast,
                            'financial_variance' if kind=='money' else 'operational_metric_variance',unit,currency or None,ref))
    if len(currencies)>1:
        raise ValueError('Mixed currency not supported')
    internal_target=METRICS[target][0]
    if target=='LABOR_EXPENSE' and clinical:
        internal_target='EXP_CLINICAL_LABOR'
    selected=next((v for v in values if v.item_id==internal_target),None)
    if selected is None:
        raise ValueError('Selected performance metric is missing')
    events=[]; original_events={}
    for index,row in enumerate(event_rows):
        fields={'entity_id','period','event_type','start_date','end_date','description','observed_value','unit','source','reported_at','_lineage'}
        if not isinstance(row,dict) or set(row)!=fields or row['entity_id']!=entity or row['period']!=period:
            raise ValueError('Only selected normalized events are accepted')
        start=date.fromisoformat(row['start_date']); end=date.fromisoformat(row['end_date']) if row['end_date'] else None
        if end and end<start:
            raise ValueError('Reversed event dates')
        kind=text(row['event_type'],100,True)
        description=text(row['description'],2000,True)
        if row['reported_at']:
            stamp=datetime.fromisoformat(row['reported_at'].replace('Z','+00:00'))
            if stamp.tzinfo is None:
                raise ValueError('Reported timestamp requires timezone')
        if row['observed_value']:
            number(row['observed_value']);text(row['unit'],30,True)
        ref=reference(row,'uploaded_events',(('entity_id',entity),('period',period)))
        event_id=f'uploaded-event-{index}'
        # No event text reaches assess_drivers; a workbook cannot define the horizon.
        safe_kind='reported_forecast_horizon' if kind=='forecast_horizon' else kind
        events.append(OperatingEvent(event_id,entity,safe_kind,row['start_date'],row['end_date'] or None,'',ref))
        original_events[event_id]=(row,ref)
    rule=payload['rule']
    if not isinstance(rule,dict) or set(rule)!={'absolute','percentage','always_review'}:
        raise ValueError('Invalid review settings')
    absolute,percentage=number(rule['absolute'],True),number(rule['percentage'],True)
    always=boolean(rule['always_review'])
    rule_ref=SourceReference('session_review_settings',(('metric_id',target),('period',period)), 'Explicit analyst review settings')
    rules=() if absolute is None and percentage is None and not always else (ReviewRule('session-rule',internal_target,absolute,percentage,always,period,period,rule_ref),)
    clinic=Clinic(entity,name,'','',period,period,values[0].evidence)
    data=Datasets((clinic,),tuple(v for v in values if v.variance_type=='financial_variance'),
                  tuple(v for v in values if v.variance_type!='financial_variance'),tuple(events),rules)
    result=investigate(data,entity,period,internal_target,selected.variance_type,analyst_override=override)
    # V2 favorable-direction registry adds presentation semantics, not causal rules.
    def direction(variance):
        if variance.item_id not in ('LABOR_EXPENSE','SUPPLY_EXPENSE','OPERATING_EXPENSE','OPERATING_INCOME'):
            return variance
        delta=variance.calculation.absolute
        lower=variance.item_id!='OPERATING_INCOME'
        label='undefined' if delta is None else 'on_plan' if delta==0 else 'unfavorable' if (delta>0 if lower else delta<0) else 'favorable'
        return replace(variance,direction=label)
    result=replace(result,variance=direction(result.variance),observed_variances=tuple(direction(v) for v in result.observed_variances))
    if selected.currency and selected.currency!='USD' and result.primary_driver:
        unresolved=Driver(DriverFamily.UNRESOLVED,None,EpistemicState.UNRESOLVED,'business_mechanism_unresolved',(selected.evidence,))
        result=replace(result,drivers=(unresolved,),contribution_estimate=None,
                       unresolved_questions=('Currency-specific mechanism is unsupported; validate the operating explanation.',))
    # Restore descriptions solely as observed facts, after all causal rules finish.
    facts=[f for f in result.observed_facts if f.fact_type!='reported_event']
    for event_id,(row,ref) in original_events.items():
        facts.append(ObservedFact('reported_event',event_id,tuple((k,row[k] or None) for k in
                    ('event_type','description','start_date','end_date','observed_value','unit')),(ref,)))
    timing=payload['timing']
    if not isinstance(timing,dict) or set(timing)!={'normalization_month','persists_through','source','forecast_end','recurring'}:
        raise ValueError('Invalid structured timing')
    for key in ('normalization_month','persists_through','forecast_end'):
        text(timing[key],7)
        if timing[key]: month_index(timing[key])
    recurring=boolean(timing['recurring'])
    source=text(timing['source'],2000)
    horizon=fallback_horizon(period)
    if timing['forecast_end']:
        if timing['forecast_end']<=period or not source.strip():
            raise ValueError('Approved future horizon requires a source')
        horizon=ForecastHorizon(add_months(period,1),timing['forecast_end'],'latest_approved_forecast',
            (SourceReference('session_timing',(('entity_id',entity),('period',period)),source),))
    signals=()
    if timing['normalization_month'] or timing['persists_through'] or recurring:
        if not source.strip():
            raise ValueError('Structured timing requires an explicit source')
        if any(timing[k] and timing[k]<period for k in ('normalization_month','persists_through')):
            raise ValueError('Timing evidence must apply to the selected month or later')
        if result.primary_driver:
            signals=(TimingEvidence(timing['normalization_month'] or None,timing['persists_through'] or None,recurring,
                (SourceReference('session_timing',(('entity_id',entity),('period',period),('metric_id',target)),source),)),)
    result=replace(result,observed_facts=tuple(facts),timing=classify_timing(horizon,signals))
    return result, bool(rules)


def uploaded_investigation(payload):
    result,configured=_build(payload)
    system=investigation_payload(result)
    context={k:v for k,v in payload.items() if k not in ('snapshot_id','decisions')}
    snapshot=hashlib.sha256(json.dumps([context,system],sort_keys=True).encode()).hexdigest()
    decisions=payload['decisions']
    if not isinstance(decisions,dict):
        raise ValueError('Invalid decisions')
    if payload['snapshot_id'] is not None and payload['snapshot_id']!=snapshot:
        raise ValueError('Stale snapshot: rerun before human review')
    if decisions and payload['snapshot_id']!=snapshot:
        raise ValueError('Human review requires the current snapshot')
    reviewed,receipts=apply_review_decisions(result,decisions)
    return dict(snapshot_id=snapshot,data_kind='user_uploaded',system=system,
                reviewed=investigation_payload(reviewed),decisions=receipts,
                rule_disclosure='Session review rules configured.' if configured else 'No automatic materiality rule configured.',
                policy=dict(structural_horizon_fraction=0.5,disclosure='Timing uses explicit evidence covering the selected supported mechanism; event end dates do not establish recovery. Structural threshold: at least half of the remaining horizon.'))
