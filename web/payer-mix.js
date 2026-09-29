import Decimal from './vendor/decimal.mjs';

const D=Decimal.clone({precision:28,rounding:Decimal.ROUND_HALF_EVEN});
const frozen=value=>{if(value&&typeof value==='object'&&!Object.isFrozen(value)){Object.values(value).forEach(frozen);Object.freeze(value);}return value;};

export function payerMixSummary(rows,entityId,entityName,period) {
  const selected=(rows??[]).filter(row=>row.period===period&&((entityId&&row.entity_id===entityId)||(entityName&&row.entity_name===entityName)));
  const categories=selected.map(row=>({category:row.payer_category,share:row.payer_mix_share,rate:row.net_revenue_per_visit||row.reimbursement_rate||''}));
  const total=categories.reduce((sum,row)=>sum.add(row.share||0),new D(0));
  const complete=categories.length>0&&categories.every(row=>row.rate!=='');
  const blended=complete?categories.reduce((sum,row)=>sum.add(new D(row.share).mul(row.rate)),new D(0)).toString():'';
  return frozen({rows:selected,categories,total:total.toString(),shares_complete:categories.length>0&&total.eq(1),reimbursement_complete:complete,blended_net_revenue_per_visit:blended});
}

export function payerMixContextText(summary) {
  if(!summary?.rows?.length) return 'No payer-mix data is available for the selected entity and period.';
  if(!summary.reimbursement_complete) return 'Payer mix is available as context, but payer-specific reimbursement values are required to calculate a financial impact.';
  return `Blended Net Revenue / Visit: ${summary.blended_net_revenue_per_visit}`;
}
