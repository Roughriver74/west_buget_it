/**
 * API Configuration
 * Supports both build-time (VITE_API_URL) and runtime (window.ENV_CONFIG) configuration
 */

const API_OVERRIDE_STORAGE_KEY = 'app-api-url-override';

// Extend Window interface to include ENV_CONFIG
declare global {
  interface Window {
    ENV_CONFIG?: {
      VITE_API_URL?: string;
    };
  }
}

const getStoredApiOverride = (): string | null => {
  if (typeof window === 'undefined' || !window.localStorage) return null;
  const override = window.localStorage.getItem(API_OVERRIDE_STORAGE_KEY);
  const trimmed = override?.trim();
  return trimmed ? trimmed : null;
};

// Get API URL from runtime config (Docker) or build-time env (development)
const getRawApiUrl = (): string => {
  // Priority 0: Local admin override for debugging (stored in localStorage)
  const overrideUrl = getStoredApiOverride();
  if (overrideUrl) {
    return overrideUrl;
  }

  // Priority 1: Runtime configuration (for Docker/production)
  if (typeof window !== 'undefined' && window.ENV_CONFIG?.VITE_API_URL) {
    // Check if it's still a placeholder (not replaced by entrypoint)
    const runtimeUrl = window.ENV_CONFIG.VITE_API_URL;
    if (runtimeUrl && !runtimeUrl.includes('__VITE_API_URL__')) {
      return runtimeUrl;
    }
  }

  // Priority 2: Build-time environment variable (for development)
  return import.meta.env.VITE_API_URL || '';
};

// Build API base URL with /api/v1 prefix
// IMPORTANT: Use getter function to make it dynamic (re-evaluated on each access)
export const getApiBaseUrl = (): string => {
  const rawApiUrl = getRawApiUrl();

  // If empty, use default
  if (!rawApiUrl) {
    return '/api/v1';
  }

  // If already contains /api/v1, use it as is
  if (rawApiUrl.includes('/api/v1')) {
    return rawApiUrl;
  }

  // If ends with /api, just append /v1 (avoid double /api)
  if (rawApiUrl.endsWith('/api')) {
    return `${rawApiUrl}/v1`;
  }

  // Otherwise append full /api/v1
  return `${rawApiUrl}/api/v1`;
};

export const getApiOverride = getStoredApiOverride;
export { API_OVERRIDE_STORAGE_KEY };

// Deprecated: Use getApiBaseUrl() instead for dynamic runtime config
// This is kept for backwards compatibility but may use stale build-time values
export const API_BASE_URL = getApiBaseUrl();

export const API_ROOT = import.meta.env.VITE_API_ROOT || '';

// Helper to build API URLs (dynamic)
export const buildApiUrl = (path: string): string => {
  // Remove leading slash from path if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;

  // If path already includes /api/v1, use it as is
  if (cleanPath.startsWith('api/v1')) {
    return `/${cleanPath}`;
  }

  // Otherwise prepend API_BASE_URL (get fresh value)
  return `${getApiBaseUrl()}/${cleanPath}`;
};
