import React, { useState, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  DatePicker,
  Select,
  Button,
  Tabs,
  Statistic,
  Table,
  Space,
  Spin,
  Alert,
  Typography,
  Tag,
  Divider,
  Empty
} from 'antd';
import {
  TrendingUpOutlined,
  TrendingDownOutlined,
  DollarOutlined,
  UserOutlined,
  CalendarOutlined,
  BarChartOutlined,
  FundOutlined,
  ThunderboltOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs, { Dayjs } from 'dayjs';
import { Line, Column, Pie, Heatmap, Treemap, Sankey, Scatter, Waterfall } from '@ant-design/plots';
import type { TabsProps } from 'antd';

import { useDepartment } from '../contexts/DepartmentContext';
import apiClient from '../api/client';

const { RangePicker } = DatePicker;
const { Title, Text } = Typography;

interface ExpenseTrendPoint {
  period: string;
  category_id: number;
  category_name: string;
  total_amount: number;
  expense_count: number;
  average_amount: number;
  growth_rate?: number;
}

interface ExpenseTrendsResponse {
  trends: ExpenseTrendPoint[];
  summary: {
    total_periods: number;
    date_from: string;
    date_to: string;
    total_amount: number;
    average_per_period: number;
    max_period_amount: number;
    min_period_amount: number;
    volatility: number;
  };
  top_growing_categories: Array<{ name: string; growth_rate: number }>;
  top_declining_categories: Array<{ name: string; growth_rate: number }>;
}

interface ContractorStats {
  contractor_id: number;
  contractor_name: string;
  total_amount: number;
  expense_count: number;
  average_expense: number;
  first_expense_date: string;
  last_expense_date: string;
  active_months: number;
  categories_count: number;
  top_category: string;
  share_of_total: number;
}

interface ContractorAnalysisResponse {
  contractors: ContractorStats[];
  total_contractors: number;
  total_amount: number;
  concentration_ratio: number;
  average_contractor_amount: number;
  new_contractors_count: number;
  inactive_contractors_count: number;
}

interface DepartmentMetrics {
  department_id: number;
  department_name: string;
  total_budget: number;
  total_actual: number;
  execution_rate: number;
  variance: number;
  variance_percent: number;
  capex_amount: number;
  opex_amount: number;
  capex_ratio: number;
  expense_count: number;
  average_expense: number;
  employee_count: number;
  cost_per_employee: number;
  top_category: string;
  top_category_amount: number;
}

interface DepartmentComparisonResponse {
  departments: DepartmentMetrics[];
  total_departments: number;
  total_budget: number;
  total_actual: number;
  overall_execution_rate: number;
  best_performing_dept?: string;
  highest_variance_dept?: string;
  most_efficient_dept?: string;
}

interface SeasonalPattern {
  month: number;
  month_name: string;
  average_amount: number;
  median_amount: number;
  min_amount: number;
  max_amount: number;
  expense_count_average: number;
  seasonality_index: number;
  year_over_year_growth?: number;
}

interface SeasonalPatternsResponse {
  patterns: SeasonalPattern[];
  peak_month: string;
  lowest_month: string;
  seasonality_strength: number;
  predictability_score: number;
  recommended_budget_distribution: Array<{ month: string; recommended_percent: number }>;
}

interface CategoryEfficiency {
  category_id: number;
  category_name: string;
  budget_amount: number;
  actual_amount: number;
  savings: number;
  savings_rate: number;
  expense_count: number;
  average_processing_days: number;
  on_time_payment_rate: number;
  efficiency_score: number;
}

interface CostEfficiencyResponse {
  metrics: {
    total_budget: number;
    total_actual: number;
    total_savings: number;
    savings_rate: number;
    average_processing_days: number;
    on_time_payment_rate: number;
    budget_utilization_rate: number;
    cost_control_score: number;
    roi_estimate?: number;
  };
  categories: CategoryEfficiency[];
  best_performing_categories: string[];
  areas_for_improvement: string[];
  efficiency_trends: Array<{ month: number; score: number }>;
  recommendations: string[];
}

const ExtendedAnalyticsPage: React.FC = () => {
  const { selectedDepartment } = useDepartment();
  const [activeTab, setActiveTab] = useState('trends');

  // Filters
  const [dateRange, setDateRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(6, 'months').startOf('month'),
    dayjs().endOf('month')
  ]);
  const [selectedCategory, setSelectedCategory] = useState<number | undefined>();
  const [period, setPeriod] = useState<'month' | 'quarter'>('month');
  const [year, setYear] = useState(dayjs().year());
  const [startYear, setStartYear] = useState(dayjs().year() - 2);
  const [endYear, setEndYear] = useState(dayjs().year());

  // Fetch expense trends
  const { data: trendsData, isLoading: trendsLoading } = useQuery<ExpenseTrendsResponse>({
    queryKey: ['analytics-trends', dateRange, selectedDepartment?.id, selectedCategory, period],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/advanced/expense-trends', {
        params: {
          start_date: dateRange[0].format('YYYY-MM-DD'),
          end_date: dateRange[1].format('YYYY-MM-DD'),
          department_id: selectedDepartment?.id,
          category_id: selectedCategory,
          period
        }
      });
      return res.data;
    },
    enabled: activeTab === 'trends'
  });

  // Fetch contractor analysis
  const { data: contractorData, isLoading: contractorLoading } = useQuery<ContractorAnalysisResponse>({
    queryKey: ['analytics-contractors', dateRange, selectedDepartment?.id],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/advanced/contractor-analysis', {
        params: {
          start_date: dateRange[0].format('YYYY-MM-DD'),
          end_date: dateRange[1].format('YYYY-MM-DD'),
          department_id: selectedDepartment?.id
        }
      });
      return res.data;
    },
    enabled: activeTab === 'contractors'
  });

  // Fetch department comparison
  const { data: deptData, isLoading: deptLoading } = useQuery<DepartmentComparisonResponse>({
    queryKey: ['analytics-departments', year],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/advanced/department-comparison', {
        params: { year }
      });
      return res.data;
    },
    enabled: activeTab === 'departments'
  });

  // Fetch seasonal patterns
  const { data: seasonalData, isLoading: seasonalLoading } = useQuery<SeasonalPatternsResponse>({
    queryKey: ['analytics-seasonal', startYear, endYear, selectedDepartment?.id],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/advanced/seasonal-patterns', {
        params: {
          start_year: startYear,
          end_year: endYear,
          department_id: selectedDepartment?.id
        }
      });
      return res.data;
    },
    enabled: activeTab === 'seasonal'
  });

  // Fetch cost efficiency
  const { data: efficiencyData, isLoading: efficiencyLoading } = useQuery<CostEfficiencyResponse>({
    queryKey: ['analytics-efficiency', year, selectedDepartment?.id],
    queryFn: async () => {
      const res = await apiClient.get('/analytics/advanced/cost-efficiency', {
        params: {
          year,
          department_id: selectedDepartment?.id
        }
      });
      return res.data;
    },
    enabled: activeTab === 'efficiency'
  });

  // Expense Trends Tab
  const renderTrendsTab = () => {
    if (trendsLoading) return <Spin size="large" tip="Загрузка трендов..." />;
    if (!trendsData) return <Empty description="Нет данных" />;

    // Prepare data for line chart
    const lineData = trendsData.trends.map(t => ({
      period: t.period,
      category: t.category_name,
      amount: t.total_amount
    }));

    // Prepare growth data for column chart
    const growthData = trendsData.top_growing_categories
      .concat(trendsData.top_declining_categories)
      .map(c => ({
        category: c.name,
        growth: c.growth_rate,
        type: c.growth_rate > 0 ? 'Рост' : 'Снижение'
      }));

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Summary Cards */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Всего периодов"
                value={trendsData.summary.total_periods}
                prefix={<CalendarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Общая сумма"
                value={trendsData.summary.total_amount}
                precision={2}
                suffix="₽"
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Средняя за период"
                value={trendsData.summary.average_per_period}
                precision={2}
                suffix="₽"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Волатильность"
                value={trendsData.summary.volatility}
                precision={0}
                suffix="₽"
                prefix={<ThunderboltOutlined />}
              />
            </Card>
          </Col>
        </Row>

        {/* Trend Line Chart */}
        <Card title="Тренды расходов по категориям">
          <Line
            data={lineData}
            xField="period"
            yField="amount"
            seriesField="category"
            smooth
            animation={{
              appear: {
                animation: 'path-in',
                duration: 1000,
              },
            }}
            legend={{ position: 'top' }}
            tooltip={{
              formatter: (datum) => ({
                name: datum.category,
                value: `${Number(datum.amount).toLocaleString('ru-RU')} ₽`
              })
            }}
          />
        </Card>

        {/* Growth/Decline Chart */}
        <Card title="Топ растущих и падающих категорий">
          <Column
            data={growthData}
            xField="category"
            yField="growth"
            seriesField="type"
            color={({ type }) => type === 'Рост' ? '#52c41a' : '#f5222d'}
            label={{
              position: 'top',
              formatter: (datum) => `${datum.growth.toFixed(1)}%`
            }}
            legend={{ position: 'top' }}
            tooltip={{
              formatter: (datum) => ({
                name: datum.category,
                value: `${datum.growth.toFixed(2)}%`
              })
            }}
          />
        </Card>
      </Space>
    );
  };

  // Contractor Analysis Tab
  const renderContractorsTab = () => {
    if (contractorLoading) return <Spin size="large" tip="Загрузка анализа контрагентов..." />;
    if (!contractorData) return <Empty description="Нет данных" />;

    // Prepare data for treemap
    const treemapData = {
      name: 'Контрагенты',
      children: contractorData.contractors.slice(0, 20).map(c => ({
        name: c.contractor_name,
        value: c.total_amount
      }))
    };

    const columns = [
      {
        title: 'Контрагент',
        dataIndex: 'contractor_name',
        key: 'contractor_name',
        width: 200,
      },
      {
        title: 'Общая сумма',
        dataIndex: 'total_amount',
        key: 'total_amount',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
        sorter: (a: ContractorStats, b: ContractorStats) => a.total_amount - b.total_amount
      },
      {
        title: 'Кол-во заявок',
        dataIndex: 'expense_count',
        key: 'expense_count',
        sorter: (a: ContractorStats, b: ContractorStats) => a.expense_count - b.expense_count
      },
      {
        title: 'Средний чек',
        dataIndex: 'average_expense',
        key: 'average_expense',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
      },
      {
        title: 'Доля от общего',
        dataIndex: 'share_of_total',
        key: 'share_of_total',
        render: (val: number) => (
          <Tag color={val > 10 ? 'red' : val > 5 ? 'orange' : 'default'}>
            {val.toFixed(2)}%
          </Tag>
        ),
        sorter: (a: ContractorStats, b: ContractorStats) => a.share_of_total - b.share_of_total
      },
      {
        title: 'Топ категория',
        dataIndex: 'top_category',
        key: 'top_category',
      },
    ];

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Summary Cards */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Всего контрагентов"
                value={contractorData.total_contractors}
                prefix={<UserOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Общая сумма"
                value={contractorData.total_amount}
                precision={2}
                suffix="₽"
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Коэффициент концентрации"
                value={contractorData.concentration_ratio}
                precision={1}
                suffix="%"
                valueStyle={{ color: contractorData.concentration_ratio > 50 ? '#cf1322' : '#3f8600' }}
                prefix={contractorData.concentration_ratio > 50 ? <TrendingUpOutlined /> : <TrendingDownOutlined />}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                Топ-10 контрагентов
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Новых контрагентов"
                value={contractorData.new_contractors_count}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Treemap */}
        <Card title="Распределение расходов по контрагентам (Top 20)">
          <Treemap
            data={treemapData}
            colorField="name"
            legend={false}
            label={{
              formatter: (datum) => `${datum.name}\n${Number(datum.value).toLocaleString('ru-RU')} ₽`
            }}
            tooltip={{
              formatter: (datum) => ({
                name: datum.name,
                value: `${Number(datum.value).toLocaleString('ru-RU')} ₽`
              })
            }}
          />
        </Card>

        {/* Contractors Table */}
        <Card title="Детализация по контрагентам">
          <Table
            columns={columns}
            dataSource={contractorData.contractors}
            rowKey="contractor_id"
            pagination={{ pageSize: 20 }}
            scroll={{ x: 1000 }}
          />
        </Card>
      </Space>
    );
  };

  // Department Comparison Tab
  const renderDepartmentsTab = () => {
    if (deptLoading) return <Spin size="large" tip="Загрузка сравнения отделов..." />;
    if (!deptData) return <Empty description="Нет данных" />;

    // Waterfall data for budget execution
    const waterfallData = [
      { type: 'Бюджет', value: deptData.total_budget },
      { type: 'Фактические расходы', value: -deptData.total_actual },
      { type: 'Остаток/Перерасход', value: deptData.total_budget - deptData.total_actual, isTotal: true }
    ];

    const columns = [
      {
        title: 'Отдел',
        dataIndex: 'department_name',
        key: 'department_name',
        fixed: 'left' as const,
        width: 150,
      },
      {
        title: 'Бюджет',
        dataIndex: 'total_budget',
        key: 'total_budget',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
        sorter: (a: DepartmentMetrics, b: DepartmentMetrics) => a.total_budget - b.total_budget
      },
      {
        title: 'Факт',
        dataIndex: 'total_actual',
        key: 'total_actual',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
        sorter: (a: DepartmentMetrics, b: DepartmentMetrics) => a.total_actual - b.total_actual
      },
      {
        title: 'Исполнение',
        dataIndex: 'execution_rate',
        key: 'execution_rate',
        render: (val: number) => (
          <Tag color={val > 100 ? 'red' : val > 90 ? 'orange' : 'green'}>
            {val.toFixed(1)}%
          </Tag>
        ),
        sorter: (a: DepartmentMetrics, b: DepartmentMetrics) => a.execution_rate - b.execution_rate
      },
      {
        title: 'Отклонение',
        dataIndex: 'variance',
        key: 'variance',
        render: (val: number) => (
          <Text type={val > 0 ? 'danger' : 'success'}>
            {val > 0 ? '+' : ''}{val.toLocaleString('ru-RU')} ₽
          </Text>
        ),
        sorter: (a: DepartmentMetrics, b: DepartmentMetrics) => a.variance - b.variance
      },
      {
        title: 'Сотрудников',
        dataIndex: 'employee_count',
        key: 'employee_count',
        sorter: (a: DepartmentMetrics, b: DepartmentMetrics) => a.employee_count - b.employee_count
      },
      {
        title: 'Затраты на сотрудника',
        dataIndex: 'cost_per_employee',
        key: 'cost_per_employee',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
        sorter: (a: DepartmentMetrics, b: DepartmentMetrics) => a.cost_per_employee - b.cost_per_employee
      },
    ];

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Summary Cards */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Всего отделов"
                value={deptData.total_departments}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Общее исполнение"
                value={deptData.overall_execution_rate}
                precision={1}
                suffix="%"
                valueStyle={{ color: deptData.overall_execution_rate > 100 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Лучший отдел"
                value={deptData.best_performing_dept || 'N/A'}
                prefix={<TrendingUpOutlined />}
                valueStyle={{ fontSize: 16 }}
              />
            </Card>
          </Col>
        </Row>

        {/* Waterfall Chart */}
        <Card title="Водопадная диаграмма исполнения бюджета">
          <Waterfall
            data={waterfallData}
            xField="type"
            yField="value"
            total={{
              label: 'Итого',
              style: {
                fill: deptData.total_budget - deptData.total_actual >= 0 ? '#52c41a' : '#f5222d'
              }
            }}
            label={{
              formatter: (datum) => `${Math.abs(Number(datum.value)).toLocaleString('ru-RU')} ₽`
            }}
            tooltip={{
              formatter: (datum) => ({
                name: datum.type,
                value: `${Math.abs(Number(datum.value)).toLocaleString('ru-RU')} ₽`
              })
            }}
          />
        </Card>

        {/* Departments Table */}
        <Card title="Сравнение отделов">
          <Table
            columns={columns}
            dataSource={deptData.departments}
            rowKey="department_id"
            scroll={{ x: 1200 }}
            pagination={false}
          />
        </Card>
      </Space>
    );
  };

  // Seasonal Patterns Tab
  const renderSeasonalTab = () => {
    if (seasonalLoading) return <Spin size="large" tip="Загрузка сезонных паттернов..." />;
    if (!seasonalData) return <Empty description="Нет данных" />;

    // Prepare data for radar/area chart
    const seasonalChartData = seasonalData.patterns.map(p => ({
      month: p.month_name,
      average: p.average_amount,
      seasonality: p.seasonality_index * 100
    }));

    // Heatmap data (seasonality index)
    const heatmapData = seasonalData.patterns.map(p => ({
      month: p.month_name,
      type: 'Индекс сезонности',
      value: p.seasonality_index
    }));

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Summary Cards */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Пиковый месяц"
                value={seasonalData.peak_month}
                prefix={<TrendingUpOutlined />}
                valueStyle={{ fontSize: 16, color: '#cf1322' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Низший месяц"
                value={seasonalData.lowest_month}
                prefix={<TrendingDownOutlined />}
                valueStyle={{ fontSize: 16, color: '#3f8600' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Сила сезонности"
                value={seasonalData.seasonality_strength}
                precision={1}
                suffix="%"
                prefix={<ThunderboltOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Предсказуемость"
                value={seasonalData.predictability_score}
                precision={1}
                suffix="%"
                valueStyle={{ color: seasonalData.predictability_score > 70 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Seasonal Chart */}
        <Card title="Сезонные паттерны расходов">
          <Column
            data={seasonalChartData}
            xField="month"
            yField="average"
            label={{
              position: 'top',
              formatter: (datum) => `${(Number(datum.average) / 1000).toFixed(0)}K ₽`
            }}
            tooltip={{
              formatter: (datum) => ({
                name: 'Средняя сумма',
                value: `${Number(datum.average).toLocaleString('ru-RU')} ₽`
              })
            }}
            color="#1890ff"
          />
        </Card>

        {/* Seasonality Heatmap */}
        <Card title="Тепловая карта сезонности">
          <Heatmap
            data={heatmapData}
            xField="month"
            yField="type"
            colorField="value"
            color={['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']}
            label={{
              formatter: (datum) => datum.value.toFixed(2)
            }}
            tooltip={{
              formatter: (datum) => ({
                name: datum.month,
                value: `Индекс: ${datum.value.toFixed(2)}`
              })
            }}
          />
        </Card>

        {/* Recommended Distribution */}
        <Card title="Рекомендуемое распределение бюджета">
          <Pie
            data={seasonalData.recommended_budget_distribution}
            angleField="recommended_percent"
            colorField="month"
            radius={0.8}
            label={{
              type: 'outer',
              content: '{name} {percentage}'
            }}
            interactions={[{ type: 'element-active' }]}
            legend={{ position: 'right' }}
          />
        </Card>
      </Space>
    );
  };

  // Cost Efficiency Tab
  const renderEfficiencyTab = () => {
    if (efficiencyLoading) return <Spin size="large" tip="Загрузка анализа эффективности..." />;
    if (!efficiencyData) return <Empty description="Нет данных" />;

    const columns = [
      {
        title: 'Категория',
        dataIndex: 'category_name',
        key: 'category_name',
        fixed: 'left' as const,
        width: 150,
      },
      {
        title: 'Бюджет',
        dataIndex: 'budget_amount',
        key: 'budget_amount',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
      },
      {
        title: 'Факт',
        dataIndex: 'actual_amount',
        key: 'actual_amount',
        render: (val: number) => `${val.toLocaleString('ru-RU')} ₽`,
      },
      {
        title: 'Экономия',
        dataIndex: 'savings',
        key: 'savings',
        render: (val: number) => (
          <Text type={val < 0 ? 'danger' : 'success'}>
            {val > 0 ? '+' : ''}{val.toLocaleString('ru-RU')} ₽
          </Text>
        ),
        sorter: (a: CategoryEfficiency, b: CategoryEfficiency) => a.savings - b.savings
      },
      {
        title: 'Процент экономии',
        dataIndex: 'savings_rate',
        key: 'savings_rate',
        render: (val: number) => (
          <Tag color={val < 0 ? 'red' : 'green'}>
            {val > 0 ? '+' : ''}{val.toFixed(1)}%
          </Tag>
        ),
        sorter: (a: CategoryEfficiency, b: CategoryEfficiency) => a.savings_rate - b.savings_rate
      },
      {
        title: 'Оценка эффективности',
        dataIndex: 'efficiency_score',
        key: 'efficiency_score',
        render: (val: number) => (
          <Tag color={val > 80 ? 'green' : val > 60 ? 'orange' : 'red'}>
            {val.toFixed(0)}
          </Tag>
        ),
        sorter: (a: CategoryEfficiency, b: CategoryEfficiency) => a.efficiency_score - b.efficiency_score
      },
    ];

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Summary Cards */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Общая экономия"
                value={efficiencyData.metrics.total_savings}
                precision={2}
                suffix="₽"
                valueStyle={{ color: efficiencyData.metrics.total_savings >= 0 ? '#3f8600' : '#cf1322' }}
                prefix={efficiencyData.metrics.total_savings >= 0 ? <TrendingUpOutlined /> : <TrendingDownOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Процент экономии"
                value={efficiencyData.metrics.savings_rate}
                precision={1}
                suffix="%"
                valueStyle={{ color: efficiencyData.metrics.savings_rate >= 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Своевременные оплаты"
                value={efficiencyData.metrics.on_time_payment_rate}
                precision={1}
                suffix="%"
                prefix={<ThunderboltOutlined />}
                valueStyle={{ color: efficiencyData.metrics.on_time_payment_rate > 80 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Оценка контроля затрат"
                value={efficiencyData.metrics.cost_control_score}
                precision={0}
                suffix="/100"
                prefix={<FundOutlined />}
                valueStyle={{ color: efficiencyData.metrics.cost_control_score > 70 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Categories Table */}
        <Card title="Эффективность по категориям">
          <Table
            columns={columns}
            dataSource={efficiencyData.categories}
            rowKey="category_id"
            pagination={{ pageSize: 10 }}
            scroll={{ x: 1000 }}
          />
        </Card>

        {/* Recommendations */}
        <Card title="Рекомендации по оптимизации">
          <Alert
            message="Области для улучшения"
            description={
              <ul>
                {efficiencyData.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            }
            type="info"
            showIcon
          />
        </Card>

        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card title="Лучшие категории (экономия)">
              <ul>
                {efficiencyData.best_performing_categories.map((cat, idx) => (
                  <li key={idx}>
                    <Tag color="green">{idx + 1}</Tag> {cat}
                  </li>
                ))}
              </ul>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Требуют внимания (перерасход)">
              <ul>
                {efficiencyData.areas_for_improvement.map((cat, idx) => (
                  <li key={idx}>
                    <Tag color="red">{idx + 1}</Tag> {cat}
                  </li>
                ))}
              </ul>
            </Card>
          </Col>
        </Row>
      </Space>
    );
  };

  const tabs: TabsProps['items'] = [
    {
      key: 'trends',
      label: 'Тренды расходов',
      children: renderTrendsTab(),
      icon: <TrendingUpOutlined />
    },
    {
      key: 'contractors',
      label: 'Анализ контрагентов',
      children: renderContractorsTab(),
      icon: <UserOutlined />
    },
    {
      key: 'departments',
      label: 'Сравнение отделов',
      children: renderDepartmentsTab(),
      icon: <BarChartOutlined />
    },
    {
      key: 'seasonal',
      label: 'Сезонные паттерны',
      children: renderSeasonalTab(),
      icon: <CalendarOutlined />
    },
    {
      key: 'efficiency',
      label: 'Эффективность затрат',
      children: renderEfficiencyTab(),
      icon: <FundOutlined />
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <BarChartOutlined /> Расширенная аналитика
        </Title>
        <Text type="secondary">
          Глубокий анализ расходов, контрагентов, отделов и эффективности затрат
        </Text>
      </div>

      {/* Global Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          {(activeTab === 'trends' || activeTab === 'contractors') && (
            <>
              <div>
                <Text strong>Период:</Text>
                <br />
                <RangePicker
                  value={dateRange}
                  onChange={(dates) => dates && setDateRange(dates as [Dayjs, Dayjs])}
                  format="YYYY-MM-DD"
                />
              </div>
              {activeTab === 'trends' && (
                <div>
                  <Text strong>Группировка:</Text>
                  <br />
                  <Select
                    value={period}
                    onChange={setPeriod}
                    style={{ width: 120 }}
                    options={[
                      { label: 'Месяц', value: 'month' },
                      { label: 'Квартал', value: 'quarter' }
                    ]}
                  />
                </div>
              )}
            </>
          )}
          {(activeTab === 'departments' || activeTab === 'efficiency') && (
            <div>
              <Text strong>Год:</Text>
              <br />
              <DatePicker
                picker="year"
                value={dayjs().year(year)}
                onChange={(date) => date && setYear(date.year())}
              />
            </div>
          )}
          {activeTab === 'seasonal' && (
            <>
              <div>
                <Text strong>Начальный год:</Text>
                <br />
                <DatePicker
                  picker="year"
                  value={dayjs().year(startYear)}
                  onChange={(date) => date && setStartYear(date.year())}
                />
              </div>
              <div>
                <Text strong>Конечный год:</Text>
                <br />
                <DatePicker
                  picker="year"
                  value={dayjs().year(endYear)}
                  onChange={(date) => date && setEndYear(date.year())}
                />
              </div>
            </>
          )}
        </Space>
      </Card>

      {/* Tabs with Analytics */}
      <Tabs
        activeKey={activeTab}
        items={tabs}
        onChange={setActiveTab}
        tabBarExtraContent={
          <Button icon={<DownloadOutlined />} type="primary">
            Экспорт отчета
          </Button>
        }
      />
    </div>
  );
};

export default ExtendedAnalyticsPage;
