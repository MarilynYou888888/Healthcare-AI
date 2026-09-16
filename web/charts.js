// SVG renderers map supplied values to geometry only. Financial signs, shares,
// totals and trace relationships come from the shared presentation adapter.
import {formatValue, formatPercent} from './scenario.js';
import {compact, comparisonTooltip} from './presentation.js';
const NS='http://www.w3.org/2000/svg';
export function node(tag,text,cls) {const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
function svgNode(tag,attrs={},text) {const e=document.createElementNS(NS,tag);set(e,attrs);if(text!==undefined)e.textContent=text;return e;}
function set(e,attrs) {for(const [k,v] of Object.entries(attrs))e.setAttribute(k,String(v));}
function chartShell(id,label,width,height) {
  const root=document.getElementById(id);root.hidden=false;root.classList.add('chart');
  const scroll=node('div',undefined,'chart-scroll');
  const svg=svgNode('svg',{viewBox:`0 0 ${width} ${height}`,role:'group','aria-label':label});
  const tip=node('div',undefined,'chart-tooltip');tip.id=id+'-tooltip';tip.role='tooltip';tip.hidden=true;
  const unavailable=node('p','Chart scale unavailable for these inputs. Exact values remain in the model.','chart-unavailable');unavailable.hidden=true;
  scroll.append(svg);root.append(scroll,tip,unavailable);
  root.addEventListener('keydown',event=>{if(event.key==='Escape')tip.hidden=true;});
  function interactive(element) {
    set(element,{tabindex:0,'aria-describedby':tip.id});
    for(const event of ['pointerenter','focus','click']) element.addEventListener(event,()=>{tip.textContent=element.getAttribute('aria-label');tip.hidden=false;});
    for(const event of ['pointerleave','blur']) element.addEventListener(event,()=>tip.hidden=true);
    return element;
  }
  function update(revision,stale,values) {
    root.dataset.revision=revision;root.dataset.stale=String(stale);tip.hidden=true;
    const valid=values.every(value=>Number.isFinite(Number(value)));
    scroll.hidden=!valid;unavailable.hidden=valid;return valid;
  }
  return {root,svg,interactive,update};
}
function domain(values) {let min=Math.min(0,...values),max=Math.max(0,...values);if(min===max)max=min+1;return {min,max,span:max-min};}
function makeBridge() {
  const c=chartShell('income-bridge-chart','Operating income bridge, USD',1000,285);
  const grid=svgNode('g');c.svg.append(grid);
  const pieces=Array.from({length:6},(_,i)=>{
    const group=svgNode('g'),rect=c.interactive(svgNode('rect',{rx:3,class:'chart-mark',width:88}));
    const value=svgNode('text',{'text-anchor':'middle',class:'chart-value'}),label=svgNode('text',{'text-anchor':'middle',y:263,class:'chart-label'});
    const connector=svgNode('line',{class:'bridge-connector'});
    group.append(connector,rect,value,label);c.svg.append(group);return {rect,value,label,connector,x:105+i*156};
  });
  const exact=node('details'),summary=node('summary','Inspect exact bridge values');const list=node('dl',undefined,'chart-data');exact.append(summary,list);c.root.append(exact);
  return (view,stale)=>{
    list.replaceChildren(...view.bridge.map(b=>{const row=node('div');row.append(node('dt',b.label),node('dd',formatValue(b.impact,'USD',!['baseline','scenario'].includes(b.id))));return row;}));
    const values=view.bridge.flatMap(b=>[Number(b.start),Number(b.end)]);
    const d=domain(values);
    if(!c.update(view.revision,stale,[...values,d.span]))return;
    const y=value=>225-(value-d.min)/d.span*185;
    grid.replaceChildren(...[d.min,0,d.max].filter((v,i,a)=>a.indexOf(v)===i).flatMap(value=>[
      svgNode('line',{x1:65,x2:985,y1:y(value),y2:y(value),class:value===0?'zero-line':'grid-line'}),
      svgNode('text',{x:54,y:y(value)+4,'text-anchor':'end',class:'axis-label'},compact(value)),
    ]));
    view.bridge.forEach((b,i)=>{
      const p=pieces[i],start=Number(b.start),end=Number(b.end),top=Math.min(y(start),y(end));
      const context=b.baseline===undefined?b.meaning:`Baseline: ${formatValue(b.baseline,'USD')} → Scenario: ${formatValue(b.scenario,'USD')}\n${b.meaning}`;
      const tooltip=`${b.label}\n${i===0||i===5?'Operating income':'Income impact'}: ${formatValue(b.impact,'USD',i>0&&i<5)}\n${context}${stale?'\nStale — last valid scenario.':''}`;
      set(p.rect,{x:p.x,y:top,width:88,height:Math.max(2,Math.abs(y(start)-y(end))),class:'chart-mark '+b.tone,'data-component':b.id,'data-value':b.impact,'aria-label':tooltip});
      set(p.value,{x:p.x+44,y:Math.max(17,top-10)});p.value.textContent=(Number(b.impact)>0&&i>0&&i<5?'+':'')+compact(b.impact);
      set(p.label,{x:p.x+44});p.label.textContent=b.label;
      set(p.connector,{x1:p.x-68,x2:p.x,y1:y(start),y2:y(start),visibility:i>0&&i<5?'visible':'hidden'});
    });
  };
}
function makeDonut() {
  const c=chartShell('expense-mix-chart','Scenario operating expense composition',340,245);
  c.svg.append(svgNode('circle',{cx:170,cy:118,r:83,class:'donut-track','stroke-width':24,fill:'none'}));
  const arcs=Array.from({length:3},(_,i)=>{
    const circle=c.interactive(svgNode('circle',{cx:170,cy:118,r:83,pathLength:100,'stroke-width':24,fill:'none',transform:'rotate(-90 170 118)',class:'donut-mark expense-'+i}));c.svg.append(circle);return circle;
  });
  c.svg.append(svgNode('text',{x:170,y:105,'text-anchor':'middle',class:'chart-label'},'Total operating expense'));
  const total=svgNode('text',{x:170,y:134,'text-anchor':'middle',class:'donut-total'});c.svg.append(total);
  const empty=node('p','No operating expense in this scenario; composition shares are undefined.','chart-empty');empty.hidden=true;c.root.append(empty);
  const legend=node('dl',undefined,'expense-legend');c.root.append(legend);
  return (view,stale)=>{
    const data=view.expenses;
    total.textContent=compact(data.total);total.setAttribute('aria-label',formatValue(data.total,'USD'));
    const zero=data.total==='0';empty.hidden=!zero;
    let offset=0;
    data.items.forEach((item,i)=>{
      const share=item.share===null?0:Number(item.share)*100;
      const text=`${item.label}\n${formatValue(item.amount,'USD')} · ${item.share===null?'Share N/A':formatValue(item.share,'ratio')+' of total expense'}${stale?'\nStale — last valid scenario.':''}`;
      set(arcs[i],{'stroke-dasharray':`${share} ${100-share}`,'stroke-dashoffset':-offset,'data-value':item.amount,'aria-label':text,visibility:share>0?'visible':'hidden'});offset+=share;
    });
    legend.replaceChildren(...data.items.map((item,i)=>{
      const row=node('div');row.append(node('dt',item.label,'expense-key expense-'+i),node('dd',`${formatValue(item.amount,'USD')} · ${item.share===null?'N/A':formatValue(item.share,'ratio')}`));return row;
    }));
    c.update(view.revision,stale,[data.total,...data.items.map(i=>i.share ?? '0')]);
  };
}
function makeComparison() {
  const c=chartShell('scenario-comparison-chart','Baseline versus scenario financial values, USD',670,265);
  const zero=svgNode('line',{class:'zero-line'});c.svg.append(zero);
  const groups=Array.from({length:3},(_,i)=>{
    const group=svgNode('g'),label=svgNode('text',{x:0,y:i*82+17,class:'chart-label'});
    const bars=['baseline','scenario'].map(kind=>{
      const r=c.interactive(svgNode('rect',{height:14,rx:2,class:'chart-mark '+kind}));group.append(r);return r;
    });
    const values=svgNode('text',{x:660,y:i*82+17,'text-anchor':'end',class:'chart-value'});group.append(label,values);c.svg.append(group);return {label,bars,values};
  });
  return (view,stale)=>{
    const values=view.comparison.flatMap(r=>[Number(r.baseline),Number(r.scenario)]);
    const d=domain(values);
    if(!c.update(view.revision,stale,[...values,d.span]))return;
    const x=value=>8+(value-d.min)/d.span*644;
    set(zero,{x1:x(0),x2:x(0),y1:25,y2:232});
    view.comparison.forEach((row,i)=>{
      groups[i].label.textContent={revenue:'Revenue',contribution:'Contribution margin',operating_income:'Operating income'}[row.id];
      groups[i].values.textContent=`${compact(row.baseline)} → ${compact(row.scenario)}`;
      groups[i].bars.forEach((bar,j)=>{
        const v=Number(j?row.scenario:row.baseline);
        set(bar,{x:Math.min(x(0),x(v)),y:i*82+28+j*20,width:Math.abs(x(v)-x(0)),'data-metric':row.id,'data-series':j?'scenario':'baseline','data-value':j?row.scenario:row.baseline,'aria-label':comparisonTooltip(row)+(stale?'\nStale — last valid scenario.':'')});
      });
    });
  };
}
function renderTrace(view,stale) {
  const root=document.getElementById('summary-model-logic');root.hidden=false;root.dataset.revision=view.revision;root.dataset.stale=String(stale);
  const list=document.getElementById('trace-rows');
  list.replaceChildren(...view.trace.map(item=>{
    const row=node('div',undefined,'trace-row');row.dataset.trace=item.id;row.dataset.affected=String(item.affected);
    const inputs=node('div',undefined,'trace-inputs');
    item.inputs.forEach((input,index)=>{
      if(index)inputs.append(node('span',{multiply:'×',add:'+',subtract:'−'}[item.op],'trace-operator'));
      const chip=node('span',undefined,'trace-chip'+(input.affected?' affected':''));chip.append(node('span',input.label),node('strong',formatValue(input.value,input.unit)));inputs.append(chip);
    });
    const output=node('div',undefined,'trace-result');output.append(node('span',item.label),node('strong',formatValue(item.value,item.unit)));
    row.append(inputs,node('span','→','trace-arrow'),output);row.title=item.formula;return row;
  }));
}
export function mountScenarioCharts() {
  const bridge=makeBridge(),donut=makeDonut(),comparison=makeComparison();
  return (view,stale)=>{bridge(view,stale);donut(view,stale);comparison(view,stale);renderTrace(view,stale);};
}
