// Investigation state is local to this page session. No browser persistence and
// no writes to the ScenarioStore: handoff carries provenance, never assumptions.
import {formatValue} from './scenario.js';
const $ = id => document.getElementById(id);
const STATES = {
  observed_fact:'Observed Fact', candidate_driver:'Candidate Driver', supported_driver:'Supported Driver',
  analyst_confirmed_cause:'Analyst-Confirmed Cause', rejected_driver:'Rejected Driver', unresolved_driver:'Unresolved Driver',
};
const FACT_LABELS = {
  REV_NET_PATIENT:'Net patient revenue', PATIENT_VISITS:'Patient visits',
  PROVIDER_AVAILABLE_DAYS:'Provider available days', NET_REVENUE_PER_VISIT:'Net revenue / visit',
  PROVIDER_PTO_DAYS:'Provider PTO', CLINIC_CLOSURE_DAYS:'Clinic closure', OVERTIME_HOURS:'Overtime hours',
  COMMERCIAL_PAYER_MIX:'Commercial payer mix', clinic_identity:'Clinic identity', reported_event:'Operating event',
};
const ACTIONS = {confirm:'Confirm supported cause', reject:'Reject cause', keep_unresolved:'Keep unresolved', request_investigation:'Request further investigation'};
function node(tag,text,cls) {
  const element=document.createElement(tag);
  if(text !== undefined) element.textContent=text;
  if(cls) element.className=cls;
  return element;
}
const label = value => value.replaceAll('_',' ');
function sources(references) {
  const list=node('ul',undefined,'evidence-sources');
  for(const ref of references) {
    list.append(node('li',`${ref.input_file} · ${Object.entries(ref.row_selector).map(([key,value])=>`${key}=${value}`).join(', ')} · Source: ${ref.source}${ref.recorded_at ? ' · Recorded: '+ref.recorded_at : ''}`));
  }
  return list;
}
function details(title,children) {
  const detail=node('details'); detail.append(node('summary',title),...children); return detail;
}
function display(value,unit) {
  if(value === null) return 'Unavailable';
  return formatValue(value,unit || 'number');
}
async function request(path,options) {
  const response=await fetch(path,options);
  if(!response.ok) throw new Error('Investigation unavailable or review rejected. Reload and select an allowed action.');
  return response.json();
}
function canReview(state,action) {
  if(action === 'confirm') return state === 'supported_driver';
  if(action === 'request_investigation') return true;
  if(action === 'reject') return ['candidate_driver','supported_driver','unresolved_driver','rejected_driver'].includes(state);
  return ['candidate_driver','supported_driver','unresolved_driver'].includes(state);
}

