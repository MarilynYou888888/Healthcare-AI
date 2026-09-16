"""Ticket 4 visual acceptance against the running local demo."""
import os
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width':1440,'height':1000})
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(os.environ.get('DEMO_URL','http://127.0.0.1:8501/'))
    page.get_by_role('tab',name='Variance Investigation',exact=True).click()
    expect(page.locator('#investigation-status')).to_contain_text('C01 · CL001')
    page.locator('#investigation-facts summary').nth(1).click()
    page.screenshot(path='/tmp/provider-fpa-ticket4-c01.png',full_page=True)
    provider=page.locator('[data-driver-family="Provider Availability"]')
    provider.get_by_role('button',name='Confirm supported cause',exact=True).click()
    expect(provider).to_contain_text('Analyst-Confirmed Cause')
    page.get_by_role('button',name='Explore Provider FTE',exact=True).click()
    expect(page.locator('#input-provider_fte')).to_have_value('4.0')
    page.screenshot(path='/tmp/provider-fpa-ticket4-handoff.png',full_page=True)
    page.get_by_role('tab',name='Variance Investigation',exact=True).click()
    page.locator('#investigation-case').select_option('C04')
    expect(page.locator('#investigation-status')).to_contain_text('C04 · CL004')
    expect(page.locator('#investigation-conclusion')).to_contain_text('Unresolved')
    page.screenshot(path='/tmp/provider-fpa-ticket4-c04.png',full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile overflow'
    page.screenshot(path='/tmp/provider-fpa-ticket4-mobile.png',full_page=True)
    # A failed investigation fetch must not disable the independent scenario engine.
    page.route('**/api/investigation?*',lambda route:route.abort())
    page.locator('#investigation-case').select_option('C03')
    expect(page.locator('#investigation-content')).to_be_hidden()
    expect(page.locator('#investigation-status')).not_to_contain_text('Loading')
    page.get_by_role('tab',name='Scenario Model',exact=True).click()
    page.locator('#input-provider_fte').fill('3.5')
    expect(page.locator('#scenario-impact')).to_have_text('−$21,740.40')
    assert not errors, errors
    browser.close()
    print('Ticket 4 visual checks passed: evidence, confirmation, non-mutating handoff, C04 refusal, mobile, isolated request failure.')
    print('Screenshots: /tmp/provider-fpa-ticket4-{c01,c04,handoff,mobile}.png')
