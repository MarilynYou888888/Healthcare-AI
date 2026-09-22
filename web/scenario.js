import Decimal from './vendor/decimal.mjs';

// The sole scenario calculation engine. Neither views nor Python repeat this model.
const D = Decimal.clone({precision: 28, rounding: Decimal.ROUND_HALF_EVEN});
// Technical resource limits, not clinical or financial assumption policies.
const MAX_INPUT_LENGTH = 128;
const MAX_EXPONENT = 1000;
const supported = value => value.isFinite() && Math.abs(value.e) <= MAX_EXPONENT;
export const MODEL_VERSION = 'clinic-month-v1';
export const ASSUMPTIONS = deepFreeze({
  provider_fte: {name: 'Provider FTE', unit: 'FTE'},
  clinic_days: {name: 'Clinic operating days', unit: 'days'},
  visits_per_provider_day: {name: 'Visits / provider day', unit: 'slots'},
  utilization: {name: 'Utilization', unit: 'ratio'},
  net_revenue_per_visit: {name: 'Net revenue / visit', unit: 'USD'},
  labor_per_visit: {name: 'Variable labor / visit', unit: 'USD'},
  supplies_per_visit: {name: 'Variable supplies / visit', unit: 'USD'},
  fixed_expense: {name: 'Fixed monthly expense', unit: 'USD'},
  reimbursement_factor: {name: 'Reimbursement factor', unit: 'multiplier'},
});
export const GRAPH = deepFreeze([
  {id:'capacity', name:'Available visit capacity', unit:'slots', op:'multiply', inputs:['provider_fte','clinic_days','visits_per_provider_day']},
  {id:'visits', name:'Expected visits', unit:'visits', op:'multiply', inputs:['capacity','utilization']},
  {id:'revenue', name:'Modeled net patient revenue', unit:'USD', op:'multiply', inputs:['visits','net_revenue_per_visit','reimbursement_factor']},
  {id:'labor', name:'Variable labor expense', unit:'USD', op:'multiply', inputs:['visits','labor_per_visit']},
  {id:'supplies', name:'Variable supply expense', unit:'USD', op:'multiply', inputs:['visits','supplies_per_visit']},
  {id:'variable_expense', name:'Total variable expense', unit:'USD', op:'add', inputs:['labor','supplies']},
  {id:'contribution', name:'Contribution margin', unit:'USD', op:'subtract', inputs:['revenue','variable_expense']},
  {id:'operating_income', name:'Modeled clinic operating income', unit:'USD', op:'subtract', inputs:['contribution','fixed_expense']},
]);

function deepFreeze(value) {
  if (value && typeof value === 'object' && !Object.isFrozen(value)) {
    Object.values(value).forEach(deepFreeze);
    Object.freeze(value);
  }
  return value;
}

export function validate(assumptions, month) {
  const errors = {};
  const match = /^(\d{4})-(\d{2})$/.exec(month);
  const year = match ? Number(match[1]) : 0;
  const mon = match ? Number(match[2]) : 0;
  if (!year || mon < 1 || mon > 12) errors.month = 'Use a valid YYYY-MM planning period.';
  const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const days = [31,leap ? 29 : 28,31,30,31,30,31,31,30,31,30,31][mon-1];
  const values = {};
  if (!assumptions || Object.keys(assumptions).some(id => !ASSUMPTIONS[id])) errors.assumptions = 'Use only the nine synthetic assumptions.';
  for (const [id, meta] of Object.entries(ASSUMPTIONS)) {
    const raw = assumptions?.[id];
    if (typeof raw !== 'string' || !raw.trim()) { errors[id] = `${meta.name} is required; blank is not zero.`; continue; }
    if (raw.length > MAX_INPUT_LENGTH) { errors[id] = `${meta.name} exceeds the demo's 128-character input limit.`; continue; }
    try {
      const value = new D(raw.trim());
      if (!supported(value)) { errors[id] = `${meta.name} exceeds the demo's supported numeric range (exponent −1000 to 1000).`; continue; }
      if (!value.isFinite() || value.lt(0)) throw new Error();
      values[id] = value;
    } catch { errors[id] = `${meta.name} must be a finite, nonnegative number.`; }
  }
  if (values.utilization?.gt(1)) errors.utilization = 'Utilization must be between 0% and 100%.';
  if (values.clinic_days && (!values.clinic_days.isInteger() || values.clinic_days.gt(days ?? 31))) errors.clinic_days = `Use whole operating days between 0 and ${days ?? 31}.`;
  return {errors, values};
}

