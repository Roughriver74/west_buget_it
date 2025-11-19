/**
 * Timing Configuration
 *
 * Centralized timing settings for consistent behavior across the application
 * All values in milliseconds unless otherwise specified
 */

export const TIMING_CONFIG = {
  // ============================================================================
  // POLLING & SYNC
  // ============================================================================
  SYNC_POLL_INTERVAL_MS: 5000, // 5 seconds - interval between poll checks
  SYNC_MAX_POLLS: 120, // Maximum poll attempts (10 minutes total at 5s interval)
  SYNC_INITIAL_DELAY_MS: 2000, // 2 seconds - initial delay before first poll
  SYNC_COMPLETION_DELAY_MS: 3000, // 3 seconds - delay after completion message

  // ============================================================================
  // UI FEEDBACK & NOTIFICATIONS
  // ============================================================================
  COPY_CONFIRMATION_TIMEOUT_MS: 2000, // 2 seconds - "Copied!" message display
  PROGRESS_UPDATE_DELAY_MS: 3000, // 3 seconds - delay between progress updates
  SUCCESS_MESSAGE_TIMEOUT_MS: 2000, // 2 seconds - success notification auto-close
  ERROR_MESSAGE_TIMEOUT_MS: 5000, // 5 seconds - error notification auto-close

  // ============================================================================
  // DEBOUNCING & THROTTLING
  // ============================================================================
  DEBOUNCE_DELAY_MS: 300, // 300ms - standard debounce for search/filter inputs
  DEBOUNCE_FAST_MS: 150, // 150ms - fast debounce for rapid updates
  DEBOUNCE_SLOW_MS: 500, // 500ms - slow debounce for heavy operations
  THROTTLE_DELAY_MS: 1000, // 1 second - throttle for scroll/resize events

  // ============================================================================
  // TABLE & SCROLL
  // ============================================================================
  TABLE_SCROLL_DELAY_MS: 100, // Delay for table scroll synchronization
  SCROLL_TO_DELAY_MS: 200, // Delay before scrolling to element
  DOUBLE_RAF_DELAY_MS: 50, // Additional delay after double requestAnimationFrame

  // ============================================================================
  // LOADING STATES
  // ============================================================================
  MIN_LOADING_SPINNER_MS: 300, // Minimum time to show spinner (prevent flash)
  SKELETON_DELAY_MS: 200, // Delay before showing skeleton screens

  // ============================================================================
  // FORM & VALIDATION
  // ============================================================================
  FORM_VALIDATION_DELAY_MS: 500, // Delay for inline form validation
  AUTO_SAVE_DELAY_MS: 2000, // Delay for auto-save functionality
} as const;

// Export individual constants for convenience
export const SYNC_POLL_INTERVAL = TIMING_CONFIG.SYNC_POLL_INTERVAL_MS;
export const DEBOUNCE_DELAY = TIMING_CONFIG.DEBOUNCE_DELAY_MS;
export const TABLE_SCROLL_DELAY = TIMING_CONFIG.TABLE_SCROLL_DELAY_MS;
