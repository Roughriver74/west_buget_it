# Анализ модуля "Бюджет доходов" (Revenue Budget)

  

**Дата анализа:** 2025-10-29

**Источник:** `xls/Бюджет доходов Acme СПБ проект 11.02 (1).xlsx`

**Статус:** Концептуальный дизайн

  

---

  

## 1. Обзор

  

Модуль "Бюджет доходов" является **комплементарной системой** к существующему модулю бюджетирования расходов. Если текущая система управляет затратами (OPEX/CAPEX), то новый модуль управляет планированием и учетом доходов компании.

  

### 1.1. Отличия от текущей системы

  

| Аспект | Бюджет расходов (текущий) | Бюджет доходов (новый) |

|--------|---------------------------|------------------------|

| **Фокус** | Затраты, расходы | Выручка, доходы |

| **Категории** | Статьи расходов (IT оборудование, ЗП, и т.д.) | Каналы продаж, продуктовые категории |

| **Структура** | Департаменты → Категории → Статьи | Регионы → Каналы → Продуктовые линейки |

| **Метрики** | План vs Факт расходов | План vs Факт доходов, средний чек, конверсия |

| **Сезонность** | Не критична | Критически важна (коэффициенты сезонности) |

  

---

  

## 2. Структура данных Excel файла

  

### 2.1. Листы и их назначение

  

#### **Основные листы:**

  

1. **2025** - Сводный план доходов

- Общий план по всем направлениям на 2025 год

- Разбивка по месяцам (январь-декабрь)

- Уровни агрегации: СПБ и ЛО, СЗФО (области), Регионы (ЦФО, ПФО и т.д.)

- Метрики: выручка с НДС, прирост к 2024, доля в общем объеме

  

2. **Расчет доходной части СПБ СЗФО** - Детальные расчеты для СПБ и СЗФО

- Сегментация клиентов: обычные клиники, сетевые клиники, новые клиники

- Метрики: средняя закупка на клиента, ОКБ (общая клиентская база), АКБ (активная клиентская база)

- Покрытие клиентской базы (АКБ/ОКБ)

- Сезонность по месяцам

- Разбивка по областям СЗФО

  

3. **Расчет доходной части РЕГИОНЫ** - Расчеты для остальных регионов РФ

- Москва, ЦФО, ПФО, УФО, СФО, ДФО, СНГ

- Аналогичная структура: средний чек, клиентская база, покрытие

  

4. **Сезонность 2023** - Исторические коэффициенты сезонности

- По федеральным округам

- По месяцам

- Используется для прогнозирования

  

5. **Расчет доходной части ОПТ** - Оптовые продажи

- Продажи торговым компаниям (ТК)

- Средний чек по регионам

- Отдельная модель от розничных продаж

  

6. **ОРТО** - Ортодонтическая продукция (детальная разбивка)

- 20+ категорий продукции (брекеты, дуги, адгезивы и т.д.)

- План/факт по месяцам

- Сравнение 2024 vs 2025

- Самый детализированный лист по продуктовым категориям

  

7. **ОБОРУДОВАНИЕ 1.0** - Продажи оборудования

- Отдел оборудования (без наконечников)

- Вся компания

- Наценка 14%

- Планируемая прибыль

  

8. **ТЕНДЕРЫ** - Тендерные продажи

- Государственные тендеры

- Количество выигранных тендеров

- Средняя сумма тендера

- Сезонность

  

9. **ИТЕРНЕТ МАГАЗИН** - Интернет-магазин

- Количество заказов

- Средний чек

- План vs факт

  

10. **Исходные данные 2024** - Исторические данные

11. **БДР 2022 -пример** - Пример БДР (бюджета доходов и расходов)

  

### 2.2. Ключевые метрики

  

#### **Клиентские метрики:**

- **ОКБ** (Общая клиентская база) - все потенциальные клиенты в регионе

- **АКБ** (Активная клиентская база) - клиенты, совершившие покупки

- **Покрытие** (АКБ/ОКБ) - процент активных клиентов от общей базы

- **Средняя закупка на клиента** - средний чек

  

#### **Финансовые метрики:**

- **Выручка с НДС** - основная метрика дохода

- **Прирост к предыдущему году** - темп роста

- **Доля в общем объеме** - вклад в общую выручку

- **Наценка** - для продукции с добавленной стоимостью

- **Планируемая прибыль** - для оборудования

  

#### **Операционные метрики:**

- **Сезонность** - коэффициенты по месяцам (0.74 - 1.26)

- **Количество заказов/тендеров** - объемные показатели

  

---

  

## 3. Архитектура решения

  

### 3.1. Концептуальная модель данных

  

#### **Иерархия сущностей:**

  

```

Organization (Организация)

├── RevenueStream (Поток доходов)

│ ├── Channel (Канал продаж)

│ ├── Region (Регион)

│ └── ProductCategory (Продуктовая категория)

├── RevenueCategory (Категория доходов)

│ └── SubCategory (Подкатегория)

├── RevenuePlan (План доходов)

│ ├── RevenuePlanVersion (Версия плана)

│ └── RevenuePlanDetails (Детали плана по месяцам)

├── RevenueActual (Фактические доходы)

├── CustomerMetrics (Клиентские метрики)

├── SeasonalityCoefficients (Коэффициенты сезонности)

└── RevenueForecast (Прогноз доходов)

```

  

