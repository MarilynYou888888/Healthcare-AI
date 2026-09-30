"""Ticket 3 benchmark context and zero-token commentary acceptance seams."""
import unittest
from pathlib import Path

from playwright.sync_api import expect

import test_import as import_support
from test_scenario import BrowserModelCase
from test_user_workflows import UserWorkspaceBrowserTests


BENCHMARK = ('Company,Period,Business Segment,Metric ID,Metric Name,Value,Unit,Source,Notes,Source URL\n'
             'Company A,FY2026,Consolidated,LABOR_TO_REVENUE,Labor / Revenue,0.42,ratio,Submitted filing,Analyst supplied,https://example.com/filing\n')


class CommentaryTests(BrowserModelCase):
    def test_commentary_is_deterministic_current_result_bound_and_multi_driver(self):
        value = self.evaluate('''
          const {composeScenarioCommentary, composeInvestigationCommentary} = await import('/commentary.js');
          const first=model.scenarioResult(baseline,{...baseline.assumptions,provider_fte:'3.5'},1);
          const second=model.scenarioResult(baseline,{...baseline.assumptions,provider_fte:'3.5',fixed_expense:'90000'},2);
          const unresolved=composeInvestigationCommentary({snapshot_id:'s1',variance:{id:'REV_NET_PATIENT',currency:'USD',absolute:'-26700',actual:'73300',forecast_or_expected:'100000',direction:'unfavorable'},primary_driver:null,drivers:[],timing_classification:'unresolved'});
          return {first:composeScenarioCommentary(first),second:composeScenarioCommentary(second),unresolved};
        ''')
        self.assertEqual(value['first']['mode'], 'deterministic-rule-based')
        self.assertEqual(len(value['first']['sentences']), 5)
        self.assertIn('−$21,740.40', value['first']['summary'])
        self.assertIn('Fixed operating expense changes by +$5,000.00', value['second']['summary'])
        self.assertNotEqual(value['first']['summary'], value['second']['summary'])
        self.assertIn('remains Unresolved', value['unresolved']['summary'])
        self.assertNotIn('caused by', value['unresolved']['summary'].lower())
        self.assertIn('No LLM or external API is used', value['first']['disclosure'])
        reviewed = self.evaluate('''
          const {composeInvestigationCommentary} = await import('/commentary.js');
          return composeInvestigationCommentary({snapshot_id:'s2',variance:{id:'VISITS',absolute:'-10',actual:'90',forecast_or_expected:'100',direction:'unfavorable'},primary_driver:'provider_availability',drivers:[{role:'primary',driver_family:'provider_availability',epistemic_state:'rejected_driver'},{role:'contributing',driver_family:'staffing_shortage',epistemic_state:'analyst_confirmed_cause'}],timing_classification:'temporary'}, {drivers:[{role:'primary',driver_family:'provider_availability',epistemic_state:'rejected_driver'},{role:'contributing',driver_family:'staffing_shortage',epistemic_state:'analyst_confirmed_cause'}],timing_classification:'temporary'});
        ''')
        self.assertIn('contributing driver', reviewed['summary'])
        self.assertIn('primary cause remains unresolved', reviewed['summary'])
        self.assertIn('temporary', reviewed['summary'])

    def test_commentary_disappears_for_invalid_draft_and_has_no_network_provider(self):
        requests=[]
        self.page.on('request',lambda request:requests.append(request.url))
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        self.page.locator('#input-provider_fte').fill('3.5')
        expect(self.page.locator('#commentary-summary')).to_contain_text('Provider FTE changed')
        self.page.locator('#input-provider_fte').fill('')
        expect(self.page.locator('#commentary-summary')).to_have_text('Commentary unavailable until all scenario inputs are valid.')
        self.assertTrue(all(url.startswith(f'http://127.0.0.1:{self.server.server_port}/') for url in requests))


class BenchmarkWorkspaceTests(unittest.TestCase):
    setUpClass=import_support.ImportTests.__dict__['setUpClass']
    tearDownClass=import_support.ImportTests.__dict__['tearDownClass']
    setUp=import_support.ImportTests.setUp
    tearDown=import_support.ImportTests.tearDown

    def confirm(self):
        self.page.get_by_label('Numeric percentage encoding').first.select_option('fraction')
        self.page.get_by_role('button',name='Validate data',exact=True).click()
        expect(self.page.locator('#import-validation')).to_contain_text('0 errors')
        if self.page.locator('#import-warnings').is_visible():self.page.get_by_label('I reviewed all warnings').check()
        self.page.get_by_role('button',name='Preview normalized data',exact=True).click()
        self.page.get_by_label('I confirm the normalized data').check()
        self.page.get_by_role('button',name='Confirm import',exact=True).click()

    def test_custom_benchmark_import_no_benchmark_and_public_switches_are_context_only(self):
        requests=[];errors=[]
        self.page.on('request',lambda request:requests.append((request.url,request.method)))
        self.page.on('pageerror',lambda error:errors.append(str(error)))
        self.page.get_by_label('Choose CSV or XLSX').set_input_files({'name':'analyst-benchmark.csv','mimeType':'text/csv','buffer':BENCHMARK.encode()})
        self.page.get_by_label('Dataset role',exact=False).first.select_option('benchmark')
        self.page.get_by_role('button',name='Map columns',exact=True).click()
        self.confirm()
        expect(self.page.locator('#import-confirmed')).to_contain_text('Custom Benchmark: 1 row')
        self.page.locator('#import-open-workflows').click()
        expect(self.page.locator('#user-benchmark')).to_have_value('none')
        expect(self.page.locator('#user-benchmark-status')).to_contain_text('No Benchmark selected')
        self.page.locator('#user-benchmark').select_option('custom')
        expect(self.page.locator('#user-benchmark-status')).to_contain_text('USER UPLOADED')
        expect(self.page.locator('#user-benchmark-context')).to_contain_text('Company A')
        self.page.locator('#user-benchmark').select_option('HCA')
        expect(self.page.locator('#user-benchmark-status')).to_contain_text('BUILT-IN PUBLIC')
        expect(self.page.locator('#user-benchmark-context')).to_contain_text('FY2025')
        expect(self.page.locator('#user-benchmark-context')).to_contain_text('Form 10-K')
        self.page.locator('#user-benchmark').select_option('THC')
        expect(self.page.locator('#user-benchmark-status')).to_contain_text('BUILT-IN PUBLIC')
        self.page.locator('#user-benchmark').select_option('none')
        expect(self.page.locator('#user-analysis-status')).to_contain_text('Custom Benchmark context is available')
        self.assertFalse(self.page.locator('#user-open-model').is_enabled())
        self.assertFalse(self.page.locator('#user-open-investigation').is_enabled())
        self.assertFalse(errors,errors)
        self.assertTrue(all(url.startswith(self.url + '/') for url,_ in requests))
        self.assertFalse(any(method=='POST' for _,method in requests))


if __name__ == '__main__':
    unittest.main()
