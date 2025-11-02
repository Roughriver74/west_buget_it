import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  Button,
  Space,
  Card,
  Tag,
  Input,
  Select,
  message,
  Popconfirm,
  Statistic,
  Row,
  Col,
  Modal,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  UserOutlined,
  DownloadOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { useDepartment } from '../contexts/DepartmentContext';
import { employeeAPI, Employee } from '../api/payroll';
import { formatCurrency } from '../utils/formatters';
import EmployeeFormModal from '../components/employees/EmployeeFormModal';
import EmployeeImportModal from '../components/employees/EmployeeImportModal';

const { Search } = Input;
const { Option } = Select;

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

export default function EmployeesPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { selectedDepartment } = useDepartment();
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState<Employee | undefined>();
  const [importModalVisible, setImportModalVisible] = useState(false);

  // Fetch employees
  const { data: employees = [], isLoading } = useQuery<Employee[]>({
    queryKey: ['employees', selectedDepartment?.id, searchText, statusFilter],
    queryFn: () =>
      employeeAPI.list({
        department_id: selectedDepartment?.id,
        search: searchText || undefined,
        status: statusFilter,
      }),
  });

  // Delete employee mutation
  const deleteMutation = useMutation({
    mutationFn: employeeAPI.delete,
    onSuccess: () => {
      message.success('Сотрудник удален');
      queryClient.invalidateQueries({ queryKey: ['employees'] });
    },
    onError: (error: any) => {
      const errorDetail = error.response?.data?.detail;

      // Check if it's a structured error with related records
      if (errorDetail && typeof errorDetail === 'object' && errorDetail.message) {
        Modal.error({
          title: errorDetail.message || 'Невозможно удалить сотрудника',
          content: (
            <div>
              <p><strong>Причина:</strong> {errorDetail.reason || 'Неизвестная причина'}</p>
              {errorDetail.related_records && errorDetail.related_records.length > 0 && (
                <>
                  <p><strong>Связанные записи:</strong></p>
                  <ul>
                    {errorDetail.related_records.map((record: string, index: number) => (
                      <li key={index}>{record}</li>
                    ))}
                  </ul>
                </>
              )}
              {errorDetail.suggestion && (
                <p style={{ marginTop: 16, fontWeight: 'bold', color: '#1890ff' }}>
                  💡 {errorDetail.suggestion}
                </p>
              )}
            </div>
          ),
          width: 600,
        });
      } else {
        // Fallback for other errors
        message.error(
          typeof errorDetail === 'string'
            ? errorDetail
            : 'Ошибка при удалении сотрудника'
        );
      }
    },
  });

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const handleCreate = () => {
    setSelectedEmployee(undefined);
    setModalVisible(true);
  };

  const handleEdit = (employee: Employee) => {
    setSelectedEmployee(employee);
    setModalVisible(true);
  };

  const handleCloseModal = () => {
    setModalVisible(false);
    setSelectedEmployee(undefined);
  };

  const handleExport = async () => {
    try {
      await employeeAPI.exportToExcel({
        department_id: selectedDepartment?.id,
        status: statusFilter,
      });
      message.success('Экспорт выполнен успешно');
    } catch (error) {
      message.error('Ошибка при экспорте');
    }
  };

  const handleImport = () => {
    setImportModalVisible(true);
  };

  const handleCloseImportModal = () => {
    setImportModalVisible(false);
    queryClient.invalidateQueries({ queryKey: ['employees'] });
  };

  // Calculate statistics
  const activeEmployees = employees.filter((e) => e.status === 'ACTIVE');
  const totalSalary = activeEmployees.reduce((sum, e) => sum + Number(e.base_salary), 0);
  const totalBonuses = activeEmployees.reduce((sum, e) =>
    sum + Number(e.monthly_bonus_base || 0) * 12 + Number(e.quarterly_bonus_base || 0) * 4 + Number(e.annual_bonus_base || 0), 0);
  const totalPayroll = totalSalary * 12 + totalBonuses;
  const avgSalary = activeEmployees.length > 0 ? totalSalary / activeEmployees.length : 0;

  // Helper function to calculate progressive NDFL for annual income
  const calculateProgressiveNDFL = (annualIncome: number, year: number = 2025): number => {
    // Tax brackets for 2025+ (5-tier progressive system)
    const brackets2025 = [
      { limit: 2400000, rate: 0.13 },
      { limit: 5000000, rate: 0.15 },
      { limit: 20000000, rate: 0.18 },
      { limit: 50000000, rate: 0.20 },
      { limit: Infinity, rate: 0.22 },
    ];

    // Tax brackets for 2024 (2-tier system)
    const brackets2024 = [
      { limit: 5000000, rate: 0.13 },
      { limit: Infinity, rate: 0.15 },
    ];

    const brackets = year >= 2025 ? brackets2025 : brackets2024;
    let totalTax = 0;
    let remainingIncome = annualIncome;
    let previousLimit = 0;

    for (const bracket of brackets) {
      const taxableInBracket = Math.min(remainingIncome, bracket.limit - previousLimit);
      if (taxableInBracket <= 0) break;

      totalTax += taxableInBracket * bracket.rate;
      remainingIncome -= taxableInBracket;
      previousLimit = bracket.limit;

      if (remainingIncome <= 0) break;
    }

    return Math.round(totalTax);
  };

  // Tax calculations (расчет налогов по прогрессивной шкале)
  const currentYear = new Date().getFullYear();
  const socialTaxRate = 0.302; // 30.2% страховые взносы (ПФР 22% + ОМС 5.1% + ФСС 2.9% + травматизм 0.2%)

  // Calculate NDFL for each employee using progressive scale
  const totalIncomeTax = activeEmployees.reduce((sum, employee) => {
    const employeeAnnualIncome =
      Number(employee.base_salary) * 12 +
      Number(employee.monthly_bonus_base || 0) * 12 +
      Number(employee.quarterly_bonus_base || 0) * 4 +
      Number(employee.annual_bonus_base || 0);
    const employeeNDFL = calculateProgressiveNDFL(employeeAnnualIncome, currentYear);
    return sum + employeeNDFL;
  }, 0);

  const totalGross = totalPayroll; // Общая начисленная сумма (gross)
  const totalSocialTax = Math.round(totalGross * socialTaxRate); // Страховые взносы
  const totalEmployerCost = totalGross + totalSocialTax; // Полная стоимость для работодателя
  const totalNet = totalGross - totalIncomeTax; // Сумма на руки сотрудникам

  // Calculate effective tax rate for display
  const effectiveNDFLRate = totalGross > 0 ? (totalIncomeTax / totalGross) * 100 : 13;

  const columns = [
    {
      title: 'ФИО',
      dataIndex: 'full_name',
      key: 'full_name',
      sorter: (a: Employee, b: Employee) => a.full_name.localeCompare(b.full_name),
      render: (name: string, record: Employee) => (
        <Button
          type="link"
          onClick={() => navigate(`/employees/${record.id}`)}
          style={{ padding: 0 }}
        >
          {name}
        </Button>
      ),
    },
    {
      title: 'Должность',
      dataIndex: 'position',
      key: 'position',
    },
    {
      title: 'Табельный номер',
      dataIndex: 'employee_number',
      key: 'employee_number',
    },
    {
      title: 'Оклад',
      dataIndex: 'base_salary',
      key: 'base_salary',
      render: (salary: number) => formatCurrency(salary),
      sorter: (a: Employee, b: Employee) => Number(a.base_salary) - Number(b.base_salary),
    },
    {
      title: 'Премии (мес/квар/год)',
      key: 'bonuses',
      render: (_: any, record: Employee) => {
        const monthly = Number(record.monthly_bonus_base || 0);
        const quarterly = Number(record.quarterly_bonus_base || 0);
        const annual = Number(record.annual_bonus_base || 0);
        const total = monthly + quarterly + annual;
        return total > 0 ? `${formatCurrency(monthly)} / ${formatCurrency(quarterly)} / ${formatCurrency(annual)}` : '-';
      },
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={STATUS_COLORS[status]}>{STATUS_LABELS[status]}</Tag>
      ),
      filters: Object.keys(STATUS_LABELS).map((key) => ({
        text: STATUS_LABELS[key],
        value: key,
      })),
      onFilter: (value: any, record: Employee) => record.status === value,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Телефон',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: 'Дата приема',
      dataIndex: 'hire_date',
      key: 'hire_date',
      render: (date: string) => (date ? new Date(date).toLocaleDateString('ru-RU') : '-'),
    },
    {
      title: 'Действия',
      key: 'actions',
      fixed: 'right' as const,
      width: 120,
      render: (_: any, record: Employee) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Вы уверены, что хотите удалить этого сотрудника?"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1>
          <UserOutlined /> Управление сотрудниками
        </h1>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: '16px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего сотрудников"
              value={employees.length}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Активных сотрудников"
              value={activeEmployees.length}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Годовой ФОТ (начислено)"
              value={totalPayroll}
              precision={0}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Средний оклад"
              value={avgSalary}
              precision={0}
              suffix="₽"
            />
          </Card>
        </Col>
      </Row>

      {/* Tax Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title={`НДФЛ (${effectiveNDFLRate.toFixed(2)}%)`}
              value={totalIncomeTax}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Страховые взносы (30.2%)"
              value={totalSocialTax}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#d46b08' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ backgroundColor: '#f6ffed', border: '1px solid #b7eb8f' }}>
            <Statistic
              title="К выплате сотрудникам (Net)"
              value={totalNet}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#52c41a', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card style={{ backgroundColor: '#fff7e6', border: '1px solid #ffd591' }}>
            <Statistic
              title="Полная стоимость для компании"
              value={totalEmployerCost}
              precision={0}
              suffix="₽"
              valueStyle={{ color: '#fa8c16', fontWeight: 'bold' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters and Actions */}
      <Card style={{ marginBottom: '16px' }}>
        <Space style={{ marginBottom: '16px', width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Search
              placeholder="Поиск по ФИО, должности, табельному номеру"
              allowClear
              enterButton={<SearchOutlined />}
              onSearch={setSearchText}
              style={{ width: 400 }}
            />
            <Select
              placeholder="Статус"
              allowClear
              style={{ width: 200 }}
              onChange={setStatusFilter}
            >
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <Option key={value} value={value}>
                  {label}
                </Option>
              ))}
            </Select>
          </Space>
          <Space>
            <Button
              icon={<UploadOutlined />}
              onClick={handleImport}
            >
              Импорт из Excel
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
            >
              Экспорт в Excel
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
            >
              Добавить сотрудника
            </Button>
          </Space>
        </Space>

        {/* Employees Table */}
        <Table
          columns={columns}
          dataSource={employees}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Всего сотрудников: ${total}`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <EmployeeFormModal
        visible={modalVisible}
        employee={selectedEmployee}
        onCancel={handleCloseModal}
      />

      <EmployeeImportModal
        visible={importModalVisible}
        onCancel={handleCloseImportModal}
      />
    </div>
  );
}
