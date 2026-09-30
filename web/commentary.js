import {formatValue} from './scenario.js';

export const COMMENTARY_DISCLOSURE = 'Rule-based commentary from calculated results and recorded evidence. No LLM or external API is used.';
const signedNegative = value => String(value).startsWith('-');
const money = (result, value, signed = false) => formatValue(value, result.currency || 'USD', signed);
const display = (result, value, field, signed = false) => formatValue(value, field === 'USD' ? (result.currency || 'USD') : field, signed);

function scenarioStatements(result) {
  const drivers = result.changed_drivers;
  if (!drivers.length) return [
    'The scenario matches the selected baseline and no planning assumptions have changed.',
    `Expected visits, modeled net patient revenue, and modeled operating income remain ${display(result, result.scenario.visits, 'visits')}, ${money(result, result.scenario.revenue)}, and ${money(result, result.scenario.operating_income)}.`,
    'There is no modeled offset or amplification to report because the draft matches baseline.',
    'The analyst can retain the baseline or change an assumption to evaluate a separate hypothetical scenario.',
  ];
  const driverText = drivers.map(driver => `${driver.name} changed from ${display(result, driver.baseline, driver.unit)} to ${display(result, driver.scenario, driver.unit)}`).join('; ');
  const visitChange = result.changes.visits;
  const volumeSentence = visitChange.amount === '0'
    ? 'Modeled visit volume is unchanged.'
    : `Expected visits ${signedNegative(visitChange.amount) ? 'decline' : 'increase'} by ${display(result, visitChange.amount, 'visits')} versus baseline.`;
  const expenseChange = result.changes.variable_expense.amount;
  const incomeChange = result.changes.operating_income.amount;
  const expenseRelationship = expenseChange === '0' ? '' : (signedNegative(expenseChange) === signedNegative(incomeChange) ? 'partially offsetting the operating income change' : 'amplifying the operating income change');
  const offset = expenseChange !== '0'
    ? `Variable labor and supply expense ${signedNegative(expenseChange) ? 'declines' : 'increases'} by ${money(result, expenseChange, true)}, ${expenseRelationship}.`
    : 'Variable labor and supply expense is unchanged.';
  const fixed = result.assumption_changes.fixed_expense.amount === '0'
    ? 'Fixed operating expense remains unchanged.'
    : `Fixed operating expense changes by ${money(result, result.assumption_changes.fixed_expense.amount, true)}.`;
  const margin = result.margin?.change_pp;
  const marginStatement = margin && margin !== '0'
    ? `Operating margin changes by ${display(result, margin, '', true)} percentage points.`
    : 'Operating margin is unchanged.';
  return [
    `${driverText}.`,
    `${volumeSentence.replace(/\.$/, '')}; modeled net patient revenue changes by ${money(result, result.changes.revenue.amount, true)} versus baseline.`,
    `Modeled operating income changes by ${money(result, result.changes.operating_income.amount, true)}; ${marginStatement.toLowerCase()}`,
    `${offset} ${fixed}`,
    'The analyst should assess whether the selected assumptions are appropriate for the next forecast review; no approved forecast has been changed.',
  ];
}

export function composeScenarioCommentary(result) {
  if (!result || result.validation?.status !== 'valid' || result.revision === undefined) return null;
  const sentences = scenarioStatements(result);
  return Object.freeze({mode:'deterministic-rule-based', disclosure:COMMENTARY_DISCLOSURE, revision:result.revision,
    baseline_id:result.baseline_id, summary:sentences.join(' '), sentences,
    source_label:`${result.data_kind === 'synthetic' ? 'Synthetic' : 'User uploaded'} ScenarioResult · Revision ${result.revision}`,
    boundary:'Commentary formats the current ScenarioResult. It does not calculate values, classify causes, or update a forecast.'});
}

export function composeInvestigationCommentary(system, reviewed = system) {
  if (!system || !system.variance) return null;
  const variance = system.variance;
  const amount = variance.currency ? `${variance.currency} ${variance.absolute}` : variance.absolute;
  const drivers = Array.isArray(reviewed?.drivers) ? reviewed.drivers : (system.drivers || []);
  const primary = drivers.find(driver => driver.role === 'primary');
  const contributing = drivers.find(driver => driver.role === 'contributing');
  const sentences = [`${variance.id} is ${amount} versus forecast; actual is ${variance.actual} compared with ${variance.forecast_or_expected}, with direction recorded as ${String(variance.direction || 'unclassified').replaceAll('_', ' ')}.`];
  if (primary?.epistemic_state === 'analyst_confirmed_cause') sentences.push(`${primary.driver_family} is the analyst-confirmed primary cause for this snapshot.`);
  else if (primary?.epistemic_state === 'supported_driver') sentences.push(`${primary.driver_family} is supported as the primary driver by recorded evidence, but remains subject to analyst confirmation.`);
  else if (contributing?.epistemic_state === 'analyst_confirmed_cause') sentences.push(`${contributing.driver_family} is an analyst-confirmed contributing driver; the primary cause remains unresolved.`);
  else sentences.push('The available operating evidence does not establish a supported primary cause, so the case remains Unresolved.');
  const timing=reviewed.timing_classification || reviewed.timing?.classification || system.timing_classification || system.timing?.classification;
  if (timing === 'temporary') sentences.push('Recorded timing classifies the issue as temporary; recovery timing should be reviewed before changing the approved forecast.');
  else if (timing === 'structural') sentences.push('Recorded timing classifies the issue as structural; the next forecast review should consider the persistence evidence.');
  else if (timing === 'unresolved') sentences.push('Timing remains Unresolved because the result does not contain sufficient structured persistence evidence.');
  sentences.push('Additional operational context is required before changing an approved forecast; no forecast update has been made.');
  return Object.freeze({mode:'deterministic-rule-based', disclosure:COMMENTARY_DISCLOSURE,
    snapshot_id:system.snapshot_id, summary:sentences.join(' '), sentences,
    source_label:'InvestigationResult · recorded evidence and review state',
    boundary:'Commentary formats the current InvestigationResult. It does not infer causes, calculate variances, or approve a forecast.'});
}
