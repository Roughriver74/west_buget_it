import { Card, Row, Col, Statistic, Progress, Empty, Spin } from 'antd'
import {
  RiseOutlined,
  FallOutlined,
  PercentageOutlined,
  TrophyOutlined,
} from '@ant-design/icons'
import { useQuery } from '@tanstack/react-query'
import { useDepartment } from '@/contexts/DepartmentContext'
import { creditPortfolioApi } from '@/api/creditPortfolio'

export default function CreditPortfolioKPIPage() {
  const { selectedDepartment } = useDepartment()

  const { data: summary, isLoading } = useQuery({
    queryKey: ['credit-portfolio-summary', selectedDepartment?.id],
    queryFn: () =>
      creditPortfolioApi.getSummary({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  })

  if (isLoading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!summary) {
    return (
      <div style={{ padding: 24 }}>
        <Empty description="Нет данных" />
      </div>
    )
  }

  // Calculate KPIs
  const totalDebt = summary.total_receipts - summary.total_expenses
  const debtRatio = summary.total_receipts > 0
    ? ((summary.total_expenses / summary.total_receipts) * 100)
    : 0
  const interestRatio = summary.total_expenses > 0
    ? ((summary.total_interest / summary.total_expenses) * 100)
    : 0
  const principalRatio = summary.total_expenses > 0
    ? ((summary.total_principal / summary.total_expenses) * 100)
    : 0

  return (
    <div style={{ padding: 24 }}>
      <h1 style={{ marginBottom: 24 }}>Кредитный портфель - KPI метрики</h1>

      <Row gutter={[16, 16]}>
        {/* Debt Ratio */}
        <Col xs={24} md={12}>
          <Card>
            <Statistic
              title="Коэффициент погашения"
              value={debtRatio}
              precision={2}
              suffix="%"
              prefix={<PercentageOutlined />}
              valueStyle={{ color: debtRatio > 100 ? '#cf1322' : '#3f8600' }}
            />
            <Progress
              percent={Math.min(debtRatio, 100)}
              strokeColor={debtRatio > 100 ? '#cf1322' : '#3f8600'}
              style={{ marginTop: 16 }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Отношение списаний к поступлениям. Оптимально: 80-100%
            </p>
          </Card>
        </Col>

        {/* Current Debt */}
        <Col xs={24} md={12}>
          <Card>
            <Statistic
              title="Текущая задолженность"
              value={totalDebt}
              precision={2}
              suffix="₽"
              prefix={totalDebt >= 0 ? <RiseOutlined /> : <FallOutlined />}
              valueStyle={{ color: totalDebt >= 0 ? '#3f8600' : '#cf1322' }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Разница между поступлениями и списаниями
            </p>
          </Card>
        </Col>

        {/* Interest Ratio */}
        <Col xs={24} md={12}>
          <Card>
            <Statistic
              title="Доля процентов в платежах"
              value={interestRatio}
              precision={2}
              suffix="%"
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <Progress
              percent={interestRatio}
              strokeColor="#1890ff"
              style={{ marginTop: 16 }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Доля процентов от общей суммы списаний
            </p>
          </Card>
        </Col>

        {/* Principal Ratio */}
        <Col xs={24} md={12}>
          <Card>
            <Statistic
              title="Доля тела кредита в платежах"
              value={principalRatio}
              precision={2}
              suffix="%"
              prefix={<PercentageOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress
              percent={principalRatio}
              strokeColor="#52c41a"
              style={{ marginTop: 16 }}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Доля тела кредита от общей суммы списаний
            </p>
          </Card>
        </Col>

        {/* Active Contracts */}
        <Col xs={24} md={12}>
          <Card>
            <Statistic
              title="Активных договоров"
              value={summary.active_contracts_count}
              prefix={<TrophyOutlined />}
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Количество действующих кредитных договоров
            </p>
          </Card>
        </Col>

        {/* Average Payment */}
        <Col xs={24} md={12}>
          <Card>
            <Statistic
              title="Средний платеж на договор"
              value={summary.active_contracts_count > 0
                ? summary.total_expenses / summary.active_contracts_count
                : 0}
              precision={2}
              suffix="₽"
            />
            <p style={{ marginTop: 8, color: '#8c8c8c', fontSize: 12 }}>
              Средняя сумма списаний на один договор
            </p>
          </Card>
        </Col>
      </Row>

      {/* Summary Info */}
      <Card style={{ marginTop: 24 }} title="Расшифровка показателей">
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <h4>Коэффициент погашения</h4>
            <p>
              Показывает, какой процент от полученных кредитов уже погашен.
              Значение более 100% означает, что списания превышают поступления (переплата).
            </p>
          </Col>
          <Col span={24}>
            <h4>Доля процентов / тела кредита</h4>
            <p>
              Показывает структуру платежей. Высокая доля процентов указывает на
              высокую стоимость обслуживания долга.
            </p>
          </Col>
          <Col span={24}>
            <h4>Средний платеж на договор</h4>
            <p>
              Помогает оценить среднюю нагрузку на один кредитный договор.
            </p>
          </Col>
        </Row>
      </Card>
    </div>
  )
}
