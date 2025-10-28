import { useEffect, useState } from 'react';
import { Modal, Form, InputNumber, Select, DatePicker, message, Divider, Typography, Alert } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { payrollActualAPI, employeeAPI, payrollPlanAPI, PayrollActualCreate, PayrollActualUpdate } from '../../api/payroll';
import dayjs from 'dayjs';
import { shouldPayQuarterlyBonus, shouldPayAnnualBonus, calculateSocialTax } from '../../utils/payroll';

const { Text } = Typography;

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

  // Watch form values for tax calculation
  const [baseSalary, setBaseSalary] = useState(0);
  const [monthlyBonus, setMonthlyBonus] = useState(0);
  const [quarterlyBonus, setQuarterlyBonus] = useState(0);
  const [annualBonus, setAnnualBonus] = useState(0);
  const [otherPayments, setOtherPayments] = useState(0);
  const [incomeTaxRate, setIncomeTaxRate] = useState(0.13);
  const [currentMonth, setCurrentMonth] = useState<number | undefined>(undefined);

  // ВАЖНО: Введенные суммы - это то, что сотрудник получает НА РУКИ (net amount)
  // Нужно рассчитать gross и НДФЛ сверху

  // Net amount (на руки) - сумма всех введенных значений
  const netAmount = baseSalary + monthlyBonus + quarterlyBonus + annualBonus + otherPayments;

  // Calculate gross amount from net: gross = net / (1 - tax_rate)
  // Например: если net = 100,000 и НДФЛ 13%, то gross = 100,000 / 0.87 = 114,942.53
  const grossAmount = netAmount > 0 ? Math.round(netAmount / (1 - incomeTaxRate)) : 0;

  // Calculate income tax amount: income_tax = gross - net
  const incomeTaxAmount = grossAmount - netAmount;

  // Calculate social tax amount (30.2% - paid by employer, NOT deducted from employee)
  const socialTaxAmount = calculateSocialTax(grossAmount);

  // Calculate employer cost (gross + social tax)
  const employerCost = grossAmount + socialTaxAmount;

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
        monthly_bonus_paid: 0,
        quarterly_bonus_paid: 0,
        annual_bonus_paid: 0,
        other_payments_paid: 0,
        income_tax_rate: 13,  // Default 13%
        payment_date: dayjs(),
      });

      // Set current month for bonus alerts
      if (defaultValues.month) {
        setCurrentMonth(defaultValues.month);
      }

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
              monthly_bonus_paid: plan.monthly_bonus,
              quarterly_bonus_paid: plan.quarterly_bonus,
              annual_bonus_paid: plan.annual_bonus,
              other_payments_paid: plan.other_payments,
            });
          }
        }).catch(() => {
          // If no plan found, try to get employee base salary and bonus rates
          const employee = employees.find((e: any) => e.id === defaultValues.employee_id);
          if (employee) {
            form.setFieldsValue({
              base_salary_paid: employee.base_salary,
              monthly_bonus_paid: employee.monthly_bonus_base || 0,
              quarterly_bonus_paid: employee.quarterly_bonus_base || 0,
              annual_bonus_paid: employee.annual_bonus_base || 0,
            });
          }
        });
      }
    } else if (visible) {
      form.resetFields();
      form.setFieldsValue({
        year: currentYear,
        monthly_bonus_paid: 0,
        quarterly_bonus_paid: 0,
        annual_bonus_paid: 0,
        other_payments_paid: 0,
        income_tax_rate: 13,  // Default 13%
        payment_date: dayjs(),
      });
      setCurrentMonth(undefined);
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
            monthly_bonus_paid: plan.monthly_bonus,
            quarterly_bonus_paid: plan.quarterly_bonus,
            annual_bonus_paid: plan.annual_bonus,
            other_payments_paid: plan.other_payments,
          });
          return;
        }
      } catch (error) {
        // No plan found, continue to employee salary
      }
    }

    // Fallback to employee base salary and bonus rates
    const employee = employees.find((e: any) => e.id === employeeId);
    if (employee) {
      form.setFieldsValue({
        base_salary_paid: employee.base_salary,
        monthly_bonus_paid: employee.monthly_bonus_base || 0,
        quarterly_bonus_paid: employee.quarterly_bonus_base || 0,
        annual_bonus_paid: employee.annual_bonus_base || 0,
      });
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        payment_date: values.payment_date ? values.payment_date.format('YYYY-MM-DD') : undefined,
        monthly_bonus_paid: values.monthly_bonus_paid || 0,
        quarterly_bonus_paid: values.quarterly_bonus_paid || 0,
        annual_bonus_paid: values.annual_bonus_paid || 0,
        other_payments_paid: values.other_payments_paid || 0,
        income_tax_rate: (values.income_tax_rate || 13) / 100,  // Convert percentage to decimal
        income_tax_amount: incomeTaxAmount,
        social_tax_amount: socialTaxAmount,  // Automatically calculated (30.2%)
      };

      if (isEdit && actualId) {
        updateMutation.mutate({
          id: actualId,
          data: {
            base_salary_paid: data.base_salary_paid,
            monthly_bonus_paid: data.monthly_bonus_paid,
            quarterly_bonus_paid: data.quarterly_bonus_paid,
            annual_bonus_paid: data.annual_bonus_paid,
            other_payments_paid: data.other_payments_paid,
            income_tax_rate: data.income_tax_rate,
            income_tax_amount: data.income_tax_amount,
            social_tax_amount: data.social_tax_amount,
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
          <Select
            placeholder="Выберите месяц"
            disabled={isEdit}
            onChange={(value) => setCurrentMonth(value)}
          >
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

        {currentMonth && (
          <Alert
            message="Какие премии начисляются в этом месяце"
            description={
              <div>
                <div>✓ Месячная премия: всегда начисляется</div>
                {shouldPayQuarterlyBonus(currentMonth) && (
                  <div>✓ Квартальная премия: начисляется в этом месяце (конец квартала)</div>
                )}
                {!shouldPayQuarterlyBonus(currentMonth) && (
                  <div>✗ Квартальная премия: НЕ начисляется (только в марте, июне, сентябре и декабре)</div>
                )}
                {shouldPayAnnualBonus(currentMonth) && (
                  <div>✓ Годовая премия: начисляется в этом месяце (декабрь)</div>
                )}
                {!shouldPayAnnualBonus(currentMonth) && (
                  <div>✗ Годовая премия: НЕ начисляется (только в декабре)</div>
                )}
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form.Item
          name="base_salary_paid"
          label="Оклад (на руки)"
          tooltip="Сумма которую сотрудник получает на руки. НДФЛ рассчитывается автоматически."
          rules={[
            { required: true, message: 'Введите выплаченный оклад' },
            { type: 'number', min: 0, message: 'Оклад не может быть отрицательным' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="50000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setBaseSalary(value || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="monthly_bonus_paid"
          label="Месячная премия (на руки)"
          tooltip="Сумма которую сотрудник получает на руки. НДФЛ рассчитывается автоматически."
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setMonthlyBonus(value || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="quarterly_bonus_paid"
          label="Квартальная премия (на руки)"
          tooltip="Сумма которую сотрудник получает на руки. НДФЛ рассчитывается автоматически."
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setQuarterlyBonus(value || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="annual_bonus_paid"
          label="Годовая премия (на руки)"
          tooltip="Сумма которую сотрудник получает на руки. НДФЛ рассчитывается автоматически."
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setAnnualBonus(value || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="other_payments_paid"
          label="Прочие выплаты (на руки)"
          tooltip="Сумма которую сотрудник получает на руки. НДФЛ рассчитывается автоматически."
          rules={[
            { type: 'number', min: 0, message: 'Прочие выплаты не могут быть отрицательными' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="5000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setOtherPayments(value || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Divider orientation="left">Расчет выплаты и налогов</Divider>

        <Alert
          message="Расчет налогов"
          description="Введенные суммы (оклад, премии) - это то, что сотрудник получает НА РУКИ. НДФЛ и страховые взносы рассчитываются автоматически."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <Text strong style={{ color: '#52c41a' }}>Сумма на руки (введенные значения):</Text>
            <Text strong style={{ fontSize: 18, color: '#52c41a' }}>
              {netAmount.toLocaleString('ru-RU')} ₽
            </Text>
          </div>
          <Divider style={{ margin: '8px 0' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text>НДФЛ ({(incomeTaxRate * 100).toFixed(0)}%) - удержан из начислений:</Text>
            <Text type="danger">+{incomeTaxAmount.toLocaleString('ru-RU')} ₽</Text>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text>Начислено сотруднику (Gross):</Text>
            <Text strong style={{ fontSize: 16 }}>{grossAmount.toLocaleString('ru-RU')} ₽</Text>
          </div>
          <Divider style={{ margin: '8px 0' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <Text>Страховые взносы работодателя (30.2%):</Text>
            <Text style={{ color: '#fa8c16' }}>+{socialTaxAmount.toLocaleString('ru-RU')} ₽</Text>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <Text strong style={{ color: '#fa8c16' }}>Полная стоимость для компании:</Text>
            <Text strong style={{ fontSize: 18, color: '#fa8c16' }}>
              {employerCost.toLocaleString('ru-RU')} ₽
            </Text>
          </div>
        </div>

        <Form.Item
          name="income_tax_rate"
          label="Ставка НДФЛ (%)"
          rules={[
            { required: true, message: 'Введите ставку НДФЛ' },
            { type: 'number', min: 0, max: 100, message: 'Ставка должна быть от 0 до 100%' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="13"
            min={0}
            max={100}
            onChange={(value) => setIncomeTaxRate((value || 13) / 100)}
            addonAfter="%"
          />
        </Form.Item>

        <Alert
          message="Страховые взносы рассчитываются автоматически"
          description="Страховые взносы работодателя (30.2%) рассчитываются автоматически от суммы начислений. ПФР 22% + ОМС 5.1% + ФСС 2.9% + травматизм 0.2%"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      </Form>
    </Modal>
  );
}
