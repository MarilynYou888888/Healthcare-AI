"""V2.1 payer mix context and explicit reimbursement opt-in seams."""
import unittest

try:
    from test_scenario import BrowserModelCase
except ModuleNotFoundError:
    from tests.test_scenario import BrowserModelCase


class PayerMixTests(BrowserModelCase):
    def test_weighted_blended_reimbursement_is_deterministic(self):
        result=self.page.evaluate('''async()=>{
          const {payerMixSummary}=await import('/payer-mix.js');
          return payerMixSummary([
            {entity_id:'C01',period:'2026-08',payer_category:'Commercial',payer_mix_share:'0.42',net_revenue_per_visit:'240'},
            {entity_id:'C01',period:'2026-08',payer_category:'Medicare',payer_mix_share:'0.31',net_revenue_per_visit:'170'},
            {entity_id:'C01',period:'2026-08',payer_category:'Medicaid',payer_mix_share:'0.12',net_revenue_per_visit:'130'},
            {entity_id:'C01',period:'2026-08',payer_category:'Self Pay',payer_mix_share:'0.15',net_revenue_per_visit:'210'}
          ],'C01','Clinic','2026-08');
        }''')
        self.assertEqual(result['blended_net_revenue_per_visit'],'200.6')
        self.assertTrue(result['reimbursement_complete'])

    def test_missing_reimbursement_does_not_create_financial_impact(self):
        result=self.page.evaluate('''async()=>{
          const {payerMixSummary,payerMixContextText}=await import('/payer-mix.js');
          const summary=payerMixSummary([{entity_id:'C01',period:'2026-08',payer_category:'Commercial',payer_mix_share:'1'}],'C01','Clinic','2026-08');
          return {summary,text:payerMixContextText(summary)};
        }''')
        self.assertFalse(result['summary']['reimbursement_complete'])
        self.assertEqual(result['summary']['blended_net_revenue_per_visit'],'')
        self.assertIn('required to calculate a financial impact',result['text'])

    def test_explicit_opt_in_recalculates_existing_scenario_engine(self):
        result=self.evaluate('''const {scenarioResult}=model;
          const summary=(()=>{
            const rows=[{entity_id:baseline.entity_id,period:baseline.month,payer_category:'Commercial',payer_mix_share:'1',net_revenue_per_visit:'250'}];
            return rows[0].net_revenue_per_visit;
          })();
          const before=scenarioResult(baseline,baseline.assumptions,0),after=scenarioResult(baseline,{...baseline.assumptions,net_revenue_per_visit:summary},1);
          return {before:before.scenario.revenue,after:after.scenario.revenue,changed:after.changed_drivers.map(driver=>driver.id)};''')
        self.assertNotEqual(result['before'],result['after'])
        self.assertIn('net_revenue_per_visit',result['changed'])


if __name__ == '__main__':
    unittest.main()
