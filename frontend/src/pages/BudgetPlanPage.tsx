import React, { useState } from 'react'
import { Typography, Card, Select, Space, Button } from 'antd'
import BudgetPlanTable from '@/components/budget/BudgetPlanTable'
import { LeftOutlined, RightOutlined } from '@ant-design/icons'

const { Title, Paragraph } = Typography
const { Option } = Select

const BudgetPlanPage: React.FC = () => {
  const currentYear = new Date().getFullYear()
  const [selectedYear, setSelectedYear] = useState(currentYear)
  const tableRef = React.useRef<{ scrollBy: (direction: 'left' | 'right') => void } | null>(null)

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

      <Card styles={{ body: { padding: 24, position: 'relative' } }}>
        {/* Плавающие кнопки навигации привязанные к липкой панели */}
        <div
          style={{
            position: 'sticky',
            top: 64,
            zIndex: 100,
            pointerEvents: 'none',
            display: 'flex',
            justifyContent: 'space-between',
            padding: '0 12px',
            height: 0,
            marginBottom: 0,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              shape="circle"
              size="large"
              icon={<LeftOutlined />}
              onClick={() => tableRef.current?.scrollBy('left')}
              className="budget-scroll-button budget-scroll-button-transparent"
              style={{ pointerEvents: 'auto' }}
            />
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Button
              shape="circle"
              size="large"
              icon={<RightOutlined />}
              onClick={() => tableRef.current?.scrollBy('right')}
              className="budget-scroll-button budget-scroll-button-transparent"
              style={{ pointerEvents: 'auto' }}
            />
          </div>
        </div>

        <BudgetPlanTable year={selectedYear} ref={tableRef} />
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
