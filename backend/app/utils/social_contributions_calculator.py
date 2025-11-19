"""
Social Contributions Calculator - Страховые взносы 2024-2025

Implements social contributions calculation according to Russian law:
- ПФР (Pension Fund): 22% до 1,917,000 ₽, 10% сверху
- ФОМС (Medical Insurance): 5.1% до 1,917,000 ₽
- ФСС (Social Insurance): 2.9% до 1,032,000 ₽
"""
from decimal import Decimal
from typing import Dict
from datetime import datetime

from app.core import constants

# Social contribution limits for 2024-2025 (from constants)
PENSION_LIMIT_2024 = Decimal(str(constants.PENSION_FUND_LIMIT))
PENSION_LIMIT_2025 = Decimal(str(constants.PENSION_FUND_LIMIT))

MEDICAL_LIMIT_2024 = Decimal(str(constants.MEDICAL_INSURANCE_LIMIT))
MEDICAL_LIMIT_2025 = Decimal(str(constants.MEDICAL_INSURANCE_LIMIT))

SOCIAL_LIMIT_2024 = Decimal(str(constants.SOCIAL_INSURANCE_LIMIT))
SOCIAL_LIMIT_2025 = Decimal(str(constants.SOCIAL_INSURANCE_LIMIT))

# Rates (from constants)
PENSION_BASE_RATE = Decimal(str(constants.PENSION_FUND_BASE_RATE))
PENSION_OVER_RATE = Decimal(str(constants.PENSION_FUND_OVER_LIMIT_RATE))

MEDICAL_RATE = Decimal(str(constants.MEDICAL_INSURANCE_RATE))
SOCIAL_RATE = Decimal(str(constants.SOCIAL_INSURANCE_RATE))


def calculate_social_contributions(
    annual_income: Decimal,
    year: int = None
) -> Dict[str, any]:
    """
    Calculate social contributions (ПФР, ФОМС, ФСС) for given annual income.

    Args:
        annual_income: Total annual gross income
        year: Year for calculation (defaults to current year)

    Returns:
        Dictionary with:
        - pfr: Pension fund contribution details
        - foms: Medical insurance contribution details
        - fss: Social insurance contribution details
        - total_contributions: Total contributions amount
        - effective_rate: Effective contribution rate (as percentage)
    """
    if year is None:
        year = datetime.now().year

    annual_income = Decimal(str(annual_income))

    # Choose limits based on year
    pension_limit = PENSION_LIMIT_2025 if year >= 2025 else PENSION_LIMIT_2024
    medical_limit = MEDICAL_LIMIT_2025 if year >= 2025 else MEDICAL_LIMIT_2024
    social_limit = SOCIAL_LIMIT_2025 if year >= 2025 else SOCIAL_LIMIT_2024

    # Calculate ПФР (Pension Fund)
    if annual_income <= pension_limit:
        pfr_base = annual_income * PENSION_BASE_RATE
        pfr_over = Decimal('0')
    else:
        pfr_base = pension_limit * PENSION_BASE_RATE
        pfr_over = (annual_income - pension_limit) * PENSION_OVER_RATE

    pfr_total = pfr_base + pfr_over

    # Calculate ФОМС (Medical Insurance)
    foms_taxable = min(annual_income, medical_limit)
    foms_total = foms_taxable * MEDICAL_RATE

    # Calculate ФСС (Social Insurance)
    fss_taxable = min(annual_income, social_limit)
    fss_total = fss_taxable * SOCIAL_RATE

    # Total contributions
    total_contributions = pfr_total + foms_total + fss_total

    # Effective rate
    effective_rate = (total_contributions / annual_income * 100) if annual_income > 0 else Decimal('0')

    return {
        'pfr': {
            'base_rate': float(PENSION_BASE_RATE),
            'over_limit_rate': float(PENSION_OVER_RATE),
            'limit': float(pension_limit),
            'base_amount': float(pfr_base),
            'over_amount': float(pfr_over),
            'total': float(pfr_total),
        },
        'foms': {
            'rate': float(MEDICAL_RATE),
            'limit': float(medical_limit),
            'taxable_amount': float(foms_taxable),
            'total': float(foms_total),
        },
        'fss': {
            'rate': float(SOCIAL_RATE),
            'limit': float(social_limit),
            'taxable_amount': float(fss_taxable),
            'total': float(fss_total),
        },
        'total_contributions': float(total_contributions),
        'effective_rate': float(effective_rate),
    }


