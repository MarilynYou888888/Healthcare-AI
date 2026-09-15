"""Tickets 1–2 browser acceptance. Start python -m provider_fpa.web first."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('DEMO_URL', 'http://127.0.0.1:8501/'))
    income = page.locator('[data-output="operating_income"] .scenario-value')
    expect(income).to_have_text('$88,923.20')
    expect(page.locator('#benchmark-note')).to_contain_text('HCA Healthcare')
    expect(page.locator('#benchmark-cards')).to_contain_text('$75.600B')
    assert page.locator('.reference input, .reference select, [contenteditable="true"]').count() == 0
    expect(page.get_by_text('SYNTHETIC · SCENARIO MODEL')).to_be_visible()
    base = page.locator('.baseline-value').all_text_contents()
    field = page.get_by_role('textbox', name='Provider FTE scenario', exact=True)
    field.fill('3.5')
    expect(income).to_have_text('$67,182.80')
    expect(page.locator('#scenario-impact')).to_have_text('−$21,740.40')
    before_switch = page.locator('#financial-rows').inner_text()
    page.get_by_role('button', name='Tenet Healthcare', exact=True).click()
    expect(page.locator('#benchmark-note')).to_contain_text('Tenet Healthcare')
    expect(page.locator('#benchmark-cards')).to_contain_text('$21.310B')
    assert page.locator('#financial-rows').inner_text() == before_switch
    assert page.locator('.baseline-value').all_text_contents() == base
    page.locator('#sources-button').click()
    expect(page.locator('#source-rows')).to_contain_text('Not disclosed')
    expect(page.locator('#source-rows')).to_contain_text('Same-hospital')
    links = page.locator('#source-rows a').evaluate_all('(links) => links.map(a => a.href)')
    assert links and all('sec.gov/Archives/' in link for link in links)
    page.locator('#sources-button').click()
    page.get_by_role('button', name='HCA Healthcare', exact=True).click()
    expect(page.locator('#benchmark-note')).to_contain_text('HCA Healthcare')
    page.locator('#sources-button').click()
    expect(page.locator('#company-notes')).to_contain_text('excludes Corporate and other')
    expect(page.locator('#source-rows')).to_contain_text('instant · 2025-12-31')
    page.locator('#sources-button').click()
    expect(page.locator('#financial-rows')).to_contain_text('Provider FTE × Clinic operating days')
    assert page.locator('#financial-rows input').count() == 0
    screenshot = Path(os.environ.get('DEMO_SCREENSHOT', '/tmp/provider-fpa-ticket2.png'))
    page.screenshot(path=str(screenshot), full_page=True)
    # From a real input event through the next painted frame, with all requests blocked.
    requests = []
    page.on('request', lambda request: requests.append(request.url))
    page.route('**/*', lambda route: route.abort())
    latency = page.evaluate('''async () => {
        const samples=[];
        const input=document.getElementById('input-provider_fte');
        for (const value of ['4.0','3.5','4.0','3.5','4.0','3.5','4.0','3.5','4.0','3.5']) {
            const start=performance.now();
            input.value=value;
            input.dispatchEvent(new Event('input',{bubbles:true}));
            await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            samples.push(performance.now()-start);
        }
        return samples;
    }''')
    assert max(latency) < 200, latency
    assert not requests, f'Unexpected recalculation network requests: {requests}'
    recalculation_requests = len(requests)
    expect(income).to_have_text('$67,182.80')
    field.fill('')
    expect(page.locator('#scenario-status')).to_contain_text('Stale')
    expect(field).to_have_attribute('aria-invalid', 'true')
    expect(income).to_have_text('$67,182.80')
    page.get_by_role('button', name='Reset scenario').click()
    expect(field).to_have_value('4.0')
    expect(income).to_have_text('$88,923.20')
    assert page.locator('.baseline-value').all_text_contents() == base
    page.get_by_role('textbox',name='Utilization scenario',exact=True).fill('80')
    expect(income).to_have_text('$69,598.40')
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile layout overflows'
    page.get_by_role('button', name='Tenet Healthcare', exact=True).click()
    expect(page.locator('#benchmark-state')).to_contain_text('Public reference unavailable')
    expect(income).to_have_text('$69,598.40')
    assert not errors, errors
    browser.close()
    print(json.dumps({'browser_acceptance':'passed', 'latency_ms':latency,
                      'max_latency_ms':max(latency), 'recalculation_requests':recalculation_requests,
                      'screenshot':str(screenshot)}, indent=2))
