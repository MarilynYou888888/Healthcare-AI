import {toScenarioAssumptions} from './import-schema.js';

// Identity/provenance adapter only. All financial arithmetic stays in scenario.js.
export function planningBaseline(row, uploadRevision) {
  if (!row?._lineage || !['synthetic','user_uploaded'].includes(row._lineage.kind)) throw new Error('A confirmed planning row with source lineage is required.');
  return {data_kind:'user_uploaded',baseline_id:`upload-${uploadRevision}-${crypto.randomUUID()}`,
    entity_id:row.entity_id,entity_name:row.entity_name,clinic:row.entity_name,month:row.period,
    scenario_name:row.scenario_name || 'Uploaded baseline',currency:row.currency,
    source:row.source,source_lineage:{...row._lineage},assumptions:toScenarioAssumptions(row)};
}

import {createScenarioStore} from './scenario.js';
import {mountScenarioModel} from './scenario-view.js';
import {mountExecutiveSummary} from './executive.js';
import {mountUploadedInvestigation} from './user-investigation.js';
import {COMMENTARY_DISCLOSURE,composeScenarioCommentary} from './commentary.js';
const $=id=>document.getElementById(id);
let ready;
async function templates() {
  if (!ready) ready=Promise.all([fetch('/user-analysis.html').then(r=>r.text()),fetch('/').then(r=>r.text())]).then(([html,demo])=>{
    const fragment=new DOMParser().parseFromString(html,'text/html');
    const host=document.createElement('div');host.id='user-analysis-host';
    host.append(...fragment.body.childNodes);document.querySelector('main').append(host);
    const original=new DOMParser().parseFromString(demo,'text/html');
    for(const id of ['model-view','executive-view','investigation-view']) {
      const section=original.getElementById(id);section.hidden=true;section.removeAttribute('aria-labelledby');
      $('user-panels').append(section);
    }
    // Reuse V1 panels and renderers; replace demo-only context, not model logic.
    document.querySelector('#executive-view .context-strip').replaceChildren();
    $('commentary-disclosure').textContent=COMMENTARY_DISCLOSURE;
    document.querySelector('#summary-commentary .summary-eyebrow').textContent='02 · AUTOMATED FP&A COMMENTARY';
    document.querySelector('#summary-commentary h3').textContent='Automated FP&A Commentary';
    document.querySelector('#investigation-view .investigation-controls').remove();
    document.querySelector('#investigation-view .investigation-intro').textContent='Uploaded Actual vs Latest Approved Forecast. Confirm the comparator before investigation.';
    document.querySelector('#investigation-view .model-heading .badge').textContent='UPLOADED · EVIDENCE REVIEW';
    $('investigation-target').hidden=true;
    document.querySelector('label[for="investigation-target"]').hidden=true;
    $('investigation-override').hidden=true;
    $('investigation-handoffs').closest('section').hidden=true;
    document.querySelector('#investigation-narrative').replaceChildren();
    $('investigation-view').insertBefore($('user-investigation-controls-template').content.cloneNode(true),$('investigation-status'));
  }).catch(error=>{ready=null;throw error;});
  return ready;
}

