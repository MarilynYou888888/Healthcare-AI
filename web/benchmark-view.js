// Read-only public context. Existing loader-derived ratios retain their full
// source records. No corporate metric is passed into the synthetic model.
import {node} from './charts.js';
import {formatValue} from './scenario.js';
export function benchmarkComparison(companies) {
  if(companies.some(c=>c.data_kind!=='public_benchmark')) throw new Error('Only public benchmark records can supply this comparison.');
  return ['LABOR_RATIO','SUPPLIES_RATIO'].map(id=>({
    id,label:id==='LABOR_RATIO'?'Labor / revenue':'Supplies / revenue',
    metrics:companies.map(company=>({company:company.company,ticker:company.ticker,metric:company.metrics.find(m=>m.metric_id===id && m.period==='FY2025' && m.business_segment==='Consolidated') ?? null})),
  }));
}
export async function mountBenchmarkComparison() {
  const root=document.getElementById('benchmark-ratio-chart'),status=document.getElementById('benchmark-comparison-status');
  try {
    const companies=await Promise.all(['HCA','THC'].map(async ticker=>{
      const response=await fetch('/api/benchmarks/'+ticker);if(!response.ok)throw new Error();return response.json();
    }));
    root.replaceChildren(...benchmarkComparison(companies).map(group=>{
      const card=node('article',undefined,'benchmark-ratio');card.append(node('h4',group.label));
      for(const {company,ticker,metric} of group.metrics) {
        const row=node('div',undefined,'benchmark-ratio-row');
        row.append(node('span',company),node('strong',metric?.value==null?'Not disclosed':formatValue(metric.value,'ratio')));
        const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 400 14');svg.setAttribute('role','img');svg.setAttribute('preserveAspectRatio','none');
        svg.setAttribute('aria-label',`${company} ${group.label}: ${metric?.value==null?'Not disclosed':formatValue(metric.value,'ratio')}. 0 to 100% scale.`);
        const title=document.createElementNS(svg.namespaceURI,'title');title.textContent=svg.getAttribute('aria-label')+(metric?' '+metric.reporting_basis+' · FY2025 public filings · read-only.':'');svg.append(title);
        if(metric?.value!=null) {
          const rect=document.createElementNS(svg.namespaceURI,'rect');rect.setAttribute('width',String(Number(metric.value)*400));rect.setAttribute('height','10');rect.setAttribute('rx','2');rect.setAttribute('class',ticker==='HCA'?'benchmark-hca':'benchmark-tenet');svg.append(rect);
        }
        row.append(svg);
        if(metric) {
          const source=node('a',`${ticker} source & ratio definition ↗`);source.href=metric.source_url;source.target='_blank';source.rel='noopener noreferrer';
          const detail=node('details');detail.append(node('summary',`${ticker} · ${metric.reporting_basis} · derived`),node('p',metric.metric_definition+' '+metric.derivation),node('p',metric.source_document+' · '+metric.source_locator),source);row.append(detail);
        }
        card.append(row);
      }
      card.append(node('small','Common scale: 0–100% of each company’s consolidated revenue.'));return card;
    }));status.textContent='';
  } catch {root.replaceChildren();status.textContent='Comparison unavailable. Select a company below to inspect its available public references. The synthetic model remains independent.';}
}