### 3.2. Базовые сущности (Database Models)

  

#### **1. RevenueStream (Поток доходов)**

Основная классификация источников дохода.

  

```python

class RevenueStream(Base):

__tablename__ = "revenue_streams"

  

id = Column(Integer, primary_key=True, index=True)

name = Column(String(255), nullable=False) # "СПБ и ЛО", "СЗФО", "Регионы" и т.д.

stream_type = Column(Enum(RevenueStreamType), nullable=False)

# REGIONAL (региональные), CHANNEL (каналы продаж), PRODUCT (продуктовые)

  

parent_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

  

is_active = Column(Boolean, default=True, nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

updated_at = Column(DateTime(timezone=True), onupdate=func.now())

  

# Relationships

department_rel = relationship("Department")

parent = relationship("RevenueStream", remote_side=[id], backref="children")

```

  

**Примеры:**

- СПБ и ЛО (региональный)

- СЗФО → Архангельская область, Вологодская область и т.д. (региональные, иерархия)

- Регионы → Москва, ЦФО, ПФО и т.д.

- Опт, Тендеры, Интернет-магазин (каналы)

- Ортодонтия → Брекеты, Дуги, Адгезивы (продуктовые)

  

#### **2. RevenueCategory (Категория доходов)**

Продуктовые и сервисные категории.

  

```python

class RevenueCategory(Base):

__tablename__ = "revenue_categories"

  

id = Column(Integer, primary_key=True, index=True)

name = Column(String(255), nullable=False) # "Брекеты", "Дуги", "Оборудование"

code = Column(String(50), unique=True, nullable=True)

category_type = Column(Enum(RevenueCategoryType), nullable=False)

# PRODUCT (продукция), SERVICE (услуги), EQUIPMENT (оборудование), TENDER (тендеры)

  

parent_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

  

# Специфичные поля

default_margin = Column(Numeric(5, 2), nullable=True) # Наценка в %

  

is_active = Column(Boolean, default=True, nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

department_rel = relationship("Department")

parent = relationship("RevenueCategory", remote_side=[id], backref="subcategories")

```

  

**Примеры иерархии:**

- Ортодонтия

- Брекеты

- Брекеты лигатурные металлические

- Брекеты лигатурные эстетические

- Брекеты самолигирующие металлические

- Брекеты самолигирующие эстетические

- Дуги

- Адгезивы ортодонтические

- Оборудование

- Оборудование без наконечников

- Наконечники

  

#### **3. RevenuePlan (План доходов)**

Годовой план доходов с версионированием.

  

```python

class RevenuePlan(Base):

__tablename__ = "revenue_plans"

  

id = Column(Integer, primary_key=True, index=True)

name = Column(String(255), nullable=False) # "План доходов 2025"

year = Column(Integer, nullable=False, index=True)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)

revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

  

status = Column(Enum(PlanStatus), default=PlanStatus.DRAFT, nullable=False)

# DRAFT, PENDING_APPROVAL, APPROVED, ACTIVE, ARCHIVED

  

total_planned_revenue = Column(Numeric(15, 2), nullable=True)

  

created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

created_at = Column(DateTime(timezone=True), server_default=func.now())

approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)

approved_at = Column(DateTime(timezone=True), nullable=True)

  

# Relationships

department_rel = relationship("Department")

revenue_stream = relationship("RevenueStream")

revenue_category = relationship("RevenueCategory")

creator = relationship("User", foreign_keys=[created_by])

versions = relationship("RevenuePlanVersion", back_populates="plan")

```

  

#### **4. RevenuePlanVersion (Версия плана)**

Версионирование плана (как в budget_plan_versions).

  

```python

class RevenuePlanVersion(Base):

__tablename__ = "revenue_plan_versions"

  

id = Column(Integer, primary_key=True, index=True)

plan_id = Column(Integer, ForeignKey("revenue_plans.id"), nullable=False)

version_number = Column(Integer, nullable=False)

version_name = Column(String(255), nullable=True)

  

status = Column(Enum(VersionStatus), default=VersionStatus.DRAFT, nullable=False)

  

created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

plan = relationship("RevenuePlan", back_populates="versions")

details = relationship("RevenuePlanDetail", back_populates="version")

```

  

#### **5. RevenuePlanDetail (Детали плана по месяцам)**

Детализация плана по месяцам и категориям.

  

```python

class RevenuePlanDetail(Base):

__tablename__ = "revenue_plan_details"

  

id = Column(Integer, primary_key=True, index=True)

version_id = Column(Integer, ForeignKey("revenue_plan_versions.id"), nullable=False)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)

revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

  

# Месячные планы (12 колонок)

month_01 = Column(Numeric(15, 2), default=0)

month_02 = Column(Numeric(15, 2), default=0)

month_03 = Column(Numeric(15, 2), default=0)

month_04 = Column(Numeric(15, 2), default=0)

month_05 = Column(Numeric(15, 2), default=0)

month_06 = Column(Numeric(15, 2), default=0)

month_07 = Column(Numeric(15, 2), default=0)

month_08 = Column(Numeric(15, 2), default=0)

month_09 = Column(Numeric(15, 2), default=0)

month_10 = Column(Numeric(15, 2), default=0)

month_11 = Column(Numeric(15, 2), default=0)

month_12 = Column(Numeric(15, 2), default=0)

  

# Итого

total = Column(Numeric(15, 2), nullable=True)

  

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

version = relationship("RevenuePlanVersion", back_populates="details")

revenue_stream = relationship("RevenueStream")

revenue_category = relationship("RevenueCategory")

department_rel = relationship("Department")

```

  

