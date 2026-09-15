from test_scenario import BrowserModelCase
from playwright.sync_api import expect


class InterpretationTests(BrowserModelCase):
    def test_commentary_is_bound_to_current_result_and_cannot_mutate_it(self):
        result = self.evaluate('''
            const {interpret} = await import('/interpretation.js');
            const store=model.createScenarioStore(baseline);
            store.edit('provider_fte','3.5');
            const state=store.snapshot();
            const before=JSON.stringify(state);
            const commentary=interpret(state);
            store.edit('provider_fte','');
            return {commentary, unchanged:before===JSON.stringify(state), invalid:interpret(store.snapshot())};
        ''')
        self.assertTrue(result['unchanged'])
        c=result['commentary']
        self.assertEqual(c['revision'],1)
        self.assertEqual(c['mode'],'offline-deterministic-fallback')
        self.assertIn('no live LLM used',c['disclosure'])
        self.assertIn('−$21,740.40',c['summary'])
        self.assertIn('$243,243.00',str(c['metrics']))
        self.assertIn('Under these synthetic assumptions',c['summary'])
        self.assertIsNone(result['invalid'])

    def test_all_review_actions_are_revision_bound_and_session_only(self):
        result=self.evaluate('''
            const {createReviewSession,REVIEW_ACTIONS}=await import('/interpretation.js');
            const store=model.createScenarioStore(baseline);
            const review=createReviewSession(store);
            store.edit('provider_fte','3.5');
            const before=JSON.stringify(store.snapshot());
            const actions=Object.keys(REVIEW_ACTIONS).map(action=>review.decide(action,1));
            const unchanged=before===JSON.stringify(store.snapshot());
            store.edit('fixed_expense','90000');
            const cleared=review.snapshot().decision;
            let staleRejected=false;
            try {review.decide('retain_baseline',1);} catch {staleRejected=true;}
            store.edit('provider_fte','');
            let invalidRejected=false;
            try {review.decide('retain_baseline',3);} catch {invalidRejected=true;}
            const blocked=review.snapshot();
            store.reset();
            const reset=review.snapshot();
            const fresh=createReviewSession(model.createScenarioStore(baseline)).snapshot();
            return {actions,unchanged,cleared,staleRejected,invalidRejected,blocked,reset,fresh};
        ''')
        self.assertEqual(len(result['actions']),3)
        self.assertTrue(result['unchanged'])
        for action in result['actions']:
            self.assertEqual(action['revision'],1)
            self.assertFalse(action['forecast_updated'])
            self.assertFalse(action['causal_confirmation'])
        self.assertIsNone(result['cleared'])
        self.assertTrue(result['staleRejected'])
        self.assertTrue(result['invalidRejected'])
        self.assertIsNone(result['blocked']['commentary'])
        self.assertFalse(result['blocked']['review_eligible'])
        self.assertIsNone(result['reset']['decision'])
        self.assertIsNone(result['fresh']['decision'])

    def test_executive_summary_and_review_follow_the_model_revision(self):
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click(timeout=1000)
        self.page.get_by_role('textbox',name='Provider FTE scenario',exact=True).fill('3.5')
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        expect(self.page.locator('[data-kpi="operating_income"] .kpi-scenario')).to_have_text('$67,182.80')
        expect(self.page.locator('#commentary-summary')).to_contain_text('−$21,740.40')
        expect(self.page.locator('#commentary-disclosure')).to_have_text('Offline demo — deterministic fallback commentary; no live LLM used.')
        self.page.get_by_role('button',name='Reviewed — retain baseline',exact=True).click()
        expect(self.page.locator('#review-status')).to_contain_text('Reviewed — retain baseline')
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        self.page.locator('#input-provider_fte').fill('')
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        expect(self.page.locator('#summary-status')).to_contain_text('Stale')
        expect(self.page.locator('#commentary-summary')).to_have_text('Commentary unavailable until all scenario inputs are valid.')
        expect(self.page.get_by_role('button',name='Reviewed — retain baseline',exact=True)).to_be_disabled()
        self.page.get_by_role('button',name='Reset to baseline',exact=True).click()
        expect(self.page.locator('#review-status')).to_have_text('Not reviewed for this revision.')

    def test_multiple_changes_have_source_references_and_no_causal_confirmation(self):
        result=self.evaluate('''
            const {interpret}=await import('/interpretation.js');
            const store=model.createScenarioStore(baseline);
            store.edit('provider_fte','3.5');
            store.edit('net_revenue_per_visit','200');
            const state=store.snapshot();
            const commentary=interpret(state);
            const badRevision=interpret({...state,revision:99});
            return {commentary,badRevision,source:state.result};
        ''')
        c=result['commentary']
        self.assertEqual([d['id'] for d in c['drivers']],['provider_fte','net_revenue_per_visit'])
        self.assertEqual(c['revision'],2)
        self.assertIsNone(result['badRevision'])
        self.assertIn('net-rate', ' '.join(c['implications']))
        for metric in c['metrics']:
            self.assertIn('scenario.'+metric['id'],metric['sources'])
        self.assertIn(result['source']['baseline_id'],c['source_label'])
        self.assertNotIn('HCA',c['summary'])
        self.assertNotIn('Tenet',c['summary'])
        self.assertIn('does not confirm an actual cause',c['boundary'])
        self.assertNotIn('will occur',str(c))

    def test_navigation_preserves_review_and_reload_discards_it(self):
        self.page.reload()
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        button=self.page.get_by_role('button',name='Request further investigation',exact=True)
        button.click()
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        self.page.get_by_role('tab',name='Executive Summary',exact=True).click()
        expect(self.page.locator('#review-status')).to_contain_text('Request further investigation')
        self.page.reload()
        expect(self.page.locator('#review-status')).to_have_text('Not reviewed for this revision.')
        self.assertEqual(self.page.evaluate('localStorage.length'),0)
        self.assertEqual(self.page.evaluate('sessionStorage.length'),0)
