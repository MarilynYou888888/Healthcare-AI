import {GRAPH, formatValue, formatPercent} from './scenario.js';
import {createReviewSession, REVIEW_ACTIONS} from './interpretation.js';
import {scenarioPresentation, tone} from './presentation.js';
import {mountScenarioCharts} from './charts.js';
const $ = id => document.getElementById(id);
function node(tag, text, cls) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (cls) element.className = cls;
  return element;
}
export function setupNavigation() {
  const tabs = [$('tab-summary'),$('tab-model'),$('tab-investigation')];
  function activate(tab) {
    window.scrollTo({top:0,behavior:'instant'});
    for (const item of tabs) {
      const active = item === tab;
      item.setAttribute('aria-selected',String(active)); item.tabIndex = active ? 0 : -1;
      item.classList.toggle('active',active);
      $(item.getAttribute('aria-controls')).hidden = !active;
    }
    const summary = tab === tabs[0];
    const investigation = tab === tabs[2];
    document.body.classList.toggle('investigation-active',investigation);
    document.querySelector('.period').hidden = investigation;
    document.querySelector('.eyebrow').textContent = investigation ? 'EVIDENCE-AWARE REVIEW' : 'DRIVER-BASED PLANNING';
    $('page-title').textContent = investigation ? 'Variance Investigation' : summary ? 'Executive Summary' : 'Scenario Model';
    $('page-description').textContent = investigation ? 'What happened, and why? Evidence first. Analyst judgment last.' : summary ? 'Synthetic clinic planning · deterministic results · analyst judgment' : 'Edit an assumption cell to recalculate the complete monthly model.';
  }
  tabs.forEach((tab,index) => {
    tab.addEventListener('click',() => activate(tab));
    tab.addEventListener('keydown',event => {
      const keys = {ArrowDown:(index+1)%tabs.length,ArrowUp:(index+tabs.length-1)%tabs.length,Home:0,End:tabs.length-1};
      if (Object.hasOwn(keys,event.key)) { event.preventDefault(); const next=tabs[keys[event.key]]; activate(next); next.focus(); }
    });
  });
  $('edit-model').addEventListener('click',() => { activate(tabs[1]); $('input-provider_fte')?.focus(); });
  $('view-summary').addEventListener('click',()=>activate(tabs[0]));
  return view => activate($('tab-' + view));
}

