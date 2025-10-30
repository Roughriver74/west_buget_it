import React, { useState, useMemo } from 'react'
import { Modal, Form, InputNumber, Select, message, Statistic, Row, Col, Card, Alert, Progress, Typography, Divider, Slider } from 'antd'
import { useMutation, useQuery } from '@tanstack/react-query'
import { budgetApi } from '@/api'
import { InfoCircleOutlined } from '@ant-design/icons'

const { Option } = Select
const { Text } = Typography

interface CopyPlanModalProps {
  open: boolean
  targetYear: number
  departmentId?: number
  onClose: () => void
  onSuccess: () => void
}

const CopyPlanModal: React.FC<CopyPlanModalProps> = ({ open, targetYear, departmentId, onClose, onSuccess }) => {
  const [form] = Form.useForm()
  const [selectedSourceYear, setSelectedSourceYear] = useState<number | null>(null)
  const [coefficient, setCoefficient] = useState<number>(1.0)

  // Загружаем данные из исходного года для предпросмотра
  const { data: sourceData, isLoading: isLoadingSource } = useQuery({
    queryKey: ['budget-plan-preview', selectedSourceYear, departmentId],
    queryFn: () => budgetApi.getPlanForYear(selectedSourceYear!, departmentId),
    enabled: !!selectedSourceYear && open,
  })

  const copyMutation = useMutation({
    mutationFn: ({ sourceYear, coefficient }: { sourceYear: number; coefficient: number }) =>
      budgetApi.copyPlan(targetYear, sourceYear, coefficient, departmentId),
    onSuccess: (data) => {
      message.success(`План скопирован! Создано: ${data.created_entries}, обновлено: ${data.updated_entries}`)
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

  // Генерируем список последних 10 лет
  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 10 }, (_, i) => currentYear - i + 1).filter((y) => y !== targetYear)

  // Вычисляем статистику из исходных данных
  const statistics = useMemo(() => {
    if (!sourceData) return null

    let totalPlanned = 0
    let totalCapex = 0
    let totalOpex = 0
    let categoriesCount = 0

    sourceData.categories.forEach((category) => {
      categoriesCount++
      Object.values(category.months).forEach((month) => {
        totalPlanned += month.planned_amount || 0
        totalCapex += month.capex_planned || 0
        totalOpex += month.opex_planned || 0
      })
    })

    return {
      totalPlanned,
      totalCapex,
      totalOpex,
      categoriesCount,
      totalAfterCoefficient: totalPlanned * coefficient,
      capexAfterCoefficient: totalCapex * coefficient,
      opexAfterCoefficient: totalOpex * coefficient,
    }
  }, [sourceData, coefficient])

  // Процент изменения
  const changePercent = ((coefficient - 1) * 100).toFixed(1)

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <InfoCircleOutlined style={{ color: '#1890ff' }} />
          <span>Скопировать план в {targetYear} год</span>
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
        loading: copyMutation.isPending
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
          message="Копирование бюджетного плана"
          description="Все данные из выбранного года будут скопированы с учетом коэффициента корректировки. Это позволяет быстро создать план на следующий год с учетом инфляции или изменения объемов."
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
                <Progress type="circle" percent={66} status="active" />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">Загрузка данных из {selectedSourceYear} года...</Text>
                </div>
              </div>
            ) : statistics ? (
              <>
                <Alert
                  message={
                    <span>
                      Изменение бюджета: {' '}
                      <Text strong style={{ color: coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : '#1890ff' }}>
                        {coefficient > 1 ? '+' : ''}{changePercent}%
                      </Text>
                    </span>
                  }
                  type={coefficient > 1 ? 'success' : coefficient < 1 ? 'warning' : 'info'}
                  style={{ marginBottom: 16 }}
                />

                <Card size="small" title="Статистика плана">
                  <Row gutter={16}>
                    <Col span={8}>
                      <Statistic
                        title="Категорий"
                        value={statistics.categoriesCount}
                        suffix="шт"
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="OPEX"
                        value={statistics.totalOpex}
                        precision={0}
                        suffix="₽"
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="CAPEX"
                        value={statistics.totalCapex}
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
                          value={statistics.totalPlanned}
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
                          backgroundColor: coefficient > 1 ? '#f6ffed' : coefficient < 1 ? '#fff1f0' : '#e6f7ff',
                          borderColor: coefficient > 1 ? '#b7eb8f' : coefficient < 1 ? '#ffa39e' : '#91d5ff'
                        }}
                      >
                        <Statistic
                          title={`Станет (${targetYear})`}
                          value={statistics.totalAfterCoefficient}
                          precision={0}
                          suffix="₽"
                          valueStyle={{
                            fontSize: 20,
                            color: coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : '#1890ff'
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
                        • Будет скопировано <Text strong>{statistics.categoriesCount}</Text> категорий
                      </p>
                      <p style={{ margin: '8px 0' }}>
                        • OPEX: {statistics.totalOpex.toLocaleString('ru-RU')} ₽ → {' '}
                        <Text strong style={{ color: coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : undefined }}>
                          {statistics.opexAfterCoefficient.toLocaleString('ru-RU')} ₽
                        </Text>
                      </p>
                      <p style={{ margin: '8px 0' }}>
                        • CAPEX: {statistics.totalCapex.toLocaleString('ru-RU')} ₽ → {' '}
                        <Text strong style={{ color: coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : undefined }}>
                          {statistics.capexAfterCoefficient.toLocaleString('ru-RU')} ₽
                        </Text>
                      </p>
                      <p style={{ margin: '8px 0' }}>
                        • Изменение общего бюджета: {' '}
                        <Text strong style={{ color: coefficient > 1 ? '#52c41a' : coefficient < 1 ? '#ff4d4f' : '#1890ff' }}>
                          {(statistics.totalAfterCoefficient - statistics.totalPlanned).toLocaleString('ru-RU')} ₽ ({changePercent}%)
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
                description={`В ${selectedSourceYear} году нет данных для копирования. Выберите другой год.`}
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

export default CopyPlanModal
