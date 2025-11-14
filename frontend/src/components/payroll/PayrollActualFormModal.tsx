import { useEffect, useState } from 'react';
import { Modal, Form, InputNumber, Select, DatePicker, message, Divider, Typography, Alert, Spin } from 'antd';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { payrollActualAPI, employeeAPI, payrollPlanAPI, ndflAPI, PayrollActualCreate, PayrollActualUpdate } from '../../api/payroll';
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
  const defaultYear = new Date().getFullYear();

  // Watch form values for tax calculation
  const [baseSalary, setBaseSalary] = useState(0);
  const [monthlyBonus, setMonthlyBonus] = useState(0);
  const [quarterlyBonus, setQuarterlyBonus] = useState(0);
  const [annualBonus, setAnnualBonus] = useState(0);
  const [otherPayments, setOtherPayments] = useState(0);
  const [currentMonth, setCurrentMonth] = useState<number | undefined>(undefined);
  const [currentYear, setCurrentYear] = useState<number>(defaultYear);
  const [currentEmployeeId, setCurrentEmployeeId] = useState<number | undefined>(undefined);

  // YTD (year-to-date) income data
  const [ytdIncome, setYtdIncome] = useState(0);
  const [ytdTax, setYtdTax] = useState(0);
  const [loadingYtd, setLoadingYtd] = useState(false);

  // NDFL calculation result
  const [ndflResult, setNdflResult] = useState<any>(null);
  const [calculatingNdfl, setCalculatingNdfl] = useState(false);

  // НОВАЯ ЛОГИКА: Введенные суммы - это НАЧИСЛЕННАЯ сумма (gross)
  // Из неё автоматически рассчитывается НДФЛ по прогрессивной шкале
  const grossAmount = baseSalary + monthlyBonus + quarterlyBonus + annualBonus + otherPayments;

  // НДФЛ рассчитывается через API (прогрессивная шкала)
  const incomeTaxAmount = ndflResult?.tax_to_withhold || 0;
  const incomeTaxRate = ndflResult?.monthly_effective_rate ? ndflResult.monthly_effective_rate / 100 : 0.13;

  // Net amount (на руки) = gross - НДФЛ
  const netAmount = grossAmount - incomeTaxAmount;

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

  // Fetch employee YTD income and tax
  const fetchEmployeeYTD = async (employeeId: number, year: number, month: number) => {
    if (!employeeId || !year || !month) return;

    setLoadingYtd(true);
    try {
      const ytdData = await ndflAPI.getEmployeeYTDIncome({
        employee_id: employeeId,
        year,
        month,
      });
      setYtdIncome(ytdData.ytd_income);
      setYtdTax(ytdData.ytd_tax);
    } catch (error) {
      console.error('Failed to fetch YTD data:', error);
      // На случай ошибки используем 0
      setYtdIncome(0);
      setYtdTax(0);
    } finally {
      setLoadingYtd(false);
    }
  };

  // Calculate NDFL for current month
  const calculateNDFL = async (currentMonthIncome: number) => {
    if (!currentYear || !currentMonthIncome || currentMonthIncome <= 0) {
      setNdflResult(null);
      return;
    }

    setCalculatingNdfl(true);
    try {
      const result = await ndflAPI.calculateMonthlyNDFL({
        current_month_income: currentMonthIncome,
        ytd_income_before_month: ytdIncome,
        ytd_tax_withheld: ytdTax,
        year: currentYear,
      });
      setNdflResult(result);
    } catch (error) {
      console.error('Failed to calculate NDFL:', error);
      message.error('Ошибка расчета НДФЛ');
      setNdflResult(null);
    } finally {
      setCalculatingNdfl(false);
    }
  };

  // Auto-calculate NDFL when gross amount or YTD changes
  useEffect(() => {
    if (grossAmount > 0 && currentEmployeeId && currentMonth && currentYear) {
      calculateNDFL(grossAmount);
    } else {
      setNdflResult(null);
    }
  }, [grossAmount, ytdIncome, ytdTax, currentYear]);

  useEffect(() => {
    if (visible && defaultValues) {
      const year = defaultValues.year || defaultYear;
      const month = defaultValues.month;
      const employeeId = defaultValues.employee_id;

      form.setFieldsValue({
        year,
        month,
        employee_id: employeeId,
        monthly_bonus_paid: 0,
        quarterly_bonus_paid: 0,
        annual_bonus_paid: 0,
        other_payments_paid: 0,
        payment_date: dayjs(),
      });

      // Set current context
      setCurrentYear(year);
      setCurrentEmployeeId(employeeId);
      if (month) {
        setCurrentMonth(month);
      }

      // Fetch YTD data for this employee/year/month
      if (employeeId && year && month) {
        fetchEmployeeYTD(employeeId, year, month);
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
        year: defaultYear,
        monthly_bonus_paid: 0,
        quarterly_bonus_paid: 0,
        annual_bonus_paid: 0,
        other_payments_paid: 0,
        payment_date: dayjs(),
      });
      setCurrentYear(defaultYear);
      setCurrentMonth(undefined);
      setCurrentEmployeeId(undefined);
      setYtdIncome(0);
      setYtdTax(0);
      setNdflResult(null);
    }
  }, [visible, defaultValues, employees, form, defaultYear]);

  const handleClose = () => {
    form.resetFields();
    onCancel();
  };

  const handleEmployeeChange = async (employeeId: number) => {
    setCurrentEmployeeId(employeeId);

    const year = form.getFieldValue('year');
    const month = form.getFieldValue('month');

    // Fetch YTD data if we have all required parameters
    if (year && month) {
      fetchEmployeeYTD(employeeId, year, month);
    }

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
          // Update local state для автоматического расчета НДФЛ
          setBaseSalary(plan.base_salary);
          setMonthlyBonus(plan.monthly_bonus);
          setQuarterlyBonus(plan.quarterly_bonus);
          setAnnualBonus(plan.annual_bonus);
          setOtherPayments(plan.other_payments);
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
      // Update local state
      setBaseSalary(employee.base_salary);
      setMonthlyBonus(employee.monthly_bonus_base || 0);
      setQuarterlyBonus(employee.quarterly_bonus_base || 0);
      setAnnualBonus(employee.annual_bonus_base || 0);
    }
  };

  const handleYearChange = (year: number) => {
    setCurrentYear(year);
    const employeeId = form.getFieldValue('employee_id');
    const month = form.getFieldValue('month');
    if (employeeId && month) {
      fetchEmployeeYTD(employeeId, year, month);
    }
  };

  const handleMonthChange = (month: number) => {
    setCurrentMonth(month);
    const employeeId = form.getFieldValue('employee_id');
    const year = form.getFieldValue('year');
    if (employeeId && year) {
      fetchEmployeeYTD(employeeId, year, month);
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
          <Select placeholder="Выберите год" disabled={isEdit} onChange={handleYearChange}>
            {[defaultYear - 1, defaultYear, defaultYear + 1].map((year) => (
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
            onChange={handleMonthChange}
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
          label="Оклад (начислено)"
          tooltip="НАЧИСЛЕННАЯ сумма (до вычета НДФЛ). НДФЛ рассчитывается автоматически по прогрессивной шкале."
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
            onChange={(value) => setBaseSalary(Number(value) || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="monthly_bonus_paid"
          label="Месячная премия (начислено)"
          tooltip="НАЧИСЛЕННАЯ сумма (до вычета НДФЛ). НДФЛ рассчитывается автоматически по прогрессивной шкале."
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setMonthlyBonus(Number(value) || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="quarterly_bonus_paid"
          label="Квартальная премия (начислено)"
          tooltip="НАЧИСЛЕННАЯ сумма (до вычета НДФЛ). НДФЛ рассчитывается автоматически по прогрессивной шкале."
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setQuarterlyBonus(Number(value) || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="annual_bonus_paid"
          label="Годовая премия (начислено)"
          tooltip="НАЧИСЛЕННАЯ сумма (до вычета НДФЛ). НДФЛ рассчитывается автоматически по прогрессивной шкале."
          rules={[
            { type: 'number', min: 0, message: 'Премия не может быть отрицательной' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="0"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setAnnualBonus(Number(value) || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Form.Item
          name="other_payments_paid"
          label="Прочие выплаты (начислено)"
          tooltip="НАЧИСЛЕННАЯ сумма (до вычета НДФЛ). НДФЛ рассчитывается автоматически по прогрессивной шкале."
          rules={[
            { type: 'number', min: 0, message: 'Прочие выплаты не могут быть отрицательными' },
          ]}
        >
          <InputNumber
            style={{ width: '100%' }}
            placeholder="5000"
            formatter={(value) => `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ' ')}
            parser={(value) => Number((value ?? '').replace(/\s?/g, ''))}
            onChange={(value) => setOtherPayments(Number(value) || 0)}
            addonAfter="₽"
          />
        </Form.Item>

        <Divider orientation="left">Расчет выплаты и налогов</Divider>

        <Alert
          message="Прогрессивный НДФЛ"
          description="Введенные суммы (оклад, премии) - это НАЧИСЛЕННЫЕ суммы. НДФЛ рассчитывается автоматически по прогрессивной шкале с учетом дохода с начала года."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />

        {loadingYtd && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
            <Spin tip="Загрузка данных о доходе сотрудника...">
              <div style={{ minHeight: 100 }} />
            </Spin>
          </div>
        )}

        {!loadingYtd && currentEmployeeId && currentMonth && currentYear && (
          <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#e6f7ff', borderRadius: '4px' }}>
            <Text strong>Доход с начала года (до текущего месяца):</Text>
            <div style={{ marginTop: 8 }}>
              <Text>• Начислено с начала года: {ytdIncome.toLocaleString('ru-RU')} ₽</Text><br/>
              <Text>• НДФЛ удержан с начала года: {ytdTax.toLocaleString('ru-RU')} ₽</Text>
            </div>
          </div>
        )}

        {calculatingNdfl && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
            <Spin tip="Расчет НДФЛ по прогрессивной шкале...">
              <div style={{ minHeight: 100 }} />
            </Spin>
          </div>
        )}

        {!calculatingNdfl && grossAmount > 0 && (
          <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <Text>Начислено в текущем месяце (Gross):</Text>
              <Text strong style={{ fontSize: 16 }}>{grossAmount.toLocaleString('ru-RU')} ₽</Text>
            </div>
            <Divider style={{ margin: '8px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text>НДФЛ ({(incomeTaxRate * 100).toFixed(2)}%) - по прогрессивной шкале:</Text>
              <Text type="danger" strong>-{Math.round(incomeTaxAmount).toLocaleString('ru-RU')} ₽</Text>
            </div>
            {ndflResult && (
              <div style={{ fontSize: '12px', color: '#666', marginLeft: 8, marginBottom: 8 }}>
                <Text type="secondary">
                  Система: {ndflResult.system === '5-tier' ? '5 ступеней (2025+)' : '2 ступени (2024)'}
                </Text><br/>
                <Text type="secondary">
                  YTD доход: {ndflResult.ytd_income_total.toLocaleString('ru-RU')} ₽
                </Text>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <Text strong style={{ color: '#52c41a' }}>Сумма на руки:</Text>
              <Text strong style={{ fontSize: 18, color: '#52c41a' }}>
                {Math.round(netAmount).toLocaleString('ru-RU')} ₽
              </Text>
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
        )}

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
