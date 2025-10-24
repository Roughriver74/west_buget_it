import React from 'react'
import type { Widget } from '@/types'
import TotalAmountWidget from './TotalAmountWidget'
import CategoryChartWidget from './CategoryChartWidget'
import MonthlyTrendWidget from './MonthlyTrendWidget'
import RecentExpensesWidget from './RecentExpensesWidget'

interface WidgetRendererProps {
  widget: Widget
}

const WidgetRenderer: React.FC<WidgetRendererProps> = ({ widget }) => {
  switch (widget.type) {
    case 'total_amount':
      return <TotalAmountWidget title={widget.title} config={widget.config} />
    case 'category_chart':
      return <CategoryChartWidget title={widget.title} config={widget.config} />
    case 'monthly_trend':
      return <MonthlyTrendWidget title={widget.title} config={widget.config} />
    case 'recent_expenses':
      return <RecentExpensesWidget title={widget.title} config={widget.config} />
    default:
      return <div>Неизвестный тип виджета: {widget.type}</div>
  }
}

export default WidgetRenderer
