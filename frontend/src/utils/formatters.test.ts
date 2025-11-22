import { ExpenseStatus } from '../types'
import {
  getExpenseStatusLabel,
  getExpenseStatusColor,
  formatCurrency,
} from './formatters'

describe('formatters', () => {
  it('returns readable status labels', () => {
    expect(getExpenseStatusLabel(ExpenseStatus.PAID)).toBe('Оплачена')
    expect(getExpenseStatusLabel('UNKNOWN' as ExpenseStatus)).toBe('UNKNOWN')
  })

  it('returns status colors with default fallback', () => {
    expect(getExpenseStatusColor(ExpenseStatus.REJECTED)).toBe('error')
    expect(getExpenseStatusColor('UNKNOWN' as ExpenseStatus)).toBe('default')
  })

  it('formats currency in Russian locale', () => {
    const formatted = formatCurrency(1234.56)
    // Locale string can vary slightly, but must contain the value and currency sign/code
    expect(formatted).toMatch(/1[\s\u00A0]?234/) // regular or non-breaking space
    expect(formatted).toMatch(/₽|RUB/)
  })
})
