import { useEffect } from 'react';
import { Modal, Form, InputNumber, Select, message } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { payrollPlanAPI, employeeAPI, PayrollPlanCreate, PayrollPlanUpdate } from '../../api/payroll';

const { Option } = Select;

const MONTHS = [
  { value: 1, label: 'Январь' },
  { value: 2, label: 'Февраль' },
  { value: 3, label: 'Март' },
  { value: 4, label: 'Апрель' },
  { value: 5, label: 'Май' },
  { value: 6, label: 'Июнь' },
  { value: 7, label: 'Июль' },
  { value: 8, label: 'Август' },
  { value: 9, label: 'Сентябрь' },
  { value: 10, label: 'Октябрь' },
  { value: 11, label: 'Ноябрь' },
  { value: 12, label: 'Декабрь' },
];

interface PayrollPlanFormModalProps {
  visible: boolean;
  planId?: number;
  defaultValues?: {
    year?: number;
    month?: number;
    employee_id?: number;
  };
  onCancel: () => void;
}

export default function PayrollPlanFormModal({
  visible,
  planId,
  defaultValues,
  onCancel
}: PayrollPlanFormModalProps) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!planId;
  const currentYear = new Date().getFullYear();

  // Fetch employees for dropdown
  const { data: employees = [] } = useQuery({
    queryKey: ['employees'],
    queryFn: () => employeeAPI.list({ status: 'ACTIVE' }),
  });

  // Fetch plan if editing
  const { data: plan } = useQuery({
    queryKey: ['payroll-plan', planId],
    queryFn: () => planId ? payrollPlanAPI.get(planId) : null,
    enabled: !!planId,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: payrollPlanAPI.create,
    onSuccess: () => {
      message.success('План ФОТ создан');
      queryClient.invalidateQueries({ queryKey: ['payroll-plans'] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании плана ФОТ');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PayrollPlanUpdate }) =>
      payrollPlanAPI.update(id, data),
    onSuccess: () => {
      message.success('План ФОТ обновлен');
      queryClient.invalidateQueries({ queryKey: ['payroll-plans'] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении плана ФОТ');
    },
  });

  useEffect(() => {
    if (visible) {
      if (plan && isEdit) {
        form.setFieldsValue({
          year: plan.year,
          month: plan.month,
          employee_id: plan.employee_id,
          base_salary: plan.base_salary,
          monthly_bonus: plan.monthly_bonus,
          quarterly_bonus: plan.quarterly_bonus,
          annual_bonus: plan.annual_bonus,
          other_payments: plan.other_payments,
        });
      } else if (defaultValues) {
        form.setFieldsValue({
          year: defaultValues.year || currentYear,
          month: defaultValues.month,
          employee_id: defaultValues.employee_id,
          monthly_bonus: 0,
          quarterly_bonus: 0,
          annual_bonus: 0,
          other_payments: 0,
        });

        // Auto-fill base salary and bonus rates from employee if employee is selected
        if (defaultValues.employee_id) {
          const employee = employees.find((e: any) => e.id === defaultValues.employee_id);
          if (employee) {
            form.setFieldsValue({
              base_salary: employee.base_salary,
              monthly_bonus: employee.monthly_bonus_base || 0,
              quarterly_bonus: employee.quarterly_bonus_base || 0,
              annual_bonus: employee.annual_bonus_base || 0,
            });
          }
        }
      } else {
        form.resetFields();
        form.setFieldsValue({
          year: currentYear,
          monthly_bonus: 0,
          quarterly_bonus: 0,
          annual_bonus: 0,
          other_payments: 0,
        });
      }
    }
  }, [visible, plan, defaultValues, employees, isEdit, form, currentYear]);

  const handleClose = () => {
    form.resetFields();
    onCancel();
  };

  const handleEmployeeChange = (employeeId: number) => {
    const employee = employees.find((e: any) => e.id === employeeId);
    if (employee) {
      form.setFieldsValue({
        base_salary: employee.base_salary,
        monthly_bonus: employee.monthly_bonus_base || 0,
        quarterly_bonus: employee.quarterly_bonus_base || 0,
        annual_bonus: employee.annual_bonus_base || 0,
      });
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();

      if (isEdit && planId) {
        updateMutation.mutate({
          id: planId,
          data: {
            base_salary: values.base_salary,
            monthly_bonus: values.monthly_bonus || 0,
            quarterly_bonus: values.quarterly_bonus || 0,
            annual_bonus: values.annual_bonus || 0,
            other_payments: values.other_payments || 0,
          }
        });
      } else {
        createMutation.mutate({
          ...values,
          monthly_bonus: values.monthly_bonus || 0,
          quarterly_bonus: values.quarterly_bonus || 0,
          annual_bonus: values.annual_bonus || 0,
          other_payments: values.other_payments || 0,
        } as PayrollPlanCreate);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Редактировать план ФОТ' : 'Добавить план ФОТ'}
      open={visible}
      onCancel={handleClose}
      onOk={handleSubmit}
      confirmLoading={createMutation.isPending || updateMutation.isPending}
      width={600}
      okText={isEdit ? 'Сохранить' : 'Создать'}
      cancelText="Отмена"
    >
      <Form
        form={form}
        layout="vertical"
      >
        <Form.Item
          name="employee_id"
          label="Сотрудник"
          rules={[{ required: true, message: 'Выберите сотрудника' }]}
        >
          <Select
            placeholder="Выберите сотрудника"
            disabled={isEdit}
            onChange={handleEmployeeChange}
            showSearch
            filterOption={(input, option) => {
              const label = option?.label ?? option?.value
              return String(label ?? '')
                .toLowerCase()
                .includes(input.toLowerCase())
            }}
          >
            {employees.map((emp: any) => (
              <Option key={emp.id} value={emp.id}>
                {emp.full_name} - {emp.position}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="year"
          label="Год"
          rules={[{ required: true, message: 'Выберите год' }]}
        >
          <Select placeholder="Выберите год" disabled={isEdit}>
            {[currentYear - 1, currentYear, currentYear + 1].map((year) => (
              <Option key={year} value={year}>
                {year}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="month"
          label="Месяц"
          rules={[{ required: true, message: 'Выберите месяц' }]}
        >
          <Select placeholder="Выберите месяц" disabled={isEdit}>
            {MONTHS.map((month) => (
              <Option key={month.value} value={month.value}>
                {month.label}
              </Option>
            ))}
          </Select>
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
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="monthly_bonus"
          label="Месячная премия"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="quarterly_bonus"
          label="Квартальная премия"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="annual_bonus"
          label="Годовая премия"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="other_payments"
          label="Прочие выплаты"
          rules={[
            { type: 'number', min: 0, message: 'Прочие выплаты не могут быть отрицательными' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="5000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            addonAfter="₽"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
