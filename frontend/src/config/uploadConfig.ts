/**
 * File Upload Configuration
 *
 * File size limits and upload settings
 * These should match backend constraints (INVOICE_MAX_FILE_SIZE, etc.)
 */

export const UPLOAD_CONFIG = {
  // File size limits (in MB)
  INVOICE_MAX_SIZE_MB: 10,
  KPI_IMPORT_MAX_SIZE_MB: 10,
  ATTACHMENT_MAX_SIZE_MB: 10,
  PROFILE_PHOTO_MAX_SIZE_MB: 5,
  EXCEL_IMPORT_MAX_SIZE_MB: 10,

  // File size limits (in bytes) - for programmatic use
  INVOICE_MAX_SIZE_BYTES: 10 * 1024 * 1024, // 10 MB
  KPI_IMPORT_MAX_SIZE_BYTES: 10 * 1024 * 1024,
  ATTACHMENT_MAX_SIZE_BYTES: 10 * 1024 * 1024,
  PROFILE_PHOTO_MAX_SIZE_BYTES: 5 * 1024 * 1024,

  // Accepted file types
  INVOICE_ACCEPTED_TYPES: ['application/pdf', 'image/png', 'image/jpeg'],
  EXCEL_ACCEPTED_TYPES: [
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ],
  IMAGE_ACCEPTED_TYPES: ['image/png', 'image/jpeg', 'image/jpg'],
} as const;

/**
 * Helper to validate file size
 */
export const validateFileSize = (file: File, maxSizeMB: number): boolean => {
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  return file.size <= maxSizeBytes;
};

/**
 * Helper to format file size for display
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
};