#### **6. RevenueActual (Фактические доходы)**

Фактическая выручка за месяц.

  

```python

class RevenueActual(Base):

__tablename__ = "revenue_actuals"

  

id = Column(Integer, primary_key=True, index=True)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)

revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

  

year = Column(Integer, nullable=False, index=True)

month = Column(Integer, nullable=False, index=True) # 1-12

  

planned_amount = Column(Numeric(15, 2), nullable=True) # Из плана

actual_amount = Column(Numeric(15, 2), nullable=False) # Факт

variance = Column(Numeric(15, 2), nullable=True) # Отклонение

variance_percent = Column(Numeric(5, 2), nullable=True) # % отклонения

  

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

  

# Метаданные

notes = Column(Text, nullable=True)

created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

created_at = Column(DateTime(timezone=True), server_default=func.now())

updated_at = Column(DateTime(timezone=True), onupdate=func.now())

  

# Relationships

revenue_stream = relationship("RevenueStream")

revenue_category = relationship("RevenueCategory")

department_rel = relationship("Department")

creator = relationship("User")

```

  

#### **7. CustomerMetrics (Клиентские метрики)**

Метрики клиентской базы по регионам.

  

```python

class CustomerMetrics(Base):

__tablename__ = "customer_metrics"

  

id = Column(Integer, primary_key=True, index=True)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=False)

year = Column(Integer, nullable=False, index=True)

month = Column(Integer, nullable=False, index=True)

  

# Клиентские метрики

total_customer_base = Column(Integer, nullable=True) # ОКБ

active_customer_base = Column(Integer, nullable=True) # АКБ

coverage_rate = Column(Numeric(5, 4), nullable=True) # Покрытие (АКБ/ОКБ)

  

# Сегменты клиентов

regular_clinics = Column(Integer, nullable=True) # Обычные клиники

network_clinics = Column(Integer, nullable=True) # Сетевые клиники

new_clinics = Column(Integer, nullable=True) # Новые клиники

  

# Средний чек

avg_order_value = Column(Numeric(12, 2), nullable=True)

avg_order_value_regular = Column(Numeric(12, 2), nullable=True)

avg_order_value_network = Column(Numeric(12, 2), nullable=True)

avg_order_value_new = Column(Numeric(12, 2), nullable=True)

  

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

revenue_stream = relationship("RevenueStream")

department_rel = relationship("Department")

```

  

#### **8. SeasonalityCoefficient (Коэффициенты сезонности)**

Исторические коэффициенты для прогнозирования.

  

```python

class SeasonalityCoefficient(Base):

__tablename__ = "seasonality_coefficients"

  

id = Column(Integer, primary_key=True, index=True)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=False)

year = Column(Integer, nullable=False, index=True) # Исторический год

  

# Коэффициенты по месяцам (относительно среднего = 1.0)

coef_01 = Column(Numeric(5, 4), nullable=False)

coef_02 = Column(Numeric(5, 4), nullable=False)

coef_03 = Column(Numeric(5, 4), nullable=False)

coef_04 = Column(Numeric(5, 4), nullable=False)

coef_05 = Column(Numeric(5, 4), nullable=False)

coef_06 = Column(Numeric(5, 4), nullable=False)

coef_07 = Column(Numeric(5, 4), nullable=False)

coef_08 = Column(Numeric(5, 4), nullable=False)

coef_09 = Column(Numeric(5, 4), nullable=False)

coef_10 = Column(Numeric(5, 4), nullable=False)

coef_11 = Column(Numeric(5, 4), nullable=False)

coef_12 = Column(Numeric(5, 4), nullable=False)

  

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

revenue_stream = relationship("RevenueStream")

department_rel = relationship("Department")

```

  

#### **9. RevenueForecast (Прогноз доходов)**

ML-прогнозы на основе исторических данных.

  

```python

class RevenueForecast(Base):

__tablename__ = "revenue_forecasts"

  

id = Column(Integer, primary_key=True, index=True)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)

revenue_category_id = Column(Integer, ForeignKey("revenue_categories.id"), nullable=True)

  

forecast_year = Column(Integer, nullable=False, index=True)

forecast_month = Column(Integer, nullable=False, index=True)

  

forecast_amount = Column(Numeric(15, 2), nullable=False)

confidence_level = Column(Numeric(5, 2), nullable=True) # Уровень доверия (0-100%)

  

model_type = Column(String(50), nullable=True) # "LINEAR", "ARIMA", "ML" и т.д.

model_params = Column(JSON, nullable=True) # Параметры модели

  

created_at = Column(DateTime(timezone=True), server_default=func.now())

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

  

# Relationships

revenue_stream = relationship("RevenueStream")

revenue_category = relationship("RevenueCategory")

department_rel = relationship("Department")

```

  

### 3.3. Дополнительные сущности

  

#### **10. RevenueBudgetScenario (Сценарии бюджета)**

Для создания оптимистичного/пессимистичного/реалистичного сценариев.

  

