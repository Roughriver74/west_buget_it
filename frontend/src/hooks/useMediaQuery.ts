import { useState, useEffect } from 'react'

export type Breakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl'

// Ant Design breakpoints
const breakpoints = {
  xs: 480,
  sm: 576,
  md: 768,
  lg: 992,
  xl: 1200,
  xxl: 1600,
}

/**
 * Custom hook to detect screen size changes
 *
 * @param query - Media query string or breakpoint name
 * @returns boolean indicating if the query matches
 *
 * @example
 * ```tsx
 * const isMobile = useMediaQuery('(max-width: 768px)')
 * const isDesktop = useMediaQuery('lg')
 * ```
 */
export function useMediaQuery(query: string): boolean {
  // Check if query is a breakpoint name
  const mediaQuery = query in breakpoints
    ? `(min-width: ${breakpoints[query as Breakpoint]}px)`
    : query

  const [matches, setMatches] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(mediaQuery).matches
    }
    return false
  })

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const mediaQueryList = window.matchMedia(mediaQuery)
    const listener = (event: MediaQueryListEvent) => {
      setMatches(event.matches)
    }

    // Modern browsers
    if (mediaQueryList.addEventListener) {
      mediaQueryList.addEventListener('change', listener)
    } else {
      // Legacy browsers
      mediaQueryList.addListener(listener)
    }

    // Set initial value
    setMatches(mediaQueryList.matches)

    return () => {
      if (mediaQueryList.removeEventListener) {
        mediaQueryList.removeEventListener('change', listener)
      } else {
        mediaQueryList.removeListener(listener)
      }
    }
  }, [mediaQuery])

  return matches
}

/**
 * Hook to get current breakpoint
 *
 * @returns Current breakpoint name ('xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl')
 *
 * @example
 * ```tsx
 * const breakpoint = useBreakpoint()
 * if (breakpoint === 'xs' || breakpoint === 'sm') {
 *   return <MobileLayout />
 * }
 * ```
 */
export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>(() => {
    if (typeof window === 'undefined') {
      return 'md'
    }
    return getCurrentBreakpoint(window.innerWidth)
  })

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const handleResize = () => {
      setBreakpoint(getCurrentBreakpoint(window.innerWidth))
    }

    window.addEventListener('resize', handleResize)
    handleResize() // Set initial value

    return () => {
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return breakpoint
}

function getCurrentBreakpoint(width: number): Breakpoint {
  if (width < breakpoints.xs) return 'xs'
  if (width < breakpoints.sm) return 'xs'
  if (width < breakpoints.md) return 'sm'
  if (width < breakpoints.lg) return 'md'
  if (width < breakpoints.xl) return 'lg'
  if (width < breakpoints.xxl) return 'xl'
  return 'xxl'
}

/**
 * Convenient hooks for common breakpoints
 */
export const useIsMobile = () => useMediaQuery('(max-width: 767px)')
export const useIsTablet = () => useMediaQuery('(min-width: 768px) and (max-width: 991px)')
export const useIsDesktop = () => useMediaQuery('(min-width: 992px)')
export const useIsSmallScreen = () => useMediaQuery('(max-width: 991px)') // Mobile + Tablet
