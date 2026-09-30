"""Request-local adapter boundaries, independent of synthetic fixtures."""
import copy
import unittest
from provider_fpa.uploaded_investigation import uploaded_investigation


def row(metric, actual, forecast, unit='USD', currency='USD'):
    return dict(entity_id='NSC',entity_name='Nashville',period='2026-08',metric_id=metric,
                metric_name=metric,actual_value=str(actual),forecast_value=str(forecast),unit=unit,
                currency=currency,source='Finance close',_lineage=dict(file='finance.xlsx',sheet='Monthly Actuals',row=2,kind='user_uploaded'))


def request(supported=False):
    rows=[row('REV_NET_PATIENT',18000,20000),row('VISITS',90,100,'visits',''),row('NET_REVENUE_PER_VISIT',200,200,'USD_per_visit')]
    if supported: rows.append(row('PROVIDER_AVAILABLE_DAYS',18,20,'days',''))
    return dict(selection=dict(entity_id='NSC',period='2026-08',metric_id='REV_NET_PATIENT'),
                import_revision=1,performance=rows,events=[dict(entity_id='NSC',period='2026-08',event_type='provider_pto',start_date='2026-08-01',end_date='2026-08-10',description='Reported leave',observed_value='',unit='',source='Ops report',reported_at='',_lineage=dict(file='ops.csv',sheet='CSV',row=2,kind='user_uploaded'))],
                confirmations=dict(closed_month=True,latest_approved_forecast=True,clinical_labor=False),
                rule=dict(absolute='',percentage='',always_review=False),analyst_override=True,
                timing=dict(normalization_month='',persists_through='',source='',forecast_end='',recurring=False),
                snapshot_id=None,decisions={})