```python

class RevenueBudgetScenario(Base):

__tablename__ = "revenue_budget_scenarios"

  

id = Column(Integer, primary_key=True, index=True)

name = Column(String(255), nullable=False) # "Оптимистичный 2025", "Пессимистичный 2025"

scenario_type = Column(Enum(ScenarioType), nullable=False)

# OPTIMISTIC, REALISTIC, PESSIMISTIC, CUSTOM

  

year = Column(Integer, nullable=False, index=True)

adjustment_factor = Column(Numeric(5, 2), nullable=True) # ±% к базовому плану

  

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

department_rel = relationship("Department")

```

  

#### **11. RevenueTarget (Целевые показатели)**

KPI и целевые показатели для отделов продаж.

  

```python

class RevenueTarget(Base):

__tablename__ = "revenue_targets"

  

id = Column(Integer, primary_key=True, index=True)

  

revenue_stream_id = Column(Integer, ForeignKey("revenue_streams.id"), nullable=True)

user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Менеджер/отдел

  

year = Column(Integer, nullable=False, index=True)

quarter = Column(Integer, nullable=True, index=True) # 1-4 или NULL для года

  

target_amount = Column(Numeric(15, 2), nullable=False)

achieved_amount = Column(Numeric(15, 2), nullable=True)

achievement_rate = Column(Numeric(5, 2), nullable=True) # %

  

department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

created_at = Column(DateTime(timezone=True), server_default=func.now())

  

# Relationships

revenue_stream = relationship("RevenueStream")

user = relationship("User")

department_rel = relationship("Department")

```

  

---

  

## 4. API Endpoints (Backend)

  

### 4.1. Revenue Streams API (`/api/v1/revenue-streams`)

  

```python

# GET /api/v1/revenue-streams

def get_revenue_streams(

department_id: Optional[int] = None,

stream_type: Optional[RevenueStreamType] = None,

parent_id: Optional[int] = None,

is_active: Optional[bool] = True,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenueStreamSchema]

  

# POST /api/v1/revenue-streams

def create_revenue_stream(

stream: RevenueStreamCreate,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> RevenueStreamSchema

  

# GET /api/v1/revenue-streams/{id}

def get_revenue_stream(

id: int,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> RevenueStreamSchema

  

# PUT /api/v1/revenue-streams/{id}

def update_revenue_stream(...)

  

# DELETE /api/v1/revenue-streams/{id}

def delete_revenue_stream(...)

  

# GET /api/v1/revenue-streams/tree

def get_revenue_streams_tree(...) -> TreeStructure

```

  

### 4.2. Revenue Plans API (`/api/v1/revenue-plans`)

  

```python

# GET /api/v1/revenue-plans

def get_revenue_plans(

year: Optional[int] = None,

department_id: Optional[int] = None,

status: Optional[PlanStatus] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenuePlanSchema]

  

# POST /api/v1/revenue-plans

def create_revenue_plan(...)

  

# GET /api/v1/revenue-plans/{id}

def get_revenue_plan(...)

  

# PUT /api/v1/revenue-plans/{id}

def update_revenue_plan(...)

  

# POST /api/v1/revenue-plans/{id}/versions

def create_plan_version(...)

  

# GET /api/v1/revenue-plans/{id}/versions/{version_id}

def get_plan_version(...)

  

# POST /api/v1/revenue-plans/{id}/approve

def approve_plan(...)

  

# POST /api/v1/revenue-plans/{id}/copy

def copy_plan(

plan_id: int,

target_year: int,

apply_seasonality: bool = True,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> RevenuePlanSchema

```

  

### 4.3. Revenue Plan Details API (`/api/v1/revenue-plan-details`)

  

```python

# GET /api/v1/revenue-plan-details

def get_plan_details(

version_id: int,

revenue_stream_id: Optional[int] = None,

revenue_category_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenuePlanDetailSchema]

  

# POST /api/v1/revenue-plan-details

def create_plan_detail(...)

  

# PUT /api/v1/revenue-plan-details/{id}

def update_plan_detail(...)

  

# POST /api/v1/revenue-plan-details/bulk

def bulk_update_plan_details(

updates: List[RevenuePlanDetailUpdate],

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenuePlanDetailSchema]

```

  

### 4.4. Revenue Actuals API (`/api/v1/revenue-actuals`)

  

```python

# GET /api/v1/revenue-actuals

def get_revenue_actuals(

year: int,

month: Optional[int] = None,

revenue_stream_id: Optional[int] = None,

department_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenueActualSchema]

  

# POST /api/v1/revenue-actuals

def create_revenue_actual(...)

  

# PUT /api/v1/revenue-actuals/{id}

def update_revenue_actual(...)

  

# GET /api/v1/revenue-actuals/variance

def get_plan_vs_actual_variance(

year: int,

month: Optional[int] = None,

revenue_stream_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> VarianceReportSchema

```

  

### 4.5. Customer Metrics API (`/api/v1/customer-metrics`)

  

```python

# GET /api/v1/customer-metrics

def get_customer_metrics(

year: int,

month: Optional[int] = None,

revenue_stream_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[CustomerMetricsSchema]

  

# POST /api/v1/customer-metrics

def create_customer_metrics(...)

  

# PUT /api/v1/customer-metrics/{id}

def update_customer_metrics(...)

  

# GET /api/v1/customer-metrics/trends

def get_customer_trends(

revenue_stream_id: int,

year: int,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> CustomerTrendsSchema

```

  

