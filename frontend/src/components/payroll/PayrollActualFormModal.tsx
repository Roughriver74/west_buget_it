import { useEffect } from 'react';
import { Modal, Form, InputNumber, Select, DatePicker, message } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { payrollActualAPI, employeeAPI, payrollPlanAPI, PayrollActualCreate, PayrollActualUpdate } from '../../api/payroll';
import dayjs from 'dayjs';

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

interface PayrollActualFormModalProps {
  visible: boolean;
  actualId?: number;
  defaultValues?: {
    year?: number;
    month?: number;
    employee_id?: number;
  };
  onCancel: () => void;
}

export default function PayrollActualFormModal({
  visible,
  actualId,
  defaultValues,
  onCancel
}: PayrollActualFormModalProps) {
  const [form] = Form.useForm();
  const queryClient = useQueryClient();
  const isEdit = !!actualId;
  const currentYear = new Date().getFullYear();

  // Fetch employees for dropdown
  const { data: employees = [] } = useQuery({
    queryKey: ['employees'],
    queryFn: () => employeeAPI.list({ status: 'ACTIVE' }),
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: payrollActualAPI.create,
    onSuccess: () => {
      message.success('Факт выплаты создан');
      queryClient.invalidateQueries({ queryKey: ['payroll-actuals'] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при создании факта выплаты');
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: PayrollActualUpdate }) =>
      payrollActualAPI.update(id, data),
    onSuccess: () => {
      message.success('Факт выплаты обновлен');
      queryClient.invalidateQueries({ queryKey: ['payroll-actuals'] });
      handleClose();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении факта выплаты');
    },
  });

  useEffect(() => {
    if (visible && defaultValues) {
      form.setFieldsValue({
        year: defaultValues.year || currentYear,
        month: defaultValues.month,
        employee_id: defaultValues.employee_id,
        bonus_paid: 0,
        other_payments_paid: 0,
        payment_date: dayjs(),
      });

      // Try to get plan for this employee/year/month and pre-fill values
      if (defaultValues.employee_id && defaultValues.year && defaultValues.month) {
        payrollPlanAPI.list({
          employee_id: defaultValues.employee_id,
          year: defaultValues.year,
          month: defaultValues.month,
        }).then((plans) => {
          if (plans && plans.length > 0) {
            const plan = plans[0];
            form.setFieldsValue({
              base_salary_paid: plan.base_salary,
              bonus_paid: plan.bonus,
              other_payments_paid: plan.other_payments,
            });
          }
        }).catch(() => {
          // If no plan found, try to get employee base salary
          const employee = employees.find((e: any) => e.id === defaultValues.employee_id);
          if (employee) {
            form.setFieldsValue({ base_salary_paid: employee.base_salary });
          }
        });
      }
    } else if (visible) {
      form.resetFields();
      form.setFieldsValue({
        year: currentYear,
        bonus_paid: 0,
        other_payments_paid: 0,
        payment_date: dayjs(),
      });
    }
  }, [visible, defaultValues, employees, form, currentYear]);

  const handleClose = () => {
    form.resetFields();
    onCancel();
  };

  const handleEmployeeChange = async (employeeId: number) => {
    const year = form.getFieldValue('year');
    const month = form.getFieldValue('month');

    if (year && month) {
      try {
        const plans = await payrollPlanAPI.list({ employee_id: employeeId, year, month });
        if (plans && plans.length > 0) {
          const plan = plans[0];
          form.setFieldsValue({
            base_salary_paid: plan.base_salary,
            bonus_paid: plan.bonus,
            other_payments_paid: plan.other_payments,
          });
          return;
        }
      } catch (error) {
        // No plan found, continue to employee salary
      }
    }

    // Fallback to employee base salary
    const employee = employees.find((e: any) => e.id === employeeId);
    if (employee) {
      form.setFieldsValue({ base_salary_paid: employee.base_salary });
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        payment_date: values.payment_date ? values.payment_date.format('YYYY-MM-DD') : undefined,
        bonus_paid: values.bonus_paid || 0,
        other_payments_paid: values.other_payments_paid || 0,
      };

      if (isEdit && actualId) {
        updateMutation.mutate({
          id: actualId,
          data: {
            base_salary_paid: data.base_salary_paid,
            bonus_paid: data.bonus_paid,
            other_payments_paid: data.other_payments_paid,
            payment_date: data.payment_date,
          }
        });
      } else {
        createMutation.mutate(data as PayrollActualCreate);
      }
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  return (
    <Modal
      title={isEdit ? 'Редактировать факт выплаты' : 'Добавить факт выплаты'}
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
            filterOption={(input, option) =>
              (option?.children as string).toLowerCase().includes(input.toLowerCase())
            }
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
          name="payment_date"
          label="Дата выплаты"
          rules={[{ required: true, message: 'Выберите дату выплаты' }]}
        >
          <DatePicker style={{ width: '100%' }} format="DD.MM.YYYY" />
        </Form.Item>

        <Form.Item
          name="base_salary_paid"
          label="Оклад (выплачено)"
          rules={[
            { required: true, message: 'Введите выплаченный оклад' },
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
          name="bonus_paid"
          label="Премия (выплачено)"
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="10000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => value!.replace(/\s?/g, '')}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="other_payments_paid"
          label="Прочие выплаты (выплачено)"
          rules={[
            { type: 'number', min: 0, message: 'Прочие выплаты не могут быть отрицательными' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="5000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => value!.replace(/\s?/g, '')}
            addonAfter="₽"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
}
