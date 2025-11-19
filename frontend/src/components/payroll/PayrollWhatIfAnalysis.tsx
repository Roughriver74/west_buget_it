/**
 * PayrollWhatIfAnalysis - Интерактивный what-if анализ для сценариев ФОТ
 *
 * Позволяет динамически изменять параметры и видеть результаты в реальном времени:
 * - Изменение штата (headcount)
 * - Изменение зарплат (salary)
 * - Ставки страховых взносов (ПФР, ФОМС, ФСС, Травматизм)
 * - Ставка НДФЛ
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Slider,
  InputNumber,
  Statistic,
  Space,
  Typography,
  Divider,
  Alert,
  Button,
  message,
} from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  UserOutlined,
  SaveOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

interface InsuranceRate {
  rate_type: string;
  rate_percentage: number;
}

interface WhatIfParams {
  headcountChangePercent: number;
  salaryChangePercent: number;
  pensionRate: number;
  medicalRate: number;
  socialRate: number;
  injuryRate: number;
  incomeTaxRate: number;
}

interface WhatIfResults {
  totalHeadcount: number;
  totalBaseSalary: number;
  totalInsuranceCost: number;
  totalIncomeTax: number;
  totalPayrollCost: number;
  costDifference: number;
  costDifferencePercent: number;
}

interface PayrollWhatIfAnalysisProps {
  scenarioId: number;
  baseScenario: {
    total_headcount: number;
    total_base_salary: number;
    total_insurance_cost: number;
    total_payroll_cost: number;
    headcount_change_percent: number;
    salary_change_percent: number;
    base_year_total_cost?: number;
    base_year?: number;
    scenario_details?: Array<{
      base_year_salary?: number;
      [key: string]: any;
    }>;
  };
  insuranceRates: InsuranceRate[];
  onApplyChanges?: (params: WhatIfParams) => void;
}

export const PayrollWhatIfAnalysis: React.FC<PayrollWhatIfAnalysisProps> = ({
  scenarioId: _scenarioId,
  baseScenario,
  insuranceRates,
  onApplyChanges,
}) => {
  // Извлекаем текущие ставки из справочника
  const getRate = (type: string, defaultRate: number) => {
    const rate = insuranceRates.find(r => r.rate_type === type);
    return rate ? rate.rate_percentage : defaultRate;
  };

  // ВАЖНО: What-If всегда начинается с 0% (без изменений от текущего сценария)
  // baseScenario.headcount_change_percent - это % относительно БАЗОВОГО ГОДА, а не текущего сценария
  const [params, setParams] = useState<WhatIfParams>({
    headcountChangePercent: 0,  // Нет изменений от текущего сценария
    salaryChangePercent: 0,     // Нет изменений от текущего сценария
    pensionRate: 22, // Временные дефолты, обновятся из справочника
    medicalRate: 5.1,
    socialRate: 2.9,
    injuryRate: 0.2,
    incomeTaxRate: 13,
  });

  // Результаты расчета
  const [results, setResults] = useState<WhatIfResults | null>(null);

  // Обновляем ставки страховых взносов из справочника после загрузки
  useEffect(() => {
    if (insuranceRates && insuranceRates.length > 0) {
      setParams(prev => ({
        ...prev,
        pensionRate: getRate('PENSION_FUND', 22),
        medicalRate: getRate('MEDICAL_INSURANCE', 5.1),
        socialRate: getRate('SOCIAL_INSURANCE', 2.9),
        injuryRate: getRate('INJURY_INSURANCE', 0.2),
      }));
    }
  }, [insuranceRates]);

  // ВАЖНО: НЕ синхронизируем headcountChangePercent/salaryChangePercent с baseScenario!
  // What-If работает относительно ТЕКУЩЕГО сценария, поэтому начальные значения всегда 0%
  // (без изменений от текущего сценария). Параметры сценария (baseScenario.headcount_change_percent)
  // - это проценты относительно БАЗОВОГО ГОДА, а не текущего сценария.

  // После применения What-If сценарий пересчитывается и baseScenario обновляется.
  // Когда приходят новые данные сценария, сбрасываем контролы к нулю,
  // чтобы нижняя панель снова отражала актуальные цифры из основного сценария.
  useEffect(() => {
    resetParamsToCurrentScenario(false);
  }, [
    _scenarioId,
    baseScenario.total_headcount,
    baseScenario.total_base_salary,
    baseScenario.total_insurance_cost,
    baseScenario.total_payroll_cost,
  ]);

  // ВАЖНО: What-If анализ работает от ТЕКУЩИХ данных целевого года (2026),
  // а не от базового года (2025). Пользователь видит текущий сценарий и моделирует изменения от него.
  const currentScenarioData = useMemo(() => {
    console.log('🔍 currentScenarioData calculation (ЦЕЛЕВОЙ ГОД)');
    console.log('baseScenario:', baseScenario);

    // Используем ТЕКУЩИЕ данные целевого года как отправную точку
    const result = {
      headcount: baseScenario.total_headcount || 0,
      totalSalary: baseScenario.total_base_salary || 0,
      totalInsurance: baseScenario.total_insurance_cost || 0,
      totalCost: baseScenario.total_payroll_cost || 0,
      // Для сравнения сохраняем данные базового года
      baseYearCost: baseScenario.base_year_total_cost || 0,
    };
    console.log('✅ Using CURRENT scenario data (target year):', result);
    return result;
  }, [
    baseScenario.total_headcount,
    baseScenario.total_base_salary,
    baseScenario.total_insurance_cost,
    baseScenario.total_payroll_cost,
    baseScenario.base_year_total_cost,
  ]);

  // Функция локального пересчета (без вызова API)
  const calculateResults = (currentParams: WhatIfParams): WhatIfResults => {
    console.log('💰 calculateResults called');
    console.log('currentParams:', currentParams);
    console.log('currentScenarioData:', currentScenarioData);

    // ВАЖНО: Используем данные ТЕКУЩЕГО СЦЕНАРИЯ (целевой год 2026) как базу для What-If
    const baseHeadcount = currentScenarioData.headcount;
    const baseAnnualSalary = currentScenarioData.totalSalary;
    console.log('baseHeadcount:', baseHeadcount, 'baseAnnualSalary:', baseAnnualSalary);

    // Применяем изменения от текущего состояния
    const headcountMultiplier = 1 + (currentParams.headcountChangePercent / 100);
    const salaryMultiplier = 1 + (currentParams.salaryChangePercent / 100);

    const newHeadcount = Math.round(baseHeadcount * headcountMultiplier);
    const newBaseSalary = baseAnnualSalary * headcountMultiplier * salaryMultiplier;

    // Рассчитываем страховые взносы
    const totalInsuranceRate =
      currentParams.pensionRate +
      currentParams.medicalRate +
      currentParams.socialRate +
      currentParams.injuryRate;

    const insuranceCost = newBaseSalary * (totalInsuranceRate / 100);

    // Рассчитываем НДФЛ (13% от зарплаты)
    const incomeTax = newBaseSalary * (currentParams.incomeTaxRate / 100);

    // Общая стоимость = Зарплата + Страховые взносы (как в расчете сценария на бэке)
    // НДФЛ показываем отдельно, но не включаем в итог, чтобы цифры совпадали с карточками сценария
    const totalCost = newBaseSalary + insuranceCost;

    // Сравнение с ТЕКУЩИМ сценарием (до What-If изменений)
    const baseCost = currentScenarioData.totalCost;
    const costDifference = totalCost - baseCost;
    const costDifferencePercent = baseCost > 0 ? (costDifference / baseCost) * 100 : 0;

    return {
      totalHeadcount: newHeadcount,
      totalBaseSalary: newBaseSalary,
      totalInsuranceCost: insuranceCost,
      totalIncomeTax: incomeTax,
      totalPayrollCost: totalCost,
      costDifference,
      costDifferencePercent,
    };
  };

  // Пересчитываем при изменении параметров или базового сценария
  useEffect(() => {
    const newResults = calculateResults(params);
    setResults(newResults);
  }, [params, baseScenario]);

  const handleParamChange = (key: keyof WhatIfParams, value: number) => {
    setParams(prev => ({ ...prev, [key]: value }));
  };

  const resetParamsToCurrentScenario = (showMessage = true) => {
    // ВАЖНО: Сбрасываем к НУЛЮ (без изменений от текущего сценария)
    // baseScenario.headcount_change_percent - это % относительно БАЗОВОГО ГОДА
    // А What-If работает относительно ТЕКУЩЕГО сценария, поэтому сброс = 0%
    setParams({
      headcountChangePercent: 0,  // Нет изменений от текущего сценария
      salaryChangePercent: 0,     // Нет изменений от текущего сценария
      pensionRate: getRate('PENSION_FUND', 22),
      medicalRate: getRate('MEDICAL_INSURANCE', 5.1),
      socialRate: getRate('SOCIAL_INSURANCE', 2.9),
      injuryRate: getRate('INJURY_INSURANCE', 0.2),
      incomeTaxRate: 13,
    });

    if (showMessage) {
      message.info('Параметры сброшены к текущему сценарию (без изменений)');
    }
  };

  const handleReset = () => {
    resetParamsToCurrentScenario(true);
  };

  const handleApply = async () => {
    if (onApplyChanges) {
      console.log('Applying what-if changes:', params);
      try {
        await onApplyChanges(params);
        message.success('Параметры применены к сценарию. Идет пересчет...');
      } catch (error) {
        console.error('Failed to apply what-if changes', error);
        message.error('Не удалось применить параметры What-If');
      }
    } else {
      message.error('Callback onApplyChanges не определен');
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercent = (value: number) => {
    const color = value >= 0 ? '#52c41a' : '#f5222d';
    const icon = value >= 0 ? <RiseOutlined /> : <FallOutlined />;
    return (
      <Text style={{ color }}>
        {icon} {value.toFixed(2)}%
      </Text>
    );
  };

  return (
    <Card
      title={
        <Space>
          <Title level={4} style={{ margin: 0 }}>What-If Анализ</Title>
          <Text type="secondary">(Интерактивное моделирование)</Text>
        </Space>
      }
      extra={
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleReset}>
            Сбросить
          </Button>
          <Button type="primary" icon={<SaveOutlined />} onClick={handleApply}>
            Применить к сценарию
          </Button>
        </Space>
      }
    >
      <Alert
        message="Динамическое моделирование"
        description="Изменяйте параметры относительно ТЕКУЩЕГО сценария и наблюдайте за результатами в реальном времени. Кнопка 'Сбросить' вернет к параметрам текущего сценария. Кнопка 'Применить к сценарию' перенесет ВСЕ изменения (штат, зарплаты, страховые взносы) в основной сценарий."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={[24, 24]}>
        {/* Левая панель - Параметры */}
        <Col xs={24} lg={12}>
          <Card title="Параметры моделирования" size="small">
            {/* Штат */}
            <div style={{ marginBottom: 24 }}>
              <Text strong>Изменение штата (%)</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={-100}
                    max={100}
                    step={1}
                    value={params.headcountChangePercent}
                    onChange={(value) => handleParamChange('headcountChangePercent', value)}
                    marks={{
                      '-100': '-100%',
                      '0': '0%',
                      '100': '+100%',
                    }}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={-100}
                    max={100}
                    step={0.1}
                    value={params.headcountChangePercent}
                    onChange={(value) => handleParamChange('headcountChangePercent', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>

            {/* Зарплаты */}
            <div style={{ marginBottom: 24 }}>
              <Text strong>Изменение зарплат (%)</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={-100}
                    max={100}
                    step={1}
                    value={params.salaryChangePercent}
                    onChange={(value) => handleParamChange('salaryChangePercent', value)}
                    marks={{
                      '-100': '-100%',
                      '0': '0%',
                      '100': '+100%',
                    }}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={-100}
                    max={100}
                    step={0.1}
                    value={params.salaryChangePercent}
                    onChange={(value) => handleParamChange('salaryChangePercent', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>

            <Divider />

            {/* Страховые взносы */}
            <Text strong style={{ display: 'block', marginBottom: 16 }}>Ставки страховых взносов (%)</Text>

            {/* ПФР */}
            <div style={{ marginBottom: 16 }}>
              <Text>ПФР (Пенсионный фонд)</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={0}
                    max={50}
                    step={0.1}
                    value={params.pensionRate}
                    onChange={(value) => handleParamChange('pensionRate', value)}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={0}
                    max={50}
                    step={0.1}
                    value={params.pensionRate}
                    onChange={(value) => handleParamChange('pensionRate', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>

            {/* ФОМС */}
            <div style={{ marginBottom: 16 }}>
              <Text>ФОМС (Медицинское страхование)</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={0}
                    max={20}
                    step={0.1}
                    value={params.medicalRate}
                    onChange={(value) => handleParamChange('medicalRate', value)}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={0}
                    max={20}
                    step={0.1}
                    value={params.medicalRate}
                    onChange={(value) => handleParamChange('medicalRate', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>

            {/* ФСС */}
            <div style={{ marginBottom: 16 }}>
              <Text>ФСС (Социальное страхование)</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={0}
                    max={20}
                    step={0.1}
                    value={params.socialRate}
                    onChange={(value) => handleParamChange('socialRate', value)}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={0}
                    max={20}
                    step={0.1}
                    value={params.socialRate}
                    onChange={(value) => handleParamChange('socialRate', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>

            {/* Травматизм */}
            <div style={{ marginBottom: 16 }}>
              <Text>Травматизм</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={0}
                    max={10}
                    step={0.1}
                    value={params.injuryRate}
                    onChange={(value) => handleParamChange('injuryRate', value)}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={0}
                    max={10}
                    step={0.1}
                    value={params.injuryRate}
                    onChange={(value) => handleParamChange('injuryRate', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>

            <Divider />

            {/* НДФЛ */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>Ставка НДФЛ (%)</Text>
              <Row gutter={16} align="middle" style={{ marginTop: 8 }}>
                <Col flex="auto">
                  <Slider
                    min={0}
                    max={30}
                    step={1}
                    value={params.incomeTaxRate}
                    onChange={(value) => handleParamChange('incomeTaxRate', value)}
                    marks={{
                      '13': '13%',
                      '15': '15%',
                    }}
                  />
                </Col>
                <Col>
                  <InputNumber
                    min={0}
                    max={30}
                    step={0.1}
                    value={params.incomeTaxRate}
                    onChange={(value) => handleParamChange('incomeTaxRate', value || 0)}
                    formatter={(value) => `${value}%`}
                    parser={(value) => Number(value?.replace('%', '') || 0)}
                    style={{ width: 100 }}
                  />
                </Col>
              </Row>
            </div>
          </Card>
        </Col>

        {/* Правая панель - Результаты */}
        <Col xs={24} lg={12}>
          <Card title="Результаты расчета" size="small">
            {results && (
              <>
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={12}>
                    <Card>
                      <Statistic
                        title="Численность"
                        value={results.totalHeadcount}
                        prefix={<UserOutlined />}
                        suffix="чел."
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Текущий сценарий: {currentScenarioData.headcount} чел.
                      </Text>
                    </Card>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Card>
                      <Statistic
                        title="Годовой ФОТ"
                        value={results.totalBaseSalary}
                        prefix={<DollarOutlined />}
                        formatter={(value) => formatCurrency(Number(value))}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Текущий сценарий: {formatCurrency(currentScenarioData.totalSalary)}
                      </Text>
                    </Card>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Card>
                      <Statistic
                        title="Страховые взносы"
                        value={results.totalInsuranceCost}
                        formatter={(value) => formatCurrency(Number(value))}
                        valueStyle={{ color: '#1890ff' }}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Общая ставка: {(params.pensionRate + params.medicalRate + params.socialRate + params.injuryRate).toFixed(2)}%
                      </Text>
                    </Card>
                  </Col>
                  <Col xs={24} sm={12}>
                    <Card>
                      <Statistic
                        title="НДФЛ"
                        value={results.totalIncomeTax}
                        formatter={(value) => formatCurrency(Number(value))}
                        valueStyle={{ color: '#722ed1' }}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Ставка: {params.incomeTaxRate}%
                      </Text>
                    </Card>
                  </Col>
                  <Col span={24}>
                    <Card style={{ backgroundColor: '#f0f2f5' }}>
                      <Statistic
                        title="Общая стоимость ФОТ"
                        value={results.totalPayrollCost}
                        formatter={(value) => formatCurrency(Number(value))}
                        valueStyle={{ color: '#52c41a', fontSize: 24 }}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        Текущий сценарий: {formatCurrency(currentScenarioData.totalCost)}
                      </Text>
                    </Card>
                  </Col>
                  <Col span={24}>
                    <Card>
                      <Statistic
                        title="Изменение относительно текущего сценария"
                        value={results.costDifference}
                        formatter={(value) => formatCurrency(Number(value))}
                        valueStyle={{ color: results.costDifference >= 0 ? '#f5222d' : '#52c41a' }}
                        prefix={results.costDifference >= 0 ? <RiseOutlined /> : <FallOutlined />}
                      />
                      <div style={{ marginTop: 8 }}>
                        {formatPercent(results.costDifferencePercent)}
                      </div>
                    </Card>
                  </Col>
                </Row>

                <Divider />

                {/* Разбивка страховых взносов */}
                <div style={{ marginTop: 16 }}>
                  <Text strong style={{ display: 'block', marginBottom: 8 }}>Детализация страховых взносов:</Text>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Row justify="space-between">
                      <Text>ПФР ({params.pensionRate}%):</Text>
                      <Text strong>{formatCurrency(results.totalBaseSalary * (params.pensionRate / 100))}</Text>
                    </Row>
                    <Row justify="space-between">
                      <Text>ФОМС ({params.medicalRate}%):</Text>
                      <Text strong>{formatCurrency(results.totalBaseSalary * (params.medicalRate / 100))}</Text>
                    </Row>
                    <Row justify="space-between">
                      <Text>ФСС ({params.socialRate}%):</Text>
                      <Text strong>{formatCurrency(results.totalBaseSalary * (params.socialRate / 100))}</Text>
                    </Row>
                    <Row justify="space-between">
                      <Text>Травматизм ({params.injuryRate}%):</Text>
                      <Text strong>{formatCurrency(results.totalBaseSalary * (params.injuryRate / 100))}</Text>
                    </Row>
                  </Space>
                </div>
              </>
            )}
          </Card>
        </Col>
      </Row>
    </Card>
  );
};

export default PayrollWhatIfAnalysis;
