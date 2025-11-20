import { describe, it, expect } from 'vitest'
import { cn } from './cn'

describe('cn utility', () => {
  it('should merge classes correctly', () => {
    expect(cn('c1', 'c2')).toBe('c1 c2')
  })

  it('should handle conditional classes', () => {
    expect(cn('c1', true && 'c2', false && 'c3')).toBe('c1 c2')
  })

  it('should merge tailwind classes', () => {
    expect(cn('p-2 p-4')).toBe('p-4')
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500')
  })

  it('should handle arrays and objects', () => {
    expect(cn(['c1', 'c2'])).toBe('c1 c2')
    expect(cn({ c1: true, c2: false })).toBe('c1')
  })
})
