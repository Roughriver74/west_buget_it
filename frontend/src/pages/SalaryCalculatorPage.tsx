import { Card, Typography, Space } from 'antd'
import { SalaryCalculator } from '@/components/payroll/SalaryCalculator'

const { Title, Paragraph } = Typography

const SalaryCalculatorPage = () => {
  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Card>
        <Title level={2}>Калькулятор зарплаты</Title>
        <Paragraph>
          Интерактивный инструмент для расчета заработной платы с учетом базового оклада, KPI
          и различных типов премий. Все расчеты выполняются в реальном времени.
        </Paragraph>
        <Paragraph type="secondary">
          <strong>Типы премий:</strong>
          <ul>
            <li>
              <strong>Фиксированная</strong> - премия выплачивается полностью независимо от КПИ%
            </li>
            <li>
              <strong>Результативная</strong> - премия пропорциональна КПИ% (Премия = База × КПИ% / 100)
            </li>
            <li>
              <strong>Смешанная</strong> - часть премии фиксирована, часть зависит от КПИ%
            </li>
          </ul>
        </Paragraph>
        <Paragraph type="secondary">
          <strong>Депремирование:</strong> Если КПИ% ниже установленного порога (по умолчанию 10%),
          все премии обнуляются (полное депремирование).
        </Paragraph>
      </Card>

      <SalaryCalculator />
    </Space>
  )
}

export default SalaryCalculatorPage
