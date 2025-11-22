/**
 * Russian holidays and weekends utility
 */

// Фиксированные праздники России
const FIXED_HOLIDAYS: Record<string, string> = {
  '1-1': 'Новый год',
  '1-2': 'Новогодние каникулы',
  '1-3': 'Новогодние каникулы',
  '1-4': 'Новогодние каникулы',
  '1-5': 'Новогодние каникулы',
  '1-6': 'Новогодние каникулы',
  '1-7': 'Рождество Христово',
  '1-8': 'Новогодние каникулы',
  '2-23': 'День защитника Отечества',
  '3-8': 'Международный женский день',
  '5-1': 'Праздник Весны и Труда',
  '5-9': 'День Победы',
  '6-12': 'День России',
  '11-4': 'День народного единства',
}

// Переносы выходных по годам (обновляется правительством)
const WEEKEND_TRANSFERS: Record<number, { workdays: string[]; holidays: string[] }> = {
  2024: {
    workdays: ['4-27', '11-2', '12-28'], // Рабочие дни вместо выходных
    holidays: ['4-29', '4-30', '5-10', '12-30', '12-31'], // Выходные вместо рабочих
  },
  2025: {
    workdays: ['1-3', '5-2'], // Рабочие дни вместо выходных
    holidays: ['1-1', '1-2', '1-7', '1-8', '5-1', '5-8', '5-9', '6-11', '6-12', '6-13', '11-3', '11-4'], // Выходные вместо рабочих
  },
}

/**
 * Check if date is a Russian holiday
 */
export function isRussianHoliday(year: number, month: number, day: number): boolean {
  const key = `${month}-${day}`

  // Check fixed holidays
  if (FIXED_HOLIDAYS[key]) {
    return true
  }

  // Check weekend transfers
  const transfers = WEEKEND_TRANSFERS[year]
  if (transfers?.holidays.includes(key)) {
    return true
  }

  return false
}

/**
 * Check if date is a weekend (Saturday or Sunday) or holiday
 */
export function isWeekendOrHoliday(year: number, month: number, day: number): boolean {
  const date = new Date(year, month - 1, day)
  const dayOfWeek = date.getDay() // 0 = Sunday, 1 = Monday, ..., 6 = Saturday

  // Check if it's a transferred workday
  const transfers = WEEKEND_TRANSFERS[year]
  const key = `${month}-${day}`
  if (transfers?.workdays.includes(key)) {
    return false // This is a workday despite being weekend/holiday
  }

  // Check if weekend (Saturday = 6, Sunday = 0)
  if (dayOfWeek === 0 || dayOfWeek === 6) {
    return true
  }

  // Check if holiday
  return isRussianHoliday(year, month, day)
}

/**
 * Get holiday name if exists
 */
export function getHolidayName(_year: number, month: number, day: number): string | null {
  const key = `${month}-${day}`
  return FIXED_HOLIDAYS[key] || null
}

/**
 * Check if date is a transferred workday
 */
export function isTransferredWorkday(year: number, month: number, day: number): boolean {
  const transfers = WEEKEND_TRANSFERS[year]
  const key = `${month}-${day}`
  return transfers?.workdays.includes(key) || false
}
