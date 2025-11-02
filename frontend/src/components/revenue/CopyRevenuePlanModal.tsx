import React, { useState, useMemo } from 'react'
import { Modal, Form, InputNumber, Select, message, Statistic, Row, Col, Card, Alert, Typography, Divider, Slider } from 'antd'
import { useMutation, useQuery } from '@tanstack/react-query'
import { revenueApi } from '@/api/revenue'
import { InfoCircleOutlined } from '@ant-design/icons'

const { Option } = Select
const { Text } = Typography

interface CopyRevenuePlanModalProps {
  open: boolean
  targetYear: number
  departmentId?: number
  onClose: () => void
  onSuccess: () => void
}

const CopyRevenuePlanModal: React.FC<CopyRevenuePlanModalProps> = ({
  open,
  targetYear,
  departmentId,
  onClose,
  onSuccess
}) => {
  const [form] = Form.useForm()
  const [selectedSourceYear, setSelectedSourceYear] = useState<number | null>(null)
  const [coefficient, setCoefficient] = useState<number>(1.0)

  // Load source plans for preview
  const { data: sourcePlans, isLoading: isLoadingSource } = useQuery({
    queryKey: ['revenue-plans-preview', selectedSourceYear, departmentId],
    queryFn: () =>
      revenueApi.plans.getAll({
        year: selectedSourceYear!,
        department_id: departmentId,
      }),
    enabled: !!selectedSourceYear && open,
  })

  const copyMutation = useMutation({
    mutationFn: ({ sourceYear, coefficient }: { sourceYear: number; coefficient: number }) =>
      revenueApi.plans.copyPlan(targetYear, sourceYear, coefficient, departmentId),
    onSuccess: (data) => {
      message.success(
        `План доходов скопирован! Создано планов: ${data.created_plans}, версий: ${data.created_versions}, деталей: ${data.created_details}`
      )
      onSuccess()
      onClose()
      form.resetFields()
      setSelectedSourceYear(null)
    },
    onError: (error: any) => {
      message.error(`Ошибка копирования: ${error.response?.data?.detail || error.message}`)
    },
  })

  const handleSubmit = (values: any) => {
    copyMutation.mutate({
      sourceYear: values.sourceYear,
      coefficient: values.coefficient,
    })
  }

  const handleCancel = () => {
    form.resetFields()
    setSelectedSourceYear(null)
    onClose()
  }

  // Generate list of last 10 years
  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 10 }, (_, i) => currentYear - i + 1).filter((y) => y !== targetYear)

  // Calculate statistics from source data
  const statistics = useMemo(() => {
    if (!sourcePlans || sourcePlans.length === 0) return null

    let totalRevenue = 0
    let plansCount = 0

    sourcePlans.forEach((plan) => {
      plansCount++
      totalRevenue += Number(plan.total_planned_revenue || 0)
    })

    return {
      totalRevenue,
      plansCount,
      totalAfterCoefficient: totalRevenue * coefficient,
    }
  }, [sourcePlans, coefficient])

  // Change percentage
  const changePercent = ((coefficient - 1) * 100).toFixed(1)

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <InfoCircleOutlined style={{ color: '#1890ff' }} />
          <span>Скопировать план доходов в {targetYear} год</span>
        </div>
      }
      open={open}
      onCancel={handleCancel}
      onOk={() => form.submit()}
      confirmLoading={copyMutation.isPending}
      width={800}
      okText="Скопировать план"
      cancelText="Отмена"
      okButtonProps={{
        disabled: !selectedSourceYear || isLoadingSource,
        loading: copyMutation.isPending,
      }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          sourceYear: targetYear - 1,
          coefficient: 1.0,
        }}
      >
        <Alert
          message="Копирование плана доходов"
          description="Все утвержденные (approved) планы из выбранного года будут скопированы с учетом коэффициента корректировки. Для каждого плана будет создана версия v1 со статусом Draft."
          type="info"
          showIcon
          style={{ marginBottom: 20 }}
        />

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="sourceYear"
              label="Исходный год"
              rules={[{ required: true, message: 'Выберите исходный год' }]}
            >
              <Select
                placeholder="Выберите год"
                size="large"
                onChange={(value) => {
                  setSelectedSourceYear(value)
                  form.setFieldValue('sourceYear', value)
                }}
              >
                {years.map((year) => (
                  <Option key={year} value={year}>
                    {year} год
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>

          <Col span={12}>
            <Form.Item
              name="coefficient"
              label="Коэффициент корректировки"
              rules={[{ required: true, message: 'Введите коэффициент' }]}
            >
              <InputNumber
                min={0.1}
                max={10}
                step={0.05}
                size="large"
                style={{ width: '100%' }}
                placeholder="Например: 1.1"
                onChange={(value) => setCoefficient(value || 1.0)}
              />
            </Form.Item>
          </Col>
        </Row>

        <div style={{ marginBottom: 16 }}>
          <Text type="secondary">Быстрая настройка: </Text>
          <Slider
            min={0.5}
            max={2.0}
            step={0.05}
            value={coefficient}
            onChange={(value) => {
              setCoefficient(value)
              form.setFieldValue('coefficient', value)
            }}
            marks={{
              0.5: '-50%',
              0.8: '-20%',
              0.9: '-10%',
              1.0: 'Без изменений',
              1.1: '+10%',
              1.2: '+20%',
              1.5: '+50%',
              2.0: '+100%',
            }}
            tooltip={{ formatter: (value) => `${((value! - 1) * 100).toFixed(0)}%` }}
            style={{ marginTop: 20 }}
          />
        </div>

        {selectedSourceYear && (
          <>
            <Divider>Предпросмотр копирования</Divider>

            {isLoadingSource ? (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Text type="secondary">Загрузка данных из {selectedSourceYear} года...</Text>
              </div>
            ) : statistics ? (
              <>
                <Alert
                  message={
                    <span>
                      Изменение плана доходов:{' '}
                      <Text
                        strong
                        style={{
                          color: coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : '#1890ff',
                        }}
                      >
                        {coefficient > 1 ? '+' : ''}
                        {changePercent}%
                      </Text>
                    </span>
                  }
                  type={coefficient > 1 ? 'success' : coefficient < 1 ? 'warning' : 'info'}
                  style={{ marginBottom: 16 }}
                />

                <Card size="small" title="Статистика плана">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Statistic title="Количество планов" value={statistics.plansCount} suffix="шт" />
                    </Col>
                    <Col span={12}>
                      <Statistic
                        title="Общая плановая выручка"
                        value={statistics.totalRevenue}
                        precision={0}
                        suffix="₽"
                      />
                    </Col>
                  </Row>

                  <Divider style={{ margin: '12px 0' }} />

                  <Row gutter={16}>
                    <Col span={12}>
                      <Card size="small" style={{ backgroundColor: '#fafafa' }}>
                        <Statistic
                          title={`Было (${selectedSourceYear})`}
                          value={statistics.totalRevenue}
                          precision={0}
                          suffix="₽"
                          valueStyle={{ fontSize: 20 }}
                        />
                      </Card>
                    </Col>
                    <Col span={12}>
                      <Card
                        size="small"
                        style={{
                          backgroundColor:
                            coefficient > 1 ? '#f6ffed' : coefficient < 1 ? '#fff1f0' : '#e6f7ff',
                          borderColor:
                            coefficient > 1 ? '#b7eb8f' : coefficient < 1 ? '#ffa39e' : '#91d5ff',
                        }}
                      >
                        <Statistic
                          title={`Станет (${targetYear})`}
                          value={statistics.totalAfterCoefficient}
                          precision={0}
                          suffix="₽"
                          valueStyle={{
                            fontSize: 20,
                            color:
                              coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : '#1890ff',
                          }}
                          prefix={coefficient > 1 ? '↑' : coefficient < 1 ? '↓' : '→'}
                        />
                      </Card>
                    </Col>
                  </Row>
                </Card>

                <Alert
                  message="Детали операции"
                  description={
                    <div style={{ fontSize: 12 }}>
                      <p style={{ margin: '8px 0' }}>
                        • Будет скопировано <Text strong>{statistics.plansCount}</Text> планов доходов
                      </p>
                      <p style={{ margin: '8px 0' }}>
                        • Для каждого плана будет создана версия v1 со статусом Draft
                      </p>
                      <p style={{ margin: '8px 0' }}>
                        • Плановая выручка: {statistics.totalRevenue.toLocaleString('ru-RU')} ₽ →{' '}
                        <Text
                          strong
                          style={{
                            color:
                              coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : undefined,
                          }}
                        >
                          {statistics.totalAfterCoefficient.toLocaleString('ru-RU')} ₽
                        </Text>
                      </p>
                      <p style={{ margin: '8px 0' }}>
                        • Изменение выручки:{' '}
                        <Text
                          strong
                          style={{
                            color:
                              coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : '#1890ff',
                          }}
                        >
                          {(statistics.totalAfterCoefficient - statistics.totalRevenue).toLocaleString(
                            'ru-RU'
                          )}{' '}
                          ₽ ({changePercent}%)
                        </Text>
                      </p>
                    </div>
                  }
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              </>
            ) : (
              <Alert
                message="Нет данных"
                description={`В ${selectedSourceYear} году нет утвержденных планов доходов для копирования. Выберите другой год.`}
                type="warning"
                showIcon
              />
            )}
          </>
        )}
      </Form>
    </Modal>
  )
}

export default CopyRevenuePlanModal
