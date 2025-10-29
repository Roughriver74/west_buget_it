import { useState } from 'react'
import {
  Card,
  Form,
  InputNumber,
  Button,
  Select,
  Space,
  Typography,
  Table,
  Statistic,
  Row,
  Col,
  Alert,
  Divider,
} from 'antd'
import { CalculatorOutlined } from '@ant-design/icons'
import { ndflAPI, type NDFLCalculationResult } from '@/api'

const { Title, Text } = Typography
const { Option } = Select

const NDFLCalculator = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<NDFLCalculationResult | null>(null)

  const handleCalculate = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)

      const response = await ndflAPI.calculateNDFL({
        annual_income: values.annual_income,
        year: values.year,
      })

      setResult(response)
    } catch (error) {
      console.error('Calculation failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: 'Диапазон дохода',
      key: 'range',
      render: (_: any, record: any) => (
        <span>
          {record.from.toLocaleString('ru-RU')} -{' '}
          {record.to ? record.to.toLocaleString('ru-RU') : '∞'} ₽
        </span>
      ),
    },
    {
      title: 'Ставка',
      dataIndex: 'rate',
      key: 'rate',
      render: (rate: number) => `${(rate * 100).toFixed(0)}%`,
    },
    {
      title: 'Налогооблагаемая сумма',
      dataIndex: 'taxable_amount',
      key: 'taxable_amount',
      render: (amount: number) => amount ? `${amount.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽` : '—',
    },
    {
      title: 'НДФЛ',
      dataIndex: 'tax_amount',
      key: 'tax_amount',
      render: (amount: number) => amount ? (
        <Text strong>{amount.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽</Text>
      ) : '—',
    },
  ]

  return (
    <Card>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={4}>
            <CalculatorOutlined /> Калькулятор НДФЛ
          </Title>
          <Text type="secondary">
            Расчет прогрессивного НДФЛ по новой шкале 2024-2025
          </Text>
        </div>

        <Alert
          message="Прогрессивная шкала НДФЛ"
          description={
            <div>
              <div><strong>2024:</strong> 13% до 5 млн, 15% свыше 5 млн (2 ступени)</div>
              <div><strong>2025+:</strong> 13%/15%/18%/20%/22% по 5 ступеням</div>
            </div>
          }
          type="info"
          showIcon
        />

        <Form
          form={form}
          layout="inline"
          initialValues={{
            year: new Date().getFullYear(),
          }}
        >
          <Form.Item
            name="annual_income"
            label="Годовой доход"
            rules={[{ required: true, message: 'Введите годовой доход' }]}
          >
            <InputNumber
              style={{ width: 200 }}
              placeholder="Например: 6000000"
              min={0}
              formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
              parser={(value) => Number(value!.replace(/\s/g, '')) as any}
              addonAfter="₽"
            />
          </Form.Item>

          <Form.Item
            name="year"
            label="Год"
            rules={[{ required: true, message: 'Выберите год' }]}
          >
            <Select style={{ width: 120 }}>
              <Option value={2024}>2024</Option>
              <Option value={2025}>2025</Option>
              <Option value={2026}>2026</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              icon={<CalculatorOutlined />}
              onClick={handleCalculate}
              loading={loading}
            >
              Рассчитать
            </Button>
          </Form.Item>
        </Form>

        {result && (
          <>
            <Divider />

            <Row gutter={16}>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Итого НДФЛ"
                    value={result.total_tax}
                    precision={2}
                    suffix="₽"
                    valueStyle={{ color: '#cf1322' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="Эффективная ставка"
                    value={result.effective_rate}
                    precision={2}
                    suffix="%"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col xs={24} sm={8}>
                <Card>
                  <Statistic
                    title="На руки (чистыми)"
                    value={result.net_income}
                    precision={2}
                    suffix="₽"
                    valueStyle={{ color: '#3f8600' }}
                  />
                </Card>
              </Col>
            </Row>

            <div>
              <Title level={5}>Разбивка по ступеням налогообложения</Title>
              <Text type="secondary">
                Система: {result.system === '5-tier' ? 'Пятиступенчатая (2025+)' : 'Двухступенчатая (2024)'}
              </Text>
            </div>

            <Table
              columns={columns}
              dataSource={result.breakdown}
              rowKey={(record) => `${record.from}-${record.to}`}
              pagination={false}
              size="small"
              summary={(pageData) => {
                const totalTax = pageData.reduce((sum, item) => sum + (item.tax_amount || 0), 0)
                return (
                  <Table.Summary.Row style={{ backgroundColor: '#fafafa' }}>
                    <Table.Summary.Cell index={0} colSpan={3}>
                      <Text strong>Итого:</Text>
                    </Table.Summary.Cell>
                    <Table.Summary.Cell index={1}>
                      <Text strong style={{ color: '#cf1322' }}>
                        {totalTax.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} ₽
                      </Text>
                    </Table.Summary.Cell>
                  </Table.Summary.Row>
                )
              }}
            />

            <Alert
              message="Детальный расчет"
              description={
                <div style={{ fontFamily: 'monospace', fontSize: '12px' }}>
                  {result.details.map((detail: string, idx: number) => (
                    <div key={idx}>{detail}</div>
                  ))}
                </div>
              }
              type="success"
            />
          </>
        )}
      </Space>
    </Card>
  )
}

export default NDFLCalculator
