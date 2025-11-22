import { describe, expect, it, vi } from 'vitest'

import { downloadBlob, generateExportFilename } from './downloadUtils'

describe('downloadUtils', () => {
  it('generates timestamped export filename', () => {
    const result = generateExportFilename('budget', 2025, 'csv')
    const match = /^budget_(\d{4})_(\d{8})_(\d{6})\.csv$/.exec(result)
    expect(match).not.toBeNull()
    if (!match) return
    expect(match[1]).toBe('2025')
    expect(match[2]).toHaveLength(8)
    expect(match[3]).toHaveLength(6)
  })

  it('creates link, triggers click and revokes url', () => {
    const createObjectURL = vi.fn(() => 'blob:test')
    const revokeObjectURL = vi.fn()
    Object.defineProperty(URL, 'createObjectURL', { writable: true, value: createObjectURL })
    Object.defineProperty(URL, 'revokeObjectURL', { writable: true, value: revokeObjectURL })
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    const initialChildren = document.body.childElementCount

    downloadBlob(new Blob(['test']), 'export.xlsx')

    expect(createObjectURL).toHaveBeenCalledTimes(1)
    expect(clickSpy).toHaveBeenCalledTimes(1)
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:test')
    expect(document.body.childElementCount).toBe(initialChildren)
  })
})
