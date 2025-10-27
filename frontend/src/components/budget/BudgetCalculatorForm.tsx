/**
 * Budget Calculator Form Component
 * Modal form for calculating budget using different methods
 */
import React, { useState } from 'react'
import {
  Modal,
  Form,
  Select,
  InputNumber,
  Tabs,
  Space,
  Button,
  Alert,
  Descriptions,
  Typography,
} from 'antd'
import { CalculatorOutlined } from '@ant-design/icons'
import {
  useCalculateByAverage,
  useCalculateByGrowth,
  useCalculateByDriver,
  useBaseline,
} from '@/hooks/useBudgetPlanning'
import type {
  CalculateByAverageRequest,
  CalculateByGrowthRequest,
  CalculateByDriverRequest,
  CalculationResult,
} from '@/types/budgetPlanning'

const { Text } = Typography

interface BudgetCalculatorFormProps {
  open: boolean
  onClose: () => void
  onApply?: (result: CalculationResult) => void
  categories: Array<{ id: number; name: string }>
  defaultCategoryId?: number
  defaultYear?: number
  departmentId: number
}

type CalculationMethod = 'average' | 'growth' | 'driver'

export const BudgetCalculatorForm: React.FC<BudgetCalculatorFormProps> = ({
  open,
  onClose,
  onApply,
  categories,
  defaultCategoryId,
  defaultYear = new Date().getFullYear(),
  departmentId,
}) => {
  const [form] = Form.useForm()
  const [activeMethod, setActiveMethod] = useState<CalculationMethod>('average')
  const [calculationResult, setCalculationResult] = useState<CalculationResult | null>(null)

  const calculateByAverage = useCalculateByAverage()
  const calculateByGrowth = useCalculateByGrowth()
  const calculateByDriver = useCalculateByDriver()

  // Get baseline data when category is selected
  const categoryId = Form.useWatch('category_id', form)
  const baseYear = Form.useWatch('base_year', form) || defaultYear - 1

  const { data: baseline } = useBaseline(
    categoryId || defaultCategoryId || 0,
    baseYear,
    departmentId
  )

  const handleCalculate = async () => {
    try {
      await form.validateFields()
      const values = form.getFieldsValue()

      let result: CalculationResult | undefined

      if (activeMethod === 'average') {
        const request: CalculateByAverageRequest = {
          category_id: values.category_id,
          base_year: values.base_year,
          adjustment_percent: values.adjustment_percent || 0,
          target_year: values.target_year,
        }
        result = await calculateByAverage.mutateAsync(request)
      } else if (activeMethod === 'growth') {
        const request: CalculateByGrowthRequest = {
          category_id: values.category_id,
          base_year: values.base_year,
          growth_rate: values.growth_rate,
          inflation_rate: values.inflation_rate || 0,
          target_year: values.target_year,
        }
        result = await calculateByGrowth.mutateAsync(request)
      } else if (activeMethod === 'driver') {
        const request: CalculateByDriverRequest = {
          category_id: values.category_id,
          base_year: values.base_year,
          driver_type: values.driver_type,
          base_driver_value: values.base_driver_value,
          planned_driver_value: values.planned_driver_value,
          cost_per_unit: values.cost_per_unit,
          adjustment_percent: values.adjustment_percent || 0,
          target_year: values.target_year,
        }
        result = await calculateByDriver.mutateAsync(request)
      }

      if (result) {
        setCalculationResult(result)
      }
    } catch (error) {
      console.error('Calculation error:', error)
    }
  }

  const handleApply = () => {
    if (calculationResult && onApply) {
      onApply(calculationResult)
      handleClose()
    }
  }

  const handleClose = () => {
    form.resetFields()
    setCalculationResult(null)
    onClose()
  }

  const renderAverageForm = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Form.Item
        name="category_id"
        label="Категория расходов"
        rules={[{ required: true, message: 'Выберите категорию' }]}
      >
        <Select
          showSearch
          placeholder="Выберите категорию"
          optionFilterProp="children"
        >
          {categories.map((cat) => (
            <Select.Option key={cat.id} value={cat.id}>
              {cat.name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="base_year"
        label="Базовый год"
        rules={[{ required: true, message: 'Укажите базовый год' }]}
        initialValue={defaultYear - 1}
      >
        <InputNumber style={{ width: '100%' }} min={2020} max={defaultYear} />
      </Form.Item>

      <Form.Item
        name="target_year"
        label="Целевой год"
        rules={[{ required: true, message: 'Укажите целевой год' }]}
        initialValue={defaultYear}
      >
        <InputNumber style={{ width: '100%' }} min={defaultYear} max={2030} />
      </Form.Item>

      <Form.Item
        name="adjustment_percent"
        label="Корректировка (%)"
        tooltip="Процент корректировки от среднего значения"
        initialValue={0}
      >
        <InputNumber style={{ width: '100%' }} min={-50} max={100} />
      </Form.Item>

      {baseline && (
        <Alert
          message="Базовые данные"
          description={
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="Всего за год">
                {Number(baseline.total_amount).toLocaleString('ru-RU')} ₽
              </Descriptions.Item>
              <Descriptions.Item label="Среднее в месяц">
                {Number(baseline.monthly_avg).toLocaleString('ru-RU')} ₽
              </Descriptions.Item>
            </Descriptions>
          }
          type="info"
        />
      )}
    </Space>
  )

  const renderGrowthForm = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Form.Item
        name="category_id"
        label="Категория расходов"
        rules={[{ required: true, message: 'Выберите категорию' }]}
      >
        <Select
          showSearch
          placeholder="Выберите категорию"
          optionFilterProp="children"
        >
          {categories.map((cat) => (
            <Select.Option key={cat.id} value={cat.id}>
              {cat.name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="base_year"
        label="Базовый год"
        rules={[{ required: true, message: 'Укажите базовый год' }]}
        initialValue={defaultYear - 1}
      >
        <InputNumber style={{ width: '100%' }} min={2020} max={defaultYear} />
      </Form.Item>

      <Form.Item
        name="target_year"
        label="Целевой год"
        rules={[{ required: true, message: 'Укажите целевой год' }]}
        initialValue={defaultYear}
      >
        <InputNumber style={{ width: '100%' }} min={defaultYear} max={2030} />
      </Form.Item>

      <Form.Item
        name="growth_rate"
        label="Процент роста (%)"
        rules={[{ required: true, message: 'Укажите процент роста' }]}
        tooltip="Ожидаемый рост расходов"
      >
        <InputNumber style={{ width: '100%' }} min={-50} max={100} />
      </Form.Item>

      <Form.Item
        name="inflation_rate"
        label="Инфляция (%)"
        tooltip="Учет инфляции сверх роста"
        initialValue={0}
      >
        <InputNumber style={{ width: '100%' }} min={0} max={50} />
      </Form.Item>

      {baseline && (
        <Alert
          message="Базовые данные"
          description={
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="Всего за год">
                {Number(baseline.total_amount).toLocaleString('ru-RU')} ₽
              </Descriptions.Item>
            </Descriptions>
          }
          type="info"
        />
      )}
    </Space>
  )

  const renderDriverForm = () => (
    <Space direction="vertical" style={{ width: '100%' }} size="large">
      <Form.Item
        name="category_id"
        label="Категория расходов"
        rules={[{ required: true, message: 'Выберите категорию' }]}
      >
        <Select
          showSearch
          placeholder="Выберите категорию"
          optionFilterProp="children"
        >
          {categories.map((cat) => (
            <Select.Option key={cat.id} value={cat.id}>
              {cat.name}
            </Select.Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        name="base_year"
        label="Базовый год"
        rules={[{ required: true, message: 'Укажите базовый год' }]}
        initialValue={defaultYear - 1}
      >
        <InputNumber style={{ width: '100%' }} min={2020} max={defaultYear} />
      </Form.Item>

      <Form.Item
        name="target_year"
        label="Целевой год"
        rules={[{ required: true, message: 'Укажите целевой год' }]}
        initialValue={defaultYear}
      >
        <InputNumber style={{ width: '100%' }} min={defaultYear} max={2030} />
      </Form.Item>

      <Form.Item
        name="driver_type"
        label="Тип драйвера"
        rules={[{ required: true, message: 'Выберите тип драйвера' }]}
      >
        <Select placeholder="Выберите драйвер">
          <Select.Option value="headcount">Численность персонала</Select.Option>
          <Select.Option value="projects">Количество проектов</Select.Option>
          <Select.Option value="revenue">Выручка</Select.Option>
          <Select.Option value="users">Количество пользователей</Select.Option>
          <Select.Option value="devices">Количество устройств</Select.Option>
        </Select>
      </Form.Item>

      <Form.Item
        name="base_driver_value"
        label="Значение драйвера (базовый год)"
        rules={[{ required: true, message: 'Укажите значение' }]}
      >
        <InputNumber style={{ width: '100%' }} min={0} />
      </Form.Item>

      <Form.Item
        name="planned_driver_value"
        label="Значение драйвера (план)"
        rules={[{ required: true, message: 'Укажите значение' }]}
      >
        <InputNumber style={{ width: '100%' }} min={0} />
      </Form.Item>

      <Form.Item
        name="cost_per_unit"
        label="Стоимость на единицу (₽)"
        tooltip="Оставьте пустым для автоматического расчета"
      >
        <InputNumber style={{ width: '100%' }} min={0} />
      </Form.Item>

      <Form.Item
        name="adjustment_percent"
        label="Корректировка (%)"
        initialValue={0}
      >
        <InputNumber style={{ width: '100%' }} min={-50} max={100} />
      </Form.Item>

      {baseline && (
        <Alert
          message="Базовые данные"
          description={
            <Descriptions size="small" column={2}>
              <Descriptions.Item label="Всего за год">
                {Number(baseline.total_amount).toLocaleString('ru-RU')} ₽
              </Descriptions.Item>
            </Descriptions>
          }
          type="info"
        />
      )}
    </Space>
  )

  const tabItems = [
    {
      key: 'average',
      label: 'По среднему',
      children: renderAverageForm(),
    },
    {
      key: 'growth',
      label: 'С учетом роста',
      children: renderGrowthForm(),
    },
    {
      key: 'driver',
      label: 'На основе драйверов',
      children: renderDriverForm(),
    },
  ]

  return (
    <Modal
      title={
        <Space>
          <CalculatorOutlined />
          <span>Калькулятор бюджета</span>
        </Space>
      }
      open={open}
      onCancel={handleClose}
      width={700}
      footer={[
        <Button key="close" onClick={handleClose}>
          Отмена
        </Button>,
        <Button
          key="calculate"
          type="primary"
          onClick={handleCalculate}
          loading={
            calculateByAverage.isPending ||
            calculateByGrowth.isPending ||
            calculateByDriver.isPending
          }
        >
          Рассчитать
        </Button>,
        calculationResult && (
          <Button key="apply" type="primary" onClick={handleApply}>
            Применить
          </Button>
        ),
      ]}
    >
      <Form form={form} layout="vertical">
        <Tabs
          activeKey={activeMethod}
          onChange={(key) => setActiveMethod(key as CalculationMethod)}
          items={tabItems}
        />

        {calculationResult && (
          <Alert
            message="Результат расчета"
            description={
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>Итого за год: </Text>
                <Text style={{ fontSize: 18, color: '#1890ff' }}>
                  {Number(calculationResult.annual_total).toLocaleString('ru-RU')} ₽
                </Text>
                <Text type="secondary">
                  Среднее в месяц: {Number(calculationResult.monthly_avg).toLocaleString('ru-RU')} ₽
                </Text>
                <Text type="secondary">
                  Метод расчета: {calculationResult.calculation_method}
                </Text>
              </Space>
            }
            type="success"
            style={{ marginTop: 16 }}
          />
        )}
      </Form>
    </Modal>
  )
}
