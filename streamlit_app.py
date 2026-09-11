"""Single-page Streamlit portfolio demo for the Provider FP&A Copilot."""

from __future__ import annotations

from decimal import Decimal
import html
from pathlib import Path
from typing import Any

from provider_fpa.engine import investigate
from provider_fpa.loading import load_datasets
from provider_fpa.narrative import NarrativeOutput, generate_narrative


APP_ROOT = Path(__file__).resolve().parent
BENCHMARK_ROOT = APP_ROOT / 'data' / 'synthetic_benchmark'
CASE_OPTIONS: dict[str, dict[str, str]] = {
    'C01': {
        'label': 'C01 — Provider PTO', 'clinic_id': 'CL001', 'month': '2026-03',
        'target_id': 'REV_NET_PATIENT',
        'description': 'A temporary provider absence reduces availability, visits, and revenue.',
    },
    'C03': {
        'label': 'C03 — Weather / Clinic Closure', 'clinic_id': 'CL003', 'month': '2026-05',
        'target_id': 'REV_NET_PATIENT',
        'description': 'A documented weather disruption closes the Clinic and lowers visit capacity.',
    },
    'C04': {
        'label': 'C04 — Unresolved Volume Miss', 'clinic_id': 'CL004', 'month': '2026-06',
        'target_id': 'REV_NET_PATIENT',
        'description': 'Visits miss plan, but the available operating evidence does not establish why.',
    },
}


def load_case_result(case_id: str, benchmark_root: Path = BENCHMARK_ROOT):
    """Load one public scenario and delegate all analysis to Phase 3/4."""
    try:
        case = CASE_OPTIONS[case_id]
    except KeyError as exc:
        raise ValueError(f'Unsupported demo case: {case_id}') from exc
    datasets = load_datasets(benchmark_root / 'inputs')
    return investigate(datasets, case['clinic_id'], case['month'], case['target_id'])


def _variance(result, item_id: str):
    return next((item for item in result.observed_variances if item.item_id == item_id), None)


def _number(value: Any) -> str:
    if value is None:
        return '—'
    if isinstance(value, Decimal):
        return format(value, ',.2f').rstrip('0').rstrip('.')
    return f'{value:,}' if isinstance(value, int) else str(value)


def _amount(value: Any, currency: str | None = 'USD') -> str:
    if value is None:
        return '—'
    prefix = '$' if currency == 'USD' else ''
    return prefix + _number(value)


def _percent(variance) -> str:
    if variance is None or variance.calculation.percentage is None:
        return '—'
    return f'{variance.calculation.percentage * 100:.1f}%'


def _event_facts(result) -> list[dict[str, Any]]:
    return [dict(fact.values) | {'subject_id': fact.subject_id}
            for fact in result.observed_facts if fact.fact_type == 'reported_event']


def build_evidence_text(result) -> str:
    """Build an evidence chain from facts and driver evidence already in the result."""
    events = _event_facts(result)
    lines: list[str] = []
    for event in events:
        if event.get('event_type') != 'forecast_horizon':
            lines.append(f"{event.get('description', event.get('event_type', 'Reported event'))}")
    target = result.variance
    if target.calculation.absolute is not None:
        lines.append(f"{target.item_id} actual {_number(target.calculation.actual)} vs comparator {_number(target.calculation.forecast_or_expected)}")
    visits = _variance(result, 'PATIENT_VISITS')
    if visits:
        lines.append(f"Patient visits actual {_number(visits.calculation.actual)} vs expected {_number(visits.calculation.forecast_or_expected)}")
    availability = _variance(result, 'PROVIDER_AVAILABLE_DAYS')
    if availability and availability.calculation.absolute:
        lines.append(f"Provider availability actual {_number(availability.calculation.actual)} vs expected {_number(availability.calculation.forecast_or_expected)}")
    closure = _variance(result, 'CLINIC_CLOSURE_DAYS')
    if closure and closure.calculation.absolute:
        lines.append(f"Clinic closure days actual {_number(closure.calculation.actual)} vs expected {_number(closure.calculation.forecast_or_expected)}")
    if result.primary_driver is None:
        lines.append('Insufficient evidence to establish the operating cause.')
    elif visits and target.calculation.absolute is not None and target.calculation.absolute < 0:
        lines.append('Supported relationship: lower visits reduce revenue; contribution percentages are not estimated.')
    return '\n↓\n'.join(lines) if lines else 'No traceable evidence is available for this investigation.'


