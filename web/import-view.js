import {createUserWorkspace} from './user-workflows.js';
import {ROLES,FIELDS,METRICS,LIMITS,suggestMappings,suggestSheetRole,suggestPayerMappings,PAYER_CATEGORIES,ambiguousAlias,normalizeName} from './import-schema.js';
import {headersFor,validateImport,createImportSession} from './import-validation.js';
const $=id=>document.getElementById(id);
function el(tag,text,cls) {const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;}
function option(value,text){const n=el('option',text);n.value=value;return n;}
function select(label,choices,value,onchange) {const box=el('label',label),input=el('select');input.setAttribute('aria-label',label);for(const [v,t]of choices)input.append(option(v,t));input.value=value;input.addEventListener('change',()=>onchange(input.value));box.append(input);return box;}
function check(label,value,onchange) {const box=el('label',undefined,'import-check'),input=el('input');input.type='checkbox';input.checked=value;input.addEventListener('change',()=>onchange(input.checked));box.append(input,document.createTextNode(label));return box;}
const session=createImportSession();
const workspace=createUserWorkspace(session);
$('import-open-workflows').onclick=()=>workspace.open().catch(()=>status('Unable to open analytical panels. Your confirmed data remains in this session.'));
const entryChoice=document.createElement('nav');entryChoice.className='entry-choice';entryChoice.setAttribute('aria-label','Choose workspace');entryChoice.append(Object.assign(document.createElement('a'),{href:'/',textContent:'Explore Demo ↗'}),Object.assign(document.createElement('a'),{href:'/import',textContent:'Use My Data',className:'entry-choice-current'}));document.querySelector('#import-workspace .page-heading > div').append(entryChoice);
const clearButton=document.createElement('button');clearButton.type='button';clearButton.id='import-clear-data';clearButton.textContent='Clear Uploaded Data';$('import-open-workflows').after(clearButton);clearButton.onclick=()=>workspace.clear();
let tables=[],result=null,worker=null,timer=null,generation=0,hasDraft=false;
const STEPS=['Upload','Role & sheets','Map columns','Validate','Preview','Confirm'];
function step(index) {$('import-steps').replaceChildren(...STEPS.map((name,i)=>{const li=el('li');li.append(el('b',String(i+1)),document.createTextNode(name));if(i===index)li.setAttribute('aria-current','step');return li;}));}
function status(text){$('import-status').textContent=text;}
function invalidate(){result=null;$('import-validation').hidden=true;$('import-preview').hidden=true;$('import-warnings').checked=false;$('import-confirm-check').checked=false;$('import-replace-check').checked=false;$('import-confirm').disabled=true;}
function stopWorker(){generation++;if(worker)worker.terminate();worker=null;clearTimeout(timer);$('import-cancel').hidden=true;}
function grid(headers,rows,target,pageSize=20) {
  const wrap=el('div'),scroll=el('div',undefined,'import-scroll'),table=el('table'),head=el('thead'),body=el('tbody'),hr=el('tr');
  headers.forEach(h=>hr.append(el('th',h)));head.append(hr);table.append(head,body);scroll.append(table);wrap.append(scroll);
  let page=0;const controls=el('div',undefined,'import-page-buttons'),prev=el('button','Previous rows'),next=el('button','Next rows'),label=el('span');prev.type=next.type='button';
  function render(){body.replaceChildren(...rows.slice(page*pageSize,(page+1)*pageSize).map(row=>{const tr=el('tr');row.forEach(v=>tr.append(el('td',String(v??''))));return tr;}));label.textContent=rows.length?`Rows ${page*pageSize+1}–${Math.min((page+1)*pageSize,rows.length)} of ${rows.length}`:'No rows';prev.disabled=page===0;next.disabled=(page+1)*pageSize>=rows.length;}
  prev.onclick=()=>{page--;render();};next.onclick=()=>{page++;render();};controls.append(prev,label,next);wrap.append(controls);render();target.append(wrap);
}
function renderSheets(){
  $('import-sheet-list').replaceChildren();
  for(const table of tables){
    const card=el('div',undefined,'import-sheet');card.append(el('h3',`Sheet: ${table.sheet.name}${table.sheet.hidden?' · Hidden sheet':''}`));
    const suggestion=table.suggestion??suggestSheetRole(table.sheet,table.headerRow);card.append(el('p',`Suggested role: ${suggestion.label}`,'import-role-suggestion'));card.append(el('p',suggestion.reason,'import-role-reason'));
    const controls=el('div',undefined,'import-controls');
    controls.append(select(`Dataset role — ${table.sheet.name}`,[['','Do not import'],...Object.entries(ROLES).map(([id,r])=>[id,r.label])],table.role,v=>{table.role=v;invalidate();}));
    const label=el('label','Header row'),input=el('input');input.type='number';input.min='1';input.max=String(table.sheet.rows.length||1);input.value=table.headerRow;input.setAttribute('aria-label',`Header row — ${table.sheet.name}`);
    input.onchange=()=>{table.headerRow=Math.max(1,Math.min(table.sheet.rows.length,Number(input.value)||1));table.suggestion=suggestSheetRole(table.sheet,table.headerRow);invalidate();renderSheets();};label.append(input);controls.append(label);card.append(controls);
    const rows=table.sheet.rows.slice(0,Math.max(6,Math.min(table.headerRow+3,20)));grid(['Row',...Array.from({length:Math.max(0,...rows.map(r=>r.length))},(_,i)=>String(i+1))],rows.map((r,i)=>[i+1,...r.map(c=>c.w||c.v)]),card,6);
    $('import-sheet-list').append(card);
  }
  $('import-sheets').hidden=false;
}
function autoSelectSafePercentageEncoding(table){
  if(table.settings.percent||table.settings.percentTouched||!['planning','payer_mix'].includes(table.role)) return;
  const ratioIndexes=table.mapping.map((id,index)=>({id,index})).filter(item=>item.id==='utilization_rate'||item.id==='payer_mix_share'||String(item.id).startsWith('payer_share:'));
  if(!ratioIndexes.length) return;
  let sawPercent=false,sawPointValue=false,sawFraction=false;
  for(const {index} of ratioIndexes){
    for(const row of table.sheet.rows.slice(table.headerRow)){
      const cell=row[index]; if(!cell||String(cell.v??'').trim()==='') continue;
      const raw=String(cell.v??'').trim(); if(cell.percent||raw.endsWith('%')) sawPercent=true;
      const numericValue=Number(raw.replace(/,/g,'')); if(Number.isFinite(numericValue)){if(numericValue>1)sawPointValue=true;if(numericValue>0&&numericValue<1)sawFraction=true;}
    }
  }
  const headers=headersFor(table).map(normalizeName);
  const explicitHeader=ratioIndexes.some(({index})=>/(%|percent|share|mix)/.test(headers[index]||''));
  if(!sawFraction && (sawPercent||(sawPointValue&&explicitHeader)||(sawPointValue&&table.mapping.some(id=>id==='utilization_rate')))){
    table.settings.percent='percent';
    table.safeFixes.push({type:'percentage-encoding',sheet:table.sheet.name,detail:'Unmarked ratio values were treated as percentage points (for example, 90 → 0.90) because the mapped field and values were unambiguous.'});
  }
}
$('import-file').addEventListener('change',()=>{
  stopWorker();const file=$('import-file').files[0];if(!file)return;
  invalidate();tables=[];$('import-sheets').hidden=true;$('import-mapping').hidden=true;hasDraft=true;
  if(!['localhost','127.0.0.1','[::1]'].includes(location.hostname)){status('User-data import is available only on the local loopback app.');return;}
  if(file.size>LIMITS.fileBytes){status('ERROR · File exceeds 10 MiB. Export a smaller CSV or XLSX.');return;}
  if(!/\.(csv|xlsx)$/i.test(file.name)){status('ERROR · Choose CSV or XLSX; macro-enabled files are not supported.');return;}
  status('Reading locally… You can cancel without affecting confirmed data.');$('import-cancel').hidden=false;step(0);
  const token=generation;worker=new Worker('/import-worker.js');
  timer=setTimeout(()=>{if(token!==generation)return;stopWorker();status('ERROR · File reading exceeded 15 seconds. Export a smaller table and retry.');},LIMITS.parseMs);
  worker.onerror=()=>{if(token!==generation)return;stopWorker();status('ERROR · File reading failed. Try a smaller, unencrypted CSV or XLSX.');};
  worker.onmessage=({data})=>{
    if(token!==generation)return;stopWorker();
    if(data.error){status('ERROR · '+data.error);return;}
    // Safe percentage repair is selected only after the mapped role, field, and
    // source values make the representation unambiguous. Ambiguous values stay
    // blocked by the validator and still require an analyst choice.
    tables=data.sheets.map(sheet=>({sheet,fileName:data.name,synthetic:data.synthetic,role:'',headerRow:1,suggestion:suggestSheetRole(sheet,1),mapping:[],mappingDrafts:new Map(),safeFixes:[],constants:{},settings:{percent:data.synthetic?'percent':'',percentTouched:false,numberFormat:'dot',dateFormat:'iso',currency:'',confirmSemantics:false,generateIds:false}}));
    renderSheets();step(1);status(`${data.name} · ${tables.length} table(s) read locally. Select the roles to include.`);
  };
  worker.postMessage({file});
});
$('import-cancel').onclick=()=>{stopWorker();status('Reading cancelled. Previously confirmed data is unchanged.');};
function renderMapping(){
  $('import-mapping-list').replaceChildren();
  for(const table of tables.filter(t=>t.role)){
    const section=el('div',undefined,'import-sheet');section.append(el('h3',`${table.sheet.name} → ${ROLES[table.role].label}`));
    const headers=headersFor(table),list=el('table',undefined,'import-mapping-table'),body=el('tbody'),head=el('thead'),hr=el('tr');
    ['Uploaded column','Expected FP&A field','Example from your file'].forEach(x=>hr.append(el('th',x)));head.append(hr);list.append(head,body);
    const fieldStatus=el('div',undefined,'import-field-status');
    function refreshStatus(){fieldStatus.replaceChildren();for(const id of ROLES[table.role].fields){const mapped=id==='payer_mix_share'&&table.role==='payer_mix'?table.mapping.some(value=>value==='payer_mix_share'||String(value).startsWith('payer_share:')):table.mapping.includes(id)||!!table.constants[id];const required=table.role==='payer_mix'&&['payer_mix_share','period'].includes(id)?true:FIELDS[id].required;fieldStatus.append(el('span',`${required?'* ':''}${FIELDS[id].label}: ${mapped?'mapped / supplied':'unmapped'}`,!mapped&&required?'import-unmapped':''));}}
    headers.forEach((header,c)=>{const row=el('tr'),name=el('td',header),mapping=el('td'),sel=el('select');sel.setAttribute('aria-label',`Map ${header}`);sel.append(option('','Do not import this column'));
      ROLES[table.role].fields.forEach(id=>sel.append(option(id,`${FIELDS[id].label}${FIELDS[id].required?' *':''}`)));
      if(table.role==='payer_mix') PAYER_CATEGORIES.forEach(category=>{sel.append(option(`payer_share:${category}`,`Payer mix share · ${category}`));sel.append(option(`payer_rate:${category}`,`Reimbursement value · ${category}`));});
      sel.value=table.mapping[c]??'';
      sel.onchange=()=>{table.mapping[c]=sel.value;if(!table.settings.percentTouched){table.settings.percent='';table.safeFixes=[];}invalidate();refreshStatus();};mapping.append(sel);row.append(name,mapping,el('td',table.sheet.rows[table.headerRow]?.[c]?.w||table.sheet.rows[table.headerRow]?.[c]?.v||'—'));body.append(row);
    });
    const scroll=el('div',undefined,'import-scroll');scroll.append(list);section.append(scroll,fieldStatus);refreshStatus();
    const settings=el('div',undefined,'import-settings'),controls=el('div',undefined,'import-controls');
    controls.append(select('Numeric percentage encoding',[['','Choose for unmarked numbers'],['fraction','Fraction (0.90 = 90%)'],['percent','Percentage points (90 = 90%)']],table.settings.percent,v=>{table.settings.percentTouched=true;table.settings.percent=v;invalidate();}));
    controls.append(select('Numeric format',[['dot','1,234.56 — dot decimals'],['comma','1.234,56 — comma decimals']],table.settings.numberFormat,v=>{table.settings.numberFormat=v;invalidate();}));
    controls.append(select('Date format',[['iso','ISO: YYYY-MM or YYYY-MM-DD'],['mdy','MM/DD/YYYY'],['dmy','DD/MM/YYYY']],table.settings.dateFormat,v=>{table.settings.dateFormat=v;invalidate();}));
    controls.append(select('Currency for missing monetary currency',[['','Use mapped currency'],...Intl.supportedValuesOf('currency').map(c=>[c,c])],table.settings.currency,v=>{table.settings.currency=v;invalidate();}));settings.append(controls);
    settings.append(el('p','Excel percent cells retain their stored fraction. An unmarked 90 or 0.90 needs your explicit encoding choice. A currency symbol alone does not establish currency.','import-help'));
    if(headers.some(ambiguousAlias)) settings.append(check('I confirm Provider Count means FTE and Visits Per Day means visits per provider-day (if mapped)',table.settings.confirmSemantics,v=>{table.settings.confirmSemantics=v;invalidate();}));
    if(['planning','performance'].includes(table.role)) settings.append(check('Create session entity IDs from mapped names; I have checked that names uniquely identify my entities',table.settings.generateIds,v=>{table.settings.generateIds=v;invalidate();}));
    section.append(settings);
    const details=el('details'),summary=el('summary','Supply an explicit constant instead of a missing column');details.append(summary,el('p','Optional: enter a value only when it applies to every row of this table. Mapped columns take precedence. Every supplied value is shown in the normalization register.','import-help'));
    const constants=el('div',undefined,'import-constants');
    for(const id of ROLES[table.role].fields){const label=el('label',FIELDS[id].label),input=el('input');input.type='text';input.value=table.constants[id]??'';input.setAttribute('aria-label',`Constant ${FIELDS[id].label} — ${table.sheet.name}`);input.oninput=()=>{table.constants[id]=input.value;invalidate();refreshStatus();};label.append(input);constants.append(label);}details.append(constants);section.append(details);
    if(table.role==='performance'){const help=el('details');help.append(el('summary','Supported performance metrics & expected units'));help.append(el('p',Object.entries(METRICS).map(([id,m])=>`${id}: ${m.label} (${m.units.join(', ')})`).join(' · '),'import-help'));section.append(help);}
    $('import-mapping-list').append(section);
  }
  $('import-mapping').hidden=false;$('import-sheets').hidden=true;step(2);$('import-mapping').scrollIntoView({block:'start'});
}
$('import-map').onclick=()=>{if(!tables.some(t=>t.role)){status('Choose at least one dataset role before mapping.');return;}invalidate();for(const t of tables.filter(t=>t.role)){
  // Keep separate drafts when the user changes a sheet's role or header row.
  const key=JSON.stringify([t.role,t.headerRow]);
  if(!t.mappingDrafts.has(key))t.mappingDrafts.set(key,t.role==='payer_mix'?suggestPayerMappings(headersFor(t)):suggestMappings(headersFor(t),t.role));
  t.mapping=t.mappingDrafts.get(key); t.safeFixes=[]; autoSelectSafePercentageEncoding(t);
}renderMapping();status('Review your column mappings and explicit format choices. Previous choices are preserved; new mappings use suggestions.');};
$('import-back-sheets').onclick=()=>{invalidate();$('import-sheets').hidden=false;$('import-mapping').hidden=true;step(1);};
$('import-validate').onclick=()=>{
  invalidate();for(const table of tables.filter(t=>t.role)){if(!table.settings.percentTouched){table.settings.percent='';table.safeFixes=[];}autoSelectSafePercentageEncoding(table);}result=validateImport(tables.filter(t=>t.role),session.snapshot().datasets);
  const counts=el('div',undefined,'import-counts');for(const severity of ['ERROR','WARNING','INFO'])counts.append(el('span',`${result.issues.filter(i=>i.severity===severity).length} ${severity==='ERROR'?'errors':severity==='WARNING'?'warnings':'info'}`,`severity-${severity.toLowerCase()}`));
  const safeFixes=tables.flatMap(table=>table.safeFixes||[]),summary=[counts,el('p',`${result.rowsCount} rows checked. Safe fixes are applied only when the field and source representation are unambiguous.`)];
  if(safeFixes.length){const fixes=el('div',undefined,'import-auto-fixes');fixes.append(el('strong',`System applied ${safeFixes.length} safe fix${safeFixes.length===1?'':'es'}.`));safeFixes.forEach(fix=>fixes.append(el('p',`${fix.sheet}: ${fix.detail}`)));summary.push(fixes);}
  summary.push(el('p','Remaining ERROR items require a source or mapping correction. WARNING items require review. INFO items describe normalization or exclusions.'));$('import-validation-summary').replaceChildren(...summary);
  $('import-issues').replaceChildren();grid(['Level','File / sheet','Row','Column','Problem','Suggested correction'],result.issues.map(i=>[i.severity,`${i.file??''} / ${i.sheet??''}`,i.row,i.column,i.problem,i.correction]),$('import-issues'));
  $('import-warnings').parentElement.hidden=!result.issues.some(i=>i.severity==='WARNING');$('import-validation').hidden=false;$('import-show-preview').disabled=!result.valid||result.issues.some(i=>i.severity==='WARNING');step(3);$('import-validation').scrollIntoView({block:'start'});status(result.valid?'Validation complete. Review warnings and proceed to preview.':'Some data needs correction. Confirmed session data has not changed.');
};
$('import-warnings').onchange=()=>{$('import-show-preview').disabled=!result?.valid||!$('import-warnings').checked;};
$('import-back-map').onclick=()=>{invalidate();step(2);$('import-mapping').scrollIntoView({block:'start'});};
$('import-show-preview').onclick=()=>{
  if(!result?.valid)return;
  $('import-preview-tables').replaceChildren();
  for(const table of tables.filter(t=>t.role)){const box=el('div');box.append(el('h3',`${table.sheet.name} · Original`));const headers=headersFor(table);grid(['Source row',...headers],table.sheet.rows.slice(table.headerRow).map((r,i)=>[table.headerRow+i+1,...r.map(c=>c.w||c.v)]),box);$('import-preview-tables').append(box);}
  for(const [role,rows]of Object.entries(result.datasets)){const box=el('div');box.append(el('h3',`${ROLES[role].label} · Normalized`));grid(['Source row',...ROLES[role].fields],rows.map(r=>[r._lineage.row,...ROLES[role].fields.map(f=>r[f])]),box);$('import-preview-tables').append(box);}
  $('import-transformations').replaceChildren();grid(['Sheet','Row','Column','Normalized field','Uploaded / original','Normalized','Reason'],result.transformations.map(t=>[t.sheet,t.row,t.column,t.field,t.original,t.normalized,t.reason]),$('import-transformations'));
  $('import-replace-label').hidden=!Object.keys(result.datasets).some(role=>session.snapshot().datasets[role]);$('import-preview').hidden=false;step(4);$('import-preview').scrollIntoView({block:'start'});status('Review all rows and conversions. Nothing changes until you confirm.');
};
function confirmationReady(){ $('import-confirm').disabled=!result?.valid||!$('import-confirm-check').checked||(!$('import-replace-label').hidden&&!$('import-replace-check').checked);if($('import-confirm-check').checked)step(5); }
$('import-confirm-check').onchange=confirmationReady;$('import-replace-check').onchange=confirmationReady;
$('import-back-validation').onclick=()=>{$('import-preview').hidden=true;$('import-confirm-check').checked=false;confirmationReady();step(3);$('import-validation').scrollIntoView({block:'start'});};
$('import-confirm').onclick=()=>{
  try {
    if(!workspace.canReplace())return;
    const snapshot=session.confirm(result,{reviewed:$('import-confirm-check').checked,replace:$('import-replace-check').checked});
    $('import-confirmed-list').replaceChildren();
    for(const [role,rows]of Object.entries(snapshot.datasets)){const details=el('details');details.append(el('summary',`${ROLES[role].label}: ${rows.length} row${rows.length===1?'':'s'} · confirmed`));const kinds=[...new Set(rows.map(r=>r._lineage.kind))];details.append(el('p',`${kinds.includes('synthetic')?'SYNTHETIC SAMPLE':'USER UPLOADED'} · Session revision ${snapshot.revision}`));grid(ROLES[role].fields,rows.map(r=>ROLES[role].fields.map(f=>r[f])),details);$('import-confirmed-list').append(details);}
    $('import-open-workflows').disabled=false;
    status('Import confirmed. Data is held in this page session only; V1 demo data is unchanged.');$('import-confirmed').scrollIntoView({block:'start'});invalidate();hasDraft=false;$('import-file').value='';
  }catch(e){status(e.message);}
};
window.addEventListener('beforeunload',event=>{if(session.snapshot().revision||hasDraft){event.preventDefault();event.returnValue='';}});
window.addEventListener('pagehide',()=>{
  stopWorker();workspace.dispose();session.dispose();tables=[];result=null;hasDraft=false;$('import-file').value='';
  for(const id of ['import-sheet-list','import-mapping-list','import-issues','import-preview-tables','import-transformations','import-confirmed-list']) $(id).replaceChildren();
});
window.addEventListener('pageshow',event=>{if(event.persisted)location.reload();});
step(0);

$('import-limits').textContent = `Up to ${LIMITS.fileBytes/1024/1024} MiB per file · ${LIMITS.rows.toLocaleString('en-US')} selected rows · ${LIMITS.columns} columns per sheet · ${LIMITS.cells.toLocaleString('en-US')} populated cells · ${LIMITS.expandedBytes/1024/1024} MiB expanded workbook · ${LIMITS.parseMs/1000}-second read limit. One table per sheet. CSV uses UTF-8.`;
