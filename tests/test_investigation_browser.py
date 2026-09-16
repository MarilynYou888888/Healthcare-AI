"""Human workflow through the local HTTP/browser boundary."""
from playwright.sync_api import expect
from test_scenario import BrowserModelCase


class InvestigationBrowserTests(BrowserModelCase):
    def test_evidence_review_and_handoff_preserve_scenario_revision(self):
        self.page.reload()
        self.page.get_by_role('tab', name='Variance Investigation', exact=True).click()
        expect(self.page.locator('#investigation-status')).to_contain_text('C01 · CL001 · 2026-03')
        expect(self.page.locator('#investigation-drivers')).to_contain_text('Provider Availability')
        self.page.locator('#investigation-facts summary').first.click()
        expect(self.page.locator('#investigation-facts')).to_contain_text('financial_values.csv')
        before = self.page.evaluate('async () => (await import("/scenario-view.js")).scenarioStore.snapshot()')
        provider = self.page.locator('[data-driver-family="Provider Availability"]')
        provider.get_by_role('button', name='Confirm supported cause', exact=True).click()
        expect(provider).to_contain_text('Analyst-Confirmed Cause')
        self.page.get_by_role('button', name='Explore Provider FTE', exact=True).click()
        expect(self.page.locator('#model-view')).to_be_visible()
        expect(self.page.locator('#input-provider_fte')).to_be_focused()
        expect(self.page.locator('#investigation-handoff')).to_contain_text('C01 · CL001 · 2026-03')
        expect(self.page.locator('#investigation-handoff')).to_contain_text('No inputs or approved forecast changed')
        after = self.page.evaluate('async () => (await import("/scenario-view.js")).scenarioStore.snapshot()')
        self.assertEqual(before, after)
        self.page.get_by_role('tab', name='Variance Investigation', exact=True).click()
        self.page.locator('#investigation-case').select_option('C04')
        expect(self.page.locator('#investigation-status')).to_contain_text('C04 · CL004 · 2026-06')
        expect(self.page.locator('#investigation-conclusion')).to_contain_text('Unresolved')
        expect(self.page.locator('#investigation-narrative')).to_contain_text('Insufficient evidence')
        self.assertEqual(self.page.locator('#investigation-handoffs button').count(), 0)
        self.assertEqual(self.page.get_by_role('button', name='Confirm supported cause', exact=True).and_(self.page.locator(':enabled')).count(), 0)
        unresolved = self.page.locator('[data-driver-family="Unresolved"]')
        unresolved.get_by_role('button', name='Keep unresolved', exact=True).click()
        expect(unresolved).to_contain_text('Session decision: Keep unresolved')
        unresolved.get_by_role('button', name='Request further investigation', exact=True).click()
        expect(unresolved).to_contain_text('Session decision: Request further investigation')
        self.page.locator('#investigation-case').select_option('C01')
        expect(provider).to_contain_text('Analyst-Confirmed Cause')
        provider.get_by_role('button', name='Reject cause', exact=True).click()
        expect(provider).to_contain_text('Session decision: Reject cause')
        self.assertEqual(self.page.locator('#investigation-handoffs button').count(), 0)
        self.page.reload()
        self.page.get_by_role('tab', name='Variance Investigation', exact=True).click()
        expect(provider).to_contain_text('Session decision: Not reviewed')

    def test_weather_queue_override_and_scenario_review_isolation(self):
        self.page.reload()
        self.page.get_by_role('button', name='Reviewed — retain baseline', exact=True).click()
        review_before = self.page.locator('#review-status').inner_text()
        self.page.get_by_role('tab', name='Variance Investigation', exact=True).click()
        self.page.locator('#investigation-case').select_option('C03')
        expect(self.page.locator('#investigation-status')).to_contain_text('C03 · CL003 · 2026-05')
        external = self.page.locator('[data-driver-family="External Disruption"]')
        expect(external).to_contain_text('Observed Fact · Role: upstream context')
        expect(external.get_by_role('button',name='Confirm supported cause',exact=True)).to_be_disabled()
        self.page.get_by_role('button',name='Explore Clinic operating days',exact=True).click()
        expect(self.page.locator('#input-clinic_days')).to_be_focused()
        expect(self.page.locator('#input-clinic_days')).to_have_value('22')
        self.assertEqual(self.page.locator('#review-status').inner_text(),review_before)
        self.page.get_by_role('tab', name='Variance Investigation', exact=True).click()
        self.page.locator('#investigation-case').select_option('C01')
        expect(self.page.locator('#investigation-status')).to_contain_text('C01 · CL001 · 2026-03')
        self.page.locator('#investigation-target').select_option('["CLINIC_CLOSURE_DAYS","operational_metric_variance"]')
        expect(self.page.locator('#investigation-queue')).to_contain_text('Not selected')
        expect(self.page.locator('#investigation-disclosure')).to_contain_text('Commentary withheld')
        self.page.get_by_role('button', name='Add via Analyst Override',exact=True).click()
        expect(self.page.locator('#investigation-queue')).to_contain_text('analyst override')
        expect(self.page.locator('#investigation-override')).to_be_hidden()
        self.assertEqual(self.page.locator('#review-status').inner_text(),review_before)

    def test_http_rejects_stale_confirmation_and_never_serves_gold(self):
        client = self.page.request
        base = client.get(self.page.url + 'api/investigation?case=C04').json()
        response = client.post(self.page.url + 'api/investigation/review', data={
            'context': base['context'], 'snapshot_id':base['snapshot_id'],
            'decisions':{'0':{'action':'confirm'}},
        })
        self.assertEqual(response.status,400)
        for path in ('data/synthetic_benchmark/gold', 'api/investigation/gold', 'provider_fpa/evaluation.py'):
            self.assertEqual(client.get(self.page.url + path).status,404)
        response = client.post(self.page.url + 'api/investigation/review',data={
            'context':base['context'], 'snapshot_id':'stale','decisions':{},
        })
        self.assertEqual(response.status,400)

    def test_handoff_keeps_input_validation_accessible_after_context_is_cleared(self):
        self.page.reload()
        self.page.get_by_role('tab', name='Variance Investigation', exact=True).click()
        expect(self.page.locator('#investigation-status')).to_contain_text('C01 · CL001')
        self.page.get_by_role('button',name='Explore Provider FTE',exact=True).click()
        field = self.page.locator('#input-provider_fte')
        self.assertEqual(set(field.get_attribute('aria-describedby').split()),
                         {'error-provider_fte', 'investigation-handoff'})
        self.page.get_by_role('tab',name='Variance Investigation',exact=True).click()
        self.page.locator('#investigation-case').select_option('C04')
        expect(self.page.locator('#investigation-status')).to_contain_text('C04 · CL004')
        self.page.get_by_role('tab',name='Scenario Model',exact=True).click()
        expect(field).to_have_attribute('aria-describedby', 'error-provider_fte')
        field.fill('')
        expect(field).to_have_attribute('aria-invalid','true')
        expect(self.page.locator('#error-provider_fte')).not_to_have_text('')
