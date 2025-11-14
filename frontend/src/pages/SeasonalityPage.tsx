import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic,
  Alert,
  Tag,
  Spin,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  BarChartOutlined,
  CalculatorOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import { useDepartment } from '@/contexts/DepartmentContext'
import { revenueApi } from '@/api/revenue'
import type { SeasonalityCoefficient, SeasonalityCoefficientCreate } from '@/types/revenue'

const { Option } = Select

const MONTH_NAMES = [
  'Январь',
  'Февраль',
  'Март',
  'Апрель',
  'Май',
  'Июнь',
  'Июль',
  'Август',
  'Сентябрь',
  'Октябрь',
  'Ноябрь',
  'Декабрь',
]

const SeasonalityPage = () => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const [form] = Form.useForm()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [editingCoefficient, setEditingCoefficient] = useState<SeasonalityCoefficient | null>(null)
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>()

  // Fetch seasonality coefficients
  const { data: coefficients = [], isLoading } = useQuery({
    queryKey: ['seasonality-coefficients', selectedYear, selectedCategory, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.seasonality.getAll({
        year: selectedYear,
        category: selectedCategory,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Create coefficient mutation
  const createCoefficientMutation = useMutation({
    mutationFn: (data: SeasonalityCoefficientCreate) => revenueApi.seasonality.create(data),
    onSuccess: () => {
      message.success('Коэффициенты сезонности успешно созданы')
      queryClient.invalidateQueries({ queryKey: ['seasonality-coefficients'] })
      setIsModalVisible(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка создания коэффициентов: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Update coefficient mutation
  const updateCoefficientMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => revenueApi.seasonality.update(id, data),
    onSuccess: () => {
      message.success('Коэффициенты сезонности успешно обновлены')
      queryClient.invalidateQueries({ queryKey: ['seasonality-coefficients'] })
      setIsModalVisible(false)
      setEditingCoefficient(null)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления коэффициентов: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Delete coefficient mutation
  const deleteCoefficientMutation = useMutation({
    mutationFn: (id: number) => revenueApi.seasonality.delete(id),
    onSuccess: () => {
      message.success('Коэффициенты сезонности успешно удалены')
      queryClient.invalidateQueries({ queryKey: ['seasonality-coefficients'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления коэффициентов: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Calculate average coefficient and validation
  const calculateAverage = useCallback((values: any) => {
    const coeffs = [
      values.coef_01,
      values.coef_02,
      values.coef_03,
      values.coef_04,
      values.coef_05,
      values.coef_06,
      values.coef_07,
      values.coef_08,
      values.coef_09,
      values.coef_10,
      values.coef_11,
      values.coef_12,
    ].filter((v) => v !== undefined && v !== null)

    if (coeffs.length === 0) return { avg: 1.0, isValid: false }

    const sum = coeffs.reduce((a, b) => a + Number(b), 0)
    const avg = sum / coeffs.length
    const isValid = Math.abs(avg - 1.0) <= 0.1 // Allow 10% deviation

    return { avg, isValid }
  }, [])

  const handleOpenModal = useCallback(
    (coefficient?: SeasonalityCoefficient) => {
      if (coefficient) {
        setEditingCoefficient(coefficient)
        form.setFieldsValue({
          year: coefficient.year,
          category: coefficient.revenue_stream_id,
          coef_01: coefficient.coef_01,
          coef_02: coefficient.coef_02,
          coef_03: coefficient.coef_03,
          coef_04: coefficient.coef_04,
          coef_05: coefficient.coef_05,
          coef_06: coefficient.coef_06,
          coef_07: coefficient.coef_07,
          coef_08: coefficient.coef_08,
          coef_09: coefficient.coef_09,
          coef_10: coefficient.coef_10,
          coef_11: coefficient.coef_11,
          coef_12: coefficient.coef_12,
          notes: coefficient.description,
        })
      } else {
        setEditingCoefficient(null)
        // Set default values (all 1.0)
        form.setFieldsValue({
          year: selectedYear,
          coef_01: 1.0,
          coef_02: 1.0,
          coef_03: 1.0,
          coef_04: 1.0,
          coef_05: 1.0,
          coef_06: 1.0,
          coef_07: 1.0,
          coef_08: 1.0,
          coef_09: 1.0,
          coef_10: 1.0,
          coef_11: 1.0,
          coef_12: 1.0,
        })
      }
      setIsModalVisible(true)
    },
    [form, selectedYear]
  )

  const handleCloseModal = useCallback(() => {
    setIsModalVisible(false)
    setEditingCoefficient(null)
    form.resetFields()
  }, [form])

  const handleSubmit = useCallback(() => {
    form.validateFields().then((values) => {
      if (editingCoefficient) {
        updateCoefficientMutation.mutate({ id: editingCoefficient.id, data: values })
      } else {
        createCoefficientMutation.mutate(values)
      }
    })
  }, [editingCoefficient, form, createCoefficientMutation, updateCoefficientMutation])

  // Expand row to show monthly coefficients
  const expandedRowRender = (record: SeasonalityCoefficient) => {
    const monthlyData = MONTH_NAMES.map((name, index) => {
      const field = `coef_${String(index + 1).padStart(2, '0')}` as keyof SeasonalityCoefficient
      const value = Number(record[field]) || 1.0

      return {
        month: name,
        coefficient: value,
        impact: ((value - 1) * 100).toFixed(1),
      }
    })

    const columns = [
      { title: 'Месяц', dataIndex: 'month', key: 'month' },
      {
        title: 'Коэффициент',
        dataIndex: 'coefficient',
        key: 'coefficient',
        render: (value: number) => (
          <Tag color={value > 1 ? 'green' : value < 1 ? 'red' : 'default'}>{value.toFixed(3)}</Tag>
        ),
      },
      {
        title: 'Влияние',
        dataIndex: 'impact',
        key: 'impact',
        render: (value: string) => {
          const num = parseFloat(value)
          return (
            <span style={{ color: num > 0 ? '#52c41a' : num < 0 ? '#ff4d4f' : '#8c8c8c' }}>
              {num > 0 ? '+' : ''}
              {value}%
            </span>
          )
        },
      },
    ]

    return <Table columns={columns} dataSource={monthlyData} pagination={false} rowKey="month" size="small" />
  }

  const columns = [
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 100,
    },
    {
      title: 'Категория',
      dataIndex: 'category',
      key: 'category',
      width: 200,
    },
    {
      title: 'Средний коэффициент',
      key: 'avg_coefficient',
      width: 180,
      render: (_: any, record: SeasonalityCoefficient) => {
        const coeffs = [
          record.coef_01,
          record.coef_02,
          record.coef_03,
          record.coef_04,
          record.coef_05,
          record.coef_06,
          record.coef_07,
          record.coef_08,
          record.coef_09,
          record.coef_10,
          record.coef_11,
          record.coef_12,
        ]
        const sum = coeffs.reduce((a, b) => a + Number(b || 0), 0)
        const avg = sum / 12
        const isValid = Math.abs(avg - 1.0) <= 0.1

        return (
          <Space>
            <span>{avg.toFixed(3)}</span>
            {isValid ? (
              <CheckCircleOutlined style={{ color: '#52c41a' }} />
            ) : (
              <Tooltip title="Среднее отклоняется от 1.0 более чем на 10%">
                <WarningOutlined style={{ color: '#faad14' }} />
              </Tooltip>
            )}
          </Space>
        )
      },
    },
    {
      title: 'Примечания',
      dataIndex: 'notes',
      key: 'notes',
      ellipsis: true,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      fixed: 'right' as const,
      render: (_: any, record: SeasonalityCoefficient) => (
        <Space size="small">
          <Tooltip title="Редактировать">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleOpenModal(record)}
            />
          </Tooltip>

          <Popconfirm
            title="Удалить коэффициенты?"
            description="Это действие нельзя отменить"
            onConfirm={() => deleteCoefficientMutation.mutate(record.id)}
            okText="Удалить"
            cancelText="Отмена"
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Watch form values for real-time average calculation
  const formValues = Form.useWatch([], form)
  const avgInfo = useMemo(() => {
    if (!formValues) return null
    return calculateAverage(formValues)
  }, [formValues, calculateAverage])

  if (!selectedDepartment) {
    return (
      <div style={{ padding: 24, display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px' }}>
        <Spin tip="Загрузка данных отдела...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, marginBottom: 8 }}>Коэффициенты сезонности</h1>
        <p style={{ margin: 0, color: '#8c8c8c' }}>
          Управление коэффициентами сезонности для прогнозирования доходов (12 месяцев)
        </p>
      </div>

      {/* Info Alert */}
      <Alert
        message="О коэффициентах сезонности"
        description="Коэффициенты сезонности помогают распределить годовой план доходов по месяцам с учетом сезонных колебаний. Среднее значение всех коэффициентов должно быть близко к 1.0. Коэффициент > 1.0 означает более высокую активность, < 1.0 - более низкую."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="Всего наборов"
              value={coefficients.length}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Годы"
              value={selectedYear}
              prefix={<CalculatorOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="Категорий"
              value={new Set(coefficients.map((c) => c.revenue_stream_id)).size}
              prefix={<BarChartOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16} align="middle">
          <Col flex="auto">
            <Space size="middle">
              <span>Год:</span>
              <Select value={selectedYear} onChange={setSelectedYear} style={{ width: 120 }}>
                {[2023, 2024, 2025, 2026, 2027].map((year) => (
                  <Option key={year} value={year}>
                    {year}
                  </Option>
                ))}
              </Select>

              <span>Категория:</span>
              <Input
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value || undefined)}
                style={{ width: 200 }}
                placeholder="Поиск по категории"
                allowClear
              />
            </Space>
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              Добавить коэффициенты
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Coefficients Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={coefficients}
          rowKey="id"
          loading={isLoading}
          expandable={{
            expandedRowRender,
            expandRowByClick: true,
          }}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total}`,
            defaultPageSize: 20,
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingCoefficient ? 'Редактировать коэффициенты' : 'Добавить коэффициенты сезонности'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        width={900}
        confirmLoading={createCoefficientMutation.isPending || updateCoefficientMutation.isPending}
        okText={editingCoefficient ? 'Сохранить' : 'Создать'}
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="year" label="Год" rules={[{ required: true, message: 'Введите год' }]}>
                <InputNumber min={2020} max={2030} style={{ width: '100%' }} placeholder="2025" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="category"
                label="Категория"
                rules={[{ required: true, message: 'Введите категорию' }]}
              >
                <Input placeholder="Например: Ортодонтия" />
              </Form.Item>
            </Col>
          </Row>

          {/* Average indicator */}
          {avgInfo && (
            <Alert
              message={
                <span>
                  Среднее значение: <strong>{avgInfo.avg.toFixed(3)}</strong>
                </span>
              }
              type={avgInfo.isValid ? 'success' : 'warning'}
              description={
                avgInfo.isValid
                  ? 'Среднее значение близко к 1.0 (допустимое отклонение ±10%)'
                  : 'Среднее значение отклоняется от 1.0 более чем на 10%. Рассмотрите нормализацию коэффициентов.'
              }
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* Monthly coefficients */}
          <div style={{ marginBottom: 16 }}>
            <strong>Месячные коэффициенты:</strong>
          </div>

          <Row gutter={[12, 12]}>
            {MONTH_NAMES.map((month, index) => (
              <Col span={6} key={index}>
                <Form.Item
                  name={`coef_${String(index + 1).padStart(2, '0')}`}
                  label={month}
                  rules={[{ required: true, message: 'Введите коэффициент' }]}
                >
                  <InputNumber
                    min={0}
                    max={5}
                    step={0.05}
                    style={{ width: '100%' }}
                    placeholder="1.0"
                  />
                </Form.Item>
              </Col>
            ))}
          </Row>

          <Form.Item name="notes" label="Примечания">
            <Input.TextArea rows={3} placeholder="Дополнительная информация (необязательно)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default SeasonalityPage
