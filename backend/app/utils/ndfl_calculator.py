"""
НДФЛ Calculator - Progressive tax calculation for 2024 and 2025+

Implements progressive income tax calculation according to Russian tax law:
- 2024: Two-tier system (13% / 15%)
- 2025+: Five-tier progressive system (13% / 15% / 18% / 20% / 22%)
"""
from decimal import Decimal
from typing import Dict, List, Tuple
from datetime import datetime


# Tax brackets for 2025+ (progressive 5-tier system)
TAX_BRACKETS_2025 = [
    (Decimal('2400000'), Decimal('0.13')),    # До 2,4 млн - 13%
    (Decimal('5000000'), Decimal('0.15')),    # 2,4-5 млн - 15%
    (Decimal('20000000'), Decimal('0.18')),   # 5-20 млн - 18%
    (Decimal('50000000'), Decimal('0.20')),   # 20-50 млн - 20%
    (None, Decimal('0.22')),                   # Свыше 50 млн - 22%
]

# Tax brackets for 2024 (two-tier system)
TAX_BRACKETS_2024 = [
    (Decimal('5000000'), Decimal('0.13')),    # До 5 млн - 13%
    (None, Decimal('0.15')),                   # Свыше 5 млн - 15%
]


def calculate_progressive_ndfl(
    annual_income: Decimal,
    year: int = None
) -> Dict[str, any]:
    """
    Calculate progressive NDFL (income tax) for given annual income.

    Args:
        annual_income: Total annual income (gross)
        year: Tax year (defaults to current year)

    Returns:
        Dictionary with:
        - total_tax: Total NDFL amount
        - effective_rate: Effective tax rate (as percentage)
        - breakdown: List of tax amounts per bracket
        - details: Detailed calculation per bracket
    """
    if year is None:
        year = datetime.now().year

    # Choose tax brackets based on year
    brackets = TAX_BRACKETS_2025 if year >= 2025 else TAX_BRACKETS_2024

    annual_income = Decimal(str(annual_income))
    total_tax = Decimal('0')
    breakdown = []
    details = []

    previous_threshold = Decimal('0')

    for threshold, rate in brackets:
        if threshold is None:
            # Last bracket (no upper limit)
            taxable_in_bracket = annual_income - previous_threshold
        else:
            # Check if income reaches this bracket
            if annual_income <= previous_threshold:
                break
            # Calculate taxable amount in this bracket
            taxable_in_bracket = min(annual_income, threshold) - previous_threshold

        if taxable_in_bracket > 0:
            tax_in_bracket = taxable_in_bracket * rate
            total_tax += tax_in_bracket

            breakdown.append({
                'from': float(previous_threshold),
                'to': float(threshold) if threshold else None,
                'rate': float(rate),
                'taxable_amount': float(taxable_in_bracket),
                'tax_amount': float(tax_in_bracket)
            })

            threshold_str = f"{threshold:,.0f}" if threshold else "∞"
            details.append(
                f"{previous_threshold:,.0f} - "
                f"{threshold_str} ₽: "
                f"{taxable_in_bracket:,.0f} ₽ × {rate * 100:.0f}% = "
                f"{tax_in_bracket:,.2f} ₽"
            )

            if threshold:
                previous_threshold = threshold

        # If we've calculated tax for the last bracket, stop
        if threshold is None or annual_income <= threshold:
            break

    # Calculate effective rate
    effective_rate = (total_tax / annual_income * 100) if annual_income > 0 else Decimal('0')

    return {
        'total_tax': float(total_tax),
        'effective_rate': float(effective_rate),
        'net_income': float(annual_income - total_tax),
        'breakdown': breakdown,
        'details': details,
        'year': year,
        'system': '5-tier' if year >= 2025 else '2-tier'
    }


def calculate_monthly_ndfl_withholding(
    current_month_income: Decimal,
    ytd_income_before_month: Decimal,
    ytd_tax_withheld: Decimal,
    year: int = None
) -> Dict[str, any]:
    """
    Calculate NDFL to withhold for current month based on year-to-date income.

    This implements the correct progressive tax calculation where:
    1. Calculate total tax on YTD income (including current month)
    2. Subtract tax already withheld in previous months
    3. Result is the tax to withhold this month

    Args:
        current_month_income: Gross income for current month
        ytd_income_before_month: Year-to-date income BEFORE current month
        ytd_tax_withheld: Tax already withheld in previous months
        year: Tax year

    Returns:
        Dictionary with:
        - tax_to_withhold: NDFL to withhold this month
        - ytd_income_total: Total YTD income after current month
        - ytd_tax_total: Total YTD tax after current month
        - monthly_effective_rate: Effective rate for this month
        - calculation_details: Explanation of calculation
    """
    current_month_income = Decimal(str(current_month_income))
    ytd_income_before_month = Decimal(str(ytd_income_before_month))
    ytd_tax_withheld = Decimal(str(ytd_tax_withheld))

    # Calculate total YTD income after current month
    ytd_income_total = ytd_income_before_month + current_month_income

    # Calculate total tax on YTD income
    tax_calc = calculate_progressive_ndfl(ytd_income_total, year)
    ytd_tax_total = Decimal(str(tax_calc['total_tax']))

    # Tax to withhold this month = Total YTD tax - Tax already withheld
    tax_to_withhold = ytd_tax_total - ytd_tax_withheld

    # Ensure non-negative (edge case protection)
    tax_to_withhold = max(tax_to_withhold, Decimal('0'))

    # Calculate monthly effective rate
    monthly_effective_rate = (tax_to_withhold / current_month_income * 100) if current_month_income > 0 else Decimal('0')

    return {
        'tax_to_withhold': float(tax_to_withhold),
        'ytd_income_total': float(ytd_income_total),
        'ytd_tax_total': float(ytd_tax_total),
        'monthly_effective_rate': float(monthly_effective_rate),
        'net_income_this_month': float(current_month_income - tax_to_withhold),
        'calculation_details': {
            'step1_ytd_income': float(ytd_income_total),
            'step2_total_tax_on_ytd': float(ytd_tax_total),
            'step3_tax_already_withheld': float(ytd_tax_withheld),
            'step4_tax_to_withhold': float(tax_to_withhold)
        },
        'breakdown': tax_calc['breakdown'],
        'year': tax_calc['year'],
        'system': tax_calc['system']
    }


def get_tax_brackets_info(year: int = None) -> Dict[str, any]:
    """
    Get information about tax brackets for a given year.

    Args:
        year: Tax year (defaults to current year)

    Returns:
        Dictionary with tax bracket information
    """
    if year is None:
        year = datetime.now().year

    brackets = TAX_BRACKETS_2025 if year >= 2025 else TAX_BRACKETS_2024

    brackets_info = []
    previous_threshold = Decimal('0')

    for threshold, rate in brackets:
        brackets_info.append({
            'from': float(previous_threshold),
            'to': float(threshold) if threshold else None,
            'rate': float(rate),
            'rate_percent': f"{rate * 100:.0f}%",
            'description': (
                f"{'От ' + f'{previous_threshold:,.0f}' if previous_threshold > 0 else 'До'} "
                f"{'до ' + f'{threshold:,.0f}' if threshold else 'свыше ' + f'{previous_threshold:,.0f}'} ₽ - "
                f"{rate * 100:.0f}%"
            )
        })

        if threshold:
            previous_threshold = threshold

    return {
        'year': year,
        'system': '5-tier progressive' if year >= 2025 else '2-tier',
        'brackets': brackets_info,
        'description': (
            'Пятиступенчатая прогрессивная шкала' if year >= 2025
            else 'Двухступенчатая шкала'
        )
    }
