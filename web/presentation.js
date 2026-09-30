// Presentation-only measures from one immutable ScenarioResult. This module
// never calls calculate(), creates assumptions, or writes to the scenario store.
import Decimal from './vendor/decimal.mjs';
import {formatValue, formatPercent} from './scenario.js';
const D=Decimal.clone({precision:28,rounding:Decimal.ROUND_HALF_EVEN});
const frozen=value=>{if(value && typeof value==='object' && !Object.isFrozen(value)){Object.values(value).forEach(frozen);Object.freeze(value);}return value;};
export const tone=value=>new D(value).isZero() ? 'neutral' : new D(value).gt(0) ? 'favorable' : 'unfavorable';
export function compact(raw,unit='USD') {
  if(raw===null) return 'N/A';
  const d=new D(raw),abs=d.abs();
  const scale=abs.gte('1e9') ? ['1e9','B'] : abs.gte('1e6') ? ['1e6','M'] : abs.gte('1e3') ? ['1e3','K'] : ['1',''];
  return (d.lt(0)?'−':'')+(unit==='USD'?'$':/^[A-Z]{3}$/.test(unit)?unit+' ':'')+abs.div(scale[0]).toFixed(scale[1]?1:0)+scale[1];
}
export function scenarioPresentation(source) {
  if (!['synthetic','user_uploaded'].includes(source?.data_kind) || source.validation?.status !== 'valid' || !source.presentation) throw new Error('A validated ScenarioResult is required.');
  return frozen({source,...source.presentation});
}
export function comparisonTooltip(item,unit='USD') {
  const percent=item.change.percent===null?'N/A ('+item.change.percent_reason+')':formatPercent(item.change.percent);
  return `${item.label}\nBaseline: ${formatValue(item.baseline,unit)}\nScenario: ${formatValue(item.scenario,unit)}\nChange: ${formatValue(item.change.amount,unit,true)} · ${percent}`;
}