### 4.6. Seasonality API (`/api/v1/seasonality`)

  

```python

# GET /api/v1/seasonality

def get_seasonality_coefficients(

revenue_stream_id: int,

year: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[SeasonalityCoefficientSchema]

  

# POST /api/v1/seasonality

def create_seasonality_coefficients(...)

  

# PUT /api/v1/seasonality/{id}

def update_seasonality_coefficients(...)

  

# GET /api/v1/seasonality/calculate

def calculate_seasonality(

revenue_stream_id: int,

historical_years: int = 3, # Использовать последние 3 года

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> SeasonalityCoefficientSchema

```

  

### 4.7. Revenue Forecast API (`/api/v1/revenue-forecast`)

  

```python

# GET /api/v1/revenue-forecast

def get_revenue_forecast(

forecast_year: int,

revenue_stream_id: Optional[int] = None,

model_type: Optional[str] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenueForecastSchema]

  

# POST /api/v1/revenue-forecast/generate

def generate_forecast(

revenue_stream_id: int,

forecast_year: int,

model_type: str = "LINEAR", # LINEAR, ARIMA, ML

use_seasonality: bool = True,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> List[RevenueForecastSchema]

```

  

### 4.8. Analytics & Reports API (`/api/v1/revenue-analytics`)

  

```python

# GET /api/v1/revenue-analytics/summary

def get_revenue_summary(

year: int,

department_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> RevenueSummarySchema

  

# GET /api/v1/revenue-analytics/plan-vs-actual

def get_plan_vs_actual(

year: int,

month: Optional[int] = None,

revenue_stream_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> PlanVsActualSchema

  

# GET /api/v1/revenue-analytics/trends

def get_revenue_trends(

start_year: int,

end_year: int,

revenue_stream_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> RevenueTrendsSchema

  

# GET /api/v1/revenue-analytics/regional-breakdown

def get_regional_breakdown(

year: int,

quarter: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> RegionalBreakdownSchema

  

# GET /api/v1/revenue-analytics/product-mix

def get_product_mix(

year: int,

revenue_stream_id: Optional[int] = None,

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> ProductMixSchema

  

# POST /api/v1/revenue-analytics/export

def export_revenue_report(

year: int,

format: str = "xlsx", # xlsx, csv, pdf

current_user: User = Depends(get_current_active_user),

db: Session = Depends(get_db)

) -> FileResponse

```

  

---

  

## 5. Frontend Компоненты

  

### 5.1. Страницы (Pages)

  

#### **1. RevenueDashboardPage** (`/revenue/dashboard`)

Главная страница модуля доходов.

  

**Компоненты:**

- Сводные карточки (общая выручка, прирост к прошлому году, выполнение плана)

- График план vs факт (линейный график по месяцам)

- Разбивка по регионам (круговая диаграмма)

- Топ-5 продуктовых категорий (столбчатая диаграмма)

- Тренды выручки (график за несколько лет)

  

#### **2. RevenuePlanningPage** (`/revenue/planning`)

Страница планирования доходов.

  

**Компоненты:**

- Таблица планирования (аналог BudgetPlanDetailsTable)

- Sticky header с месяцами

- Группировка по потокам доходов/категориям

- Inline редактирование

- Автосумма по строкам и колонкам

- Применение коэффициентов сезонности

- Панель управления версиями

- Сравнение версий (side-by-side)

- Копирование плана из предыдущего года

  

**Особенности:**

- Мультиуровневая группировка (регионы → области → категории)

- Поддержка сворачивания/разворачивания групп

- Цветовая индикация отклонений от таргетов

- Экспорт в Excel

  

#### **3. RevenueActualsPage** (`/revenue/actuals`)

Учет фактических доходов.

  

**Компоненты:**

- Таблица ввода фактов по месяцам

- Сравнение с планом (variance)

- График отклонений

- Фильтры по регионам/категориям

  

#### **4. RevenueAnalyticsPage** (`/revenue/analytics`)

Аналитика и отчеты.

  

**Компоненты:**

- План vs Факт (по месяцам, кварталам, году)

- Региональная разбивка

- Продуктовый микс

- Тренды выручки

- Клиентские метрики (ОКБ, АКБ, покрытие, средний чек)

- Сезонность (визуализация коэффициентов)

  

#### **5. CustomerMetricsPage** (`/revenue/customers`)

Управление клиентскими метриками.

  

**Компоненты:**

- Таблица метрик по регионам

- График покрытия клиентской базы

- Динамика среднего чека

- Сегментация клиентов (обычные, сетевые, новые)

  

#### **6. RevenueForecastPage** (`/revenue/forecast`)

Прогнозирование доходов.

  

**Компоненты:**

- Выбор модели прогнозирования

- Настройка параметров (сезонность, исторический период)

- Визуализация прогноза

- Сравнение сценариев (оптимистичный/реалистичный/пессимистичный)

  

#### **7. RevenueSettingsPage** (`/revenue/settings`)

Справочники и настройки.

  

**Компоненты:**

- Управление потоками доходов (иерархическое дерево)

- Управление категориями продукции

- Настройка коэффициентов сезонности

