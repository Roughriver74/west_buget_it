import { useMemo, useState } from 'react'
import { cn } from '@/legacy/lib/utils'
import { useIsMobile } from '@/legacy/hooks/usePerformance'

export interface VirtualTableColumn<T> {
  key: string
  label: string
  flex?: number
  minWidth?: string
  maxWidth?: string
  align?: 'left' | 'center' | 'right'
  render?: (value: any, item: T, index: number) => React.ReactNode
}

interface VirtualTableProps<T> {
  data: T[]
  columns: VirtualTableColumn<T>[]
  rowHeight?: number
  height?: number
  onRowClick?: (item: T, index: number) => void
  emptyMessage?: string
}

export default function VirtualTable<T extends Record<string, any>>({
  data = [],
  columns = [],
  rowHeight = 60,
  height = 600,
  onRowClick,
  emptyMessage = 'Нет данных',
}: VirtualTableProps<T>) {
  const isMobile = useIsMobile()
  const viewportHeight = typeof window !== 'undefined' ? window.innerHeight : 800
  const actualRowHeight = isMobile ? 80 : rowHeight
  const actualHeight = isMobile ? Math.min(height, viewportHeight - 200) : height
  const [scrollTop, setScrollTop] = useState(0)

  const totalHeight = data.length * actualRowHeight
  const visibleCount = Math.max(1, Math.ceil(actualHeight / actualRowHeight))
  const overscan = 5
  const startIndex = Math.max(0, Math.floor(scrollTop / actualRowHeight) - overscan)
  const endIndex = Math.min(data.length, startIndex + visibleCount + overscan * 2)
  const visibleItems = useMemo(() => data.slice(startIndex, endIndex), [data, startIndex, endIndex])
  const offsetY = startIndex * actualRowHeight

  if (!data || data.length === 0) {
    return (
      <div className="p-5 text-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-sm text-gray-600 m-0">{emptyMessage}</p>
      </div>
    )
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden bg-white">
      <div className="bg-gray-50 border-b-2 border-gray-200 sticky top-0 z-10">
        <div className="flex px-4 py-3 gap-3">
          {columns.map((column, index) => (
            <div
              key={index}
              className="text-xs font-semibold text-gray-700 uppercase tracking-wider"
              style={{
                flex: column.flex || 1,
                minWidth: column.minWidth || (isMobile ? '80px' : '100px'),
                maxWidth: column.maxWidth,
                textAlign: column.align || 'left',
              }}
            >
              {column.label}
            </div>
          ))}
        </div>
      </div>

      <div
        className="scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-transparent"
        style={{ height: actualHeight, overflowY: 'auto' }}
        onScroll={event => setScrollTop(event.currentTarget.scrollTop)}
      >
        <div style={{ height: totalHeight, position: 'relative' }}>
          <div style={{ transform: `translateY(${offsetY}px)` }}>
            {visibleItems.map((item, idx) => {
              const isEven = (startIndex + idx) % 2 === 0
              return (
                <div
                  key={startIndex + idx}
                  className={cn(
                    'border-b border-gray-200 transition-colors',
                    isEven ? 'bg-gray-50' : 'bg-white',
                    onRowClick && 'cursor-pointer hover:bg-gray-100'
                  )}
                  style={{ height: actualRowHeight }}
                  onClick={() => onRowClick && onRowClick(item, startIndex + idx)}
                >
                  <div className="flex px-4 py-3 gap-3 items-center h-full">
                    {columns.map((column, colIndex) => (
                      <div
                        key={colIndex}
                        className="text-sm text-gray-900 overflow-hidden text-ellipsis whitespace-nowrap"
                        style={{
                          flex: column.flex || 1,
                          minWidth: column.minWidth || (isMobile ? '80px' : '100px'),
                          maxWidth: column.maxWidth,
                          textAlign: column.align || 'left',
                        }}
                      >
                        {column.render ? column.render(item[column.key], item, startIndex + idx) : item[column.key]}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200 text-[13px] text-gray-600 text-center">
        Всего записей: <strong>{data.length.toLocaleString()}</strong>
      </div>
    </div>
  )
}

