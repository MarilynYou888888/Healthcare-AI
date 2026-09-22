"""Ticket 2 browser/model boundaries using normalized user imports."""
from test_scenario import BrowserModelCase


class UserScenarioTests(BrowserModelCase):
    def test_uploaded_baseline_uses_shared_engine_and_result_measures(self):
        result = self.evaluate('''
          const {planningBaseline} = await import('/user-workflows.js');
          const row={entity_id:'NSC',entity_name:'Nashville Specialty Clinic',period:'2026-08',
            scenario_name:'Approved plan',currency:'CAD',source:'Finance plan',provider_fte:'4',
            operating_days:'22',visits_per_provider_day:'18',utilization_rate:'0.9',
            net_revenue_per_visit:'195',variable_labor_cost_per_visit:'55',
            variable_supply_cost_per_visit:'18',fixed_operating_expense:'85000',reimbursement_factor:'1',
            _lineage:{file:'plan.csv',sheet:'CSV',row:2,kind:'user_uploaded'}};
          const base=planningBaseline(row,1), store=model.createScenarioStore(base);
          store.edit('provider_fte','3.5');
          const state=store.snapshot(), {scenarioPresentation}=await import('/presentation.js');
          const view=scenarioPresentation(state.result);
          const {createReviewSession}=await import('/interpretation.js');
          const review=createReviewSession(store);review.decide('retain_baseline',state.revision);
          store.edit('provider_fte','');
          const invalid={...store.snapshot(),review:review.snapshot()};
          store.reset();
          return {base,state,invalid,reset:store.snapshot(),row,
            same:view.bridge===state.result.presentation.bridge,
            identityChanges:planningBaseline(row,1).baseline_id!==base.baseline_id};
        ''')
        self.assertEqual(result['state']['result']['impact'], '-21740.4')
        self.assertEqual(result['state']['result']['currency'], 'CAD')
        self.assertEqual(result['state']['result']['output_units']['revenue'], 'CAD')
        self.assertEqual(result['base']['assumptions']['provider_fte'], '4')
        self.assertEqual(result['row']['provider_fte'], '4')
        self.assertTrue(result['same'])
        self.assertTrue(result['identityChanges'])
        self.assertFalse(result['invalid']['review']['review_eligible'])
        self.assertIsNone(result['invalid']['review']['decision'])
        self.assertEqual(result['reset']['result']['impact'], '0')

import unittest
import test_import as import_support
PLANNING=import_support.PLANNING
from playwright.sync_api import expect


