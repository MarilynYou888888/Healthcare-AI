import Decimal from './vendor/decimal.mjs';
import {calculate} from './scenario.js';
import {FIELDS,ROLES,LIMITS,METRICS,normalizeName,ambiguousAlias,prohibitedHeader,toScenarioAssumptions} from './import-schema.js';
const D=Decimal.clone({precision:28,rounding:Decimal.ROUND_HALF_EVEN});
const currencies=new Set(Intl.supportedValuesOf('currency'));
const ISO_DATE=/^(\d{4})-(\d{2})-(\d{2})$/;
function validDate(value) {
  const m=ISO_DATE.exec(value);
  if(!m || +m[1]<1) return false;
  const date=new Date(value+'T00:00:00Z');
  return !Number.isNaN(+date) && date.toISOString().slice(0,10)===value;
}
function dateValue(raw,cell,format,month=false) {
  if(cell?.date) return month?cell.date.slice(0,7):cell.date;
  if(month && /^\d{4}-(0[1-9]|1[0-2])$/.test(raw) && +raw.slice(0,4)>0) return raw;
  let value=raw;
  if(format!=='iso') {
    const m=/^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$/.exec(raw);
    if(m) value=`${m[3]}-${(format==='mdy'?m[1]:m[2]).padStart(2,'0')}-${(format==='mdy'?m[2]:m[1]).padStart(2,'0')}`;
  }
  if(!validDate(value)) throw new Error('Use YYYY-MM / YYYY-MM-DD, or explicitly select the matching date format.');
  return month?value.slice(0,7):value;
}
function numeric(raw,cell,settings,ratio=false) {
  let text=raw.trim(), percent=text.endsWith('%');
  if(text.length>128) throw new Error('Use a number no longer than 128 characters.');
  if(percent) text=text.slice(0,-1).trim();
  if(text.startsWith('(')&&text.endsWith(')')) text='-'+text.slice(1,-1);
  const symbol=/^(?:([A-Z]{3})\s*|([$€£¥])\s*)/.exec(text);
  if(symbol) {
    const expected=symbol[1]??({'€':'EUR','£':'GBP'}[symbol[2]]);
    if(!settings.currency || (expected && expected!==settings.currency) || (symbol[2]==='$' && !['USD','CAD','AUD','NZD','SGD','HKD'].includes(settings.currency)) || (symbol[2]==='¥'&&!['JPY','CNY'].includes(settings.currency))) throw new Error('Confirm the matching currency before removing currency formatting.');
    text=text.slice(symbol[0].length);
  }
  if(cell?.t!=='n') {
    if(settings.numberFormat==='comma') {
      if(!/^[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?(?:e[+-]?\d+)?$/i.test(text)) throw new Error('Use comma decimals and dot groups, or change the numeric format.');
      text=text.replaceAll('.','').replace(',','.');
    } else {
      if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+|\d{1,3}(?:,\d{3})+(?:\.\d+)?)(?:e[+-]?\d+)?$/i.test(text)) throw new Error('Use dot decimals and comma groups, or change the numeric format.');
      text=text.replaceAll(',','');
    }
  }
  let value;
  try { value=new D(text); } catch { throw new Error('Enter a finite numeric value; blank is not zero.'); }
  if(!value.isFinite() || Math.abs(value.e)>1000) throw new Error('Use a finite number within the supported exponent range −1000 to 1000.');
  if(ratio) {
    if(cell?.percent) { /* XLSX stores a fraction already. */ }
    else if(percent || settings.percent==='percent') value=value.div(100);
    else if(settings.percent!=='fraction') throw new Error('Select fraction (0–1) or percentage points (0–100); an unmarked number is ambiguous.');
  } else if(percent || cell?.percent) throw new Error('A percentage is not valid for this field. Check the mapped field and unit.');
  return value;
}
function freeze(value) { if(value && typeof value==='object' && !Object.isFrozen(value)){Object.values(value).forEach(freeze);Object.freeze(value);} return value; }
export function headersFor(table) { return (table.sheet.rows[table.headerRow-1]??[]).map(c=>String(c.v??'')); }
export function validateImport(tables,confirmed={}) {
  const issues=[],transformations=[],datasets={}; let rowsCount=0,cellsCount=0;
  const add=(severity,table,row,column,problem,correction)=>issues.push({severity,sheet:table.sheet.name,file:table.fileName,row,column,problem,correction});
  for(const table of tables) {
    const role=ROLES[table.role]; if(!role) continue;
    const headers=headersFor(table), settings={dateFormat:'iso',numberFormat:'dot',percent:'',currency:'',...table.settings};
    const error=(row,column,problem,correction='Correct the source file or mapping, then validate again.')=>add('ERROR',table,row,column,problem,correction);
    if(!headers.length || headers.every(h=>!h.trim())) {error(table.headerRow,'Header','The selected header row is empty.','Choose the row containing column names.');continue;}
    if(table.sheet.merges.some(m=>m.e.r>=table.headerRow-1)) error(table.headerRow,'Table','Merged cells are not supported in the selected table.','Export one rectangular table without merged cells.');
    const names=headers.map(normalizeName);
    if(new Set(names).size!==names.length || names.some(n=>!n)) error(table.headerRow,'Header','Column names must be nonblank and unique.','Choose a valid header row or correct duplicate/blank headers.');
    for(let c=0;c<headers.length;c++) {
      if(prohibitedHeader(headers[c])) error(table.headerRow,headers[c],'Personal identifiers are outside the aggregated-data contract.','Remove patient/employee/claim identifiers from the file before retrying.');
      const id=table.mapping[c];
      if(id && !role.fields.includes(id)) error(table.headerRow,headers[c],'This field does not belong to the chosen dataset role.');
      if(id && table.mapping.filter(x=>x===id).length>1) error(table.headerRow,headers[c],'More than one column maps to the same field.','Choose one source column for each FP&A field.');
      if(id && ambiguousAlias(headers[c]) && !settings.confirmSemantics) error(table.headerRow,headers[c],'This suggested mapping has ambiguous business meaning.','Confirm that provider count means FTE and visits per day means visits per provider-day, or correct the mapping.');
      if(!id) add('INFO',table,table.headerRow,headers[c],'Unmapped column will be excluded.','Map it if needed, or review its exclusion.');
    }
    if(settings.currency && !currencies.has(settings.currency)) error(table.headerRow,'Currency','Choose a valid ISO currency.');
    // Mixed unmarked fractional and percentage-point values require source correction,
    // even when a column-level encoding was selected.
    for(let c=0;c<headers.length;c++) {
      const id=table.mapping[c];
      if(id!=='utilization_rate') continue;
      const values=table.sheet.rows.slice(table.headerRow).map(row=>row[c]).filter(cell=>cell && !cell.percent && !String(cell.v).includes('%')).map(cell=>Number(cell.v)).filter(Number.isFinite);
      if(values.some(v=>v>0&&v<1)&&values.some(v=>v>1)) error(table.headerRow,headers[c],'Mixed percentage scales are ambiguous.','Use one encoding consistently in this column; do not mix 0.90 and 90.');
    }
    let dataRows=0;
    for(let r=table.headerRow;r<table.sheet.rows.length;r++) {
      const cells=table.sheet.rows[r];
      if(cells.every(c=>c.v===''&&!c.formula)) continue;
      rowsCount++;dataRows++;cellsCount+=cells.filter(c=>c.v!==''||c.formula).length;
      if(cells.slice(headers.length).some(c=>c.v!=='')) error(r+1,'Row','This row contains values beyond the header columns.','Use one rectangular table.');
      const record={}, sourceCells={};
      for(const id of role.fields) {
        const index=table.mapping.indexOf(id), cell=index>=0?cells[index]:null;
        const constant=table.constants?.[id];
        const raw=String(cell?.v??constant??'');
        sourceCells[id]={cell,raw,column:index>=0?headers[index]:FIELDS[id].label,constant:index<0&&constant!==undefined&&constant!==''};
        record[id]=raw.trim();
      }
      for(const id of role.fields) {
        const field=FIELDS[id], info=sourceCells[id], cell=info.cell;
        let value=record[id], required=field.required;
        if(table.role==='events' && id==='unit') required=record.observed_value!=='';
        if(id==='metric_name' && !value && METRICS[record.metric_id]) value=METRICS[record.metric_id].label;
        if(id==='currency' && !value && settings.currency && (table.role==='planning' || METRICS[record.metric_id]?.units.some(u=>u.startsWith('currency')))) value=settings.currency;
        if(id==='source' && !value) value=`${table.fileName} / ${table.sheet.name} / row ${r+1}`;
        if(id==='scenario_name' && !value) value='Uploaded baseline';
        if(id==='entity_id' && !value && settings.generateIds && record.entity_name) value='session:'+record.entity_name;
        if(cell?.formula) {
          if(!value) error(r+1,info.column,'Formula has no cached value.','Recalculate in Excel and export values only.');
          else add('WARNING',table,r+1,info.column,'Cached formula value used; freshness is unverified.','Confirm freshness or export values only.');
        }
        if(cell?.t==='e') error(r+1,info.column,'The workbook contains a spreadsheet error.','Correct the cell and export values only.');
        if(!value) {
          if(required) error(r+1,info.column,`${field.label} is required.`,'Map a column or explicitly enter a constant; blank is not zero.');
          record[id]='';continue;
        }
        try {
          if(['number','nonnegative','positive','days','ratio'].includes(field.type)) {
            const ratio=field.type==='ratio' || (['actual_value','forecast_value','value','observed_value'].includes(id) && ['ratio','percent'].includes(record.unit));
            const number=numeric(value,cell,{...settings,currency:record.currency?.toUpperCase()||settings.currency},ratio);
            if(['nonnegative','days','ratio'].includes(field.type)&&number.lt(0)) throw new Error('Use a nonnegative value.');
            if(field.type==='positive'&&!number.gt(0)) throw new Error('Use a value greater than zero.');
            if(field.type==='days'&&(!number.isInteger()||!number.gt(0))) throw new Error('Use whole operating days greater than zero.');
            if(ratio&&(number.lt(0)||number.gt(1))) throw new Error('Normalized percentage must be between 0 and 1.');
            value=number.toString();
            if(ratio && !cell?.percent && !info.raw.includes('%') && settings.percent==='percent') add('WARNING',table,r+1,info.column,`${info.raw} normalized to ${value} using percentage-point encoding.`,'Review the conversion before confirming.');
          } else if(field.type==='month') {
            if(table.role==='benchmark' && /^FY\d{4}$/.test(value)) { /* Explicit annual context, no allocation. */ }
            else value=dateValue(value,cell,settings.dateFormat,true);
          } else if(field.type==='date') value=dateValue(value,cell,settings.dateFormat);
          else if(field.type==='timestamp') {
            if(cell?.date) value=cell.date+'T00:00:00Z';
            else if(!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$/.test(value) || !validDate(value.slice(0,10)) || !Number.isFinite(Date.parse(value))) throw new Error('Use an ISO timestamp including timezone, or leave unknown.');
          } else if(field.type==='currency') {value=value.toUpperCase(); if(!currencies.has(value)) throw new Error('Use a supported ISO currency code, such as USD.');}
          else if(field.type==='url'&&!/^https?:\/\//i.test(value)) throw new Error('Use an http(s) URL, or leave blank.');
        } catch(e) {error(r+1,info.column,`${field.label} could not be imported.`,e.message);}
        record[id]=value;
        if(value!==info.raw || info.constant || (cell?.w && cell.w!==value)) transformations.push({file:table.fileName,sheet:table.sheet.name,row:r+1,column:info.column,field:id,original:cell?.w||info.raw,normalized:value,reason:info.constant?'Analyst-entered constant':!info.raw?'Disclosed metadata/setup value':'Explicit format normalization'});
      }
      if(table.role==='planning') {
        if(!record.currency) error(r+1,'Currency','Currency must be explicitly supplied for monetary assumptions.','Map Currency or choose the currency setting.');
        try {
          const mapped=toScenarioAssumptions(record);
          calculate(mapped,record.period); // Reuse the authoritative V1 model only for range validation.
        } catch(e) {error(r+1,'Planning row','The planning row is outside the supported model inputs or derived range.','Correct field errors; operating days must fit the month and all model outputs must fit the supported numeric range.');}
      }
      if(table.role==='performance') {
        const metric=METRICS[record.metric_id];
        if(!metric) error(r+1,'Metric ID','Metric ID is not in the supported finance/operating registry.','Choose a supported metric ID using an explicit mapping or constant.');
        else {
          const monetary=metric.units.some(u=>u.startsWith('currency'));
          const units=metric.units.map(u=>u.replace('currency',record.currency));
          if(record.unit==='currency'&&record.currency) {
            transformations.push({file:table.fileName,sheet:table.sheet.name,row:r+1,column:'Unit',field:'unit',original:record.unit,normalized:record.currency,reason:'Explicit currency unit'});record.unit=record.currency;
          }
          if(record.unit==='percent'&&metric.units.includes('ratio')) {record.unit='ratio';transformations.push({file:table.fileName,sheet:table.sheet.name,row:r+1,column:'Unit',field:'unit',original:'percent',normalized:'ratio',reason:'Explicit percentage normalization'});}
          if(!units.includes(record.unit)) error(r+1,'Unit',`Unsupported unit for ${metric.label}.`,`Use ${units.join(' or ')} with an explicit currency for money.`);
          if(monetary&&!record.currency) error(r+1,'Currency','Monetary metrics require an explicit currency.');
          if(!monetary&&record.currency) error(r+1,'Currency','Nonmonetary metrics must not carry currency.','Leave currency blank for counts, FTE, days, hours, and ratios.');
          for(const id of ['actual_value','forecast_value']) {
            try {if(new D(record[id]).lt(0)) {
              if(!metric.signed) error(r+1,FIELDS[id].label,'Negative values are not meaningful for this operating metric.');
              else if(record.metric_id!=='OPERATING_INCOME') add('WARNING',table,r+1,FIELDS[id].label,'Signed revenue/expense adjustment.','Confirm the positive revenue / positive expense sign convention.');
            }} catch { /* Numeric issue already reported. */ }
          }
        }
      }
      if(['events','benchmark'].includes(table.role)) {
        const units=['visits','FTE','days','hours','count','ratio','percent','multiplier',...currencies];
        if(record.unit&&!units.includes(record.unit)&&!(/^[A-Z]{3}_per_visit$/.test(record.unit)&&currencies.has(record.unit.slice(0,3)))) error(r+1,'Unit','Unsupported unit.','Use visits, FTE, days, hours, count, ratio/percent, multiplier, ISO currency, or ISO currency_per_visit.');
        if(record.unit==='percent') {record.unit='ratio';transformations.push({file:table.fileName,sheet:table.sheet.name,row:r+1,column:'Unit',field:'unit',original:'percent',normalized:'ratio',reason:'Explicit percentage normalization'});}
      }
      if(table.role==='events') {
        if(record.end_date && record.start_date>record.end_date) error(r+1,'End date','Event end date precedes its start.');
        if(record.start_date.slice(0,7)>record.period || (record.end_date&&record.end_date.slice(0,7)<record.period)) error(r+1,'Period','Event interval does not overlap the selected month.');
      }
      record._lineage={file:table.fileName,sheet:table.sheet.name,row:r+1,kind:table.synthetic?'synthetic':'user_uploaded'};
      (datasets[table.role]??=[]).push(record);
    }
    if(!dataRows) error(table.headerRow,'Table','No data rows follow the selected header.');
  }
  if(rowsCount>LIMITS.rows||cellsCount>LIMITS.cells) issues.push({severity:'ERROR',row:'—',column:'Import',problem:'Selected tables exceed 50,000 rows or 500,000 cells.',correction:'Select fewer tables.'});
  const combined={...confirmed,...datasets}, identities=new Map(), nameIds=new Map(), monetary=new Set();
  for(const [role,rows] of Object.entries(combined)) {
    const keys=new Set();
    for(const row of rows) {
      const loc=row._lineage??{};
      const report=(severity,column,problem,correction)=>issues.push({severity,...loc,column,problem,correction});
      if(row.entity_id&&row.entity_name) {
        if(identities.has(row.entity_id)&&identities.get(row.entity_id)!==row.entity_name) report('ERROR','Entity','One entity ID has conflicting names.','Correct the entity identity across datasets.');
        identities.set(row.entity_id,row.entity_name);
        const ids=nameIds.get(row.entity_name)??new Set();ids.add(row.entity_id);nameIds.set(row.entity_name,ids);
      }
      const key=JSON.stringify(ROLES[role].key.map(k=>row[k]));
      if(keys.has(key)) report('ERROR','Row identity','Duplicate or conflicting row identity.','Remove or distinguish the duplicate in the source; rows are never silently combined.');keys.add(key);
      const money=row.currency || (currencies.has(row.unit)?row.unit:/^[A-Z]{3}_per_visit$/.test(row.unit??'')?row.unit.slice(0,3):'');
      if(money) monetary.add(money);
    }
  }
  if(monetary.size>1) issues.push({severity:'ERROR',row:'—',column:'Currency',problem:'User datasets contain more than one currency.',correction:'Use one currency per confirmed session. No FX conversion is available.'});
  for(const [name,ids] of nameIds) if(ids.size>1) issues.push({severity:'WARNING',row:'—',column:'Entity',problem:`“${name}” belongs to several IDs. They remain separate entities.`,correction:'Review the identity mapping; names are never silently merged.'});
  for(const row of combined.events??[]) if(!identities.has(row.entity_id)) issues.push({severity:'WARNING',...row._lineage,column:'Entity ID',problem:'No analytical entity matches this operating event yet.',correction:'Import matching Planning or Actual vs Forecast data before investigation.'});
  for(const t of transformations) issues.push({severity:'INFO',file:t.file,sheet:t.sheet,row:t.row,column:t.column,problem:`${t.reason}: ${t.original || '(empty)'} → ${t.normalized}`,correction:'Review this change in the normalization preview.'});
  return freeze({datasets,issues,transformations,valid:!issues.some(i=>i.severity==='ERROR'),rowsCount});
}
export function createImportSession() {
  let datasets=freeze({}),revision=0;
  return Object.freeze({
    snapshot:()=>({datasets,revision}),
    confirm(result,{reviewed=false,replace=false}={}) {
      if(!result.valid || !reviewed) throw new Error('Review valid normalized data before confirming.');
      if(Object.keys(result.datasets).some(role=>datasets[role])&&!replace) throw new Error('Explicit replacement confirmation is required.');
      datasets=freeze(structuredClone({...datasets,...result.datasets})); revision++;
      return {datasets,revision};
    },
  });
}
