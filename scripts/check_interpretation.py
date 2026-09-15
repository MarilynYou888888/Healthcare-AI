"""Ticket 3 visual/browser acceptance, against the running local app."""
import os
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1100})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(os.environ.get('DEMO_URL','http://127.0.0.1:8501/'))
    expect(page.locator('[data-kpi="operating_income"] .kpi-scenario')).to_have_text('$88,923.20')
    # Keyboard navigation follows the vertical tabs pattern.
    page.get_by_role('tab',name='Executive Summary',exact=True).focus()
    page.keyboard.press('ArrowDown')
    expect(page.get_by_role('tab',name='Scenario Model',exact=True)).to_have_attribute('aria-selected','true')
    page.locator('#input-provider_fte').fill('3.5')
    table=page.locator('[data-output="operating_income"] .scenario-value').inner_text()
    page.get_by_role('tab',name='Executive Summary',exact=True).click()
    expect(page.locator('[data-kpi="operating_income"] .kpi-scenario')).to_have_text(table)
    expect(page.locator('#summary-impact-value')).to_have_text('−$21,740.40')
    expect(page.locator('#commentary-disclosure')).to_have_text('Offline demo — deterministic fallback commentary; no live LLM used.')
    assert page.locator('#executive-view').get_attribute('data-revision')==page.locator('#summary-commentary').get_attribute('data-revision')
    page.get_by_role('button',name='Mark for forecast-assumption review',exact=True).click()
    expect(page.locator('#review-status')).to_contain_text('No forecast updated')
    page.screenshot(path='/tmp/provider-fpa-ticket3.png',full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth'), 'Mobile overflow'
    page.screenshot(path='/tmp/provider-fpa-ticket3-mobile.png',full_page=True)
    # No external credentials/network needed after local loading.
    page.route('**/*',lambda route:route.abort())
    page.get_by_role('tab',name='Scenario Model',exact=True).click()
    page.locator('#input-provider_fte').fill('3.0')
    page.get_by_role('tab',name='Executive Summary',exact=True).click()
    expect(page.locator('#review-status')).to_have_text('Not reviewed for this revision.')
    expect(page.locator('#commentary-summary')).to_contain_text('$45,442.40')
    assert not errors,errors
    browser.close()
    print('Ticket 3 browser checks passed: keyboard, shared revision, offline commentary, review invalidation, mobile. Screenshots: /tmp/provider-fpa-ticket3.png and /tmp/provider-fpa-ticket3-mobile.png')
