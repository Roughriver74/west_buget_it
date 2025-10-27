import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
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
} from 'antd';
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
  Cell,
} from 'recharts';
import {
  BarChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  TeamOutlined,
} from '@ant-design/icons';
import { useDepartment } from '../contexts/DepartmentContext';
import { payrollAnalyticsAPI } from '../api/payroll';
import { formatCurrency } from '../utils/formatters';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2'];
const MONTH_NAMES = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

export default function PayrollAnalyticsPage() {
  const currentYear = dayjs().year();
  const [selectedYear, setSelectedYear] = useState(currentYear);
  const { selectedDepartment } = useDepartment();

  // Fetch salary statistics
  const { data: salaryStats, isLoading: statsLoading } = useQuery({
    queryKey: ['payroll-salary-stats', selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getSalaryStats(selectedDepartment?.id),
  });

  // Fetch payroll structure
  const { data: structure, isLoading: structureLoading } = useQuery({
    queryKey: ['payroll-structure', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getStructure(selectedYear, selectedDepartment?.id),
  });

  // Fetch payroll dynamics
  const { data: dynamics, isLoading: dynamicsLoading } = useQuery({
    queryKey: ['payroll-dynamics', selectedYear, selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getDynamics(selectedYear, selectedDepartment?.id),
  });

  // Fetch payroll forecast
  const { data: forecast, isLoading: forecastLoading } = useQuery({
    queryKey: ['payroll-forecast', selectedDepartment?.id],
    queryFn: () => payrollAnalyticsAPI.getForecast({
      months_ahead: 6,
      historical_months: 6,
      department_id: selectedDepartment?.id,
    }),
  });

  const isLoading = statsLoading || structureLoading || dynamicsLoading || forecastLoading;

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
    'Сотрудников': item.employee_count,
  })) || [];

  const structureChartData = structure?.map((item) => ({
    month: MONTH_NAMES[item.month - 1],
    'Оклад': Number(item.total_base_salary),
    'Премия мес.': Number(item.total_monthly_bonus),
    'Премия квар.': Number(item.total_quarterly_bonus),
    'Премия год.': Number(item.total_annual_bonus),
    'Прочие': Number(item.total_other_payments),
  })) || [];

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
                        borderRadius: 2,
                      }}
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
              'Прогноз': Number(item.forecasted_total),
            }))}>
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
    </div>
  );
}
