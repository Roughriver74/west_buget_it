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
  Progress,
  Spin,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  TeamOutlined,
  PercentageOutlined,
  DollarOutlined,
} from '@ant-design/icons'
import { useDepartment } from '@/contexts/DepartmentContext'
import { revenueApi } from '@/api/revenue'
import type { CustomerMetrics, CustomerMetricsCreate } from '@/types/revenue'

const { Option } = Select

const CustomerMetricsPage = () => {
  const { selectedDepartment } = useDepartment()
  const queryClient = useQueryClient()
  const [form] = Form.useForm()
  const [isModalVisible, setIsModalVisible] = useState(false)
  const [editingMetrics, setEditingMetrics] = useState<CustomerMetrics | null>(null)
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear())
  const [selectedMonth, setSelectedMonth] = useState<number | undefined>()
  const [selectedRegion, setSelectedRegion] = useState<string | undefined>()

  // Fetch customer metrics
  const { data: metrics = [], isLoading } = useQuery({
    queryKey: ['customer-metrics', selectedYear, selectedMonth, selectedRegion, selectedDepartment?.id],
    queryFn: () =>
      revenueApi.customerMetrics.getAll({
        year: selectedYear,
        month: selectedMonth,
        region: selectedRegion,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  // Create metrics mutation
  const createMetricsMutation = useMutation({
    mutationFn: (data: CustomerMetricsCreate) => revenueApi.customerMetrics.create(data),
    onSuccess: () => {
      message.success('Клиентские метрики успешно созданы')
      queryClient.invalidateQueries({ queryKey: ['customer-metrics'] })
      setIsModalVisible(false)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка создания метрик: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Update metrics mutation
  const updateMetricsMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => revenueApi.customerMetrics.update(id, data),
    onSuccess: () => {
      message.success('Клиентские метрики успешно обновлены')
      queryClient.invalidateQueries({ queryKey: ['customer-metrics'] })
      setIsModalVisible(false)
      setEditingMetrics(null)
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка обновления метрик: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Delete metrics mutation
  const deleteMetricsMutation = useMutation({
    mutationFn: (id: number) => revenueApi.customerMetrics.delete(id),
    onSuccess: () => {
      message.success('Клиентские метрики успешно удалены')
      queryClient.invalidateQueries({ queryKey: ['customer-metrics'] })
    },
    onError: (error: any) => {
      message.error(`Ошибка удаления метрик: ${error.response?.data?.detail || error.message}`)
    },
  })

  // Calculate summary statistics
  const summary = useMemo(() => {
    const totalCustomerBase = metrics.reduce((sum, m) => sum + Number(m.total_customer_base || 0), 0)
    const activeCustomerBase = metrics.reduce((sum, m) => sum + Number(m.active_customer_base || 0), 0)
    const avgCoverage = totalCustomerBase > 0 ? (activeCustomerBase / totalCustomerBase) * 100 : 0

    const avgCheckRegular =
      metrics.reduce((sum, m) => sum + Number(m.avg_check_regular || 0), 0) / (metrics.length || 1)
    const avgCheckNetwork =
      metrics.reduce((sum, m) => sum + Number(m.avg_check_network || 0), 0) / (metrics.length || 1)

    return {
      totalCustomerBase,
      activeCustomerBase,
      avgCoverage,
      avgCheckRegular,
      avgCheckNetwork,
    }
  }, [metrics])

  const handleOpenModal = useCallback(
    (metricsItem?: CustomerMetrics) => {
      if (metricsItem) {
        setEditingMetrics(metricsItem)
        form.setFieldsValue({
          year: metricsItem.year,
          month: metricsItem.month,
          region: metricsItem.region,
          total_customer_base: metricsItem.total_customer_base,
          active_customer_base: metricsItem.active_customer_base,
          avg_check_regular: metricsItem.avg_check_regular,
          avg_check_network: metricsItem.avg_check_network,
          avg_check_new_clinics: metricsItem.avg_check_new_clinics,
          notes: metricsItem.notes,
        })
      } else {
        setEditingMetrics(null)
        form.setFieldsValue({
          year: selectedYear,
          month: selectedMonth || new Date().getMonth() + 1,
        })
      }
      setIsModalVisible(true)
    },
    [form, selectedYear, selectedMonth]
  )

  const handleCloseModal = useCallback(() => {
    setIsModalVisible(false)
    setEditingMetrics(null)
    form.resetFields()
  }, [form])

  const handleSubmit = useCallback(() => {
    form.validateFields().then((values) => {
      if (editingMetrics) {
        updateMetricsMutation.mutate({ id: editingMetrics.id, data: values })
      } else {
        createMetricsMutation.mutate(values)
      }
    })
  }, [editingMetrics, form, createMetricsMutation, updateMetricsMutation])

  const columns = [
    {
      title: 'Год',
      dataIndex: 'year',
      key: 'year',
      width: 80,
    },
    {
      title: 'Месяц',
      dataIndex: 'month',
      key: 'month',
      width: 80,
      render: (month: number) => {
        const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        return months[month - 1] || month
      },
    },
    {
      title: 'Регион',
      dataIndex: 'region',
      key: 'region',
      width: 150,
    },
    {
      title: 'ОКБ',
      dataIndex: 'total_customer_base',
      key: 'total_customer_base',
      width: 100,
      align: 'right' as const,
      render: (value: number) => value?.toLocaleString('ru-RU') || '—',
    },
    {
      title: 'АКБ',
      dataIndex: 'active_customer_base',
      key: 'active_customer_base',
      width: 100,
      align: 'right' as const,
      render: (value: number) => value?.toLocaleString('ru-RU') || '—',
    },
    {
      title: 'Покрытие',
      dataIndex: 'coverage_percent',
      key: 'coverage_percent',
      width: 120,
      align: 'center' as const,
      render: (value: number) => {
        if (!value) return '—'
        const percent = Number(value)
        return (
          <Progress
            percent={percent}
            size="small"
            status={percent >= 70 ? 'success' : percent >= 50 ? 'normal' : 'exception'}
            format={(percent) => `${percent?.toFixed(1)}%`}
          />
        )
      },
    },
    {
      title: 'Средний чек (обычные)',
      dataIndex: 'avg_check_regular',
      key: 'avg_check_regular',
      width: 140,
      align: 'right' as const,
      render: (value: number) => (value ? `${value.toLocaleString('ru-RU')} ₽` : '—'),
    },
    {
      title: 'Средний чек (сетевые)',
      dataIndex: 'avg_check_network',
      key: 'avg_check_network',
      width: 140,
      align: 'right' as const,
      render: (value: number) => (value ? `${value.toLocaleString('ru-RU')} ₽` : '—'),
    },
    {
      title: 'Средний чек (новые клиники)',
      dataIndex: 'avg_check_new_clinics',
      key: 'avg_check_new_clinics',
      width: 160,
      align: 'right' as const,
      render: (value: number) => (value ? `${value.toLocaleString('ru-RU')} ₽` : '—'),
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
      render: (_: any, record: CustomerMetrics) => (
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
            title="Удалить метрики?"
            description="Это действие нельзя отменить"
            onConfirm={() => deleteMetricsMutation.mutate(record.id)}
            okText="Удалить"
            cancelText="Отмена"
          >
            <Button type="link" danger size="small" icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  if (!selectedDepartment) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin tip="Загрузка данных отдела..." />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, marginBottom: 8 }}>Клиентские метрики</h1>
        <p style={{ margin: 0, color: '#8c8c8c' }}>
          Управление метриками клиентской базы (ОКБ, АКБ, покрытие, средний чек)
        </p>
      </div>

      {/* Summary Statistics */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Общая клиентская база (ОКБ)"
              value={summary.totalCustomerBase}
              prefix={<TeamOutlined />}
              suffix="клиентов"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Активная клиентская база (АКБ)"
              value={summary.activeCustomerBase}
              prefix={<TeamOutlined />}
              suffix="клиентов"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Среднее покрытие"
              value={summary.avgCoverage}
              precision={1}
              prefix={<PercentageOutlined />}
              suffix="%"
              valueStyle={{ color: summary.avgCoverage >= 70 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Средний чек (обычные)"
              value={summary.avgCheckRegular}
              precision={0}
              prefix={<DollarOutlined />}
              suffix="₽"
              valueStyle={{ color: '#1890ff' }}
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

              <span>Месяц:</span>
              <Select
                value={selectedMonth}
                onChange={setSelectedMonth}
                style={{ width: 120 }}
                allowClear
                placeholder="Все месяцы"
              >
                {[
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
                ].map((month, index) => (
                  <Option key={index + 1} value={index + 1}>
                    {month}
                  </Option>
                ))}
              </Select>

              <span>Регион:</span>
              <Input
                value={selectedRegion}
                onChange={(e) => setSelectedRegion(e.target.value || undefined)}
                style={{ width: 200 }}
                placeholder="Поиск по региону"
                allowClear
              />
            </Space>
          </Col>
          <Col>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => handleOpenModal()}>
              Добавить метрики
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Metrics Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={metrics}
          rowKey="id"
          loading={isLoading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `Всего: ${total}`,
            defaultPageSize: 20,
          }}
          scroll={{ x: 1600 }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingMetrics ? 'Редактировать метрики' : 'Добавить клиентские метрики'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleCloseModal}
        width={700}
        confirmLoading={createMetricsMutation.isPending || updateMetricsMutation.isPending}
        okText={editingMetrics ? 'Сохранить' : 'Создать'}
        cancelText="Отмена"
      >
        <Form form={form} layout="vertical" style={{ marginTop: 24 }}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="year"
                label="Год"
                rules={[{ required: true, message: 'Выберите год' }]}
              >
                <InputNumber min={2020} max={2030} style={{ width: '100%' }} placeholder="2025" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="month"
                label="Месяц"
                rules={[{ required: true, message: 'Выберите месяц' }]}
              >
                <Select placeholder="Выберите месяц">
                  {[
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
                  ].map((month, index) => (
                    <Option key={index + 1} value={index + 1}>
                      {month}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="region"
                label="Регион"
                rules={[{ required: true, message: 'Введите регион' }]}
              >
                <Input placeholder="Например: СПБ и ЛО" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="total_customer_base"
                label="ОКБ (Общая клиентская база)"
                rules={[{ required: true, message: 'Введите ОКБ' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} placeholder="500" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="active_customer_base"
                label="АКБ (Активная клиентская база)"
                rules={[{ required: true, message: 'Введите АКБ' }]}
              >
                <InputNumber min={0} style={{ width: '100%' }} placeholder="350" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="avg_check_regular" label="Средний чек (обычные клиенты)">
                <InputNumber
                  min={0}
                  step={100}
                  style={{ width: '100%' }}
                  placeholder="50000"
                  addonAfter="₽"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="avg_check_network" label="Средний чек (сетевые клиенты)">
                <InputNumber
                  min={0}
                  step={100}
                  style={{ width: '100%' }}
                  placeholder="120000"
                  addonAfter="₽"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="avg_check_new_clinics" label="Средний чек (новые клиники)">
                <InputNumber
                  min={0}
                  step={100}
                  style={{ width: '100%' }}
                  placeholder="80000"
                  addonAfter="₽"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="notes" label="Примечания">
            <Input.TextArea rows={3} placeholder="Дополнительная информация (необязательно)" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default CustomerMetricsPage
