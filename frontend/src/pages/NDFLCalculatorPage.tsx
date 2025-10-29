import { Typography, Space } from 'antd'
import NDFLCalculator from '@/components/payroll/NDFLCalculator'

const { Title, Paragraph } = Typography

const NDFLCalculatorPage = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <Title level={2}>Калькулятор НДФЛ</Title>
          <Paragraph type="secondary">
            Расчет прогрессивного налога на доходы физических лиц по новой шкале 2024-2025
          </Paragraph>
        </div>

        <NDFLCalculator />
      </Space>
    </div>
  )
}

export default NDFLCalculatorPage
