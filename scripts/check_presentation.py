"""Ticket 5 chart/visual acceptance against the running local app."""
import json
import os
from playwright.sync_api import sync_playwright, expect

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.goto(os.environ.get('DEMO_URL','http://127.0.0.1:8501/'))
    expect(page.locator('#income-bridge-chart [data-component="scenario"]')).to_have_attribute('data-value','88923.2')
    page.screenshot(path='/tmp/provider-fpa-ticket5-baseline.png',full_page=False)
    page.get_by_role('tab',name='Scenario Model',exact=True).click()
    page.locator('#input-provider_fte').fill('3.5')
    expect(page.locator('#scenario-impact')).to_have_text('−$21,740.40')
    page.screenshot(path='/tmp/provider-fpa-ticket5-model.png',full_page=False)
    page.get_by_role('tab',name='Executive Summary',exact=True).click()
    expect(page.locator('#income-bridge-chart [data-component="scenario"]')).to_have_attribute('data-value','67182.8')
    # Capture after the intentionally short visual interpolation has settled.
    page.wait_for_timeout(350)
    page.screenshot(path='/tmp/provider-fpa-ticket5-summary.png',full_page=False)
    page.locator('#summary-analysis').scroll_into_view_if_needed()
    page.screenshot(path='/tmp/provider-fpa-ticket5-composition.png',full_page=False)
    page.locator('#summary-model-logic summary').click()
    page.locator('#summary-model-logic').scroll_into_view_if_needed()
    page.screenshot(path='/tmp/provider-fpa-ticket5-trace.png',full_page=False)
    page.locator('#benchmark-comparison-panel > summary').click()
    expect(page.locator('#benchmark-ratio-chart')).to_contain_text('43.46%')
    expect(page.locator('#benchmark-ratio-chart')).to_contain_text('40.85%')
    page.locator('#benchmark-comparison-panel').scroll_into_view_if_needed()
    page.screenshot(path='/tmp/provider-fpa-ticket5-benchmarks.png',full_page=False)
    for width in [390,768,1024,1440]:
        page.set_viewport_size({'width':width,'height':900})
        for tab in ['Executive Summary','Scenario Model','Variance Investigation']:
            page.get_by_role('tab',name=tab,exact=True).click()
            assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'),(width,tab)
    page.set_viewport_size({'width':390,'height':844})
    page.get_by_role('tab',name='Executive Summary',exact=True).click()
    page.screenshot(path='/tmp/provider-fpa-ticket5-mobile.png',full_page=True)
    page.emulate_media(reduced_motion='reduce')
    assert page.locator('#income-bridge-chart rect').first.evaluate('(e)=>getComputedStyle(e).transitionDuration')=='0s'
    assert not errors,errors
    browser.close()
    print(json.dumps({'visual_acceptance':'passed','responsive_widths':[390,768,1024,1440],'page_errors':errors}))
