import { useEffect } from 'react';
import { Modal, Form, Input, InputNumber, Select, DatePicker, message } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { employeeAPI, Employee, EmployeeCreate, EmployeeUpdate } from '../../api/payroll';
import { departmentsAPI } from '../../api/departments';
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
  const isEdit = !!employee;

  // Fetch departments for dropdown
  const { data: departments = [] } = useQuery({
    queryKey: ['departments'],
    queryFn: () => departmentsAPI.list(),
  });

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
        hire_date: employee.hire_date ? dayjs(employee.hire_date) : null,
        fire_date: employee.fire_date ? dayjs(employee.fire_date) : null,
      });
    } else if (visible) {
      form.resetFields();
      form.setFieldsValue({ status: 'ACTIVE' });
    }
  }, [visible, employee, form]);

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

        <Form.Item
          name="base_salary"
          label="Оклад"
          rules={[
            { required: true, message: 'Введите оклад' },
            { type: 'number', min: 0, message: 'Оклад не может быть отрицательным' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="50000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => value!.replace(/\s?/g, '')}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="department_id"
          label="Отдел"
          rules={[{ required: true, message: 'Выберите отдел' }]}
        >
          <Select placeholder="Выберите отдел">
            {departments.map((dept: any) => (
              <Option key={dept.id} value={dept.id}>
                {dept.name}
              </Option>
            ))}
          </Select>
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
