"""Record Ticket 1 browser acceptance evidence; no user uploads or external services."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.test_import import ImportTests, PLANNING
from playwright.sync_api import expect

OUT = Path('docs/validation/ticket1-import')
OUT.mkdir(parents=True, exist_ok=True)
ImportTests.setUpClass()
case = ImportTests('test_csv_mapping_validation_and_explicit_confirmation')
case.setUp()
page = case.page
page.set_viewport_size({'width': 1440, 'height': 1000})
requests = []
errors = []
page.on('request', lambda r: requests.append({'url': r.url, 'method': r.method}))
page.on('pageerror', lambda e: errors.append(str(e)))
try:
    page.screenshot(path=str(OUT / '01-upload-desktop.png'), full_page=True)
    page.get_by_label('Choose CSV or XLSX').set_input_files('web/sample-import.xlsx')
    for sheet, role in [('Planning Assumptions','planning'),('Actual vs Forecast','performance'),('Operating Events','events')]:
        page.get_by_label('Dataset role — '+sheet, exact=True).select_option(role)
    page.locator('#import-sheets').screenshot(path=str(OUT / '02-sheet-roles.png'))
    page.get_by_role('button', name='Map columns', exact=True).click()
    page.get_by_label('Numeric percentage encoding').first.select_option('percent')
    page.screenshot(path=str(OUT / '03-column-mapping.png'))
    page.get_by_role('button',name='Validate data',exact=True).click()
    expect(page.locator('#import-validation')).to_contain_text('0 errors')
    page.locator('#import-validation').screenshot(path=str(OUT / '04-validation.png'))
    page.get_by_label('I reviewed all warnings').check()
    page.get_by_role('button',name='Preview normalized data',exact=True).click()
    page.screenshot(path=str(OUT / '05-original-normalized-preview.png'))
    page.locator('#import-transformations').screenshot(path=str(OUT / '06-normalization-register.png'))
    page.get_by_label('I confirm the normalized data').check()
    page.get_by_role('button',name='Confirm import',exact=True).click()
    expect(page.locator('#import-confirmed')).to_contain_text('Planning Assumptions: 3 rows')
    expect(page.locator('#import-confirmed')).to_contain_text('Actual vs Forecast: 3 rows')
    expect(page.locator('#import-confirmed')).to_contain_text('Operating Events: 1 row')
    page.locator('#import-confirmed details').first.locator('summary').click()
    expect(page.locator('#import-confirmed')).to_contain_text('SYNTHETIC SAMPLE')
    page.locator('#import-confirmed').screenshot(path=str(OUT / '07-confirmed-session.png'))
    case.upload(PLANNING.replace(',4,22,',',not a number,22,'))
    page.get_by_role('button',name='Validate data',exact=True).click()
    expect(page.locator('#import-confirmed')).to_contain_text('Planning Assumptions: 3 rows')
    page.locator('#import-validation').screenshot(path=str(OUT / '08-errors-preserve-session.png'))
    page.set_viewport_size({'width':390,'height':844})
    page.locator('#import-validation').scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / '09-mobile-validation.png'))
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile page overflow'
    page.on('dialog',lambda d:d.accept())
    page.reload()
    page.evaluate('window.scrollTo(0,0)')
    expect(page.locator('#import-confirmed')).to_contain_text('No confirmed datasets')
    page.screenshot(path=str(OUT / '10-mobile-upload.png'),full_page=True)
    assert not errors, errors
    assert all(r['url'].startswith(case.url + '/') and r['method']=='GET' for r in requests)
    report={'result':'pass','page_errors':errors,'external_requests':0,'upload_requests':0,'sample_roles':{'planning':3,'performance':3,'events':1},'replacement_failure_preserved_data':True,'reload_discarded_session':True,'viewports':['1440x1000','390x844'],'screenshots':[p.name for p in sorted(OUT.glob('*.png'))]}
    (OUT/'rehearsal.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
finally:
    case.tearDown()
    ImportTests.tearDownClass()
