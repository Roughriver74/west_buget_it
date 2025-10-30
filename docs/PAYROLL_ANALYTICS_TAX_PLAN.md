# Payroll Analytics - Tax Enhancement Plan

## Проблема
PayrollAnalyticsPage существует, но не показывает налоги (НДФЛ, страховые взносы) и недостаточно графиков для анализа налоговой нагрузки.

## Текущее состояние

### Backend (`backend/app/api/v1/payroll.py`)
Существующие analytics endpoints:
- `GET /api/v1/payroll/analytics/salary-stats` - статистика зарплат
- `GET /api/v1/payroll/analytics/structure` - структура ФОТ
- `GET /api/v1/payroll/analytics/dynamics` - динамика ФОТ
- `GET /api/v1/payroll/analytics/forecast` - прогноз ФОТ

Существующие налоговые утилиты:
- `backend/app/utils/ndfl_calculator.py`:
  - `calculate_progressive_ndfl(annual_income, year)` - расчет НДФЛ
  - `calculate_monthly_ndfl_withholding(monthly_income, ytd_income, month, year)` - удержание за месяц
  - `get_tax_brackets_info(year)` - информация о ставках

### Frontend (`frontend/src/pages/PayrollAnalyticsPage.tsx`)
**Размер**: ~22KB (~600 строк)

**Существующие данные**:
- salaryStats: общая статистика
- structure: структура по типам выплат (base, bonus, etc.)
- dynamics: динамика по месяцам
- forecast: прогноз на 6 месяцев

**Существующие графики**:
- LineChart: динамика ФОТ
- BarChart: структура ФОТ
- AreaChart: прогноз
- PieChart: распределение

**Отсутствует**:
- Налоговые расчеты (НДФЛ, страховые взносы)
- Waterfall chart для декомпозиции затрат
- Tax burden analysis

## План реализации

### Фаза 1: Backend - Utility для страховых взносов

#### Создать `backend/app/utils/social_contributions_calculator.py`

**Страховые взносы 2024-2025**:
- **ПФР (Пенсионный фонд)**: 22% до 1 917 000 ₽, 10% сверху
- **ФОМС (Медицинское страхование)**: 5.1% до 1 917 000 ₽
- **ФСС (Социальное страхование)**: 2.9% до 1 032 000 ₽

**Функции**:
```python
def calculate_social_contributions(
    annual_income: Decimal,
    year: int = None
) -> Dict[str, any]:
    """
    Calculate social contributions (ПФР, ФОМС, ФСС)

    Returns:
        {
            'pfr': {
                'base_rate': 0.22,
                'over_limit_rate': 0.10,
                'limit': 1917000,
                'total': amount
            },
            'foms': {
                'rate': 0.051,
                'limit': 1917000,
                'total': amount
            },
            'fss': {
                'rate': 0.029,
                'limit': 1032000,
                'total': amount
            },
            'total_contributions': total,
            'effective_rate': percentage
        }
    """
    pass


def calculate_total_tax_burden(
    annual_income: Decimal,
    year: int = None
) -> Dict[str, any]:
    """
    Calculate total tax burden: NDFL + social contributions

    Returns:
        {
            'ndfl': {...},  # from calculate_progressive_ndfl
            'social_contributions': {...},  # from calculate_social_contributions
            'gross_income': amount,
            'net_income': amount,
            'total_taxes': amount,
            'effective_tax_rate': percentage,
            'breakdown': [...]
        }
    """
    pass
```

---

### Фаза 2: Backend - New Analytics Endpoints

#### 1. `GET /api/v1/payroll/analytics/tax-burden`

**Параметры**:
- `year`: int (required)
- `month`: int (optional)
- `department_id`: int (optional)
- `employee_id`: int (optional)

**Ответ**:
```json
{
  "period": "2025-01",
  "gross_payroll": 5000000,
  "ndfl": {
    "total": 650000,
    "effective_rate": 13.0,
    "breakdown": [...]
  },
  "social_contributions": {
    "pfr": 1100000,
    "foms": 255000,
    "fss": 145000,
    "total": 1500000
  },
  "net_payroll": 4350000,
  "total_tax_burden": 2150000,
  "effective_burden_rate": 30.0,
  "employer_cost": 6500000
}
```

**Логика**:
1. Получить все PayrollActual за период
2. Суммировать total_paid (gross)
3. Для каждого сотрудника:
   - Рассчитать НДФЛ через `calculate_progressive_ndfl`
   - Рассчитать взносы через `calculate_social_contributions`
