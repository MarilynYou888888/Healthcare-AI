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
    $('summary-commentary').hidden=true; // Ticket 3 provides the complete user commentary composer.
    document.querySelector('#investigation-view .investigation-controls').remove();
    document.querySelector('#investigation-view .investigation-intro').textContent='Uploaded Actual vs Latest Approved Forecast. Confirm the comparator before investigation.';
    document.querySelector('#investigation-view .model-heading .badge').textContent='UPLOADED · EVIDENCE REVIEW';
    $('investigation-target').hidden=true;
    document.querySelector('label[for="investigation-target"]').hidden=true;
    $('investigation-override').hidden=true;
    $('investigation-handoffs').closest('section').hidden=true;
    $('investigation-narrative').closest('section').hidden=true;
    $('investigation-view').insertBefore($('user-investigation-controls-template').content.cloneNode(true),$('investigation-status'));
  }).catch(error=>{ready=null;throw error;});
  return ready;
}

export function createUserWorkspace(session) {
  let snapshot=null, selected=null, baseline=null, store=null, disposeModel=()=>{},disposeSummary=()=>{},investigation=null;
  let view='model', notes=new Map(), previous=null,openVersion=0;
  const dirty=()=>store && (store.snapshot().status!=='valid' || store.snapshot().result.changed_drivers.length>0);
  function noteKey(){return JSON.stringify([snapshot?.revision,selected,view,view==='investigation'?$('user-metric')?.value:'']);}
  function saveNote(){if(previous)notes.set(previous,$('user-analyst-note').value);}
  function loadNote(){saveNote();previous=noteKey();$('user-analyst-note').value=notes.get(previous)??'';}
  function options(id,values,current) {
    $(id).replaceChildren(...values.map(([value,label])=>{const o=document.createElement('option');o.value=value;o.textContent=label;return o;}));
    if(values.some(([value])=>value===current))$(id).value=current;
  }
  function rows(role){return snapshot?.datasets[role]??[];}
  function periodRows(role){return rows(role).filter(r=>r.entity_id===$('user-entity').value && r.period===$('user-period').value);}
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
    saveNote();disposeModel();disposeSummary();store=null;
    selected={entity:$('user-entity').value,period:$('user-period').value,scenario:$('user-scenario').value};
    const row=periodRows('planning')[Number(selected.scenario)];
    $('user-open-model').disabled=$('user-open-summary').disabled=!row;
    $('user-open-investigation').disabled=!periodRows('performance').length;
    if(row){
      baseline=planningBaseline(row,snapshot.revision);store=createScenarioStore(baseline);
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
    $('user-source').textContent=labelRow ? `${labelRow._lineage.kind==='synthetic'?'SYNTHETIC SAMPLE':'USER UPLOADED'} · ${labelRow.entity_name} · ${labelRow.period} · ${row?.scenario_name||'Uploaded baseline'} · ${row?.currency||'Metric-specific units'} · Source: ${labelRow.source} · ${labelRow._lineage.file} / ${labelRow._lineage.sheet} / row ${labelRow._lineage.row}. Public benchmarks are separate context and never initialize these inputs.` : 'Operating evidence is available, but Actual vs Forecast data is required to start a variance investigation.';
    if(!row && view!=='investigation')view='investigation';
    if(view==='investigation' && !periodRows('performance').length && row)view='model';
    activate(view);
  }
  function activate(next){saveNote();view=next;for(const [key,id] of [['model','model-view'],['summary','executive-view'],['investigation','investigation-view']]) $(id).hidden=key!==view || (key==='investigation'?!periodRows('performance').length:!store);
    $('user-analysis-status').textContent=!store&&!periodRows('performance').length?'Operating evidence is available, but Actual vs Forecast data is required to start a variance investigation.':!store?'Scenario Model requires Planning Assumptions. Variance Investigation is available.':!periodRows('performance').length?'Variance Investigation requires Actual vs Forecast data. Scenario Model and Executive Summary are available.':'';
    loadNote();
  }
  return {
    async open(){
      const token=++openVersion;await templates();if(token!==openVersion)return;
      if(!investigation){investigation=mountUploadedInvestigation(()=>loadNote());
        $('user-back-import').onclick=()=>{saveNote();$('user-analysis').hidden=true;for(const child of document.querySelector('main').children)if(child.id!=='user-analysis-host')child.hidden=false;};
        for(const name of ['model','summary','investigation'])$('user-open-'+name).onclick=()=>activate(name);
        $('user-entity').onchange=()=>{selectors(1);choose();};$('user-period').onchange=()=>{selectors(2);choose();};$('user-scenario').onchange=choose;
      }
      const fresh=session.snapshot();
      if(snapshot?.revision!==fresh.revision){
        snapshot=fresh;selected=null;notes.clear();previous=null;disposeModel();disposeSummary();store=null;selectors();choose();
      }
      for(const child of document.querySelector('main').children)if(child.id!=='user-analysis-host')child.hidden=true;
      $('user-analysis').hidden=false;window.scrollTo({top:0});
    },
    canReplace(){return !dirty() || window.confirm('Replacing confirmed data will discard the edited scenario and its review decision. Continue?');},
    dispose(){openVersion++;disposeModel();disposeSummary();investigation?.dispose();snapshot=selected=baseline=store=null;notes.clear();previous=null;$('user-analysis-host')?.remove();ready=null;},
  };
}
