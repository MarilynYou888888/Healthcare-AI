"""Reproduce curated public extracts from supplied filings; not used at app runtime.

Requires openpyxl and pypdf. Usage: python3 scripts/prepare_public_benchmarks.py
Sources remain unchanged. Each record is checked against the identified PDF page.
"""
import csv
import hashlib
import json
from pathlib import Path
from decimal import Decimal
from openpyxl import load_workbook
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
HCA_PDF = Path.home() / 'Desktop/HCA 10-K.pdf'
TENET_PDF = Path.home() / 'Desktop/tenet K-10.pdf'
WORKBOOK = Path.home() / 'Desktop/HCA_2025_Public_Dataset.xlsx'
SOURCES = {
    'HCA': ('HCA Healthcare', HCA_PDF, 'https://www.sec.gov/Archives/edgar/data/860730/000119312526044769/hca-20251231.htm'),
    'THC': ('Tenet Healthcare', TENET_PDF, 'https://www.sec.gov/Archives/edgar/data/70318/000007031826000012/thc-20251231.htm'),
}


def mapped_rows(worksheet, mapping):
    rows = list(worksheet.values)[1:]
    labels = [row[0] for row in rows]
    if len(labels) != len(set(labels)) or set(labels) != set(mapping):
        raise ValueError(f'{worksheet.title}: unexpected, duplicate or missing source labels')
    return [(index, row, mapping[row[0]]) for index, row in enumerate(rows, 2)]


