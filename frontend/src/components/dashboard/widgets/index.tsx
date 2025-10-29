import React from 'react'
import type { Widget } from '@/types'
import TotalAmountWidget from './TotalAmountWidget'
import CategoryChartWidget from './CategoryChartWidget'
import MonthlyTrendWidget from './MonthlyTrendWidget'
import RecentExpensesWidget from './RecentExpensesWidget'
import BudgetPlanVsActualWidget from './BudgetPlanVsActualWidget'

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
    case 'budget_plan_vs_actual':
      return <BudgetPlanVsActualWidget year={widget.config.year} height={widget.config.height} showStats={widget.config.showStats} />
    default:
      return <div>Неизвестный тип виджета: {widget.type}</div>
  }
}

export default WidgetRenderer