export function calculate(assumptions, month) {
  const {errors, values} = validate(assumptions, month);
  if (Object.keys(errors).length) throw new Error(Object.values(errors).join(' '));
  const outputs = {};
  for (const item of GRAPH) {
    const args = item.inputs.map(id => values[id]);
    const value = item.op === 'multiply' ? args.reduce((a,b) => a.mul(b))
      : item.op === 'add' ? args[0].add(args[1]) : args[0].sub(args[1]);
    if (!supported(value)) throw new Error('Derived output exceeds the demo supported numeric range (exponent −1000 to 1000).');
    values[item.id] = value;
    outputs[item.id] = value.toString();
  }
  return deepFreeze(outputs);
}

export function change(baseline, scenario) {
  const base = new D(baseline);
  const delta = new D(scenario).sub(base);
  return {amount:delta.toString(), percent:base.gt(0) ? delta.div(base).mul(100).toString() : null,
    percent_reason:base.gt(0) ? null : base.isZero() ? 'Baseline is zero.' : 'Baseline is negative.'};
}

export function scenarioResult(baseline, assumptions, revision) {
  if (!['synthetic','user_uploaded'].includes(baseline.data_kind)) throw new Error('Scenario inputs must be synthetic or validated user planning data.');
  if (baseline.data_kind === 'user_uploaded' && (!baseline.entity_id || !baseline.currency || !baseline.source_lineage)) throw new Error('Uploaded planning inputs require identity, currency, and lineage.');
  const base = calculate(baseline.assumptions, baseline.month);
  const scenario = calculate(assumptions, baseline.month);
  const changes = Object.fromEntries(GRAPH.map(({id}) => [id, change(base[id], scenario[id])]));
  const assumptionChanges = Object.fromEntries(Object.keys(ASSUMPTIONS).map(id => [id,change(baseline.assumptions[id],assumptions[id])]));
  const changedDrivers = Object.entries(ASSUMPTIONS).filter(([id]) => !new D(assumptions[id]).eq(baseline.assumptions[id]))
    .map(([id, meta]) => ({id, ...meta, unit:meta.unit === 'USD' ? (baseline.currency ?? 'USD') : meta.unit, baseline:baseline.assumptions[id], scenario:assumptions[id]}));
  const result = {data_kind:baseline.data_kind, currency:baseline.currency ?? 'USD', entity_id:baseline.entity_id, entity_name:baseline.entity_name, scenario_name:baseline.scenario_name, source_lineage:baseline.source_lineage, source:baseline.source, validation:{status:'valid',errors:{}}, model_version:MODEL_VERSION, baseline_id:baseline.baseline_id,
    clinic:baseline.clinic, month:baseline.month, revision, baseline_assumptions:{...baseline.assumptions},
    assumptions:{...assumptions}, baseline:base, scenario, changes, assumption_changes:assumptionChanges,
    changed_drivers:changedDrivers, output_units:Object.fromEntries(GRAPH.map(m => [m.id,m.unit === 'USD' ? (baseline.currency ?? 'USD') : m.unit])),
    impact:changes.operating_income.amount, impact_definition:'Hypothetical one-month operating income change; not an approved forecast update.'};
  result.presentation = assemblePresentation(result);
  return deepFreeze(result);
}

export function formula(item) {
  const names = {...ASSUMPTIONS, ...Object.fromEntries(GRAPH.map(m => [m.id,m]))};
  return item.inputs.map(id => names[id].name).join({multiply:' × ', add:' + ', subtract:' − '}[item.op]);
}

// Presentation helpers never feed rounded amounts back into the model.
export function formatValue(raw, unit, signed = false) {
  const value = new D(raw);
  const sign = value.lt(0) ? '−' : signed && value.gt(0) ? '+' : '';
  let display = unit === 'ratio' ? value.abs().mul(100) : value.abs();
  let fixed = display.toFixed(2);
  const money = /^[A-Z]{3}$/.test(unit) && unit !== 'FTE';
  if (!money) fixed = fixed.replace(/\.?0+$/, '');
  if (unit === 'FTE' && !fixed.includes('.')) fixed += '.0';
  fixed = fixed.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  return sign + (unit === 'USD' ? '$' : money ? unit+' ' : '') + fixed + (unit === 'ratio' ? '%' : unit === 'multiplier' ? '×' : '');
}
export function formatPercent(raw) {
  const d = new D(raw);
  return (d.lt(0) ? '−' : d.gt(0) ? '+' : '') + d.abs().toFixed(2) + '%';
}
export function inputValue(raw, unit) { return unit === 'ratio' ? new D(raw).mul(100).toString() : raw; }
export function modelInput(raw, unit) {
  if (!raw.trim() || raw.length > MAX_INPUT_LENGTH) return raw;
  try { return unit === 'ratio' ? new D(raw).div(100).toString() : raw; }
  catch { return raw; }
}