- Целевые показатели (KPI)

  

### 5.2. Переиспользуемые компоненты

  

#### **RevenuePlanTable** (`components/revenue/RevenuePlanTable.tsx`)

Основная таблица планирования.

  

**Props:**

```typescript

interface RevenuePlanTableProps {

versionId: number

year: number

editable?: boolean

groupBy?: 'stream' | 'category' | 'region'

onUpdate?: (updates: PlanDetailUpdate[]) => void

}

```

  

**Особенности:**

- Виртуализация для больших объемов данных

- Мемоизация строк для производительности

- Sticky header и footer

- Inline редактирование с валидацией

- Поддержка горячих клавиш (Enter, Tab, Esc)

  

#### **SeasonalityApplier** (`components/revenue/SeasonalityApplier.tsx`)

Применение коэффициентов сезонности к плану.

  

**Props:**

```typescript

interface SeasonalityApplierProps {

revenueStreamId: number

year: number

annualTarget: number // Целевая выручка за год

onApply: (monthlyDistribution: number[]) => void

}

```

  

**Логика:**

- Загрузка исторических коэффициентов

- Расчет месячного распределения

- Визуализация результата

- Применение к плану

  

#### **PlanVsActualChart** (`components/revenue/PlanVsActualChart.tsx`)

График сравнения план vs факт.

  

**Props:**

```typescript

interface PlanVsActualChartProps {

year: number

revenueStreamId?: number

chartType?: 'line' | 'bar' | 'combo'

}

```

  

#### **RevenueStreamTree** (`components/revenue/RevenueStreamTree.tsx`)

Иерархическое дерево потоков доходов.

  

**Props:**

```typescript

interface RevenueStreamTreeProps {

editable?: boolean

selectable?: boolean

onSelect?: (streamId: number) => void

onUpdate?: (stream: RevenueStream) => void

}

```

  

---

  

## 6. Интеграция с существующей системой

  

### 6.1. Общие компоненты

  

Переиспользование существующих компонентов:

  

1. **AppLayout** - единая навигация

2. **ProtectedRoute** - авторизация

3. **DepartmentContext** - мультитенантность

4. **Ant Design компоненты** - UI библиотека

  

### 6.2. Расширение навигации

  

Добавить новый раздел в `AppLayout`:

  

```typescript

const menuItems = [

// ... существующие пункты

{

key: 'revenue',

icon: <DollarOutlined />,

label: 'Доходы',

children: [

{ key: '/revenue/dashboard', label: 'Дашборд' },

{ key: '/revenue/planning', label: 'Планирование' },

{ key: '/revenue/actuals', label: 'Факт' },

{ key: '/revenue/analytics', label: 'Аналитика' },

{ key: '/revenue/customers', label: 'Клиенты' },

{ key: '/revenue/forecast', label: 'Прогноз' },

{ key: '/revenue/settings', label: 'Настройки' },

]

}

]

```

  

### 6.3. Роли и права доступа

  

Использовать существующую систему ролей:

  

- **USER**: только просмотр своего департамента

- **MANAGER**: просмотр всех департаментов + редактирование

- **ADMIN**: полный доступ + управление справочниками

  

### 6.4. Связь с бюджетом расходов

  

Возможные интеграции:

  

1. **Совмещенный дашборд** - сравнение доходов и расходов

2. **Прибыльность** - расчет прибыли (доходы - расходы)

3. **БДР (Бюджет доходов и расходов)** - полная финансовая картина

4. **Планирование рентабельности** - целевая маржа по направлениям

  

---

  

## 7. Импорт данных из Excel

  

### 7.1. Скрипт импорта

  

Создать `backend/scripts/import_revenue_excel.py`:

  

```python

import pandas as pd

from app.db.session import SessionLocal

from app.db.models import RevenueStream, RevenuePlan, RevenuePlanDetail, etc.

  

def import_revenue_data(file_path: str, year: int, department_id: int):

"""

Импорт данных о доходах из Excel файла

"""

db = SessionLocal()

  

try:

# 1. Импорт потоков доходов из листа "2025"

df_summary = pd.read_excel(file_path, sheet_name='2025', header=0)

import_revenue_streams(df_summary, db, department_id)

  

# 2. Импорт детальных данных СПБ/СЗФО

df_spb = pd.read_excel(file_path, sheet_name='Расчет доходной части СПБ СЗФО')

import_regional_details(df_spb, db, department_id, year, 'SPB_SZFO')

  

# 3. Импорт продуктовых категорий из "ОРТО"

df_orto = pd.read_excel(file_path, sheet_name='ОРТО')

import_product_categories(df_orto, db, department_id)

  

# 4. Импорт коэффициентов сезонности

df_seasonality = pd.read_excel(file_path, sheet_name='Сезонность 2023')

import_seasonality_coefficients(df_seasonality, db, department_id)

  

db.commit()

print(f"Импорт завершен успешно для года {year}")

  

except Exception as e:

db.rollback()

print(f"Ошибка импорта: {e}")

raise

finally:

db.close()

```

  

### 7.2. Маппинг данных

  

**Лист "2025" → RevenueStream + RevenuePlanDetail**

  

| Excel колонка | Database поле |

|--------------|---------------|

| "СПБ и ЛО" | RevenueStream.name |

| "Январь" | RevenuePlanDetail.month_01 |

