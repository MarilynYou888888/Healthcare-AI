// Investigation state is local to this page session. No browser persistence and
// no writes to the ScenarioStore: handoff carries provenance, never assumptions.
import {formatValue} from './scenario.js';
const $ = id => document.getElementById(id);
const STATES = {
  observed_fact:'Observed Fact', candidate_driver:'Candidate Driver', supported_driver:'Supported Driver',
  analyst_confirmed_cause:'Analyst-Confirmed Cause', rejected_driver:'Rejected Driver', unresolved_driver:'Unresolved Driver',
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
    $('investigation-drivers').replaceChildren(...system.drivers.map((driver,index)=>{
      const reviewed=effective.drivers[index], decision=view.decisions?.[index];
      const card=node('article',undefined,'driver-card'); card.dataset.driverFamily=driver.driver_family;
      card.append(node('h4',driver.driver_family),
        node('p',`System: ${STATES[driver.epistemic_state]} · Role: ${driver.role ? label(driver.role) : 'Not assigned'}`,'driver-system'),
        node('p',driver.explanation), sources(driver.evidence),
        node('p',`Current review state: ${STATES[reviewed.epistemic_state]} · Role: ${reviewed.role ? label(reviewed.role) : 'Not assigned'}`,'driver-review-state'),
        node('p','Session decision: '+(decision ? ACTIONS[decision.action] : 'Not reviewed'),'driver-decision'));
      if(reviewed.human_decision) card.append(node('small','Explicit analyst confirmation · '+reviewed.human_decision.review_reference));
      const rationale=node('textarea'); rationale.id='investigation-rationale-'+index; rationale.maxLength=2000;
      rationale.rows=2; rationale.value=decision?.rationale ?? '';
      const title=node('label','Analyst rationale (optional)'); title.htmlFor=rationale.id;
      card.append(title,rationale);
      const buttons=node('div',undefined,'investigation-actions');
      for(const [action,title] of Object.entries(ACTIONS)) {
        const button=node('button',title); button.type='button'; button.dataset.investigationAction=action;
        button.disabled=!canReview(driver.epistemic_state,action);
        button.setAttribute('aria-pressed',String(decision?.action === action));
        button.addEventListener('click',()=>decide(index,action,rationale.value)); buttons.append(button);
      }
      card.append(buttons);
      if(driver.epistemic_state !== 'supported_driver') card.append(node('small','Confirmation requires a Supported Driver. A human request cannot manufacture missing operating evidence.'));
      return card;
    }));
    $('investigation-success').textContent=`Investigation workflow completed: ${system.successful_investigation ? 'Yes' : 'No'}. Analyst-confirmed explanation: ${effective.successfully_explained_variance ? 'Yes' : 'No'}. These are distinct measures; an unresolved investigation can still be complete.`;
  }
  function render(view) {
    const system=view.system, variance=system.variance;
    $('investigation-content').inert=false; $('investigation-content').hidden=false;
    $('investigation-status').textContent=`${view.context.case_id} · ${system.clinic_id} · ${system.month} · ${view.data_kind === 'user_uploaded' ? 'Uploaded investigation inputs' : 'Synthetic investigation inputs'} · Current evidence`;
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
    $('investigation-comparison').replaceChildren(node('h4',variance.id),
      node('p',`${comparator}: ${display(variance.forecast_or_expected,variance.currency)} → Actual: ${display(variance.actual,variance.currency)} · ${variance.unit}${variance.currency ? ' / '+variance.currency : ''}`),
      node('strong',`Variance: ${display(variance.absolute,variance.currency)} · ${percent} · ${label(variance.direction)}`), sources(variance.evidence));
    $('investigation-facts').replaceChildren(...system.observed_facts.map(fact=>details(
      `Observed Fact · ${fact.subject_id} · ${label(fact.fact_type)}`,
      [node('p',Object.entries(fact.values).map(([key,value])=>`${label(key)}: ${value ?? 'Missing'}`).join(' · ')),sources(fact.evidence)])));
    $('investigation-conclusion').textContent=system.primary_driver ? `System primary driver: ${system.primary_driver}. Supported does not mean analyst-confirmed. Contribution allocation: ${system.contribution_estimate ? display(system.contribution_estimate.amount,system.contribution_estimate.unit) : 'Not quantified; no guessed attribution.'}` : 'Unresolved — evidence does not establish a supported primary cause. Do not invent a root cause.';
    renderDrivers(view);
    const timing=system.timing;
    $('investigation-timing').textContent=`Classification: ${label(timing.classification)} · Recurring: ${timing.recurring ? 'Yes' : 'No'} · Remaining horizon: ${timing.horizon.start} to ${timing.horizon.end} · Basis: ${label(timing.horizon.basis)}`;
    $('investigation-policy').textContent=`Configured threshold: ${new Intl.NumberFormat('en-US',{style:'percent'}).format(view.policy.structural_horizon_fraction)}. ${view.policy.disclosure}`;
    $('investigation-timing-sources').replaceChildren(details('Timing and horizon sources',[sources([...timing.evidence,...timing.horizon.evidence])]));
    $('investigation-questions').replaceChildren(...system.unresolved_questions.map(question=>node('li',question)));
    $('investigation-disclosure').textContent=view.narrative_disclosure;
    if(view.narrative_status === 'withheld') $('investigation-disclosure').textContent += ' Commentary withheld by the existing narrative guard for this target. Review the deterministic facts and evidence directly.';
    $('investigation-narrative').replaceChildren(...view.narrative.sections.map(section=>{
      const block=node('section'); block.append(node('h4',section.title),node('p',section.body)); return block;
    }));
    $('investigation-handoffs').replaceChildren(...view.handoffs.map(option=>{
      const button=node('button','Explore '+option.label); button.type='button';
      button.addEventListener('click',()=>handoff(view,option)); return button;
    }));
    if(!view.handoffs.length) $('investigation-handoffs').append(node('p','No supported provider/capacity handoff is available. Use further investigation to resolve evidence gaps; do not infer a scenario input.'));
  }
  return render;
}