def calculate_total_tax_burden(
    annual_income: Decimal,
    year: int = None,
    ndfl_calculator = None
) -> Dict[str, any]:
    """
    Calculate total tax burden: NDFL + social contributions.

    Args:
        annual_income: Total annual gross income
        year: Year for calculation (defaults to current year)
        ndfl_calculator: NDFL calculator function (optional, will import if not provided)

    Returns:
        Dictionary with:
        - gross_income: Gross income
        - ndfl: NDFL calculation details
        - social_contributions: Social contributions details
        - total_taxes: Total taxes (NDFL + contributions)
        - net_income: Net income after NDFL
        - employer_cost: Total employer cost (gross + contributions)
        - effective_tax_rate: Effective NDFL rate
        - effective_burden_rate: Total burden rate (taxes/gross)
        - employee_burden_rate: Employee burden (NDFL/gross)
        - employer_burden_rate: Employer burden (contributions/gross)
    """
    if year is None:
        year = datetime.now().year

    # Import NDFL calculator if not provided
    if ndfl_calculator is None:
        from app.utils.ndfl_calculator import calculate_progressive_ndfl
        ndfl_calculator = calculate_progressive_ndfl

    annual_income = Decimal(str(annual_income))

    # Calculate NDFL (employee pays)
    ndfl_result = ndfl_calculator(annual_income, year)
    ndfl_total = Decimal(str(ndfl_result['total_tax']))

    # Calculate social contributions (employer pays)
    contributions_result = calculate_social_contributions(annual_income, year)
    contributions_total = Decimal(str(contributions_result['total_contributions']))

    # Net income (after NDFL)
    net_income = annual_income - ndfl_total

    # Total employer cost (gross + employer contributions)
    employer_cost = annual_income + contributions_total

    # Total taxes (NDFL + contributions)
    total_taxes = ndfl_total + contributions_total

    # Effective rates
    effective_tax_rate = float(ndfl_result['effective_rate'])  # NDFL rate
    employee_burden_rate = (ndfl_total / annual_income * 100) if annual_income > 0 else 0
    employer_burden_rate = (contributions_total / annual_income * 100) if annual_income > 0 else 0
    effective_burden_rate = (total_taxes / annual_income * 100) if annual_income > 0 else 0

    return {
        'gross_income': float(annual_income),
        'ndfl': {
            'total': float(ndfl_total),
            'effective_rate': effective_tax_rate,
            'breakdown': ndfl_result.get('breakdown', []),
        },
        'social_contributions': contributions_result,
        'net_income': float(net_income),
        'total_taxes': float(total_taxes),
        'employer_cost': float(employer_cost),
        'effective_tax_rate': effective_tax_rate,
        'employee_burden_rate': float(employee_burden_rate),
        'employer_burden_rate': float(employer_burden_rate),
        'effective_burden_rate': float(effective_burden_rate),
    }


def get_contribution_rates_info(year: int = None) -> Dict[str, any]:
    """
    Get information about social contribution rates and limits for a given year.

    Args:
        year: Tax year (defaults to current year)

    Returns:
        Dictionary with rate information
    """
    if year is None:
        year = datetime.now().year

    pension_limit = PENSION_LIMIT_2025 if year >= 2025 else PENSION_LIMIT_2024
    medical_limit = MEDICAL_LIMIT_2025 if year >= 2025 else MEDICAL_LIMIT_2024
    social_limit = SOCIAL_LIMIT_2025 if year >= 2025 else SOCIAL_LIMIT_2024

    return {
        'year': year,
        'pfr': {
            'name': 'ПФР (Пенсионный фонд)',
            'base_rate': float(PENSION_BASE_RATE),
            'over_limit_rate': float(PENSION_OVER_RATE),
            'limit': float(pension_limit),
            'description': f'22% до {pension_limit:,} ₽, 10% сверху',
        },
        'foms': {
            'name': 'ФОМС (Медицинское страхование)',
            'rate': float(MEDICAL_RATE),
            'limit': float(medical_limit),
            'description': f'5.1% до {medical_limit:,} ₽',
        },
        'fss': {
            'name': 'ФСС (Социальное страхование)',
            'rate': float(SOCIAL_RATE),
            'limit': float(social_limit),
            'description': f'2.9% до {social_limit:,} ₽',
        },
        'total_standard_rate': float(PENSION_BASE_RATE + MEDICAL_RATE + SOCIAL_RATE),
    }
