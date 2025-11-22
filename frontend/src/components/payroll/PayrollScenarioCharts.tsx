import React from 'react';
import { Card, Row, Col, Empty } from 'antd';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
} from 'recharts';
import { PayrollScenarioWithDetails } from '@/api/payrollScenarios';

interface PayrollScenarioChartsProps {
  scenario: PayrollScenarioWithDetails;
}

const COLORS = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2'];

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
};

const PayrollScenarioCharts: React.FC<PayrollScenarioChartsProps> = ({ scenario }) => {
  // Подготовка данных для графика сравнения зарплат
  const salaryComparisonData = scenario.scenario_details
    .filter(detail => detail.base_year_salary && detail.base_year_salary > 0)
    .slice(0, 10) // Топ-10 сотрудников
    .map(detail => {
      // ИСПРАВЛЕНО: Учитываем все виды премий
      const targetYearSalary =
        (detail.base_salary + (detail.monthly_bonus || 0)) * 12 +
        (detail.quarterly_bonus || 0) * 4 +
        (detail.annual_bonus || 0);

      return {
        name: detail.employee_name.split(' ').slice(0, 2).join(' '), // Имя и фамилия
        baseYear: detail.base_year_salary || 0,
        targetYear: targetYearSalary,
        increase: detail.cost_increase || 0,
      };
    });

  // Подготовка данных для графика распределения страховых взносов
  const insuranceDistributionData = [
    {
      name: 'ПФР',
      value: scenario.scenario_details.reduce((sum, d) => sum + (d.pension_contribution || 0), 0),
    },
    {
      name: 'ФОМС',
      value: scenario.scenario_details.reduce((sum, d) => sum + (d.medical_contribution || 0), 0),
    },
    {
      name: 'ФСС',
      value: scenario.scenario_details.reduce((sum, d) => sum + (d.social_contribution || 0), 0),
    },
    {
      name: 'Травматизм',
      value: scenario.scenario_details.reduce((sum, d) => sum + (d.injury_contribution || 0), 0),
    },
  ].filter(item => item.value > 0);

  // Подготовка данных для графика структуры затрат
  const costStructureData = [
    {
      name: 'Базовая зарплата',
      value: scenario.total_base_salary || 0,
      percent: ((scenario.total_base_salary || 0) / (scenario.total_payroll_cost || 1)) * 100,
    },
    {
      name: 'Страховые взносы',
      value: scenario.total_insurance_cost || 0,
      percent: ((scenario.total_insurance_cost || 0) / (scenario.total_payroll_cost || 1)) * 100,
    },
    {
      name: 'НДФЛ',
      value: scenario.scenario_details.reduce((sum, d) => sum + (d.income_tax || 0), 0),
      percent: (scenario.scenario_details.reduce((sum, d) => sum + (d.income_tax || 0), 0) / (scenario.total_payroll_cost || 1)) * 100,
    },
  ].filter(item => item.value > 0);

  // Подготовка данных для графика динамики роста затрат
  const costGrowthData = scenario.scenario_details
    .filter(detail => detail.base_year_salary && detail.base_year_salary > 0)
    .map(detail => ({
      name: detail.employee_name.split(' ').slice(0, 2).join(' '),
      baseYearCost: (detail.base_year_salary || 0) + (detail.base_year_insurance || 0),
      targetYearCost: detail.total_employee_cost || 0,
      growthPercent: detail.base_year_salary
        ? (((detail.total_employee_cost || 0) - ((detail.base_year_salary || 0) + (detail.base_year_insurance || 0))) /
            ((detail.base_year_salary || 0) + (detail.base_year_insurance || 0))) *
          100
        : 0,
    }))
    .sort((a, b) => b.growthPercent - a.growthPercent)
    .slice(0, 10);

  // Подготовка данных для графика прогноза по месяцам
  const monthlyProjectionData = Array.from({ length: 12 }, (_, i) => {
    const month = i + 1;
    const monthlyBaseSalary = (scenario.total_base_salary || 0) / 12;
    const monthlyInsurance = (scenario.total_insurance_cost || 0) / 12;
    const monthlyIncomeTax = scenario.scenario_details.reduce((sum, d) => sum + (d.income_tax || 0), 0) / 12;

    return {
      month: `${month} мес`,
      baseSalary: monthlyBaseSalary,
      insurance: monthlyInsurance,
      incomeTax: monthlyIncomeTax,
      total: monthlyBaseSalary + monthlyInsurance + monthlyIncomeTax,
    };
  });

  if (!scenario.scenario_details || scenario.scenario_details.length === 0) {
    return (
      <Card>
        <Empty description="Нет данных для визуализации" />
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px 0' }}>
      <Row gutter={[16, 16]}>
        {/* График сравнения зарплат (базовый vs целевой год) */}
        <Col xs={24} lg={12}>
          <Card title="Сравнение зарплат: Базовый vs Целевой год" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={salaryComparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                <YAxis tickFormatter={formatCurrency} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Bar dataKey="baseYear" name="Базовый год" fill="#1890ff" />
                <Bar dataKey="targetYear" name="Целевой год" fill="#52c41a" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* График распределения страховых взносов */}
        <Col xs={24} lg={12}>
          <Card title="Распределение страховых взносов" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={insuranceDistributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {insuranceDistributionData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* График структуры затрат */}
        <Col xs={24} lg={12}>
          <Card title="Структура затрат на ФОТ" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={costStructureData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${percent.toFixed(1)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {costStructureData.map((_entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* График динамики роста затрат */}
        <Col xs={24} lg={12}>
          <Card title="Топ-10 по росту затрат" bordered={false}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={costGrowthData} layout="horizontal">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" tickFormatter={(value) => `${value.toFixed(0)}%`} />
                <YAxis dataKey="name" type="category" width={150} />
                <Tooltip
                  formatter={(value: number, name: string) => {
                    if (name === 'growthPercent') {
                      return `${value.toFixed(1)}%`;
                    }
                    return formatCurrency(value);
                  }}
                />
                <Legend />
                <Bar dataKey="growthPercent" name="Рост затрат, %" fill="#faad14" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* График прогноза по месяцам */}
        <Col xs={24}>
          <Card title="Прогноз затрат по месяцам" bordered={false}>
            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={monthlyProjectionData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis tickFormatter={formatCurrency} />
                <Tooltip formatter={(value: number) => formatCurrency(value)} />
                <Legend />
                <Area type="monotone" dataKey="total" name="Итого" fill="#1890ff" stroke="#1890ff" fillOpacity={0.3} />
                <Bar dataKey="baseSalary" name="Базовая зарплата" fill="#52c41a" stackId="a" />
                <Bar dataKey="insurance" name="Страховые взносы" fill="#faad14" stackId="a" />
                <Bar dataKey="incomeTax" name="НДФЛ" fill="#f5222d" stackId="a" />
                <Line type="monotone" dataKey="total" name="Общие затраты" stroke="#722ed1" strokeWidth={2} />
              </ComposedChart>
            </ResponsiveContainer>
          </Card>
        </Col>

        {/* Сводная статистика изменений */}
        {scenario.base_year_total_cost && scenario.base_year_total_cost > 0 && (
          <Col xs={24}>
            <Card title="Сравнение с базовым годом" bordered={false}>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={[
                    {
                      category: 'Общие затраты',
                      baseYear: scenario.base_year_total_cost,
                      targetYear: scenario.total_payroll_cost || 0,
                      difference: scenario.cost_difference || 0,
                    },
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" />
                  <YAxis tickFormatter={formatCurrency} />
                  <Tooltip formatter={(value: number) => formatCurrency(value)} />
                  <Legend />
                  <Bar dataKey="baseYear" name="Базовый год" fill="#1890ff" />
                  <Bar dataKey="targetYear" name="Целевой год" fill="#52c41a" />
                  <Bar dataKey="difference" name="Разница" fill="#faad14" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default PayrollScenarioCharts;