| "Февраль" | RevenuePlanDetail.month_02 |

| ... | ... |

| "2025 ГОД" | RevenuePlanDetail.total |

  

**Лист "Расчет доходной части СПБ СЗФО" → CustomerMetrics**

  

| Excel | Database |

|-------|----------|

| "ОКБ" | CustomerMetrics.total_customer_base |

| "АКБ" | CustomerMetrics.active_customer_base |

| "Покрытие" | CustomerMetrics.coverage_rate |

| "Средняя закупка" | CustomerMetrics.avg_order_value |

  

---

  

## 8. Roadmap реализации

  

### Фаза 1: Базовая структура (2-3 недели)

✅ **Цель:** Создать минимальную рабочую версию

  

**Задачи:**

1. Создать модели БД (RevenueStream, RevenuePlan, RevenuePlanDetail, RevenueActual)

2. Создать миграции

3. Создать базовые API endpoints (CRUD для справочников)

4. Создать импорт из Excel (базовый)

5. Создать страницу Revenue Dashboard (только просмотр)

  

**Результат:** Можно импортировать данные и просматривать дашборд

  

### Фаза 2: Планирование (2-3 недели)

✅ **Цель:** Реализовать функционал планирования

  

**Задачи:**

1. Создать RevenuePlanTable с inline редактированием

2. Реализовать версионирование планов

3. Добавить применение коэффициентов сезонности

4. Создать копирование плана из предыдущего года

5. Реализовать экспорт в Excel

  

**Результат:** Можно создавать и редактировать планы доходов

  

### Фаза 3: Учет фактов (1-2 недели)

✅ **Цель:** Добавить учет фактических доходов

  

**Задачи:**

1. Создать страницу ввода фактов

2. Реализовать расчет отклонений (план vs факт)

3. Добавить визуализацию variance

4. Создать уведомления о превышении/недовыполнении плана

  

**Результат:** Можно вводить факты и сравнивать с планом

  

### Фаза 4: Клиентские метрики (1-2 недели)

✅ **Цель:** Добавить управление клиентскими метриками

  

**Задачи:**

1. Создать модели CustomerMetrics, SeasonalityCoefficient

2. Создать страницу управления метриками

3. Добавить графики покрытия и среднего чека

4. Реализовать расчет коэффициентов сезонности из истории

  

**Результат:** Можно отслеживать клиентские метрики

  

### Фаза 5: Аналитика (2 недели)

✅ **Цель:** Расширенная аналитика и отчеты

  

**Задачи:**

1. Создать страницу Revenue Analytics

2. Реализовать региональную разбивку

3. Добавить анализ продуктового микса

4. Создать экспорт отчетов в различных форматах

5. Добавить дашборды для руководства

  

**Результат:** Полная аналитика доходов

  

### Фаза 6: Прогнозирование (опционально, 2-3 недели)

⚠️ **Цель:** ML-прогнозирование доходов

  

**Задачи:**

1. Создать модели прогнозирования (LINEAR, ARIMA)

2. Интегрировать ML библиотеки (scikit-learn, statsmodels)

3. Создать страницу настройки прогнозов

4. Реализовать сценарное планирование

5. Добавить визуализацию прогнозов

  

**Результат:** Автоматическое прогнозирование доходов

  

### Фаза 7: Интеграция (1 неделя)

✅ **Цель:** Интеграция с модулем расходов

  

**Задачи:**

1. Создать совмещенный дашборд доходов и расходов

2. Реализовать расчет прибыльности

3. Добавить БДР (бюджет доходов и расходов)

4. Создать сквозную аналитику

  

**Результат:** Единая система финансового планирования

  

---

  

## 9. Технические рекомендации

  

### 9.1. Производительность

  

**Проблемы:**

- Большие объемы данных (десятки тысяч строк планов)

- Сложные вычисления (агрегации, тренды)

- Множественные фильтрации

  

**Решения:**

1. **Индексы БД:**

- Composite indexes на (department_id, year, month)

- Indexes на foreign keys

- Partial indexes для активных записей (WHERE is_active = true)

  

2. **Кэширование:**

- Redis для агрегированных данных (сводки по годам/кварталам)

- Кэш на уровне API (ttl = 5 минут для планов, 1 минута для фактов)

  

3. **Пагинация:**

- Серверная пагинация для больших списков

- Виртуализация таблиц на фронтенде (react-window)

  

4. **Оптимизация запросов:**

- Eager loading связанных сущностей

- Использование WITH (CTE) для сложных запросов

- Материализованные представления для отчетов

  

### 9.2. Безопасность

  

**Критические моменты:**

1. **Мультитенантность:**

- ВСЕГДА фильтровать по department_id

- Проверка прав на уровне API

  

2. **Версионирование:**

- Immutable versions (нельзя изменить утвержденную версию)

- Audit trail для всех изменений

  

3. **Валидация:**

- Проверка диапазонов (month 1-12, year > 2020)

- Проверка суммы строк = сумме месяцев

- Проверка уникальности (год + поток + категория)

  

### 9.3. UI/UX

  

**Принципы:**

1. **Консистентность:**

- Использовать те же паттерны, что и в модуле расходов

- Единый стиль таблиц (BudgetPlanTable как референс)

  

2. **Производительность:**

- React.memo для тяжелых компонентов

