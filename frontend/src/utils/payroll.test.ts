import {
  shouldPayQuarterlyBonus,
  shouldPayAnnualBonus,
  calculateMonthlyBonuses,
  calculateIncomeTax,
  calculateSocialTax,
  calculateNetAmount,
  calculateEmployerCost,
} from './payroll'

describe('payroll utils', () => {
  it('identifies quarterly bonus months', () => {
    expect(shouldPayQuarterlyBonus(3)).toBe(true)
    expect(shouldPayQuarterlyBonus(4)).toBe(false)
    expect(shouldPayQuarterlyBonus(12)).toBe(true)
  })

  it('identifies annual bonus month', () => {
    expect(shouldPayAnnualBonus(12)).toBe(true)
    expect(shouldPayAnnualBonus(11)).toBe(false)
  })

  it('calculates monthly bonuses breakdown', () => {
    const result = calculateMonthlyBonuses(10_000, 40_000, 100_000, 12)

    expect(result).toEqual({
      monthly: 10_000,
      quarterly: 40_000,
      annual: 100_000,
      total: 150_000,
    })
  })

  it('calculates taxes and net amounts', () => {
    const gross = 100_000
    const incomeTax = calculateIncomeTax(gross) // 13% default
    const socialTax = calculateSocialTax(gross) // 30.2% default
    const net = calculateNetAmount(gross, incomeTax)
    const employerCost = calculateEmployerCost(gross, socialTax)

    expect(incomeTax).toBe(13_000)
    expect(socialTax).toBe(30_200)
    expect(net).toBe(87_000)
    expect(employerCost).toBe(130_200)
  })
})
