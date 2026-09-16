// Presentation-only measures from one immutable ScenarioResult. This module
// never calls calculate(), creates assumptions, or writes to the scenario store.
import Decimal from './vendor/decimal.mjs';
import {ASSUMPTIONS, GRAPH, formula, formatValue, formatPercent} from './scenario.js';
const D=Decimal.clone({precision:28,rounding:Decimal.ROUND_HALF_EVEN});
const frozen=value=>{if(value && typeof value==='object' && !Object.isFrozen(value)){Object.values(value).forEach(frozen);Object.freeze(value);}return value;};
export const tone=value=>new D(value).isZero() ? 'neutral' : new D(value).gt(0) ? 'favorable' : 'unfavorable';
export function compact(raw,unit='USD') {
  if(raw===null) return 'N/A';
  const d=new D(raw),abs=d.abs();
  const scale=abs.gte('1e9') ? ['1e9','B'] : abs.gte('1e6') ? ['1e6','M'] : abs.gte('1e3') ? ['1e3','K'] : ['1',''];
  return (d.lt(0)?'−':'')+(unit==='USD'?'$':'')+abs.div(scale[0]).toFixed(scale[1]?1:0)+scale[1];
}
export function scenarioPresentation(source) {
  if(source?.data_kind!=='synthetic' || source.validation?.status!=='valid') throw new Error('A validated synthetic ScenarioResult is required.');
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
    bridge.push({id,label,baseline:b,scenario:s,start:cursor.toString(),end:end.toString(),impact:impact.toString(),tone:tone(impact),
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
    return {id:n.id,label:n.name,unit:n.unit,value:scenario[n.id],affected:impacted,formula:formula(n),op:n.op,
      inputs:n.inputs.map(id=>({id,label:names[id].name,unit:names[id].unit,value:values[id],affected:affected.has(id)}))};
  });
  return frozen({source,revision:source.revision,bridge,expenses,comparison,trace,
    margin:{baseline:baselineMargin,scenario:scenarioMargin,change_pp:baselineMargin===null||scenarioMargin===null?null:new D(scenarioMargin).sub(baselineMargin).mul(100).toString()}});
}
export function comparisonTooltip(item,unit='USD') {
  const percent=item.change.percent===null?'N/A ('+item.change.percent_reason+')':formatPercent(item.change.percent);
  return `${item.label}\nBaseline: ${formatValue(item.baseline,unit)}\nScenario: ${formatValue(item.scenario,unit)}\nChange: ${formatValue(item.change.amount,unit,true)} · ${percent}`;
}
