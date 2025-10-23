import React, { useState } from 'react'
import { Typography, Card, Select, Space } from 'antd'
import BudgetOverviewTable from '@/components/budget/BudgetOverviewTable'

const { Title, Paragraph } = Typography
const { Option } = Select

const MONTH_NAMES = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
]

const BudgetOverviewPage: React.FC = () => {
  const currentDate = new Date()
  const [selectedYear, setSelectedYear] = useState(currentDate.getFullYear())
  const [selectedMonth, setSelectedMonth] = useState(currentDate.getMonth() + 1)

  // Генерируем список последних 3 лет и следующий год
  const currentYear = new Date().getFullYear()
  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i)

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={2}>Бюджет (План-Факт-Остаток)</Title>
          <Paragraph>
            Основная рабочая страница для контроля бюджета. Выберите месяц для просмотра плана, факта и остатков по статьям.
          </Paragraph>
        </div>

        <Space align="center" size="large">
          <div>
            <div style={{ marginBottom: 4, fontSize: 12, color: '#666' }}>Год:</div>
            <Select
              value={selectedYear}
              onChange={setSelectedYear}
              style={{ width: 120 }}
            >
              {years.map((year) => (
                <Option key={year} value={year}>
                  {year}
                </Option>
              ))}
            </Select>
          </div>

          <div>
            <div style={{ marginBottom: 4, fontSize: 12, color: '#666' }}>Месяц:</div>
            <Select
              value={selectedMonth}
              onChange={setSelectedMonth}
              style={{ width: 150 }}
            >
              {MONTH_NAMES.map((name, index) => (
                <Option key={index + 1} value={index + 1}>
                  {name}
                </Option>
              ))}
            </Select>
          </div>
        </Space>
      </div>

      <Card>
        <BudgetOverviewTable year={selectedYear} month={selectedMonth} />
      </Card>

      <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f0f5ff', borderRadius: 8 }}>
        <Title level={5}>Цветовая индикация остатков:</Title>
        <Space direction="vertical">
          <div>
            <span style={{ color: '#52c41a', fontWeight: 'bold' }}>🟢 Зеленый</span> — остаток больше 20% от плана (хорошо)
          </div>
          <div>
            <span style={{ color: '#faad14', fontWeight: 'bold' }}>🟡 Желтый</span> — остаток 5-20% от плана (внимание)
          </div>
          <div>
            <span style={{ color: '#ff7875', fontWeight: 'bold' }}>🟠 Оранжевый</span> — остаток менее 5% от плана (критично)
          </div>
          <div>
            <span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>🔴 Красный</span> — перерасход (факт больше плана)
          </div>
        </Space>
      </div>
    </div>
  )
}

export default BudgetOverviewPage