def build_demo_model(result) -> dict[str, Any]:
    narrative = generate_narrative(result)
    revenue = result.variance
    visits = _variance(result, 'PATIENT_VISITS')
    return {
        'clinic_id': result.clinic_id,
        'month': result.month,
        'actual_revenue': revenue.calculation.actual,
        'forecast_revenue': revenue.calculation.forecast_or_expected,
        'revenue_variance_percent': _percent(revenue),
        'visit_variance_percent': _percent(visits),
        'primary_driver': result.primary_driver.value if result.primary_driver else None,
        'contributing_drivers': [driver.value for driver in result.contributing_drivers],
        'upstream_context': [driver.value for driver in result.upstream_context],
        'timing': result.timing.classification.title(),
        'unresolved': result.primary_driver is None or result.timing.classification == 'unresolved',
        'review_required': result.human_review_required,
        'evidence_text': build_evidence_text(result),
        'narrative': narrative.to_dict(),
        'narrative_text': narrative.as_text(),
    }


def _badge(label: str, tone: str = 'blue') -> str:
    return f'<span class="badge {tone}">{html.escape(label.upper())}</span>'


def _card(label: str, value: str, detail: str = '') -> str:
    return f'<div class="kpi"><div class="kpi-label">{html.escape(label)}</div><div class="kpi-value">{html.escape(value)}</div><div class="kpi-detail">{html.escape(detail)}</div></div>'


