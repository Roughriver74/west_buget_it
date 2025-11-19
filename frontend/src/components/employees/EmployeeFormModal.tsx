import { useEffect, useState } from 'react';
import { Modal, Form, Input, InputNumber, Select, DatePicker, message, Radio, Space, Alert } from 'antd';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { employeeAPI, Employee, EmployeeCreate, EmployeeUpdate } from '../../api/payroll';
import { useDepartment } from '../../contexts/DepartmentContext';
import { useAuth } from '../../contexts/AuthContext';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

interface EmployeeFormModalProps {
  visible: boolean;
  employee?: Employee;
  onCancel: () => void;
}

const STATUS_OPTIONS = [
  { value: 'ACTIVE', label: 'Активен' },
  { value: 'ON_VACATION', label: 'В отпуске' },
  { value: 'ON_LEAVE', label: 'В отпуске/Больничный' },
  { value: 'FIRED', label: 'Уволен' },
];

export default function EmployeeFormModal({ visible, employee, onCancel }: EmployeeFormModalProps) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const { departments, selectedDepartment } = useDepartment();
  const { user } = useAuth();
  const isEdit = !!employee;

  // Check if user can select department (ADMIN/MANAGER)
  const canSelectDepartment = user?.role === 'ADMIN' || user?.role === 'MANAGER';

  // State for salary calculations (Task 1.4: Брутто ↔ Нетто)
  const [calculatedSalaries, setCalculatedSalaries] = useState<{
    gross: number | null;
    net: number | null;
    ndfl: number | null;
  }>({ gross: null, net: null, ndfl: null });

  // Calculate gross/net salaries based on type
  const calculateSalaries = (baseSalary: number | undefined, salaryType: string, ndflRate: number) => {
    if (!baseSalary || baseSalary <= 0) {
      setCalculatedSalaries({ gross: null, net: null, ndfl: null });
      return;
    }

    const rate = ndflRate || 0.13; // Default NDFL rate 13%

    if (salaryType === 'GROSS') {
      // User entered gross, calculate net
      const net = baseSalary * (1 - rate);
      const ndfl = baseSalary - net;
      setCalculatedSalaries({
        gross: baseSalary,
        net: parseFloat(net.toFixed(2)),
        ndfl: parseFloat(ndfl.toFixed(2))
      });
    } else {
      // User entered net, calculate gross
      const gross = baseSalary / (1 - rate);
      const ndfl = gross - baseSalary;
      setCalculatedSalaries({
        gross: parseFloat(gross.toFixed(2)),
        net: baseSalary,
        ndfl: parseFloat(ndfl.toFixed(2))
      });
    }
  };

  // Create mutation
  const createMutation = useMutation({
    mutationFn: employeeAPI.create,
    onSuccess: () => {
      message.success('Сотрудник создан');
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании сотрудника');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: EmployeeUpdate }) =>
      employeeAPI.update(id, data),
    onSuccess: () => {
      message.success('Сотрудник обновлен');
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении сотрудника');
    },
  });

  useEffect(() => {
    if (visible && employee) {
      form.setFieldsValue({
        ...employee,
        // Convert numeric string fields to numbers for proper validation
        base_salary: employee.base_salary ? Number(employee.base_salary) : undefined,
        monthly_bonus_base: employee.monthly_bonus_base ? Number(employee.monthly_bonus_base) : undefined,
        quarterly_bonus_base: employee.quarterly_bonus_base ? Number(employee.quarterly_bonus_base) : undefined,
        annual_bonus_base: employee.annual_bonus_base ? Number(employee.annual_bonus_base) : undefined,
        hire_date: employee.hire_date ? dayjs(employee.hire_date) : null,
        fire_date: employee.fire_date ? dayjs(employee.fire_date) : null,
        // Task 1.4: Salary type fields
        salary_type: employee.salary_type || 'GROSS',
        ndfl_rate: employee.ndfl_rate ? Number(employee.ndfl_rate) : 0.13,
      });

      // Calculate initial values for edit mode
      if (employee.base_salary) {
        calculateSalaries(
          Number(employee.base_salary),
          employee.salary_type || 'GROSS',
          employee.ndfl_rate ? Number(employee.ndfl_rate) : 0.13
        );
      }
    } else if (visible) {
      form.resetFields();
      // Set default values for new employee
      form.setFieldsValue({
        status: 'ACTIVE',
        // Set default department to selected one
        department_id: selectedDepartment?.id,
        // Task 1.4: Default salary settings
        salary_type: 'GROSS',
        ndfl_rate: 0.13,
      });
      setCalculatedSalaries({ gross: null, net: null, ndfl: null });
    }
  }, [visible, employee, form, selectedDepartment]);

  const handleClose = () => {
    form.resetFields();
    onCancel();
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        hire_date: values.hire_date ? values.hire_date.format('YYYY-MM-DD') : undefined,
        fire_date: values.fire_date ? values.fire_date.format('YYYY-MM-DD') : undefined,
      };

      if (isEdit && employee) {
        updateMutation.mutate({ id: employee.id, data });
      } else {
        createMutation.mutate(data as EmployeeCreate);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Редактировать сотрудника' : 'Добавить сотрудника'}
      open={visible}
      onCancel={handleClose}
      onOk={handleSubmit}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      width={700}
      okText={isEdit ? 'Сохранить' : 'Создать'}
      cancelText="Отмена"
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ status: 'ACTIVE' }}
      >
        <Form.Item
          name="full_name"
          label="ФИО"
          rules={[{ required: true, message: 'Введите ФИО сотрудника' }]}
        >
          <Input placeholder="Иванов Иван Иванович" />
        </Form.Item>

        {/* Department selector - visible only for ADMIN/MANAGER when creating new employee */}
        {!isEdit && canSelectDepartment && (
          <Form.Item
            name="department_id"
            label="Отдел"
            rules={[{ required: true, message: 'Выберите отдел' }]}
          >
            <Select
              placeholder="Выберите отдел"
              showSearch
              filterOption={(input, option) =>
                (option?.label?.toString() ?? '').toLowerCase().includes(input.toLowerCase())
              }
            >
              {departments.map((dept) => (
                <Option key={dept.id} value={dept.id} label={dept.name}>
                  {dept.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
        )}

        <Form.Item
          name="position"
          label="Должность"
          rules={[{ required: true, message: 'Введите должность' }]}
        >
          <Input placeholder="Менеджер по продажам" />
        </Form.Item>

        <Form.Item
          name="employee_number"
          label="Табельный номер"
        >
          <Input placeholder="EMP-001" />
        </Form.Item>

        {/* Task 1.4: Salary Type Toggle (Брутто/Нетто) */}
        <Form.Item
          name="salary_type"
          label="Тип ввода оклада"
          rules={[{ required: true }]}
        >
          <Radio.Group
            onChange={(e) => {
              const baseSalary = form.getFieldValue('base_salary');
              const ndflRate = form.getFieldValue('ndfl_rate') || 0.13;
              calculateSalaries(baseSalary, e.target.value, ndflRate);
            }}
          >
            <Radio.Button value="GROSS">Брутто (до вычета НДФЛ)</Radio.Button>
            <Radio.Button value="NET">Нетто (на руки)</Radio.Button>
          </Radio.Group>
        </Form.Item>

        <Form.Item
          name="base_salary"
          label={
            <Space>
              <span>Оклад</span>
              <span style={{ color: '#888', fontWeight: 'normal' }}>
                ({form.getFieldValue('salary_type') === 'GROSS' ? 'до вычета НДФЛ' : 'на руки после НДФЛ'})
              </span>
            </Space>
          }
          rules={[
            { required: true, message: 'Введите оклад' },
            { type: 'number', min: 0, message: 'Оклад не может быть отрицательным' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="50000"
            onChange={(value) => {
              const salaryType = form.getFieldValue('salary_type') || 'GROSS';
              const ndflRate = form.getFieldValue('ndfl_rate') || 0.13;
              calculateSalaries(value as number, salaryType, ndflRate);
            }}
            formatter={(value) => {
              if (value === undefined || value === null || value === '') return '';
              return `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
            }}
            parser={(value) => {
              if (!value) return undefined as any;
              const cleaned = value.replace(/\s/g, '');
              if (cleaned === '') return undefined as any;
              const num = Number(cleaned);
              return isNaN(num) ? undefined as any : num;
            }}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="ndfl_rate"
          label="Ставка НДФЛ"
          rules={[
            { required: true, message: 'Введите ставку НДФЛ' },
            { type: 'number', min: 0, max: 1, message: 'Ставка должна быть от 0 до 1 (например, 0.13 для 13%)' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0.13"
            step={0.01}
            onChange={(value) => {
              const baseSalary = form.getFieldValue('base_salary');
              const salaryType = form.getFieldValue('salary_type') || 'GROSS';
              calculateSalaries(baseSalary, salaryType, value as number);
            }}
            formatter={(value) => {
              if (value === undefined || value === null || value === '') return '';
              return `${(Number(value) * 100).toFixed(0)}%`;
            }}
            parser={(value) => {
              if (!value) return undefined as any;
              const cleaned = value.replace('%', '').trim();
              if (cleaned === '') return undefined as any;
              const num = Number(cleaned) / 100;
              return isNaN(num) ? undefined as any : num;
            }}
          />
        </Form.Item>

        {/* Calculated salary breakdown */}
        {calculatedSalaries.gross !== null && calculatedSalaries.net !== null && (
          <Alert
            message="Расчет заработной платы"
            description={
              <Space direction="vertical" style={{ width: '100%' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Брутто (начисление):</span>
                  <strong>{calculatedSalaries.gross?.toLocaleString('ru-RU')} ₽</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>НДФЛ ({((form.getFieldValue('ndfl_rate') || 0.13) * 100).toFixed(0)}%):</span>
                  <strong style={{ color: '#cf1322' }}>- {calculatedSalaries.ndfl?.toLocaleString('ru-RU')} ₽</strong>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #d9d9d9', paddingTop: 8 }}>
                  <span>Нетто (на руки):</span>
                  <strong style={{ color: '#3f8600', fontSize: 16 }}>{calculatedSalaries.net?.toLocaleString('ru-RU')} ₽</strong>
                </div>
              </Space>
            }
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}

        <Form.Item
          name="monthly_bonus_base"
          label="Базовая месячная премия"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => {
              if (value === undefined || value === null || value === '') return '';
              return `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
            }}
            parser={(value) => {
              if (!value) return undefined as any;
              const cleaned = value.replace(/\s/g, '');
              if (cleaned === '') return undefined as any;
              const num = Number(cleaned);
              return isNaN(num) ? undefined as any : num;
            }}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="quarterly_bonus_base"
          label="Базовая квартальная премия"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => {
              if (value === undefined || value === null || value === '') return '';
              return `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
            }}
            parser={(value) => {
              if (!value) return undefined as any;
              const cleaned = value.replace(/\s/g, '');
              if (cleaned === '') return undefined as any;
              const num = Number(cleaned);
              return isNaN(num) ? undefined as any : num;
            }}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="annual_bonus_base"
          label="Базовая годовая премия"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => {
              if (value === undefined || value === null || value === '') return '';
              return `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
            }}
            parser={(value) => {
              if (!value) return undefined as any;
              const cleaned = value.replace(/\s/g, '');
              if (cleaned === '') return undefined as any;
              const num = Number(cleaned);
              return isNaN(num) ? undefined as any : num;
            }}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="status"
          label="Статус"
          rules={[{ required: true, message: 'Выберите статус' }]}
        >
          <Select placeholder="Выберите статус">
            {STATUS_OPTIONS.map((option) => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="hire_date"
          label="Дата приема на работу"
        >
          <DatePicker style={{ width: '100%' }} format="DD.MM.YYYY" />
        </Form.Item>

        {form.getFieldValue('status') === 'FIRED' && (
          <Form.Item
            name="fire_date"
            label="Дата увольнения"
          >
            <DatePicker style={{ width: '100%' }} format="DD.MM.YYYY" />
          </Form.Item>
        )}

        <Form.Item
          name="email"
          label="Email"
          rules={[{ type: 'email', message: 'Введите корректный email' }]}
        >
          <Input placeholder="employee@company.com" />
        </Form.Item>

        <Form.Item
          name="phone"
          label="Телефон"
        >
          <Input placeholder="+7 (999) 123-45-67" />
        </Form.Item>

        <Form.Item
          name="notes"
          label="Примечания"
        >
          <TextArea rows={3} placeholder="Дополнительная информация о сотруднике" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
