import React from 'react'
import { Typography, Card } from 'antd'
import CategoryTable from '@/components/references/categories/CategoryTable'

const { Title, Paragraph } = Typography

const CategoriesPage: React.FC = () => {
  return (
    <div>
      <Title level={2}>Справочник статей расходов</Title>
      <Paragraph>
        Управление статьями расходов (категориями) для планирования и учёта бюджета.
        Статьи делятся на OPEX (операционные расходы) и CAPEX (капитальные расходы).
      </Paragraph>

      <Card>
        <CategoryTable />
      </Card>
    </div>
  )
}

export default CategoriesPage