export function mountInvestigation(openWorkspace) {
  const render=createInvestigationRenderer({decide,handoff});
  const sessions=new Map();
  let current=null, version=0;
  function clearHandoff() {
    $('investigation-handoff').hidden=true;
    document.querySelectorAll('.handoff-target').forEach(field=>{
      field.classList.remove('handoff-target');
      const descriptions=(field.getAttribute('aria-describedby') ?? '').split(/\s+/).filter(id=>id && id !== 'investigation-handoff');
      if(descriptions.length) field.setAttribute('aria-describedby',descriptions.join(' '));
      else field.removeAttribute('aria-describedby');
    });
  }
  function pending() {
    current=null;
    $('investigation-content').hidden=true;
    $('investigation-status').textContent='Loading evidence and rule decisions…';
    clearHandoff();
  }
  async function load(context) {
    const token=++version; pending();
    try {
      const query=new URLSearchParams({case:context.case_id});
      if(context.target_id) query.set('target',context.target_id);
      if(context.target_type) query.set('type',context.target_type);
      if(context.analyst_override) query.set('override','true');
      let view=await request('/api/investigation?'+query);
      const decisions=sessions.get(view.snapshot_id);
      if(decisions) view=await request('/api/investigation/review',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({context:view.context,snapshot_id:view.snapshot_id,decisions}),
      });
      if(token !== version) return;
      current=view; render(view);
    } catch(error) { if(token === version) $('investigation-status').textContent=error.message; }
  }
  async function decide(index,action,rationale) {
    if(!current) return;
    const view=current, token=++version;
    const decisions={...(sessions.get(view.snapshot_id) ?? {}),[index]:{action,rationale}};
    $('investigation-content').inert=true;
    $('investigation-status').textContent='Validating analyst decision against the current evidence…';
    clearHandoff();
    try {
      const reviewed=await request('/api/investigation/review',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({context:view.context,snapshot_id:view.snapshot_id,decisions}),
      });
      // The request is explicit human input; only the matching view may display it.
      if(token !== version) return;
      sessions.set(view.snapshot_id,reviewed.decisions);
      current=reviewed; render(reviewed);
    } catch(error) {
      if(token === version) { current=null; $('investigation-content').hidden=true; $('investigation-status').textContent=error.message; }
    } finally { if(token === version) $('investigation-content').inert=false; }
  }
  function handoff(view,option) {
    const input=$('input-'+option.assumption);
    if(!input) { $('investigation-status').textContent='Scenario baseline unavailable; handoff cannot open an editable assumption.'; return; }
    clearHandoff();
    const system=view.system, banner=$('investigation-handoff');
    banner.replaceChildren(node('strong',`${view.context.case_id} · ${system.clinic_id} · ${system.month} → Explore ${option.label}`),
      node('p',`${system.variance.id} · ${option.driver_family} · ${STATES[option.state]}. Hypothetical scenario using a separate clinic planning baseline. No inputs or approved forecast changed. No numeric value is inferred from this evidence.`),
      details('Investigation source context',[sources(system.drivers[option.driver_index].evidence)]));
    banner.hidden=false;
    input.classList.add('handoff-target');
    const descriptions=new Set((input.getAttribute('aria-describedby') ?? '').split(/\s+/).filter(Boolean));
    descriptions.add('investigation-handoff'); input.setAttribute('aria-describedby',[...descriptions].join(' '));
    openWorkspace('model'); input.focus(); banner.scrollIntoView({block:'nearest'});
  }
  $('investigation-case').addEventListener('change',()=>load({case_id:$('investigation-case').value}));
  $('investigation-target').addEventListener('change',()=>{
    const [target_id,target_type]=JSON.parse($('investigation-target').value);
    load({case_id:$('investigation-case').value,target_id,target_type});
  });
  $('investigation-override').addEventListener('click',()=>{ if(current) load({...current.context,analyst_override:true}); });
  $('investigation-reload').addEventListener('click',()=>load(current?.context ?? {case_id:$('investigation-case').value || 'C01'}));
  request('/api/investigation/catalog').then(cases=>{
    $('investigation-case').replaceChildren(...cases.map(item=>{
      const option=node('option',`${item.case_id} · ${item.clinic_id} · ${item.month}`); option.value=item.case_id; return option;
    }));
    $('investigation-case').disabled=false; load({case_id:'C01'});
  }).catch(error=>{ $('investigation-status').textContent=error.message; });
}