export function createScenarioStore(source) {
  const baseline = deepFreeze(structuredClone(source));
  const listeners = new Set();
  let revision = 0;
  let draft = {...baseline.assumptions};
  let lastValid = scenarioResult(baseline, draft, revision);
  let state;
  function refresh() {
    const errors = validate(draft, baseline.month).errors;
    let result = null;
    if (!Object.keys(errors).length) {
      try { result = scenarioResult(baseline, draft, revision); lastValid = result; }
      catch (error) { errors.model = error.message; }
    }
    state = deepFreeze({revision, status:result ? 'valid' : 'invalid', draft:{...draft},
      errors, result, last_valid:lastValid, review_eligible:result !== null});
    listeners.forEach(listener => listener(state));
    return state;
  }
  refresh();
  return Object.freeze({
    snapshot:() => state,
    subscribe(listener) { listeners.add(listener); listener(state); return () => listeners.delete(listener); },
    edit(id, value) {
      if (!ASSUMPTIONS[id]) throw new Error('Unknown scenario assumption.');
      draft = {...draft, [id]:value}; revision += 1; return refresh();
    },
    reset() { draft = {...baseline.assumptions}; revision += 1; return refresh(); },
  });
}

function assemblePresentation(source) {
  const base=source.baseline, scenario=source.scenario;
  const bridge=[{id:'baseline',label:'Baseline income',start:'0',end:base.operating_income,impact:base.operating_income,tone:'baseline',meaning:'Baseline clinic operating income.'}];
  let cursor=new D(base.operating_income);
  for(const [id,label,metric,expense] of [
    ['revenue','Revenue','revenue',false],['labor','Variable labor','labor',true],
    ['supplies','Variable supplies','supplies',true],['fixed_expense','Fixed expense','fixed_expense',true],
  ]) {
    const fixed=metric==='fixed_expense';
    const b=fixed?source.baseline_assumptions[metric]:base[metric];
    const s=fixed?source.assumptions[metric]:scenario[metric];
    const change=fixed?source.assumption_changes[metric]:source.changes[metric];
    const impact=new D(change.amount).mul(expense?-1:1),end=cursor.add(impact);
    bridge.push({id,label,baseline:b,scenario:s,start:cursor.toString(),end:end.toString(),impact:impact.toString(),tone:impact.isZero() ? 'neutral' : impact.gt(0) ? 'favorable' : 'unfavorable',
      meaning:expense ? 'An expense decrease adds to income; an increase subtracts from income.' : 'Revenue change flows into operating income.'});
    cursor=end;
  }
  bridge.push({id:'scenario',label:'Scenario income',start:'0',end:scenario.operating_income,impact:scenario.operating_income,tone:'scenario',meaning:'Scenario clinic operating income from the shared model.'});
  const total=new D(scenario.variable_expense).add(source.assumptions.fixed_expense);
  const expenses={total:total.toString(),items:[['labor','Variable labor',scenario.labor],['supplies','Variable supplies',scenario.supplies],['fixed_expense','Fixed operating expense',source.assumptions.fixed_expense]].map(([id,label,amount])=>({id,label,amount,share:total.isZero()?null:new D(amount).div(total).toString()}))};
  const comparison=GRAPH.filter(n=>['revenue','contribution','operating_income'].includes(n.id)).map(n=>({id:n.id,label:n.name,baseline:base[n.id],scenario:scenario[n.id],change:source.changes[n.id]}));
  const margin=(income,revenue)=>new D(revenue).isZero()?null:new D(income).div(revenue).toString();
  const baselineMargin=margin(base.operating_income,base.revenue),scenarioMargin=margin(scenario.operating_income,scenario.revenue);
  const affected=new Set(source.changed_drivers.map(d=>d.id));
  const names={...ASSUMPTIONS,...Object.fromEntries(GRAPH.map(n=>[n.id,n]))};
  const values={...source.assumptions,...scenario};
  const trace=GRAPH.map(n=>{
    const impacted=n.inputs.some(id=>affected.has(id));
    if(impacted) affected.add(n.id);
    return {id:n.id,label:n.name,unit:n.unit === 'USD' ? source.currency : n.unit,value:scenario[n.id],affected:impacted,formula:formula(n),op:n.op,
      inputs:n.inputs.map(id=>({id,label:names[id].name,unit:names[id].unit === 'USD' ? source.currency : names[id].unit,value:values[id],affected:affected.has(id)}))};
  });
  return deepFreeze({revision:source.revision,bridge,expenses,comparison,trace,
    margin:{baseline:baselineMargin,scenario:scenarioMargin,change_pp:baselineMargin===null||scenarioMargin===null?null:new D(scenarioMargin).sub(baselineMargin).mul(100).toString()}});
}
