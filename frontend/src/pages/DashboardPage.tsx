import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Statistic, Select, Alert } from 'antd'
import { ArrowUpOutlined, ArrowDownOutlined, DollarOutlined, WarningOutlined } from '@ant-design/icons'
import { analyticsApi } from '@/api'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { ExpenseStatus } from '@/types'
import { getExpenseStatusLabel } from '@/utils/formatters'
import dayjs from 'dayjs'
import { useDepartment } from '@/contexts/DepartmentContext'
import LoadingState from '@/components/common/LoadingState'
import ErrorState from '@/components/common/ErrorState'
import BudgetPlanVsActualWidget from '@/components/dashboard/widgets/BudgetPlanVsActualWidget'
import BudgetExecutionProgressWidget from '@/components/dashboard/widgets/BudgetExecutionProgressWidget'
import BudgetDeviationHeatmap from '@/components/dashboard/widgets/BudgetDeviationHeatmap'
import PayrollTaxWidget from '@/components/dashboard/widgets/PayrollTaxWidget'
import { Card } from '@/components/ui/Card'

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

const DashboardPage = () => {
  const currentYear = dayjs().year()
  const [year, setYear] = useState(currentYear)
  const [month, setMonth] = useState<number | undefined>(undefined)
  const { selectedDepartment } = useDepartment()

  const { data, isLoading, error } = useQuery({
    queryKey: ['dashboard', year, month, selectedDepartment?.id],
    queryFn: () => analyticsApi.getDashboard({ year, month, department_id: selectedDepartment?.id }),
  })

  if (isLoading) {
    return <LoadingState />
  }

  if (error) {
    return <ErrorState description={String(error)} />
  }

  if (!data) {
    return null
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <Select
          value={year}
          onChange={setYear}
          className="w-full sm:w-48"
          options={[
            { value: 2024, label: '2024' },
            { value: 2025, label: '2025' },
            { value: 2026, label: '2026' },
          ]}
        />
        <Select
          value={month}
          onChange={setMonth}
          allowClear
          placeholder="Все месяцы"
          className="w-full sm:w-48"
          options={[
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
          ]}
        />
      </div>

      {/* Алерт при превышении бюджета */}
      {data.totals.remaining < 0 && (
        <Alert
          message={
            <div className="flex items-center gap-2">
              <WarningOutlined />
              <span className="font-semibold">Превышение бюджета!</span>
            </div>
          }
          description={
            <div>
              <div>Фактические расходы превышают план на: <strong className="text-red-500">{formatCurrency(Math.abs(data.totals.remaining))}</strong></div>
              <div className="mt-1 text-xs">
                Процент исполнения: <strong>{data.totals.execution_percent.toFixed(2)}%</strong>
              </div>
            </div>
          }
          type="error"
          showIcon
          closable
          className="mb-4 !rounded-lg"
        />
      )}

      {/* Предупреждение при приближении к лимиту (>90% исполнения) */}
      {data.totals.remaining >= 0 && data.totals.execution_percent > 90 && (
        <Alert
          message="Внимание: бюджет почти исчерпан"
          description={
            <div>
              <div>Исполнено: <strong>{data.totals.execution_percent.toFixed(2)}%</strong> от плана</div>
              <div>Остаток бюджета: <strong>{formatCurrency(data.totals.remaining)}</strong></div>
            </div>
          }
          type="warning"
          showIcon
          closable
          className="mb-4 !rounded-lg"
        />
      )}

      {/* Основные метрики */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card variant="default" className="hover:shadow-md transition-shadow">
          <Statistic
            title={<span className="text-gray-500 font-medium">План</span>}
            value={data.totals.planned}
            precision={0}
            valueStyle={{ color: '#10b981', fontWeight: 600 }}
            prefix={<DollarOutlined />}
            suffix="₽"
          />
        </Card>
        <Card variant="default" className="hover:shadow-md transition-shadow">
          <Statistic
            title={<span className="text-gray-500 font-medium">Факт</span>}
            value={data.totals.actual}
            precision={0}
            valueStyle={{ color: '#3b82f6', fontWeight: 600 }}
            prefix={<DollarOutlined />}
            suffix="₽"
          />
        </Card>
        <Card variant="default" className="hover:shadow-md transition-shadow">
          <Statistic
            title={<span className="text-gray-500 font-medium">Остаток</span>}
            value={data.totals.remaining}
            precision={0}
            valueStyle={{ color: data.totals.remaining >= 0 ? '#10b981' : '#ef4444', fontWeight: 600 }}
            prefix={data.totals.remaining >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
            suffix="₽"
          />
        </Card>
        <Card variant="default" className="hover:shadow-md transition-shadow">
          <Statistic
            title={<span className="text-gray-500 font-medium">Исполнение</span>}
            value={data.totals.execution_percent}
            precision={2}
            valueStyle={{ color: '#3b82f6', fontWeight: 600 }}
            suffix="%"
          />
        </Card>
      </div>

      {/* CAPEX vs OPEX */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="CAPEX vs OPEX" variant="default" className="h-full">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'CAPEX', value: data.capex_vs_opex.capex },
                  { name: 'OPEX', value: data.capex_vs_opex.opex },
                ]}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {[0, 1].map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Топ-5 категорий по расходам" variant="default" className="h-full">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.top_categories}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="category_name" angle={-45} textAnchor="end" height={100} tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Bar dataKey="amount" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Распределение по статусам */}
      <Card title="Распределение заявок по статусам" variant="default">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data.status_distribution.map(item => ({
            ...item,
            status: getExpenseStatusLabel(item.status as ExpenseStatus)
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="status" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="left" orientation="left" stroke="#8b5cf6" tick={{ fontSize: 12 }} />
            <YAxis yAxisId="right" orientation="right" stroke="#10b981" tick={{ fontSize: 12 }} />
            <Tooltip formatter={(value: number, name: string) =>
              name === 'amount' ? formatCurrency(value) : value
            } />
            <Legend />
            <Bar yAxisId="left" dataKey="count" fill="#8b5cf6" name="Количество" radius={[4, 4, 0, 0]} />
            <Bar yAxisId="right" dataKey="amount" fill="#10b981" name="Сумма" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* План vs Факт - годовой обзор */}
      <div className="mt-6">
        <BudgetPlanVsActualWidget year={year} departmentId={selectedDepartment?.id} height={400} showStats={true} />
      </div>

      {/* Прогресс-бары исполнения по категориям и ФОТ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <BudgetExecutionProgressWidget year={year} departmentId={selectedDepartment?.id} height={500} />
        <PayrollTaxWidget year={year} departmentId={selectedDepartment?.id} height={500} />
      </div>

      {/* Тепловая карта отклонений - полная ширина */}
      <div className="mt-6">
        <BudgetDeviationHeatmap year={year} departmentId={selectedDepartment?.id} height={700} />
      </div>
    </div>
  )
}

export default DashboardPage