export function createInvestigationRenderer({decide,handoff}) {
  function renderDrivers(view) {
    const system=view.system, effective=view.reviewed ?? system;
    const decisionsPanel=$('investigation-decision-summary');
    decisionsPanel.replaceChildren();
    $('investigation-drivers').replaceChildren(...system.drivers.map((driver,index)=>{
      const reviewed=effective.drivers[index], decision=view.decisions?.[index];
      const role=driver.role ? label(driver.role) : 'No role assigned';
      const state=STATES[reviewed.epistemic_state];
      const card=node('article',undefined,'variance-driver-card'); card.dataset.driverFamily=driver.driver_family;
      const head=node('div',undefined,'variance-driver-head');
      head.append(node('span',role==='primary'?'PRIMARY DRIVER':role==='contributing'?'CONTRIBUTING DRIVER':'DRIVER','variance-driver-role'),node('b',state,'variance-state-chip '+state.toLowerCase().replaceAll(' ','-')));
      card.append(head,node('h4',driver.driver_family),node('p',driver.explanation,'variance-driver-explanation'));
      const evidence=details('View driver evidence',[sources(driver.evidence)]); card.append(evidence);
      const rationale=node('textarea'); rationale.id='investigation-rationale-'+index; rationale.maxLength=2000;
      rationale.rows=2; rationale.value=decision?.rationale ?? '';
      const title=node('label','Analyst rationale (optional)'); title.htmlFor=rationale.id;
      const decisionCard=node('div',undefined,'variance-driver-decision');
      decisionCard.append(node('strong',driver.driver_family),node('span',decision ? ACTIONS[decision.action] : 'Not reviewed','variance-decision-state'),title,rationale);
      const buttons=node('div',undefined,'investigation-actions');
      for(const [action,title] of Object.entries(ACTIONS)) {
        const button=node('button',title); button.type='button'; button.dataset.investigationAction=action;
        button.disabled=!canReview(driver.epistemic_state,action);
        button.setAttribute('aria-pressed',String(decision?.action === action));
        button.addEventListener('click',()=>decide(index,action,rationale.value)); buttons.append(button);
      }
      decisionCard.append(buttons);
      if(reviewed.human_decision) decisionCard.append(node('small','Explicit analyst confirmation · '+reviewed.human_decision.review_reference));
      decisionsPanel.append(decisionCard);
      return card;
    }));
    $('investigation-success').textContent=`Investigation workflow completed: ${system.successful_investigation ? 'Yes' : 'No'}. Analyst-confirmed explanation: ${effective.successfully_explained_variance ? 'Yes' : 'No'}. These are distinct measures; an unresolved investigation can still be complete.`;
    $('investigation-evidence-status').replaceChildren(...system.drivers.map((driver,index)=>{
      const row=node('div',undefined,'variance-status-row');
      row.append(node('span',driver.driver_family),node('b',STATES[(effective.drivers[index] ?? driver).epistemic_state],'variance-state-chip '+STATES[(effective.drivers[index] ?? driver).epistemic_state].toLowerCase().replaceAll(' ','-'))); return row;
    }));
  }
  function render(view) {
    const system=view.system, variance=system.variance;
    $('investigation-content').inert=false; $('investigation-content').hidden=false;
    $('investigation-status').textContent=`${view.context.case_id} · ${system.clinic_id} · ${system.month} · ${view.data_kind === 'user_uploaded' ? 'Uploaded investigation inputs' : 'Synthetic demonstration case'}`;
    $('investigation-target').replaceChildren(...view.targets.map(target=>{
      const option=node('option',`${target.required ? 'Review Queue' : 'Below selection rules'} · ${target.id} · ${label(target.type)}`);
      option.value=JSON.stringify([target.id,target.type]);
      option.selected=target.id===view.context.target_id && target.type===view.context.target_type; return option;
    }));
    $('investigation-queue').textContent=(view.rule_disclosure ? view.rule_disclosure+' ' : '')+(system.review_required ? 'Selected for review: ' : 'Not selected for Review Queue. ')+(system.review.reasons.map(label).join(' · ') || 'No configured threshold or critical rule triggered.');
    $('investigation-override').hidden=system.review_required;
    $('investigation-rule-sources').replaceChildren(sources(system.review.evidence));
    const comparator=variance.variance_type === 'financial_variance' ? 'Latest Approved Forecast' : 'Expected operating comparator';
    const percent=variance.percentage === null ? 'N/A: '+label(variance.percentage_unavailable_reason) : new Intl.NumberFormat('en-US',{style:'percent',maximumFractionDigits:2}).format(Number(variance.percentage));
    const comparison=node('div',undefined,'variance-metric-grid');
    comparison.append(...[['Actual',display(variance.actual,variance.currency)],['Forecast',display(variance.forecast_or_expected,variance.currency)],['Variance',`${display(variance.absolute,variance.currency)} · ${percent}`],['Review status',label(variance.direction)]].map(([name,value])=>{const item=node('div',undefined,'variance-metric');item.append(node('span',name),node('strong',value));return item;}));
    $('investigation-comparison').replaceChildren(comparison,details('Technical comparison',[node('p',`${comparator} · ${variance.id} · ${variance.unit}${variance.currency ? ' / '+variance.currency : ''}`),sources(variance.evidence)]));
    const month=system.month;
    const visibleFacts=system.observed_facts.filter(fact=>fact.fact_type==='clinic_identity'||fact.fact_type==='reported_event'||fact.values?.month===month).filter((fact,index,array)=>fact.fact_type==='reported_event'||fact.fact_type==='clinic_identity'||array.findIndex(other=>other.subject_id===fact.subject_id&&other.values?.month===month)===index);
    $('investigation-facts').replaceChildren(...visibleFacts.map(fact=>{const values=fact.values||{};const card=node('article',undefined,'variance-fact-card');const title=FACT_LABELS[fact.subject_id]||FACT_LABELS[fact.fact_type]||label(fact.subject_id);card.append(node('span',title));if(fact.fact_type==='clinic_identity') card.append(node('strong',values.clinic_name||'Available'));else if(fact.fact_type==='reported_event') card.append(node('strong',values.event_type ? label(values.event_type) : 'Observed'));else {const actual=values.actual??'Missing', comparator=values.comparator??'Missing';card.append(node('strong',`${actual} vs ${comparator}`));const delta=Number(comparator)-Number(actual);card.append(node('em',actual===comparator?'No change':`${delta>0?'↓':'↑'} ${Math.abs(delta).toLocaleString()} vs comparator`,'variance-fact-delta'));}card.append(details('Source detail',[node('p',Object.entries(values).map(([key,value])=>`${label(key)}: ${value ?? 'Missing'}`).join(' · ')),sources(fact.evidence)]));return card;}));
    $('investigation-conclusion').textContent=system.primary_driver ? `System primary driver: ${system.primary_driver}. Supported does not mean analyst-confirmed. Contribution allocation: ${system.contribution_estimate ? display(system.contribution_estimate.amount,system.contribution_estimate.unit) : 'Not quantified; no guessed attribution.'}` : 'Unresolved — evidence does not establish a supported primary cause. Do not invent a root cause.';
    renderDrivers(view);
    const timing=system.timing;
    $('investigation-timing').textContent=`${label(timing.classification)} · ${timing.recurring ? 'Recurring condition' : 'Evidence points to a current-period condition'}`;
    $('investigation-timing-state').textContent=label(timing.classification);
    $('investigation-policy').textContent=`Configured threshold: ${new Intl.NumberFormat('en-US',{style:'percent'}).format(view.policy.structural_horizon_fraction)}. ${view.policy.disclosure}`;
    $('investigation-policy-detail').textContent=$('investigation-policy').textContent;
    $('investigation-timing-sources').replaceChildren(details('Timing and horizon sources',[sources([...timing.evidence,...timing.horizon.evidence])]));
    $('investigation-questions').replaceChildren(...system.unresolved_questions.map(question=>node('li',question)));
    $('investigation-disclosure').textContent=view.narrative_disclosure;
    if(view.narrative_status === 'withheld') $('investigation-disclosure').textContent += ' Commentary withheld by the existing narrative guard for this target. Review the deterministic facts and evidence directly.';
    const narrativeSections=view.narrative.sections||[];
    const lead=narrativeSections.find(section=>section.title==='Executive Summary')||narrativeSections[0];
    const leadBlock=node('p',lead?.body||'Commentary is unavailable for this target.');
    if(narrativeSections.length>1){
      const detailBlocks=narrativeSections.slice(1).map(section=>{const block=node('section');block.append(node('h4',section.title),node('p',section.body));return block;});
      $('investigation-narrative').replaceChildren(leadBlock,details('View detailed commentary',detailBlocks));
    } else $('investigation-narrative').replaceChildren(leadBlock);
    $('investigation-handoffs').replaceChildren(...view.handoffs.map(option=>{
      const button=node('button','Explore '+option.label); button.type='button';
      button.addEventListener('click',()=>handoff(view,option)); return button;
    }));
    if(!view.handoffs.length) $('investigation-handoffs').append(node('p','No supported provider/capacity handoff is available. Use further investigation to resolve evidence gaps; do not infer a scenario input.'));
  }
  return render;
}
