/**
 * API Configuration
 * Uses relative URLs to leverage Vite proxy in development
 */

// Build API base URL with /api/v1 prefix
const rawApiUrl = import.meta.env.VITE_API_URL || '';
export const API_BASE_URL = rawApiUrl ? `${rawApiUrl}/api/v1` : '/api/v1';
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
