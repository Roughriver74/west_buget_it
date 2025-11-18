import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tantml:parameter>
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
  message,
} from 'antd';
import {
  BarChartOutlined,
  Calculator OutlinedPlusOutlined,
  ReloadOutlined,
  RiseOutlined,
  FallOutlined,
} from '@ant-design/icons';

import { useDepartment } from '../contexts/DepartmentContext';
import {
  payrollAnalysisAPI,
  payrollScenarioAPI,
  ImpactAnalysis,
  PayrollScenario,
  ScenarioType,
} from '../api/payrollScenarios';

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

export default function PayrollScenariosPage() {
  const { selectedDepartment } = useDepartment();
  const [isModalOpen, setModalOpen] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch impact analysis (2025 vs 2026)
  const { data: impactAnalysis, isLoading: analysisLoading } = useQuery({
    queryKey: ['payroll-impact-analysis', selectedDepartment?.id],
    queryFn: () =>
      payrollAnalysisAPI.getImpactAnalysis({
        base_year: 2025,
        target_year: 2026,
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  });

  // Fetch scenarios
  const { data: scenarios = [], isLoading: scenariosLoading } = useQuery({
    queryKey: ['payroll-scenarios', selectedDepartment?.id],
    queryFn: () =>
      payrollScenarioAPI.list({
        department_id: selectedDepartment?.id,
      }),
    enabled: !!selectedDepartment,
  });

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

  const handleModalOpen = () => {
    setModalOpen(true);
    form.resetFields();
    form.setFieldsValue({
      scenario_type: 'BASE',
      base_year: 2025,
      target_year: 2026,
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

  const formatCurrency = (value?: number | null) =>
    value !== undefined && value !== null
      ? new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', minimumFractionDigits: 0 }).format(
          value
        )
      : '—';

  const formatPercent = (value?: number | null) =>
    value !== undefined && value !== null ? `${value.toFixed(1)}%` : '—';

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
        value !== undefined && value !== null ? (
          <Tag color={value > 0 ? 'volcano' : 'green'} icon={value > 0 ? <RiseOutlined /> : <FallOutlined />}>
            {formatPercent(value)}
          </Tag>
        ) : (
          '—'
        ),
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: PayrollScenario) => (
        <Space>
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
        <h1>Сценарии планирования ФОТ (2025 vs 2026)</h1>
        <p style={{ color: '#666' }}>
          Анализ влияния изменений в страховых взносах на фонд оплаты труда
        </p>
      </div>

      {/* Impact Analysis Card */}
      {impactAnalysis && (
        <Card
          title={
            <Space>
              <BarChartOutlined />
              Влияние изменений 2025 → 2026
            </Space>
          }
          style={{ marginBottom: '24px' }}
          loading={analysisLoading}
        >
          <Alert
            message="Планируемые изменения в страховых взносах"
            description={
              <div>
                <p>
                  В 2026 году ожидается значительное повышение ставок страховых взносов, что приведет к
                  росту нагрузки на работодателя с <strong>30.2%</strong> до <strong>39.7%</strong> (+9.5 п.п.).
                </p>
              </div>
            }
            type="warning"
            showIcon
            style={{ marginBottom: '24px' }}
          />

          <Row gutter={16} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Statistic
                title="Общее влияние"
                value={impactAnalysis.total_impact}
                precision={0}
                suffix="₽"
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Рост в процентах"
                value={impactAnalysis.impact_percent}
                precision={1}
                suffix="%"
                prefix={<RiseOutlined />}
                valueStyle={{ color: '#cf1322' }}
              />
            </Col>
          </Row>

          <Divider />

          <Descriptions title="Изменения ставок" bordered column={2} size="small">
            {Object.entries(impactAnalysis.rate_changes).map(([type, change]) => (
              <Descriptions.Item
                key={type}
                label={type}
                span={2}
              >
                <Space>
                  <Tag>{change.from.toFixed(1)}%</Tag>
                  →
                  <Tag color="volcano">{change.to.toFixed(1)}%</Tag>
                  <Tag color="red">(+{change.change.toFixed(1)} п.п.)</Tag>
                </Space>
              </Descriptions.Item>
            ))}
          </Descriptions>

          {impactAnalysis.recommendations && impactAnalysis.recommendations.length > 0 && (
            <>
              <Divider />
              <h4>Рекомендации по оптимизации:</h4>
              <ul>
                {impactAnalysis.recommendations.map((rec, index) => (
                  <li key={index}>
                    <strong>{rec.description}</strong>
                    <br />
                    <span style={{ color: '#666' }}>Потенциальная экономия: {formatCurrency(Math.abs(rec.impact))}</span>
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
    </div>
  );
}
