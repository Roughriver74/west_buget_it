import React, { useCallback, useEffect, useRef, useState } from 'react'
import { Table, Tag, Spin, message, Button, Space, Alert, Segmented } from 'antd'
import { CopyOutlined, PlusOutlined, DownloadOutlined, WarningOutlined, CalendarOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { budgetApi } from '@/api'
import EditableCell from './EditableCell'
import CopyPlanModal from './CopyPlanModal'
import { useDepartment } from '@/contexts/DepartmentContext'

interface BudgetPlanTableProps {
  year: number
}

const MONTH_NAMES = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
const MONTH_SEGMENT_OPTIONS = MONTH_NAMES.map((label, index) => ({ label, value: index + 1 }))
const MONTH_COLUMN_WIDTH = 270
const TABLE_SCROLL_WIDTH = 300 + MONTH_COLUMN_WIDTH * 12 + 270
const STICKY_HEADER_OFFSET = 64
const CONTROL_PANEL_HEIGHT = 110 // Высота панели управления

const BudgetPlanTable = React.forwardRef<
  { scrollBy: (direction: 'left' | 'right') => void },
  BudgetPlanTableProps
>((props, ref) => {
  const { year } = props
  const [copyModalOpen, setCopyModalOpen] = useState(false)
  const [updatingCells, setUpdatingCells] = useState<Set<string>>(new Set())
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1
  const [activeMonth, setActiveMonth] = useState<number>(year === currentYear ? currentMonth : 1)
  const queryClient = useQueryClient()
  const { selectedDepartment } = useDepartment()
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const scrollTargetRef = useRef<HTMLDivElement | null>(null)

  // Загрузка плана на год
  const { data: planData, isLoading } = useQuery({
    queryKey: ['budget-plan', year, selectedDepartment?.id],
    queryFn: () => budgetApi.getPlanForYear(year, selectedDepartment?.id),
  })

  // Инициализация плана
  const initMutation = useMutation({
    mutationFn: () => budgetApi.initializePlan(year),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ['budget-plan', year] })
      message.success(`План инициализирован! Создано записей: ${response.created_entries}`)
    },
    onError: (error: any) => {
      message.error(`Ошибка инициализации: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Обновление ячейки
  const updateCellMutation = useMutation({
    mutationFn: budgetApi.updateCell,
    onMutate: async (variables) => {
      const cellKey = `${variables.category_id}-${variables.month}`
      setUpdatingCells((prev) => new Set(prev).add(cellKey))
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['budget-plan', year] })
      const cellKey = `${variables.category_id}-${variables.month}`
      setUpdatingCells((prev) => {
        const newSet = new Set(prev)
        newSet.delete(cellKey)
        return newSet
      })
    },
    onError: (error: any, variables) => {
      message.error(`Ошибка обновления: ${error.response?.data?.detail || error.message}`)
      const cellKey = `${variables.category_id}-${variables.month}`
      setUpdatingCells((prev) => {
        const newSet = new Set(prev)
        newSet.delete(cellKey)
        return newSet
      })
    },
  })

  const handleCellChange = (categoryId: number, month: number, value: number) => {
    updateCellMutation.mutate({
      year,
      month,
      category_id: categoryId,
      planned_amount: value,
    })
  }

  const isCellUpdating = (categoryId: number, month: number): boolean => {
    return updatingCells.has(`${categoryId}-${month}`)
  }

  const handleExport = () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
    const url = `${apiUrl}/api/v1/budget/plans/year/${year}/export`
    window.open(url, '_blank')
    message.success('Экспорт начат. Файл скоро будет загружен.')
  }

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ru-RU').format(num)
  }

  useEffect(() => {
    setActiveMonth(year === currentYear ? currentMonth : 1)
  }, [year, currentYear, currentMonth])

  const updateScrollState = useCallback(() => {
    // Функция для обновления состояния прокрутки (может использоваться для кнопок навигации)
    const target = scrollTargetRef.current ?? scrollContainerRef.current
    if (!target) return
    // В будущем здесь можно добавить логику для кнопок навигации
  }, [])

  const resolveScrollTarget = useCallback(() => {
    const container = scrollContainerRef.current
    if (!container) return null
    const content = container.querySelector<HTMLDivElement>('.ant-table-content')
    const body = container.querySelector<HTMLDivElement>('.ant-table-body')
    return content ?? body ?? container
  }, [])

  const scrollToMonth = useCallback((month: number, behavior: ScrollBehavior = 'smooth', retryCount: number = 0) => {
    // Используем двойной requestAnimationFrame для гарантии полного рендеринга
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        setTimeout(() => {
          const target = scrollTargetRef.current ?? scrollContainerRef.current
          if (!target) {
            console.warn('Scroll target not found')
            return
          }

          // Проверяем, что таблица отрендерена
          const tableBody = target.querySelector('.ant-table-body')
          if (!tableBody && retryCount < 5) {
            console.warn(`Table body not found, retrying... (${retryCount + 1}/5)`)
            // Повторная попытка через 100мс (максимум 5 попыток)
            setTimeout(() => {
              const fn = (scrollToMonth as any) as (m: number, b: ScrollBehavior, r: number) => void
              fn(month, behavior, retryCount + 1)
            }, 100)
            return
          }

          const approximateCenterOffset = target.clientWidth * 0.25
          const columnOffset = Math.max(0, (month - 1) * MONTH_COLUMN_WIDTH - approximateCenterOffset)
          target.scrollTo({ left: columnOffset, behavior })
          requestAnimationFrame(updateScrollState)
        }, 200)
      })
    })
  }, [updateScrollState])

  const isInitialMount = useRef(true)

  useEffect(() => {
    const target = resolveScrollTarget()
    if (!target) return

    scrollTargetRef.current = target

    const handleScroll = () => updateScrollState()
    const handleResize = () => updateScrollState()

    updateScrollState()

    // Первичная прокрутка только при загрузке данных
    if (isInitialMount.current) {
      scrollToMonth(activeMonth, 'auto')
      isInitialMount.current = false
    }

    target.addEventListener('scroll', handleScroll, { passive: true })
    window.addEventListener('resize', handleResize)

    return () => {
      target.removeEventListener('scroll', handleScroll)
      window.removeEventListener('resize', handleResize)
    }
  }, [planData, resolveScrollTarget, updateScrollState, scrollToMonth, activeMonth])

  // Отдельный эффект для плавной прокрутки при переключении месяцев
  useEffect(() => {
    if (!planData || isInitialMount.current) return

    // Даём таблице время на рендер перед прокруткой
    const timer = setTimeout(() => {
      scrollToMonth(activeMonth, 'smooth')
    }, 50)

    return () => clearTimeout(timer)
  }, [activeMonth, planData, scrollToMonth])

  // Все хуки должны быть вызваны ПЕРЕД условными возвратами
  const scrollBy = useCallback(
    (direction: 'left' | 'right') => {
      const target = scrollTargetRef.current ?? scrollContainerRef.current
      if (!target) return
      const step = target.clientWidth * 0.6
      const delta = direction === 'left' ? -step : step
      target.scrollBy({ left: delta, behavior: 'smooth' })
      requestAnimationFrame(updateScrollState)
    },
    [updateScrollState]
  )

  React.useImperativeHandle(
    ref,
    () => ({
      scrollBy,
    }),
    [scrollBy]
  )

  const handleMonthSelect = useCallback(
    (month: number) => {
      setActiveMonth(month)
      scrollToMonth(month)
    },
    [scrollToMonth]
  )

  const handleResetMonth = useCallback(() => {
    const targetMonth = year === currentYear ? currentMonth : 1
    setActiveMonth(targetMonth)
    scrollToMonth(targetMonth)
  }, [year, currentYear, currentMonth, scrollToMonth])

  // Условные возвраты ПОСЛЕ всех хуков
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', minHeight: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" tip="Загрузка плана..." />
      </div>
    )
  }

  if (!planData || planData.categories.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <p>План на {year} год не найден</p>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => initMutation.mutate()}
          loading={initMutation.isPending}
        >
          Инициализировать план
        </Button>
      </div>
    )
  }

  // Группировка категорий по родителям
  const parentCategories = planData.categories.filter(cat => cat.parent_id === null)
  const childCategoriesMap = new Map<number, any[]>()

  planData.categories.forEach(cat => {
    if (cat.parent_id !== null) {
      if (!childCategoriesMap.has(cat.parent_id)) {
        childCategoriesMap.set(cat.parent_id, [])
      }
      childCategoriesMap.get(cat.parent_id)!.push(cat)
    }
  })

  // Функция для расчета итогов родительской категории
  const calculateParentTotals = (parentId: number) => {
    const children = childCategoriesMap.get(parentId) || []
    const months: any = {}

    for (let month = 1; month <= 12; month++) {
      const monthStr = month.toString()
      let planned = 0
      let actual = 0

      children.forEach(child => {
        planned += child.months[monthStr]?.planned_amount || 0
        actual += child.months[monthStr]?.actual_amount || 0
      })

      months[monthStr] = {
        planned_amount: planned,
        actual_amount: actual,
        remaining: planned - actual
      }
    }

    return months
  }

  const columns: any[] = [
    {
      title: 'Статья расходов',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 300,
      fixed: 'left',
      render: (text: string, record: any) => {
        const isParent = record.isParent === true
        const isChild = record.isChild === true
        const isTotal = record.key && (record.key.includes('total') || record.key === 'grand-total')

        return (
          <div style={{
            paddingLeft: isChild ? 24 : 0,
            display: 'flex',
            alignItems: 'center',
            gap: 8
          }}>
            {isChild && <span style={{ color: '#999', fontSize: 13 }}>└─</span>}
            <div style={{ flex: 1 }}>
              <div style={{
                fontWeight: isParent || isTotal ? 600 : 'normal',
                fontSize: 13,
                color: isParent ? '#1890ff' : 'inherit'
              }}>
                {text}
              </div>
              {isParent && (
                <Tag
                  color={record.category_type === 'OPEX' ? 'blue' : 'green'}
                  style={{ marginTop: 4, fontSize: 11 }}
                >
                  {record.category_type}
                </Tag>
              )}
            </div>
          </div>
        )
      },
    },
    ...Array.from({ length: 12 }, (_, i) => i + 1).map((month) => ({
      title: MONTH_NAMES[month - 1],
      key: `month-${month}`,
      width: MONTH_COLUMN_WIDTH,
      align: 'right' as const,
      className: activeMonth === month ? 'active-month-header' : undefined,
      onHeaderCell: () => ({
        className: activeMonth === month ? 'active-month-header' : undefined,
      }),
      children: [
        {
          title: <div style={{fontSize: 12, fontWeight: 500}}>План</div>,
          key: `month-${month}-plan`,
          width: 90,
          align: 'right' as const,
          onHeaderCell: () => ({
            className: activeMonth === month ? 'active-month-subheader' : undefined,
          }),
          onCell: () => ({
            className: activeMonth === month ? 'active-month-cell' : undefined,
          }),
          render: (_: any, record: any) => {
            const monthData = record.months[month.toString()]
            const isEditable = record.isChild === true
            const value = monthData?.planned_amount || 0

            if (isEditable) {
              return (
                <EditableCell
                  value={value}
                  onChange={(newValue) => handleCellChange(record.category_id, month, newValue)}
                  loading={isCellUpdating(record.category_id, month)}
                />
              )
            }
            return (
              <span style={{fontSize: 13, fontWeight: activeMonth === month ? 600 : 'normal'}}>
                {formatNumber(value)}
              </span>
            )
          },
        },
        {
          title: <div style={{fontSize: 12, fontWeight: 500}}>Факт</div>,
          key: `month-${month}-actual`,
          width: 90,
          align: 'right' as const,
          onHeaderCell: () => ({
            className: activeMonth === month ? 'active-month-subheader' : undefined,
          }),
          onCell: () => ({
            className: activeMonth === month ? 'active-month-cell' : undefined,
          }),
          render: (_: any, record: any) => {
            const monthData = record.months[month.toString()]
            const value = monthData?.actual_amount || 0
            return (
              <span style={{fontSize: 13, color: '#666', fontWeight: activeMonth === month ? 600 : 'normal'}}>
                {formatNumber(value)}
              </span>
            )
          },
        },
        {
          title: <div style={{fontSize: 12, fontWeight: 500}}>Остаток</div>,
          key: `month-${month}-remaining`,
          width: 90,
          align: 'right' as const,
          onHeaderCell: () => ({
            className: activeMonth === month ? 'active-month-subheader' : undefined,
          }),
          onCell: () => ({
            className: activeMonth === month ? 'active-month-cell' : undefined,
          }),
          render: (_: any, record: any) => {
            const monthData = record.months[month.toString()]
            const remaining = monthData?.remaining || 0
            const color = remaining < 0 ? '#ff4d4f' : (remaining > 0 ? '#52c41a' : '#666')
            return (
              <span
                style={{
                  fontSize: 13,
                  color,
                  fontWeight: remaining < 0 || activeMonth === month ? 'bold' : 'normal',
                }}
              >
                {formatNumber(remaining)}
              </span>
            )
          },
        },
      ]
    })),
    {
      title: 'Итого за год',
      key: 'total',
      width: 270,
      align: 'right' as const,
      fixed: 'right',
      children: [
        {
          title: <div style={{fontSize: 12, fontWeight: 500}}>План</div>,
          key: 'total-plan',
          width: 90,
          align: 'right' as const,
          render: (_: any, record: any) => {
            const total = Object.values(record.months).reduce((sum: number, m: any) => sum + (m.planned_amount || 0), 0)
            return <strong style={{ color: '#1890ff', fontSize: 13 }}>{formatNumber(total)}</strong>
          },
        },
        {
          title: <div style={{fontSize: 12, fontWeight: 500}}>Факт</div>,
          key: 'total-actual',
          width: 90,
          align: 'right' as const,
          render: (_: any, record: any) => {
            const total = Object.values(record.months).reduce((sum: number, m: any) => sum + (m.actual_amount || 0), 0)
            return <strong style={{ color: '#666', fontSize: 13 }}>{formatNumber(total)}</strong>
          },
        },
        {
          title: <div style={{fontSize: 12, fontWeight: 500}}>Остаток</div>,
          key: 'total-remaining',
          width: 90,
          align: 'right' as const,
          render: (_: any, record: any) => {
            const total = Object.values(record.months).reduce((sum: number, m: any) => sum + (m.remaining || 0), 0)
            const color = total < 0 ? '#ff4d4f' : (total > 0 ? '#52c41a' : '#666')
            return <strong style={{ color, fontSize: 13 }}>{formatNumber(total)}</strong>
          },
        },
      ]
    },
  ]

  // Построение dataSource с группировкой по родителям
  const dataSource: any[] = []

  parentCategories.forEach(parent => {
    // Добавляем родительскую категорию с агрегированными данными
    dataSource.push({
      key: `parent-${parent.category_id}`,
      category_id: parent.category_id,
      category_name: parent.category_name,
      category_type: parent.category_type,
      isParent: true,
      isChild: false,
      months: calculateParentTotals(parent.category_id),
    })

    // Добавляем дочерние категории
    const children = childCategoriesMap.get(parent.category_id) || []
    children.forEach(child => {
      dataSource.push({
        key: `child-${child.category_id}`,
        category_id: child.category_id,
        category_name: child.category_name,
        category_type: child.category_type,
        parent_id: child.parent_id,
        isParent: false,
        isChild: true,
        months: child.months,
      })
    })
  })

  // Строка итогов OPEX
  const opexCategories = planData.categories.filter(cat => cat.category_type === 'OPEX')
  const opexRow = {
    key: 'opex-total',
    category_name: 'ИТОГО OPEX',
    category_type: 'OPEX',
    isParent: false,
    isChild: false,
    months: Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
        const monthStr = month.toString()
        const planned = opexCategories.reduce((sum, cat) => sum + (cat.months[monthStr]?.planned_amount || 0), 0)
        const actual = opexCategories.reduce((sum, cat) => sum + (cat.months[monthStr]?.actual_amount || 0), 0)
        return [monthStr, { planned_amount: planned, actual_amount: actual, remaining: planned - actual }]
      })
    ),
  }

  // Строка итогов CAPEX
  const capexCategories = planData.categories.filter(cat => cat.category_type === 'CAPEX')
  const capexRow = {
    key: 'capex-total',
    category_name: 'ИТОГО CAPEX',
    category_type: 'CAPEX',
    isParent: false,
    isChild: false,
    months: Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
        const monthStr = month.toString()
        const planned = capexCategories.reduce((sum, cat) => sum + (cat.months[monthStr]?.planned_amount || 0), 0)
        const actual = capexCategories.reduce((sum, cat) => sum + (cat.months[monthStr]?.actual_amount || 0), 0)
        return [monthStr, { planned_amount: planned, actual_amount: actual, remaining: planned - actual }]
      })
    ),
  }

  // Строка общих итогов
  const grandTotalRow = {
    key: 'grand-total',
    category_name: 'ВСЕГО',
    category_type: '',
    isParent: false,
    isChild: false,
    months: Object.fromEntries(
      Array.from({ length: 12 }, (_, i) => i + 1).map((month) => {
        const monthStr = month.toString()
        const planned = planData.categories.reduce((sum, cat) => sum + (cat.months[monthStr]?.planned_amount || 0), 0)
        const actual = planData.categories.reduce((sum, cat) => sum + (cat.months[monthStr]?.actual_amount || 0), 0)
        return [monthStr, { planned_amount: planned, actual_amount: actual, remaining: planned - actual }]
      })
    ),
  }

  // Добавляем строки итогов в таблицу
  const dataWithTotals = [...dataSource, opexRow, capexRow, grandTotalRow]

  // Подсчет количества превышений бюджета
  const budgetOverruns = dataSource.filter(row => {
    if (!row.isChild) return false
    return Object.values(row.months).some((m: any) => m.remaining < 0)
  })

  const totalOverrunAmount = dataSource.reduce((sum, row) => {
    if (!row.isChild) return sum
    const rowOverrun = Object.values(row.months).reduce((rowSum: number, m: any) => {
      return rowSum + (m.remaining < 0 ? Math.abs(m.remaining) : 0)
    }, 0)
    return sum + rowOverrun
  }, 0)

  return (
    <div>
      {budgetOverruns.length > 0 && (
        <Alert
          message={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <WarningOutlined />
              <span>Превышение бюджета обнаружено</span>
            </div>
          }
          description={
            <div>
              <div>Категорий с превышением: <strong>{budgetOverruns.length}</strong></div>
              <div>Общая сумма превышения: <strong style={{ color: '#ff4d4f' }}>{formatNumber(totalOverrunAmount)} ₽</strong></div>
              <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                Ячейки с превышением отмечены красным цветом в столбце "Остаток"
              </div>
            </div>
          }
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Липкая панель управления */}
      <div
        style={{
          position: 'sticky',
          top: STICKY_HEADER_OFFSET,
          zIndex: 10,
          backgroundColor: '#fff',
          paddingTop: 12,
          paddingBottom: 12,
          marginBottom: 0,
          borderBottom: '2px solid #f0f0f0',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: 16,
            flexWrap: 'wrap',
            marginBottom: 12,
          }}
        >
          <Space size="middle" align="center" wrap>
            <span style={{ fontWeight: 500 }}>Месяц:</span>
            <div style={{ overflowX: 'auto', paddingBottom: 4 }}>
              <Segmented
                options={MONTH_SEGMENT_OPTIONS}
                value={activeMonth}
                onChange={(value) => handleMonthSelect(Number(value))}
              />
            </div>
          </Space>
          <Button
            type="link"
            icon={<CalendarOutlined />}
            onClick={handleResetMonth}
            style={{ padding: 0 }}
          >
            К текущему месяцу
          </Button>
        </div>

        <div>
          <Space>
            <Button
              icon={<CopyOutlined />}
              onClick={() => setCopyModalOpen(true)}
            >
              Скопировать из другого года
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              type="default"
            >
              Экспорт в Excel
            </Button>
          </Space>
        </div>
      </div>

      <div
        ref={scrollContainerRef}
        style={{ width: '100%', maxWidth: '100%', position: 'relative' }}
      >
        <Table
          sticky={{ offsetHeader: STICKY_HEADER_OFFSET + CONTROL_PANEL_HEIGHT }}
          columns={columns}
          dataSource={dataWithTotals}
          pagination={false}
          scroll={{ x: TABLE_SCROLL_WIDTH }}
          bordered
          size="small"
          rowClassName={(record) => {
            if (record.key === 'grand-total') return 'grand-total-row'
            if (record.key === 'opex-total' || record.key === 'capex-total') return 'subtotal-row'
            if (record.isParent === true) return 'parent-row'
            if (record.isChild === true) return 'child-row'
            return ''
          }}
        />
      </div>

      <CopyPlanModal
        open={copyModalOpen}
        targetYear={year}
        onClose={() => setCopyModalOpen(false)}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ['budget-plan', year] })
        }}
      />

      <style>{`
        .parent-row {
          background-color: #fafafa !important;
          font-weight: 500;
        }
        .parent-row:hover {
          background-color: #f0f0f0 !important;
        }
        .child-row {
          background-color: #ffffff !important;
        }
        .child-row:hover {
          background-color: #f5f5f5 !important;
        }
        .subtotal-row {
          background-color: #f0f5ff !important;
          font-weight: 600;
        }
        .grand-total-row {
          background-color: #e6f7ff !important;
          font-weight: 700;
          font-size: 14px;
        }
        .ant-table-cell {
          padding: 8px !important;
        }

        .active-month-header {
          background: linear-gradient(90deg, rgba(24, 144, 255, 0.18) 0%, rgba(24, 144, 255, 0.05) 100%) !important;
          color: #0958d9 !important;
          font-weight: 600 !important;
        }
        .active-month-subheader {
          background-color: rgba(24, 144, 255, 0.12) !important;
          color: #0958d9 !important;
          font-weight: 600 !important;
        }
        .active-month-cell {
          background-color: rgba(222, 242, 255, 0.7) !important;
          transition: background-color 0.2s ease;
        }
        .active-month-cell:hover {
          background-color: rgba(184, 218, 255, 0.8) !important;
        }

        .ant-table-sticky-holder {
          background: #fff;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
          z-index: 5;
        }
        .ant-table-sticky-scroll {
          display: none;
        }

        /* Плавная прокрутка */
        .ant-table-content {
          scroll-behavior: smooth;
        }

        .budget-scroll-button {
          width: 56px !important;
          height: 56px !important;
          border: none !important;
          background: linear-gradient(135deg, rgba(24, 144, 255, 0.95) 0%, rgba(69, 166, 255, 0.95) 100%) !important;
          color: #fff !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          box-shadow: 0 4px 16px rgba(24, 144, 255, 0.4), 0 8px 24px rgba(0, 0, 0, 0.15) !important;
          backdrop-filter: blur(8px);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          font-size: 20px !important;
        }
        .budget-scroll-button:hover {
          background: linear-gradient(135deg, rgba(24, 144, 255, 1) 0%, rgba(69, 166, 255, 1) 100%) !important;
          transform: translateY(-2px) scale(1.05);
          box-shadow: 0 6px 20px rgba(24, 144, 255, 0.5), 0 10px 30px rgba(0, 0, 0, 0.2) !important;
          color: #fff !important;
        }
        .budget-scroll-button:active {
          transform: translateY(0) scale(1);
          box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3), 0 4px 12px rgba(0, 0, 0, 0.1) !important;
        }
        .budget-scroll-button:disabled {
          opacity: 0.4;
          cursor: not-allowed;
          transform: none !important;
        }

        /* Прозрачная версия кнопок */
        .budget-scroll-button-transparent {
          background: rgba(255, 255, 255, 0.75) !important;
          color: #1890ff !important;
          border: 2px solid rgba(24, 144, 255, 0.3) !important;
          box-shadow: 0 2px 12px rgba(24, 144, 255, 0.15), 0 4px 16px rgba(0, 0, 0, 0.08) !important;
          backdrop-filter: blur(12px) saturate(180%);
        }
        .budget-scroll-button-transparent:hover {
          background: rgba(255, 255, 255, 0.9) !important;
          color: #0958d9 !important;
          border: 2px solid rgba(24, 144, 255, 0.6) !important;
          transform: translateY(-2px) scale(1.05);
          box-shadow: 0 4px 16px rgba(24, 144, 255, 0.25), 0 8px 24px rgba(0, 0, 0, 0.12) !important;
        }
        .budget-scroll-button-transparent:active {
          transform: translateY(0) scale(1);
          background: rgba(255, 255, 255, 0.85) !important;
          box-shadow: 0 1px 6px rgba(24, 144, 255, 0.2), 0 2px 8px rgba(0, 0, 0, 0.06) !important;
        }

        /* Голубая полоса прокрутки */
        ::-webkit-scrollbar {
          height: 16px !important;
          width: 16px !important;
        }

        ::-webkit-scrollbar-track {
          background: #f0f0f0 !important;
          border-radius: 8px !important;
        }

        ::-webkit-scrollbar-thumb {
          background: #1890ff !important;
          border-radius: 8px !important;
          border: 3px solid #f0f0f0 !important;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: #40a9ff !important;
        }

        /* Для Firefox */
        * {
          scrollbar-width: thin !important;
          scrollbar-color: #1890ff #f0f0f0 !important;
        }
      `}</style>
    </div>
  )
})

BudgetPlanTable.displayName = 'BudgetPlanTable'

export default BudgetPlanTable
