import {mountScenarioModel, scenarioStore} from './scenario-view.js';
import {mountExecutiveSummary, setupNavigation} from './executive.js';
import {mountInvestigation} from './investigation.js';
import {mountBenchmarkComparison} from './benchmark-view.js';
'use strict';
const $ = id => document.getElementById(id);
const currency = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2}).format(Number(value));
const number = value => new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(Number(value));
function node(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
function metricValue(m,compact=false){
  if(m.value===null)return 'Not disclosed';
  if(m.unit==='USD')return compact ? '$'+(Number(m.value)/1e9).toFixed(3)+'B' : currency(m.value);
  if(m.unit==='ratio')return (Number(m.value)*100).toFixed(compact?1:2).replace(/\.0$/,'')+'%';
  return compact && Number(m.value)>1e6 ? (Number(m.value)/1e6).toFixed(3)+'M' : number(m.value);
}
async function getJSON(path){const response=await fetch(path);if(!response.ok)throw new Error('Unable to load validated local data.');return response.json();}
let requestVersion=0;
async function selectCompany(ticker){
  const version=++requestVersion;
  document.querySelectorAll('[data-company]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.company===ticker)));
  $('benchmark-state').classList.remove('error');$('benchmark-state').textContent='Loading verified public references…';$('benchmark-cards').replaceChildren();$('source-rows').replaceChildren();$('company-notes').textContent='';$('benchmark-note').textContent='Reference context only';
  try{
    const company=await getJSON('/api/benchmarks/'+ticker);if(version!==requestVersion)return;
    const find=(id,seg='Consolidated')=>company.metrics.find(m=>m.metric_id===id && m.period==='FY2025' && m.business_segment===seg);
    const chosen=ticker==='HCA'?[find('REVENUE'),find('LABOR'),find('EQUIVALENT_ADMISSIONS'),find('OCCUPANCY'),find('SUPPLIES_RATIO')]:[find('REVENUE'),find('SEGMENT_REVENUE','Hospital Operations'),find('SEGMENT_REVENUE','Ambulatory Care'),find('ADJUSTED_ADMISSIONS','Hospital Operations'),find('OUTPATIENT_VISITS','Hospital Operations')];
    for(const m of chosen){
      if(!m)throw new Error('Required reference metric unavailable.');
      const card=node('div',undefined,'benchmark-metric');let label=m.metric_name;
      if(ticker==='THC' && m.metric_id==='SEGMENT_REVENUE')label=m.business_segment+' revenue';
      card.append(node('span',label,'name'),node('strong',metricValue(m,true)),node('small',m.reporting_basis+(m.provenance_kind==='derived'?' · derived':'')));$('benchmark-cards').append(card);
    }
    $('benchmark-note').textContent=company.company+' · FY2025 · Context only';
    $('company-notes').textContent=company.notes;
    for(const m of company.metrics){
      const tr=node('tr'),title=node('td',m.metric_name);title.append(node('small',m.period+' · '+m.period_type+' · '+m.period_start+' to '+m.period_end+' · '+m.provenance_kind));
      const value=node('td',metricValue(m));value.append(node('small',m.unit));
      const scope=node('td',m.business_segment+' · '+m.reporting_basis);scope.append(node('small',m.metric_definition));if(m.missing_reason)scope.append(node('small',m.missing_reason));
      const source=node('td');const link=node('a',m.source_document);link.href=m.source_url;link.target='_blank';link.rel='noopener noreferrer';
      source.append(link,node('small',m.source_locator),node('small',m.extraction_reference));
      if(m.derivation)source.append(node('small','Derived: '+m.derivation));
      tr.append(title,value,scope,source);$('source-rows').append(tr);
    }
    $('benchmark-state').textContent='';
  }catch(error){if(version!==requestVersion)return;$('benchmark-cards').replaceChildren();$('benchmark-state').textContent='Public reference unavailable. The synthetic baseline is independent and remains usable.';$('benchmark-state').classList.add('error');}
}
document.querySelectorAll('[data-company]').forEach(button=>button.addEventListener('click',()=>selectCompany(button.dataset.company)));
$('sources-button').addEventListener('click',()=>{const show=$('source-panel').hidden;$('source-panel').hidden=!show;$('sources-button').setAttribute('aria-expanded',String(show));$('sources-button').textContent=show?'Close source register ↑':'Inspect sources & definitions ↗';});
const openWorkspace = setupNavigation();
mountInvestigation(openWorkspace);
getJSON('/api/baseline').then(baseline => { mountScenarioModel(baseline); mountExecutiveSummary(scenarioStore); }).catch(()=>{$('scenario-status').textContent='Baseline unavailable — check synthetic input validation';$('scenario-status').classList.add('error');$('reset-scenario').disabled=true;$('summary-reset').disabled=true;$('summary-status').textContent='Scenario unavailable — synthetic inputs could not be validated.';});
selectCompany('HCA');

mountBenchmarkComparison();
$('benchmark-jump').addEventListener('click',()=>{document.querySelector('.reference').scrollIntoView({block:'start'});$('benchmark-comparison-panel').open=true;});
$('reset-demo').addEventListener('click',()=>window.location.reload());