def render_app(st: Any, benchmark_root: Path = BENCHMARK_ROOT) -> None:
    """Render the page against a Streamlit-compatible module."""
    st.set_page_config(page_title='Provider FP&A Variance Copilot', page_icon='▦', layout='wide', initial_sidebar_state='expanded')
    st.markdown('''
    <style>
    .stApp { background: #f7f9fc; color: #17243b; }
    .block-container { max-width: 1220px; padding: 2.2rem 2.4rem 4rem; }
    h1 { color: #102a43; letter-spacing: -.03em; margin-bottom: .25rem; }
    h2, h3 { color: #183b56; letter-spacing: -.015em; }
    .subtitle { color: #5c7084; font-size: 1.05rem; margin-bottom: 1.6rem; }
    .section-kicker { color: #2f6f9f; text-transform: uppercase; letter-spacing: .12em; font-size: .72rem; font-weight: 700; margin-top: 1.8rem; }
    .scenario-card, .kpi, .panel, .review-panel { background: white; border: 1px solid #dce5ee; border-radius: 12px; box-shadow: 0 2px 8px rgba(24,59,86,.04); }
    .scenario-card { padding: 1rem 1.1rem; min-height: 105px; }
    .scenario-label, .kpi-label { color: #6d8092; font-size: .72rem; text-transform: uppercase; letter-spacing: .08em; font-weight: 700; }
    .scenario-value { color: #183b56; font-weight: 700; font-size: 1.05rem; margin-top: .35rem; }
    .scenario-description { color: #5c7084; font-size: .9rem; line-height: 1.45; }
    .kpi { padding: 1rem 1.05rem; min-height: 115px; }
    .kpi-value { color: #102a43; font-size: 1.45rem; font-weight: 750; margin: .45rem 0 .2rem; }
    .kpi-detail { color: #78909c; font-size: .78rem; }
    .badge { display: inline-block; border-radius: 999px; padding: .3rem .62rem; margin: .2rem .25rem .2rem 0; font-size: .68rem; font-weight: 800; letter-spacing: .08em; }
    .badge.blue { color: #145374; background: #e5f2f8; }
    .badge.green { color: #176044; background: #e3f4ec; }
    .badge.amber { color: #815b16; background: #fff4d6; }
    .badge.red { color: #8d3535; background: #fdeaea; }
    .panel { padding: 1.1rem 1.2rem; min-height: 150px; }
    .panel-title { color: #557086; font-size: .72rem; text-transform: uppercase; letter-spacing: .1em; font-weight: 800; margin-bottom: .6rem; }
    .chain { background: #f1f6fa; border-left: 3px solid #4f90b5; padding: 1rem 1.15rem; border-radius: 0 8px 8px 0; color: #264a63; white-space: pre-wrap; line-height: 1.55; }
    .review-panel { background: #eef6fb; border-color: #bcd7e6; padding: 1.15rem 1.25rem; }
    .review-title { color: #124e70; font-weight: 800; font-size: 1.05rem; }
    .muted { color: #61788b; }
    </style>
    ''', unsafe_allow_html=True)

    st.title('Provider FP&A Variance Copilot')
    st.markdown('<div class="subtitle">Evidence-aware clinic-month variance investigation for healthcare FP&A teams.</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('### Demo scenario')
        selected = st.selectbox('Choose a Clinic-Month case', list(CASE_OPTIONS), format_func=lambda key: CASE_OPTIONS[key]['label'])
        st.caption('Synthetic benchmark data only · deterministic fallback enabled')
        st.markdown('**Workflow**')
        st.markdown('Clinic-month performance  →  deterministic variance analysis  →  evidence-backed investigation  →  FP&A commentary  →  human review')

    result = load_case_result(selected, benchmark_root)
    case = CASE_OPTIONS[selected]
    model = build_demo_model(result)

    st.markdown('<div class="section-kicker">Section 1 · Scenario</div>', unsafe_allow_html=True)
    st.subheader(case['label'])
    scenario_columns = st.columns(4)
    for column, label, value in zip(scenario_columns, ('Clinic', 'Month', 'Target', 'Scenario'),
                                    (result.clinic_id, result.month, case['target_id'], case['description'])):
        with column:
            st.markdown(_card(label, value, ''), unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Section 2 · Performance Snapshot</div>', unsafe_allow_html=True)
    visits = _variance(result, 'PATIENT_VISITS')
    kpis = st.columns(5)
    values = (
        _amount(model['actual_revenue']), _amount(model['forecast_revenue']),
        model['revenue_variance_percent'], model['visit_variance_percent'],
        'Yes',
    )
    details = ('Closed Month actual', 'Latest Approved Forecast', 'Actual vs forecast', 'Actual vs expected', 'Configured rule / analyst review')
    labels = ('Actual Revenue', 'Forecast Revenue', 'Revenue Variance %', 'Visit Variance %', 'Review Required')
    for column, label, value, detail in zip(kpis, labels, values, details):
        with column:
            st.markdown(_card(label, value, detail), unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Section 3 · Investigation</div>', unsafe_allow_html=True)
    investigation_columns = st.columns(3)
    with investigation_columns[0]:
        st.markdown('<div class="panel"><div class="panel-title">Driver assessment</div>', unsafe_allow_html=True)
        st.markdown(_badge('SUPPORTED' if model['primary_driver'] else 'UNRESOLVED', 'green' if model['primary_driver'] else 'amber'), unsafe_allow_html=True)
        st.markdown(f'<div><strong>Primary:</strong> {html.escape(model["primary_driver"] or "No primary driver")}</div>', unsafe_allow_html=True)
        st.markdown(f'<div><strong>Contributing:</strong> {html.escape(", ".join(model["contributing_drivers"]) or "None")}</div></div>', unsafe_allow_html=True)
    with investigation_columns[1]:
        st.markdown('<div class="panel"><div class="panel-title">Timing classification</div>', unsafe_allow_html=True)
        st.markdown(_badge(model['timing'], 'amber' if model['timing'] == 'Unresolved' else 'blue'), unsafe_allow_html=True)
        st.markdown(f'<div class="muted">Remaining Latest Approved Forecast horizon.</div></div>', unsafe_allow_html=True)
    with investigation_columns[2]:
        st.markdown('<div class="panel"><div class="panel-title">Epistemic state</div>', unsafe_allow_html=True)
        st.markdown(_badge('HUMAN REVIEW REQUIRED', 'amber'), unsafe_allow_html=True)
        st.markdown('<div class="muted">Supported findings remain analyst-reviewable; no cause is autonomously confirmed.</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Section 4 · Evidence</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="panel-title">Traceable evidence chain</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="chain">{html.escape(model["evidence_text"])}</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-kicker">Section 5 · AI FP&A Commentary</div>', unsafe_allow_html=True)
    narrative: NarrativeOutput = generate_narrative(result)
    for section in narrative.sections[:-1]:
        with st.expander(section.title, expanded=section.title == 'Executive Summary'):
            st.write(section.body)

    st.markdown('<div class="section-kicker">Section 6 · Human Review</div>', unsafe_allow_html=True)
    st.markdown('<div class="review-panel"><div class="review-title">Human Review Required</div><p>The system does not autonomously confirm root cause or change forecast assumptions.</p><p><strong>Status:</strong> Pending · <strong>Allowed actions:</strong> confirm, reject, or request more evidence.</p></div>', unsafe_allow_html=True)
    if result.unresolved_questions:
        st.markdown('**Questions for Operations**')
        for question in narrative.sections[4].body.split('; '):
            st.markdown(f'- {question.rstrip(".")}')


def main() -> None:
    try:
        import streamlit as st
    except ImportError as exc:
        raise SystemExit('Streamlit is required. Install dependencies with: python3 -m pip install -r requirements.txt') from exc
    render_app(st)


if __name__ == '__main__':
    main()
