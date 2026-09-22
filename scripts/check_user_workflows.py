"""Record Ticket 2 local acceptance demo with synthetic onboarding data."""
import json
import sys
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'tests')]
from test_user_workflows import UserWorkspaceBrowserTests
from playwright.sync_api import expect

out=Path('docs/validation/ticket2-user-workflows');out.mkdir(parents=True,exist_ok=True)
UserWorkspaceBrowserTests.setUpClass()
case=UserWorkspaceBrowserTests();case.setUp();page=case.page
errors=[];requests=[]
page.on('pageerror',lambda e:errors.append(str(e)))
page.on('request',lambda r:requests.append((r.url,r.method)))
try:
    page.set_viewport_size({'width':1440,'height':1000})
    case.sample()
    page.locator('#input-provider_fte').fill('3.5')
    expect(page.locator('#scenario-impact')).to_have_text('−$21,740.40')
    page.screenshot(path=str(out/'01-imported-model.png'),full_page=True)
    page.locator('#user-open-summary').click()
    page.screenshot(path=str(out/'02-executive-summary.png'),full_page=True)
    page.locator('#summary-model-logic summary').click()
    page.locator('#summary-model-logic').screenshot(path=str(out/'03-shared-calculation-trace.png'))
    page.locator('#user-open-investigation').click()
    page.locator('#user-closed').check();page.locator('#user-forecast').check();page.locator('#user-override').check()
    page.locator('#user-run-investigation').click()
    expect(page.locator('#investigation-conclusion')).to_contain_text('Unresolved')
    page.locator('#investigation-facts details').first.locator('summary').click()
    page.screenshot(path=str(out/'04-unresolved-investigation.png'),full_page=True)
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#user-open-summary').click()
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile overflow'
    page.screenshot(path=str(out/'05-mobile-summary.png'),full_page=True)
    assert not errors,errors
    assert all(url.startswith(case.url+'/') for url,_ in requests)
    assert all(method=='GET' or url.endswith('/api/user-investigation') for url,method in requests)
    report={'result':'pass','scenario_impact':'-21740.4','revenue':'243243','operating_income':'67182.8',
            'insufficient_evidence':'Unresolved','external_requests':0,'raw_upload_requests':0,
            'local_normalized_investigation_requests':sum(method=='POST' for _,method in requests),
            'browser_errors':errors,'viewports':['1440x1000','390x844']}
    (out/'rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
finally:
    case.tearDown();UserWorkspaceBrowserTests.tearDownClass()