class UserWorkspaceBrowserTests(unittest.TestCase):
    setUpClass=import_support.ImportTests.__dict__['setUpClass']
    tearDownClass=import_support.ImportTests.__dict__['tearDownClass']
    setUp=import_support.ImportTests.setUp
    tearDown=import_support.ImportTests.tearDown
    upload=import_support.ImportTests.upload

    def confirm(self):
        self.page.get_by_role('button',name='Validate data',exact=True).click()
        expect(self.page.locator('#import-validation')).to_contain_text('0 errors')
        self.page.get_by_label('I reviewed all warnings').check()
        self.page.get_by_role('button',name='Preview normalized data',exact=True).click()
        self.page.get_by_label('I confirm the normalized data').check()
        if self.page.locator('#import-replace-check').is_visible():self.page.locator('#import-replace-check').check()
        self.page.get_by_role('button',name='Confirm import',exact=True).click()

    def sample(self):
        self.page.get_by_label('Choose CSV or XLSX').set_input_files('web/sample-import.xlsx')
        for sheet,role in [('Planning Assumptions','planning'),('Actual vs Forecast','performance'),('Operating Events','events')]:
            self.page.get_by_label('Dataset role — '+sheet,exact=True).select_option(role)
        self.page.get_by_role('button',name='Map columns',exact=True).click()
        self.page.get_by_label('Numeric percentage encoding').first.select_option('percent')
        self.confirm()
        self.page.locator('#import-open-workflows').click()
        expect(self.page.locator('#user-analysis')).to_be_visible()

    def test_import_to_model_summary_stale_reset_and_investigation(self):
        requests=[];errors=[]
        self.page.on('request',lambda r:requests.append((r.url,r.method,r.post_data)))
        self.page.on('pageerror',lambda e:errors.append(str(e)))
        self.sample()
        self.page.locator('#input-provider_fte').fill('3.5')
        expect(self.page.locator('[data-output="revenue"] .scenario-value')).to_have_text('$243,243.00')
        expect(self.page.locator('[data-driver="provider_fte"] .baseline-value')).to_have_text('4.0')
        self.page.locator('#user-open-summary').click()
        expect(self.page.locator('[data-kpi="operating_income"] .kpi-scenario')).to_have_text('$67,182.80')
        revision=self.page.locator('#executive-view').get_attribute('data-revision')
        for chart in ['income-bridge-chart','expense-mix-chart','scenario-comparison-chart','summary-model-logic']:
            expect(self.page.locator('#'+chart)).to_have_attribute('data-revision',revision)
        self.page.locator('[data-action="retain_baseline"]').click()
        expect(self.page.locator('#review-status')).to_contain_text('Reviewed')
        self.page.locator('#user-open-model').click()
        self.page.locator('#input-provider_fte').fill('')
        self.page.locator('#user-open-summary').click()
        expect(self.page.locator('#summary-status')).to_contain_text('Stale')
        expect(self.page.locator('[data-action="retain_baseline"]')).to_be_disabled()
        self.page.locator('#summary-reset').click()
        expect(self.page.locator('#summary-impact-value')).to_have_text('$0.00')
        self.page.locator('#user-analyst-note').fill('Private analyst note; never evidence')
        self.page.locator('#user-open-investigation').click()
        expect(self.page.locator('#user-analyst-note')).to_have_value('')
        self.page.locator('#user-run-investigation').click()
        expect(self.page.locator('#investigation-status')).to_contain_text('Confirm the closed month')
        self.page.locator('#user-closed').check();self.page.locator('#user-forecast').check();self.page.locator('#user-override').check()
        self.page.locator('#user-run-investigation').click()
        expect(self.page.locator('#investigation-conclusion')).to_contain_text('Unresolved')
        expect(self.page.locator('#investigation-timing')).to_contain_text('unresolved')
        expect(self.page.locator('#investigation-queue')).to_contain_text('No automatic materiality rule configured')
        self.assertTrue(all(self.page.locator('[data-investigation-action="confirm"]').nth(i).is_disabled() for i in range(self.page.locator('[data-investigation-action="confirm"]').count())))
        self.assertFalse(errors,errors)
        self.assertTrue(all(url.startswith(self.url+'/') for url,_,_ in requests))
        posted=[body for _,method,body in requests if method=='POST']
        self.assertEqual(len(posted),1)
        self.assertNotIn('Private analyst note',posted[0])
        self.assertNotIn('provider_fte',posted[0])

    def test_selection_drafts_notes_currency_reimport_and_no_state_leak(self):
        header,data=PLANNING.strip().split('\n')
        header+=',Scenario\n'
        rows=[data+',Base',data+',Stretch',data.replace('2026-08','2026-09')+',Base',data.replace('NSC,Nashville Specialty Clinic','OTHER,Other clinic')+',Base']
        self.upload((header+'\n'.join(rows)+'\n').replace('USD','CAD'))
        self.confirm();self.page.locator('#import-open-workflows').click()
        expect(self.page.locator('#user-source')).to_contain_text('CAD')
        self.page.locator('#input-provider_fte').fill('3.5')
        expect(self.page.locator('#scenario-impact')).to_have_text('−CAD 21,740.40')
        self.page.locator('#user-analyst-note').fill('Base note')
        self.page.once('dialog',lambda d:d.dismiss())
        self.page.locator('#user-scenario').select_option('1')
        expect(self.page.locator('#user-scenario')).to_have_value('0')
        expect(self.page.locator('#input-provider_fte')).to_have_value('3.5')
        self.page.once('dialog',lambda d:d.accept())
        self.page.locator('#user-scenario').select_option('1')
        expect(self.page.locator('#input-provider_fte')).to_have_value('4')
        expect(self.page.locator('#user-analyst-note')).to_have_value('')
        self.page.locator('#user-period').select_option('2026-09')
        expect(self.page.locator('#user-source')).to_contain_text('2026-09')
        self.page.locator('#user-entity').select_option('OTHER')
        expect(self.page.locator('#user-source')).to_contain_text('Other clinic')
        expect(self.page.locator('#user-period')).to_have_value('2026-08')
        self.page.locator('#user-open-summary').click()
        expect(self.page.locator('#expense-mix-chart')).to_contain_text('CAD')
        self.page.locator('#user-back-import').click()
        self.upload(PLANNING.replace('USD','CAD').replace(',4,22,',',5,22,'))
        self.confirm();self.page.locator('#import-open-workflows').click()
        self.page.locator('#user-open-model').click()
        expect(self.page.locator('#input-provider_fte')).to_have_value('5')
        expect(self.page.locator('#user-analyst-note')).to_have_value('')

    def test_performance_only_events_only_and_user_review_invalidation(self):
        performance=('Entity ID,Clinic,Month,Metric ID,Actual,Forecast,Unit,Currency,Source\n'
                     'NSC,Nashville,2026-08,PROVIDER_AVAILABLE_DAYS,18,20,days,,Ops close\n')
        events=('Entity ID,Month,Event,Start,End,Description,Source\n'
                'NSC,2026-08,provider_pto,2026-08-01,2026-08-10,Reported leave,Ops report\n')
        def role_upload(content,role):
            self.page.get_by_label('Choose CSV or XLSX').set_input_files({'name':'independent.csv','mimeType':'text/csv','buffer':content.encode()})
            self.page.get_by_label('Dataset role',exact=False).first.select_option(role)
            self.page.get_by_role('button',name='Map columns',exact=True).click()
            self.confirm()
        role_upload(events,'events')
        self.page.locator('#import-open-workflows').click()
        expect(self.page.locator('#user-analysis-status')).to_contain_text('Actual vs Forecast data is required')
        expect(self.page.locator('#user-open-investigation')).to_be_disabled()
        self.page.locator('#user-back-import').click()
        role_upload(performance,'performance')
        self.page.locator('#import-open-workflows').click()
        expect(self.page.locator('#user-open-model')).to_be_disabled()
        expect(self.page.locator('#user-open-investigation')).to_be_enabled()
        self.page.locator('#user-closed').check();self.page.locator('#user-forecast').check()
        self.page.locator('#user-run-investigation').click()
        expect(self.page.locator('#investigation-conclusion')).to_contain_text('System primary driver: Provider Availability')
        self.page.locator('[data-investigation-action="confirm"]').click()
        expect(self.page.locator('.driver-review-state')).to_contain_text('Analyst-Confirmed Cause')
        self.page.locator('#user-absolute').fill('1')
        expect(self.page.locator('#investigation-content')).to_be_hidden()
        self.page.locator('#user-run-investigation').click()
        expect(self.page.locator('.driver-review-state')).to_contain_text('Supported Driver')
        expect(self.page.locator('.driver-decision')).to_contain_text('Not reviewed')
        self.page.get_by_text('Optional structured timing evidence',exact=True).click()
        self.page.locator('#user-normalization').fill('2026-09')
        self.page.locator('#user-timing-source').fill('Coverage restored per approved staffing plan')
        self.page.locator('#user-run-investigation').click()
        expect(self.page.locator('#investigation-timing')).to_contain_text('temporary')
        self.page.on('dialog',lambda d:d.accept())
        self.page.reload()
        expect(self.page.locator('#import-confirmed')).to_contain_text('No confirmed datasets')
        self.assertEqual(self.page.evaluate('localStorage.length+sessionStorage.length'),0)

    def test_loopback_api_boundary_is_stateless_bounded_and_does_not_log_payloads(self):
        import contextlib
        import io
        from test_uploaded_investigation import request
        payload=request(True)
        captured=io.StringIO()
        with contextlib.redirect_stderr(captured):
            response=self.page.request.post(self.url+'/api/user-investigation',data=payload,headers={'Origin':self.url})
            self.assertEqual(response.status,200)
            snapshot=response.json()['snapshot_id']
            second=self.page.request.post(self.url+'/api/user-investigation',data=payload,headers={'Origin':self.url})
            self.assertEqual(second.json()['snapshot_id'],snapshot)
            for origin in ['http://external.example','null','http://localhost:9']:
                response=self.page.request.post(self.url+'/api/user-investigation',data=payload,headers={'Origin':origin})
                self.assertEqual(response.status,400)
            response=self.page.request.post(self.url+'/api/user-investigation',data='x'*(1024*1024+1),headers={'Origin':self.url,'Content-Type':'application/json'})
            self.assertEqual(response.status,400)
            self.assertNotIn('Traceback',response.text())
        self.assertEqual(captured.getvalue(),'')
