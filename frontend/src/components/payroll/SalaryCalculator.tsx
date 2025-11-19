import { useState, useMemo } from 'react'
import {
  Card,
  Form,
  InputNumber,
  Select,
  Row,
  Col,
  Statistic,
  Divider,
  Alert,
  Button,
  Space,
  Descriptions,
  Typography,
} from 'antd'
import {
  CalculatorOutlined,
  DownloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons'
import type { BonusType } from '@/types/payroll'

const { Option } = Select
const { Title, Text, Paragraph } = Typography

interface CalculationResult {
  baseSalary: number
  monthlyBonusCalculated: number
  quarterlyBonusCalculated: number
  annualBonusCalculated: number
  totalGross: number
  incomeTax: number
  netAmount: number
  depremiationApplied: boolean
}

interface SalaryCalculatorProps {
  defaultValues?: {
    baseSalary?: number
    kpiPercentage?: number
    monthlyBonusBase?: number
    quarterlyBonusBase?: number
    annualBonusBase?: number
  }
}

export const SalaryCalculator: React.FC<SalaryCalculatorProps> = ({
  defaultValues,
}) => {
  const [form] = Form.useForm()

  // Form values state
  const [baseSalary, setBaseSalary] = useState<number>(defaultValues?.baseSalary || 100000)
  const [kpiPercentage, setKpiPercentage] = useState<number>(
    defaultValues?.kpiPercentage || 100
  )
  const [depremiumThreshold, setDepremiumThreshold] = useState<number>(10)

  const [monthlyBonusType, setMonthlyBonusType] = useState<BonusType>('PERFORMANCE_BASED')
  const [monthlyBonusBase, setMonthlyBonusBase] = useState<number>(
    defaultValues?.monthlyBonusBase || 30000
  )
  const [monthlyFixedPart, setMonthlyFixedPart] = useState<number>(50)

  const [quarterlyBonusType, setQuarterlyBonusType] =
    useState<BonusType>('PERFORMANCE_BASED')
  const [quarterlyBonusBase, setQuarterlyBonusBase] = useState<number>(
    defaultValues?.quarterlyBonusBase || 0
  )
  const [quarterlyFixedPart, setQuarterlyFixedPart] = useState<number>(50)

  const [annualBonusType, setAnnualBonusType] = useState<BonusType>('PERFORMANCE_BASED')
  const [annualBonusBase, setAnnualBonusBase] = useState<number>(
    defaultValues?.annualBonusBase || 0
  )
  const [annualFixedPart, setAnnualFixedPart] = useState<number>(50)

  // Calculation logic (matches backend calculate_bonus function)
  const calculateBonus = (
    baseAmount: number,
    bonusType: BonusType,
    kpi: number,
    fixedPart: number,
    threshold: number
  ): number => {
    // FIXED type always returns base amount
    if (bonusType === 'FIXED') {
      return baseAmount
    }

    // Apply depremium threshold
    if (kpi < threshold) {
      return 0 // Полное депремирование
    }

    // PERFORMANCE_BASED calculation
    if (bonusType === 'PERFORMANCE_BASED') {
      return baseAmount * (kpi / 100)
    }

    // MIXED calculation
    if (bonusType === 'MIXED') {
      const fixedAmount = baseAmount * (fixedPart / 100)
      const performanceAmount = baseAmount * ((100 - fixedPart) / 100) * (kpi / 100)
      return fixedAmount + performanceAmount
    }

    return 0
  }

  // Calculate all values
  const calculation: CalculationResult = useMemo(() => {
    const depremiationApplied = kpiPercentage < depremiumThreshold

    const monthlyBonus = calculateBonus(
      monthlyBonusBase,
      monthlyBonusType,
      kpiPercentage,
      monthlyFixedPart,
      depremiumThreshold
    )

    const quarterlyBonus = calculateBonus(
      quarterlyBonusBase,
      quarterlyBonusType,
      kpiPercentage,
      quarterlyFixedPart,
      depremiumThreshold
    )

    const annualBonus = calculateBonus(
      annualBonusBase,
      annualBonusType,
      kpiPercentage,
      annualFixedPart,
      depremiumThreshold
    )

    const totalGross = baseSalary + monthlyBonus + quarterlyBonus + annualBonus
    const incomeTax = totalGross * 0.13 // НДФЛ 13%
    const netAmount = totalGross - incomeTax

    return {
      baseSalary,
      monthlyBonusCalculated: monthlyBonus,
      quarterlyBonusCalculated: quarterlyBonus,
      annualBonusCalculated: annualBonus,
      totalGross,
      incomeTax,
      netAmount,
      depremiationApplied,
    }
  }, [
    baseSalary,
    kpiPercentage,
    depremiumThreshold,
    monthlyBonusBase,
    monthlyBonusType,
    monthlyFixedPart,
    quarterlyBonusBase,
    quarterlyBonusType,
    quarterlyFixedPart,
    annualBonusBase,
    annualBonusType,
    annualFixedPart,
  ])

  // Export to JSON (for demo purposes - can be enhanced to PDF/Excel)
  const handleExport = () => {
    const exportData = {
      input: {
        baseSalary,
        kpiPercentage,
        depremiumThreshold,
        monthlyBonus: {
          type: monthlyBonusType,
          base: monthlyBonusBase,
          fixedPart: monthlyBonusType === 'MIXED' ? monthlyFixedPart : null,
        },
        quarterlyBonus: {
          type: quarterlyBonusType,
          base: quarterlyBonusBase,
          fixedPart: quarterlyBonusType === 'MIXED' ? quarterlyFixedPart : null,
        },
        annualBonus: {
          type: annualBonusType,
          base: annualBonusBase,
          fixedPart: annualBonusType === 'MIXED' ? annualFixedPart : null,
        },
      },
      result: calculation,
      timestamp: new Date().toISOString(),
    }

    const dataStr = JSON.stringify(exportData, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `salary_calculation_${new Date().toISOString().split('T')[0]}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const bonusTypeLabel = (type: BonusType) => {
    switch (type) {
      case 'FIXED':
        return 'Фиксированная'
      case 'PERFORMANCE_BASED':
        return 'Результативная'
      case 'MIXED':
        return 'Смешанная'
      default:
        return type
    }
  }

  const getFormulaText = (type: BonusType, fixedPart: number) => {
    if (type === 'FIXED') {
      return 'Премия = База'
    }
    if (type === 'PERFORMANCE_BASED') {
      return 'Премия = База × (КПИ% / 100)'
    }
    if (type === 'MIXED') {
      return `Премия = База × ${fixedPart}% + База × ${100 - fixedPart}% × (КПИ% / 100)`
    }
    return ''
  }

  return (
    <Card
      title={
        <Space>
          <CalculatorOutlined />
          <span>Онлайн-калькулятор зарплаты</span>
        </Space>
      }
      extra={
        <Button icon={<DownloadOutlined />} onClick={handleExport}>
          Экспорт результатов
        </Button>
      }
    >
      <Row gutter={[24, 24]}>
        {/* Input Form */}
        <Col xs={24} lg={12}>
          <Card type="inner" title="Исходные данные">
            <Form form={form} layout="vertical">
              <Title level={5}>Базовые параметры</Title>

              <Form.Item label="Базовый оклад (₽)">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  value={baseSalary}
                  onChange={(value) => setBaseSalary(value || 0)}
                  formatter={(value) =>
                    `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
                  }
                  parser={(value) => value!.replace(/\s/g, '') as unknown as number}
                />
              </Form.Item>

              <Form.Item
                label="КПИ%"
                tooltip="Процент выполнения KPI (0-200%). Если ниже порога депремирования, все премии = 0"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={200}
                  value={kpiPercentage}
                  onChange={(value) => setKpiPercentage(value || 0)}
                  addonAfter="%"
                />
              </Form.Item>

              <Form.Item
                label="Порог депремирования (%)"
                tooltip="Если КПИ% ниже этого порога, все премии обнуляются"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  max={100}
                  value={depremiumThreshold}
                  onChange={(value) => setDepremiumThreshold(value || 0)}
                  addonAfter="%"
                />
              </Form.Item>

              <Divider />

              <Title level={5}>Месячная премия</Title>
              <Form.Item label="Тип премии">
                <Select
                  value={monthlyBonusType}
                  onChange={setMonthlyBonusType}
                  style={{ width: '100%' }}
                >
                  <Option value="FIXED">Фиксированная</Option>
                  <Option value="PERFORMANCE_BASED">Результативная</Option>
                  <Option value="MIXED">Смешанная</Option>
                </Select>
              </Form.Item>

              <Form.Item label="Базовая премия (₽)">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  value={monthlyBonusBase}
                  onChange={(value) => setMonthlyBonusBase(value || 0)}
                  formatter={(value) =>
                    `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
                  }
                  parser={(value) => value!.replace(/\s/g, '') as unknown as number}
                />
              </Form.Item>

              {monthlyBonusType === 'MIXED' && (
                <Form.Item label="Фиксированная часть (%)">
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    max={100}
                    value={monthlyFixedPart}
                    onChange={(value) => setMonthlyFixedPart(value || 0)}
                    addonAfter="%"
                  />
                </Form.Item>
              )}

              <Alert
                message={
                  <Text>
                    <strong>Формула:</strong> {getFormulaText(monthlyBonusType, monthlyFixedPart)}
                  </Text>
                }
                type="info"
                showIcon
                icon={<InfoCircleOutlined />}
                style={{ marginBottom: 16 }}
              />

              <Divider />

              <Title level={5}>Квартальная премия</Title>
              <Form.Item label="Тип премии">
                <Select
                  value={quarterlyBonusType}
                  onChange={setQuarterlyBonusType}
                  style={{ width: '100%' }}
                >
                  <Option value="FIXED">Фиксированная</Option>
                  <Option value="PERFORMANCE_BASED">Результативная</Option>
                  <Option value="MIXED">Смешанная</Option>
                </Select>
              </Form.Item>

              <Form.Item label="Базовая премия (₽)">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  value={quarterlyBonusBase}
                  onChange={(value) => setQuarterlyBonusBase(value || 0)}
                  formatter={(value) =>
                    `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
                  }
                  parser={(value) => value!.replace(/\s/g, '') as unknown as number}
                />
              </Form.Item>

              {quarterlyBonusType === 'MIXED' && (
                <Form.Item label="Фиксированная часть (%)">
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    max={100}
                    value={quarterlyFixedPart}
                    onChange={(value) => setQuarterlyFixedPart(value || 0)}
                    addonAfter="%"
                  />
                </Form.Item>
              )}

              <Divider />

              <Title level={5}>Годовая премия</Title>
              <Form.Item label="Тип премии">
                <Select
                  value={annualBonusType}
                  onChange={setAnnualBonusType}
                  style={{ width: '100%' }}
                >
                  <Option value="FIXED">Фиксированная</Option>
                  <Option value="PERFORMANCE_BASED">Результативная</Option>
                  <Option value="MIXED">Смешанная</Option>
                </Select>
              </Form.Item>

              <Form.Item label="Базовая премия (₽)">
                <InputNumber
                  style={{ width: '100%' }}
                  min={0}
                  value={annualBonusBase}
                  onChange={(value) => setAnnualBonusBase(value || 0)}
                  formatter={(value) =>
                    `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')
                  }
                  parser={(value) => value!.replace(/\s/g, '') as unknown as number}
                />
              </Form.Item>

              {annualBonusType === 'MIXED' && (
                <Form.Item label="Фиксированная часть (%)">
                  <InputNumber
                    style={{ width: '100%' }}
                    min={0}
                    max={100}
                    value={annualFixedPart}
                    onChange={(value) => setAnnualFixedPart(value || 0)}
                    addonAfter="%"
                  />
                </Form.Item>
              )}
            </Form>
          </Card>
        </Col>

        {/* Results */}
        <Col xs={24} lg={12}>
          <Card type="inner" title="Результаты расчета">
            {calculation.depremiationApplied && (
              <Alert
                message="Депремирование применено!"
                description={`КПИ% (${kpiPercentage}%) ниже порога (${depremiumThreshold}%). Все премии обнулены.`}
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            <Descriptions bordered column={1} size="small">
              <Descriptions.Item label="Базовый оклад">
                <Text strong>
                  {calculation.baseSalary.toLocaleString('ru-RU')} ₽
                </Text>
              </Descriptions.Item>

              <Descriptions.Item label={`Месячная премия (${bonusTypeLabel(monthlyBonusType)})`}>
                <Text strong style={{ color: calculation.depremiationApplied ? '#ff4d4f' : '#52c41a' }}>
                  {calculation.monthlyBonusCalculated.toLocaleString('ru-RU')} ₽
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {getFormulaText(monthlyBonusType, monthlyFixedPart)}
                </Text>
              </Descriptions.Item>

              <Descriptions.Item label={`Квартальная премия (${bonusTypeLabel(quarterlyBonusType)})`}>
                <Text strong style={{ color: calculation.depremiationApplied ? '#ff4d4f' : '#52c41a' }}>
                  {calculation.quarterlyBonusCalculated.toLocaleString('ru-RU')} ₽
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {getFormulaText(quarterlyBonusType, quarterlyFixedPart)}
                </Text>
              </Descriptions.Item>

              <Descriptions.Item label={`Годовая премия (${bonusTypeLabel(annualBonusType)})`}>
                <Text strong style={{ color: calculation.depremiationApplied ? '#ff4d4f' : '#52c41a' }}>
                  {calculation.annualBonusCalculated.toLocaleString('ru-RU')} ₽
                </Text>
                <br />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {getFormulaText(annualBonusType, annualFixedPart)}
                </Text>
              </Descriptions.Item>
            </Descriptions>

            <Divider />

            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Итого до налогов"
                  value={calculation.totalGross}
                  precision={2}
                  suffix="₽"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="НДФЛ (13%)"
                  value={calculation.incomeTax}
                  precision={2}
                  suffix="₽"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>

            <Divider />

            <Card
              style={{
                backgroundColor: '#f0f5ff',
                border: '2px solid #1890ff',
              }}
            >
              <Statistic
                title={
                  <Text strong style={{ fontSize: 18 }}>
                    Сумма на руки
                  </Text>
                }
                value={calculation.netAmount}
                precision={2}
                suffix="₽"
                valueStyle={{ color: '#52c41a', fontSize: 32, fontWeight: 'bold' }}
              />
            </Card>

            <Divider />

            <Title level={5}>Формула расчета НДФЛ</Title>
            <Paragraph>
              <Text code>НДФЛ = (Оклад + Все премии) × 13%</Text>
            </Paragraph>
            <Paragraph>
              <Text code>
                НДФЛ = ({calculation.baseSalary.toLocaleString('ru-RU')} +{' '}
                {calculation.monthlyBonusCalculated.toLocaleString('ru-RU')} +{' '}
                {calculation.quarterlyBonusCalculated.toLocaleString('ru-RU')} +{' '}
                {calculation.annualBonusCalculated.toLocaleString('ru-RU')}) × 0.13 ={' '}
                {calculation.incomeTax.toLocaleString('ru-RU')} ₽
              </Text>
            </Paragraph>
          </Card>
        </Col>
      </Row>
    </Card>
  )
}