class UploadedInvestigationTests(unittest.TestCase):
    def test_insufficient_evidence_and_ftes_never_become_available_days(self):
        payload=request()
        payload['performance'].append(row('PROVIDER_FTE',3.5,4,'FTE',''))
        before=copy.deepcopy(payload)
        result=uploaded_investigation(payload)
        self.assertEqual(payload,before)
        self.assertIsNone(result['system']['primary_driver'])
        self.assertEqual(result['system']['variance']['absolute'],'-2000')
        self.assertEqual(result['system']['timing']['classification'],'unresolved')
        self.assertIn('No automatic materiality rule configured',result['rule_disclosure'])

    def test_supported_requires_explicit_confirmation_and_timing_evidence(self):
        payload=request(True)
        view=uploaded_investigation(payload)
        self.assertEqual(view['system']['primary_driver'],'Demand & Volume')
        self.assertEqual(view['system']['timing']['classification'],'unresolved')
        self.assertIsNone(view['system']['contribution_estimate'])
        index=next(i for i,d in enumerate(view['system']['drivers']) if d['role']=='primary')
        payload.update(snapshot_id=view['snapshot_id'],decisions={str(index):dict(action='confirm',rationale='Reviewed operating evidence')})
        reviewed=uploaded_investigation(payload)
        self.assertEqual(reviewed['reviewed']['drivers'][index]['epistemic_state'],'analyst_confirmed_cause')
        payload['performance'][0]['actual_value']='17999'
        with self.assertRaises(ValueError): uploaded_investigation(payload)

    def test_text_accrual_and_end_date_do_not_establish_cause_or_timing(self):
        payload=request()
        payload['selection']['metric_id']='EXP_CLINICAL_LABOR'
        payload['performance']=[row('EXP_CLINICAL_LABOR',12000,10000)]
        payload['events'][0].update(event_type='accrual_timing',description='USD 2,000 labor accrual',end_date='2026-09-01')
        view=uploaded_investigation(payload)
        self.assertIsNone(view['system']['primary_driver'])
        self.assertIsNone(view['system']['contribution_estimate'])
        self.assertEqual(view['system']['timing']['classification'],'unresolved')
        self.assertIn('USD 2,000 labor accrual',str(view['system']['observed_facts']))

    def test_reconciliation_and_non_usd_mechanisms_stay_unresolved(self):
        payload=request(True);payload['performance'][0]['actual_value']='17999.99'
        view=uploaded_investigation(payload)
        self.assertIsNone(view['system']['primary_driver'])
        self.assertIn('revenue_bridge_does_not_reconcile',str(view['system']['drivers']))
        payload=request(True)
        for r in payload['performance']:
            if r['currency']:r.update(currency='CAD',unit=r['unit'].replace('USD','CAD'))
        self.assertIsNone(uploaded_investigation(payload)['system']['primary_driver'])

    def test_structured_timing_uses_explicit_source_and_horizon(self):
        payload=request(True)
        payload['timing'].update(normalization_month='2026-09',source='Approved coverage plan')
        view=uploaded_investigation(payload)
        self.assertEqual(view['system']['timing']['classification'],'temporary')
        self.assertEqual(view['system']['timing']['horizon']['basis'],'next_3_month_fallback')
        payload['timing'].update(normalization_month='',persists_through='2026-12',forecast_end='2026-12')
        view=uploaded_investigation(payload)
        self.assertEqual(view['system']['timing']['classification'],'structural')
        self.assertEqual(view['system']['timing']['horizon']['basis'],'latest_approved_forecast')
        payload['timing']['source']=''
        with self.assertRaises(ValueError):uploaded_investigation(payload)
        payload=request();payload['timing'].update(normalization_month='2026-09',source='Unproven claim')
        self.assertEqual(uploaded_investigation(payload)['system']['timing']['classification'],'unresolved')

    def test_rules_override_and_direction_without_causal_inference(self):
        payload=request();payload['analyst_override']=False
        self.assertFalse(uploaded_investigation(payload)['system']['review_required'])
        payload['rule']['absolute']='1999'
        self.assertTrue(uploaded_investigation(payload)['system']['review_required'])
        payload['rule'].update(absolute='',percentage='0.09')
        self.assertTrue(uploaded_investigation(payload)['system']['review_required'])
        payload['rule'].update(percentage='',always_review=True)
        self.assertTrue(uploaded_investigation(payload)['system']['review_required'])
        for metric,direction in [('SUPPLY_EXPENSE','favorable'),('OPERATING_EXPENSE','favorable'),('OPERATING_INCOME','unfavorable')]:
            payload=request();payload['selection']['metric_id']=metric;payload['performance']=[row(metric,90,100)]
            result=uploaded_investigation(payload)['system']
            self.assertEqual(result['variance']['direction'],direction)
            self.assertIsNone(result['primary_driver'])

    def test_clinical_labor_semantics_are_explicit_and_ambiguous_events_context_only(self):
        payload=request();payload['selection']['metric_id']='LABOR_EXPENSE'
        payload['performance']=[row('LABOR_EXPENSE',12000,10000),row('OVERTIME_HOURS',20,10,'hours','')]
        payload['events'][0]['event_type']='temporary_staffing_vacancy'
        self.assertIsNone(uploaded_investigation(payload)['system']['primary_driver'])
        payload['confirmations']['clinical_labor']=True
        self.assertEqual(uploaded_investigation(payload)['system']['primary_driver'],'Workforce & Operating Expense')
        payload['events'][0]['event_type']='staffing_shortage'
        self.assertIsNone(uploaded_investigation(payload)['system']['primary_driver'])

    def test_unresolved_cannot_be_confirmed_and_request_validation(self):
        payload=request();view=uploaded_investigation(payload)
        index=next(i for i,d in enumerate(view['system']['drivers']) if d['epistemic_state']=='unresolved_driver')
        payload.update(snapshot_id=view['snapshot_id'],decisions={str(index):dict(action='confirm',rationale='Please confirm')})
        with self.assertRaises(ValueError):uploaded_investigation(payload)
        mutations=[lambda p:p['confirmations'].update(closed_month=False),
                   lambda p:p['performance'][1].update(unit='FTE'),
                   lambda p:p['performance'][1].update(actual_value='NaN'),
                   lambda p:p['performance'][1].update(entity_id='OTHER'),
                   lambda p:p['performance'].append(row('PATIENT_VISITS',90,100,'visits','')),
                   lambda p:p['rule'].update(absolute='-1'),
                   lambda p:p.update(analyst_note='Should never be sent'),
                   lambda p:p.update(events=p['events']*1001)]
        for mutation in mutations:
            payload=request();mutation(payload)
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):uploaded_investigation(payload)

    def test_stateless_no_file_or_network_io(self):
        from unittest.mock import patch
        with patch('builtins.open',side_effect=AssertionError('File access')),patch('socket.socket',side_effect=AssertionError('Network access')):
            first=uploaded_investigation(request(True))
            second=uploaded_investigation(request(True))
        self.assertEqual(first,second)
        self.assertEqual(first['decisions'],{})

    def test_mixed_provenance_is_preserved_per_source(self):
        payload=request(True)
        payload['events'][0]['_lineage']['kind']='synthetic'
        result=uploaded_investigation(payload)['system']
        event=next(f for f in result['observed_facts'] if f['fact_type']=='reported_event')
        self.assertEqual(event['evidence'][0]['row_selector']['kind'],'synthetic')
        self.assertEqual(result['variance']['evidence'][0]['row_selector']['kind'],'user_uploaded')
