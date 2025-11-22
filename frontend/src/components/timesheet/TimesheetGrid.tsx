import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react'
import { Table, Tag, Typography, Space, Tooltip, theme, InputNumber, message, Spin, Dropdown } from 'antd'
import type { MenuProps } from 'antd'
import { CheckCircleOutlined, ClockCircleOutlined, DollarOutlined, WarningOutlined, LoadingOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import type { TimesheetGrid as TimesheetGridData, TimesheetGridEmployee } from '@/types/timesheet'
import type { DayType } from '@/types/timesheet'
import { DAY_TYPE_COLORS, DAY_TYPE_LABELS } from '@/types/timesheet'
import { useTheme } from '@/contexts/ThemeContext'
import { isWeekendOrHoliday, getHolidayName, isTransferredWorkday } from '@/utils/holidays'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { timesheetsApi } from '@/api/timesheets'

const { Text } = Typography

interface TimesheetGridProps {
  data: TimesheetGridData
  loading?: boolean
}

interface EditingCell {
  employeeId: number
  day: number
}

// Helper to get day of week name
const DAY_NAMES = ['Вс', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб']

const TimesheetGrid: React.FC<TimesheetGridProps> = ({ data, loading = false }) => {
  const { mode } = useTheme()
  const { token } = theme.useToken()
  const queryClient = useQueryClient()
  const tableRef = useRef<HTMLDivElement>(null)

  const isDark = mode === 'dark'

  // State for tracking which cell is being edited
  const [editingCell, setEditingCell] = useState<EditingCell | null>(null)
  const [savingCells, setSavingCells] = useState<Set<string>>(new Set())

  // Auto-scroll to today's column on mount
  useEffect(() => {
    const today = new Date()
    const currentYear = today.getFullYear()
    const currentMonth = today.getMonth() + 1
    const currentDay = today.getDate()

    // Only scroll if viewing current month
    if (data.year === currentYear && data.month === currentMonth) {
      // Small delay to ensure table is rendered
      const scrollTimer = setTimeout(() => {
        if (tableRef.current) {
          const tableBody = tableRef.current.querySelector('.ant-table-body')
          if (tableBody) {
            // Calculate horizontal scroll position
            // Each day column is 60px wide, plus 250px for fixed columns (№ + Сотрудник)
            const fixedColumnsWidth = 250
            const dayColumnWidth = 60
            const scrollPosition = fixedColumnsWidth + (currentDay - 1) * dayColumnWidth - 200 // offset to center

            tableBody.scrollTo({
              left: Math.max(0, scrollPosition),
              behavior: 'smooth',
            })
          }
        }
      }, 300)

      return () => clearTimeout(scrollTimer)
    }
  }, [data.year, data.month])

  // Helper to generate cell key
  const getCellKey = (employeeId: number, day: number) => `${employeeId}-${day}`

  // Mutation for creating timesheet (if it doesn't exist)
  const createTimesheetMutation = useMutation({
    mutationFn: async (params: { employeeId: number; year: number; month: number }) => {
      return timesheetsApi.createTimesheet({
        employee_id: params.employeeId,
        year: params.year,
        month: params.month,
      })
    },
    onError: (error: any) => {
      message.error(`Ошибка создания табеля: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Mutation for creating daily record
  const createDailyRecordMutation = useMutation({
    mutationFn: async (params: {
      timesheetId: string
      workDate: string
      hoursWorked: number
      dayType?: DayType
    }) => {
      return timesheetsApi.createDailyRecord({
        timesheet_id: params.timesheetId,
        work_date: params.workDate,
        is_working_day: true,
        hours_worked: params.hoursWorked,
        day_type: params.dayType || 'WORK',
      })
    },
    onSuccess: () => {
      // Refetch grid data
      queryClient.invalidateQueries({ queryKey: ['timesheets-grid'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка создания записи: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Mutation for updating daily record
  const updateDailyRecordMutation = useMutation({
    mutationFn: async (params: { recordId: string; hoursWorked?: number; dayType?: DayType }) => {
      return timesheetsApi.updateDailyRecord(params.recordId, {
        hours_worked: params.hoursWorked,
        day_type: params.dayType,
      })
    },
    onSuccess: () => {
      // Refetch grid data
      queryClient.invalidateQueries({ queryKey: ['timesheets-grid'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления записи: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Bulk fill day - fill 8 hours for all employees on specific day
  const handleBulkFillDay = useCallback(
    async (day: number) => {
      const editableEmployees = data.employees.filter(emp => emp.can_edit)

      if (editableEmployees.length === 0) {
        message.warning('Нет доступных для редактирования табелей')
        return
      }

      const confirmText = `Заполнить 8 часов для всех сотрудников (${editableEmployees.length} чел.) на ${day} число?`

      // Simple confirm without modal
      if (!window.confirm(confirmText)) {
        return
      }

      const promises = editableEmployees.map(async (employee) => {
        try {
          const dayData = employee.days[day - 1]

          // Check if timesheet exists
          if (!employee.timesheet_id) {
            // Create timesheet first
            const timesheet = await createTimesheetMutation.mutateAsync({
              employeeId: employee.employee_id,
              year: data.year,
              month: data.month,
            })

            // Create daily record with 8 hours and WORK day type
            await createDailyRecordMutation.mutateAsync({
              timesheetId: timesheet.id,
              workDate: dayData.date,
              hoursWorked: 8,
              dayType: 'WORK',
            })
          } else if (dayData?.record_id) {
            // Update existing record to 8 hours
            await updateDailyRecordMutation.mutateAsync({
              recordId: dayData.record_id,
              hoursWorked: 8,
            })
          } else {
            // Create new daily record with 8 hours and WORK day type
            await createDailyRecordMutation.mutateAsync({
              timesheetId: employee.timesheet_id,
              workDate: dayData.date,
              hoursWorked: 8,
              dayType: 'WORK',
            })
          }
        } catch (error) {
          // Error already handled by mutations
          return Promise.reject(error)
        }
      })

      try {
        await Promise.all(promises)
        message.success(`Установлено 8 часов для ${editableEmployees.length} сотрудников`)
      } catch (error) {
        message.error('Некоторые записи не удалось обновить')
      }
    },
    [data, createTimesheetMutation, createDailyRecordMutation, updateDailyRecordMutation]
  )

  // Handle day type change via context menu
  const handleDayTypeChange = useCallback(
    async (employee: TimesheetGridEmployee, day: number, dayType: DayType) => {
      const dayData = employee.days[day - 1]

      if (!dayData?.record_id) {
        message.warning('Сначала создайте запись для этого дня')
        return
      }

      try {
        await updateDailyRecordMutation.mutateAsync({
          recordId: dayData.record_id,
          dayType,
        })
        message.success(`Тип дня изменен на "${DAY_TYPE_LABELS[dayType]}"`)
      } catch (error) {
        // Error handled by mutation
      }
    },
    [updateDailyRecordMutation]
  )

  // Handle cell click - set 8 hours by default
  const handleCellClick = useCallback(
    async (employee: TimesheetGridEmployee, day: number) => {
      // Check if editing is allowed
      if (!employee.can_edit) {
        message.warning('Редактирование недоступно для данного табеля')
        return
      }

      const cellKey = getCellKey(employee.employee_id, day)

      // Prevent clicking if already saving
      if (savingCells.has(cellKey)) {
        return
      }

      const dayData = employee.days[day - 1]

      // If record already exists with hours, just enable editing
      if (dayData?.record_id && dayData.hours_worked > 0) {
        setEditingCell({ employeeId: employee.employee_id, day })
        return
      }

      // Otherwise, create/update with 8 hours
      setSavingCells((prev) => new Set(prev).add(cellKey))

      try {
        // Check if timesheet exists
        if (!employee.timesheet_id) {
          // Create timesheet first
          const timesheet = await createTimesheetMutation.mutateAsync({
            employeeId: employee.employee_id,
            year: data.year,
            month: data.month,
          })

          // Create daily record with 8 hours and WORK day type
          await createDailyRecordMutation.mutateAsync({
            timesheetId: timesheet.id,
            workDate: dayData.date,
            hoursWorked: 8,
            dayType: 'WORK',
          })
        } else if (dayData?.record_id) {
          // Update existing record to 8 hours
          await updateDailyRecordMutation.mutateAsync({
            recordId: dayData.record_id,
            hoursWorked: 8,
          })
        } else {
          // Create new daily record with 8 hours and WORK day type
          await createDailyRecordMutation.mutateAsync({
            timesheetId: employee.timesheet_id,
            workDate: dayData.date,
            hoursWorked: 8,
            dayType: 'WORK',
          })
        }

        message.success('Установлено 8 часов')
      } catch (error) {
        // Error already handled by mutations
      } finally {
        setSavingCells((prev) => {
          const next = new Set(prev)
          next.delete(cellKey)
          return next
        })
      }
    },
    [data.year, data.month, createTimesheetMutation, createDailyRecordMutation, updateDailyRecordMutation, savingCells]
  )

  // Handle value change in input
  const handleValueChange = useCallback(
    async (employee: TimesheetGridEmployee, day: number, value: number | null) => {
      if (value === null || value < 0) {
        return
      }

      const dayData = employee.days[day - 1]
      const cellKey = getCellKey(employee.employee_id, day)

      setSavingCells((prev) => new Set(prev).add(cellKey))
      setEditingCell(null)

      try {
        if (dayData?.record_id) {
          // Update existing record
          await updateDailyRecordMutation.mutateAsync({
            recordId: dayData.record_id,
            hoursWorked: value,
          })
        } else if (employee.timesheet_id) {
          // Create new record
          await createDailyRecordMutation.mutateAsync({
            timesheetId: employee.timesheet_id,
            workDate: dayData.date,
            hoursWorked: value,
          })
        }
      } catch (error) {
        // Error already handled by mutations
      } finally {
        setSavingCells((prev) => {
          const next = new Set(prev)
          next.delete(cellKey)
          return next
        })
      }
    },
    [updateDailyRecordMutation, createDailyRecordMutation]
  )

  // Generate columns for each day of the month
  const dayColumns = useMemo(() => {
    const columns: ColumnsType<TimesheetGridEmployee> = []

    for (let day = 1; day <= data.calendar_days_in_month; day++) {
      // Check if this day is weekend or holiday
      const isHoliday = isWeekendOrHoliday(data.year, data.month, day)
      const holidayName = getHolidayName(data.year, data.month, day)
      const isTransferred = isTransferredWorkday(data.year, data.month, day)

      // Column background colors
      const columnBgColor = isHoliday
        ? isDark
          ? 'rgba(255, 77, 79, 0.15)'  // Red tint for dark mode
          : '#fff1f0'                    // Light red for light mode
        : isDark
        ? token.colorBgContainer
        : '#ffffff'

      // Calculate day of week for this day
      const dayDate = new Date(data.year, data.month - 1, day)
      const dayOfWeekIndex = dayDate.getDay() // 0 = Sunday, 6 = Saturday
      const dayOfWeekName = DAY_NAMES[dayOfWeekIndex]

      columns.push({
        title: () => (
          <Tooltip title="Клик = заполнить 8 часов для всех">
            <div
              onClick={() => handleBulkFillDay(day)}
              style={{
                textAlign: 'center',
                cursor: 'pointer',
                padding: '4px 0',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = isDark ? 'rgba(24, 144, 255, 0.2)' : '#e6f7ff'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <div style={{ fontSize: 12, fontWeight: 600 }}>
                {day}
                {isTransferred && (
                  <Tooltip title="Рабочий день (перенос)">
                    <WarningOutlined style={{ marginLeft: 4, fontSize: 10, color: '#faad14' }} />
                  </Tooltip>
                )}
              </div>
              <div style={{ fontSize: 10, fontWeight: 400, opacity: 0.7, marginTop: 2 }}>
                {dayOfWeekName}
              </div>
            </div>
          </Tooltip>
        ),
        dataIndex: ['days', day - 1],
        key: `day-${day}`,
        width: 60,
        align: 'center',
        className: isHoliday ? 'timesheet-holiday-column' : undefined,
        onHeaderCell: () => ({
          style: {
            backgroundColor: columnBgColor,
            borderRight: isHoliday ? `2px solid ${isDark ? '#ff4d4f' : '#ff7875'}` : undefined,
          },
        }),
        onCell: () => ({
          style: {
            backgroundColor: columnBgColor,
            borderRight: isHoliday ? `2px solid ${isDark ? '#ff4d4f' : '#ff7875'}` : undefined,
          },
        }),
        render: (_, record) => {
          const dayData = record.days[day - 1]
          if (!dayData) return <div style={{ color: isDark ? '#666' : '#999' }}>-</div>

          const dayOfWeek = dayData.day_of_week
          const hours = dayData.hours_worked
          const cellKey = getCellKey(record.employee_id, day)
          const isSaving = savingCells.has(cellKey)
          const isEditing = editingCell?.employeeId === record.employee_id && editingCell?.day === day

          // Get day_type color (default to WORK if not set)
          const dayTypeKey = (dayData.day_type || 'WORK') as DayType
          const dayTypeColor = DAY_TYPE_COLORS[dayTypeKey]

          // Cell styles - use day_type color if hours > 0
          const cellBgColor = hours > 0
            ? isDark
              ? dayTypeColor.bgDark
              : dayTypeColor.bg
            : 'transparent'

          const tooltipContent = (
            <div>
              <div><strong>{DAY_NAMES[dayOfWeek - 1]}</strong></div>
              {dayData.day_type && (
                <div style={{ marginTop: 4 }}>
                  Тип: {DAY_TYPE_LABELS[dayData.day_type as DayType]}
                </div>
              )}
              {holidayName && (
                <div style={{ marginTop: 4, color: '#ff7875' }}>
                  🎉 {holidayName}
                </div>
              )}
              {isTransferred && (
                <div style={{ marginTop: 4, color: '#faad14' }}>
                  ⚠️ Перенесенный рабочий день
                </div>
              )}
              {dayData.notes && (
                <div style={{ marginTop: 4, fontSize: 11 }}>{dayData.notes}</div>
              )}
              {record.can_edit && (
                <div style={{ marginTop: 4, fontSize: 11, color: '#1890ff' }}>
                  Клик = 8 часов | ПКМ = тип дня
                </div>
              )}
            </div>
          )

          // Context menu items for day type selection
          const dayTypeMenuItems: MenuProps['items'] = Object.entries(DAY_TYPE_LABELS).map(([key, label]) => ({
            key,
            label,
            onClick: () => handleDayTypeChange(record, day, key as DayType),
          }))

          // Show loading spinner when saving
          if (isSaving) {
            return (
              <div style={{ padding: '4px', textAlign: 'center' }}>
                <Spin indicator={<LoadingOutlined style={{ fontSize: 14 }} spin />} />
              </div>
            )
          }

          // Show input when editing
          if (isEditing) {
            return (
              <InputNumber
                autoFocus
                size="small"
                min={0}
                max={24}
                step={0.5}
                defaultValue={hours || 8}
                style={{ width: '100%' }}
                onBlur={(e) => {
                  const value = parseFloat(e.target.value)
                  if (!isNaN(value)) {
                    handleValueChange(record, day, value)
                  } else {
                    setEditingCell(null)
                  }
                }}
                onPressEnter={(e) => {
                  const value = parseFloat((e.target as HTMLInputElement).value)
                  if (!isNaN(value)) {
                    handleValueChange(record, day, value)
                  }
                }}
              />
            )
          }

          // Show clickable display
          return (
            <Dropdown
              menu={{ items: dayTypeMenuItems }}
              trigger={['contextMenu']}
              disabled={!record.can_edit || !dayData.record_id}
            >
              <Tooltip title={tooltipContent}>
                <div
                  onClick={() => handleCellClick(record, day)}
                  onContextMenu={(e) => {
                    if (record.can_edit && dayData.record_id) {
                      e.preventDefault()
                    }
                  }}
                  style={{
                    padding: '4px',
                    backgroundColor: cellBgColor,
                    borderRadius: 4,
                    fontSize: 13,
                    fontWeight: hours > 0 ? 600 : 400,
                    color: hours > 0
                      ? isDark ? token.colorText : '#000'
                      : isDark ? '#666' : '#999',
                    cursor: record.can_edit ? 'pointer' : 'default',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    if (record.can_edit && hours > 0) {
                      const brightness = isDark ? 1.3 : 0.85
                      e.currentTarget.style.filter = `brightness(${brightness})`
                    }
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.filter = 'none'
                  }}
                >
                  {hours > 0 ? hours : '-'}
                </div>
              </Tooltip>
            </Dropdown>
          )
        },
      })
    }

    return columns
  }, [
    data.calendar_days_in_month,
    data.year,
    data.month,
    isDark,
    token,
    editingCell,
    savingCells,
    handleCellClick,
    handleValueChange,
  ])

  const columns: ColumnsType<TimesheetGridEmployee> = [
    {
      title: '№',
      key: 'index',
      width: 50,
      fixed: 'left',
      render: (_, __, index) => index + 1,
    },
    {
      title: 'Сотрудник',
      key: 'employee',
      width: 200,
      fixed: 'left',
      render: (_, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.employee_full_name}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {record.employee_position}
          </Text>
          {record.employee_number && (
            <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>
              №{record.employee_number}
            </Text>
          )}
        </div>
      ),
    },
    ...dayColumns,
    {
      title: 'Всего дней',
      key: 'total_days',
      width: 100,
      fixed: 'right',
      align: 'center',
      render: (_, record) => (
        <div style={{ fontWeight: 600, fontSize: 14 }}>
          {record.total_days_worked}
        </div>
      ),
    },
    {
      title: 'Всего часов',
      key: 'total_hours',
      width: 100,
      fixed: 'right',
      align: 'center',
      render: (_, record) => (
        <div style={{ fontWeight: 600, fontSize: 14, color: '#1890ff' }}>
          {record.total_hours_worked}
        </div>
      ),
    },
    {
      title: 'Статус',
      key: 'status',
      width: 120,
      fixed: 'right',
      align: 'center',
      render: (_, record) => {
        if (!record.timesheet_status) {
          return (
            <Tag
              color="default"
              style={{
                backgroundColor: isDark ? 'rgba(255,255,255,0.08)' : undefined,
                borderColor: isDark ? token.colorBorder : undefined,
              }}
            >
              Не создан
            </Tag>
          )
        }

        const statusLabels: Record<string, string> = {
          DRAFT: 'Черновик',
          APPROVED: 'Утвержден',
          PAID: 'Оплачен',
        }

        const statusColors: Record<string, string> = {
          DRAFT: 'default',
          APPROVED: 'processing',
          PAID: 'success',
        }

        const statusIcons: Record<string, React.ReactNode> = {
          DRAFT: <ClockCircleOutlined />,
          APPROVED: <CheckCircleOutlined />,
          PAID: <DollarOutlined />,
        }

        return (
          <Tag
            color={statusColors[record.timesheet_status] || 'default'}
            icon={statusIcons[record.timesheet_status]}
          >
            {statusLabels[record.timesheet_status] || record.timesheet_status}
          </Tag>
        )
      },
    },
  ]

  // Calculate summary row
  const summaryRow = useMemo(() => {
    if (!data.employees.length) return null

    // Count unique PAID days (ONLY day_type = 'WORK', strictly)
    const paidDaysSet = new Set<number>()
    data.employees.forEach((emp) => {
      emp.days.forEach((dayData, index) => {
        // Count ONLY days with explicit day_type = 'WORK'
        // Default to 'WORK' if day_type is missing (for backward compatibility)
        const dayType = dayData?.day_type || 'WORK'
        if (dayData && dayData.hours_worked > 0 && dayType === 'WORK') {
          paidDaysSet.add(index + 1) // day number
        }
      })
    })
    const uniquePaidDays = paidDaysSet.size

    const totalHours = data.employees.reduce((sum, emp) => {
      const hours = typeof emp.total_hours_worked === 'string'
        ? parseFloat(emp.total_hours_worked)
        : emp.total_hours_worked
      return sum + (hours || 0)
    }, 0)

    return {
      employee_full_name: 'ИТОГО',
      total_days_worked: uniquePaidDays,
      total_hours_worked: Number(totalHours).toFixed(1).replace(/\.0$/, ''),
    }
  }, [data.employees])

  return (
    <div ref={tableRef}>
      {/* Summary header */}
      <div
        style={{
          marginBottom: 16,
          padding: 12,
          backgroundColor: isDark ? token.colorBgElevated : '#f5f5f5',
          borderRadius: 8,
          border: isDark ? `1px solid ${token.colorBorder}` : 'none',
        }}
      >
        <Space size="large" wrap>
          <span>
            <Text strong>Всего сотрудников:</Text> {data.employees.length}
          </span>
          <span>
            <Text strong>Рабочих дней в месяце:</Text> {data.working_days_in_month}
          </span>
          <span>
            <Text strong>Всего рабочих часов в месяце:</Text>{' '}
            <Text style={{ fontSize: 16, fontWeight: 600, color: '#faad14' }}>
              {data.working_days_in_month * 8}
            </Text>
          </span>
          {summaryRow && (
            <>
              <span>
                <Text strong>Всего отработано дней:</Text>{' '}
                <Text style={{ fontSize: 16, fontWeight: 600, color: token.colorPrimary }}>
                  {summaryRow.total_days_worked}
                </Text>
              </span>
              <span>
                <Text strong>Всего отработано часов:</Text>{' '}
                <Text style={{ fontSize: 16, fontWeight: 600, color: token.colorSuccess }}>
                  {typeof summaryRow.total_hours_worked === 'string'
                    ? summaryRow.total_hours_worked
                    : Number(summaryRow.total_hours_worked).toFixed(1).replace(/\.0$/, '')}
                </Text>
              </span>
            </>
          )}
        </Space>
      </div>

      {/* Day types legend */}
      <div
        style={{
          marginBottom: 16,
          padding: 12,
          backgroundColor: isDark ? token.colorBgElevated : '#fafafa',
          borderRadius: 8,
          border: isDark ? `1px solid ${token.colorBorder}` : '1px solid #e8e8e8',
        }}
      >
        <Text strong style={{ marginRight: 16 }}>Легенда:</Text>
        <Space size="middle" wrap>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 20,
              height: 20,
              backgroundColor: isDark ? DAY_TYPE_COLORS.WORK.bgDark : DAY_TYPE_COLORS.WORK.bg,
              border: '1px solid #d9d9d9',
              borderRadius: 4
            }} />
            <Text style={{ fontSize: 13 }}>{DAY_TYPE_COLORS.WORK.label}</Text>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 20,
              height: 20,
              backgroundColor: isDark ? DAY_TYPE_COLORS.UNPAID_LEAVE.bgDark : DAY_TYPE_COLORS.UNPAID_LEAVE.bg,
              border: '1px solid #d9d9d9',
              borderRadius: 4
            }} />
            <Text style={{ fontSize: 13 }}>{DAY_TYPE_COLORS.UNPAID_LEAVE.label}</Text>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 20,
              height: 20,
              backgroundColor: isDark ? DAY_TYPE_COLORS.SICK_LEAVE.bgDark : DAY_TYPE_COLORS.SICK_LEAVE.bg,
              border: '1px solid #d9d9d9',
              borderRadius: 4
            }} />
            <Text style={{ fontSize: 13 }}>{DAY_TYPE_COLORS.SICK_LEAVE.label}</Text>
          </span>
        </Space>
      </div>

      {/* Main table */}
      <Table
        columns={columns}
        dataSource={data.employees}
        rowKey="employee_id"
        loading={loading}
        pagination={false}
        scroll={{ x: 250 + data.calendar_days_in_month * 60 + 420, y: 600 }}
        size="small"
        bordered
        sticky={{ offsetHeader: 64 }}
        summary={() => {
          if (!summaryRow) return null

          return (
            <Table.Summary fixed>
              <Table.Summary.Row
                style={{
                  backgroundColor: isDark ? token.colorBgElevated : '#fafafa',
                  fontWeight: 600,
                }}
              >
                <Table.Summary.Cell index={0} colSpan={2}>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>ИТОГО</div>
                </Table.Summary.Cell>
                {Array.from({ length: data.calendar_days_in_month }).map((_, day) => {
                  const dayTotal = data.employees.reduce((sum, emp) => {
                    const dayData = emp.days[day]
                    const hours = dayData?.hours_worked || 0
                    // Convert to number if it's a string
                    return sum + (typeof hours === 'string' ? parseFloat(hours) : hours)
                  }, 0)

                  // Check if this day is weekend or holiday for border styling
                  const isHoliday = isWeekendOrHoliday(data.year, data.month, day + 1)

                  return (
                    <Table.Summary.Cell
                      key={`summary-day-${day}`}
                      index={day + 2}
                      align="center"
                    >
                      <div
                        style={{
                          fontWeight: dayTotal > 0 ? 700 : 400,
                          color: dayTotal > 0 ? token.colorText : isDark ? '#666' : '#999',
                          backgroundColor: isHoliday
                            ? isDark
                              ? 'rgba(255, 77, 79, 0.15)'
                              : '#fff1f0'
                            : undefined,
                          borderRight: isHoliday
                            ? `2px solid ${isDark ? '#ff4d4f' : '#ff7875'}`
                            : undefined,
                        }}
                      >
                        {dayTotal > 0 ? Number(dayTotal).toFixed(1).replace(/\.0$/, '') : '-'}
                      </div>
                    </Table.Summary.Cell>
                  )
                })}
                <Table.Summary.Cell index={data.calendar_days_in_month + 2} align="center">
                  <div style={{ fontWeight: 700, fontSize: 14 }}>
                    {summaryRow.total_days_worked}
                  </div>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={data.calendar_days_in_month + 3} align="center">
                  <div style={{ fontWeight: 700, fontSize: 14, color: token.colorPrimary }}>
                    {typeof summaryRow.total_hours_worked === 'string'
                      ? summaryRow.total_hours_worked
                      : Number(summaryRow.total_hours_worked).toFixed(1).replace(/\.0$/, '')}
                  </div>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={data.calendar_days_in_month + 4} />
              </Table.Summary.Row>
            </Table.Summary>
          )
        }}
      />
    </div>
  )
}

export default TimesheetGrid
