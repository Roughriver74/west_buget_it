import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Typography,
  Card,
  Button,
  Space,
  Select,
  message,
  Table,
  InputNumber,
  Input,
  Popconfirm,
  Tag,
  Modal,
  Form,
  DatePicker,
  Result,
  Empty,
} from 'antd'
import {
  PlusOutlined, DeleteOutlined, EditOutlined,
  CheckOutlined, CloseOutlined, ThunderboltOutlined, DownloadOutlined, RobotOutlined
} from '@ant-design/icons'
import { forecastApi, categoriesApi, contractorsApi, organizationsApi } from '@/api'
import type { ForecastExpense } from '@/types'
import type { AIForecastResponse } from '@/api/forecast'
import { useAuth } from '@/contexts/AuthContext'
import { useDepartment } from '@/contexts/DepartmentContext'
import dayjs from 'dayjs'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'

const { Title, Paragraph } = Typography
const { Option } = Select

const currencyFormatter = new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB' })
const formatCurrency = (value?: number | null) => currencyFormatter.format(value ?? 0)

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
  const [aiResultModalVisible, setAiResultModalVisible] = useState(false)
  const [aiResult, setAiResult] = useState<AIForecastResponse | null>(null)

  const sourceLabels = {
    plan: 'План',
    history: 'История',
    other: 'Другое',
  } as const

  const sourceColors = {
    plan: 'blue',
    history: 'purple',
    other: 'default',
  } as const

  const getConfidenceTagColor = (value: number) => {
    if (value >= 70) return 'success'
    if (value >= 50) return 'warning'
    return 'error'
  }

  const getProbabilityTagColor = (value: number) => {
    if (value >= 60) return 'success'
    if (value >= 40) return 'blue'
    return 'warning'
  }

  const baseScenario = aiResult?.scenarios?.find(scenario => scenario.name === 'base' || scenario.name === 'baseline') ?? aiResult?.scenarios?.[0] ?? null

  const queryClient = useQueryClient()

  // Load data
  const departmentId = selectedDepartment?.id ?? (user?.department_id ?? undefined)

  const {
    data: forecastsData,
    isLoading: forecastsLoading,
    isError: forecastsError,
    error: forecastsErrorObj,
    refetch: refetchForecasts,
  } = useQuery({
    queryKey: ['forecasts', selectedYear, selectedMonth, departmentId ?? 'none'],
    queryFn: () => {
      if (departmentId == null) {
        return []
      }
      return forecastApi.getAll(selectedYear, selectedMonth, departmentId)
    },
  })

  const {
    data: categoriesData = [],
    isLoading: categoriesLoading,
    isError: categoriesError,
    error: categoriesErrorObj,
    refetch: refetchCategories,
  } = useQuery({
    queryKey: ['categories'],
    queryFn: () => categoriesApi.getAll(),
  })

  const {
    data: contractorsData,
    isLoading: contractorsLoading,
    isError: contractorsError,
    error: contractorsErrorObj,
    refetch: refetchContractors,
  } = useQuery({
    queryKey: ['contractors', departmentId ?? 'none'],
    queryFn: () => {
      if (departmentId == null) {
        return []
      }
      return contractorsApi.getAll({ limit: 1000, department_id: departmentId })
    },
  })

  const {
    data: organizationsData,
    isLoading: organizationsLoading,
    isError: organizationsError,
    error: organizationsErrorObj,
    refetch: refetchOrganizations,
  } = useQuery({
    queryKey: ['organizations'],
    queryFn: () => organizationsApi.getAll({ limit: 100 }),
  })

  const forecasts = forecastsData ?? []
  const categories = categoriesData
  const contractors = contractorsData ?? []
  const organizations = organizationsData ?? []

  const getErrorMessage = (error: unknown) => (error instanceof Error ? error.message : 'Неизвестная ошибка')

  const queryErrors: string[] = []
  if (forecastsError) {
    queryErrors.push(`Прогнозы: ${getErrorMessage(forecastsErrorObj)}`)
  }
  if (categoriesError) {
    queryErrors.push(`Категории: ${getErrorMessage(categoriesErrorObj)}`)
  }
  if (contractorsError) {
    queryErrors.push(`Контрагенты: ${getErrorMessage(contractorsErrorObj)}`)
  }
  if (organizationsError) {
    queryErrors.push(`Организации: ${getErrorMessage(organizationsErrorObj)}`)
  }

  const handleRetry = async () => {
    await Promise.allSettled([
      refetchForecasts(),
      refetchCategories(),
      refetchContractors(),
      refetchOrganizations(),
    ])
  }

  const isInitialLoading =
    forecastsLoading || categoriesLoading || contractorsLoading || organizationsLoading

  // Mutations
  const generateMutation = useMutation({
    mutationFn: () => {
      if (!departmentId) {
        throw new Error('Отдел не выбран')
      }
      return forecastApi.generate({
        target_year: selectedYear,
        target_month: selectedMonth,
        department_id: departmentId,
        include_regular: true,
        include_average: true,
      })
    },
    onSuccess: (data) => {
      message.success(`Прогноз создан! Добавлено: ${data.created} позиций`)
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка генерации: ${error.message}`)
    },
  })

  const generateAIMutation = useMutation({
    mutationFn: () => {
      if (!departmentId) {
        throw new Error('Отдел не выбран')
      }
      return forecastApi.generateAI({
        target_year: selectedYear,
        target_month: selectedMonth,
        department_id: departmentId,
      })
    },
    onSuccess: (data) => {
      setAiResult(data)
      setAiResultModalVisible(true)
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
      if (data.success) {
        message.success(`AI прогноз создан! Добавлено: ${data.created_forecast_records} позиций`)
      } else {
        message.warning(`AI прогноз выполнен с предупреждениями`)
      }
    },
    onError: (error: any) => {
      message.error(`Ошибка AI генерации: ${error.message}`)
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
    mutationFn: () => {
      if (!departmentId) {
        throw new Error('Отдел не выбран')
      }
      return forecastApi.clear(selectedYear, selectedMonth, departmentId)
    },
    onSuccess: () => {
      message.success('Прогнозы очищены')
      queryClient.invalidateQueries({ queryKey: ['forecasts'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка очистки: ${error.message}`)
    },
  })

  if (!departmentId) {
    return (
      <Result
        status="info"
        title="Выберите отдел"
        subTitle="Для работы с прогнозом расходов выберите отдел в шапке приложения."
      />
    )
  }

  if (isInitialLoading) {
    return <LoadingState />
  }

  if (queryErrors.length > 0) {
    return (
      <ErrorState
        description={queryErrors.join(' • ')}
        onRetry={handleRetry}
        retryLabel="Повторить попытку"
      />
    )
  }

  const handleSaveEdit = (id: number) => {
    if (!editingData) return

    // Удаляем поля, которые не нужны для обновления (read-only)
    const { category, contractor, organization, created_at, updated_at, ...dataToSend } = editingData as any

    updateMutation.mutate({
      id,
      data: dataToSend
    })
  }

  const handleAddForecast = () => {
    addForm.validateFields().then(values => {
      if (!departmentId) {
        message.error('Отдел не выбран')
        return
      }
      createMutation.mutate({
        ...values,
        department_id: departmentId,
        forecast_date: values.forecast_date.format('YYYY-MM-DD'),
      })
    })
  }

  const handleExportToExcel = async () => {
    try {
      if (!departmentId) {
        message.error('Отдел не выбран')
        return
      }
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
  // Group forecasts by day
  const forecastsByDay: Record<number, ForecastExpense[]> = {}
  forecasts.forEach(f => {
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
              filterOption={(input, option) => {
                const label = option?.label ?? option?.value
                return String(label ?? '')
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }}
            >
              {categories.map(cat => (
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
              filterOption={(input, option) => {
                const label = option?.label ?? option?.value
                return String(label ?? '')
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }}
            >
              {contractors.map(contractor => (
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

  const totalAmount = forecasts.reduce((sum, f) => sum + Number(f.amount), 0)
  const isForecastsEmpty = forecasts.length === 0

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
              Статистический прогноз
            </Button>
            <Button
              icon={<RobotOutlined />}
              onClick={() => generateAIMutation.mutate()}
              loading={generateAIMutation.isPending}
              type="primary"
              style={{ background: '#722ed1', borderColor: '#722ed1' }}
            >
              AI Прогноз
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

      {!isForecastsEmpty ? (
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
          <Empty
            description="Нет прогнозов на выбранный месяц"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button
              type="primary"
              icon={<ThunderboltOutlined />}
              onClick={() => generateMutation.mutate()}
              loading={generateMutation.isPending}
            >
              Сгенерировать прогноз
            </Button>
          </Empty>
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
              filterOption={(input, option) => {
                const label = option?.label ?? option?.value
                return String(label ?? '')
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }}
            >
              {categories.map(cat => (
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
              filterOption={(input, option) => {
                const label = option?.label ?? option?.value
                return String(label ?? '')
                  .toLowerCase()
                  .includes(input.toLowerCase())
              }}
            >
              {contractors.map(contractor => (
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
              {organizations.map(org => (
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

      {/* AI Results Modal */}
      <Modal
        title={<Space><RobotOutlined /> Результаты AI прогноза</Space>}
        open={aiResultModalVisible}
        onCancel={() => setAiResultModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setAiResultModalVisible(false)}>
            Закрыть
          </Button>
        ]}
        width={840}
      >
        {aiResult && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <Card size="small">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span><strong>Статус:</strong></span>
                  <Tag color={aiResult.success ? 'success' : 'warning'}>
                    {aiResult.success ? 'Успешно' : 'С предупреждениями'}
                  </Tag>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span><strong>Прогнозная сумма:</strong></span>
                  <span style={{ fontSize: 16, fontWeight: 'bold', color: '#1890ff' }}>
                    {formatCurrency(aiResult.forecast_total)}
                  </span>
                </div>
                {baseScenario && (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span><strong>Базовый сценарий:</strong></span>
                      <Space size="small">
                        <Tag color="blue">{baseScenario.label || baseScenario.name}</Tag>
                        <Tag color={getProbabilityTagColor(baseScenario.probability)}>
                          {baseScenario.probability}%
                        </Tag>
                      </Space>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span><strong>Диапазон:</strong></span>
                      <span>{formatCurrency(baseScenario.range_min)} – {formatCurrency(baseScenario.range_max)}</span>
                    </div>
                  </>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span><strong>Уверенность AI:</strong></span>
                  <Tag color={getConfidenceTagColor(aiResult.confidence)}>
                    {aiResult.confidence}%
                  </Tag>
                </div>
                {aiResult.ai_model && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span><strong>Модель:</strong></span>
                    <span style={{ fontFamily: 'monospace', fontSize: 12 }}>{aiResult.ai_model}</span>
                  </div>
                )}
                {aiResult.created_forecast_records > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span><strong>Создано позиций:</strong></span>
                    <Tag color="blue">{aiResult.created_forecast_records}</Tag>
                  </div>
                )}
              </Space>
            </Card>

            <Card size="small" title="Сводка">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Paragraph style={{ marginBottom: aiResult.quality_notes ? 8 : 0 }}>{aiResult.summary}</Paragraph>
                {aiResult.quality_notes && (
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    {aiResult.quality_notes}
                  </Paragraph>
                )}
              </Space>
            </Card>

            {aiResult.scenarios && aiResult.scenarios.length > 0 && (
              <Card size="small" title="Сценарии">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {aiResult.scenarios.map((scenario, index) => {
                    const isBase = scenario.name === 'base' || scenario.name === 'baseline'
                    const rangeText = `${formatCurrency(scenario.range_min)} – ${formatCurrency(scenario.range_max)}`
                    return (
                      <Card
                        key={`${scenario.name}-${index}`}
                        size="small"
                        type="inner"
                      >
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <Space size="small">
                              <Tag color={isBase ? 'blue' : scenario.name === 'optimistic' ? 'green' : 'volcano'}>
                                {scenario.label || scenario.name}
                              </Tag>
                              <Tag color={getProbabilityTagColor(scenario.probability)}>
                                {scenario.probability}%
                              </Tag>
                            </Space>
                            <span><strong>Сумма:</strong> {formatCurrency(scenario.total)}</span>
                          </div>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span><strong>Диапазон:</strong></span>
                            <span>{rangeText}</span>
                          </div>
                          {scenario.description && (
                            <Paragraph style={{ marginBottom: 0, fontSize: 13 }}>
                              {scenario.description}
                            </Paragraph>
                          )}
                        </Space>
                      </Card>
                    )
                  })}
                </Space>
              </Card>
            )}

            {aiResult.items && aiResult.items.length > 0 && (
              <Card size="small" title="Детализация прогноза">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {aiResult.items.map((item, index) => (
                    <Card
                      key={index}
                      size="small"
                      type="inner"
                      title={<Space><Tag color="purple">{index + 1}</Tag>{item.description}</Space>}
                    >
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span><strong>Сумма:</strong></span>
                          <span style={{ fontSize: 15, fontWeight: 'bold' }}>
                            {formatCurrency(item.amount)}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span><strong>Диапазон:</strong></span>
                          <span>{formatCurrency(item.range_min)} – {formatCurrency(item.range_max)}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span><strong>Источник:</strong></span>
                          <Space size="small">
                            <Tag color={sourceColors[item.source] ?? 'default'}>
                              {sourceLabels[item.source] ?? item.source}
                            </Tag>
                            <Tag color={getConfidenceTagColor(item.confidence)}>
                              {item.confidence}%
                            </Tag>
                          </Space>
                        </div>
                        <div>
                          <strong>Обоснование:</strong>
                          <Paragraph style={{ marginTop: 8, marginBottom: 0, fontSize: 13 }}>
                            {item.reasoning}
                          </Paragraph>
                        </div>
                      </Space>
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            {aiResult.correlations && aiResult.correlations.length > 0 && (
              <Card size="small" title="Корреляции и драйверы">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {aiResult.correlations.map((corr, index) => (
                    <Card key={index} size="small" type="inner">
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Space size="small">
                          <Tag color="geekblue">{corr.driver}</Tag>
                          <Tag color={getConfidenceTagColor(corr.confidence)}>{corr.confidence}%</Tag>
                          {typeof corr.lag_months === 'number' && (
                            <Tag color="gold">Лаг: {corr.lag_months} мес.</Tag>
                          )}
                        </Space>
                        <Paragraph style={{ marginBottom: 0, fontSize: 13 }}>
                          {corr.impact}
                        </Paragraph>
                      </Space>
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            {aiResult.recommendations && aiResult.recommendations.length > 0 && (
              <Card size="small" title="Рекомендации действий">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {aiResult.recommendations.map((rec, index) => (
                    <Card key={index} size="small" type="inner">
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <span style={{ fontWeight: 600 }}>{rec.title}</span>
                        <Paragraph style={{ marginBottom: 0, fontSize: 13 }}>
                          {rec.description}
                        </Paragraph>
                        {rec.potential_saving != null && (
                          <Tag color="green">Экономия: {formatCurrency(rec.potential_saving)}</Tag>
                        )}
                      </Space>
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            {aiResult.baseline_metrics && (
              <Card size="small" title="Статистические ориентиры">
                {Object.values(aiResult.baseline_metrics).some(value => value != null) ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {aiResult.baseline_metrics.simple_average != null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><strong>Среднее за период:</strong></span>
                        <span>{formatCurrency(aiResult.baseline_metrics.simple_average)}</span>
                      </div>
                    )}
                    {aiResult.baseline_metrics.moving_average != null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><strong>Скользящее (3 мес):</strong></span>
                        <span>{formatCurrency(aiResult.baseline_metrics.moving_average)}</span>
                      </div>
                    )}
                    {aiResult.baseline_metrics.seasonal_reference != null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><strong>Сезонный ориентир (прошлый год):</strong></span>
                        <span>{formatCurrency(aiResult.baseline_metrics.seasonal_reference)}</span>
                      </div>
                    )}
                    {aiResult.baseline_metrics.last_12_months_total != null && (
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span><strong>Сумма за 12 мес:</strong></span>
                        <span>{formatCurrency(aiResult.baseline_metrics.last_12_months_total)}</span>
                      </div>
                    )}
                  </Space>
                ) : (
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    Недостаточно статистики для расчёта базовых ориентиров.
                  </Paragraph>
                )}
              </Card>
            )}

            {aiResult.anomaly_summary && (
              <Card size="small" title="Аномалии и выбросы">
                {aiResult.anomaly_summary.items && aiResult.anomaly_summary.items.length > 0 ? (
                  <Space direction="vertical" style={{ width: '100%' }}>
                    {aiResult.anomaly_summary.items.map((anomaly, index) => (
                      <Paragraph key={index} style={{ marginBottom: 0, fontSize: 13 }}>
                        <Tag color="volcano">
                          {`${String(anomaly.month).padStart(2, '0')}.${anomaly.year}`}
                        </Tag>
                        {formatCurrency(anomaly.total)} (
                        {anomaly.deviation_percent > 0 ? '+' : ''}{anomaly.deviation_percent}% к среднему)
                      </Paragraph>
                    ))}
                    {(aiResult.anomaly_summary.mean != null || aiResult.anomaly_summary.threshold != null) && (
                      <Paragraph type="secondary" style={{ marginBottom: 0, fontSize: 12 }}>
                        Среднее: {aiResult.anomaly_summary.mean != null ? formatCurrency(aiResult.anomaly_summary.mean) : 'N/A'} · Порог ±σ: {aiResult.anomaly_summary.threshold != null ? formatCurrency(aiResult.anomaly_summary.threshold) : 'N/A'}
                      </Paragraph>
                    )}
                  </Space>
                ) : (
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    Существенных выбросов не обнаружено.
                  </Paragraph>
                )}
              </Card>
            )}

            {aiResult.plan_context && aiResult.plan_context.length > 0 && (
              <Card size="small" title="Контекст утверждённого плана">
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {aiResult.plan_context.map((ctx, index) => (
                    <Card key={index} size="small" type="inner">
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span><strong>{ctx.category_name ?? 'Категория'}</strong></span>
                          {ctx.planned_amount != null && (
                            <span>{formatCurrency(ctx.planned_amount)}</span>
                          )}
                        </div>
                        {ctx.justification && (
                          <Paragraph style={{ marginBottom: 0, fontSize: 13 }}>
                            {ctx.justification}
                          </Paragraph>
                        )}
                        {ctx.calculation_method && (
                          <Tag color="processing">Метод: {ctx.calculation_method}</Tag>
                        )}
                      </Space>
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            {aiResult.error && (
              <Card size="small" title="Предупреждение" type="inner">
                <Paragraph type="warning" style={{ marginBottom: 0 }}>
                  {aiResult.error}
                </Paragraph>
              </Card>
            )}
          </Space>
        )}
      </Modal>
    </div>
  )
}

export default ForecastPage
