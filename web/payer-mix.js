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

export function renderPayerMixComposition(root,summary) {
  root.replaceChildren();
  if(!summary?.categories?.length) return;
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 520 210');svg.setAttribute('role','img');svg.setAttribute('aria-label','Payer Mix Composition');
  const title=document.createElementNS('http://www.w3.org/2000/svg','text');title.setAttribute('x','0');title.setAttribute('y','18');title.setAttribute('class','chart-label');title.textContent='Payer Mix Composition';svg.append(title);
  const colors=['#c3a45d','#8096a3','#6f8974','#9d6c5d','#8b82a7','#777'];
  const track=document.createElementNS('http://www.w3.org/2000/svg','rect');track.setAttribute('x','0');track.setAttribute('y','42');track.setAttribute('width','320');track.setAttribute('height','26');track.setAttribute('class','donut-track');svg.append(track);
  let offset=0;
  summary.categories.forEach((item,index)=>{
    const share=Math.max(0,Math.min(1,Number(item.share)||0)),bar=document.createElementNS('http://www.w3.org/2000/svg','rect');bar.setAttribute('x',String(320*offset));bar.setAttribute('y','42');bar.setAttribute('width',String(320*share));bar.setAttribute('height','26');bar.setAttribute('fill',colors[index%colors.length]);bar.setAttribute('data-payer-category',item.category);bar.setAttribute('data-share',item.share);bar.setAttribute('aria-label',`${item.category}: ${(share*100).toFixed(1)}%`);svg.append(bar);offset+=share;
    const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x','0');label.setAttribute('y',String(100+index*22));label.setAttribute('class','chart-label');label.textContent=`${item.category} ${(share*100).toFixed(1)}%`;svg.append(label);
  });
  root.append(svg);
}
