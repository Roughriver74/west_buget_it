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
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  UserOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { useDepartment } from '../contexts/DepartmentContext';
import { employeeAPI, Employee } from '../api/payroll';
import { formatCurrency } from '../utils/formatters';
import EmployeeFormModal from '../components/employees/EmployeeFormModal';

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
    onError: () => {
      message.error('Ошибка при удалении сотрудника');
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

  // Calculate statistics
  const activeEmployees = employees.filter((e) => e.status === 'ACTIVE');
  const totalSalary = activeEmployees.reduce((sum, e) => sum + Number(e.base_salary), 0);
  const avgSalary = activeEmployees.length > 0 ? totalSalary / activeEmployees.length : 0;

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
      <Row gutter={16} style={{ marginBottom: '24px' }}>
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
              title="Общий ФОТ"
              value={totalSalary}
              precision={2}
              suffix="₽"
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Средний оклад"
              value={avgSalary}
              precision={2}
              suffix="₽"
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
    </div>
  );
}
