import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  DatePicker,
  Tabs,
  Statistic,
  Table,
  Space,
  Typography,
  Tag,
  Empty,
  Alert
} from 'antd';
import {
  RiseOutlined,
  DollarOutlined,
  BarChartOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { Line, Column } from '@ant-design/plots';
import type { TabsProps } from 'antd';

import { useDepartment } from '../contexts/DepartmentContext';
import { analyticsApi } from '../api';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';

const { Title, Text } = Typography;

const ExtendedAnalyticsPage: React.FC = () => {
  const { selectedDepartment } = useDepartment();
  const [activeTab, setActiveTab] = useState('execution');
  const [year, setYear] = useState(dayjs().year());

  // Fetch budget execution data
  const { data: executionData, isLoading: executionLoading, error: executionError } = useQuery({
    queryKey: ['budget-execution', year, selectedDepartment?.id],
    queryFn: async () => {
      const res = await analyticsApi.getBudgetExecution({
        year,
        department_id: selectedDepartment?.id
      });
      return res;
    },
    enabled: activeTab === 'execution' && !!selectedDepartment
  });

  // Fetch category analytics
  const { data: categoryData, isLoading: categoryLoading, error: categoryError } = useQuery({
    queryKey: ['analytics-by-category', year, selectedDepartment?.id],
    queryFn: async () => {
      const res = await analyticsApi.getByCategory({
        year,
        department_id: selectedDepartment?.id
      });
      return res;
    },
    enabled: activeTab === 'categories' && !!selectedDepartment
  });

  // Fetch trends data
  const { data: trendsData, isLoading: trendsLoading, error: trendsError } = useQuery({
    queryKey: ['analytics-trends', year, selectedDepartment?.id],
    queryFn: async () => {
      const res = await analyticsApi.getTrends({
        year
      });
      return res;
    },
    enabled: activeTab === 'trends' && !!selectedDepartment
  });

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
    }).format(value)
  }

  // Budget Execution Tab
  const renderExecutionTab = () => {
    if (executionLoading) return <LoadingState />;
    if (executionError) return <ErrorState description={String(executionError)} />;

    // Debug logging
    console.log('[ExtendedAnalytics] executionData:', executionData);
    console.log('[ExtendedAnalytics] executionData type:', typeof executionData);
    console.log('[ExtendedAnalytics] executionData keys:', executionData ? Object.keys(executionData) : 'null');

    if (!executionData) return <Empty description="Нет данных" />;

    const data: any = executionData;
    console.log('[ExtendedAnalytics] data.months:', data.months);
    console.log('[ExtendedAnalytics] data.by_category length:', data.by_category?.length);

    const monthlyData = data.months?.map((item: any) => ({
      month: item.month_name || `${item.month} мес`,
      plan: item.planned || 0,
      fact: item.actual || 0,
      execution: item.execution_percent || 0
    })) || [];

    console.log('[ExtendedAnalytics] monthlyData length:', monthlyData.length);

    const totalPlanned = data.total_planned || 0;
    const totalActual = data.total_actual || 0;
    const totalRemaining = totalPlanned - totalActual;
    const executionPercent = totalPlanned > 0 ? (totalActual / totalPlanned * 100) : 0;

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Общий бюджет"
                value={totalPlanned}
                precision={0}
                suffix="₽"
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Факт"
                value={totalActual}
                precision={0}
                suffix="₽"
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Остаток"
                value={totalRemaining}
                precision={0}
                suffix="₽"
                valueStyle={{ color: totalRemaining >= 0 ? '#3f8600' : '#cf1322' }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Исполнение"
                value={executionPercent}
                precision={1}
                suffix="%"
                valueStyle={{ color: executionPercent > 100 ? '#cf1322' : '#3f8600' }}
              />
            </Card>
          </Col>
        </Row>

        <Card title="Помесячное исполнение бюджета">
          <Column
            data={monthlyData}
            xField="month"
            yField="plan"
            isGroup
            seriesField="type"
            label={{
              position: 'top',
              formatter: (datum: any) => formatCurrency(datum.plan)
            }}
          />
        </Card>
      </Space>
    );
  };

  // Categories Tab
  const renderCategoriesTab = () => {
    if (categoryLoading) return <LoadingState />;
    if (categoryError) return <ErrorState description={String(categoryError)} />;
    if (!categoryData || !categoryData.categories) return <Empty description="Нет данных" />;

    const columns = [
      {
        title: 'Категория',
        dataIndex: 'category_name',
        key: 'category_name',
        width: 200,
      },
      {
        title: 'Тип',
        dataIndex: 'category_type',
        key: 'category_type',
        render: (type: string) => (
          <Tag color={type === 'CAPEX' ? 'blue' : 'green'}>{type}</Tag>
        )
      },
      {
        title: 'План',
        dataIndex: 'planned',
        key: 'planned',
        render: (val: number) => formatCurrency(val || 0),
        sorter: (a: any, b: any) => (a.planned || 0) - (b.planned || 0)
      },
      {
        title: 'Факт',
        dataIndex: 'actual',
        key: 'actual',
        render: (val: number) => formatCurrency(val || 0),
        sorter: (a: any, b: any) => (a.actual || 0) - (b.actual || 0)
      },
      {
        title: 'Остаток',
        dataIndex: 'remaining',
        key: 'remaining',
        render: (val: number) => {
          const remaining = val || 0;
          return (
            <Text type={remaining < 0 ? 'danger' : 'success'}>
              {formatCurrency(remaining)}
            </Text>
          );
        },
        sorter: (a: any, b: any) => (a.remaining || 0) - (b.remaining || 0)
      },
      {
        title: 'Исполнение',
        dataIndex: 'execution_percent',
        key: 'execution_percent',
        render: (val: number) => {
          const rate = val || 0;
          return (
            <Tag color={rate > 100 ? 'red' : rate > 90 ? 'orange' : 'green'}>
              {rate.toFixed(1)}%
            </Tag>
          );
        },
        sorter: (a: any, b: any) => (a.execution_percent || 0) - (b.execution_percent || 0)
      },
    ];

    const chartData = categoryData.categories.slice(0, 10).map((item: any) => ({
      category: item.category_name.length > 15 ? item.category_name.substring(0, 15) + '...' : item.category_name,
      plan: item.planned || 0,
      fact: item.actual || 0
    }));

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Всего категорий"
                value={categoryData.categories.length}
                prefix={<BarChartOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Общий план"
                value={categoryData.total_planned || 0}
                precision={0}
                suffix="₽"
                prefix={<DollarOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8}>
            <Card>
              <Statistic
                title="Общий факт"
                value={categoryData.total_actual || 0}
                precision={0}
                suffix="₽"
              />
            </Card>
          </Col>
        </Row>

        <Card title="Топ-10 категорий по бюджету">
          <Column
            data={chartData}
            xField="category"
            yField="plan"
            isGroup
            seriesField="type"
            color={['#1890ff', '#52c41a']}
          />
        </Card>

        <Card title="Детализация по категориям">
          <Table
            columns={columns}
            dataSource={categoryData.categories}
            rowKey="category_id"
            pagination={{ pageSize: 20 }}
            scroll={{ x: 1000 }}
          />
        </Card>
      </Space>
    );
  };

  // Trends Tab
  const renderTrendsTab = () => {
    if (trendsLoading) return <LoadingState />;
    if (trendsError) return <ErrorState description={String(trendsError)} />;
    if (!trendsData || !trendsData.monthly_trends) return <Empty description="Нет данных" />;

    const lineData = trendsData.monthly_trends.map((item: any) => ({
      month: `${item.month} мес`,
      amount: item.total_amount || 0
    }));

    return (
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Alert
          message="Информация"
          description="Анализ трендов расходов по месяцам за выбранный год"
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
        />

        <Card title="Динамика расходов по месяцам">
          <Line
            data={lineData}
            xField="month"
            yField="amount"
            smooth
            point={{
              size: 5,
              shape: 'circle',
            }}
            label={{
              formatter: (datum: any) => `${(datum.amount / 1000).toFixed(0)}K ₽`
            }}
          />
        </Card>

        {trendsData.top_categories && (
          <Card title="Топ категорий по расходам">
            <Column
              data={trendsData.top_categories.map((item: any) => ({
                category: item.category_name,
                amount: item.total_amount || 0
              }))}
              xField="category"
              yField="amount"
              label={{
                position: 'top',
                formatter: (datum: any) => formatCurrency(datum.amount)
              }}
              color="#1890ff"
            />
          </Card>
        )}
      </Space>
    );
  };

  const tabs: TabsProps['items'] = [
    {
      key: 'execution',
      label: 'Исполнение бюджета',
      children: renderExecutionTab(),
      icon: <DollarOutlined />
    },
    {
      key: 'categories',
      label: 'По категориям',
      children: renderCategoriesTab(),
      icon: <BarChartOutlined />
    },
    {
      key: 'trends',
      label: 'Тренды',
      children: renderTrendsTab(),
      icon: <RiseOutlined />
    },
  ];

  if (!selectedDepartment) {
    return (
      <ErrorState
        status="info"
        title="Выберите департамент"
        description="Для просмотра расширенной аналитики необходимо выбрать департамент"
        fullHeight
      />
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <BarChartOutlined /> Расширенная аналитика
        </Title>
        <Text type="secondary">
          Детальный анализ исполнения бюджета, категорий и трендов расходов
        </Text>
      </div>

      {/* Global Filters */}
      <Card style={{ marginBottom: 24 }}>
        <Space wrap size="middle">
          <div>
            <Text strong>Год:</Text>
            <br />
            <DatePicker
              picker="year"
              value={dayjs().year(year)}
              onChange={(date) => date && setYear(date.year())}
              style={{ width: 120 }}
            />
          </div>
        </Space>
      </Card>

      {/* Tabs with Analytics */}
      <Tabs
        activeKey={activeTab}
        items={tabs}
        onChange={setActiveTab}
      />
    </div>
  );
};

export default ExtendedAnalyticsPage;
