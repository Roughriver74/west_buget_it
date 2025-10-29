/**
 * API Configuration
 * Supports both build-time (VITE_API_URL) and runtime (window.ENV_CONFIG) configuration
 */

// Extend Window interface to include ENV_CONFIG
declare global {
  interface Window {
    ENV_CONFIG?: {
      VITE_API_URL?: string;
    };
  }
}

// Get API URL from runtime config (Docker) or build-time env (development)
const getRawApiUrl = (): string => {
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
const rawApiUrl = getRawApiUrl();

// If rawApiUrl already contains /api/v1, use it as is
// Otherwise, append /api/v1
export const API_BASE_URL = rawApiUrl
  ? (rawApiUrl.includes('/api/v1') ? rawApiUrl : `${rawApiUrl}/api/v1`)
  : '/api/v1';

export const API_ROOT = import.meta.env.VITE_API_ROOT || '';

// Helper to build API URLs
export const buildApiUrl = (path: string): string => {
  // Remove leading slash from path if present
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;

  // If path already includes /api/v1, use it as is
  if (cleanPath.startsWith('api/v1')) {
    return `/${cleanPath}`;
  }

  // Otherwise prepend API_BASE_URL
  return `${API_BASE_URL}/${cleanPath}`;
};
