import {createInvestigationRenderer} from './investigation.js';
const $=id=>document.getElementById(id);
const fields=['closed','forecast','clinical','absolute','percentage','always','override','normalization','persistence','horizon','timing-source','recurring'];
const checks=new Set(['closed','forecast','clinical','always','override','recurring']);
export function mountUploadedInvestigation(onMetricChange) {
  let snapshot,entity,period,view=null,payload=null,version=0,controller=null;
  const rules=new Map();let lastMetric='';
  const render=createInvestigationRenderer({decide,handoff:()=>{}});
  function key(metric){return JSON.stringify([snapshot?.revision,entity,period,metric]);}
  function saveRule(){if(lastMetric)rules.set(key(lastMetric),['absolute','percentage','always'].map(id=>checks.has(id)?$('user-'+id).checked:$('user-'+id).value));}
  function invalidate(){version++;controller?.abort();view=payload=null;$('investigation-content').hidden=true;$('investigation-content').inert=false;$('investigation-status').textContent='Settings changed. Run the investigation before reviewing; previous decisions are not current.';}
  function resetControls(){for(const id of fields){if(checks.has(id))$('user-'+id).checked=false;else $('user-'+id).value='';}}
  function metricChanged(){saveRule();lastMetric=$('user-metric').value;resetControls();const rule=rules.get(key(lastMetric));if(rule){$('user-absolute').value=rule[0];$('user-percentage').value=rule[1];$('user-always').checked=rule[2];}invalidate();onMetricChange();}
  function requestPayload(){
    const performance=(snapshot.datasets.performance??[]).filter(r=>r.entity_id===entity&&r.period===period);
    const events=(snapshot.datasets.events??[]).filter(r=>r.entity_id===entity&&r.period===period);
    if(performance.length>1000||events.length>1000)throw new Error('This entity-month exceeds 1,000 metrics or events. Import a smaller analytical slice.');
    const read=id=>$('user-'+id).value.trim(),checked=id=>$('user-'+id).checked;
    return {selection:{entity_id:entity,period,metric_id:$('user-metric').value},import_revision:snapshot.revision,
      performance,events,confirmations:{closed_month:checked('closed'),latest_approved_forecast:checked('forecast'),clinical_labor:checked('clinical')},
      rule:{absolute:read('absolute'),percentage:read('percentage'),always_review:checked('always')},analyst_override:checked('override'),
      timing:{normalization_month:read('normalization'),persists_through:read('persistence'),forecast_end:read('horizon'),source:read('timing-source'),recurring:checked('recurring')},snapshot_id:null,decisions:{}};
  }
  async function send(request){
    const body=JSON.stringify(request);
    if(new TextEncoder().encode(body).length>1024*1024)throw new Error('The selected analytical slice exceeds the 1 MiB local request limit. Import fewer supporting records.');
    controller?.abort();controller=new AbortController();
    const response=await fetch('/api/user-investigation',{method:'POST',headers:{'Content-Type':'application/json'},body,signal:controller.signal});
    const data=await response.json();if(!response.ok)throw new Error(data.error);return data;
  }
  function show(data){
    view=data;
    const variance=data.system.variance;
    const kinds=new Set(payload.performance.map(r=>r._lineage.kind));
    const sourceLabel=kinds.size>1?'USER UPLOADED + SYNTHETIC SAMPLE':kinds.has('synthetic')?'SYNTHETIC SAMPLE':'USER UPLOADED';
    render({...data,context:{case_id:'USER DATA',target_id:variance.id,target_type:variance.variance_type},
      targets:[{id:variance.id,type:variance.variance_type,required:data.system.review_required}],
      handoffs:[],narrative:{sections:[]},narrative_status:'available',narrative_disclosure:''});
    $('investigation-override').hidden=true;
    document.querySelector('#investigation-view .model-heading .badge').textContent=sourceLabel+' · EVIDENCE REVIEW';
  }
  async function run(event){
    event.preventDefault();saveRule();invalidate();const token=version;
    try{
      if(!$('user-closed').checked||!$('user-forecast').checked)throw new Error('Confirm the closed month and Latest Approved Forecast before running this investigation.');
      const request=requestPayload();$('investigation-status').textContent='Running deterministic review on the local Python process…';
      const data=await send(request);if(token!==version)return;payload=request;show(data);
    }catch(error){if(token===version)$('investigation-status').textContent=error.message;}
  }
  async function decide(index,action,rationale){
    if(!view||!payload)return;
    const token=++version,request={...payload,snapshot_id:view.snapshot_id,decisions:{...view.decisions,[index]:{action,rationale}}};
    $('investigation-content').inert=true;
    try{const data=await send(request);if(token!==version)return;show(data);}
    catch(error){if(token===version){invalidate();$('investigation-status').textContent=error.message;}}
  }
  $('user-investigation-controls').onsubmit=run;
  for(const id of fields)$('user-'+id).addEventListener('input',invalidate);
  $('user-metric').onchange=metricChanged;
  return {
    select(next,entityId,month){
      saveRule();snapshot=next;entity=entityId;period=month;lastMetric='';resetControls();invalidate();
      const rows=(snapshot.datasets.performance??[]).filter(r=>r.entity_id===entity&&r.period===period);
      $('user-metric').replaceChildren(...rows.map(r=>{const option=document.createElement('option');option.value=r.metric_id;option.textContent=`${r.metric_name} · ${r.unit}`;return option;}));
      lastMetric=$('user-metric').value;const rule=rules.get(key(lastMetric));if(rule){$('user-absolute').value=rule[0];$('user-percentage').value=rule[1];$('user-always').checked=rule[2];}
      $('investigation-status').textContent='Confirm the closed month and Latest Approved Forecast, then run this variance. No automatic materiality rule is configured until you supply one.';
    },
    dispose(){invalidate();snapshot=null;rules.clear();},
  };
}