// Stable section IDs host Ticket 5 visualizations. Every section receives the same
// ScenarioResult, with financial derivations kept out of renderers.
export function mountExecutiveSummary(store) {
  const review = createReviewSession(store);
  const renderCharts = mountScenarioCharts();
  const metrics = [...GRAPH.filter(m => ['revenue','visits','contribution','operating_income'].includes(m.id)),{id:'operating_margin',name:'Operating margin',unit:'ratio'}];
  $('summary-kpis').replaceChildren();
  $('review-actions').replaceChildren();
  const kpis = new Map();
  for (const metric of metrics) {
    const card = node('article',undefined,'kpi'); card.dataset.kpi = metric.id;
    const baseline = node('span','','kpi-baseline');
    const scenario = node('strong','','kpi-scenario');
    const delta = node('span','','kpi-change');
    card.append(node('h3',metric.name),node('small','Baseline → Scenario'),baseline,scenario,delta);
    $('summary-kpis').append(card); kpis.set(metric.id,{baseline,scenario,delta});
  }
  for (const [action,label] of Object.entries(REVIEW_ACTIONS)) {
    const button = node('button',label); button.type='button'; button.dataset.action=action;
    button.addEventListener('click',() => {
      try { review.decide(action,Number($('summary-review').dataset.revision)); }
      catch (error) { $('review-status').textContent=error.message; }
    });
    $('review-actions').append(button);
  }
  $('summary-reset').onclick=() => store.reset();
  const unsubscribeStore=store.subscribe(state => {
    const result=state.result ?? state.last_valid;
    const stale=state.status !== 'valid';
    const presentation=scenarioPresentation(result);
    const money=result.currency ?? 'USD';
    const format=(value,unit,signed=false)=>formatValue(value,unit === 'USD' ? money : unit,signed);
    renderCharts(presentation,stale);
    $('executive-view').dataset.revision=String(result.revision);
    $('executive-view').classList.toggle('stale',stale);
    $('summary-status').textContent=stale ? `Stale — last valid revision ${result.revision}. Fix the draft in Scenario Model; commentary and review are unavailable.` : `Current · Revision ${result.revision} · ${result.month} · ${result.data_kind === 'synthetic' ? 'Synthetic clinic planning' : 'Uploaded planning · '+result.entity_name+' · '+result.currency}`;
    $('summary-driver-label').textContent=result.changed_drivers.length > 1 ? 'Changed assumptions' : 'Scenario driver';
    $('summary-driver').textContent=result.changed_drivers.length ? result.changed_drivers.map(d => `${d.name}: ${format(d.baseline,d.unit)} → ${format(d.scenario,d.unit)}`).join(' · ') : 'Baseline scenario · no assumptions changed';
    for (const metric of metrics) {
      const elements=kpis.get(metric.id);
      if(metric.id==='operating_margin') {
        const margin=presentation.margin;
        elements.baseline.textContent=(margin.baseline===null?'N/A':format(margin.baseline,'ratio'))+' →';
        elements.scenario.textContent=margin.scenario===null?'N/A':format(margin.scenario,'ratio');
        elements.delta.textContent=margin.change_pp===null?'N/A · revenue is zero':format(margin.change_pp,'number',true)+' pp';
        elements.delta.className='kpi-change '+(margin.change_pp===null?'neutral':tone(margin.change_pp));
        continue;
      }
      const delta=result.changes[metric.id];
      elements.delta.className='kpi-change '+(metric.id==='visits'?'neutral':tone(delta.amount));
      elements.baseline.textContent=format(result.baseline[metric.id],metric.unit)+' →';
      elements.scenario.textContent=format(result.scenario[metric.id],metric.unit);
      elements.delta.textContent=format(delta.amount,metric.unit,true)+' · '+(delta.percent === null ? `N/A (${delta.percent_reason})` : formatPercent(delta.percent));
    }
    $('summary-impact-value').textContent=format(result.impact,'USD',true);
    $('summary-impact-value').className=tone(result.impact);
    $('visits-comparison').textContent=`Expected visits: ${format(result.baseline.visits,'visits')} → ${format(result.scenario.visits,'visits')} · ${result.changes.visits.percent===null?'N/A':formatPercent(result.changes.visits.percent)}. Separate volume measure; financial bars are ${money} only.`;
    $('summary-impact-context').textContent=`Operating income: ${format(result.baseline.operating_income,'USD')} baseline → ${format(result.scenario.operating_income,'USD')} scenario. No approved forecast is changed.`;
    const comparisons=GRAPH.filter(m => ['revenue','contribution','operating_income'].includes(m.id)).map(m => [m.name,`${format(result.baseline[m.id],'USD')} → ${format(result.scenario[m.id],'USD')}`]);
    renderPairs('summary-comparison-values',comparisons);
    renderPairs('summary-expense-values',[
      ['Variable labor',format(result.scenario.labor,'USD')],
      ['Variable supplies',format(result.scenario.supplies,'USD')],
      ['Fixed operating expense',format(result.assumptions.fixed_expense,'USD')],
    ]);
  });
  const unsubscribeReview=review.subscribe(state => {
    const commentary=state.commentary;
    $('summary-review').dataset.revision=String(state.revision);
    $('summary-commentary').dataset.revision=commentary ? String(commentary.revision) : '';
    $('commentary-summary').textContent=commentary?.summary ?? 'Commentary unavailable until all scenario inputs are valid.';
    fillList('commentary-implications',commentary?.implications ?? []);
    fillList('commentary-questions',commentary?.questions ?? []);
    fillList('commentary-facts',commentary ? [...commentary.drivers.map(d=>d.text),...commentary.metrics.map(m=>m.text)] : []);
    $('commentary-source').textContent=commentary?.source_label ?? '';
    $('review-status').textContent=state.decision ? `${state.decision.label} · Revision ${state.decision.revision}. No forecast updated.` : state.review_eligible ? 'Not reviewed for this revision.' : 'Review unavailable for invalid inputs.';
    $('review-actions').querySelectorAll('[data-action]').forEach(button => {
      button.disabled=!state.review_eligible;
      button.setAttribute('aria-pressed',String(state.decision?.action===button.dataset.action));
    });
  });
  return () => { unsubscribeStore(); unsubscribeReview(); review.dispose(); };
}
function fillList(id,items) { $(id).replaceChildren(...items.map(text=>node('li',text))); }
function renderPairs(id,pairs) {
  $(id).replaceChildren(...pairs.map(([label,value])=>{
    const row=node('div'); row.append(node('dt',label),node('dd',value)); return row;
  }));
}
