import {formatValue, formatPercent, GRAPH} from './scenario.js';

export const DISCLOSURE = 'Offline demo — deterministic fallback commentary; no live LLM used.';
export const REVIEW_ACTIONS = Object.freeze({
  retain_baseline: 'Reviewed — retain baseline',
  investigate: 'Request further investigation',
  forecast_review: 'Mark for forecast-assumption review',
});
const QUESTIONS = Object.freeze({
  provider_fte: 'Can effective provider availability support the modeled capacity?',
  clinic_days: 'Are the proposed operating days feasible for this clinic-month?',
  visits_per_provider_day: 'Is the assumed daily visit capacity operationally achievable?',
  utilization: 'What demand and scheduling evidence supports the utilization assumption?',
  net_revenue_per_visit: 'What evidence supports the assumed net realized revenue per visit?',
  reimbursement_factor: 'Is the reimbursement adjustment supported without double-counting the net rate?',
  labor_per_visit: 'Which labor costs truly vary with visits rather than remaining fixed?',
  supplies_per_visit: 'Does the variable supply assumption reflect the expected visit mix?',
  fixed_expense: 'Which fixed costs can change within the modeled month?',
});
function freeze(value) {
  if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}
function currentResult(state) {
  const result = state?.result;
  return state?.status === 'valid' && state.review_eligible && result?.validation?.status === 'valid'
    && result.data_kind === 'synthetic' && result.revision === state.revision ? result : null;
}

// Narrow adaptation of Phase 4's result-bound formatter pattern. No provider text,
// financial arithmetic, cause classification, or forecast-writing capability.
export function interpret(state) {
  const result = currentResult(state);
  if (!result) return null;
  const drivers = result.changed_drivers.map(d => ({id:d.id,
    text:`${d.name}: ${formatValue(d.baseline,d.unit)} → ${formatValue(d.scenario,d.unit)}`,
    source:`assumptions.${d.id}`}));
  const metrics = GRAPH.filter(m => result.changes[m.id].amount !== '0').map(m => {
    const delta = result.changes[m.id];
    const percentage = delta.percent === null ? `N/A (${delta.percent_reason})` : formatPercent(delta.percent);
    return {id:m.id, text:`${m.name}: ${formatValue(result.baseline[m.id],m.unit)} → ${formatValue(result.scenario[m.id],m.unit)}; change ${formatValue(delta.amount,m.unit,true)} (${percentage}).`,
      sources:[`baseline.${m.id}`,`scenario.${m.id}`,`changes.${m.id}`]};
  });
  const summary = drivers.length
    ? `Under these synthetic assumptions, modeled monthly operating income is ${formatValue(result.scenario.operating_income,'USD')} versus baseline ${formatValue(result.baseline.operating_income,'USD')}, a ${formatValue(result.impact,'USD',true)} change. This is a hypothetical scenario, not a prediction or approved forecast update.`
    : 'The scenario matches the synthetic baseline. No assumptions have changed and there is no modeled financial impact. Edit an assumption to explore a hypothetical outcome.';
  const implications = [];
  if (result.changes.visits.amount !== '0') implications.push('In this model, visit volume drives revenue and variable labor and supply expense. Actual cost flexibility would require analyst validation.');
  if (result.assumption_changes.fixed_expense.amount === '0' && result.changes.visits.amount !== '0') implications.push('Fixed expense remains unchanged under this scenario, so it does not offset the volume change.');
  if (result.changed_drivers.some(d => ['net_revenue_per_visit','reimbursement_factor'].includes(d.id))) implications.push('The net-rate assumptions affect modeled revenue without changing visit capacity or volume.');
  if (result.changes.revenue.amount.startsWith('-') && result.changes.variable_expense.amount.startsWith('-')
      && result.assumption_changes.fixed_expense.amount === '0' && result.impact.startsWith('-')) {
    implications.push('Revenue downside is partially offset by lower variable expense under these assumptions.');
  }
  if (!implications.length && drivers.length) {
    implications.push(metrics.length === 0
      ? 'The changed assumptions produce no net change in the displayed outputs; offsetting operating inputs can preserve the same modeled result.'
      : 'The displayed impact follows the changed assumptions within this one-month model; feasibility and business interpretation remain for the analyst.');
  }
  return freeze({mode:'offline-deterministic-fallback', disclosure:DISCLOSURE, revision:result.revision,
    baseline_id:result.baseline_id, month:result.month, model_version:result.model_version,
    summary, drivers, metrics, implications,
    questions:drivers.length ? drivers.map(d => QUESTIONS[d.id]) : ['Which operating assumption should be tested, and what evidence would support it?'],
    source_label:`Synthetic planning baseline ${result.baseline_id} · ${result.month} · ${result.model_version} · Revision ${result.revision}`,
    boundary:'Analyst review records a scenario decision only. It does not confirm an actual cause or update an approved forecast.'});
}

export function createReviewSession(store) {
  const listeners = new Set();
  let decision = null;
  let snapshot;
  function publish() {
    const state = store.snapshot();
    snapshot = freeze({revision:state.revision, commentary:interpret(state), decision,
      review_eligible:currentResult(state) !== null});
    listeners.forEach(listener => listener(snapshot));
  }
  const unsubscribe = store.subscribe(() => { decision = null; publish(); });
  return Object.freeze({
    snapshot:() => snapshot,
    subscribe(listener) { listeners.add(listener); listener(snapshot); return () => listeners.delete(listener); },
    decide(action, expectedRevision) {
      const result = currentResult(store.snapshot());
      if (!Object.hasOwn(REVIEW_ACTIONS,action)) throw new Error('Unknown analyst decision.');
      if (!result || result.revision !== expectedRevision) throw new Error('Review requires the current valid calculation revision.');
      decision = freeze({action, label:REVIEW_ACTIONS[action], revision:result.revision,
        baseline_id:result.baseline_id, month:result.month, model_version:result.model_version,
        forecast_updated:false, causal_confirmation:false});
      publish();
      return decision;
    },
    dispose() { unsubscribe(); listeners.clear(); decision = null; snapshot = null; },
  });
}
