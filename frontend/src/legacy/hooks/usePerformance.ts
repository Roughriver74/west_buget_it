import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

export const useDebounce = <T>(value: T, delay: number = 500): T => {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}

export const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768)
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return isMobile
}

export const useOptimizedData = <T>(
  data: T[] | null | undefined,
  filterFn?: (item: T) => boolean,
  dependencies: any[] = []
): T[] => {
  return useMemo(() => {
    if (!data || !Array.isArray(data)) return []
    return filterFn ? data.filter(filterFn) : data
  }, [data, filterFn, ...dependencies])
}

export const useThrottle = <T extends (...args: any[]) => void>(callback: T, delay: number = 1000) => {
  const lastRan = useRef(Date.now())

  return useCallback(
    (...args: Parameters<T>) => {
      const now = Date.now()
      if (now - lastRan.current >= delay) {
        callback(...args)
        lastRan.current = now
      }
    },
    [callback, delay]
  )
}

