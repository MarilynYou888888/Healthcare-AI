"""Ticket 1 browser acceptance. Start python -m provider_fpa.web first."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('DEMO_URL', 'http://127.0.0.1:8501/'))
    expect(page.locator('#income')).to_have_text('$88,923.20')
    expect(page.locator('#benchmark-note')).to_contain_text('HCA Healthcare')
    expect(page.locator('#benchmark-cards')).to_contain_text('$75.600B')
    assert page.locator('.reference input, .reference select, [contenteditable="true"]').count() == 0
    expect(page.get_by_text('SYNTHETIC · PLANNING BASELINE')).to_be_visible()
    baseline = page.locator('.model-grid').inner_text()
    page.get_by_role('button', name='Tenet Healthcare', exact=True).click()
    expect(page.locator('#benchmark-note')).to_contain_text('Tenet Healthcare')
    expect(page.locator('#benchmark-cards')).to_contain_text('$21.310B')
    assert page.locator('.model-grid').inner_text() == baseline
    page.locator('#sources-button').click()
    expect(page.locator('#source-rows')).to_contain_text('Not disclosed')
    expect(page.locator('#source-rows')).to_contain_text('Same-hospital')
    links = page.locator('#source-rows a').evaluate_all('(links) => links.map(a => a.href)')
    assert links and all('sec.gov/Archives/' in link for link in links)
    page.locator('#sources-button').click()
    page.get_by_role('button', name='HCA Healthcare', exact=True).click()
    expect(page.locator('#benchmark-note')).to_contain_text('HCA Healthcare')
    assert page.locator('.model-grid').inner_text() == baseline
    page.locator('#sources-button').click()
    expect(page.locator('#company-notes')).to_contain_text('excludes Corporate and other')
    expect(page.locator('#source-rows')).to_contain_text('instant · 2025-12-31')
    page.locator('#sources-button').click()
    page.locator('.formula-section summary').click()
    expect(page.locator('#formulas')).to_contain_text('Provider FTE × clinic days')
    page.locator('.formula-section summary').click()
    screenshot = Path(os.environ.get('DEMO_SCREENSHOT', '/tmp/provider-fpa-ticket1.png'))
    page.screenshot(path=str(screenshot), full_page=True)
    page.set_viewport_size({'width': 390, 'height': 844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile layout overflows'
    page.route('**/api/benchmarks/THC', lambda route: route.fulfill(status=503, body='unavailable'))
    page.get_by_role('button', name='Tenet Healthcare', exact=True).click()
    expect(page.locator('#benchmark-state')).to_contain_text('Public reference unavailable')
    expect(page.locator('#income')).to_have_text('$88,923.20')
    assert not errors, errors
    browser.close()
    print(f'Browser acceptance passed; screenshot: {screenshot}')