- useCallback/useMemo для функций и вычислений

- Debounce для автосохранения (500ms)

  

3. **Удобство:**

- Горячие клавиши (Ctrl+S сохранить, Esc отменить)

- Контекстное меню (правая кнопка мыши)

- Подсказки (tooltips) для сложных метрик

- Индикаторы загрузки

  

### 9.4. Тестирование

  

**Unit тесты (Backend):**

- Модели (валидация, constraints)

- API endpoints (CRUD, permissions)

- Бизнес-логика (расчет variance, сезонность)

  

**Integration тесты:**

- Импорт данных

- Версионирование планов

- Расчет агрегаций

  

**E2E тесты (Frontend):**

- Создание и редактирование плана

- Применение сезонности

- Экспорт в Excel

  

---

  

## 10. Риски и митигации

  

### Риск 1: Сложность данных

**Описание:** Многоуровневая иерархия (регионы → области → категории) усложняет модель

**Митигация:**

- Использовать self-referencing foreign keys (parent_id)

- Реализовать рекурсивные запросы (WITH RECURSIVE)

- Ограничить глубину иерархии (max 4 уровня)

  

### Риск 2: Производительность больших таблиц

**Описание:** Миллионы строк в RevenuePlanDetail при детализации

**Митигация:**

- Партиционирование таблиц по годам (PostgreSQL table partitioning)

- Архивация старых данных (>3 лет)

- Материализованные представления для отчетов

  

### Риск 3: Конфликты при одновременном редактировании

**Описание:** Несколько пользователей редактируют один план

**Митигация:**

- Optimistic locking (version field)

- WebSocket уведомления о конфликтах

- Merge-стратегия для разрешения конфликтов

  

### Риск 4: Сложность прогнозирования

**Описание:** ML-модели требуют экспертизы

**Митигация:**

- Начать с простых моделей (линейная регрессия)

- Сделать прогноз опциональным (Фаза 6)

- Использовать готовые библиотеки (Prophet от Facebook)

  

---

  

## 11. Выводы и рекомендации

  

### ✅ Стоит реализовать

  

1. **Фазы 1-5** - основной функционал, критически важен для бизнеса

2. **Интеграция с модулем расходов** - создаст единую систему финансового управления

3. **Импорт из Excel** - позволит быстро перенести существующие данные

  

### ⚠️ Опционально

  

1. **Фаза 6 (Прогнозирование)** - требует ML экспертизы, можно отложить

2. **Сценарное планирование** - nice-to-have, но не критично

3. **Мобильное приложение** - пока не требуется

  

### 🚫 Не рекомендуется

  

1. **Интеграция с CRM** - выходит за рамки модуля бюджетирования

2. **Автоматический импорт из 1С** - слишком сложно на первом этапе

3. **Blockchain для аудита** - overkill для текущих требований

  

### 📊 Оценка объема работ

  

- **Минимальная версия (Фазы 1-3):** 6-8 недель

- **Полная версия (Фазы 1-5):** 10-12 недель

- **С прогнозированием (Фазы 1-6):** 14-16 недель

- **С интеграцией (Фазы 1-7):** 16-18 недель

  

### 🎯 Следующие шаги

  

1. **Утвердить архитектуру** с заказчиком

2. **Создать прототип БД** (модели + миграции)

3. **Провести proof-of-concept** импорта данных

4. **Разработать UI mockups** для ключевых страниц

5. **Начать итеративную разработку** (Фаза 1)

  

---

  

## Приложение A: Пример данных

  

### Пример иерархии RevenueStream

  

```

СПБ и ЛО (id=1, parent_id=null)

СЗФО (id=2, parent_id=null)

├── Архангельская область (id=3, parent_id=2)

├── Вологодская область (id=4, parent_id=2)

└── Калининградская область (id=5, parent_id=2)

Регионы (id=6, parent_id=null)

├── Москва (id=7, parent_id=6)

├── ЦФО (id=8, parent_id=6)

└── ПФО (id=9, parent_id=6)

Опт (id=10, parent_id=null)

Тендеры (id=11, parent_id=null)

Интернет-магазин (id=12, parent_id=null)

```

  

### Пример RevenuePlanDetail

  

```json

{

"id": 123,

"version_id": 1,

"revenue_stream_id": 1, // СПБ и ЛО

"revenue_category_id": null,

"month_01": 132201250,

"month_02": 177000650,

"month_03": 179585000,

"month_04": 176784300,

"month_05": 195476800,

"month_06": 174020600,

"month_07": 150491450,

"month_08": 165031650,

"month_09": 177942100,

"month_10": 196513600,

"month_11": 215165100,

"month_12": 230244700,

"total": 2170457200,

"department_id": 1

}

```

  

### Пример CustomerMetrics

  

```json

{

"id": 456,

"revenue_stream_id": 1, // СПБ и ЛО

"year": 2025,

"month": 1,

"total_customer_base": 2299, // ОКБ

"active_customer_base": 1683, // АКБ

"coverage_rate": 0.7321, // 73.21%

"regular_clinics": 1200,

"network_clinics": 400,

"new_clinics": 83,

"avg_order_value": 80000,

"avg_order_value_network": 589000,

"department_id": 1

}

```

  

---

  

**Документ подготовлен:** Claude Code

**Версия:** 1.0

**Дата:** 2025-10-29