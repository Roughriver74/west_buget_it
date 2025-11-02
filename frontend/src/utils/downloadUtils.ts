// Utility function to download blob as file
export const downloadBlob = (blob: Blob, filename: string) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', filename)
  document.body.appendChild(link)
  link.click()
  link.parentNode?.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// Generate filename with timestamp
export const generateExportFilename = (prefix: string, year: number, ext: string = 'xlsx') => {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '').replace('T', '_')
  return `${prefix}_${year}_${timestamp}.${ext}`
}
