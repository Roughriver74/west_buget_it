import { useState, useEffect } from 'react'
import { Grid } from 'antd'

const { useBreakpoint: useAntdBreakpoint } = Grid

export interface BreakpointState {
  isMobile: boolean
  isTablet: boolean
  isDesktop: boolean
  isLargeDesktop: boolean
  xs: boolean
  sm: boolean
  md: boolean
  lg: boolean
  xl: boolean
  xxl: boolean
}

/**
 * Custom hook for responsive breakpoint detection
 * Returns breakpoint states and helper flags
 */
export const useBreakpoint = (): BreakpointState => {
  const screens = useAntdBreakpoint()

  // Helper flags for common use cases
  const isMobile = !screens.md // < 768px
  const isTablet = !!(screens.md && !screens.lg) // >= 768px && < 992px
  const isDesktop = !!screens.lg // >= 992px
  const isLargeDesktop = !!screens.xl // >= 1200px

  return {
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,
    xs: !!screens.xs,
    sm: !!screens.sm,
    md: !!screens.md,
    lg: !!screens.lg,
    xl: !!screens.xl,
    xxl: !!screens.xxl,
  }
}

/**
 * Hook for window width tracking
 */
export const useWindowWidth = (): number => {
  const [width, setWidth] = useState(window.innerWidth)

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth)
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  return width
}

export default useBreakpoint
