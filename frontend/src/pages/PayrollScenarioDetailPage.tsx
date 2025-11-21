/**
 * PayrollScenarioDetailPage - Детальный просмотр сценария ФОТ
 *
 * Показывает разбивку по каждому сотруднику с расчетами:
 * - Базовая зарплата и премии
 * - Страховые взносы (ПФР, ФОМС, ФСС, травматизм)
 * - НДФЛ
 * - Общая стоимость сотрудника
 * - Сравнение с базовым годом
 */

import React, { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Card,
  Table,
  Typography,
  Statistic,
  Row,
  Col,
  Descriptions,
  Tag,
  Button,
  Spin,
  Space,
  Divider,
  Alert,
  Modal,
  Form,
  InputNumber,
  message,
  Tabs,
} from 'antd';
import {
  ArrowLeftOutlined,
  UserOutlined,
  DollarOutlined,
  RiseOutlined,
  FallOutlined,
  EditOutlined,
  CalculatorOutlined,
  ExperimentOutlined,
  TableOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { payrollScenarioAPI, type PayrollScenarioWithDetails } from '@/api/payrollScenarios';
import { taxRateAPI, type TaxRateListItem, type TaxType } from '@/api/taxRates';
import { PayrollWhatIfAnalysis } from '../components/payroll/PayrollWhatIfAnalysis';
import PayrollScenarioCharts from '../components/payroll/PayrollScenarioCharts';
import { useIsMobile, useIsSmallScreen } from '@/hooks/useMediaQuery';
import { ResponsiveTable } from '@/components/common/ResponsiveTable';

const { Title, Text } = Typography;

const SCENARIO_TYPE_LABELS: Record<string, string> = {
  BASE: 'Базовый',
  OPTIMISTIC: 'Оптимистичный',
  PESSIMISTIC: 'Пессимистичный',
  CUSTOM: 'Пользовательский',
};

const SCENARIO_TYPE_COLORS: Record<string, string> = {
  BASE: 'blue',
  OPTIMISTIC: 'green',
  PESSIMISTIC: 'red',
  CUSTOM: 'purple',
};

const DATA_SOURCE_LABELS: Record<string, string> = {
  EMPLOYEES: 'Сотрудники',
  PLAN: 'План ФОТ',
  ACTUAL: 'Факт',
};

const DATA_SOURCE_COLORS: Record<string, string> = {
  EMPLOYEES: 'blue',
  PLAN: 'orange',
  ACTUAL: 'green',
};

const formatCurrency = (value?: number) => {
  if (value === undefined || value === null) return '—';
  return new Intl.NumberFormat('ru-RU', {
    style: 'currency',
    currency: 'RUB',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
};

const formatPercent = (value?: number) => {
  if (value === undefined || value === null) return '—';
  const formatted = value.toFixed(2);
  const color = value >= 0 ? '#52c41a' : '#f5222d';
  const icon = value >= 0 ? <RiseOutlined /> : <FallOutlined />;
  return (
    <Text style={{ color }}>
      {icon} {formatted}%
    </Text>
  );
};

export const PayrollScenarioDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isMobile = useIsMobile();
  const isSmallScreen = useIsSmallScreen();
  const [isEditModalOpen, setEditModalOpen] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: scenario, isLoading } = useQuery<PayrollScenarioWithDetails>({
    queryKey: ['payroll-scenario', id],
    queryFn: () => payrollScenarioAPI.get(Number(id)),
    enabled: !!id,
  });

  // Получаем страховые взносы для целевого года из справочника tax-rates
  // Используем department_id из сценария, а не из контекста
  // Берем все активные ставки и фильтруем на фронтенде, чтобы учесть будущие ставки
  // ВАЖНО: Запрашиваем ВСЕ активные ставки (без фильтра по department_id), чтобы получить и департаментные, и глобальные
  const { data: allTaxRates = [] } = useQuery<TaxRateListItem[]>({
    queryKey: ['tax-rates-all', scenario?.department_id],
    queryFn: async () => {
      // Запрашиваем ВСЕ активные ставки (без фильтра по department_id)
      // Это даст нам и ставки для департамента, и глобальные ставки (department_id = null)
      const allRates = await taxRateAPI.list({ 
        is_active: true,
        limit: 500, // Получаем все ставки
      });
      
      console.log('Fetched all tax rates:', {
        total: allRates.length,
        department_id: scenario?.department_id,
        rates: allRates.map(r => ({ 
          id: r.id, 
          type: r.tax_type, 
          dept: r.department_id,
          from: r.effective_from 
        })),
      });
      
      return allRates;
    },
    enabled: !!scenario?.department_id,
  });

  // Фильтруем ставки для целевого года (актуальные на 1 января или будущие в течение года)
  const insuranceRates = useMemo(() => {
    console.log('Calculating insuranceRates for target year:', scenario?.target_year);
    console.log('allTaxRates length:', allTaxRates.length);

    if (!allTaxRates.length || !scenario?.target_year) {
      console.log('Returning empty insuranceRates - no data or no target year');
      return [];
    }

    const targetDate = new Date(scenario.target_year, 0, 1); // 1 января целевого года
    const yearEndDate = new Date(scenario.target_year, 11, 31); // 31 декабря целевого года
    
    const insuranceTypes = ['PENSION_FUND', 'MEDICAL_INSURANCE', 'SOCIAL_INSURANCE', 'INJURY_INSURANCE'];
    const ratesByType: Record<string, TaxRateListItem[]> = {};
    
    // Группируем ставки по типу
    // ВАЖНО: Приоритет ставкам для департамента сценария, затем глобальным (department_id === null)
    allTaxRates
      .filter(rate => insuranceTypes.includes(rate.tax_type))
      .forEach(rate => {
        const effectiveFrom = new Date(rate.effective_from);
        const effectiveTo = rate.effective_to ? new Date(rate.effective_to) : null;
        
        // Проверяем, актуальна ли ставка на целевую дату или начнется в течение года
        const isCurrent = effectiveFrom <= targetDate && (!effectiveTo || effectiveTo >= targetDate);
        const isFuture = effectiveFrom > targetDate && effectiveFrom <= yearEndDate;
        
        if (isCurrent || isFuture) {
          // Проверяем, подходит ли ставка для департамента сценария
          const isForDepartment = rate.department_id === scenario?.department_id;
          const isGlobal = rate.department_id === null || rate.department_id === undefined;
          
          // Берем ставки для департамента сценария ИЛИ глобальные
          if (isForDepartment || isGlobal) {
            if (!ratesByType[rate.tax_type]) {
              ratesByType[rate.tax_type] = [];
            }
            ratesByType[rate.tax_type].push(rate);
          }
        }
      });
    
    // Для каждого типа берем самую актуальную ставку
    // ПРИОРИТЕТ: 1) Ставки для департамента сценария, 2) Глобальные ставки
    const result: TaxRateListItem[] = [];
    insuranceTypes.forEach(type => {
      const rates = ratesByType[type] || [];
      if (rates.length > 0) {
        // Разделяем на ставки для департамента и глобальные
        const deptRates = rates.filter(r => r.department_id === scenario?.department_id);
        const globalRates = rates.filter(r => r.department_id === null || r.department_id === undefined);
        
        // Приоритет: сначала ставки для департамента, потом глобальные
        const priorityRates = deptRates.length > 0 ? deptRates : globalRates;
        
        // Сортируем: ПРИОРИТЕТ будущим ставкам, которые начнут действовать в целевом году
        // Если есть ставка с effective_from в пределах целевого года, она важнее текущей
        priorityRates.sort((a, b) => {
          const aDate = new Date(a.effective_from);
          const bDate = new Date(b.effective_from);
          const aIsCurrent = aDate <= targetDate;
          const bIsCurrent = bDate <= targetDate;
          const aIsFuture = aDate > targetDate && aDate <= yearEndDate;
          const bIsFuture = bDate > targetDate && bDate <= yearEndDate;
          
          // Будущие ставки (в пределах года) имеют приоритет над текущими
          if (aIsFuture && !bIsFuture) return -1;
          if (!aIsFuture && bIsFuture) return 1;
          
          // Если обе будущие - берем самую раннюю (которая начнет действовать первой)
          if (aIsFuture && bIsFuture) return aDate.getTime() - bDate.getTime();
          
          // Если обе текущие - берем самую позднюю (самую актуальную)
          if (aIsCurrent && bIsCurrent) return bDate.getTime() - aDate.getTime();
          
          return 0;
        });
        
        if (priorityRates.length > 0) {
          result.push(priorityRates[0]); // Берем первую (самую актуальную)
        }
      }
    });

    console.log('Filtered insuranceRates for target year:', result);
    console.log('Rates by type:', result.map(r => ({ type: r.tax_type, rate: r.rate, from: r.effective_from, to: r.effective_to })));

    return result;
  }, [allTaxRates, scenario?.target_year]);

  // Фильтруем ставки для базового года
  const baseYearInsuranceRates = useMemo(() => {
    if (!allTaxRates.length || !scenario?.base_year) return [];
    
    const baseDate = new Date(scenario.base_year, 0, 1);
    
    const insuranceTypes = ['PENSION_FUND', 'MEDICAL_INSURANCE', 'SOCIAL_INSURANCE', 'INJURY_INSURANCE'];
    const ratesByType: Record<string, TaxRateListItem[]> = {};
    
    allTaxRates
      .filter(rate => insuranceTypes.includes(rate.tax_type))
      .forEach(rate => {
        const effectiveFrom = new Date(rate.effective_from);
        const effectiveTo = rate.effective_to ? new Date(rate.effective_to) : null;
        
        const isCurrent = effectiveFrom <= baseDate && (!effectiveTo || effectiveTo >= baseDate);
        
        if (isCurrent) {
          if (!ratesByType[rate.tax_type]) {
            ratesByType[rate.tax_type] = [];
          }
          ratesByType[rate.tax_type].push(rate);
        }
      });
    
    const result: TaxRateListItem[] = [];
    insuranceTypes.forEach(type => {
      const rates = ratesByType[type] || [];
      if (rates.length > 0) {
        rates.sort((a, b) => new Date(b.effective_from).getTime() - new Date(a.effective_from).getTime());
        result.push(rates[0]);
      }
    });
    
    return result;
  }, [allTaxRates, scenario?.base_year]);

  const updateMutation = useMutation({
    mutationFn: async (values: any) => {
      console.log('updateMutation.mutationFn called with values:', values);
      console.log('Scenario ID:', id);

      // 1. Обновляем параметры (headcount_change_percent, salary_change_percent)
      const updated = await payrollScenarioAPI.update(Number(id), values);
      console.log('Update response:', updated);

      // 2. Пересчитываем сценарий (calculate создает/обновляет scenario_details и считает суммы)
      console.log('Calling calculate...');
      const calculated = await payrollScenarioAPI.calculate(Number(id));
      console.log('Calculate response:', calculated);

      // 3. ВАЖНО: Получаем полный сценарий со всеми деталями
      // calculate возвращает только итоги, но нам нужен полный объект с base_year, scenario_details и т.д.
      console.log('Fetching full scenario after calculate...');
      const fullScenario = await payrollScenarioAPI.get(Number(id));
      console.log('Full scenario response:', fullScenario);

      return fullScenario;
    },
    onSuccess: (data) => {
      console.log('updateMutation.onSuccess called with calculated data:', data);
      message.success('Параметры сценария обновлены и пересчитаны');

      // ВАЖНО: Сразу устанавливаем пересчитанные данные в кэш,
      // чтобы UI обновился мгновенно без дополнительного запроса
      queryClient.setQueryData(['payroll-scenario', id], data);

      // Также инвалидируем общий список сценариев
      queryClient.invalidateQueries({ queryKey: ['payroll-scenarios'] });
      setEditModalOpen(false);
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || 'Не удалось обновить параметры';
      message.error(errorMsg);
      console.error('Update scenario error:', error);
      console.error('Error details:', error?.response?.data);
    },
  });

  const calculateMutation = useMutation({
    mutationFn: () => payrollScenarioAPI.calculate(Number(id)),
    onSuccess: () => {
      message.success('Сценарий пересчитан');
      queryClient.invalidateQueries({ queryKey: ['payroll-scenario', id] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Не удалось пересчитать сценарий');
    },
  });

  const handleEditOpen = () => {
    if (scenario) {
      form.setFieldsValue({
        headcount_change_percent: scenario.headcount_change_percent || 0,
        salary_change_percent: scenario.salary_change_percent || 0,
      });
      setEditModalOpen(true);
    }
  };

  const handleEditSubmit = (values: any) => {
    updateMutation.mutate(values);
  };

  // Синхронизация ставок (ПФР/ФОМС/ФСС/Травматизм/НДФЛ) с выбранными в What-If
  // При применении What-If создаем/обновляем ставки для целевого года и департамента сценария,
  // чтобы серверный пересчет использовал те же проценты.
  const upsertWhatIfTaxRates = async (params: {
    pensionRate: number;
    medicalRate: number;
    socialRate: number;
    injuryRate: number;
    incomeTaxRate: number;
  }) => {
    if (!scenario) return;

    const targetYear = scenario.target_year;
    const departmentId = scenario.department_id;
    const yearStart = `${targetYear}-01-01`;

    const rateItems: Array<{ type: TaxType; value: number; name: string }> = [
      { type: 'PENSION_FUND', value: params.pensionRate, name: 'ПФР' },
      { type: 'MEDICAL_INSURANCE', value: params.medicalRate, name: 'ФОМС' },
      { type: 'SOCIAL_INSURANCE', value: params.socialRate, name: 'ФСС' },
      { type: 'INJURY_INSURANCE', value: params.injuryRate, name: 'Травматизм' },
      { type: 'INCOME_TAX', value: params.incomeTaxRate, name: 'НДФЛ' },
    ];

    const updates: Promise<any>[] = [];

    rateItems.forEach(({ type, value, name }) => {
      // API принимает долю (0.22), UI работает в процентах (22)
      const rateFraction = Number((value / 100).toFixed(6));
      const existing = (allTaxRates || []).find(
        (r) =>
          r.tax_type === type &&
          r.department_id === departmentId &&
          new Date(r.effective_from).getFullYear() === targetYear
      );

      if (existing) {
        // Обновляем только если отличается
        if (Math.abs(existing.rate - rateFraction) > 1e-6) {
          updates.push(
            taxRateAPI.update(existing.id, {
              rate: rateFraction,
            })
          );
        }
      } else {
        updates.push(
          taxRateAPI.create({
            tax_type: type as any,
            name: `${name} ${targetYear}`,
            rate: rateFraction,
            effective_from: yearStart,
            department_id: departmentId,
            is_active: true,
          })
        );
      }
    });

    if (updates.length) {
      await Promise.all(updates);
      queryClient.invalidateQueries({ queryKey: ['tax-rates-all', scenario?.department_id] });
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400 }}>
        <Spin size="large" tip="Загрузка деталей сценария..."  mobileLayout="card" />
      </div>
    );
  }

  if (!scenario) {
    return (
      <Alert
        message="Сценарий не найден"
        description="Запрашиваемый сценарий не существует или был удален."
        type="error"
        showIcon
       mobileLayout="card" />
    );
  }

  const columns = [
    {
      title: 'Сотрудник',
      dataIndex: 'employee_name',
      key: 'employee_name',
      width: 200,
      fixed: 'left' as const,
      render: (name: string, record: any) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name}</Text>
          {record.position && <Text type="secondary" style={{ fontSize: 12 }}>{record.position}</Text>}
          {record.is_new_hire && <Tag color="green" style={{ marginTop: 4 }}>Новый</Tag>}
          {record.is_terminated && <Tag color="red" style={{ marginTop: 4 }}>Увольнение</Tag>}
        </Space>
      ),
    },
    {
      title: 'Оклад (месяц)',
      dataIndex: 'base_salary',
      key: 'base_salary',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Премия (месяц)',
      dataIndex: 'monthly_bonus',
      key: 'monthly_bonus',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Премия (квартал)',
      dataIndex: 'quarterly_bonus',
      key: 'quarterly_bonus',
      width: 130,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value || 0),
    },
    {
      title: 'Премия (год)',
      dataIndex: 'annual_bonus',
      key: 'annual_bonus',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value || 0),
    },
    {
      title: 'Годовая ЗП',
      key: 'annual_salary',
      width: 140,
      align: 'right' as const,
      render: (_: any, record: any) => {
        // ИСПРАВЛЕНО: Учитываем все виды премий
        const months_worked = record.is_terminated && record.termination_month
          ? record.termination_month
          : 12;
        const monthly_total = (record.base_salary + record.monthly_bonus) * months_worked;
        const quarterly_total = (record.quarterly_bonus || 0) * 4;
        const annual_total = record.annual_bonus || 0;
        const total = monthly_total + quarterly_total + annual_total;
        return <Text strong>{formatCurrency(total)}</Text>;
      },
    },
    {
      title: 'ПФР',
      dataIndex: 'pension_contribution',
      key: 'pension_contribution',
      width: 110,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'ФОМС',
      dataIndex: 'medical_contribution',
      key: 'medical_contribution',
      width: 110,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'ФСС',
      dataIndex: 'social_contribution',
      key: 'social_contribution',
      width: 110,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Травматизм',
      dataIndex: 'injury_contribution',
      key: 'injury_contribution',
      width: 110,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Всего взносы',
      dataIndex: 'total_insurance',
      key: 'total_insurance',
      width: 130,
      align: 'right' as const,
      render: (value: number) => <Text strong style={{ color: '#1890ff' }}>{formatCurrency(value)}</Text>,
    },
    {
      title: 'НДФЛ (13%)',
      dataIndex: 'income_tax',
      key: 'income_tax',
      width: 120,
      align: 'right' as const,
      render: (value: number) => formatCurrency(value),
    },
    {
      title: 'Общая стоимость',
      dataIndex: 'total_employee_cost',
      key: 'total_employee_cost',
      width: 150,
      align: 'right' as const,
      fixed: 'right' as const,
      render: (value: number) => (
        <Text strong style={{ color: '#52c41a', fontSize: 14 }}>
          {formatCurrency(value)}
        </Text>
      ),
    },
    {
      title: 'Изменение',
      dataIndex: 'cost_increase',
      key: 'cost_increase',
      width: 120,
      align: 'right' as const,
      fixed: 'right' as const,
      render: (value: number) => {
        if (!value) return '—';
        const color = value >= 0 ? '#52c41a' : '#f5222d';
        const icon = value >= 0 ? <RiseOutlined /> : <FallOutlined />;
        return (
          <Space size={4}>
            {icon}
            <Text style={{ color }}>{formatCurrency(Math.abs(value))}</Text>
          </Space>
        );
      },
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header with back button */}
      <Space style={{ marginBottom: 24 }}>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/payroll/scenarios')}
        >
          Назад к сценариям
        </Button>
        <Button
          type="primary"
          icon={<EditOutlined />}
          onClick={handleEditOpen}
        >
          Редактировать параметры
        </Button>
        <Button
          icon={<CalculatorOutlined />}
          onClick={() => calculateMutation.mutate()}
          loading={calculateMutation.isPending}
        >
          Пересчитать сценарий
        </Button>
      </Space>

      {/* Scenario Summary Card */}
      <Card style={{ marginBottom: 24 }}>
        <Title level={3} style={{ marginTop: 0 }}>
          {scenario.name}
        </Title>

        {scenario.description && (
          <Text type="secondary" style={{ display: 'block', marginBottom: 16 }}>
            {scenario.description}
          </Text>
        )}

        <Descriptions column={4} bordered size="small">
          <Descriptions.Item label="Тип сценария">
            <Tag color={SCENARIO_TYPE_COLORS[scenario.scenario_type]}>
              {SCENARIO_TYPE_LABELS[scenario.scenario_type]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Источник данных">
            <Tag color={DATA_SOURCE_COLORS[scenario.data_source]}>
              {DATA_SOURCE_LABELS[scenario.data_source]}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="Базовый год">
            <Text strong>{scenario.base_year}</Text>
          </Descriptions.Item>
          <Descriptions.Item label="Целевой год">
            <Text strong>{scenario.target_year}</Text>
          </Descriptions.Item>
        </Descriptions>

        <Divider  mobileLayout="card" />

        {/* Параметры сценария */}
        <Descriptions title="Параметры сценария" column={2} bordered size="small" style={{ marginBottom: 16 }}>
          <Descriptions.Item label="Изменение штата">
            <Text strong style={{ color: (scenario.headcount_change_percent || 0) >= 0 ? '#52c41a' : '#f5222d' }}>
              {(scenario.headcount_change_percent || 0) >= 0 ? '+' : ''}
              {typeof scenario.headcount_change_percent === 'number' ? scenario.headcount_change_percent.toFixed(1) : '0.0'}%
            </Text>
          </Descriptions.Item>
          <Descriptions.Item label="Изменение зарплат">
            <Text strong style={{ color: (scenario.salary_change_percent || 0) >= 0 ? '#52c41a' : '#f5222d' }}>
              {(scenario.salary_change_percent || 0) >= 0 ? '+' : ''}
              {typeof scenario.salary_change_percent === 'number' ? scenario.salary_change_percent.toFixed(1) : '0.0'}%
            </Text>
          </Descriptions.Item>
        </Descriptions>

        {/* Страховые взносы */}
        {insuranceRates.length > 0 && (
          <>
            <Divider  mobileLayout="card" />
            <Alert
              message="Ставки страховых взносов берутся из справочника"
              description={`Ставки для ${scenario.target_year} года загружаются из справочника страховых взносов. Для изменения ставок используйте раздел управления ставками.`}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
             mobileLayout="card" />
            <Descriptions title={`Ставки страховых взносов (${scenario.target_year} год)`} column={2} bordered size="small" style={{ marginBottom: 16 }}>
              {(() => {
                // Фильтруем дубликаты - оставляем только одну ставку для каждого типа
                // Приоритет: ставки для департамента, затем глобальные
                const uniqueRates = insuranceRates.reduce((acc, rate) => {
                  const existing = acc.find(r => r.tax_type === rate.tax_type);
                  if (!existing) {
                    acc.push(rate);
                  } else if (rate.department_id && !existing.department_id) {
                    // Заменяем глобальную ставку на ставку для департамента
                    const index = acc.indexOf(existing);
                    acc[index] = rate;
                  }
                  return acc;
                }, [] as TaxRateListItem[]);
                
                const rateTypeLabels: Record<string, string> = {
                  PENSION_FUND: 'ПФР',
                  MEDICAL_INSURANCE: 'ФОМС',
                  SOCIAL_INSURANCE: 'ФСС',
                  INJURY_INSURANCE: 'Травматизм',
                  INCOME_TAX: 'НДФЛ',
                };
                
                // Фильтруем только страховые взносы (без НДФЛ)
                const insuranceTypes = ['PENSION_FUND', 'MEDICAL_INSURANCE', 'SOCIAL_INSURANCE', 'INJURY_INSURANCE'];
                const filteredRates = uniqueRates.filter(r => insuranceTypes.includes(r.tax_type));
                
                return filteredRates.map((rate) => {
                  const baseRate = baseYearInsuranceRates.find(r => r.tax_type === rate.tax_type);
                  const ratePercent = (rate.rate * 100).toFixed(2);
                  const baseRatePercent = baseRate ? (baseRate.rate * 100).toFixed(2) : null;
                  const change = baseRate ? ((rate.rate - baseRate.rate) * 100) : 0;
                  return (
                    <Descriptions.Item key={rate.id} label={rateTypeLabels[rate.tax_type] || rate.tax_type} span={2}>
                      <Space>
                        {baseRatePercent && (
                          <>
                            <Tag>{baseRatePercent}%</Tag>
                            <Text>→</Text>
                          < mobileLayout="card" />
                        )}
                        <Tag color={change > 0 ? 'volcano' : change < 0 ? 'green' : 'default'}>
                          {ratePercent}%
                        </Tag>
                        {change !== 0 && (
                          <Tag color={change > 0 ? 'red' : 'green'}>
                            {change > 0 ? '+' : ''}{change.toFixed(2)} п.п.
                          </Tag>
                        )}
                      </Space>
                    </Descriptions.Item>
                  );
                });
              })()}
            </Descriptions>
          < mobileLayout="card" />
        )}
        {insuranceRates.length === 0 && scenario.target_year && (
          <>
            <Divider  mobileLayout="card" />
            <Alert
              message="Ставки страховых взносов не найдены"
              description={`Ставки для ${scenario.target_year} года отсутствуют в справочнике. Будут использованы значения по умолчанию (ПФР: 22%, ФОМС: 5.1%, ФСС: 2.9%, Травматизм: 0.2%).`}
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
             mobileLayout="card" />
          < mobileLayout="card" />
        )}

        <Divider  mobileLayout="card" />

        {/* Key Statistics */}
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Численность"
                value={scenario.total_headcount}
                prefix={<UserOutlined />}
                suffix="чел."
               mobileLayout="card" />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Годовой ФОТ"
                value={scenario.total_base_salary}
                prefix={<DollarOutlined />}
                formatter={(value) => formatCurrency(Number(value))}
               mobileLayout="card" />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Страховые взносы"
                value={scenario.total_insurance_cost}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ color: '#1890ff' }}
               mobileLayout="card" />
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card>
              <Statistic
                title="Общая стоимость"
                value={scenario.total_payroll_cost}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ color: '#52c41a' }}
               mobileLayout="card" />
            </Card>
          </Col>
        </Row>

        {/* Comparison with Base Year */}
        {scenario.base_year_total_cost && (
          <>
            <Divider  mobileLayout="card" />
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12}>
                <Card>
                  <Statistic
                    title={`Базовый год (${scenario.base_year})`}
                    value={scenario.base_year_total_cost}
                    formatter={(value) => formatCurrency(Number(value))}
                   mobileLayout="card" />
                </Card>
              </Col>
              <Col xs={24} sm={12}>
                <Card>
                  <Statistic
                    title="Изменение"
                    value={scenario.cost_difference}
                    formatter={(value) => formatCurrency(Number(value))}
                    valueStyle={{ color: (scenario.cost_difference || 0) >= 0 ? '#52c41a' : '#f5222d' }}
                    prefix={(scenario.cost_difference || 0) >= 0 ? <RiseOutlined /> : <FallOutlined />}
                   mobileLayout="card" />
                  <div style={{ marginTop: 8 }}>
                    {formatPercent(scenario.cost_difference_percent)}
                  </div>
                </Card>
              </Col>
            </Row>
          < mobileLayout="card" />
        )}
      </Card>

      {/* Tabs: Employee Details & What-If Analysis */}
      <Tabs
        defaultActiveKey="employees"
        items={[
          {
            key: 'employees',
            label: (
              <span>
                <TableOutlined  mobileLayout="card" />
                Детализация по сотрудникам
              </span>
            ),
            children: (
              <Card
                title={
                  <Space>
                    <Text strong>Детализация по сотрудникам</Text>
                    <Tag color="blue">{scenario.scenario_details?.length || 0} записей</Tag>
                  </Space>
                }
              >
                <ResponsiveTable
                  columns={columns}
                  dataSource={scenario.scenario_details || []}
                  rowKey="id"
                  scroll={{ x: 1800 }}
                  pagination={{
                    pageSize: 20,
                    showSizeChanger: true,
                    showTotal: (total) => `Всего: ${total} записей`,
                  }}
                  summary={(data) => {
                    // ИСПРАВЛЕНО: Учитываем все виды премий
                    const totalSalary = data.reduce((sum, record) => {
                      const months_worked = record.is_terminated && record.termination_month
                        ? record.termination_month
                        : 12;
                      const monthly_total = (record.base_salary + record.monthly_bonus) * months_worked;
                      const quarterly_total = (record.quarterly_bonus || 0) * 4;
                      const annual_total = record.annual_bonus || 0;
                      return sum + monthly_total + quarterly_total + annual_total;
                    }, 0);
                    const totalPension = data.reduce((sum, record) => sum + (record.pension_contribution || 0), 0);
                    const totalMedical = data.reduce((sum, record) => sum + (record.medical_contribution || 0), 0);
                    const totalSocial = data.reduce((sum, record) => sum + (record.social_contribution || 0), 0);
                    const totalInjury = data.reduce((sum, record) => sum + (record.injury_contribution || 0), 0);
                    const totalInsurance = data.reduce((sum, record) => sum + (record.total_insurance || 0), 0);
                    const totalTax = data.reduce((sum, record) => sum + (record.income_tax || 0), 0);
                    const totalCost = data.reduce((sum, record) => sum + (record.total_employee_cost || 0), 0);
                    const totalIncrease = data.reduce((sum, record) => sum + (record.cost_increase || 0), 0);

                    return (
                      <Table.Summary fixed>
                        <Table.Summary.Row style={{ backgroundColor: '#fafafa', fontWeight: 'bold' }}>
                          <Table.Summary.Cell index={0}>ИТОГО</Table.Summary.Cell>
                          <Table.Summary.Cell index={1} align="right">—</Table.Summary.Cell>
                          <Table.Summary.Cell index={2} align="right">—</Table.Summary.Cell>
                          <Table.Summary.Cell index={3} align="right">
                            <Text strong>{formatCurrency(totalSalary)}</Text>
                          </Table.Summary.Cell>
                          <Table.Summary.Cell index={4} align="right">{formatCurrency(totalPension)}</Table.Summary.Cell>
                          <Table.Summary.Cell index={5} align="right">{formatCurrency(totalMedical)}</Table.Summary.Cell>
                          <Table.Summary.Cell index={6} align="right">{formatCurrency(totalSocial)}</Table.Summary.Cell>
                          <Table.Summary.Cell index={7} align="right">{formatCurrency(totalInjury)}</Table.Summary.Cell>
                          <Table.Summary.Cell index={8} align="right">
                            <Text strong style={{ color: '#1890ff' }}>{formatCurrency(totalInsurance)}</Text>
                          </Table.Summary.Cell>
                          <Table.Summary.Cell index={9} align="right">{formatCurrency(totalTax)}</Table.Summary.Cell>
                          <Table.Summary.Cell index={10} align="right">
                            <Text strong style={{ color: '#52c41a', fontSize: 14 }}>{formatCurrency(totalCost)}</Text>
                          </Table.Summary.Cell>
                          <Table.Summary.Cell index={11} align="right">
                            <Text style={{ color: totalIncrease >= 0 ? '#52c41a' : '#f5222d' }}>
                              {formatCurrency(Math.abs(totalIncrease))}
                            </Text>
                          </Table.Summary.Cell>
                        </Table.Summary.Row>
                      </Table.Summary>
                    );
                  }}
                 mobileLayout="card" />
              </Card>
            ),
          },
          {
            key: 'what-if',
            label: (
              <span>
                <ExperimentOutlined  mobileLayout="card" />
                What-If Анализ
              </span>
            ),
            children: (() => {
              const mappedRates = insuranceRates.map(rate => ({
                rate_type: rate.tax_type,
                rate_percentage: rate.rate * 100, // Convert decimal to percentage
              }));

              console.log('Rendering PayrollWhatIfAnalysis with:');
              console.log('- scenarioId:', scenario.id);
              console.log('- headcount_change_percent:', scenario.headcount_change_percent);
              console.log('- salary_change_percent:', scenario.salary_change_percent);
              console.log('- insuranceRates (mapped):', mappedRates);

              return (
                <PayrollWhatIfAnalysis
                  scenarioId={scenario.id}
                  baseScenario={{
                    total_headcount: scenario.total_headcount || 0,
                    total_base_salary: scenario.total_base_salary || 0,
                    total_insurance_cost: scenario.total_insurance_cost || 0,
                    total_payroll_cost: scenario.total_payroll_cost || 0,
                    headcount_change_percent: scenario.headcount_change_percent || 0,
                    salary_change_percent: scenario.salary_change_percent || 0,
                    base_year_total_cost: scenario.base_year_total_cost,
                    base_year: scenario.base_year,
                    scenario_details: scenario.scenario_details || [],
                  }}
                  insuranceRates={mappedRates}
                  onApplyChanges={async (params) => {
                    console.log('onApplyChanges called with params:', params);

                    // ВАЖНО: Пересчитываем проценты относительно БАЗОВОГО ГОДА (=API ожидает)
                    // Пользователь меняет параметры относительно ТЕКУЩЕГО сценария (target).
                    // 1) Отталкиваемся от базового года и применяем уже текущие проценты сценария.
                    // 2) Затем накладываем сдвиг What-If (params.*) поверх текущего сценария.

                    // Сохраняем выбранные ставки в справочник, чтобы серверный расчет их учел
                    await upsertWhatIfTaxRates(params);

                    // 1. Данные базового года
                    const baseYearEmployees = (scenario.scenario_details || []).filter(
                      (d) => d.base_year_salary && d.base_year_salary > 0
                    );
                    const baseYearHeadcount = baseYearEmployees.length;
                    const currentHeadcountMultiplierFromBase = 1 + (scenario.headcount_change_percent || 0) / 100;
                    const currentSalaryMultiplierFromBase = 1 + (scenario.salary_change_percent || 0) / 100;

                    // 2. Применяем What-If поверх текущего сценария
                    const newHeadcountMultiplierFromBase =
                      currentHeadcountMultiplierFromBase * (1 + params.headcountChangePercent / 100);
                    const newSalaryMultiplierFromBase =
                      currentSalaryMultiplierFromBase * (1 + params.salaryChangePercent / 100);

                    // Численность и зарплаты для вычисления процентов к базовому году
                    const overallHeadcountChangePercent =
                      baseYearHeadcount > 0 ? (newHeadcountMultiplierFromBase - 1) * 100 : 0;
                    const overallSalaryChangePercent = (newSalaryMultiplierFromBase - 1) * 100;

                    console.log('Overall change (relative to base year):', {
                      overallHeadcountChangePercent,
                      overallSalaryChangePercent,
                    });

                    console.log('Sending to API:', {
                      headcount_change_percent: overallHeadcountChangePercent,
                      salary_change_percent: overallSalaryChangePercent,
                    });

                    // Применяем изменения к сценарию
                    updateMutation.mutate({
                      headcount_change_percent: overallHeadcountChangePercent,
                      salary_change_percent: overallSalaryChangePercent,
                    });
                  }}
               mobileLayout="card" />
              );
            })(),
          },
          {
            key: 'charts',
            label: (
              <span>
                <BarChartOutlined  mobileLayout="card" />
                Графики и аналитика
              </span>
            ),
            children: <PayrollScenarioCharts scenario={scenario} />,
          },
        ]}
       mobileLayout="card" />

      {/* Модальное окно редактирования параметров */}
      <Modal
        title="Редактировать параметры сценария"
        open={isEditModalOpen}
        onCancel={() => setEditModalOpen(false)}
        onOk={() => form.submit()}
        confirmLoading={updateMutation.isPending}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEditSubmit}
        >
          <Form.Item
            name="headcount_change_percent"
            label="Изменение штата (%)"
            tooltip="Положительное число - рост штата, отрицательное - сокращение"
            rules={[
              { required: true, message: 'Введите изменение штата' },
              { type: 'number', min: -100, max: 100, message: 'Значение должно быть от -100 до 100' },
            ]}
          >
            <InputNumber
              min={-100}
              max={100}
              step={0.1}
              style={{ width: '100%' }}
              formatter={(value) => `${value}%`}
              parser={(value) => Number(value?.replace('%', '') || 0) as any}
             mobileLayout="card" />
          </Form.Item>

          <Form.Item
            name="salary_change_percent"
            label="Изменение зарплат (%)"
            tooltip="Положительное число - рост зарплат, отрицательное - снижение"
            rules={[
              { required: true, message: 'Введите изменение зарплат' },
              { type: 'number', min: -100, max: 100, message: 'Значение должно быть от -100 до 100' },
            ]}
          >
            <InputNumber
              min={-100}
              max={100}
              step={0.1}
              style={{ width: '100%' }}
              formatter={(value) => `${value}%`}
              parser={(value) => Number(value?.replace('%', '') || 0) as any}
             mobileLayout="card" />
          </Form.Item>

          <Alert
            message="После изменения параметров необходимо пересчитать сценарий"
            type="info"
            showIcon
            style={{ marginTop: 16 }}
           mobileLayout="card" />
        </Form>
      </Modal>
    </div>
  );
};

export default PayrollScenarioDetailPage;
