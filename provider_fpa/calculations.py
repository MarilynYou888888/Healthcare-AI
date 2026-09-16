"""Pure arithmetic. Ratios are fractions, never display percentages."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, localcontext


def decimal_value(value: Decimal | str | int | float | None) -> Decimal | None:
    if value is None or value == '':
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError('Invalid numeric value') from exc
    if not number.is_finite():
        raise ValueError('Numeric values must be finite')
    return number


@dataclass(frozen=True)
class Calculation:
    actual: Decimal | None
    forecast_or_expected: Decimal | None
    absolute: Decimal | None
    percentage: Decimal | None
    percentage_unavailable_reason: str | None


def calculate_variance(
    actual: Decimal | str | int | float | None,
    comparator: Decimal | str | int | float | None,
) -> Calculation:
    actual, comparator = decimal_value(actual), decimal_value(comparator)
    if actual is None or comparator is None:
        return Calculation(actual, comparator, None, None, 'missing_actual_or_comparator')
    with localcontext() as context:
        context.prec = 28
        absolute = actual - comparator
        percentage = absolute / comparator if comparator != 0 else None
    return Calculation(actual, comparator, absolute, percentage,
                       'zero_comparator' if comparator == 0 else None)
