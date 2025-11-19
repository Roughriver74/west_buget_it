import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Divider,
  Form,
  Input,
  InputNumber,
  Modal,
  Row,
  Select,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';

const { Text } = Typography;
import {
  BarChartOutlined,
  CalculatorOutlined,
  EyeOutlined,
  PlusOutlined,
  ReloadOutlined,
  RiseOutlined,
  FallOutlined,
  EditOutlined,
} from '@ant-design/icons';

import { useDepartment } from '../contexts/DepartmentContext';
import {
  payrollAnalysisAPI,
  payrollScenarioAPI,
  ImpactAnalysis,
  PayrollScenario,
  ScenarioType,
} from '../api/payrollScenarios';
import { taxRateAPI, type TaxRateListItem } from '../api/taxRates';
import { useMemo } from 'react';

const SCENARIO_TYPE_LABELS: Record<ScenarioType, string> = {
  BASE: 'Базовый',
  OPTIMISTIC: 'Оптимистичный',
  PESSIMISTIC: 'Пессимистичный',
  CUSTOM: 'Кастомный',
};

const SCENARIO_TYPE_COLORS: Record<ScenarioType, string> = {
  BASE: 'blue',
  OPTIMISTIC: 'green',
  PESSIMISTIC: 'volcano',
  CUSTOM: 'purple',
};

const DATA_SOURCE_LABELS: Record<string, string> = {
  EMPLOYEES: 'Сотрудники',
  PLAN: 'План ФОТ',
  ACTUAL: 'Факт',
};

const DATA_SOURCE_COLORS: Record<string, string> = {
  EMPLOYEES: 'blue',
  PLAN: 'orange',
  ACTUAL: 'green',
};