4. Агрегировать результаты

---

#### 2. `GET /api/v1/payroll/analytics/tax-breakdown-by-month`

**Параметры**:
- `year`: int (required)
- `department_id`: int (optional)

**Ответ**:
```json
[
  {
    "month": 1,
    "month_name": "Январь",
    "gross_payroll": 5000000,
    "ndfl": 650000,
    "pfr": 1100000,
    "foms": 255000,
    "fss": 145000,
    "total_taxes": 2150000,
    "net_payroll": 4350000,
    "employer_cost": 6500000
  },
  ...
]
```

**Использование**: Stacked area chart, Line chart

---

#### 3. `GET /api/v1/payroll/analytics/tax-by-employee`

**Параметры**:
- `year`: int (required)
- `month`: int (optional)
- `department_id`: int (optional)

**Ответ**:
```json
[
  {
    "employee_id": 1,
    "employee_name": "Иванов И.И.",
    "position": "Senior Developer",
    "gross_income": 250000,
    "ndfl": 32500,
    "social_contributions": 75000,
    "net_income": 217500,
    "effective_tax_rate": 13.0,
    "effective_burden_rate": 30.0
  },
  ...
]
```

**Использование**: Bar chart, Таблица

---

#### 4. `GET /api/v1/payroll/analytics/cost-waterfall`

**Параметры**:
- `year`: int (required)
- `month`: int (optional)
- `department_id`: int (optional)

**Ответ для Waterfall chart**:
```json
{
  "base_salary": 4000000,
  "monthly_bonus": 500000,
  "quarterly_bonus": 300000,
  "annual_bonus": 200000,
  "gross_total": 5000000,
  "ndfl": -650000,
  "pfr": -1100000,
  "foms": -255000,
  "fss": -145000,
  "net_payroll": 2850000,
  "total_employer_cost": 6500000
}
```

**Waterfall steps**:
1. Base Salary (start)
2. + Monthly Bonus
3. + Quarterly Bonus
4. + Annual Bonus
5. = Gross Total
6. - НДФЛ
7. - ПФР
8. - ФОМС
9. - ФСС
10. = Net Payroll

---

### Фаза 3: Frontend - New Components & Charts

#### 1. Tax Burden Summary Cards

**Добавить в PayrollAnalyticsPage**:
```tsx
<Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
  <Col xs={24} md={6}>
    <Card>
      <Statistic
        title="НДФЛ"
        value={taxData?.ndfl.total}
        formatter={(value) => formatCurrency(value as number)}
        prefix={<DollarOutlined />}
        suffix={`(${taxData?.ndfl.effective_rate.toFixed(1)}%)`}
      />
    </Card>
  </Col>
  <Col xs={24} md={6}>
    <Card>
      <Statistic
        title="Страховые взносы"
        value={taxData?.social_contributions.total}
        formatter={(value) => formatCurrency(value as number)}
        prefix={<TeamOutlined />}
      />
    </Card>
  </Col>
  <Col xs={24} md={6}>
    <Card>
      <Statistic
        title="Общая налоговая нагрузка"
        value={taxData?.total_tax_burden}
        formatter={(value) => formatCurrency(value as number)}
        valueStyle={{ color: '#cf1322' }}
      />
    </Card>
  </Col>
  <Col xs={24} md={6}>
    <Card>
      <Statistic
        title="Эффективная ставка"
        value={taxData?.effective_burden_rate}
        suffix="%"
        precision={1}
        valueStyle={{ color: '#cf1322' }}
      />
    </Card>
  </Col>
</Row>
```

---

#### 2. Waterfall Chart - Cost Breakdown

**Библиотека**: recharts не поддерживает Waterfall напрямую, но можно использовать BarChart с кастомными данными

**Альтернатива**: Использовать **ApexCharts** (лучше для Waterfall)

```tsx
import ReactApexChart from 'react-apexcharts';

const WaterfallChart: React.FC<{ data: any }> = ({ data }) => {
  const series = [{
    name: 'Затраты',
    data: [
      { x: 'Base Salary', y: [0, data.base_salary] },
      { x: 'Bonuses', y: [data.base_salary, data.gross_total] },
      { x: 'НДФЛ', y: [data.gross_total, data.gross_total - data.ndfl] },
      { x: 'ПФР', y: [...] },
      { x: 'ФОМС', y: [...] },
      { x: 'ФСС', y: [...] },
      { x: 'Net', y: [0, data.net_payroll] }
    ]
  }];

  const options = {
    chart: { type: 'rangeBar' },
    plotOptions: {
      bar: { horizontal: false }
    },
    dataLabels: { enabled: true },
    xaxis: { type: 'category' }
  };

  return <ReactApexChart options={options} series={series} type="rangeBar" height={350} />;
};
```

