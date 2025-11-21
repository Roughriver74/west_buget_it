import React, { useState } from 'react'
import { Card, Row, Col, Statistic, DatePicker, Spin, Alert, Table, Progress, Tag } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { Area, Pie, Column } from '@ant-design/plots'
import { TrophyOutlined, TeamOutlined, RiseOutlined, DollarOutlined, AimOutlined } from '@ant-design/icons'
import dayjs, { Dayjs } from 'dayjs'
import { kpiApi } from '@/api/kpi'
import { useDepartment } from '@/contexts/DepartmentContext'

const KPIAnalyticsPage: React.FC = () => {
  const { selectedDepartment } = useDepartment()
  const isMobile = useIsMobile()
  const isSmallScreen = useIsSmallScreen()
  const [selectedYear, setSelectedYear] = useState<Dayjs>(dayjs())
  const year = selectedYear.year()

  const { data: employeeSummary, isLoading: loadingEmployees } = useQuery({
    queryKey: ['kpi-employee-summary', year, selectedDepartment?.id],
    queryFn: () => kpiApi.getEmployeeSummary({
      year,
      department_id: selectedDepartment?.id
    }),
    enabled: !!year,
  })

  const { data: goalProgress, isLoading: loadingGoals } = useQuery({
    queryKey: ['kpi-goal-progress', year, selectedDepartment?.id],
    queryFn: () => kpiApi.getGoalProgress({
      year,
      department_id: selectedDepartment?.id
    }),
    enabled: !!year,
  })

  const { data: kpiTrends, isLoading: loadingTrends } = useQuery({
    queryKey: ['kpi-trends', year, selectedDepartment?.id],
    queryFn: () => kpiApi.getKpiTrends({
      year,
      department_id: selectedDepartment?.id
    }),
    enabled: !!year,
  })

  const { data: bonusDistribution, isLoading: loadingBonus } = useQuery({
    queryKey: ['bonus-distribution', year],
    queryFn: () => kpiApi.getBonusDistribution({ year }),
    enabled: !!year,
  })

  const isLoading = loadingEmployees || loadingGoals || loadingTrends || loadingBonus

  // Calculate summary statistics
  const avgKPI = (employeeSummary && employeeSummary.length > 0)
    ? employeeSummary.reduce((sum, e) => sum + Number(e.kpi_percentage || 0), 0) / employeeSummary.length
    : 0
  const totalBonuses = employeeSummary?.reduce((sum, e) => sum + Number(e.total_bonus_calculated || 0), 0) || 0
  const totalEmployees = employeeSummary?.length || 0
  const goalsAchieved = employeeSummary?.reduce((sum, e) => sum + (e.goals_achieved || 0), 0) || 0
  const totalGoals = employeeSummary?.reduce((sum, e) => sum + (e.goals_count || 0), 0) || 0
  const achievementRate = totalGoals > 0 ? (goalsAchieved / totalGoals) * 100 : 0

  // Prepare data for employee ranking
  const rankedEmployees = employeeSummary
    ?.slice()
    .sort((a, b) => Number(b.kpi_percentage || 0) - Number(a.kpi_percentage || 0))
    .map((emp, index) => ({
      ...emp,
      rank: index + 1,
    })) || []

  // Employee ranking columns
  const rankingColumns = [
    {
      title: 'Место',
      dataIndex: 'rank',
      key: 'rank',
      width: 80,
      render: (rank: number) => (
        <Tag color={rank === 1 ? 'gold' : rank === 2 ? 'silver' : rank === 3 ? '#cd7f32' : 'default'}>
          #{rank}
        </Tag>
      ),
    },
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
    },
    {
      title: 'Должность',
      dataIndex: 'position',
      key: 'position',
    },
    {
      title: 'КПИ %',
      dataIndex: 'kpi_percentage',
      key: 'kpi_percentage',
      render: (val: number | null) => (
        <span style={{ fontWeight: 'bold', color: val && val >= 100 ? '#52c41a' : '#ff4d4f' }}>
          {val?.toFixed(1)}%
        </span>
      ),
    },
    {
      title: 'Премии',
      dataIndex: 'total_bonus_calculated',
      key: 'total_bonus_calculated',
      render: (val: number) => `${Number(val).toLocaleString('ru-RU')} ₽`,
    },
    {
      title: 'Цели',
      key: 'goals',
      render: (_: any, record: any) => (
        <Progress
          percent={record.goals_count > 0 ? (record.goals_achieved / record.goals_count) * 100 : 0}
          size="small"
          format={() => `${record.goals_achieved}/${record.goals_count}`}
        />
      ),
    },
  ]

  // Goal progress columns
  const goalColumns = [
    {
      title: 'Цель',
      dataIndex: 'goal_name',
      key: 'goal_name',
    },
    {
      title: 'Категория',
      dataIndex: 'category',
      key: 'category',
      render: (val: string | null) => val || '-',
    },
    {
      title: 'Назначено сотрудников',
      dataIndex: 'employees_assigned',
      key: 'employees_assigned',
    },
    {
      title: 'Достигли цели',
      dataIndex: 'employees_achieved',
      key: 'employees_achieved',
    },
    {
      title: 'Прогресс',
      key: 'progress',
      render: (_: any, record: any) => (
        <Progress
          percent={record.employees_assigned > 0 ? (record.employees_achieved / record.employees_assigned) * 100 : 0}
          size="small"
        />
      ),
    },
    {
      title: 'Ср. выполнение',
      dataIndex: 'avg_achievement_percentage',
      key: 'avg_achievement_percentage',
      render: (val: number) => `${Number(val).toFixed(1)}%`,
    },
  ]

  // KPI Trends Chart
  const trendsChartConfig = {
    data: kpiTrends || [],
    xField: 'month',
    yField: 'avg_kpi',
    xAxis: {
      label: {
        formatter: (v: string) => {
          const months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
          return months[parseInt(v) - 1] || v
        },
      },
    },
    yAxis: {
      label: {
        formatter: (v: string) => `${v}%`,
      },
    },
    line: {
      color: '#1890ff',
    },
    areaStyle: {
      fillOpacity: 0.3,
    },
    smooth: true,
    point: {
      size: 5,
      shape: 'circle',
    },
  }

  // Bonus Distribution by Department
  const bonusChartConfig = {
    data: bonusDistribution || [],
    xField: 'department_name',
    yField: 'total_bonus',
    seriesField: 'department_name',
    label: {
      position: 'middle' as const,
      style: {
        fill: '#FFFFFF',
        opacity: 0.6,
      },
      formatter: (datum: any) => `${Number(datum.total_bonus).toLocaleString('ru-RU')} ₽`,
    },
    xAxis: {
      label: {
        autoHide: true,
        autoRotate: false,
      },
    },
    yAxis: {
      label: {
        formatter: (v: string) => `${Number(v).toLocaleString('ru-RU')} ₽`,
      },
    },
  }

  // Bonus Distribution by Type (Pie Chart)
  const bonusTypeData = bonusDistribution?.flatMap(dept => [
    { type: 'Месячные', value: dept.monthly_total, department: dept.department_name },
    { type: 'Квартальные', value: dept.quarterly_total, department: dept.department_name },
    { type: 'Годовые', value: dept.annual_total, department: dept.department_name },
  ]).filter(item => item.value > 0) || []

  const bonusTypePieConfig = {
    data: bonusTypeData,
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer' as const,
      content: '{name} {percentage}',
    },
    interactions: [
      {
        type: 'pie-legend-active',
      },
      {
        type: 'element-active',
      },
    ],
  }

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '400px', padding: '100px 0' }}>
        <Spin size="large" tip="Загрузка аналитики КПИ...">
          <div style={{ minHeight: 200 }} />
        </Spin>
      </div>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <Row gutter={[16, 16]} align="middle" style={{ marginBottom: 24 }}>
        <Col flex="auto">
          <h1 style={{ margin: 0 }}>Аналитика КПИ</h1>
        </Col>
        <Col>
          <DatePicker
            picker="year"
            value={selectedYear}
            onChange={(date) => date && setSelectedYear(date)}
            placeholder="Выберите год"
          />
        </Col>
      </Row>

      {/* Key Metrics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Средний КПИ"
              value={avgKPI || 0}
              precision={1}
              suffix="%"
              prefix={<RiseOutlined />}
              valueStyle={{ color: avgKPI >= 100 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Сотрудников"
              value={totalEmployees}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Общие премии"
              value={totalBonuses}
              precision={0}
              suffix="₽"
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Достижение целей"
              value={achievementRate || 0}
              precision={1}
              suffix="%"
              prefix={<AimOutlined />}
              valueStyle={{ color: achievementRate >= 80 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* KPI Trends Chart */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Динамика КПИ по месяцам">
            {kpiTrends && kpiTrends.length > 0 ? (
              <Area {...trendsChartConfig} />
            ) : (
              <Alert message="Нет данных для отображения динамики КПИ" type="info" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Employee Ranking */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card
            title={
              <span>
                <TrophyOutlined style={{ marginRight: 8 }} />
                Рейтинг сотрудников по КПИ
              </span>
            }
          >
            <ResponsiveTable
              dataSource={rankedEmployees}
              columns={rankingColumns}
              rowKey="employee_id"
              pagination={{ pageSize: 10 }} mobileLayout="card"
            />
          </Card>
        </Col>
      </Row>

      {/* Goals Progress */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="Анализ выполнения целей">
            {goalProgress && goalProgress.length > 0 ? (
              <ResponsiveTable
                dataSource={goalProgress}
                columns={goalColumns}
                rowKey="goal_id"
                pagination={{ pageSize: 10 }} mobileLayout="card"
              />
            ) : (
              <Alert message="Нет данных о целях" type="info" />
            )}
          </Card>
        </Col>
      </Row>

      {/* Bonus Distribution */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Распределение премий по отделам">
            {bonusDistribution && bonusDistribution.length > 0 ? (
              <Column {...bonusChartConfig} />
            ) : (
              <Alert message="Нет данных о премиях" type="info" />
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Структура премий">
            {bonusTypeData.length > 0 ? (
              <Pie {...bonusTypePieConfig} />
            ) : (
              <Alert message="Нет данных о структуре премий" type="info" />
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default KPIAnalyticsPage
