import { describe, expect, it, vi } from 'vitest'

import {
  getCachedBaseline,
  setCachedBaseline,
  invalidateBaselineCache,
  setInflightBaseline,
  getInflightBaseline,
  clearInflightBaseline,
} from './baselineCache'

const sampleBaseline = { total: 1000, opex: 700, capex: 300 } as const

describe('baselineCache', () => {
  it('stores and expires cache entries', () => {
    vi.useFakeTimers()

    setCachedBaseline(1, 2025, sampleBaseline as any)
    expect(getCachedBaseline(1, 2025)).toEqual(sampleBaseline)

    // Advance beyond TTL (5 minutes)
    vi.advanceTimersByTime(5 * 60 * 1000 + 1)
    expect(getCachedBaseline(1, 2025)).toBeUndefined()

    vi.useRealTimers()
  })

  it('handles inflight promises and clears them', async () => {
    const promise = Promise.resolve(sampleBaseline as any)
    setInflightBaseline(2, 2024, promise)
    expect(getInflightBaseline(2, 2024)).toBe(promise)
    clearInflightBaseline(2, 2024)
    expect(getInflightBaseline(2, 2024)).toBeUndefined()
  })

  it('invalidates by category or completely', () => {
    setCachedBaseline(10, 2024, sampleBaseline as any)
    setCachedBaseline(11, 2024, sampleBaseline as any)
    setInflightBaseline(10, 2024, Promise.resolve(sampleBaseline as any))

    invalidateBaselineCache(10)
    expect(getCachedBaseline(10, 2024)).toBeUndefined()
    expect(getInflightBaseline(10, 2024)).toBeUndefined()
    expect(getCachedBaseline(11, 2024)).toEqual(sampleBaseline)

    invalidateBaselineCache()
    expect(getCachedBaseline(11, 2024)).toBeUndefined()
  })
})