---

#### 3. Stacked Area Chart - Tax + Salary Dynamics

```tsx
<ResponsiveContainer width="100%" height={400}>
  <AreaChart data={monthlyBreakdown}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="month_name" />
    <YAxis tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
    <Tooltip formatter={(value) => formatCurrency(value as number)} />
    <Legend />

    <Area
      type="monotone"
      dataKey="net_payroll"
      stackId="1"
      stroke="#1890ff"
      fill="#1890ff"
      name="Чистая ЗП"
    />
    <Area
      type="monotone"
      dataKey="ndfl"
      stackId="1"
      stroke="#faad14"
      fill="#faad14"
      name="НДФЛ"
    />
    <Area
      type="monotone"
      dataKey="pfr"
      stackId="1"
      stroke="#f5222d"
      fill="#f5222d"
      name="ПФР"
    />
    <Area
      type="monotone"
      dataKey="foms"
      stackId="1"
      stroke="#722ed1"
      fill="#722ed1"
      name="ФОМС"
    />
    <Area
      type="monotone"
      dataKey="fss"
      stackId="1"
      stroke="#13c2c2"
      fill="#13c2c2"
      name="ФСС"
    />
  </AreaChart>
</ResponsiveContainer>
```

---

#### 4. Pie Chart - Tax Distribution

```tsx
const taxDistribution = [
  { name: 'НДФЛ', value: taxData?.ndfl.total, color: '#faad14' },
  { name: 'ПФР', value: taxData?.social_contributions.pfr.total, color: '#f5222d' },
  { name: 'ФОМС', value: taxData?.social_contributions.foms.total, color: '#722ed1' },
  { name: 'ФСС', value: taxData?.social_contributions.fss.total, color: '#13c2c2' },
];

<ResponsiveContainer width="100%" height={400}>
  <PieChart>
    <Pie
      data={taxDistribution}
      cx="50%"
      cy="50%"
      labelLine={false}
      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
      outerRadius={120}
      fill="#8884d8"
      dataKey="value"
    >
      {taxDistribution.map((entry, index) => (
        <Cell key={`cell-${index}`} fill={entry.color} />
      ))}
    </Pie>
    <Tooltip formatter={(value) => formatCurrency(value as number)} />
  </PieChart>
</ResponsiveContainer>
```

---

#### 5. Bar Chart - Tax Burden by Employee/Department

```tsx
<ResponsiveContainer width="100%" height={400}>
  <BarChart data={employeeTaxData}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="employee_name" angle={-45} textAnchor="end" height={100} />
    <YAxis tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`} />
    <Tooltip formatter={(value) => formatCurrency(value as number)} />
    <Legend />

    <Bar dataKey="gross_income" fill="#1890ff" name="Gross" />
    <Bar dataKey="ndfl" fill="#faad14" name="НДФЛ" />
    <Bar dataKey="social_contributions" fill="#f5222d" name="Взносы" />
    <Bar dataKey="net_income" fill="#52c41a" name="Net" />
  </BarChart>
</ResponsiveContainer>
```

---

#### 6. Line Chart - Effective Tax Rate Over Time

```tsx
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={monthlyBreakdown}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="month_name" />
    <YAxis domain={[0, 40]} tickFormatter={(value) => `${value}%`} />
    <Tooltip formatter={(value) => `${(value as number).toFixed(1)}%`} />
    <Legend />

    <Line
      type="monotone"
      dataKey="effective_tax_rate"
      stroke="#1890ff"
      name="НДФЛ %"
      strokeWidth={2}
    />
    <Line
      type="monotone"
      dataKey="effective_burden_rate"
      stroke="#f5222d"
      name="Общая нагрузка %"
      strokeWidth={2}
    />
  </LineChart>
