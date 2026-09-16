"""Shared-result presentation and recruiting-view acceptance."""
from test_scenario import BrowserModelCase


class PresentationTests(BrowserModelCase):
    def test_bridge_and_expense_mix_derive_from_the_same_result(self):
        result = self.evaluate('''
          const {scenarioPresentation} = await import('/presentation.js');
          const source=model.scenarioResult(baseline,{...baseline.assumptions,provider_fte:'3.5'},7);
          const view=scenarioPresentation(source);
          return {same:view.source===source,view};
        ''')
        self.assertTrue(result['same'])
        view=result['view']
        self.assertEqual(view['revision'],7)
        self.assertEqual([b['impact'] for b in view['bridge']],['88923.2','-34749','9801','3207.6','0','67182.8'])
        self.assertEqual(view['bridge'][-2]['end'],'67182.8')
        self.assertEqual(view['expenses']['total'],'176060.2')
        self.assertEqual([i['amount'] for i in view['expenses']['items']],['68607','22453.2','85000'])
        self.assertEqual(view['comparison'][0]['scenario'],'243243')
        self.assertEqual([n['id'] for n in view['trace'] if n['affected']],
                         ['capacity','visits','revenue','labor','supplies','variable_expense','contribution','operating_income'])

    def test_negative_income_zero_expense_and_margin_states_are_honest(self):
        views=self.evaluate('''
          const {scenarioPresentation}=await import('/presentation.js');
          return [
            scenarioPresentation(model.scenarioResult(baseline,{...baseline.assumptions,provider_fte:'0'},1)),
            scenarioPresentation(model.scenarioResult(baseline,{...baseline.assumptions,labor_per_visit:'0',supplies_per_visit:'0',fixed_expense:'0'},2)),
            scenarioPresentation(model.scenarioResult(baseline,{...baseline.assumptions,fixed_expense:'90000'},3))
          ];
        ''')
        self.assertEqual(views[0]['bridge'][-1]['end'],'-85000')
        self.assertIsNone(views[0]['margin']['scenario'])
        self.assertIsNone(views[0]['margin']['change_pp'])
        self.assertEqual(views[1]['expenses']['total'],'0')
        self.assertTrue(all(i['share'] is None for i in views[1]['expenses']['items']))
        self.assertEqual(views[2]['bridge'][-2]['impact'],'-5000')
        self.assertEqual([n['id'] for n in views[2]['trace'] if n['affected']],['operating_income'])

    def test_chart_revisions_tooltips_and_trace_follow_single_fte_edit(self):
        from playwright.sync_api import expect
        self.page.reload()
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        self.page.locator('#input-provider_fte').fill('3.5')
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        expect(self.page.locator('#income-bridge-chart')).to_be_visible()
        revision=self.page.locator('#executive-view').get_attribute('data-revision')
        for chart in ('income-bridge-chart','expense-mix-chart','scenario-comparison-chart','summary-model-logic'):
            expect(self.page.locator('#'+chart)).to_have_attribute('data-revision',revision)
        labor=self.page.locator('#income-bridge-chart [data-component="labor"]')
        expect(labor).to_have_attribute('data-value','9801')
        labor.focus()
        expect(self.page.locator('#income-bridge-chart [role="tooltip"]')).to_contain_text('+$9,801.00')
        self.page.keyboard.press('Escape')
        expect(self.page.locator('#income-bridge-chart [role="tooltip"]')).to_be_hidden()
        expect(self.page.locator('#expense-mix-chart')).to_contain_text('$176.1K')
        self.page.locator('#summary-model-logic summary').click()
        expect(self.page.locator('[data-trace="capacity"]')).to_have_attribute('data-affected','true')
        expect(self.page.locator('[data-trace="capacity"]')).to_contain_text('1,386')
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        self.page.locator('#input-provider_fte').fill('')
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        expect(self.page.locator('#income-bridge-chart')).to_have_attribute('data-stale','true')
        expect(self.page.locator('#summary-status')).to_contain_text('Stale')

    def test_public_comparison_preserves_lineage_and_missing_values(self):
        result=self.evaluate('''
          const {benchmarkComparison}=await import('/benchmark-view.js');
          const companies=await Promise.all(['HCA','THC'].map(t=>fetch('/api/benchmarks/'+t).then(r=>r.json())));
          const rows=benchmarkComparison(companies);
          const hca=companies[0].metrics.find(m=>m.metric_id==='LABOR_RATIO'&&m.period==='FY2025'&&m.business_segment==='Consolidated');
          const missing=benchmarkComparison([{...companies[0],metrics:[]},companies[1]]);
          let refused=false;
          try{benchmarkComparison([{data_kind:'synthetic',metrics:[]}]);}catch{refused=true;}
          return {same:rows[0].metrics[0].metric===hca,rows,missing,refused};
        ''')
        self.assertTrue(result['same'])
        self.assertTrue(result['refused'])
        self.assertIsNone(result['missing'][0]['metrics'][0]['metric'])
        for row in result['rows']:
            for company in row['metrics']:
                metric=company['metric']
                self.assertTrue(metric['source_url'].startswith('https://www.sec.gov/Archives/'))
                self.assertTrue(metric['parent_metric_ids'])
                self.assertEqual(metric['business_segment'],'Consolidated')

    def test_all_drivers_bridge_reconciles_and_result_is_never_modified(self):
        from decimal import Decimal
        records=self.evaluate('''
          const {scenarioPresentation}=await import('/presentation.js');
          return Object.entries({provider_fte:'3.5',clinic_days:'20',visits_per_provider_day:'20',utilization:'.8',net_revenue_per_visit:'180',labor_per_visit:'60',supplies_per_visit:'20',fixed_expense:'95000',reimbursement_factor:'.95'}).map(([id,value])=>{
            const source=model.scenarioResult(baseline,{...baseline.assumptions,[id]:value},1);
            const before=JSON.stringify(source),view=scenarioPresentation(source);
            return {unchanged:before===JSON.stringify(source),source,bridge:view.bridge};
          });
        ''')
        for record in records:
            self.assertTrue(record['unchanged'])
            bridge=record['bridge']
            self.assertEqual(sum(Decimal(b['impact']) for b in bridge[:-1]),Decimal(record['source']['scenario']['operating_income']))

    def test_public_selection_and_full_demo_reset_do_not_leak_approvals(self):
        from playwright.sync_api import expect
        self.page.reload()
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        self.page.locator('#input-provider_fte').fill('3.5')
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        self.page.get_by_role('button',name='Reviewed — retain baseline',exact=True).click()
        before=self.page.locator('#summary-impact-value').inner_text()
        self.page.get_by_role('button',name='Tenet Healthcare',exact=True).click()
        expect(self.page.locator('#benchmark-note')).to_contain_text('Tenet Healthcare')
        self.assertEqual(before,self.page.locator('#summary-impact-value').inner_text())
        self.page.get_by_role('tab',name='Variance Investigation',exact=True).click()
        expect(self.page.locator('#investigation-status')).to_contain_text('C01 · CL001')
        provider=self.page.locator('[data-driver-family="Provider Availability"]')
        provider.get_by_role('button',name='Confirm supported cause',exact=True).click()
        expect(provider).to_contain_text('Analyst-Confirmed Cause')
        self.page.get_by_role('button',name='Reset demo session ↻',exact=True).click()
        expect(self.page.locator('#summary-impact-value')).to_have_text('$0.00')
        expect(self.page.locator('#review-status')).to_have_text('Not reviewed for this revision.')
        self.page.get_by_role('tab',name='Variance Investigation',exact=True).click()
        expect(provider).to_contain_text('Session decision: Not reviewed')
