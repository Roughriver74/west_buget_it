/**
 * Dimension Configuration
 *
 * Centralized UI dimensions for consistent layout
 * All values in pixels unless otherwise specified
 */

export const CHART_HEIGHTS = {
  SMALL: 300,
  MEDIUM: 320,
  STANDARD: 360,
  LARGE: 400,
  EXTRA_LARGE: 450,
} as const;

export const COMPONENT_WIDTHS = {
  DRAWER_EXTRA_LARGE: 1200,
  DRAWER_LARGE: 1000,
  DRAWER_MEDIUM: 800,
  MODAL_LARGE: 1000,
  MODAL_MEDIUM: 800,
  MODAL_SMALL: 500,
  SIDEBAR: 250,
} as const;

export const MIN_HEIGHTS = {
  EMPTY_STATE: 'calc(100vh - 200px)',
  CONTENT_AREA: '40vh',
  FULL_PAGE: '100vh',
  TABLE_CONTAINER: 'calc(100vh - 300px)',
} as const;

export const SPACING = {
  EXTRA_SMALL: 4,
  SMALL: 8,
  MEDIUM: 16,
  LARGE: 24,
  EXTRA_LARGE: 32,
} as const;

// Export individual constants for convenience
export const STANDARD_CHART_HEIGHT = CHART_HEIGHTS.STANDARD;
export const LARGE_DRAWER_WIDTH = COMPONENT_WIDTHS.DRAWER_LARGE;
