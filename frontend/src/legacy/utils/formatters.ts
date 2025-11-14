import { format, parseISO, isValid } from 'date-fns'

export const formatAmount = (value: number | string | null | undefined): string => {
  if (value == null || isNaN(Number(value))) return '0'
  const num = Number(value)
  if (num >= 1_000_000_000) return `${(num / 1_000_000_000).toFixed(1)} млрд`
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)} млн`
  if (num >= 1_000) return `${(num / 1_000).toFixed(0)} тыс`
  return num.toFixed(0)
}

export const formatAxisAmount = (value: number | string | null | undefined): string => {
  if (value == null || isNaN(Number(value))) return '0'
  const num = Number(value)
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(0)}M`
  if (num >= 1_000) return `${(num / 1_000).toFixed(0)}K`
  return num.toFixed(0)
}

export const formatTooltipAmount = (value: number | string | null | undefined): string => {
  if (value == null || isNaN(Number(value))) return '0 млн ₽'
  const num = Number(value)
  return `${(num / 1_000_000).toFixed(2)} млн ₽`
}

export const sampleArray = <T>(arr: T[], n: number = 2): T[] => {
  if (!arr || arr.length === 0) return []
  if (arr.length <= 20) return arr
  return arr.filter((_, index) => index % n === 0)
}

export const safeFormatDate = (dateStr: string | null | undefined, formatStr: string): string => {
  if (!dateStr) return '-'
  try {
    const parsed = parseISO(dateStr)
    if (!isValid(parsed)) {
      console.warn(`Invalid date value: ${dateStr}`)
      return '-'
    }
    return format(parsed, formatStr)
  } catch (error) {
    console.error(`Error formatting date: ${dateStr}`, error)
    return '-'
  }
}

