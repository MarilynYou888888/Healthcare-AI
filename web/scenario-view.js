import {ASSUMPTIONS, GRAPH, createScenarioStore, formula, formatValue, formatPercent, inputValue, modelInput} from './scenario.js';
const $ = id => document.getElementById(id);
function node(tag, text, cls) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

// This module presents snapshots. It contains no financial calculations.
// Later Executive Summary and commentary consumers subscribe to this same store.
export let scenarioStore = null;
export function mountScenarioModel(baseline, store = createScenarioStore(baseline)) {
  scenarioStore = store;
  const currency=baseline.currency ?? 'USD';
  const unitFor=unit=>unit === 'USD' ? currency : unit;
  $('month').textContent = new Date(baseline.month+'-01T12:00:00').toLocaleDateString('en-US',{month:'long',year:'numeric'});
  const inputs = new Map();
  $('assumptions').replaceChildren();
  for (const [id, meta] of Object.entries(ASSUMPTIONS)) {
    const row = node('tr'); row.dataset.driver = id;
    const label = node('label', meta.name); label.htmlFor = 'input-'+id;
    const title = node('td'); title.append(label, node('small', meta.unit === 'ratio' ? '%' : unitFor(meta.unit)));
    const base = node('td', formatValue(baseline.assumptions[id], unitFor(meta.unit)), 'baseline-value');
    const cell = node('td');
    const input = node('input'); input.id = 'input-'+id; input.type = 'text'; input.inputMode = 'decimal';
    input.autocomplete = 'off'; input.spellcheck = false;
    input.setAttribute('aria-label', meta.name+' scenario');
    input.setAttribute('aria-describedby', 'error-'+id);
    input.value = inputValue(baseline.assumptions[id], meta.unit);
    const error = node('small', '', 'input-error'); error.id = 'error-'+id;
    input.addEventListener('input', () => store.edit(id, modelInput(input.value, meta.unit)));
    input.addEventListener('keydown', event => { if (event.key === 'Enter') input.blur(); });
    cell.append(input,error); row.append(title,base,cell); $('assumptions').append(row);
    inputs.set(id,{input,error,row});
  }
  const rows = new Map();
  $('financial-rows').replaceChildren();
  for (const metric of GRAPH) {
    if (metric.id === 'operating_income') addRow({id:'fixed_expense',name:'Fixed monthly expense',unit:'USD'}, 'Fixed assumption; excluded from contribution margin');
    addRow(metric,formula(metric));
  }
  function addRow(metric, explanation) {
    const row = node('tr'); row.dataset.output = metric.id;
    if (['variable_expense','contribution','operating_income'].includes(metric.id)) row.className = 'subtotal';
    const title = node('td'); title.append(node('strong',metric.name),node('small',explanation));
    const cells = ['baseline-value','scenario-value','delta-value','percent-value'].map(cls => node('td','—',cls));
    row.append(title,...cells); $('financial-rows').append(row); rows.set(metric.id,{row,cells,unit:unitFor(metric.unit)});
  }
  $('reset-scenario').onclick = () => store.reset();
  return store.subscribe(state => {
    const result = state.result ?? state.last_valid;
    const stale = state.status !== 'valid';
    $('scenario-comparison').classList.toggle('stale',stale);
    $('scenario-comparison').dataset.revision = String(result.revision);
    $('scenario-status').textContent = stale
      ? `Stale — last valid revision ${result.revision}. Correct the highlighted input; this draft is not eligible for review.`
      : `Current · Revision ${result.revision} · Deterministic calculations`;
    if (state.errors.model) $('scenario-status').textContent += ' '+state.errors.model;
    const changed = new Set(result.changed_drivers.map(d => d.id));
    for (const [id,{input,error,row}] of inputs) {
      const unit = ASSUMPTIONS[id].unit;
      // Preserve the active edit/caret; synchronize when another consumer changes state.
      if (modelInput(input.value, unit) !== state.draft[id]) {
        try { input.value = inputValue(state.draft[id], unit); }
        catch { input.value = state.draft[id]; }
      }
      input.setAttribute('aria-invalid',String(Boolean(state.errors[id])));
      error.textContent = state.errors[id] ?? '';
      row.classList.toggle('changed',!stale && changed.has(id));
    }
    $('changed-drivers').textContent = result.changed_drivers.length
      ? (stale ? 'Last valid changes: ' : 'Changed: ') + result.changed_drivers.map(d => `${d.name} ${formatValue(d.baseline,d.unit)} → ${formatValue(d.scenario,d.unit)}`).join(' · ')
      : (stale ? 'Last valid result matches baseline.' : 'Scenario matches baseline. Edit any assumption to explore its impact.');
    for (const [id,{row,cells,unit}] of rows) {
      const fixed = id === 'fixed_expense';
      const base = fixed ? result.baseline_assumptions[id] : result.baseline[id];
      const scenario = fixed ? result.assumptions[id] : result.scenario[id];
      const delta = fixed ? result.assumption_changes[id] : result.changes[id];
      cells[0].textContent = formatValue(base,unit);
      cells[1].textContent = formatValue(scenario,unit);
      cells[2].textContent = formatValue(delta.amount,unit,true);
      cells[3].textContent = delta.percent === null ? 'N/A' : formatPercent(delta.percent);
      cells[3].title = delta.percent_reason ?? 'Change / positive baseline';
      cells[3].setAttribute('aria-label', delta.percent === null ? 'N/A: '+delta.percent_reason : cells[3].textContent);
      row.classList.toggle('output-changed',delta.amount !== '0');
    }
    $('scenario-impact').textContent = formatValue(result.impact,currency,true);
  });
}
