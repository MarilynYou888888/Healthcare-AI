"""Timed 85-second UI rehearsal with narration cues; no recorded/spoken audio.

Uses actual browser interactions and assertions. Intentional reading pauses are
reported transparently, not used as a performance benchmark. Run against the
local demo. Only local requests are permitted throughout the rehearsal.
"""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright, expect

base=os.environ.get('DEMO_URL','http://127.0.0.1:8501/')
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[]
    external=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    def route(request):
        if urlsplit(request.request.url).hostname not in ('localhost','127.0.0.1'):
            external.append(request.request.url)
            request.abort()
        else:
            request.continue_()
    page.route('**/*',route)
    started=time.monotonic()
    checkpoints=[]
    def cue(at,description):
        remaining=at-(time.monotonic()-started)
        if remaining>0: page.wait_for_timeout(remaining*1000)
        checkpoints.append({'seconds':round(time.monotonic()-started,2),'cue':description})
        print(json.dumps(checkpoints[-1]),flush=True)
    page.goto(base)
    expect(page.locator('#summary-impact-value')).to_have_text('$0.00')
    cue(0,'User and manual FP&A workflow pain; synthetic baseline and offline disclosure')
    cue(8,'Public HCA / Tenet source-grounded context, separate from clinic inputs')
    page.locator('#benchmark-jump').click()
    expect(page.locator('#benchmark-ratio-chart')).to_contain_text('43.46%')
    expect(page.locator('#benchmark-ratio-chart')).to_contain_text('40.85%')
    cue(16,'Open editable synthetic clinic model; all downstream outputs are read-only')
    page.get_by_role('tab',name='Scenario Model',exact=True).click()
    expect(page.locator('#input-provider_fte')).to_have_value('4.0')
    cue(22,'Change one input: Provider FTE 4.0 to 3.5')
    page.locator('#input-provider_fte').fill('3.5')
    expected={'capacity':'1,386','visits':'1,247.4','revenue':'$243,243.00','labor':'$68,607.00','supplies':'$22,453.20','contribution':'$152,182.80','operating_income':'$67,182.80'}
    for key,value in expected.items():expect(page.locator(f'[data-output="{key}"] .scenario-value')).to_have_text(value)
    expect(page.locator('#scenario-impact')).to_have_text('−$21,740.40')
    for selector in ['#input-provider_fte','#scenario-impact','[data-output="operating_income"]']:
        box=page.locator(selector).bounding_box()
        assert box and 0<=box['y'] and box['y']+box['height']<=900,(selector,box)
    cue(30,'Executive Summary: revenue downside partially offset by variable cost savings')
    page.get_by_role('tab',name='Executive Summary',exact=True).click()
    expect(page.locator('#income-bridge-chart [data-component="labor"]')).to_have_attribute('data-value','9801')
    cue(42,'Financial comparison and dynamic expense composition')
    page.locator('#summary-analysis').scroll_into_view_if_needed()
    cue(48,'Expand deterministic model trace and highlight affected dependencies')
    page.locator('#summary-model-logic summary').click()
    page.locator('#summary-model-logic').scroll_into_view_if_needed()
    cue(54,'Offline fallback commentary interprets results; no live AI or financial writes')
    page.locator('#summary-commentary').scroll_into_view_if_needed()
    expect(page.locator('#commentary-disclosure')).to_contain_text('no live LLM used')
    expect(page.locator('#commentary-summary')).to_contain_text('−$21,740.40')
    cue(66,'Secondary investigation: C04 insufficient evidence remains unresolved')
    page.get_by_role('tab',name='Variance Investigation',exact=True).click()
    page.locator('#investigation-case').select_option('C04')
    expect(page.locator('#investigation-status')).to_contain_text('C04 · CL004')
    expect(page.locator('#investigation-conclusion')).to_contain_text('Unresolved')
    page.locator('#investigation-conclusion').scroll_into_view_if_needed()
    cue(75,'Human judgment: request further investigation rather than inventing a cause')
    unresolved=page.locator('[data-driver-family="Unresolved"]')
    unresolved.get_by_role('button',name='Request further investigation',exact=True).click()
    expect(unresolved).to_contain_text('Session decision: Request further investigation')
    unresolved.scroll_into_view_if_needed()
    cue(85,'End: deterministic calculations → disclosed interpretation → analyst judgment')
    assert not errors,errors
    assert not external,external
    elapsed=round(time.monotonic()-started,2)
    report={'kind':'automated timed UI rehearsal with narration cues; no recorded or spoken audio',
            'elapsed_seconds':elapsed,'target_seconds':85,'viewport':{'width':1440,'height':900},
            'checkpoints':checkpoints,'external_requests':external,'page_errors':errors,'outcome':'passed',
            'feedback':['All single-input outputs and income impact fit the recording viewport.',
                        'Summary, composition and trace require deliberate short scrolls as scripted.',
                        'C04 requires scrolling to its review card; keep the case selector change visible first.',
                        'Narration pacing remains a guide until the portfolio owner records the voiceover.']}
    output=Path(os.environ.get('REHEARSAL_REPORT','/tmp/provider-fpa-ticket5-rehearsal.json'))
    output.write_text(json.dumps(report,indent=2)+'\n')
    browser.close()
    print(f'Rehearsal passed in {elapsed}s. Report: {output}',flush=True)
