import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Typography, Card, Button, Space, Select, message, Spin, Table,
  InputNumber, Input, Popconfirm, Tag, Modal, Form, DatePicker
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, ReloadOutlined, EditOutlined,
  CheckOutlined, CloseOutlined, ThunderboltOutlined, DownloadOutlined
} from '@ant-design/icons'
import { forecastApi, categoriesApi, contractorsApi, organizationsApi } from '@/api'
import type { ForecastExpense, BudgetCategory, Contractor, Organization } from '@/types'
import { useAuth } from '@/contexts/AuthContext'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs, { Dayjs } from 'dayjs'

const { Title, Paragraph } = Typography
const { Option } = Select

const ForecastPage = () => {
  const currentDate = dayjs()
  const nextMonth = currentDate.add(1, 'month')
  const { user } = useAuth()
  const { selectedDepartment } = useDepartment()

  const [selectedYear, setSelectedYear] = useState(nextMonth.year())
  const [selectedMonth, setSelectedMonth] = useState(nextMonth.month() + 1)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editingData, setEditingData] = useState<Partial<ForecastExpense> | null>(null)
  const [addModalVisible, setAddModalVisible] = useState(false)
  const [addForm] = Form.useForm()

  const queryClient = useQueryClient()

  // Load data
  const departmentId = selectedDepartment?.id || user?.department_id
  const { data: forecasts, isLoading } = useQuery({
    queryKey: ['forecasts', selectedYear, selectedMonth, departmentId],
    queryFn: () => forecastApi.getAll(selectedYear, selectedMonth, departmentId!),
    enabled: !!departmentId,
  })

  const { data: categories } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll(),
  })

  const { data: contractors } = useQuery({
    queryKey: ['contractors', departmentId],
    queryFn: () => contractorsApi.getAll({ limit: 1000, department_id: departmentId }),
    enabled: !!departmentId,
  })

  const { data: organizations } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.getAll({ limit: 100 }),
  })

  // Mutations
  const generateMutation = useMutation({
    mutationFn: () => forecastApi.generate({
      target_year: selectedYear,
      target_month: selectedMonth,
      department_id: departmentId!,
      include_regular: true,
      include_average: true,
    }),
    onSuccess: (data) => {
      message.success(`Прогноз создан! Добавлено: ${data.created} позиций`)
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка генерации: ${error.message}`)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ForecastExpense> }) =>
      forecastApi.update(id, data),
    onSuccess: () => {
      message.success('Прогноз обновлен')
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
      setEditingId(null)
      setEditingData(null)
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления: ${error.message}`)
    },
  })

  const createMutation = useMutation({
    mutationFn: (data: Partial<ForecastExpense>) => forecastApi.create(data),
    onSuccess: () => {
      message.success('Прогноз добавлен')
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
      setAddModalVisible(false)
      addForm.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка создания: ${error.message}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => forecastApi.delete(id),
    onSuccess: () => {
      message.success('Прогноз удален')
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления: ${error.message}`)
    },
  })

  const clearMutation = useMutation({
    mutationFn: () => forecastApi.clear(selectedYear, selectedMonth, departmentId!),
    onSuccess: () => {
      message.success('Прогнозы очищены')
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка очистки: ${error.message}`)
    },
  })

  const handleSaveEdit = (id: number) => {
    if (!editingData) return

    console.log('=== handleSaveEdit DEBUG ===')
    console.log('editingData:', editingData)

    // Удаляем поля, которые не нужны для обновления (read-only)
    const { category, contractor, organization, created_at, updated_at, ...dataToSend } = editingData as any

    console.log('dataToSend (final):', dataToSend)

    updateMutation.mutate({
      id,
      data: dataToSend
    })
  }

  const handleAddForecast = () => {
    addForm.validateFields().then(values => {
      createMutation.mutate({
        ...values,
        department_id: departmentId!,
        forecast_date: values.forecast_date.format('YYYY-MM-DD'),
      })
    })
  }

  const handleExportToExcel = async () => {
    try {
      const blob = await forecastApi.exportToExcel(selectedYear, selectedMonth, departmentId)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Планирование_${selectedMonth.toString().padStart(2, '0')}.${selectedYear}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      message.success('Файл Excel успешно скачан')
    } catch (error) {
      message.error('Ошибка при экспорте в Excel')
      console.error('Export error:', error)
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  // Generate days for the selected month
  const daysInMonth = dayjs(`${selectedYear}-${selectedMonth}-01`).daysInMonth()
  const monthDays = Array.from({ length: daysInMonth }, (_, i) => i + 1)

  // Group forecasts by day
  const forecastsByDay: Record<number, ForecastExpense[]> = {}
  forecasts?.forEach(f => {
    const day = dayjs(f.forecast_date).date()
    if (!forecastsByDay[day]) {
      forecastsByDay[day] = []
    }
    forecastsByDay[day].push(f)
  })

  const columns = [
    {
      title: 'Статья ДДС',
      dataIndex: ['category', 'name'],
      key: 'category',
      width: 200,
      ellipsis: true,
      render: (text: string, record: ForecastExpense) => {
        if (editingId === record.id) {
          return (
            <Select
              value={editingData?.category_id}
              onChange={(value) => setEditingData({ ...editingData, category_id: value })}
              style={{ width: '100%' }}
              showSearch
              filterOption={(input, option) =>
                (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {categories?.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.name}</Option>
              ))}
            </Select>
          )
        }
        return (
          <div>
            {text}
            {record.is_regular && (
              <Tag color="blue" style={{ marginLeft: 8 }}>Регулярный</Tag>
            )}
          </div>
        )
      },
    },
    {
      title: 'Контрагент',
      dataIndex: ['contractor', 'name'],
      key: 'contractor',
      width: 150,
      ellipsis: true,
      render: (text: string, record: ForecastExpense) => {
        if (editingId === record.id) {
          return (
            <Select
              value={editingData?.contractor_id}
              onChange={(value) => setEditingData({ ...editingData, contractor_id: value })}
              style={{ width: '100%' }}
              showSearch
              allowClear
              filterOption={(input, option) =>
                (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {contractors?.map(contractor => (
                <Option key={contractor.id} value={contractor.id}>{contractor.name}</Option>
              ))}
            </Select>
          )
        }
        return text || '—'
      },
    },
    {
      title: 'Дата',
      dataIndex: 'forecast_date',
      key: 'forecast_date',
      width: 100,
      render: (date: string, record: ForecastExpense) => {
        if (editingId === record.id) {
          return (
            <DatePicker
              value={dayjs(editingData?.forecast_date)}
              onChange={(date) => setEditingData({ ...editingData, forecast_date: date?.format('YYYY-MM-DD') })}
              format="DD.MM.YYYY"
            />
          )
        }
        return dayjs(date).format('DD.MM.YYYY')
      },
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      align: 'right' as const,
      render: (amount: number, record: ForecastExpense) => {
        if (editingId === record.id) {
          return (
            <InputNumber
              value={editingData?.amount}
              onChange={(value) => setEditingData({ ...editingData, amount: value || 0 })}
              style={{ width: '100%' }}
              min={0}
              precision={2}
            />
          )
        }
        return formatCurrency(amount)
      },
    },
    {
      title: 'Комментарий',
      dataIndex: 'comment',
      key: 'comment',
      ellipsis: true,
      render: (text: string, record: ForecastExpense) => {
        if (editingId === record.id) {
          return (
            <Input
              value={editingData?.comment}
              onChange={(e) => setEditingData({ ...editingData, comment: e.target.value })}
              placeholder="Комментарий"
            />
          )
        }
        return text || '—'
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      fixed: 'right' as const,
      render: (_: any, record: ForecastExpense) => {
        if (editingId === record.id) {
          return (
            <Space size="small">
              <Button
                type="primary"
                size="small"
                icon={<CheckOutlined />}
                onClick={() => handleSaveEdit(record.id)}
                loading={updateMutation.isPending}
              >
                Сохранить
              </Button>
              <Button
                size="small"
                icon={<CloseOutlined />}
                onClick={() => {
                  setEditingId(null)
                  setEditingData(null)
                }}
              >
                Отмена
              </Button>
            </Space>
          )
        }

        return (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => {
                setEditingId(record.id)
                setEditingData({
                  category_id: record.category_id,
                  contractor_id: record.contractor_id,
                  organization_id: record.organization_id,
                  forecast_date: record.forecast_date,
                  amount: record.amount,
                  comment: record.comment,
                  department_id: departmentId!,
                })
              }}
            >
              Изменить
            </Button>
            <Popconfirm
              title="Удалить прогноз?"
              onConfirm={() => deleteMutation.mutate(record.id)}
              okText="Удалить"
              cancelText="Отмена"
            >
              <Button
                type="link"
                danger
                size="small"
                icon={<DeleteOutlined />}
              >
                Удалить
              </Button>
            </Popconfirm>
          </Space>
        )
      },
    },
  ]

  const totalAmount = forecasts?.reduce((sum, f) => sum + Number(f.amount), 0) || 0

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Прогноз расходов</Title>
        <Paragraph>
          Планирование расходов на следующий месяц на основе регулярных платежей и средних значений.
        </Paragraph>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <Space>
            <span style={{ fontWeight: 500 }}>Период:</span>
            <Select
              value={selectedMonth}
              onChange={setSelectedMonth}
              style={{ width: 150 }}
            >
              {Array.from({ length: 12 }, (_, i) => i + 1).map(m => (
                <Option key={m} value={m}>
                  {dayjs().month(m - 1).format('MMMM')}
                </Option>
              ))}
            </Select>
            <Select
              value={selectedYear}
              onChange={setSelectedYear}
              style={{ width: 120 }}
            >
              {Array.from({ length: 3 }, (_, i) => currentDate.year() + i).map(y => (
                <Option key={y} value={y}>{y}</Option>
              ))}
            </Select>
          </Space>

          <Space>
            <Button
              icon={<ThunderboltOutlined />}
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
              type="primary"
            >
              Сгенерировать прогноз
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={() => setAddModalVisible(true)}
            >
              Добавить
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExportToExcel}
              type="default"
            >
              Экспорт в Excel
            </Button>
            <Popconfirm
              title="Очистить все прогнозы на этот месяц?"
              onConfirm={() => clearMutation.mutate()}
              okText="Очистить"
              cancelText="Отмена"
            >
              <Button
                icon={<DeleteOutlined />}
                danger
              >
                Очистить месяц
              </Button>
            </Popconfirm>
          </Space>
        </div>
      </Card>

      {forecasts && forecasts.length > 0 ? (
        <>
          <Card
            title={
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span>Прогнозные расходы</span>
                <Tag color="blue" style={{ fontSize: 16, padding: '4px 12px' }}>
                  Итого: {formatCurrency(totalAmount)}
                </Tag>
              </div>
            }
          >
            <Table
              columns={columns}
              dataSource={forecasts}
              rowKey="id"
              pagination={false}
              scroll={{ x: 1200 }}
              size="small"
              rowClassName={(record) => record.is_regular ? 'regular-row' : ''}
            />
          </Card>

          <style>{`
            .regular-row {
              background-color: #f0f5ff !important;
            }
            .regular-row:hover {
              background-color: #e6f0ff !important;
            }
          `}</style>
        </>
      ) : (
        <Card>
          <div style={{ textAlign: 'center', padding: '50px' }}>
            <Paragraph>Нет прогнозов на выбранный месяц</Paragraph>
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
            >
              Сгенерировать прогноз
            </Button>
          </div>
        </Card>
      )}

      {/* Add Modal */}
      <Modal
        title="Добавить прогноз"
        open={addModalVisible}
        onOk={handleAddForecast}
        onCancel={() => {
          setAddModalVisible(false)
          addForm.resetFields()
        }}
        okText="Добавить"
        cancelText="Отмена"
        confirmLoading={createMutation.isPending}
        width={600}
      >
        <Form
          form={addForm}
          layout="vertical"
          initialValues={{
            forecast_date: dayjs(`${selectedYear}-${selectedMonth}-15`),
            is_regular: false,
          }}
        >
          <Form.Item
            name="category_id"
            label="Статья расходов"
            rules={[{ required: true, message: 'Выберите категорию' }]}
          >
            <Select
              showSearch
              placeholder="Выберите категорию"
              filterOption={(input, option) =>
                (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {categories?.map(cat => (
                <Option key={cat.id} value={cat.id}>{cat.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="contractor_id"
            label="Контрагент"
          >
            <Select
              showSearch
              allowClear
              placeholder="Выберите контрагента"
              filterOption={(input, option) =>
                (option?.children as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {contractors?.map(contractor => (
                <Option key={contractor.id} value={contractor.id}>{contractor.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="organization_id"
            label="Организация"
            rules={[{ required: true, message: 'Выберите организацию' }]}
          >
            <Select placeholder="Выберите организацию">
              {organizations?.map(org => (
                <Option key={org.id} value={org.id}>{org.name}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="forecast_date"
            label="Дата прогноза"
            rules={[{ required: true, message: 'Укажите дату' }]}
          >
            <DatePicker format="DD.MM.YYYY" style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="amount"
            label="Сумма"
            rules={[{ required: true, message: 'Укажите сумму' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              precision={2}
              placeholder="0.00"
            />
          </Form.Item>

          <Form.Item
            name="comment"
            label="Комментарий"
          >
            <Input.TextArea rows={3} placeholder="Комментарий к прогнозу" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default ForecastPage
