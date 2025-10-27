import type { BaselineSummary } from '@/types/budgetPlanning'

const CACHE_TTL_MS = 5 * 60 * 1000

type CacheRecord = {
  expiresAt: number
  data: BaselineSummary
}

const cache = new Map<string, CacheRecord>()
const inflight = new Map<string, Promise<BaselineSummary>>()

const cacheKey = (categoryId: number, year: number) => `${categoryId}:${year}`

export const getCachedBaseline = (categoryId: number, year: number): BaselineSummary | undefined => {
  const key = cacheKey(categoryId, year)
  const record = cache.get(key)
  if (!record) {
    return undefined
  }

  if (record.expiresAt < Date.now()) {
    cache.delete(key)
    return undefined
  }

  return record.data
}

export const setCachedBaseline = (categoryId: number, year: number, data: BaselineSummary) => {
  const key = cacheKey(categoryId, year)
  cache.set(key, { data, expiresAt: Date.now() + CACHE_TTL_MS })
}

export const getInflightBaseline = (categoryId: number, year: number) => inflight.get(cacheKey(categoryId, year))
export const setInflightBaseline = (categoryId: number, year: number, promise: Promise<BaselineSummary>) =>
  inflight.set(cacheKey(categoryId, year), promise)
export const clearInflightBaseline = (categoryId: number, year: number) => inflight.delete(cacheKey(categoryId, year))

export const invalidateBaselineCache = (categoryId?: number) => {
  if (typeof categoryId === 'number') {
    const prefix = `${categoryId}:`
    for (const key of cache.keys()) {
      if (key.startsWith(prefix)) {
        cache.delete(key)
      }
    }
    for (const key of inflight.keys()) {
      if (key.startsWith(prefix)) {
        inflight.delete(key)
      }
    }
    return
  }

  cache.clear()
  inflight.clear()
}
