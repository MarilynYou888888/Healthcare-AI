// Shared, explicit business vocabulary. No financial formulas live here.
const field = (label, aliases = [], type = 'text', required = true) => ({label, aliases, type, required});
export const FIELDS = Object.freeze({
  entity_id: field('Entity ID', ['clinic id','facility id']),
  entity_name: field('Entity name', ['clinic','clinic name','facility','facility name']),
  period: field('Period', ['month','calendar month'], 'month'),
  provider_fte: field('Provider FTE', ['fte','provider fte','fte count','provider count'], 'nonnegative'),
  operating_days: field('Operating Days', ['clinic days','operating days','work days'], 'days'),
  visits_per_provider_day: field('Visits / provider day', ['visits per provider day','visits per day'], 'nonnegative'),
  utilization_rate: field('Utilization', ['utilization','utilisation','utilization rate'], 'ratio'),
  net_revenue_per_visit: field('Net Revenue / Visit', ['rev per visit','rev / visit','revenue per visit','net revenue per encounter','net rev per visit'], 'nonnegative'),
  variable_labor_cost_per_visit: field('Variable labor / visit', ['labor per visit','variable labor per visit'], 'nonnegative'),
  variable_supply_cost_per_visit: field('Variable supply / visit', ['supplies per visit','supply per visit','variable supplies per visit'], 'nonnegative'),
  fixed_operating_expense: field('Fixed operating expense', ['fixed expense','fixed monthly expense'], 'nonnegative'),
  reimbursement_factor: field('Reimbursement factor', ['reimbursement multiplier'], 'positive'),
  market: field('Market', [], 'text', false), specialty: field('Specialty', [], 'text', false),
  business_unit: field('Business unit', [], 'text', false), scenario_name: field('Scenario name', ['scenario'], 'text', false),
  currency: field('Currency', ['currency code'], 'currency', false), source: field('Source', ['data source'], 'text', false), notes: field('Notes', [], 'text', false),
  metric_id: field('Metric ID', ['account id','metric code']), metric_name: field('Metric name', ['account name','metric']),
  actual_value: field('Actual value', ['actual','actuals'], 'number'), forecast_value: field('Forecast value', ['forecast','expected value'], 'number'),
  unit: field('Unit', ['units']), event_type: field('Event type', ['event']), start_date: field('Start date', ['start'], 'date'),
  end_date: field('End date', ['end'], 'date', false), description: field('Description', ['event description']),
  observed_value: field('Observed value', ['observed'], 'number', false), reported_at: field('Reported at', ['reported date'], 'timestamp', false),
  company: field('Company', ['company name']), business_segment: field('Business segment', ['segment']),
  value: field('Value', ['benchmark value'], 'number'), source_url: field('Source URL', ['url'], 'url', false),
});
export const ROLES = Object.freeze({
  planning: {label:'Planning Assumptions', fields:'entity_id entity_name period provider_fte operating_days visits_per_provider_day utilization_rate net_revenue_per_visit variable_labor_cost_per_visit variable_supply_cost_per_visit fixed_operating_expense reimbursement_factor market specialty business_unit scenario_name currency source notes'.split(' '), key:['entity_id','period','scenario_name']},
  performance: {label:'Actual vs Forecast', fields:'entity_id entity_name period metric_id metric_name actual_value forecast_value unit currency source'.split(' '), key:['entity_id','period','metric_id']},
  events: {label:'Operating Events', fields:'entity_id period event_type start_date end_date description observed_value unit source reported_at'.split(' '), key:['entity_id','period','event_type','start_date','end_date','description','observed_value','unit']},
  benchmark: {label:'Custom Benchmark', fields:'company period business_segment metric_id metric_name value unit source notes source_url'.split(' '), key:['company','period','business_segment','metric_id']},
});
export const LIMITS = Object.freeze({fileBytes:10*1024*1024, expandedBytes:100*1024*1024, rows:50000, columns:100, cells:500000, parseMs:15000});
const metric = (label, units, signed=false) => ({label, units:units.split(' '), signed});
export const METRICS = Object.freeze({
  REV_NET_PATIENT:metric('Net patient revenue','currency',true), VISITS:metric('Visits','visits'), PATIENT_VISITS:metric('Patient visits','visits'),
  PROVIDER_FTE:metric('Provider FTE','FTE'), LABOR_EXPENSE:metric('Labor expense','currency',true), EXP_CLINICAL_LABOR:metric('Clinical labor expense','currency',true),
  SUPPLY_EXPENSE:metric('Supply expense','currency',true), OPERATING_EXPENSE:metric('Operating expense','currency',true), OPERATING_INCOME:metric('Operating income','currency',true),
  NET_REVENUE_PER_VISIT:metric('Net revenue per visit','currency_per_visit'), PROVIDER_AVAILABLE_DAYS:metric('Provider available days','days'),
  CLINIC_CLOSURE_DAYS:metric('Clinic closure days','days'), OVERTIME_HOURS:metric('Overtime hours','hours'), COMMERCIAL_PAYER_MIX:metric('Commercial payer mix','ratio'),
});
export const normalizeName = value => String(value).toLowerCase().replace(/[_/\-]+/g,' ').replace(/\s+/g,' ').trim();
export function suggestMappings(headers, role) {
  const candidates = headers.map(header => ROLES[role].fields.filter(id => [id,FIELDS[id].label,...FIELDS[id].aliases].some(alias => normalizeName(alias) === normalizeName(header))));
  return candidates.map(matches => matches.length === 1 && candidates.filter(other => other.includes(matches[0])).length === 1 ? matches[0] : '');
}
export const ambiguousAlias = header => ['provider count','visits per day'].includes(normalizeName(header));
export const prohibitedHeader = header => /^(patient( name| id| identifier)?|mrn|medical record( number)?|dob|date of birth|ssn|social security( number)?|employee( name| id| identifier)?|claim( id| number)?|member( id| name)?)$/.test(normalizeName(header));
export function toScenarioAssumptions(row) {
  return {provider_fte:row.provider_fte, clinic_days:row.operating_days, visits_per_provider_day:row.visits_per_provider_day,
    utilization:row.utilization_rate, net_revenue_per_visit:row.net_revenue_per_visit, labor_per_visit:row.variable_labor_cost_per_visit,
    supplies_per_visit:row.variable_supply_cost_per_visit, fixed_expense:row.fixed_operating_expense, reimbursement_factor:row.reimbursement_factor};
}
