"""Exercise the authoritative browser module, not a second Python calculator."""
import json
import threading
import unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
from provider_fpa.web import Handler


class BrowserModelCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(channel='chrome', headless=True)
        cls.page = cls.browser.new_page()
        cls.page.goto(f'http://127.0.0.1:{cls.server.server_port}/')
        cls.baseline = json.loads(Path('data/synthetic/scenario/clinic_baseline.json').read_text())

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def evaluate(self, expression, argument=None):
        return self.page.evaluate('async args => { "use strict"; const [baseline, arg] = args; const model = await import("/scenario.js"); ' + expression + ' }', [self.baseline, argument])


class ScenarioTests(BrowserModelCase):
    def setUp(self):
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()

    def test_one_fte_edit_produces_all_reference_outputs(self):
        result = self.evaluate('return model.scenarioResult(baseline, {...baseline.assumptions, provider_fte:"3.5"}, 1);')
        expected = {'capacity':'1386','visits':'1247.4','revenue':'243243','labor':'68607',
                    'supplies':'22453.2','variable_expense':'91060.2','contribution':'152182.8',
                    'operating_income':'67182.8'}
        self.assertEqual(result['scenario'], expected)
        self.assertEqual(result['baseline'], {'capacity':'1584','visits':'1425.6','revenue':'277992','labor':'78408','supplies':'25660.8','variable_expense':'104068.8','contribution':'173923.2','operating_income':'88923.2'})
        self.assertEqual(result['validation']['status'],'valid')
        self.assertEqual(result['impact'], '-21740.4')
        self.assertEqual(result['changes']['visits']['percent'], '-12.5')
        self.assertEqual([d['id'] for d in result['changed_drivers']], ['provider_fte'])

    def test_shared_state_tracks_invalid_drafts_and_reset_without_stale_review(self):
        result = self.evaluate('''
            const store = model.createScenarioStore(baseline);
            const observed = [];
            store.subscribe(state => observed.push(state.revision));
            store.edit('provider_fte','3.5');
            const valid = store.snapshot();
            store.edit('provider_fte','');
            const invalid = store.snapshot();
            store.edit('provider_fte','4.000');
            const noOp = store.snapshot();
            store.edit('fixed_expense','90000');
            store.reset();
            const reset = store.snapshot();
            let protectedResult = false;
            try { valid.result.scenario.revenue = '1'; } catch { protectedResult = true; }
            return {valid, invalid, noOp, reset, observed, protectedResult};
        ''')
        self.assertEqual(result['valid']['result']['impact'], '-21740.4')
        self.assertEqual(result['invalid']['status'], 'invalid')
        self.assertIsNone(result['invalid']['result'])
        self.assertFalse(result['invalid']['review_eligible'])
        self.assertEqual(result['invalid']['last_valid']['revision'], result['valid']['revision'])
        self.assertEqual(result['noOp']['result']['changed_drivers'], [])
        self.assertEqual(result['reset']['result']['impact'], '0')
        self.assertEqual(result['reset']['draft']['provider_fte'], '4.0')
        self.assertEqual(result['observed'], [0,1,2,3,4,5])
        self.assertTrue(result['protectedResult'])

    def test_browser_fte_cell_updates_every_dependent_row(self):
        from playwright.sync_api import expect
        field = self.page.get_by_role('textbox', name='Provider FTE scenario', exact=True)
        expect(field).to_be_visible(timeout=1000)
        field.fill('3.5')
        expected={'capacity':'1,386','visits':'1,247.4','revenue':'$243,243.00','labor':'$68,607.00',
                  'supplies':'$22,453.20','variable_expense':'$91,060.20','contribution':'$152,182.80','operating_income':'$67,182.80'}
        for key, value in expected.items():
            expect(self.page.locator(f'[data-output="{key}"] .scenario-value')).to_have_text(value)
        expect(self.page.locator('#scenario-impact')).to_have_text('−$21,740.40')
        expect(self.page.locator('#scenario-status')).to_contain_text('Current')
        field.fill('')
        expect(self.page.locator('#scenario-status')).to_contain_text('Stale')
        expect(self.page.locator('#input-provider_fte')).to_have_attribute('aria-invalid','true')
        self.page.get_by_role('button',name='Reset scenario').click()
        expect(field).to_have_value('4.0')
        expect(self.page.locator('#scenario-impact')).to_have_text('$0.00')

    def test_every_single_driver_changes_only_its_financial_descendants(self):
        fixtures = [
            ('provider_fte','5','132404', ['capacity','visits','revenue','labor','supplies','variable_expense','contribution','operating_income']),
            ('clinic_days','20','73112', ['capacity','visits','revenue','labor','supplies','variable_expense','contribution','operating_income']),
            ('visits_per_provider_day','20','108248', ['capacity','visits','revenue','labor','supplies','variable_expense','contribution','operating_income']),
            ('utilization','0.8','69598.4', ['visits','revenue','labor','supplies','variable_expense','contribution','operating_income']),
            ('net_revenue_per_visit','200','96051.2', ['revenue','contribution','operating_income']),
            ('labor_per_visit','60','81795.2', ['labor','variable_expense','contribution','operating_income']),
            ('supplies_per_visit','20','86072', ['supplies','variable_expense','contribution','operating_income']),
            ('fixed_expense','90000','83923.2', ['operating_income']),
            ('reimbursement_factor','0.95','75023.6', ['revenue','contribution','operating_income']),
        ]
        for driver, value, income, descendants in fixtures:
            with self.subTest(driver=driver):
                result = self.evaluate('return model.scenarioResult(baseline, {...baseline.assumptions, [arg[0]]:arg[1]}, 1);', [driver,value])
                self.assertEqual(result['scenario']['operating_income'], income)
                self.assertEqual({key for key, delta in result['changes'].items() if delta['amount'] != '0'}, set(descendants))
                self.assertEqual(result['baseline']['operating_income'], '88923.2')

    def test_joint_edits_preserve_financial_identities_and_internal_precision(self):
        from decimal import Decimal
        result = self.evaluate('return model.scenarioResult(baseline, {...baseline.assumptions, provider_fte:"3.5",utilization:"0.8",net_revenue_per_visit:"200",fixed_expense:"90000"}, 1);')
        outputs = result['scenario']
        self.assertEqual(outputs['visits'], '1108.8')
        self.assertEqual(outputs['revenue'], '221760')
        self.assertEqual(outputs['operating_income'], '50817.6')
        self.assertEqual(Decimal(outputs['revenue'])-Decimal(outputs['variable_expense']), Decimal(outputs['contribution']))
        self.assertEqual(Decimal(outputs['labor'])+Decimal(outputs['supplies']), Decimal(outputs['variable_expense']))
        fine = self.evaluate('return model.calculate({...baseline.assumptions,provider_fte:"0.1",clinic_days:"1",visits_per_provider_day:"0.2",utilization:"1",net_revenue_per_visit:"0.1",labor_per_visit:"0.02",supplies_per_visit:"0.03",fixed_expense:"0"}, baseline.month);')
        self.assertEqual(fine['revenue'], '0.002')
        self.assertEqual(fine['operating_income'], '0.001')

    def test_zero_is_valid_but_blank_invalid_and_percent_requires_positive_baseline(self):
        for key in self.baseline['assumptions']:
            with self.subTest(zero_driver=key):
                result = self.evaluate('return model.scenarioResult(baseline, {...baseline.assumptions,[arg]:"0"}, 1);',key)
                self.assertIsNotNone(result['scenario']['operating_income'])
        result = self.evaluate('return model.scenarioResult(baseline, {...baseline.assumptions,provider_fte:"0"}, 1);')
        self.assertEqual(result['scenario']['revenue'], '0')
        self.assertEqual(result['scenario']['operating_income'], '-85000')
        for base, reason in [('0','Baseline is zero.'),('-1','Baseline is negative.')]:
            delta = self.evaluate('return model.change(arg,"5");',base)
            self.assertIsNone(delta['percent'])
            self.assertEqual(delta['percent_reason'],reason)
        cases=[('provider_fte',''),('provider_fte','NaN'),('provider_fte','Infinity'),('provider_fte','-1'),
               ('clinic_days','31'),('clinic_days','1.5'),('utilization','1.01'),('labor_per_visit','-1')]
        for driver, value in cases:
            errors = self.evaluate('return model.validate({...baseline.assumptions,[arg[0]]:arg[1]}, baseline.month).errors;',[driver,value])
            self.assertIn(driver,errors)
        for month in ['2026-13','0000-01','bad']:
            errors = self.evaluate('return model.validate(baseline.assumptions,arg).errors;',month)
            self.assertIn('month',errors)

    def test_public_input_is_refused_and_subscribers_receive_same_result(self):
        result = self.evaluate('''
            let refused=false;
            try { model.createScenarioStore({...baseline,data_kind:'public_benchmark'}); } catch {refused=true;}
            const store=model.createScenarioStore(baseline);
            let analyst, executive;
            store.subscribe(state => analyst=state);
            const unsubscribe=store.subscribe(state => executive=state);
            store.edit('provider_fte','3.5');
            const shared=analyst.result===executive.result;
            const before=store.snapshot();
            unsubscribe();
            store.edit('provider_fte','3');
            return {refused,shared,oldRevision:executive.revision,newRevision:analyst.revision,
              protectedBaseline:before.result.baseline.operating_income};
        ''')
        self.assertTrue(result['refused'])
        self.assertTrue(result['shared'])
        self.assertLess(result['oldRevision'],result['newRevision'])
        self.assertEqual(result['protectedBaseline'],'88923.2')

    def test_shared_store_edits_and_reset_keep_visible_cells_in_sync(self):
        from playwright.sync_api import expect
        self.page.evaluate('async () => {const {scenarioStore} = await import("/scenario-view.js"); scenarioStore.edit("provider_fte","3.5");}')
        expect(self.page.locator('#input-provider_fte')).to_have_value('3.5', timeout=1000)
        self.page.evaluate('async () => {const {scenarioStore} = await import("/scenario-view.js"); scenarioStore.reset();}')
        expect(self.page.locator('#input-provider_fte')).to_have_value('4.0', timeout=1000)
        expect(self.page.locator('#scenario-impact')).to_have_text('$0.00')

    def test_extreme_inputs_fail_safely_and_recover_without_stale_review(self):
        result = self.evaluate("""
            const store = model.createScenarioStore(baseline);
            store.edit('provider_fte', '3.5');
            const valid = store.snapshot().result;
            const rejected = ['1e1000000000000000', '1e-1000000000000000', '9'.repeat(2000)]
                .map(raw => store.edit('fixed_expense', raw));
            store.reset();
            store.edit('provider_fte', '1e900');
            const derived = store.edit('net_revenue_per_visit', '1e900');
            const recovered = store.reset();
            return {valid, rejected, derived, recovered};
        """)
        for state in result['rejected']:
            self.assertEqual(state['status'], 'invalid')
            self.assertIsNone(state['result'])
            self.assertFalse(state['review_eligible'])
            self.assertEqual(state['last_valid'], result['valid'])
        self.assertEqual(result['derived']['status'], 'invalid')
        self.assertIsNone(result['derived']['result'])
        self.assertEqual(result['recovered']['status'], 'valid')
        self.assertEqual(result['recovered']['result']['impact'], '0')
