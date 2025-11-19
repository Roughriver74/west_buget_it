from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, Iterable, Optional, Union

from app.db.models import TaxRate, TaxTypeEnum


@dataclass(frozen=True)
class TaxRateDefault:
    """Lightweight representation of a tax rate used as fallback"""

    tax_type: TaxTypeEnum
    name: str
    rate: Decimal
    threshold_amount: Optional[Decimal] = None
    rate_above_threshold: Optional[Decimal] = None
    department_id: Optional[int] = None


DEFAULT_TAX_RATES: Dict[TaxTypeEnum, TaxRateDefault] = {
    TaxTypeEnum.INCOME_TAX: TaxRateDefault(
        tax_type=TaxTypeEnum.INCOME_TAX,
        name="НДФЛ (13%)",
        rate=Decimal("0.13"),
        threshold_amount=Decimal("5000000"),
        rate_above_threshold=Decimal("0.15"),
    ),
    TaxTypeEnum.PENSION_FUND: TaxRateDefault(
        tax_type=TaxTypeEnum.PENSION_FUND,
        name="ПФР (22%)",
        rate=Decimal("0.22"),
        threshold_amount=Decimal("1917000"),
        rate_above_threshold=Decimal("0.10"),
    ),
    TaxTypeEnum.MEDICAL_INSURANCE: TaxRateDefault(
        tax_type=TaxTypeEnum.MEDICAL_INSURANCE,
        name="ФОМС (5.1%)",
        rate=Decimal("0.051"),
    ),
    TaxTypeEnum.SOCIAL_INSURANCE: TaxRateDefault(
        tax_type=TaxTypeEnum.SOCIAL_INSURANCE,
        name="ФСС (2.9%)",
        rate=Decimal("0.029"),
    ),
    TaxTypeEnum.INJURY_INSURANCE: TaxRateDefault(
        tax_type=TaxTypeEnum.INJURY_INSURANCE,
        name="Страхование от несчастных случаев (0.2%)",
        rate=Decimal("0.002"),
    ),
}


def merge_tax_rates_with_defaults(
    tax_rates: Iterable[TaxRate],
) -> Dict[TaxTypeEnum, Union[TaxRate, TaxRateDefault]]:
    """
    Pick department-specific rates when available; otherwise fall back to global defaults.

    Returns dict keyed by TaxTypeEnum with either TaxRate ORM objects or TaxRateDefault.
    """
    selected: Dict[TaxTypeEnum, Union[TaxRate, TaxRateDefault]] = {}

    for tax_rate in tax_rates:
        key = tax_rate.tax_type
        existing = selected.get(key)

        if not existing:
            selected[key] = tax_rate
            continue

        existing_department = getattr(existing, "department_id", None)
        if existing_department is None and tax_rate.department_id is not None:
            selected[key] = tax_rate

    for tax_type, default_rate in DEFAULT_TAX_RATES.items():
        if tax_type not in selected:
            selected[tax_type] = default_rate

    return selected
