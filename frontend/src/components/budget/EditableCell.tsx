import React, { useState, useEffect, useRef } from 'react'
import { InputNumber } from 'antd'

interface EditableCellProps {
  value: number
  onChange: (value: number) => void
  loading?: boolean
}

const EditableCell: React.FC<EditableCellProps> = ({ value, onChange, loading = false }) => {
  const [editing, setEditing] = useState(false)
  const [inputValue, setInputValue] = useState(value)
  const inputRef = useRef<any>(null)

  useEffect(() => {
    setInputValue(value)
  }, [value])

  useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus()
    }
  }, [editing])

  const handleClick = () => {
    if (!loading) {
      setEditing(true)
    }
  }

  const handleChange = (val: number | null) => {
    setInputValue(val || 0)
  }

  const handleBlur = () => {
    setEditing(false)
    if (inputValue !== value) {
      onChange(inputValue)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      setEditing(false)
      if (inputValue !== value) {
        onChange(inputValue)
      }
    } else if (e.key === 'Escape') {
      setInputValue(value)
      setEditing(false)
    }
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  if (editing) {
    return (
      <InputNumber
        ref={inputRef}
        value={inputValue}
        onChange={handleChange}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        min={0}
        step={1000}
        style={{ width: '100%' }}
        formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
        parser={(value) => Number(value!.replace(/\s?/g, '')) as any}
        disabled={loading}
      />
    )
  }

  return (
    <div
      onClick={handleClick}
      style={{
        cursor: loading ? 'wait' : 'pointer',
        padding: '4px 11px',
        minHeight: '32px',
        display: 'flex',
        alignItems: 'center',
        borderRadius: '6px',
        transition: 'background-color 0.2s',
        backgroundColor: loading ? '#f5f5f5' : 'transparent',
      }}
      onMouseEnter={(e) => {
        if (!loading) {
          e.currentTarget.style.backgroundColor = '#fafafa'
        }
      }}
      onMouseLeave={(e) => {
        if (!loading) {
          e.currentTarget.style.backgroundColor = 'transparent'
        }
      }}
    >
      {formatNumber(value)}
    </div>
  )
}

export default EditableCell
