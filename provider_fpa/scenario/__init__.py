"""Load immutable synthetic assumptions. Financial arithmetic lives in web/scenario.js.

Keeping the loader free of model formulas prevents divergent server/browser engines.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

BASELINE = Path(__file__).resolve().parents[2] / 'data/synthetic/scenario/clinic_baseline.json'


@dataclass(frozen=True)
class Baseline:
    baseline_id: str
    clinic: str
    month: str
    data_kind: str
    rationale: str
    assumptions: Mapping[str, str]

    def payload(self):
        return dict(baseline_id=self.baseline_id, clinic=self.clinic, month=self.month,
                    data_kind=self.data_kind, rationale=self.rationale,
                    assumptions=dict(self.assumptions))


def load_baseline(path=BASELINE):
    row = json.loads(path.read_text())
    if row.get('data_kind') != 'synthetic':
        raise ValueError('Only synthetic planning data may enter the scenario model')
    row['assumptions'] = MappingProxyType(row['assumptions'])
    return Baseline(**row)
