"""Ticket 1 tests at the browser workflow and normalized-import boundaries."""
import threading
import unittest
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright, expect
from provider_fpa.web import Handler

PLANNING = ('Clinic ID,Clinic,Month,FTE Count,Work Days,Visits Per Provider Day,Utilization,Rev / Visit,Variable Labor Cost Per Visit,Variable Supply Cost Per Visit,Fixed Operating Expense,Reimbursement Factor,Currency\n'
            'NSC,Nashville Specialty Clinic,2026-08,4,22,18,90,195,55,18,85000,1,USD\n')

class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(channel='chrome', headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def setUp(self):
        self.page = self.browser.new_page()
        self.page.set_default_timeout(3000)
        self.page.goto(self.url + '/import')

    def tearDown(self):
        self.page.close()

    def upload(self, text=PLANNING, name='my own file.csv'):
        self.page.get_by_label('Choose CSV or XLSX').set_input_files({'name': name, 'mimeType': 'text/csv', 'buffer': text.encode()})
        self.page.get_by_label('Dataset role', exact=False).first.select_option('planning')
        self.page.get_by_role('button', name='Map columns', exact=True).click()
        self.page.get_by_label('Numeric percentage encoding').first.select_option('percent')

    def test_csv_mapping_validation_and_explicit_confirmation(self):
        self.upload()
        expect(self.page.get_by_label('Map FTE Count')).to_have_value('provider_fte')
        expect(self.page.get_by_label('Map Work Days')).to_have_value('operating_days')
        expect(self.page.get_by_label('Map Rev / Visit')).to_have_value('net_revenue_per_visit')
        self.page.get_by_role('button', name='Validate data', exact=True).click()
        expect(self.page.locator('#import-validation')).to_contain_text('0 errors')
        self.page.get_by_label('I reviewed all warnings').check()
        self.page.get_by_role('button', name='Preview normalized data', exact=True).click()
        expect(self.page.locator('#import-preview')).to_contain_text('0.9')
        expect(self.page.locator('#import-confirmed')).to_contain_text('No confirmed datasets')
        self.page.get_by_label('I confirm the normalized data').check()
        self.page.get_by_role('button', name='Confirm import', exact=True).click()
        expect(self.page.locator('#import-confirmed')).to_contain_text('Planning Assumptions: 1 row')

    def test_sample_workbook_multiple_sheet_roles_and_original_preview(self):
        from pathlib import Path
        with self.page.expect_download() as download:
            self.page.get_by_role('link', name='Download sample workbook').click()
        sample = download.value.path()
        self.assertTrue(Path(sample).read_bytes().startswith(b'PK'))
        self.page.get_by_label('Choose CSV or XLSX').set_input_files({'name': 'independent.xlsx', 'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'buffer': Path(sample).read_bytes()})
        for sheet, role in [('Planning Assumptions','planning'),('Actual vs Forecast','performance'),('Operating Events','events')]:
            self.page.get_by_label('Dataset role — '+sheet, exact=True).select_option(role)
        self.page.get_by_role('button', name='Map columns', exact=True).click()
        self.page.get_by_label('Numeric percentage encoding').first.select_option('percent')
        self.page.get_by_role('button', name='Validate data', exact=True).click()
        expect(self.page.locator('#import-validation')).to_contain_text('0 errors')
        self.page.get_by_label('I reviewed all warnings').check()
        self.page.get_by_role('button', name='Preview normalized data', exact=True).click()
        expect(self.page.locator('#import-preview')).to_contain_text('Planning Assumptions · Original')
        self.page.get_by_label('I confirm the normalized data').check()
        self.page.get_by_role('button', name='Confirm import', exact=True).click()
        for role in ['Planning Assumptions','Actual vs Forecast','Operating Events']:
            expect(self.page.locator('#import-confirmed')).to_contain_text(role+':')

    def validate_contract(self, rows, role='planning', settings=None, mapping=None):
        return self.page.evaluate('''async ({rows,role,settings,mapping}) => {
          const {suggestMappings}=await import('/import-schema.js');
          const {validateImport}=await import('/import-validation.js');
          const sheet={name:'Analyst data',rows:rows.map(r=>r.map(v=>typeof v==='object'?v:{v:String(v),t:'s'})),merges:[]};
          return validateImport([{sheet,fileName:'analyst.csv',role,headerRow:1,mapping:mapping??suggestMappings(rows[0],role),constants:{},settings:settings??{percent:'percent'}}]);
        }''', {'rows':rows,'role':role,'settings':settings,'mapping':mapping})

    def planning_rows(self):
        import csv, io
        return list(csv.reader(io.StringIO(PLANNING)))

    def test_mixed_percentage_scales_are_not_silently_normalized(self):
        rows=self.planning_rows()
        other=rows[1].copy(); other[2]='2026-09'; other[6]='0.9'; rows.append(other)
        result=self.validate_contract(rows)
        self.assertFalse(result['valid'])
        self.assertTrue(any('mixed' in i['problem'].lower() for i in result['issues']))

    def test_errors_required_numeric_duplicate_units_and_currency(self):
        for index,value in [(3,'three'),(3,''),(4,'0'),(4,'32'),(7,'-1'),(11,'0'),(12,'ZZZ')]:
            with self.subTest(index=index,value=value):
                rows=self.planning_rows();rows[1][index]=value
                result=self.validate_contract(rows)
                self.assertFalse(result['valid'])
                self.assertTrue(all(i['row'] and i['column'] and i['correction'] for i in result['issues'] if i['severity']=='ERROR'))
        rows=self.planning_rows(); rows.append(rows[1].copy())
        self.assertTrue(any('Duplicate' in i['problem'] for i in self.validate_contract(rows)['issues']))
        rows=[['entity_id','entity_name','period','metric_id','metric_name','actual_value','forecast_value','unit','currency'],['A','Clinic','2026-08','VISITS','Visits','10','9','USD','USD']]
        result=self.validate_contract(rows,'performance')
        self.assertFalse(result['valid'])
        self.assertTrue(any('unit' in i['problem'].lower() for i in result['issues']))

    def test_alias_collision_and_semantic_ambiguity_require_user_action(self):
        rows=self.planning_rows();rows[0][3]='Provider Count'
        result=self.validate_contract(rows)
        self.assertFalse(result['valid'])
        self.assertTrue(any('ambiguous business' in i['problem'] for i in result['issues']))
        self.assertTrue(self.validate_contract(rows,settings={'percent':'percent','confirmSemantics':True})['valid'])
        rows=self.planning_rows();rows[0].append('Provider FTE');rows[1].append('4')
        self.assertFalse(self.validate_contract(rows)['valid'])

    def test_failed_replacement_preserves_confirmed_data_and_reload_discards(self):
        self.test_csv_mapping_validation_and_explicit_confirmation()
        self.upload(PLANNING.replace(',4,22,',',bad,22,'))
        self.page.get_by_role('button',name='Validate data',exact=True).click()
        expect(self.page.locator('#import-validation')).not_to_contain_text('0 errors')
        expect(self.page.locator('#import-confirmed')).to_contain_text('Planning Assumptions: 1 row')
        expect(self.page.get_by_role('button',name='Preview normalized data',exact=True)).to_be_disabled()
        self.page.on('dialog',lambda d:d.accept())
        self.page.reload()
        expect(self.page.locator('#import-confirmed')).to_contain_text('No confirmed datasets')

    def test_import_has_no_external_requests_or_upload_requests_or_persistence(self):
        requests=[]
        self.page.on('request',lambda r:requests.append((r.url,r.method)))
        self.test_csv_mapping_validation_and_explicit_confirmation()
        self.assertTrue(all(url.startswith(self.url+'/') and method=='GET' for url,method in requests))
        self.assertEqual(self.page.evaluate('localStorage.length + sessionStorage.length'),0)
        self.assertEqual(self.page.evaluate('async()=> (await indexedDB.databases()).length'),0)

    def test_xlsx_percent_dates_and_formula_values_are_explicit(self):
        rows=self.planning_rows()
        rows[1][6]={'v':'0.9','t':'n','percent':True,'w':'90%'}
        rows[1][2]={'v':'46235','t':'n','date':'2026-08-01','w':'8/1/2026'}
        rows[1][3]={'v':'4','t':'n','formula':True}
        result=self.validate_contract(rows,settings={'percent':''})
        self.assertTrue(result['valid'],result['issues'])
        self.assertEqual(result['datasets']['planning'][0]['utilization_rate'],'0.9')
        self.assertTrue(any('Cached formula' in i['problem'] for i in result['issues']))
        self.assertTrue(any(t['field']=='period' and t['normalized']=='2026-08' for t in result['transformations']))

    def test_custom_benchmark_percent_and_events_import(self):
        rows=[['company','period','business_segment','metric_id','metric_name','value','unit','source'],['Company A','FY2026','Consolidated','LABOR_TO_REVENUE','Labor / Revenue','0.42','percent','Public filing']]
        result=self.validate_contract(rows,'benchmark',{'percent':'fraction'})
        self.assertTrue(result['valid'],result['issues'])
        self.assertEqual(result['datasets']['benchmark'][0]['value'],'0.42')
        self.assertEqual(result['datasets']['benchmark'][0]['unit'],'ratio')
        events=[['entity_id','period','event_type','start_date','end_date','description','observed_value','unit','source'],['A','2026-08','clinic_closure','2026-08-01','','Reported closure','2','days','Ops summary']]
        result=self.validate_contract(events,'events')
        self.assertTrue(result['valid'],result['issues'])
        self.assertTrue(any('No analytical entity' in i['problem'] for i in result['issues']))

    def worker_parse(self, data, name='ordinary.xlsx'):
        import base64
        return self.page.evaluate('''async ({data,name}) => new Promise(resolve=>{
          const worker=new Worker('/import-worker.js');
          const timeout=setTimeout(()=>{worker.terminate();resolve({error:'Test worker timeout'})},20000);
          worker.onmessage=e=>{clearTimeout(timeout);worker.terminate();resolve(e.data)};
          worker.postMessage({file:new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],name)});
        })''', {'data':base64.b64encode(data).decode(),'name':name})

    def make_xlsx(self, rows, sheet='My regional data', edits=''):
        import base64
        encoded=self.page.evaluate('''async ({rows,sheet,edits})=>{
          if(!window.XLSX){await new Promise(resolve=>{const script=document.createElement('script');script.src='/vendor/xlsx.full.min.js';script.onload=resolve;document.head.append(script);});}
          const book=XLSX.utils.book_new(),ws=XLSX.utils.aoa_to_sheet(rows);
          if(edits==='percent'){ws.G2={t:'n',v:0.9,z:'0%'};}
          if(edits==='formula'){ws.D2={t:'n',v:4,f:'2+2'};}
          if(edits==='missing_formula'){ws.D2={t:'n',f:'2+2'};}
          if(edits==='merge'){ws['!merges']=[{s:{r:1,c:0},e:{r:1,c:1}}];}
          if(edits==='hidden'){book.Workbook={Sheets:[{name:sheet,Hidden:1}]};}
          if(edits==='date1904'){book.Workbook={WBProps:{date1904:true}};ws.C2={t:'n',v:44773,z:'yyyy-mm-dd'};}
          XLSX.utils.book_append_sheet(book,ws,sheet);
          return XLSX.write(book,{type:'base64',bookType:'xlsx'});
        }''',{'rows':rows,'sheet':sheet,'edits':edits})
        return base64.b64decode(encoded)

    def test_independent_xlsx_sheet_header_row_and_manual_mapping(self):
        rows=self.planning_rows();rows[0][3]='Staffing assumption'
        data=self.make_xlsx([['Regional analyst workbook'],*rows])
        self.page.get_by_label('Choose CSV or XLSX').set_input_files({'name':'regional actual name.xlsx','mimeType':'application/octet-stream','buffer':data})
        self.page.get_by_label('Header row — My regional data').fill('2')
        self.page.get_by_label('Header row — My regional data').press('Tab')
        self.page.get_by_label('Dataset role — My regional data',exact=True).select_option('planning')
        self.page.get_by_role('button',name='Map columns',exact=True).click()
        self.page.get_by_label('Map Staffing assumption').select_option('provider_fte')
        self.page.get_by_label('Numeric percentage encoding').select_option('percent')
        self.page.get_by_role('button',name='Validate data',exact=True).click()
        expect(self.page.locator('#import-validation')).to_contain_text('0 errors')

    def test_worker_rejects_resource_limits_and_damaged_archives(self):
        import io,zipfile,struct
        for data,name,expected in [(b'x'*(10*1024*1024+1),'big.csv','10 MiB'),(b'a,'*101+b'\n1,2','wide.csv','100 columns'),(b'not an archive','fake.xlsx','not an XLSX'),(b'a,b\n"unclosed','bad.csv','CSV row'),(b'a,b','macro.xlsm','.csv or .xlsx')]:
            with self.subTest(name=name):
                self.assertIn(expected,self.worker_parse(data,name).get('error',''))
        data=bytearray(self.make_xlsx(self.planning_rows()))
        pos=data.find(b'PK\x01\x02');struct.pack_into('<I',data,pos+24,101*1024*1024)
        self.assertIn('100 MiB',self.worker_parse(data).get('error',''))
        # A dishonest declared expanded size must not evade the streamed check.
        data=bytearray(self.make_xlsx(self.planning_rows()));pos=data.find(b'PK\x01\x02');struct.pack_into('<I',data,pos+24,1)
        self.assertIn('expanded content',self.worker_parse(data).get('error',''))
        self.assertIn('50,000',self.worker_parse(('A\n'+'1\n'*50002).encode(),'tall.csv').get('error',''))

    def test_worker_preserves_percent_formula_and_hidden_sheet_metadata(self):
        for edit in ['percent','formula','missing_formula','hidden','date1904']:
            with self.subTest(edit=edit):
                result=self.worker_parse(self.make_xlsx(self.planning_rows(),edits=edit))
                self.assertNotIn('error',result)
                sheet=result['sheets'][0]
                if edit=='percent':self.assertTrue(sheet['rows'][1][6]['percent'])
                elif edit=='hidden':self.assertTrue(sheet['hidden'])
                elif edit=='date1904':self.assertEqual(sheet['rows'][1][2]['date'],'2026-08-01')
                else:self.assertTrue(sheet['rows'][1][3]['formula'])

    def test_session_store_requires_explicit_valid_replacement(self):
        result=self.page.evaluate('''async()=>{
          'use strict';
          const {createImportSession}=await import('/import-validation.js');
          const s=createImportSession(); const first={valid:true,datasets:{planning:[{provider_fte:'4'}]}};
          s.confirm(first,{reviewed:true});let rejected=0;
          for(const [r,options] of [[{valid:false,datasets:{}},{reviewed:true}], [{valid:true,datasets:{planning:[{provider_fte:'5'}]}},{reviewed:true}], [first,{reviewed:false,replace:true}]]){
            try{s.confirm(r,options)}catch{rejected++}
          }
          const retained=s.snapshot();let immutable=false;try{retained.datasets.planning[0].provider_fte='0'}catch{immutable=true}
          s.confirm({valid:true,datasets:{planning:[{provider_fte:'5'}]}},{reviewed:true,replace:true});
          return {rejected,retained,immutable,after:s.snapshot()};
        }''')
        self.assertEqual(result['rejected'],3)
        self.assertTrue(result['immutable'])
        self.assertEqual(result['retained']['datasets']['planning'][0]['provider_fte'],'4')
        self.assertEqual(result['after']['datasets']['planning'][0]['provider_fte'],'5')

    def test_dates_currency_signs_phi_and_explicit_constants(self):
        rows=self.planning_rows();rows[1][2]='08/01/2026'
        self.assertFalse(self.validate_contract(rows)['valid'])
        result=self.validate_contract(rows,settings={'dateFormat':'mdy','percent':'percent'})
        self.assertTrue(result['valid'],result['issues'])
        rows=self.planning_rows();rows[0].append('MRN');rows[1].append('not accepted')
        self.assertFalse(self.validate_contract(rows)['valid'])
        rows=self.planning_rows();rows[1][7]='$195.00'
        self.assertTrue(self.validate_contract(rows)['valid'])
        rows=self.planning_rows();rows[1][12]='EUR';other=rows[1].copy();other[2]='2026-09';other[12]='USD';rows.append(other)
        self.assertFalse(self.validate_contract(rows)['valid'])

    def test_changing_mapping_invalidates_previous_validation(self):
        self.upload()
        self.page.get_by_role('button',name='Validate data',exact=True).click()
        self.page.get_by_label('Map FTE Count').select_option('')
        expect(self.page.locator('#import-validation')).to_be_hidden()
        expect(self.page.get_by_role('button',name='Confirm import',exact=True)).to_be_hidden()
