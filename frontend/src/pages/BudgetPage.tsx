import React, { useState } from 'react'
import { Typography, Card, Select, Space } from 'antd'
import BudgetOverviewTable from '@/components/budget/BudgetOverviewTable'

const { Title, Paragraph } = Typography
const { Option } = Select

const BudgetPage: React.FC = () => {
  const currentYear = new Date().getFullYear()
  const currentMonth = new Date().getMonth() + 1

  const [selectedYear, setSelectedYear] = useState(currentYear)
  const [selectedMonth, setSelectedMonth] = useState(currentMonth)

  // Генерируем список последних 5 лет и следующие 2 года
  const years = Array.from({ length: 8 }, (_, i) => currentYear - 3 + i)

  const months = [
    { value: 1, label: 'Январь' },
    { value: 2, label: 'Февраль' },
    { value: 3, label: 'Март' },
    { value: 4, label: 'Апрель' },
    { value: 5, label: 'Май' },
    { value: 6, label: 'Июнь' },
    { value: 7, label: 'Июль' },
    { value: 8, label: 'Август' },
    { value: 9, label: 'Сентябрь' },
    { value: 10, label: 'Октябрь' },
    { value: 11, label: 'Ноябрь' },
    { value: 12, label: 'Декабрь' },
  ]

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={2}>Бюджет</Title>
          <Paragraph>
            План/факт анализ по категориям расходов. Сравнение плановых и фактических показателей.
          </Paragraph>
        </div>

        <Space align="center" size="middle">
          <span style={{ fontSize: 16, fontWeight: 500 }}>Период:</span>
          <Select
            value={selectedMonth}
            onChange={setSelectedMonth}
            style={{ width: 150 }}
            size="large"
          >
            {months.map((month) => (
              <Option key={month.value} value={month.value}>
                {month.label}
              </Option>
            ))}
          </Select>
          <Select
            value={selectedYear}
            onChange={setSelectedYear}
            style={{ width: 120 }}
            size="large"
          >
            {years.map((year) => (
              <Option key={year} value={year}>
                {year}
              </Option>
            ))}
          </Select>
        </Space>
      </div>

      <Card>
        <BudgetOverviewTable year={selectedYear} month={selectedMonth} />
      </Card>

      <div style={{ marginTop: 16, padding: 16, backgroundColor: '#f0f5ff', borderRadius: 8 }}>
        <Title level={5}>Пояснения:</Title>
        <ul style={{ marginBottom: 0 }}>
          <li><strong>План</strong> - запланированная сумма расходов на месяц</li>
          <li><strong>Факт</strong> - фактические расходы за месяц (оплаченные заявки)</li>
          <li><strong>Остаток</strong> - разница между планом и фактом (план минус факт)</li>
          <li><strong>Исполнение</strong> - процент исполнения бюджета (факт / план × 100%)</li>
          <li>Красный цвет в колонке "Остаток" указывает на перерасход бюджета</li>
          <li>Категории с отступом (└─) являются подкатегориями родительской категории</li>
        </ul>
      </div>
    </div>
  )
}

export default BudgetPage
