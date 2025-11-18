import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Spin,
  Table,
  Row,
  Col,
  Statistic,
  Tabs,
  message,
  Popconfirm,
} from 'antd';
import {
  ArrowLeftOutlined,
  EditOutlined,
  UserOutlined,
  DollarOutlined,
  CalendarOutlined,
  HistoryOutlined,
  DeleteOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { useMemo, useState } from 'react';
import { employeeAPI, payrollPlanAPI, payrollActualAPI, employeeTaxAPI } from '../api/payroll';
import { formatCurrency } from '../utils/formatters';
import EmployeeFormModal from '../components/employees/EmployeeFormModal';
import PayrollPlanFormModal from '../components/payroll/PayrollPlanFormModal';

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'green',
  ON_VACATION: 'blue',
  ON_LEAVE: 'orange',
  FIRED: 'red',
};

const STATUS_LABELS: Record<string, string> = {
  ACTIVE: 'Активен',
  ON_VACATION: 'В отпуске',
  ON_LEAVE: 'В отпуске/Больничный',
  FIRED: 'Уволен',
};

const MONTHS = [
  'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
  'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
];

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [modalVisible, setModalVisible] = useState(false);
  const [planModalVisible, setPlanModalVisible] = useState(false);
  const [editingPlan, setEditingPlan] = useState<any>(null);

  // Fetch employee details with salary history
  const { data: employee, isLoading } = useQuery({
    queryKey: ['employee', id],
    queryFn: () => employeeAPI.get(Number(id)),
  });

  // Fetch payroll plans
  const { data: plans = [] } = useQuery({
    queryKey: ['payroll-plans', id],
    queryFn: () => payrollPlanAPI.list({ employee_id: Number(id) }),
  });

  // Fetch payroll actuals
  const { data: actuals = [] } = useQuery({
    queryKey: ['payroll-actuals', id],
    queryFn: () => payrollActualAPI.list({ employee_id: Number(id) }),
  });

  // Fetch tax calculation
  const { data: taxCalculation } = useQuery({
    queryKey: ['employee-tax-calculation', id],
    queryFn: () => employeeTaxAPI.getTaxCalculation(Number(id)),
    enabled: !!id && !!employee,
  });

  // Delete plan mutation
  const deletePlanMutation = useMutation({
    mutationFn: (planId: number) => payrollPlanAPI.delete(planId),
    onSuccess: () => {
      message.success('План удален');
      queryClient.invalidateQueries({ queryKey: ['payroll-plans', id] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при удалении плана');
    },
  });

  const handleEditPlan = (plan: any) => {
    setEditingPlan(plan);
    setPlanModalVisible(true);
  };

  const handleAddPlan = () => {
    setEditingPlan(null);
    setPlanModalVisible(true);
  };

  const handleDeletePlan = (planId: number) => {
    deletePlanMutation.mutate(planId);
  };

  // Calculate statistics (hooks must run every render)
  const sortedPlans = useMemo(() => {
    return [...plans].sort((a, b) => {
      if (a.year === b.year) {
        return a.month - b.month;
      }
      return a.year - b.year;
    });
  }, [plans]);

  const sortedActuals = useMemo(() => {
    return [...actuals].sort((a, b) => {
      if (a.year === b.year) {
        return a.month - b.month;
      }
      return a.year - b.year;
    });
  }, [actuals]);

  const sortedSalaryHistory = useMemo(() => {
    const history = employee?.salary_history ?? [];
    return [...history].sort(
      (a, b) =>
        new Date(a.effective_date).getTime() - new Date(b.effective_date).getTime()
    );
  }, [employee?.salary_history]);

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!employee) {
    return (
      <div style={{ textAlign: 'center', padding: '100px' }}>
        <h2>Сотрудник не найден</h2>
        <Button onClick={() => navigate('/employees')}>Вернуться к списку</Button>
      </div>
    );
  }

  const totalPlanned = sortedPlans.reduce((sum, p) => sum + Number(p.total_planned), 0);
  const totalPaid = sortedActuals.reduce((sum, a) => sum + Number(a.total_paid), 0);
  // Salary history columns
  const salaryHistoryColumns = [
    {
      title: 'Дата',
      dataIndex: 'effective_date',
      key: 'effective_date',
      render: (date: string) => new Date(date).toLocaleDateString('ru-RU'),
    },
    {
      title: 'Старый оклад',
      dataIndex: 'old_salary',
      key: 'old_salary',
      render: (salary: number) => salary ? formatCurrency(salary) : '-',
    },
    {
      title: 'Новый оклад',
      dataIndex: 'new_salary',
      key: 'new_salary',
      render: (salary: number) => formatCurrency(salary),
    },
    {
      title: 'Изменение',
      key: 'change',
      render: (_: any, record: any) => {
        if (!record.old_salary) return '-';
        const change = Number(record.new_salary) - Number(record.old_salary);
        const percent = (change / Number(record.old_salary)) * 100;
        const color = change > 0 ? 'green' : change < 0 ? 'red' : undefined;
        return (
          <span style={{ color }}>
            {change > 0 ? '+' : ''}{formatCurrency(change)} ({percent > 0 ? '+' : ''}{percent.toFixed(1)}%)
          </span>
        );
      },
    },
    {
      title: 'Причина',
      dataIndex: 'reason',
      key: 'reason',
    },
  ];

  // Payroll plans columns
  const plansColumns = [
    {
      title: 'Период',
      key: 'period',
      render: (_: any, record: any) => `${MONTHS[record.month - 1]} ${record.year}`,
    },
    {
      title: 'Оклад',
      dataIndex: 'base_salary',
      key: 'base_salary',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Премия (мес)',
      dataIndex: 'monthly_bonus',
      key: 'monthly_bonus',
      render: (value: number) => formatCurrency(value || 0),
    },
    {
      title: 'Премия (квар)',
      dataIndex: 'quarterly_bonus',
      key: 'quarterly_bonus',
      render: (value: number) => formatCurrency(value || 0),
    },
    {
      title: 'Премия (год)',
      dataIndex: 'annual_bonus',
      key: 'annual_bonus',
      render: (value: number) => formatCurrency(value || 0),
    },
    {
      title: 'Прочие',
      dataIndex: 'other_payments',
      key: 'other_payments',
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Итого',
      dataIndex: 'total_planned',
      key: 'total_planned',
      render: (value: number) => <strong>{formatCurrency(value)}</strong>,
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 120,
      render: (_: any, record: any) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditPlan(record)}
          >
            Изменить
          </Button>
          <Popconfirm
            title="Удалить план?"
            description="Вы уверены, что хотите удалить этот план?"
            onConfirm={() => handleDeletePlan(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Payroll actuals columns
  const actualsColumns = [
    {
      title: 'Период',
      key: 'period',
      render: (_: any, record: any) => `${MONTHS[record.month - 1]} ${record.year}`,
    },
    {
      title: 'Дата выплаты',
      dataIndex: 'payment_date',
      key: 'payment_date',
      render: (date: string) => date ? new Date(date).toLocaleDateString('ru-RU') : '-',
    },
    {
      title: 'Начислено (Gross)',
      dataIndex: 'total_paid',
      key: 'total_paid',
      render: (value: number) => <strong>{formatCurrency(value)}</strong>,
    },
    {
      title: 'НДФЛ',
      key: 'income_tax',
      render: (_: any, record: any) => (
        <span>
          {formatCurrency(record.income_tax_amount || 0)}
          {' '}
          <span style={{ fontSize: '12px', color: '#666' }}>
            ({((record.income_tax_rate || 0) * 100).toFixed(1)}%)
          </span>
        </span>
      ),
    },
    {
      title: 'На руки (Net)',
      key: 'net_amount',
      render: (_: any, record: any) => {
        const netAmount = Number(record.total_paid) - Number(record.income_tax_amount || 0);
        return <strong style={{ color: '#52c41a' }}>{formatCurrency(netAmount)}</strong>;
      },
    },
    {
      title: 'Страховые взносы',
      dataIndex: 'social_tax_amount',
      key: 'social_tax_amount',
      render: (value: number) => <span style={{ color: '#fa8c16' }}>{formatCurrency(value || 0)}</span>,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/employees')}>
            Назад
          </Button>
          <h1 style={{ margin: 0 }}>
            <UserOutlined /> {employee.full_name}
          </h1>
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => setModalVisible(true)}
          >
            Редактировать
          </Button>
        </Space>
      </div>

      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Текущий оклад"
              value={employee.base_salary}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Годовые премии (база)"
              value={Number(employee.monthly_bonus_base || 0) * 12 + Number(employee.quarterly_bonus_base || 0) * 4 + Number(employee.annual_bonus_base || 0)}
              precision={2}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего запланировано"
              value={totalPlanned}
              precision={2}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего выплачено"
              value={totalPaid}
              precision={2}
              suffix="₽"
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Main info */}
      <Card title="Основная информация" style={{ marginBottom: '16px' }}>
        <Descriptions bordered column={2}>
          <Descriptions.Item label="ФИО">{employee.full_name}</Descriptions.Item>
          <Descriptions.Item label="Должность">{employee.position}</Descriptions.Item>
          <Descriptions.Item label="Табельный номер">
            {employee.employee_number || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="Статус">
            <Tag color={STATUS_COLORS[employee.status]}>
              {STATUS_LABELS[employee.status]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Дата приема">
            {employee.hire_date
              ? new Date(employee.hire_date).toLocaleDateString('ru-RU')
              : '-'}
          </Descriptions.Item>
          {employee.fire_date && (
            <Descriptions.Item label="Дата увольнения">
              {new Date(employee.fire_date).toLocaleDateString('ru-RU')}
            </Descriptions.Item>
          )}
          <Descriptions.Item label="Email">{employee.email || '-'}</Descriptions.Item>
          <Descriptions.Item label="Телефон">{employee.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="Оклад">
            <strong>{formatCurrency(employee.base_salary)}</strong>
          </Descriptions.Item>
          <Descriptions.Item label="Премия месячная">
            {formatCurrency(employee.monthly_bonus_base || 0)}
          </Descriptions.Item>
          <Descriptions.Item label="Премия квартальная">
            {formatCurrency(employee.quarterly_bonus_base || 0)}
          </Descriptions.Item>
          <Descriptions.Item label="Премия годовая">
            {formatCurrency(employee.annual_bonus_base || 0)}
          </Descriptions.Item>
          {employee.notes && (
            <Descriptions.Item label="Примечания" span={2}>
              {employee.notes}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Card>

      {/* Tax Information */}
      {taxCalculation && (
        <Card title="Налоги и страховые взносы" style={{ marginBottom: '16px' }}>
          <Row gutter={16}>
            <Col span={12}>
              <Card type="inner" title="НДФЛ" style={{ marginBottom: '16px' }}>
                <Statistic
                  title="Ставка"
                  value={taxCalculation.income_tax_rate_percent}
                  precision={1}
                  suffix="%"
                />
                <Statistic
                  title="Сумма"
                  value={taxCalculation.income_tax}
                  precision={2}
                  suffix="₽"
                  style={{ marginTop: '16px' }}
                />
              </Card>

              <Card type="inner" title="Зарплата">
                <Descriptions column={1}>
                  <Descriptions.Item label="Gross (начислено)">
                    <strong>{formatCurrency(taxCalculation.gross_salary)}</strong>
                  </Descriptions.Item>
                  <Descriptions.Item label="Net (на руки)">
                    <strong style={{ color: '#52c41a' }}>
                      {formatCurrency(taxCalculation.net_salary)}
                    </strong>
                  </Descriptions.Item>
                  <Descriptions.Item label="Стоимость для компании">
                    <strong style={{ color: '#fa8c16' }}>
                      {formatCurrency(taxCalculation.employer_total_cost)}
                    </strong>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>

            <Col span={12}>
              <Card type="inner" title="Страховые взносы" style={{ marginBottom: '16px' }}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="ПФР (пенсионный фонд)">
                    {formatCurrency(taxCalculation.social_contributions.pension_fund)}
                    {' '}
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      ({taxCalculation.social_contributions.pension_fund_rate_percent.toFixed(1)}%)
                    </span>
                  </Descriptions.Item>
                  <Descriptions.Item label="ФОМС (медицинское страхование)">
                    {formatCurrency(taxCalculation.social_contributions.medical_insurance)}
                    {' '}
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      ({taxCalculation.social_contributions.medical_insurance_rate_percent.toFixed(1)}%)
                    </span>
                  </Descriptions.Item>
                  <Descriptions.Item label="ФСС (социальное страхование)">
                    {formatCurrency(taxCalculation.social_contributions.social_insurance)}
                    {' '}
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      ({taxCalculation.social_contributions.social_insurance_rate_percent.toFixed(1)}%)
                    </span>
                  </Descriptions.Item>
                  <Descriptions.Item label={<strong>Итого взносов</strong>}>
                    <strong style={{ color: '#fa8c16' }}>
                      {formatCurrency(taxCalculation.social_contributions.total)}
                    </strong>
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>
        </Card>
      )}

      {/* Tabs with different data */}
      <Card>
        <Tabs
          defaultActiveKey="plans"
          items={[
            {
              key: 'plans',
              label: (
                <span>
                  <CalendarOutlined /> Планы ({plans.length})
                </span>
              ),
              children: (
                <>
                  <div style={{ marginBottom: 16 }}>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={handleAddPlan}
                    >
                      Добавить план
                    </Button>
                  </div>
                  <Table
                    columns={plansColumns}
                    dataSource={sortedPlans}
                    rowKey="id"
                    pagination={{ pageSize: 12 }}
                  />
                </>
              ),
            },
            {
              key: 'actuals',
              label: (
                <span>
                  <DollarOutlined /> Выплаты ({actuals.length})
                </span>
              ),
              children: (
                <Table
                  columns={actualsColumns}
                  dataSource={sortedActuals}
                  rowKey="id"
                  pagination={{ pageSize: 12 }}
                />
              ),
            },
            {
              key: 'history',
              label: (
                <span>
                  <HistoryOutlined /> История окладов ({employee.salary_history?.length || 0})
                </span>
              ),
              children: sortedSalaryHistory.length > 0 ? (
                <Table
                  columns={salaryHistoryColumns}
                  dataSource={sortedSalaryHistory}
                  rowKey="id"
                  pagination={false}
                />
              ) : (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                  <p>История изменений оклада пуста</p>
                </div>
              ),
            },
          ]}
        />
      </Card>

      <EmployeeFormModal
        visible={modalVisible}
        employee={employee}
        onCancel={() => setModalVisible(false)}
      />

      <PayrollPlanFormModal
        visible={planModalVisible}
        planId={editingPlan?.id}
        defaultValues={{
          employee_id: Number(id),
        }}
        onCancel={() => {
          setPlanModalVisible(false);
          setEditingPlan(null);
        }}
      />
    </div>
  );
}
