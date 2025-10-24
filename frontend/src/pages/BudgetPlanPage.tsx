import React, { useState } from 'react'
import { Typography, Card, Select, Space } from 'antd'
import BudgetPlanTable from '@/components/budget/BudgetPlanTable'

const { Title, Paragraph } = Typography
const { Option } = Select

const BudgetPlanPage: React.FC = () => {
  const currentYear = new Date().getFullYear()
  const [selectedYear, setSelectedYear] = useState(currentYear)

  // Генерируем список последних 5 лет и следующие 2 года
  const years = Array.from({ length: 8 }, (_, i) => currentYear - 3 + i)

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={2}>План бюджета</Title>
          <Paragraph>
            Помесячное планирование бюджета по статьям расходов. Клик по ячейке для редактирования.
          </Paragraph>
        </div>

        <Space align="center">
          <span style={{ fontSize: 16, fontWeight: 500 }}>Год:</span>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 150 }}
            size="large"
          >
            {years.map((year) => (
              <Option key={year} value={year}>
                {year} год
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      <Card styles={{ body: { padding: 0, overflow: 'auto' } }}>
        <div style={{ padding: 24 }}>
          <BudgetPlanTable year={selectedYear} />
        </div>
      </Card>

      <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f0f5ff', borderRadius: 8 }}>
        <Title level={5}>Инструкция:</Title>
        <ul style={{ marginBottom: 0 }}>
          <li>Кликните по ячейке, чтобы отредактировать сумму</li>
          <li>Нажмите Enter или уберите фокус для сохранения</li>
          <li>Нажмите Escape для отмены изменений</li>
          <li>Используйте кнопку "Скопировать из другого года" для быстрого создания плана</li>
          <li>Итоги по OPEX/CAPEX и общие итоги рассчитываются автоматически</li>
        </ul>
      </div>
    </div>
  )
}

export default BudgetPlanPage
