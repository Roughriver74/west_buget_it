/**
 * Responsive utility functions for mobile optimization
 */

export const getResponsiveSpacing = (isMobile: boolean, isSmallScreen: boolean) => ({
  card: isMobile ? 12 : isSmallScreen ? 16 : 24,
  page: isMobile ? 12 : isSmallScreen ? 16 : 24,
  section: isMobile ? 8 : isSmallScreen ? 12 : 16,
  element: isMobile ? 4 : isSmallScreen ? 6 : 8,
})

export const getResponsiveGutter = (isMobile: boolean, isSmallScreen: boolean): [number, number] => {
  if (isMobile) return [8, 8]
  if (isSmallScreen) return [12, 12]
  return [16, 16]
}

export const getResponsiveButtonSize = (isMobile: boolean, isSmallScreen: boolean) => {
  if (isMobile) return 'large' as const // Touch-friendly
  if (isSmallScreen) return 'middle' as const
  return 'middle' as const
}

export const getResponsiveTableSize = (isMobile: boolean, isSmallScreen: boolean) => {
  if (isMobile) return 'middle' as const
  if (isSmallScreen) return 'middle' as const
  return 'large' as const
}

export const getResponsiveModalWidth = (isMobile: boolean, isSmallScreen: boolean) => {
  if (isMobile) return '100%'
  if (isSmallScreen) return '90%'
  return 800
}

export const getResponsiveDrawerWidth = (isMobile: boolean) => {
  return isMobile ? '100%' : 720
}

export const getResponsivePagination = (isMobile: boolean, isSmallScreen: boolean) => ({
  pageSize: isMobile ? 10 : isSmallScreen ? 15 : 20,
  showSizeChanger: !isMobile,
  showQuickJumper: !isMobile,
  simple: isMobile,
})

export const getResponsiveCardStyle = (isMobile: boolean, isSmallScreen: boolean) => ({
  padding: isMobile ? 12 : isSmallScreen ? 16 : 24,
  marginBottom: isMobile ? 12 : isSmallScreen ? 16 : 24,
})

export const getResponsiveFormLayout = (isMobile: boolean) => ({
  labelCol: isMobile ? { span: 24 } : { span: 6 },
  wrapperCol: isMobile ? { span: 24 } : { span: 18 },
})

export const getResponsiveGridCols = (isMobile: boolean, isSmallScreen: boolean) => ({
  xs: isMobile ? 1 : 1,
  sm: isMobile ? 1 : 2,
  md: isSmallScreen ? 2 : 3,
  lg: 3,
  xl: 4,
  xxl: 6,
})

export const getResponsiveFontSize = (isMobile: boolean, isSmallScreen: boolean) => ({
  h1: isMobile ? 24 : isSmallScreen ? 28 : 32,
  h2: isMobile ? 20 : isSmallScreen ? 22 : 24,
  h3: isMobile ? 18 : isSmallScreen ? 18 : 20,
  h4: isMobile ? 16 : 16,
  body: isMobile ? 14 : 14,
  small: isMobile ? 12 : 12,
})

export const shouldUseMobileDrawer = (isMobile: boolean) => isMobile

export const getResponsiveTableScroll = (isMobile: boolean, defaultWidth?: number) => {
  if (isMobile) {
    return undefined // ResponsiveTable handles mobile scroll
  }
  return { x: defaultWidth || 1000 }
}

export const getResponsiveChartHeight = (isMobile: boolean, isSmallScreen: boolean) => {
  if (isMobile) return 250
  if (isSmallScreen) return 300
  return 400
}

export const getResponsiveStatisticSize = (isMobile: boolean) => {
  return isMobile ? 'small' as const : 'default' as const
}
