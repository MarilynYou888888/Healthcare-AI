"""Web-facing investigation contract; no gold answers or scenario calculations.

System results remain immutable. Human review is evaluated on request and returned
for browser memory only; nothing is persisted by this module.
"""
import hashlib
import json
from pathlib import Path

from provider_fpa.engine import investigate, investigate_clinic_month
from provider_fpa.loading import load_datasets
from provider_fpa.models import DriverFamily as F, EpistemicState as S
from provider_fpa.narrative import NarrativeGuardrailError, generate_narrative
from provider_fpa.presentation import investigation_payload

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / 'data/synthetic_benchmark'
POLICY = ROOT / 'data/synthetic/investigation_policy.json'
IDENTITY_FIELDS = ('case_id', 'clinic_id', 'month', 'target_id', 'target_type')
HANDOFFS = {F.PROVIDER: ('provider_fte', 'Provider FTE'), F.CAPACITY: ('clinic_days', 'Clinic operating days')}


def investigation_catalog():
    # cases.json also contains evaluator metadata. Project only identities; the
    # engine selects the Review Queue from review_rules.csv, never fixture answers.
    return [{key: case[key] for key in IDENTITY_FIELDS}
            for case in json.loads((BENCHMARK / 'cases.json').read_text())]


def _load(case_id, target_id=None, target_type=None, analyst_override=False):
    case = next((c for c in investigation_catalog() if c['case_id'] == case_id), None)
    if case is None:
        raise ValueError('Unknown synthetic case')
    policy = json.loads(POLICY.read_text())
    fraction = policy['structural_horizon_fraction']
    data = load_datasets(BENCHMARK / 'inputs')
    targets = investigate_clinic_month(data, case['clinic_id'], case['month'], material_fraction=fraction)
    target_id, target_type = target_id or case['target_id'], target_type or case['target_type']
    if not any(r.variance.item_id == target_id and r.variance.variance_type == target_type for r in targets):
        raise ValueError('Target is not part of this Clinic-Month')
    result = investigate(data, case['clinic_id'], case['month'], target_id, target_type,
                         analyst_override=analyst_override, material_fraction=fraction)
    context = dict(case_id=case_id, target_id=target_id, target_type=target_type, analyst_override=analyst_override)
    return context, result, targets, policy


def _handoffs(result):
    return [dict(driver_index=index, driver_family=driver.driver_family.value,
                 state=driver.epistemic_state.value, assumption=HANDOFFS[driver.driver_family][0],
                 label=HANDOFFS[driver.driver_family][1])
            for index, driver in enumerate(result.drivers)
            if driver.driver_family in HANDOFFS and driver.epistemic_state in (S.SUPPORTED, S.CONFIRMED)]


def investigation_view(case_id, target_id=None, target_type=None, analyst_override=False):
    context, result, targets, policy = _load(case_id, target_id, target_type, analyst_override)
    system = investigation_payload(result)
    try:
        narrative, narrative_status = generate_narrative(result).to_dict(), 'available'
    except NarrativeGuardrailError:
        # Preserve recovered guards even for additional operational targets that
        # were outside the ten primary narrative fixtures. Never display rejected text.
        narrative, narrative_status = {'sections': []}, 'withheld'
    snapshot = hashlib.sha256(json.dumps([context, system, policy], sort_keys=True).encode()).hexdigest()
    return dict(context=context, snapshot_id=snapshot, data_kind='synthetic_clinic_investigation',
                system=system, policy=policy, handoffs=_handoffs(result),
                targets=[dict(id=r.variance.item_id, type=r.variance.variance_type,
                              required=r.review.required, reasons=list(r.review.reasons)) for r in targets],
                narrative=narrative, narrative_status=narrative_status,
                narrative_disclosure='Offline demo — guarded deterministic fallback narrative; no live LLM used. '
                                     'Describes the system assessment before human review.')


def review_investigation(context, snapshot_id, decisions):
    """Validate explicit human choices against a fresh immutable system snapshot.

    Choices replace that driver's previous session choice; they never rewrite
    input evidence. The caller retains them only in page memory. This is a local
    demo boundary, not an authenticated approval or a persistent audit log.
    """
    from dataclasses import replace
    from datetime import datetime, timezone
    from uuid import uuid4
    from provider_fpa.evidence import confirm_driver, transition_driver
    from provider_fpa.models import HumanDecision, SourceReference

    if not isinstance(context, dict) or set(context) != {'case_id', 'target_id', 'target_type', 'analyst_override'}:
        raise ValueError('Invalid investigation context')
    if type(context['analyst_override']) is not bool:
        raise ValueError('Analyst Override must be explicit')
    view = investigation_view(**context)
    if snapshot_id != view['snapshot_id']:
        raise ValueError('Investigation changed. Reload before reviewing.')
    _, result, _, _ = _load(**context)
    reviewed_result, receipts = apply_review_decisions(result, decisions)
    view.update(reviewed=investigation_payload(reviewed_result), decisions=receipts, handoffs=_handoffs(reviewed_result))
    return view


def apply_review_decisions(result, decisions):
    """Shared evidence transitions for immutable demo and uploaded results."""
    from dataclasses import replace
    from datetime import datetime, timezone
    from uuid import uuid4
    from provider_fpa.evidence import confirm_driver, transition_driver
    from provider_fpa.models import HumanDecision, SourceReference

    if not isinstance(decisions, dict) or len(decisions) > len(result.drivers):
        raise ValueError('Invalid session decisions')
    drivers = list(result.drivers)
    receipts = {}
    for key, choice in decisions.items():
        if key not in {str(i) for i in range(len(drivers))} or not isinstance(choice, dict):
            raise ValueError('Unknown driver or decision')
        driver = result.drivers[int(key)]
        action = choice.get('action')
        rationale = choice.get('rationale', '')
        if not isinstance(rationale, str) or len(rationale) > 2000:
            raise ValueError('Rationale must be text, at most 2000 characters')
        rationale = rationale.strip() or 'Analyst selected ' + str(action) + ' in the demo session.'
        record = HumanDecision(str(uuid4()), datetime.now(timezone.utc).isoformat(), rationale)
        if action == 'confirm':
            reviewed = confirm_driver(driver, record)
        elif action in ('reject', 'keep_unresolved'):
            state = S.REJECTED if action == 'reject' else S.UNRESOLVED
            if driver.epistemic_state == S.OBSERVED:
                raise ValueError('Observed upstream context is not a causal driver to adjudicate')
            evidence = (*driver.evidence, SourceReference('session_review', (('review_reference', record.review_reference),),
                                                         'Explicit analyst judgment; not new operating evidence', record.recorded_at))
            reviewed = driver if driver.epistemic_state == state else transition_driver(driver, state, evidence=evidence)
        elif action == 'request_investigation':
            reviewed = driver
        else:
            raise ValueError('Unknown human-review action')
        drivers[int(key)] = reviewed
        receipts[key] = dict(action=action, rationale=rationale)
    reviewed_result = replace(result, drivers=tuple(drivers), analyst_status='reviewed' if decisions else 'pending')
    return reviewed_result, receipts
