"""Synthetic monthly operating model. No public-company operands or narrative logic."""
import calendar
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

BASELINE = Path(__file__).resolve().parents[2] / 'data/synthetic/scenario/clinic_baseline.json'
ASSUMPTIONS = {
    'provider_fte': ('Provider FTE', 'FTE'),
    'clinic_days': ('Clinic operating days', 'days'),
    'visits_per_provider_day': ('Visits / provider day', 'slots'),
    'utilization': ('Utilization', 'ratio'),
    'net_revenue_per_visit': ('Net revenue / visit', 'USD'),
    'labor_per_visit': ('Variable labor / visit', 'USD'),
    'supplies_per_visit': ('Variable supplies / visit', 'USD'),
    'fixed_expense': ('Fixed monthly expense', 'USD'),
    'reimbursement_factor': ('Reimbursement factor', 'multiplier'),
}
FORMULAS = {
    'capacity': 'Provider FTE × clinic days × slots per provider day',
    'visits': 'Available capacity × utilization',
    'revenue': 'Expected visits × net revenue per visit × reimbursement factor',
    'labor': 'Expected visits × variable labor per visit',
    'supplies': 'Expected visits × variable supplies per visit',
    'variable_expense': 'Variable labor + variable supplies',
    'contribution': 'Net patient revenue − total variable expense',
    'operating_income': 'Contribution margin − fixed monthly expense',
}


def calculate(assumptions: Mapping[str, str | Decimal], month: str) -> Mapping[str, Decimal]:
    if set(assumptions) != set(ASSUMPTIONS):
        raise ValueError('Expected exactly nine synthetic assumptions')
    if not re.fullmatch(r'\d{4}-\d{2}',month):
        raise ValueError('Month must use YYYY-MM')
    try:
        year, mon = map(int,month.split('-'))
        if year < 1:
            raise ValueError('Invalid year')
        days = calendar.monthrange(year,mon)[1]
        values = {k:Decimal(str(v)) for k,v in assumptions.items()}
    except (ValueError,InvalidOperation) as exc:
        raise ValueError('Invalid month or numeric assumption') from exc
    if any(not v.is_finite() or v < 0 for v in values.values()):
        raise ValueError('Assumptions must be finite and nonnegative')
    if values['utilization'] > 1:
        raise ValueError('Utilization must be between 0 and 1')
    if values['clinic_days'] != values['clinic_days'].to_integral_value() or values['clinic_days'] > days:
        raise ValueError('Clinic days must be a whole number within the month')
    with localcontext() as ctx:
        ctx.prec = 28
        capacity = values['provider_fte'] * values['clinic_days'] * values['visits_per_provider_day']
        visits = capacity * values['utilization']
        revenue = visits * values['net_revenue_per_visit'] * values['reimbursement_factor']
        labor = visits * values['labor_per_visit']
        supplies = visits * values['supplies_per_visit']
        variable = labor + supplies
        contribution = revenue-variable
        income = contribution-values['fixed_expense']
    return MappingProxyType(dict(capacity=capacity,visits=visits,revenue=revenue,labor=labor,
        supplies=supplies,variable_expense=variable,contribution=contribution,operating_income=income))


@dataclass(frozen=True)
class Baseline:
    baseline_id: str
    clinic: str
    month: str
    data_kind: str
    rationale: str
    assumptions: Mapping[str, str]

    def payload(self):
        outputs=calculate(self.assumptions,self.month)
        return dict(baseline_id=self.baseline_id,clinic=self.clinic,month=self.month,
            data_kind=self.data_kind,rationale=self.rationale,
            assumptions=[dict(id=k,name=ASSUMPTIONS[k][0],unit=ASSUMPTIONS[k][1],value=v) for k,v in self.assumptions.items()],
            outputs={k:str(v) for k,v in outputs.items()},formulas=FORMULAS.copy())


def load_baseline(path=BASELINE):
    row=json.loads(path.read_text())
    if row.get('data_kind')!='synthetic':
        raise ValueError('Only synthetic planning data may enter the scenario model')
    calculate(row['assumptions'],row['month'])
    row['assumptions']=MappingProxyType(row['assumptions'])
    return Baseline(**row)