</ResponsiveContainer>
```

---

### Фаза 4: Frontend - New Section "Налоги и взносы"

**Структура страницы**:
```tsx
<Tabs>
  <TabPane tab="Сводка" key="summary">
    {/* Existing summary cards */}
  </TabPane>

  <TabPane tab="Динамика" key="dynamics">
    {/* Existing dynamics charts */}
  </TabPane>

  <TabPane tab="Налоги и взносы" key="taxes">
    {/* NEW TAB */}
    <Row gutter={[16, 16]}>
      {/* Tax Burden Summary Cards */}
      <Col span={24}>
        {/* 4 cards: НДФЛ, Взносы, Общая нагрузка, Эффективная ставка */}
      </Col>

      {/* Waterfall Chart */}
      <Col xs={24} lg={12}>
        <Card title="Декомпозиция затрат">
          <WaterfallChart data={costWaterfall} />
        </Card>
      </Col>

      {/* Pie Chart */}
      <Col xs={24} lg={12}>
        <Card title="Распределение налогов">
          <PieChart data={taxDistribution} />
        </Card>
      </Col>

      {/* Stacked Area Chart */}
      <Col span={24}>
        <Card title="Динамика ФОТ и налогов">
          <StackedAreaChart data={monthlyBreakdown} />
        </Card>
      </Col>

      {/* Line Chart */}
      <Col xs={24} lg={12}>
        <Card title="Эффективная ставка по месяцам">
          <LineChart data={monthlyBreakdown} />
        </Card>
      </Col>

      {/* Bar Chart */}
      <Col xs={24} lg={12}>
        <Card title="Налоговая нагрузка по сотрудникам">
          <BarChart data={employeeTaxData} />
        </Card>
      </Col>

      {/* Tax Details Table */}
      <Col span={24}>
        <Card title="Детализация налогов">
          <Table
            dataSource={employeeTaxData}
            columns={taxColumns}
            pagination={{ pageSize: 10 }}
          />
        </Card>
      </Col>
    </Row>
  </TabPane>

  <TabPane tab="Прогноз" key="forecast">
    {/* Existing forecast */}
  </TabPane>
</Tabs>
```

---

## Порядок выполнения

1. ✅ **Создать документацию** (этот файл) - DONE
2. ⬜ Создать `social_contributions_calculator.py`
   - Функция `calculate_social_contributions`
   - Функция `calculate_total_tax_burden`
3. ⬜ Добавить endpoint `/api/v1/payroll/analytics/tax-burden`
4. ⬜ Добавить endpoint `/api/v1/payroll/analytics/tax-breakdown-by-month`
5. ⬜ Добавить endpoint `/api/v1/payroll/analytics/tax-by-employee`
6. ⬜ Добавить endpoint `/api/v1/payroll/analytics/cost-waterfall`
7. ⬜ Frontend: Добавить React Query hooks для новых endpoints
8. ⬜ Frontend: Установить ApexCharts (`npm install --save react-apexcharts apexcharts`)
9. ⬜ Frontend: Создать компонент WaterfallChart
10. ⬜ Frontend: Добавить вкладку "Налоги и взносы"
11. ⬜ Frontend: Добавить все графики и карточки
12. ⬜ Frontend: Добавить таблицу детализации
13. ⬜ Тестирование

---

## Оценка времени
- Backend utility (social contributions): ~30 минут
- Backend endpoints (4 новых): ~2 часа
- Frontend charts & components: ~2.5 часа
- Тестирование: ~30 минут

**Итого**: ~5-6 часов работы

---

## Зависимости

### Backend
- ✅ `backend/app/utils/ndfl_calculator.py` - существует
- ⬜ `backend/app/utils/social_contributions_calculator.py` - создать

### Frontend
- ✅ recharts - установлено
- ⬜ apexcharts - установить для Waterfall
- ✅ PayrollAnalyticsPage - существует

---

## Риски

### ⚠️ Сложность Waterfall Chart
**Митигация**: Использовать ApexCharts или упрощенную версию на recharts

### ⚠️ Performance при больших данных
**Митигация**:
- Pagination в таблицах
- Агрегация на backend
- Мемоизация графиков

### ⚠️ Точность налоговых расчетов
**Митигация**:
- Использовать актуальные ставки 2024-2025
- Добавить unit tests
- Верификация с бухгалтерией

---

## Примечания

- Все расчеты выполняются на основе PayrollActual (фактические выплаты)
- Multi-tenancy поддерживается через department_id
- Прогрессивная шкала НДФЛ корректна для 2024-2025
- Страховые взносы: актуальные лимиты 2024-2025