export default function PayrollScenariosPage() {
  const { selectedDepartment } = useDepartment();
  const navigate = useNavigate();
  const [isModalOpen, setModalOpen] = useState(false);
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [editingScenario, setEditingScenario] = useState<PayrollScenario | null>(null);
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const queryClient = useQueryClient();

  // Year selection state (default to current year vs next year)
  const currentYear = new Date().getFullYear();
  const [baseYear, setBaseYear] = useState(currentYear);
  const [targetYear, setTargetYear] = useState(currentYear + 1);

  // Fetch impact analysis (flexible years)
  const { data: impactAnalysis, isLoading: analysisLoading } = useQuery<ImpactAnalysis>({
    queryKey: ['payroll-impact-analysis', selectedDepartment?.id, baseYear, targetYear],
    queryFn: () =>
      payrollAnalysisAPI.getImpactAnalysis({
        base_year: baseYear,
        target_year: targetYear,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment && !!baseYear && !!targetYear,
  });

  // Fetch scenarios
  const { data: scenarios = [], isLoading: scenariosLoading } = useQuery({
    queryKey: ['payroll-scenarios', selectedDepartment?.id],
    queryFn: async () => {
      const result = await payrollScenarioAPI.list({
        department_id: selectedDepartment?.id,
      });
      console.log('Scenarios API response:', result);
      return result;
    },
    enabled: !!selectedDepartment,
  });

  // Получаем все активные ставки для отображения
  const { data: allTaxRates = [] } = useQuery<TaxRateListItem[]>({
    queryKey: ['tax-rates-all-scenarios', selectedDepartment?.id],
    queryFn: async () => {
      // Запрашиваем ВСЕ активные ставки (без фильтра по department_id)
      const allRates = await taxRateAPI.list({ 
        is_active: true,
        limit: 500,
      });
      return allRates;
    },
    enabled: !!selectedDepartment,
  });

  // Функция для получения ставок для конкретного года и департамента
  const getRatesForScenario = useMemo(() => {
    return (scenario: PayrollScenario) => {
      if (!scenario.target_year || !allTaxRates.length) return [];
      
      const targetDate = new Date(scenario.target_year, 0, 1);
      const yearEndDate = new Date(scenario.target_year, 11, 31);
      const insuranceTypes = ['PENSION_FUND', 'MEDICAL_INSURANCE', 'SOCIAL_INSURANCE', 'INJURY_INSURANCE'];
      
      const ratesByType: Record<string, TaxRateListItem[]> = {};
      
      allTaxRates
        .filter(rate => insuranceTypes.includes(rate.tax_type))
        .forEach(rate => {
          const effectiveFrom = new Date(rate.effective_from);
          const effectiveTo = rate.effective_to ? new Date(rate.effective_to) : null;
          
          const isCurrent = effectiveFrom <= targetDate && (!effectiveTo || effectiveTo >= targetDate);
          const isFuture = effectiveFrom > targetDate && effectiveFrom <= yearEndDate;
          
          if (isCurrent || isFuture) {
            const isForDepartment = rate.department_id === scenario.department_id;
            const isGlobal = rate.department_id === null || rate.department_id === undefined;
            
            if (isForDepartment || isGlobal) {
              if (!ratesByType[rate.tax_type]) {
                ratesByType[rate.tax_type] = [];
              }
              ratesByType[rate.tax_type].push(rate);
            }
          }
        });
      
      const result: TaxRateListItem[] = [];
      insuranceTypes.forEach(type => {
        const rates = ratesByType[type] || [];
        if (rates.length > 0) {
          const deptRates = rates.filter(r => r.department_id === scenario.department_id);
          const globalRates = rates.filter(r => r.department_id === null || r.department_id === undefined);
          const priorityRates = deptRates.length > 0 ? deptRates : globalRates;
          
          // Сортируем: ПРИОРИТЕТ будущим ставкам, которые начнут действовать в целевом году
          priorityRates.sort((a, b) => {
            const aDate = new Date(a.effective_from);
            const bDate = new Date(b.effective_from);
            const aIsCurrent = aDate <= targetDate;
            const bIsCurrent = bDate <= targetDate;
            const aIsFuture = aDate > targetDate && aDate <= yearEndDate;
            const bIsFuture = bDate > targetDate && bDate <= yearEndDate;
            
            // Будущие ставки (в пределах года) имеют приоритет над текущими
            if (aIsFuture && !bIsFuture) return -1;
            if (!aIsFuture && bIsFuture) return 1;
            
            // Если обе будущие - берем самую раннюю (которая начнет действовать первой)
            if (aIsFuture && bIsFuture) return aDate.getTime() - bDate.getTime();
            
            // Если обе текущие - берем самую позднюю (самую актуальную)
            if (aIsCurrent && bIsCurrent) return bDate.getTime() - aDate.getTime();
            
            return 0;
          });
          
          if (priorityRates.length > 0) {
            result.push(priorityRates[0]);
          }
        }
      });
      
      return result;
    };
  }, [allTaxRates]);

  const createMutation = useMutation({
    mutationFn: (values: any) => payrollScenarioAPI.create(values),
    onSuccess: () => {
      message.success('Сценарий создан');
      queryClient.invalidateQueries({ queryKey: ['payroll-scenarios'] });
      handleModalClose();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось создать сценарий');
    },
  });

  const calculateMutation = useMutation({
    mutationFn: (id: number) => payrollScenarioAPI.calculate(id),
    onSuccess: () => {
      message.success('Сценарий рассчитан');
      queryClient.invalidateQueries({ queryKey: ['payroll-scenarios'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось рассчитать');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: any }) => payrollScenarioAPI.update(id, values),
    onSuccess: async (_, variables) => {
      message.success('Параметры сценария обновлены');
      queryClient.invalidateQueries({ queryKey: ['payroll-scenarios'] });
      queryClient.invalidateQueries({ queryKey: ['payroll-scenario', variables.id] });
      setEditModalOpen(false);
      setEditingScenario(null);
      
      // Автоматически пересчитываем сценарий после обновления параметров
      try {
        await payrollScenarioAPI.calculate(variables.id);
        message.success('Сценарий автоматически пересчитан');
        queryClient.invalidateQueries({ queryKey: ['payroll-scenarios'] });
        queryClient.invalidateQueries({ queryKey: ['payroll-scenario', variables.id] });
      } catch (error: any) {
        message.warning('Параметры обновлены, но не удалось автоматически пересчитать сценарий. Пересчитайте вручную на странице детального просмотра.');
      }
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось обновить параметры');
    },
  });

  const handleModalOpen = () => {
    setModalOpen(true);
    form.resetFields();
    form.setFieldsValue({
      scenario_type: 'BASE',
      data_source: 'EMPLOYEES',
      base_year: baseYear,
      target_year: targetYear,
      headcount_change_percent: 0,
      salary_change_percent: 0,
    });
  };

  const handleModalClose = () => {
    setModalOpen(false);
    form.resetFields();
  };

  const handleSubmit = (values: any) => {
    createMutation.mutate({
      ...values,
      department_id: selectedDepartment?.id,
    });
  };

  const handleEditOpen = (scenario: PayrollScenario) => {
    setEditingScenario(scenario);
    editForm.setFieldsValue({
      headcount_change_percent: scenario.headcount_change_percent || 0,
      salary_change_percent: scenario.salary_change_percent || 0,
    });
    setEditModalOpen(true);
  };

  const handleEditSubmit = (values: any) => {
    if (editingScenario) {
      updateMutation.mutate({ id: editingScenario.id, values });
    }
  };

  const handleEditClose = () => {
    setEditModalOpen(false);
    setEditingScenario(null);
    editForm.resetFields();
  };

  const formatCurrency = (value?: number | null) => {
    // Debug logging
    console.log('formatCurrency called with:', { value, type: typeof value, isNumber: typeof value === 'number' });

    return typeof value === 'number'
      ? new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(
          value
        )
      : '—';
  };

  const formatPercent = (value?: number | null) =>
    typeof value === 'number' ? `${value.toFixed(1)}%` : '—';

  const formatPercentValue = (value?: number | null) =>
    typeof value === 'number' ? value.toFixed(1) : '0.0';

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Тип',
      dataIndex: 'scenario_type',
      key: 'scenario_type',
      render: (type: ScenarioType) => (
        <Tag color={SCENARIO_TYPE_COLORS[type]}>{SCENARIO_TYPE_LABELS[type]}</Tag>
      ),
    },
    {
      title: 'Данные',
      dataIndex: 'data_source',
      key: 'data_source',
      render: (source?: string) => (
        <Tag color={DATA_SOURCE_COLORS[source || 'EMPLOYEES']}>
          {DATA_SOURCE_LABELS[source || 'EMPLOYEES']}
        </Tag>
      ),
    },
    {
      title: 'Год',
      dataIndex: 'target_year',
      key: 'target_year',
    },
    {
      title: 'Численность',
      dataIndex: 'total_headcount',
      key: 'total_headcount',
      render: (value?: number) => value || '—',
    },
    {
      title: 'Общий ФОТ',
      dataIndex: 'total_payroll_cost',
      key: 'total_payroll_cost',
      render: formatCurrency,
    },
    {
      title: 'Изменение',
      dataIndex: 'cost_difference_percent',
      key: 'cost_difference_percent',
      render: (value?: number) =>
        typeof value === 'number' ? (
          <Tag color={value > 0 ? 'volcano' : 'green'} icon={value > 0 ? <RiseOutlined /> : <FallOutlined />}>
            {formatPercent(value)}
          </Tag>
        ) : (
          '—'
        ),
    },
    {
      title: 'Параметры',
      key: 'parameters',
      width: 200,
      render: (_: any, record: PayrollScenario) => (
        <Space direction="vertical" size={4}>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Штат: <Text strong style={{ color: (record.headcount_change_percent || 0) >= 0 ? '#52c41a' : '#f5222d' }}>
              {(record.headcount_change_percent || 0) >= 0 ? '+' : ''}
              {typeof record.headcount_change_percent === 'number' ? record.headcount_change_percent.toFixed(1) : '0.0'}%
            </Text>
          </Text>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Зарплаты: <Text strong style={{ color: (record.salary_change_percent || 0) >= 0 ? '#52c41a' : '#f5222d' }}>
              {(record.salary_change_percent || 0) >= 0 ? '+' : ''}
              {typeof record.salary_change_percent === 'number' ? record.salary_change_percent.toFixed(1) : '0.0'}%
            </Text>
          </Text>
        </Space>
      ),
    },
    {
      title: 'Ставки страховых взносов',
      key: 'insurance_rates',
      width: 250,
      render: (_: any, record: PayrollScenario) => {
        const rates = getRatesForScenario(record);
        if (rates.length === 0) {
          return (
            <Text type="secondary" style={{ fontSize: 12 }}>
              Ставки не найдены
            </Text>
          );
        }
        
        const rateLabels: Record<string, string> = {
          PENSION_FUND: 'ПФР',
          MEDICAL_INSURANCE: 'ФОМС',
          SOCIAL_INSURANCE: 'ФСС',
          INJURY_INSURANCE: 'Травматизм',
        };
        
        return (
          <Space direction="vertical" size={2} style={{ fontSize: 11 }}>
            {rates.map(rate => (
              <Text key={rate.id} type="secondary" style={{ fontSize: 11 }}>
                {rateLabels[rate.tax_type] || rate.tax_type}: <Text strong>{(rate.rate * 100).toFixed(1)}%</Text>
              </Text>
            ))}
          </Space>
        );
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 250,
      render: (_: any, record: PayrollScenario) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => navigate(`/payroll/scenarios/${record.id}`)}
          >
            Детали
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditOpen(record)}
          >
            Редактировать
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CalculatorOutlined />}
            onClick={() => calculateMutation.mutate(record.id)}
            loading={calculateMutation.isPending}
          >
            Рассчитать
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1>Сценарии планирования ФОТ</h1>
        <p style={{ color: '#666' }}>
          Анализ влияния изменений в страховых взносах на фонд оплаты труда
        </p>
      </div>

      {/* Year Selection */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col>
            <span style={{ fontWeight: 500 }}>Сравнить годы:</span>
          </Col>
          <Col>
            <Space>
              <span>Базовый год:</span>
              <Select
                value={baseYear}
                onChange={setBaseYear}
                style={{ width: 100 }}
              >
                {Array.from({ length: 11 }, (_, i) => currentYear - 5 + i).map(year => (
                  <Select.Option key={year} value={year}>{year}</Select.Option>
                ))}
              </Select>
            </Space>
          </Col>
          <Col>
            <span style={{ fontSize: '20px' }}>→</span>
          </Col>
          <Col>
            <Space>
              <span>Целевой год:</span>
              <Select
                value={targetYear}
                onChange={setTargetYear}
                style={{ width: 100 }}
              >
                {Array.from({ length: 11 }, (_, i) => currentYear - 5 + i).map(year => (
                  <Select.Option key={year} value={year}>{year}</Select.Option>
                ))}
              </Select>
            </Space>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={() => queryClient.invalidateQueries({ queryKey: ['payroll-impact-analysis'] })}
            >
              Пересчитать
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Impact Analysis Card */}
      {impactAnalysis && (
        <Card
          title={
            <Space>
              <BarChartOutlined />
              Влияние изменений {baseYear} → {targetYear}
            </Space>
          }
          style={{ marginBottom: '24px' }}
          loading={analysisLoading}
        >
          <Alert
            message={`Изменения в страховых взносах (${baseYear} → ${targetYear})`}
            description={
              <div>
                <p>
                  {typeof impactAnalysis.total_impact === 'number' && impactAnalysis.total_impact > 0 ? (
                    <>
                      Ожидается <strong>рост</strong> затрат на ФОТ на{' '}
                      <strong>{formatCurrency(impactAnalysis.total_impact)}</strong>{' '}
                      ({formatPercent(impactAnalysis.impact_percent)}) из-за изменений ставок страховых взносов.
                    </>
                  ) : typeof impactAnalysis.total_impact === 'number' && impactAnalysis.total_impact < 0 ? (
                    <>
                      Ожидается <strong>снижение</strong> затрат на ФОТ на{' '}
                      <strong>{formatCurrency(typeof impactAnalysis.total_impact === 'number' ? Math.abs(impactAnalysis.total_impact) : 0)}</strong>{' '}
                      ({formatPercent(typeof impactAnalysis.impact_percent === 'number' ? Math.abs(impactAnalysis.impact_percent) : 0)}) из-за изменений ставок страховых взносов.
                    </>
                  ) : (
                    'Изменения в ставках страховых взносов не ожидаются.'
                  )}
                </p>
              </div>
            }
            type={typeof impactAnalysis.total_impact === 'number' && impactAnalysis.total_impact > 0 ? 'warning' : typeof impactAnalysis.total_impact === 'number' && impactAnalysis.total_impact < 0 ? 'success' : 'info'}
            showIcon
            style={{ marginBottom: '24px' }}
          />

          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Statistic
                title="Общее влияние"
                value={typeof impactAnalysis.total_impact === 'number' ? impactAnalysis.total_impact : 0}
                precision={0}
                suffix="₽"
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Рост в процентах"
                value={typeof impactAnalysis.impact_percent === 'number' ? impactAnalysis.impact_percent : 0}
                precision={1}
                suffix="%"
                prefix={<RiseOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>

          <Divider />

          {impactAnalysis.rate_changes && Object.keys(impactAnalysis.rate_changes).length > 0 && (
            <Descriptions title="Изменения ставок" bordered column={2} size="small">
              {Object.entries(impactAnalysis.rate_changes).map(([type, change]) => {
                // Safe number conversion with fallback
                const fromValue = typeof change?.from === 'number' ? change.from : 0;
                const toValue = typeof change?.to === 'number' ? change.to : 0;
                const changeValue = typeof change?.change === 'number' ? change.change : 0;

                return (
                  <Descriptions.Item
                    key={type}
                    label={type}
                    span={2}
                  >
                    <Space>
                      <Tag>{formatPercentValue(fromValue)}%</Tag>
                      →
                      <Tag color="volcano">{formatPercentValue(toValue)}%</Tag>
                      <Tag color="red">(+{formatPercentValue(changeValue)} п.п.)</Tag>
                    </Space>
                  </Descriptions.Item>
                );
              })}
            </Descriptions>
          )}

          {impactAnalysis.recommendations && impactAnalysis.recommendations.length > 0 && (
            <>
              <Divider />
              <h4>Рекомендации по оптимизации:</h4>
              <ul>
                {impactAnalysis.recommendations.map((rec, index) => (
                  <li key={index}>
                    <strong>{rec.description}</strong>
                    <br />
                    <span style={{ color: '#666' }}>
                      Потенциальная экономия: {formatCurrency(typeof rec.impact === 'number' ? Math.abs(rec.impact) : 0)}
                    </span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </Card>
      )}

      {/* Scenarios Table */}
      <Card
        title="Сценарии планирования"
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleModalOpen}
            >
              Создать сценарий
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => queryClient.invalidateQueries({ queryKey: ['payroll-scenarios'] })}>
              Обновить
            </Button>
          </Space>
        }
        style={{ marginBottom: '24px' }}
      >
        <Table
          columns={columns}
          dataSource={scenarios}
          rowKey="id"
          loading={scenariosLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Create Scenario Modal */}
      <Modal
        title="Создать сценарий"
        open={isModalOpen}
        onCancel={handleModalClose}
        onOk={() => form.submit()}
        confirmLoading={createMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input placeholder="Например: Сокращение 10%" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <Input.TextArea rows={3} placeholder="Описание сценария" />
          </Form.Item>

          <Form.Item
            name="scenario_type"
            label="Тип сценария"
            rules={[{ required: true }]}
          >
            <Select>
              <Select.Option value="BASE">Базовый (без изменений)</Select.Option>
              <Select.Option value="OPTIMISTIC">Оптимистичный (рост)</Select.Option>
              <Select.Option value="PESSIMISTIC">Пессимистичный (сокращение)</Select.Option>
              <Select.Option value="CUSTOM">Кастомный</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="data_source"
            label="Источник данных"
            rules={[{ required: true }]}
            tooltip="Выберите источник данных для расчета: текущие сотрудники, плановые или фактические выплаты"
          >
            <Select>
              <Select.Option value="EMPLOYEES">Текущие сотрудники (из базы)</Select.Option>
              <Select.Option value="PLAN">Плановые данные (из планов ФОТ)</Select.Option>
              <Select.Option value="ACTUAL">Фактические выплаты (из истории)</Select.Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="base_year"
                label="Базовый год"
                rules={[{ required: true }]}
              >
                <InputNumber min={2020} max={2030} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="target_year"
                label="Целевой год"
                rules={[{ required: true }]}
              >
                <InputNumber min={2020} max={2030} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="headcount_change_percent"
                label="Изменение штата (%)"
                tooltip="Положительное число - рост, отрицательное - сокращение"
              >
                <InputNumber min={-100} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="salary_change_percent"
                label="Изменение зарплат (%)"
                tooltip="Положительное число - рост, отрицательное - снижение"
              >
                <InputNumber min={-100} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Edit Scenario Modal */}
      <Modal
        title={`Редактировать параметры: ${editingScenario?.name || ''}`}
        open={isEditModalOpen}
        onCancel={handleEditClose}
        onOk={() => editForm.submit()}
        confirmLoading={updateMutation.isPending}
        width={600}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Alert
            message="Изменение параметров сценария"
            description="После изменения параметров необходимо пересчитать сценарий для обновления результатов."
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          <Form.Item
            name="headcount_change_percent"
            label="Изменение штата (%)"
            tooltip="Положительное число - рост штата, отрицательное - сокращение"
            rules={[
              { required: true, message: 'Введите изменение штата' },
              { type: 'number', min: -100, max: 100, message: 'Значение должно быть от -100 до 100' },
            ]}
          >
            <InputNumber
              min={-100}
              max={100}
              step={0.1}
              style={{ width: '100%' }}
              formatter={(value) => `${value}%`}
              parser={(value) => Number(value?.replace('%', '') || 0) as any}
            />
          </Form.Item>

          <Form.Item
            name="salary_change_percent"
            label="Изменение зарплат (%)"
            tooltip="Положительное число - рост зарплат, отрицательное - снижение"
            rules={[
              { required: true, message: 'Введите изменение зарплат' },
              { type: 'number', min: -100, max: 100, message: 'Значение должно быть от -100 до 100' },
            ]}
          >
            <InputNumber
              min={-100}
              max={100}
              step={0.1}
              style={{ width: '100%' }}
              formatter={(value) => `${value}%`}
              parser={(value) => Number(value?.replace('%', '') || 0) as any}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
