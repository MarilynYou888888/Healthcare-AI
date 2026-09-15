'use strict';
const $ = id => document.getElementById(id);
const currency = value => new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',minimumFractionDigits:2}).format(Number(value));
const number = value => new Intl.NumberFormat('en-US',{maximumFractionDigits:2}).format(Number(value));
const names = {capacity:'Available visit capacity',visits:'Expected visits',revenue:'Net patient revenue',labor:'Variable labor expense',supplies:'Variable supply expense',variable_expense:'Total variable expense',contribution:'Contribution margin',operating_income:'Modeled clinic operating income'};
function node(tag,text,cls){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;}
function metricValue(m,compact=false){
  if(m.value===null)return 'Not disclosed';
  if(m.unit==='USD')return compact ? '$'+(Number(m.value)/1e9).toFixed(3)+'B' : currency(m.value);
  if(m.unit==='ratio')return (Number(m.value)*100).toFixed(compact?1:2).replace(/\.0$/,'')+'%';
  return compact && Number(m.value)>1e6 ? (Number(m.value)/1e6).toFixed(3)+'M' : number(m.value);
}
async function getJSON(path){const response=await fetch(path);if(!response.ok)throw new Error('Unable to load validated local data.');return response.json();}
function renderBaseline(b){
  if(b.data_kind!=='synthetic')throw new Error('Expected synthetic baseline.');
  $('month').textContent=new Date(b.month+'-01T12:00:00').toLocaleDateString('en-US',{month:'long',year:'numeric'});
  const assumptions=$('assumptions');assumptions.replaceChildren();
  for(const a of b.assumptions){
    const value=a.unit==='USD'?currency(a.value):a.unit==='ratio'?number(Number(a.value)*100)+'%':a.unit==='multiplier'?Number(a.value).toFixed(2)+'×':a.id==='provider_fte'?Number(a.value).toFixed(1):number(a.value);
    const row=node('div',undefined,'assumption');row.append(node('dt',a.name),node('dd',value));assumptions.append(row);
  }
  $('visits').textContent=number(b.outputs.visits);$('revenue').textContent=currency(b.outputs.revenue);$('income').textContent=currency(b.outputs.operating_income);
  const financial=$('financial-rows');financial.replaceChildren();
  for(const key of ['capacity','labor','supplies','variable_expense','contribution']){
    const row=node('div',undefined,'financial-row'+(['variable_expense','contribution'].includes(key)?' total':''));
    row.append(node('span',names[key]),node('strong',key==='capacity'?number(b.outputs[key]):currency(b.outputs[key])));financial.append(row);
  }
  const fixed=node('div',undefined,'financial-row');fixed.append(node('span','Fixed clinic expense'),node('strong',currency(b.assumptions.find(a=>a.id==='fixed_expense').value)));financial.append(fixed);
  for(const [key,formula] of Object.entries(b.formulas)){const el=node('div',undefined,'formula');el.append(node('strong',names[key]),node('span',formula));$('formulas').append(el);}
  $('baseline-status').textContent='✓ Validated inputs · deterministic model';
}
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
getJSON('/api/baseline').then(renderBaseline).catch(()=>{$('baseline-status').textContent='Baseline unavailable — check input validation';$('baseline-status').classList.add('error');});
selectCompany('HCA');