def prepare():
    for ticker, (company, pdf, url) in SOURCES.items():
        reader = PdfReader(pdf)
        rows = []
        def add(group, mid, name, raw, unit, page, definition, segment='Consolidated', basis='Consolidated annual', extraction='', period='FY2025', missing=''):
            token = format(Decimal(str(raw)), ',f').rstrip('0').rstrip('.') if raw is not None and '.' in str(raw) else (format(int(raw), ',') if raw is not None else '')
            # Numeric token occurrence plus curated table/column mapping; not an automated semantic validator.
            if raw is not None and token not in reader.pages[page-1].extract_text() and ('(' + token.lstrip('-') + ')') not in reader.pages[page-1].extract_text():
                raise ValueError(f'{ticker} {mid}: source value {token} absent from page {page}')
            instant = mid in {'HOSPITALS','SURGERY_CENTERS','LICENSED_BEDS','HOSPITALS_SAME'}
            year = period.removeprefix('FY')
            rows.append(dict(company=company,ticker=ticker,period=period,
                period_start=year+('-12-31' if instant else '-01-01'),period_end=year+'-12-31',
                period_type='instant' if instant else 'duration',business_segment=segment,reporting_basis=basis,
                metric_id=mid,metric_name=name,raw_value='' if raw is None else str(raw),raw_unit=unit,
                value='' if raw is None else str(Decimal(str(raw)) * (1000000 if unit=='USD millions' else Decimal('.01') if unit=='percent' else 1)),
                unit='USD' if unit=='USD millions' else 'ratio' if unit=='percent' else unit,
                metric_definition=definition,source_document=f'{company} FY2025 Form 10-K',source_url=url,source_type='SEC 10-K',
                source_locator=f'Supplied PDF page {page}',extraction_reference=extraction or f'Curated FY2025 column, PDF page {page}',
                source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),provenance_kind='reported',missing_reason=missing,notes='',group=group))
        if ticker=='HCA':
            wb=load_workbook(WORKBOOK,read_only=True,data_only=True)
            financial_mapping = {'Revenues': 'REVENUE', 'Salaries and benefits': 'LABOR', 'Supplies': 'SUPPLIES', 'Other operating expenses': 'OTHER_OPEX', 'Equity in earnings of affiliates': 'EQUITY_EARNINGS_EXPENSE_SIGN', 'Depreciation and amortization': 'DA', 'Interest expense': 'INTEREST', 'Losses (gains) on sales of facilities': 'FACILITY_SALE_LOSS_GAIN', 'Income before income taxes': 'PRETAX_INCOME', 'Provision for income taxes': 'TAX', 'Net income': 'NET_INCOME', 'Net income attributable to noncontrolling interests': 'NONCONTROLLING_INCOME', 'Net income attributable to HCA Healthcare, Inc.': 'ATTRIBUTABLE_NET_INCOME'}
            for i,row,mid in mapped_rows(wb['Income_Statement'], financial_mapping):
                add('financial',mid,row[0],row[1],'USD millions',136,f'{row[0]}; consolidated income statement, signed as presented.',extraction=f'Income_Statement!B{i}; printed F-5')
            operating_mapping = {'Number of hospitals at end of period': 'HOSPITALS', 'Freestanding outpatient surgery centers at end of period': 'SURGERY_CENTERS', 'Licensed beds at end of period': 'LICENSED_BEDS', 'Weighted average beds in service': 'BEDS_IN_SERVICE', 'Admissions': 'ADMISSIONS', 'Equivalent admissions': 'EQUIVALENT_ADMISSIONS', 'Average length of stay': 'LENGTH_OF_STAY', 'Average daily census': 'DAILY_CENSUS', 'Occupancy rate': 'OCCUPANCY', 'Emergency room visits': 'ED_VISITS', 'Outpatient surgeries': 'OUTPATIENT_SURGERIES', 'Inpatient surgeries': 'INPATIENT_SURGERIES', 'Days revenues in accounts receivable': 'AR_DAYS', 'Outpatient revenues as % of patient revenues': 'OUTPATIENT_REVENUE_SHARE'}
            for i,row,mid in mapped_rows(wb['Operating_Metrics'], operating_mapping):
                raw=Decimal(str(row[1]))*100 if row[4]=='%' else row[1]
                definition=row[0]+'. See operating statistics footnotes, printed p.67.'
                if mid=='OCCUPANCY': definition='Occupied beds in service, including admitted and observation patients; not clinic utilization.'
                if mid=='EQUIVALENT_ADMISSIONS': definition='Admissions multiplied by total gross inpatient/outpatient revenue divided by gross inpatient revenue; not visits.'
                add('operating',mid,row[0],raw,'percent' if row[4]=='%' else row[4],103,definition,extraction=f'Operating_Metrics!B{i}; printed p.67')
            # Payer mix admission table is located by its identifying heading and values.
            payer_page=next(i+1 for i,p in enumerate(reader.pages) if 'Managed Medicare' in (t:=p.extract_text()) and '19%' in t and '27' in t)
            for i,row,mid in mapped_rows(wb['Payer_Mix'], {'Medicare':'MEDICARE','Managed Medicare':'MANAGED_MEDICARE','Medicaid':'MEDICAID','Managed Medicaid':'MANAGED_MEDICAID','Managed care and insurers':'MANAGED_CARE','Uninsured':'UNINSURED'}):
                add('payer_mix','ADMISSION_SHARE_'+mid,row[0],Decimal(str(row[1]))*100,'percent',payer_page,'Share of admissions, not revenue or reimbursement rate.',basis='Consolidated admission payer mix',extraction=f'Payer_Mix!B{i}')
            segpage=next(i+1 for i,p in enumerate(reader.pages) if '21,278' in (t:=p.extract_text()) and '7,812' in t and '5,103' in t)
            for row in list(wb['Segments'].values)[1:]:
                if row[0]!=2025:continue
                for j,(mid,name) in enumerate([('SEGMENT_REVENUE','Revenue'),('SEGMENT_LABOR','Salaries and benefits'),('SEGMENT_SUPPLIES','Supplies'),('SEGMENT_OTHER_OPEX','Other operating expenses'),('SEGMENT_ADJUSTED_EBITDA','Adjusted Segment EBITDA')],2):
                    add('segment',mid,name,row[j],'USD millions',segpage,name+' as defined in HCA segment disclosure; not clinic income.',segment=row[1],basis='Full segment annual',extraction=f'Segments; {row[1]}; FY2025')
        else:
            for mid,name,value in [('REVENUE','Net operating revenues',21310),('LABOR','Salaries, wages and benefits',8705),('SUPPLIES','Supplies',3780),('OTHER_OPEX','Other operating expenses, net',4523),('DA','Depreciation and amortization',863),('OPERATING_INCOME','Operating income',3508)]:
                add('financial',mid,name,value,'USD millions',53,name+'; continuing operations.',basis='Consolidated continuing operations annual')
            for mid,name,value,unit in [('HOSPITALS_SAME','Same-hospital count',47,'count'),('ADMISSIONS','Admissions',468250,'admissions'),('ADJUSTED_ADMISSIONS','Adjusted admissions',842992,'adjusted admissions'),('OUTPATIENT_VISITS','Outpatient visits',5356692,'visits'),('ED_VISITS','Outpatient emergency department visits',1793143,'visits'),('LICENSED_BEDS','Licensed beds at year end',12312,'beds'),('LENGTH_OF_STAY','Average length of stay',4.88,'days'),('LICENSED_BED_UTILIZATION','Utilization of licensed beds',50.8,'percent'),('INPATIENT_SURGERIES','Inpatient surgeries',118600,'surgeries'),('OUTPATIENT_SURGERIES','Outpatient surgeries',152375,'surgeries')]:
                add('operating',mid,name,value,unit,55,name+'; same-hospital cohort. Not a consolidated volume denominator.',segment='Hospital Operations',basis='Same-hospital annual')
            add('operating','ADJUSTED_ADMISSIONS','Adjusted admissions',None,'adjusted admissions',55,'No comparable FY2023 value in this supplied FY2025/2024 cohort table.',segment='Hospital Operations',basis='Same-hospital annual',period='FY2023',missing='Not disclosed for this comparison cohort in the selected table; not inferred.')
            for seg,values in [('Hospital Operations',[16138,7440,2405,3759,2540]),('Ambulatory Care',[5172,1265,1375,764,2026])]:
                for (mid,name),value in zip([('SEGMENT_REVENUE','Net operating revenues'),('SEGMENT_LABOR','Salaries, wages and benefits'),('SEGMENT_SUPPLIES','Supplies'),('SEGMENT_OTHER_OPEX','Other operating expenses, net'),('SEGMENT_ADJUSTED_EBITDA','Adjusted EBITDA')],values):
                    add('segment',mid,name,value,'USD millions',118,name+'; per segment disclosure and reconciliation, not clinic operating income.',segment=seg,basis='Full segment continuing operations annual')
            for i,(name,value) in enumerate([('Medicare',2119),('Medicaid',1524),('Managed care',9696),('Uninsured',52),('Indemnity and other',551)]):
                add('payer_mix','PATIENT_REVENUE_'+name.upper().replace(' ','_'),name,value,'USD millions',109,'Hospital net patient-service revenue by payer, not admission share; excludes other revenue.',segment='Hospital Operations',basis='Hospital patient-service revenue annual')
        folder=ROOT/'data/public_benchmarks'/('hca' if ticker=='HCA' else 'tenet')
        folder.mkdir(parents=True,exist_ok=True)
        for group in ['financial','operating','payer_mix','segment']:
            with (folder/f'{group}_metrics.csv').open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(r for r in rows if r['group']==group)
        metadata=dict(company=company,ticker=ticker,period='FY2025',data_kind='public_benchmark',source_url=url,source_document=f'{company} FY2025 Form 10-K',source_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest(),verified_on='2026-09-15',verification='Curated table/column mapping and numeric-token checks against supplied filing pages; selected FY2025 coverage.',notes=('HCA admission mix is not revenue mix. Segment extract excludes Corporate and other.' if ticker=='HCA' else 'Same-hospital volumes differ from full-segment financials. No inferred historical values.'))
        (folder/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
        print(ticker,len(rows),'source-checked metrics')

if __name__=='__main__':prepare()