export function createUserWorkspace(session) {
  let snapshot=null, selected=null, baseline=null, store=null, disposeModel=()=>{},disposeSummary=()=>{},investigation=null;
  let view='model', notes=new Map(), previous=null,openVersion=0, benchmark='none',disposeExport=()=>{};
  const dirty=()=>store && (store.snapshot().status!=='valid' || store.snapshot().result.changed_drivers.length>0);
  function noteKey(){return JSON.stringify([snapshot?.revision,selected,view,view==='investigation'?$('user-metric')?.value:'']);}
  function saveNote(){if(previous)notes.set(previous,$('user-analyst-note').value);}
  function loadNote(){saveNote();previous=noteKey();$('user-analyst-note').value=notes.get(previous)??'';}
  function csvCell(value,numeric=false) { if(value===null || value===undefined)return ''; if(numeric || typeof value==='number')return String(value); let text=String(value);if(/^[=+\-@]/.test(text))text="'"+text;return /[",\n\r]/.test(text)?'"'+text.replaceAll('"','""')+'"':text; }
  function exportSummary() { saveNote();const state=store?.snapshot();if(!state||state.status!=='valid'||!state.result){$('user-export-status').textContent='Export unavailable until the selected scenario inputs are valid.';return;}const result=state.result,commentary=composeScenarioCommentary(result),rows=[],add=(field,value,numeric=false)=>rows.push([field,value,numeric]);add('data_source',result.data_kind==='synthetic'?'SYNTHETIC SAMPLE':'USER UPLOADED');add('entity',result.entity_name);add('period',result.month);add('scenario',result.scenario_name);add('currency',result.currency);add('revision',result.revision,true);add('source',result.source);add('source_file',result.source_lineage?.file);add('source_sheet',result.source_lineage?.sheet);add('source_row',result.source_lineage?.row,true);for(const [id,value] of Object.entries(result.baseline_assumptions)){add(`baseline_assumption.${id}`,value,true);add(`scenario_assumption.${id}`,result.assumptions[id],true);}for(const [id,value] of Object.entries(result.baseline)){add(`baseline_output.${id}`,value,true);add(`scenario_output.${id}`,result.scenario[id],true);add(`change.${id}`,result.changes[id]?.amount,true);add(`change_percent.${id}`,result.changes[id]?.percent??`N/A: ${result.changes[id]?.percent_reason??'Unavailable'}`,!result.changes[id]?.percent_reason);}add('automated_commentary',commentary?.summary);add('analyst_note',notes.get(noteKey())||'');add('disclosure','Deterministic calculation outputs and recorded source lineage; no forecast approval or external transmission.');const csv=['field,value',...rows.map(([field,value,numeric])=>`${csvCell(field)},${csvCell(value,numeric)}`)].join('\r\n')+'\r\n';const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));const link=document.createElement('a');link.href=url;link.download=`${result.entity_name||'scenario'}-${result.month||'summary'}-scenario-summary.csv`;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),0);$('user-export-status').textContent=`Exported current valid ScenarioResult revision ${result.revision}.`; }
  function clearUploadedData(){openVersion++;disposeExport();disposeModel();disposeSummary();investigation?.dispose();session.dispose();snapshot=selected=baseline=store=null;notes.clear();previous=null;location.href='/';}
  function options(id,values,current) {
    $(id).replaceChildren(...values.map(([value,label])=>{const o=document.createElement('option');o.value=value;o.textContent=label;return o;}));
    if(values.some(([value])=>value===current))$(id).value=current;
  }
  function rows(role){return snapshot?.datasets[role]??[];}
  function periodRows(role){return rows(role).filter(r=>r.entity_id===$('user-entity').value && r.period===$('user-period').value);}
  function renderCustomBenchmark(){
    const records=rows('benchmark');
    $('user-benchmark-context').replaceChildren(...records.map(row=>{
      const article=document.createElement('article'); article.className='benchmark-context-row';
      const title=document.createElement('strong');title.textContent=`${row.company} · ${row.period} · ${row.business_segment}`;
      const value=document.createElement('p');value.textContent=`${row.metric_name}: ${row.value} ${row.unit} · Source: ${row.source}`;
      article.append(title,value);
      if(row.notes){const note=document.createElement('small');note.textContent=row.notes;article.append(note);}
      if(row.source_url){const link=document.createElement('a');link.href=row.source_url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Open submitted source URL ↗';article.append(link);}
      return article;
    }));
  }
  async function selectBenchmark(value){
    benchmark=value;$('user-benchmark-context').replaceChildren();
    if(value==='none'){$('user-benchmark-status').textContent='No Benchmark selected. Analysis remains available.';return;}
    if(value==='custom'){
      const records=rows('benchmark');
      $('user-benchmark-status').textContent=records.length?`USER UPLOADED · ${records.length} benchmark row${records.length===1?'':'s'} · Unverified external context`:'No Custom Benchmark has been confirmed in this session.';
      renderCustomBenchmark();return;
    }
    $('user-benchmark-status').textContent='Loading BUILT-IN PUBLIC benchmark context…';
    try {const response=await fetch(`/api/benchmarks/${value}`);if(!response.ok)throw new Error();const data=await response.json();
      if(benchmark!==value)return;
      $('user-benchmark-status').textContent=`BUILT-IN PUBLIC · ${data.company} · Context only · Read-only`;
      $('user-benchmark-context').replaceChildren(...data.metrics.slice(0,5).map(metric=>{const p=document.createElement('p');p.textContent=`${metric.metric_name}: ${metric.value ?? 'Not disclosed'} ${metric.unit} · ${metric.period} · ${metric.business_segment} · ${metric.reporting_basis} · Source: ${metric.source_document} · ${metric.source_locator}`;return p;}));
    } catch {$('user-benchmark-status').textContent='Public benchmark context unavailable. No Benchmark remains valid.';}
  }
  function selectors(level=0){
    if(level===0){const all=[...rows('planning'),...rows('performance')];options('user-entity',[...new Map(all.map(r=>[r.entity_id,r.entity_name+' · '+r.entity_id])).entries()],selected?.entity);}
    if(level<=1) options('user-period',[...new Set([...rows('planning'),...rows('performance')].filter(r=>r.entity_id===$('user-entity').value).map(r=>r.period))].sort().map(p=>[p,p]),selected?.period);
    options('user-scenario',periodRows('planning').map((r,i)=>[String(i),r.scenario_name||'Uploaded baseline']),level===2?$('user-scenario').value:undefined);
  }
  function choose(){
    if(dirty() && !window.confirm('Discard the edited scenario and its review decision before selecting another baseline?')) {
      options('user-entity',[...new Map([...rows('planning'),...rows('performance')].map(r=>[r.entity_id,r.entity_name+' · '+r.entity_id])).entries()],selected.entity);
      selectors(1);$('user-scenario').value=selected.scenario;return;
    }
    saveNote();disposeExport();disposeModel();disposeSummary();store=null;
    selected={entity:$('user-entity').value,period:$('user-period').value,scenario:$('user-scenario').value};
    const row=periodRows('planning')[Number(selected.scenario)];
    $('user-open-model').disabled=$('user-open-summary').disabled=!row;
    $('user-open-investigation').disabled=!periodRows('performance').length;
    if(row){
      baseline=planningBaseline(row,snapshot.revision);store=createScenarioStore(baseline);disposeExport=store.subscribe(state=>{$('user-export-summary').disabled=state.status!=='valid';});
      disposeModel=mountScenarioModel(baseline,store);disposeSummary=mountExecutiveSummary(store);
      $('edit-model').onclick=()=>activate('model');$('view-summary').onclick=()=>activate('summary');
      document.querySelector('#model-view .model-heading h2').textContent=row.entity_name;
      document.querySelector('#model-view .badge').textContent=(row._lineage.kind==='synthetic'?'SYNTHETIC SAMPLE':'USER UPLOADED')+' · SCENARIO MODEL';
      document.querySelector('#model-view .assumptions .scope-note').textContent='Uploaded baseline is immutable. Edits affect only this selected session draft.';
      document.querySelector('#model-view .outputs .scope-note').textContent=`${row.currency} displayed to cents. Fractional visits remain in calculations. No approved forecast is changed.`;
      document.querySelector('#summary-impact .impact-heading p').textContent=`Revenue movement, variable cost offsets, and fixed expense · ${row.currency}`;
      document.querySelector('#summary-comparison > p').textContent=`One entity · one month · common ${row.currency} scale`;
      document.querySelector('#summary-expenses > p').textContent=`Variable costs and fixed expense · ${row.currency}`;
    }
    investigation.select(snapshot,selected.entity,selected.period);
    const labelRow=row??periodRows('performance')[0];
    $('user-source').textContent=labelRow ? `${labelRow._lineage.kind==='synthetic'?'SYNTHETIC SAMPLE':'USER UPLOADED'} · ${labelRow.entity_name} · ${labelRow.period} · ${row?.scenario_name||'Uploaded baseline'} · ${row?.currency||'Metric-specific units'} · Source: ${labelRow.source} · ${labelRow._lineage.file} / ${labelRow._lineage.sheet} / row ${labelRow._lineage.row}. Public benchmarks are separate context and never initialize these inputs.` : rows('events').length ? 'Operating evidence is available, but Actual vs Forecast data is required to start a variance investigation.' : rows('benchmark').length ? 'Custom Benchmark context is available, but Planning Assumptions or Actual vs Forecast data is required to run an analytical workflow.' : 'Planning Assumptions or Actual vs Forecast data is required to run an analytical workflow.';
    if(!row && view!=='investigation')view='investigation';
    if(view==='investigation' && !periodRows('performance').length && row)view='model';
    activate(view);
  }
  function activate(next){saveNote();view=next;for(const [key,id] of [['model','model-view'],['summary','executive-view'],['investigation','investigation-view']]) $(id).hidden=key!==view || (key==='investigation'?!periodRows('performance').length:!store);
    $('user-analysis-status').textContent=!store&&!periodRows('performance').length?(rows('events').length?'Operating evidence is available, but Actual vs Forecast data is required to start a variance investigation.':rows('benchmark').length?'Custom Benchmark context is available, but Planning Assumptions or Actual vs Forecast data is required to run an analytical workflow.':'Planning Assumptions or Actual vs Forecast data is required to run an analytical workflow.'):!store?'Scenario Model requires Planning Assumptions. Variance Investigation is available.':!periodRows('performance').length?'Variance Investigation requires Actual vs Forecast data. Scenario Model and Executive Summary are available.':'';
    loadNote();
  }
  return {
    async open(){
      const token=++openVersion;await templates();if(token!==openVersion)return;
      if(!investigation){investigation=mountUploadedInvestigation(()=>loadNote());
        $('user-back-import').onclick=()=>{saveNote();$('user-analysis').hidden=true;for(const child of document.querySelector('main').children)if(child.id!=='user-analysis-host')child.hidden=false;};
        for(const name of ['model','summary','investigation'])$('user-open-'+name).onclick=()=>activate(name);
        $('user-entity').onchange=()=>{selectors(1);choose();};$('user-period').onchange=()=>{selectors(2);choose();};$('user-scenario').onchange=choose;
        $('user-benchmark').onchange=()=>selectBenchmark($('user-benchmark').value);
        const actions=document.createElement('div');actions.className='import-actions';actions.id='user-ticket4-actions';const exportButton=document.createElement('button');exportButton.type='button';exportButton.id='user-export-summary';exportButton.textContent='Export Scenario Summary CSV';exportButton.disabled=true;exportButton.onclick=exportSummary;const clearButton=document.createElement('button');clearButton.type='button';clearButton.id='user-clear-data';clearButton.textContent='Clear Uploaded Data';clearButton.onclick=clearUploadedData;actions.append(exportButton,clearButton);const exportStatus=document.createElement('p');exportStatus.id='user-export-status';exportStatus.className='session-note';exportStatus.setAttribute('role','status');$('user-analysis-status').after(actions,exportStatus);
      }
      const fresh=session.snapshot();
      if(snapshot?.revision!==fresh.revision){
        snapshot=fresh;selected=null;notes.clear();previous=null;disposeModel();disposeSummary();store=null;selectors();choose();
        $('user-benchmark').value='none';selectBenchmark('none');
      }
      for(const child of document.querySelector('main').children)if(child.id!=='user-analysis-host')child.hidden=true;
      $('user-analysis').hidden=false;window.scrollTo({top:0});
    },
    canReplace(){return !dirty() || window.confirm('Replacing confirmed data will discard the edited scenario and its review decision. Continue?');},
    dispose(){openVersion++;disposeExport();disposeModel();disposeSummary();investigation?.dispose();snapshot=selected=baseline=store=null;notes.clear();previous=null;$('user-analysis-host')?.remove();ready=null;},
    clear:clearUploadedData,
  };
}
