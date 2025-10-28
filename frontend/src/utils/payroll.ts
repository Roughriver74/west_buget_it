/**
 * Payroll utility functions
 */

/**
 * Определяет, нужно ли начислять квартальную премию в данном месяце
 * Квартальные премии начисляются в последний месяц каждого квартала:
 * - Март (Q1)
 * - Июнь (Q2)
 * - Сентябрь (Q3)
 * - Декабрь (Q4)
 */
export function shouldPayQuarterlyBonus(month: number): boolean {
  return month === 3 || month === 6 || month === 9 || month === 12;
}

/**
 * Определяет, нужно ли начислять годовую премию в данном месяце
 * Годовая премия начисляется только в декабре
 */
export function shouldPayAnnualBonus(month: number): boolean {
  return month === 12;
}

/**
 * Рассчитывает общую сумму премий для выплаты в конкретном месяце
 * @param monthlyBonus - месячная премия (начисляется каждый месяц)
 * @param quarterlyBonus - квартальная премия (начисляется в марте, июне, сентябре, декабре)
 * @param annualBonus - годовая премия (начисляется в декабре)
 * @param month - номер месяца (1-12)
 * @returns общая сумма премий для этого месяца
 */
export function calculateMonthlyBonuses(
  monthlyBonus: number,
  quarterlyBonus: number,
  annualBonus: number,
  month: number
): {
  monthly: number;
  quarterly: number;
  annual: number;
  total: number;
} {
  return {
    monthly: monthlyBonus,
    quarterly: shouldPayQuarterlyBonus(month) ? quarterlyBonus : 0,
    annual: shouldPayAnnualBonus(month) ? annualBonus : 0,
    total:
      monthlyBonus +
      (shouldPayQuarterlyBonus(month) ? quarterlyBonus : 0) +
      (shouldPayAnnualBonus(month) ? annualBonus : 0),
  };
}

/**
 * Рассчитывает НДФЛ (подоходный налог)
 */
export function calculateIncomeTax(grossAmount: number, rate: number = 0.13): number {
  return Math.round(grossAmount * rate);
}

/**
 * Рассчитывает страховые взносы (для работодателя)
 * По умолчанию 30.2%:
 * - ПФР (Пенсионный фонд): 22%
 * - ОМС (Медицинское страхование): 5.1%
 * - ФСС (Социальное страхование): 2.9%
 * - Страхование от несчастных случаев: ~0.2%
 */
export function calculateSocialTax(grossAmount: number, rate: number = 0.302): number {
  return Math.round(grossAmount * rate);
}

/**
 * Рассчитывает чистую сумму на руки сотруднику (net amount)
 */
export function calculateNetAmount(
  grossAmount: number,
  incomeTax: number,
  socialTaxForEmployee: number = 0
): number {
  return grossAmount - incomeTax - socialTaxForEmployee;
}

/**
 * Рассчитывает полную стоимость для работодателя
 */
export function calculateEmployerCost(grossAmount: number, socialTax: number): number {
  return grossAmount + socialTax;
}
