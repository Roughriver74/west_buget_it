import { useEffect, useMemo, useRef, useState } from 'react'
import { Check, ChevronDown, Search } from 'lucide-react'
import { Input } from '@/legacy/components/ui/input'

export interface MultiSelectOption {
  value: string
  label: string
}

export interface MultiSelectProps {
  options: MultiSelectOption[]
  selected: string[]
  onChange: (selected: string[]) => void
  placeholder?: string
  label?: string
  hint?: string
  isLoading?: boolean
  className?: string
  searchPlaceholder?: string
}

export function MultiSelect({
  options,
  selected,
  onChange,
  placeholder = 'Выберите',
  label,
  hint,
  isLoading = false,
  className = '',
  searchPlaceholder = 'Поиск...',
}: MultiSelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [search, setSearch] = useState('')
  const dropdownRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const filteredOptions = useMemo(() => {
    if (!search.trim()) return options
    return options.filter(option =>
      option.label.toLowerCase().includes(search.trim().toLowerCase())
    )
  }, [options, search])

  const toggleOption = (value: string) => {
    const newSelected = selected.includes(value)
      ? selected.filter(v => v !== value)
      : [...selected, value]
    onChange(newSelected)
  }

  const selectAll = () => onChange(options.map(opt => opt.value))
  const clearAll = () => onChange([])

  const displayText = () => {
    if (selected.length === 0) return placeholder
    if (selected.length === options.length) return 'Все'
    if (selected.length === 1) {
      const option = options.find(opt => opt.value === selected[0])
      return option?.label || selected[0]
    }
    return `Выбрано: ${selected.length}`
  }

  return (
    <div className={`relative flex flex-col gap-1.5 ${className}`} ref={dropdownRef}>
      {label && <label className="text-xs font-medium text-foreground/70">{label}</label>}

      <button
        type="button"
        onClick={() => setIsOpen(prev => !prev)}
        className="flex items-center justify-between w-full border border-border rounded-lg px-3 py-2 text-sm bg-card hover:border-primary focus:outline-none focus:ring-2 focus:ring-primary"
      >
        <span className="truncate text-left text-foreground">{displayText()}</span>
        <ChevronDown size={16} className="text-muted-foreground flex-shrink-0 ml-2" />
      </button>

      {hint && <span className="text-[10px] text-muted-foreground leading-tight">{hint}</span>}

      {isOpen && (
        <div className="absolute z-50 top-full left-0 mt-2 w-full min-w-[280px] rounded-xl border border-border bg-card shadow-2xl p-3">
          <div className="relative mb-2">
            <Input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder={searchPlaceholder}
              className="pl-9"
            />
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          </div>

          <div className="flex justify-between items-center mb-2 text-xs text-muted-foreground">
            <div className="flex gap-2">
              <button
                type="button"
                className="text-primary hover:underline"
                onClick={selectAll}
              >
                Выбрать все
              </button>
              <button
                type="button"
                className="text-primary hover:underline disabled:text-muted-foreground"
                onClick={clearAll}
                disabled={selected.length === 0}
              >
                Снять все
              </button>
            </div>
            <span>{isLoading ? 'Загружаем...' : `${filteredOptions.length} элементов`}</span>
          </div>

          <div className="max-h-64 overflow-y-auto pr-1">
            {isLoading && <div className="text-sm text-muted-foreground py-4 text-center">Загружаем...</div>}
            {!isLoading && filteredOptions.length === 0 && (
              <div className="text-sm text-muted-foreground py-4 text-center">Ничего не найдено</div>
            )}
            {!isLoading &&
              filteredOptions.map(option => (
                <label
                  key={option.value}
                  className="flex items-center gap-2 text-sm py-1.5 px-2 rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    className="accent-blue-500"
                    checked={selected.includes(option.value)}
                    onChange={() => toggleOption(option.value)}
                  />
                  <span className="truncate flex-1">{option.label}</span>
                  {selected.includes(option.value) && (
                    <Check size={14} className="text-blue-500 flex-shrink-0" />
                  )}
                </label>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}

