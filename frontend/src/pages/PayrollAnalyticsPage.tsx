import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Table, 
  Card,
  Row,
  Col,
  Select,
  Spin,
  Alert,
  Statistic,
  Typography,
  Space,
  Divider,
  Tag,
  Tabs} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell} from 'recharts';
import ReactApexChart from 'react-apexcharts';
import type { ApexOptions } from 'apexcharts';
import {
  BarChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  TeamOutlined,
  DollarOutlined,
  FundOutlined,
  PercentageOutlined} from '@ant-design/icons';
import { useDepartment } from '../contexts/DepartmentContext';
import { payrollAnalyticsAPI, payrollTaxAnalyticsAPI } from '../api/payroll';
import type { TaxByEmployee } from '../api/payroll';
import { formatCurrency } from '../utils/formatters';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2'];
const MONTH_NAMES = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

export default function PayrollAnalyticsPage() {
  const currentYear = dayjs().year();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const [activeTab, setActiveTab] = useState('summary');
  const { selectedDepartment } = useDepartment();

  // Fetch salary statistics
  const { data: salaryStats, isLoading: statsLoading } = useQuery({
    queryKey: ['payroll-salary-stats', selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getSalaryStats(selectedDepartment?.id)});

  // Fetch payroll structure
  const { data: structure, isLoading: structureLoading } = useQuery({
    queryKey: ['payroll-structure', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getStructure(selectedYear, selectedDepartment?.id)});

  // Fetch payroll dynamics
  const { data: dynamics, isLoading: dynamicsLoading } = useQuery({
    queryKey: ['payroll-dynamics', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getDynamics(selectedYear, selectedDepartment?.id)});

  // Fetch payroll forecast
  const { data: forecast, isLoading: forecastLoading } = useQuery({
    queryKey: ['payroll-forecast', selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getForecast({
      months_ahead: 6,
      historical_months: 6,
      department_id: selectedDepartment?.id})});

  // Fetch salary distribution
  const { data: salaryDistribution, isLoading: distributionLoading } = useQuery({
    queryKey: ['salary-distribution', selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getSalaryDistribution({
      department_id: selectedDepartment?.id,
      bucket_size: 50000, // 50k per bucket
    })});

  // Fetch tax analytics
  const { data: taxBurden, isLoading: taxBurdenLoading } = useQuery({
    queryKey: ['payroll-tax-burden', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollTaxAnalyticsAPI.getTaxBurden({
      year: selectedYear,
      department_id: selectedDepartment?.id}),
    enabled: activeTab === 'taxes'});

  const { data: taxBreakdownByMonth, isLoading: taxBreakdownLoading } = useQuery({
    queryKey: ['payroll-tax-breakdown', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollTaxAnalyticsAPI.getTaxBreakdownByMonth({
      year: selectedYear,
      department_id: selectedDepartment?.id}),
    enabled: activeTab === 'taxes'});

  const { data: taxByEmployee, isLoading: taxByEmployeeLoading } = useQuery({
    queryKey: ['payroll-tax-by-employee', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollTaxAnalyticsAPI.getTaxByEmployee({
      year: selectedYear,
      department_id: selectedDepartment?.id}),
    enabled: activeTab === 'taxes'});

  const { data: costWaterfall, isLoading: costWaterfallLoading } = useQuery({
    queryKey: ['payroll-cost-waterfall', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollTaxAnalyticsAPI.getCostWaterfall({
      year: selectedYear,
      department_id: selectedDepartment?.id}),
    enabled: activeTab === 'taxes'});

  const isLoading = statsLoading || structureLoading || dynamicsLoading || forecastLoading || distributionLoading;
  const isTaxLoading = taxBurdenLoading || taxBreakdownLoading || taxByEmployeeLoading || costWaterfallLoading;

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
      </div>
    );
  }

  // Prepare chart data
  const dynamicsChartData = dynamics?.map((item) => ({
    month: MONTH_NAMES[item.month - 1],
    'План': Number(item.planned_total),
    'Факт': Number(item.actual_total),
    'Сотрудников': item.employee_count})) || [];

  const structureChartData = structure?.map((item) => ({
    month: MONTH_NAMES[item.month - 1],
    'Оклад': Number(item.total_base_salary),
    'Премия мес.': Number(item.total_monthly_bonus),
    'Премия квар.': Number(item.total_quarterly_bonus),
    'Премия год.': Number(item.total_annual_bonus),
    'Прочие': Number(item.total_other_payments)})) || [];

  // Calculate average structure for pie chart
  const totalBaseSalary = structure?.reduce((sum, item) => sum + Number(item.total_base_salary), 0) || 0;
  const totalMonthlyBonus = structure?.reduce((sum, item) => sum + Number(item.total_monthly_bonus), 0) || 0;
  const totalQuarterlyBonus = structure?.reduce((sum, item) => sum + Number(item.total_quarterly_bonus), 0) || 0;
  const totalAnnualBonus = structure?.reduce((sum, item) => sum + Number(item.total_annual_bonus), 0) || 0;
  const totalOther = structure?.reduce((sum, item) => sum + Number(item.total_other_payments), 0) || 0;
  const totalSum = totalBaseSalary + totalMonthlyBonus + totalQuarterlyBonus + totalAnnualBonus + totalOther;

  const pieChartData = [
    { name: 'Оклад', value: totalBaseSalary, percent: totalSum > 0 ? (totalBaseSalary / totalSum * 100).toFixed(1) : 0 },
    { name: 'Премия месячная', value: totalMonthlyBonus, percent: totalSum > 0 ? (totalMonthlyBonus / totalSum * 100).toFixed(1) : 0 },
    { name: 'Премия квартальная', value: totalQuarterlyBonus, percent: totalSum > 0 ? (totalQuarterlyBonus / totalSum * 100).toFixed(1) : 0 },
    { name: 'Премия годовая', value: totalAnnualBonus, percent: totalSum > 0 ? (totalAnnualBonus / totalSum * 100).toFixed(1) : 0 },
    { name: 'Прочие выплаты', value: totalOther, percent: totalSum > 0 ? (totalOther / totalSum * 100).toFixed(1) : 0 },
  ];

  // Calculate salary distribution for histogram
  const salaryDistributionData = salaryStats ? [
    { range: 'Минимум', value: Number(salaryStats.min_salary) },
    { range: '25%', value: Number(salaryStats.percentile_25) },
    { range: 'Медиана', value: Number(salaryStats.median_salary) },
    { range: 'Среднее', value: Number(salaryStats.average_salary) },
    { range: '75%', value: Number(salaryStats.percentile_75) },
    { range: '90%', value: Number(salaryStats.percentile_90) },
    { range: 'Максимум', value: Number(salaryStats.max_salary) },
  ] : [];

  const renderCustomLabel = ({ name, percent }: any) => {
    return `${name}: ${percent}%`;
  };

  // Tax analytics data preparation
  const taxDistributionData = taxBurden ? [
    { name: 'НДФЛ', value: Number(taxBurden.ndfl.total), color: '#faad14' },
    { name: 'ПФР', value: Number(taxBurden.social_contributions.pfr.total), color: '#f5222d' },
    { name: 'ФОМС', value: Number(taxBurden.social_contributions.foms.total), color: '#722ed1' },
    { name: 'ФСС', value: Number(taxBurden.social_contributions.fss.total), color: '#13c2c2' },
  ] : [];

  const taxMonthlyData = taxBreakdownByMonth?.map(item => ({
    month_name: item.month_name,
    net_payroll: Number(item.net_payroll),
    ndfl: Number(item.ndfl),
    pfr: Number(item.pfr),
    foms: Number(item.foms),
    fss: Number(item.fss),
    effective_ndfl: item.gross_payroll > 0 ? (Number(item.ndfl) / Number(item.gross_payroll) * 100) : 0,
    effective_total: item.gross_payroll > 0 ? (Number(item.total_taxes) / Number(item.gross_payroll) * 100) : 0})) || [];

  // Waterfall chart data
  const waterfallSeries = costWaterfall ? [{
    name: 'Затраты',
    data: [
      {
        x: 'Оклад',
        y: [0, Number(costWaterfall.base_salary)]},
      {
        x: 'Премия мес.',
        y: [Number(costWaterfall.base_salary), Number(costWaterfall.base_salary) + Number(costWaterfall.monthly_bonus)]},
      {
        x: 'Премия квар.',
        y: [
          Number(costWaterfall.base_salary) + Number(costWaterfall.monthly_bonus),
          Number(costWaterfall.base_salary) + Number(costWaterfall.monthly_bonus) + Number(costWaterfall.quarterly_bonus)
        ]},
      {
        x: 'Премия год.',
        y: [
          Number(costWaterfall.base_salary) + Number(costWaterfall.monthly_bonus) + Number(costWaterfall.quarterly_bonus),
          Number(costWaterfall.gross_total)
        ]},
      {
        x: 'Gross Total',
        y: [0, Number(costWaterfall.gross_total)]},
      {
        x: 'НДФЛ',
        y: [Number(costWaterfall.gross_total), Number(costWaterfall.gross_total) - Number(costWaterfall.ndfl)]},
      {
        x: 'ПФР',
        y: [
          Number(costWaterfall.gross_total) - Number(costWaterfall.ndfl),
          Number(costWaterfall.gross_total) - Number(costWaterfall.ndfl) - Number(costWaterfall.pfr)
        ]},
      {
        x: 'ФОМС',
        y: [
          Number(costWaterfall.gross_total) - Number(costWaterfall.ndfl) - Number(costWaterfall.pfr),
          Number(costWaterfall.gross_total) - Number(costWaterfall.ndfl) - Number(costWaterfall.pfr) - Number(costWaterfall.foms)
        ]},
      {
        x: 'ФСС',
        y: [
          Number(costWaterfall.gross_total) - Number(costWaterfall.ndfl) - Number(costWaterfall.pfr) - Number(costWaterfall.foms),
          Number(costWaterfall.net_payroll)
        ]},
      {
        x: 'Net Payroll',
        y: [0, Number(costWaterfall.net_payroll)]},
    ]}] : [];

  const waterfallOptions: ApexOptions = {
    chart: {
      type: 'rangeBar',
      toolbar: { show: true }},
    plotOptions: {
      bar: {
        horizontal: false,
        columnWidth: '50%'}},
    dataLabels: {
      enabled: true,
      formatter: (val: any) => {
        const value = Array.isArray(val) ? val[1] - val[0] : val;
        return formatCurrency(value);
      }},
    xaxis: {
      type: 'category',
      labels: {
        rotate: -45}},
    yaxis: {
      labels: {
        formatter: (val: number) => formatCurrency(val)}},
    colors: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#1890ff', '#faad14', '#f5222d', '#722ed1', '#13c2c2', '#52c41a'],
    tooltip: {
      y: {
        formatter: (val: number) => formatCurrency(val)}}};

  // Tax by employee table columns
  const taxEmployeeColumns: ColumnsType<TaxByEmployee> = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
      fixed: 'left',
      width: 200,
      render: (text, record) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#888' }}>{record.position}</div>
        </div>
      )},
    {
      title: 'Gross доход',
      dataIndex: 'gross_income',
      key: 'gross_income',
      width: 150,
      align: 'right',
      render: (value) => formatCurrency(Number(value))},
    {
      title: 'НДФЛ',
      dataIndex: 'ndfl',
      key: 'ndfl',
      width: 120,
      align: 'right',
      render: (value) => formatCurrency(Number(value))},
    {
      title: 'Взносы',
      dataIndex: 'social_contributions',
      key: 'social_contributions',
      width: 120,
      align: 'right',
      render: (value) => formatCurrency(Number(value))},
    {
      title: 'Net доход',
      dataIndex: 'net_income',
      key: 'net_income',
      width: 150,
      align: 'right',
      render: (value) => formatCurrency(Number(value))},
    {
      title: 'Всего налогов',
      dataIndex: 'total_taxes',
      key: 'total_taxes',
      width: 150,
      align: 'right',
      render: (value) => (
        <span style={{ color: '#cf1322', fontWeight: 500 }}>
          {formatCurrency(Number(value))}
        </span>
      )},
    {
      title: 'НДФЛ %',
      dataIndex: 'effective_tax_rate',
      key: 'effective_tax_rate',
      width: 100,
      align: 'right',
      render: (value) => `${Number(value).toFixed(1)}%`},
    {
      title: 'Нагрузка %',
      dataIndex: 'effective_burden_rate',
      key: 'effective_burden_rate',
      width: 110,
      align: 'right',
      render: (value) => `${Number(value).toFixed(1)}%`},
  ];

  return (
    <div>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>
          <BarChartOutlined /> Аналитика ФОТ
        </Title>
        <Select
          value={selectedYear}
          onChange={setSelectedYear}
          style={{ width: 150 }}
        >
          {[currentYear - 1, currentYear, currentYear + 1].map((year) => (
            <Option key={year} value={year}>
              {year} год
            </Option>
          ))}
        </Select>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="Сводка" key="summary">
          {/* Salary Statistics Cards */}
      {salaryStats && (
        <>
          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Всего сотрудников"
                  value={salaryStats.total_employees}
                  prefix={<TeamOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Активных сотрудников"
                  value={salaryStats.active_employees}
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<ArrowUpOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Средняя зарплата"
                  value={Number(salaryStats.average_salary)}
                  precision={0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Медиана зарплаты"
                  value={Number(salaryStats.median_salary)}
                  precision={0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Минимум"
                  value={Number(salaryStats.min_salary)}
                  precision={0}
                  formatter={(value) => formatCurrency(Number(value))}
                  valueStyle={{ color: '#cf1322' }}
                  prefix={<ArrowDownOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Максимум"
                  value={Number(salaryStats.max_salary)}
                  precision={0}
                  formatter={(value) => formatCurrency(Number(value))}
                  valueStyle={{ color: '#3f8600' }}
                  prefix={<ArrowUpOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="75-й процентиль"
                  value={Number(salaryStats.percentile_75)}
                  precision={0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="90-й процентиль"
                  value={Number(salaryStats.percentile_90)}
                  precision={0}
                  formatter={(value) => formatCurrency(Number(value))}
                />
              </Card>
            </Col>
          </Row>
        </>
      )}

      {/* Salary Distribution Histogram */}
      <Card title="Распределение зарплат" style={{ marginBottom: '24px' }}>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={salaryDistributionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="range" />
            <YAxis />
            <Tooltip formatter={(value: number) => formatCurrency(value)} />
            <Bar dataKey="value" fill="#1890ff" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Salary Distribution Histogram with details */}
      {salaryDistribution && salaryDistribution.buckets.length > 0 && (
        <Card
          title="Распределение зарплат (гистограмма)"
          style={{ marginTop: '24px' }}
        >
          <Row gutter={[24, 24]}>
            <Col span={16}>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={salaryDistribution.buckets}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis
                    dataKey="range_label"
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis
                    label={{ value: 'Количество сотрудников', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip
                    formatter={(value: number, name: string) => {
                      if (name === 'employee_count') return [value, 'Сотрудников'];
                      return [value, name];
                    }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <Card size="small">
                            <div><strong>{data.range_label}</strong></div>
                            <div>Сотрудников: {data.employee_count} ({data.percentage}%)</div>
                            <div>Средняя ЗП: {formatCurrency(data.avg_salary)}</div>
                          </Card>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="employee_count" fill="#1890ff" name="Сотрудников" />
                </BarChart>
              </ResponsiveContainer>
            </Col>
            <Col span={8}>
              <Card size="small" title="Статистика распределения">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <Statistic
                    title="Всего сотрудников"
                    value={salaryDistribution.total_employees}
                    prefix={<TeamOutlined />}
                  />
                  <Divider style={{ margin: '8px 0' }} />
                  <div style={{ fontSize: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>Минимум:</span>
                      <strong>{formatCurrency(salaryDistribution.statistics.min_salary)}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>Максимум:</span>
                      <strong>{formatCurrency(salaryDistribution.statistics.max_salary)}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>Медиана:</span>
                      <strong>{formatCurrency(salaryDistribution.statistics.median_salary)}</strong>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <span>Среднее:</span>
                      <strong>{formatCurrency(salaryDistribution.statistics.avg_salary || 0)}</strong>
                    </div>
                  </div>
                  <Divider style={{ margin: '8px 0' }} />
                  <div style={{ fontSize: 13 }}>
                    <div><strong>Процентили:</strong></div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
                      <span>25%:</span>
                      <span>{formatCurrency(salaryDistribution.statistics.percentile_25)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>75%:</span>
                      <span>{formatCurrency(salaryDistribution.statistics.percentile_75)}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span>90%:</span>
                      <span>{formatCurrency(salaryDistribution.statistics.percentile_90)}</span>
                    </div>
                  </div>
                  {salaryDistribution.statistics.std_deviation && (
                    <>
                      <Divider style={{ margin: '8px 0' }} />
                      <div style={{ fontSize: 13 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>Стд. отклонение:</span>
                          <span>{formatCurrency(salaryDistribution.statistics.std_deviation)}</span>
                        </div>
                      </div>
                    </>
                  )}
                </Space>
              </Card>
            </Col>
          </Row>
        </Card>
      )}
        </TabPane>

        <TabPane tab="Динамика" key="dynamics">
          {/* Payroll Dynamics Chart */}
      <Card title="Динамика ФОТ: План vs Факт" style={{ marginBottom: '24px' }}>
        {dynamicsChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={dynamicsChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Area
                type="monotone"
                dataKey="План"
                stroke="#1890ff"
                fill="#1890ff"
                fillOpacity={0.3}
              />
              <Area
                type="monotone"
                dataKey="Факт"
                stroke="#52c41a"
                fill="#52c41a"
                fillOpacity={0.3}
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <Alert message="Нет данных за выбранный период" type="info" showIcon />
        )}
      </Card>

      {/* Payroll Structure Analysis */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={16}>
          <Card title="Структура ФОТ по месяцам">
            {structureChartData.length > 0 ? (
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={structureChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Bar dataKey="Оклад" stackId="a" fill="#1890ff" />
                  <Bar dataKey="Премия мес." stackId="a" fill="#52c41a" />
                  <Bar dataKey="Премия квар." stackId="a" fill="#faad14" />
                  <Bar dataKey="Премия год." stackId="a" fill="#f5222d" />
                  <Bar dataKey="Прочие" stackId="a" fill="#722ed1" />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <Alert message="Нет данных за выбранный период" type="info" showIcon />
            )}
          </Card>
        </Col>
        <Col span={8}>
          <Card title="Средняя структура ФОТ">
            {pieChartData.some(d => d.value > 0) ? (
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={pieChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={renderCustomLabel}
                    outerRadius={120}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {pieChartData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Alert message="Нет данных за выбранный период" type="info" showIcon />
            )}
            <Divider />
            <Space direction="vertical" style={{ width: '100%' }}>
              {pieChartData.map((item, index) => (
                <div key={item.name} style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Space>
                    <div
                      style={{
                        width: 12,
                        height: 12,
                        backgroundColor: COLORS[index],
                        borderRadius: 2}}
                    />
                    <span>{item.name}:</span>
                  </Space>
                  <span>
                    {formatCurrency(item.value)} ({item.percent}%)
                  </span>
                </div>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>
        </TabPane>

        <TabPane tab="Налоги и взносы" key="taxes">
          {isTaxLoading ? (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          ) : (
            <>
              {/* Tax Burden Summary Cards */}
              {taxBurden && (
                <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                  <Col xs={24} md={6}>
                    <Card>
                      <Statistic
                        title="НДФЛ"
                        value={Number(taxBurden.ndfl.total)}
                        formatter={(value) => formatCurrency(value as number)}
                        prefix={<DollarOutlined />}
                        suffix={
                          <Text type="secondary" style={{ fontSize: 14 }}>
                            ({Number(taxBurden.ndfl.effective_rate).toFixed(1)}%)
                          </Text>
                        }
                      />
                    </Card>
                  </Col>
                  <Col xs={24} md={6}>
                    <Card>
                      <Statistic
                        title="Страховые взносы"
                        value={Number(taxBurden.social_contributions.total_contributions)}
                        formatter={(value) => formatCurrency(value as number)}
                        prefix={<TeamOutlined />}
                        suffix={
                          <Text type="secondary" style={{ fontSize: 14 }}>
                            ({Number(taxBurden.social_contributions.effective_rate).toFixed(1)}%)
                          </Text>
                        }
                      />
                    </Card>
                  </Col>
                  <Col xs={24} md={6}>
                    <Card>
                      <Statistic
                        title="Общая налоговая нагрузка"
                        value={Number(taxBurden.total_tax_burden)}
                        formatter={(value) => formatCurrency(value as number)}
                        valueStyle={{ color: '#cf1322' }}
                        prefix={<FundOutlined />}
                      />
                    </Card>
                  </Col>
                  <Col xs={24} md={6}>
                    <Card>
                      <Statistic
                        title="Эффективная ставка"
                        value={Number(taxBurden.effective_burden_rate)}
                        suffix="%"
                        precision={1}
                        valueStyle={{ color: '#cf1322' }}
                        prefix={<PercentageOutlined />}
                      />
                    </Card>
                  </Col>
                </Row>
              )}

              {/* Waterfall Chart and Pie Chart */}
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} lg={14}>
                  <Card title="Декомпозиция затрат (Waterfall)">
                    {costWaterfall && waterfallSeries.length > 0 ? (
                      <ReactApexChart
                        options={waterfallOptions}
                        series={waterfallSeries}
                        type="rangeBar"
                        height={400}
                      />
                    ) : (
                      <Alert message="Нет данных за выбранный период" type="info" showIcon />
                    )}
                  </Card>
                </Col>
                <Col xs={24} lg={10}>
                  <Card title="Распределение налогов">
                    {taxDistributionData.length > 0 && taxDistributionData.some(d => d.value > 0) ? (
                      <ResponsiveContainer width="100%" height={400}>
                        <PieChart>
                          <Pie
                            data={taxDistributionData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={120}
                            fill="#8884d8"
                            dataKey="value"
                          >
                            {taxDistributionData.map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip formatter={(value: number) => formatCurrency(value)} />
                        </PieChart>
                      </ResponsiveContainer>
                    ) : (
                      <Alert message="Нет данных за выбранный период" type="info" showIcon />
                    )}
                    <Divider />
                    <Space direction="vertical" style={{ width: '100%' }}>
                      {taxDistributionData.map((item) => (
                        <div key={item.name} style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Space>
                            <div
                              style={{
                                width: 12,
                                height: 12,
                                backgroundColor: item.color,
                                borderRadius: 2}}
                            />
                            <span>{item.name}:</span>
                          </Space>
                          <span>{formatCurrency(item.value)}</span>
                        </div>
                      ))}
                    </Space>
                  </Card>
                </Col>
              </Row>

              {/* Stacked Area Chart - Tax + Salary Dynamics */}
              {taxMonthlyData.length > 0 && (
                <Card title="Динамика ФОТ и налогов по месяцам" style={{ marginBottom: 24 }}>
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={taxMonthlyData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="month_name" />
                      <YAxis tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
                      <Tooltip formatter={(value: number) => formatCurrency(value)} />
                      <Legend />
                      <Area
                        type="monotone"
                        dataKey="net_payroll"
                        stackId="1"
                        stroke="#1890ff"
                        fill="#1890ff"
                        name="Чистая ЗП"
                      />
                      <Area
                        type="monotone"
                        dataKey="ndfl"
                        stackId="1"
                        stroke="#faad14"
                        fill="#faad14"
                        name="НДФЛ"
                      />
                      <Area
                        type="monotone"
                        dataKey="pfr"
                        stackId="1"
                        stroke="#f5222d"
                        fill="#f5222d"
                        name="ПФР"
                      />
                      <Area
                        type="monotone"
                        dataKey="foms"
                        stackId="1"
                        stroke="#722ed1"
                        fill="#722ed1"
                        name="ФОМС"
                      />
                      <Area
                        type="monotone"
                        dataKey="fss"
                        stackId="1"
                        stroke="#13c2c2"
                        fill="#13c2c2"
                        name="ФСС"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </Card>
              )}

              {/* Line Chart and Bar Chart */}
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} lg={12}>
                  <Card title="Эффективная ставка по месяцам">
                    {taxMonthlyData.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={taxMonthlyData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="month_name" angle={-45} textAnchor="end" height={80} />
                          <YAxis domain={[0, 40]} tickFormatter={(value) => `${value}%`} />
                          <Tooltip formatter={(value: number) => `${value.toFixed(1)}%`} />
                          <Legend />
                          <Line
                            type="monotone"
                            dataKey="effective_ndfl"
                            stroke="#1890ff"
                            name="НДФЛ %"
                            strokeWidth={2}
                          />
                          <Line
                            type="monotone"
                            dataKey="effective_total"
                            stroke="#f5222d"
                            name="Общая нагрузка %"
                            strokeWidth={2}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    ) : (
                      <Alert message="Нет данных за выбранный период" type="info" showIcon />
                    )}
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Налоговая нагрузка по сотрудникам (топ 10)">
                    {taxByEmployee && taxByEmployee.length > 0 ? (
                      <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={taxByEmployee.slice(0, 10)}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="employee_name" angle={-45} textAnchor="end" height={120} tick={{ fontSize: 10 }} />
                          <YAxis tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
                          <Tooltip formatter={(value: number) => formatCurrency(value)} />
                          <Legend />
                          <Bar dataKey="net_income" fill="#52c41a" name="Net" />
                          <Bar dataKey="ndfl" fill="#faad14" name="НДФЛ" />
                          <Bar dataKey="social_contributions" fill="#f5222d" name="Взносы" />
                        </BarChart>
                      </ResponsiveContainer>
                    ) : (
                      <Alert message="Нет данных за выбранный период" type="info" showIcon />
                    )}
                  </Card>
                </Col>
              </Row>

              {/* Tax Details Table */}
              {taxByEmployee && taxByEmployee.length > 0 && (
                <Card title="Детализация налогов по сотрудникам">
                  <Table<TaxByEmployee>
                    dataSource={taxByEmployee}
                    columns={taxEmployeeColumns}
                    rowKey="employee_id"
                    pagination={{ pageSize: 10 }}
                    scroll={{ x: 1200 }}
                  />
                </Card>
              )}
            </>
          )}
        </TabPane>

        <TabPane tab="Прогноз" key="forecast">
          {/* Payroll Forecast */}
      {forecast && forecast.length > 0 && (
        <Card
          title={
            <Space>
              <span>Прогноз ФОТ на ближайшие месяцы</span>
              <Tag color={
                forecast[0].confidence === 'high' ? 'green' :
                forecast[0].confidence === 'medium' ? 'orange' : 'red'
              }>
                {forecast[0].confidence === 'high' ? 'Высокая точность' :
                 forecast[0].confidence === 'medium' ? 'Средняя точность' : 'Низкая точность'}
              </Tag>
              <Text type="secondary">
                (на основе {forecast[0].based_on_months} месяцев)
              </Text>
            </Space>
          }
          style={{ marginTop: '24px' }}
        >
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecast.map(item => ({
              month: `${MONTH_NAMES[item.month - 1]} ${item.year}`,
              'Прогноз': Number(item.forecasted_total)}))}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Legend />
              <Line
                type="monotone"
                dataKey="Прогноз"
                stroke="#722ed1"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>

          <Divider />

          <Row gutter={[16, 16]}>
            {forecast.map((item, index) => (
              <Col span={8} key={index}>
                <Card size="small">
                  <Statistic
                    title={`${MONTH_NAMES[item.month - 1]} ${item.year}`}
                    value={Number(item.forecasted_total)}
                    precision={0}
                    formatter={(value) => formatCurrency(Number(value))}
                  />
                  <div style={{ fontSize: 12, color: '#888', marginTop: 8 }}>
                    <div>Оклад: {formatCurrency(Number(item.forecasted_base_salary))}</div>
                    <div>
                      Премии:{' '}
                      {formatCurrency(
                        Number(item.forecasted_monthly_bonus) +
                          Number(item.forecasted_quarterly_bonus) +
                          Number(item.forecasted_annual_bonus)
                      )}
                    </div>
                    <div>Прочее: {formatCurrency(Number(item.forecasted_other))}</div>
                    <div>Сотрудников: {item.employee_count}</div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}
        </TabPane>
      </Tabs>
    </div>
  );
}
