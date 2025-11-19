# Module System - Modular Architecture Guide

## Обзор

**Module System** - система управления модулями для контроля доступа к функциям приложения на уровне организации. Позволяет включать/выключать платные функции через лицензионную модель.

## Ключевые возможности

- ✅ **Модульная архитектура**: Разделение функционала на независимые модули
- ✅ **Лицензионный контроль**: Включение/выключение модулей на уровне организации
- ✅ **Backend защита**: Автоматическая защита API endpoints через middleware
- ✅ **Frontend скрытие**: Динамическое скрытие UI элементов для недоступных модулей
- ✅ **Версионирование**: Поддержка версий модулей
- ✅ **Feature Limits**: Лимиты использования (количество записей, API calls, и т.д.)
- ✅ **Аудит**: Логирование всех событий (включение, отключение, превышение лимитов)
- ✅ **Срок действия**: Поддержка временных лицензий с датой истечения

---

## Архитектура

### Database Schema

```
┌─────────────┐
│   modules   │ ──┐
└─────────────┘   │
                  │ Many-to-Many
┌─────────────────┴──────┐
│ organization_modules   │
└────────────────────────┘
                  │
                  ├──> feature_limits (опционально)
                  └──> module_events (audit log)
```

**4 основные таблицы:**

1. **modules** - Справочник доступных модулей
2. **organization_modules** - Связь организаций с модулями (лицензии)
3. **feature_limits** - Лимиты использования (опционально)
4. **module_events** - Аудит событий

### Workflow

```
1. ADMIN включает модуль для организации
   ↓
2. Backend: require_module() проверяет доступ к API
   ↓
3. Frontend: hasModule() показывает/скрывает UI
   ↓
4. User использует функционал модуля
   ↓
5. System логирует события и проверяет лимиты
```

---

## Доступные модули

### 1. BUDGET_CORE (Базовый модуль)
- **Описание**: Основной функционал бюджетирования
- **Функции**: Заявки на расход, категории, контрагенты, бюджет
- **Статус**: Всегда включен для всех организаций
- **Icon**: 💰

### 2. AI_FORECAST (AI-прогнозирование)
- **Описание**: AI-powered прогнозирование и банковские транзакции
- **Функции**:
  - Прогноз расходов с ML
  - Банковские транзакции с AI-классификацией
  - Smart matching транзакций с заявками
  - Определение регулярных платежей
- **Icon**: 🤖

### 3. CREDIT_PORTFOLIO (Кредитный портфель)
- **Описание**: Управление финансовым портфелем
- **Функции**:
  - Управление организациями и счетами
  - Кредитные договоры
  - Поступления и расходы
  - FTP автоматический импорт
  - Аналитика и KPI
- **Icon**: 💼

### 4. REVENUE_BUDGET (Бюджет доходов)
- **Описание**: Планирование и учет доходов
- **Функции**:
  - Источники доходов и категории
  - Планирование с версионированием
  - Учет фактических доходов
  - Customer LTV метрики
  - Коэффициенты сезонности
  - Plan vs Actual аналитика
- **Icon**: 📈

### 5. PAYROLL_KPI (KPI и бонусы)
- **Описание**: Система KPI для сотрудников
- **Функции**:
  - Управление целями KPI
  - Трекинг достижений
  - Расчет премий на основе KPI
  - Аналитика производительности
- **Icon**: 🎯

### 6. INTEGRATIONS_1C (Интеграция с 1С)
- **Описание**: Синхронизация с 1С через OData
- **Функции**:
  - Синхронизация заявок на расход
  - Синхронизация справочников (организации, категории, контрагенты)
  - Импорт банковских операций
  - Автоматический scheduled sync
- **Icon**: 🔄

### 7. FOUNDER_DASHBOARD (Дашборд учредителя)
- **Описание**: Executive dashboard для руководства
- **Функции**:
  - Кросс-департментские KPI
  - P&L отчеты
  - Cash flow прогнозы
  - Топ контрагенты и расходы
- **Доступ**: Только для роли FOUNDER
- **Icon**: 👔

### 8. ADVANCED_ANALYTICS (Расширенная аналитика)
- **Описание**: Углубленная аналитика и отчеты
- **Функции**:
  - Расширенные дашборды
  - Кастомные отчеты
  - Экспорт в Excel/PDF
  - Визуализация данных
- **Icon**: 📊

### 9. MULTI_DEPARTMENT (Мультиотдельность)
- **Описание**: Управление несколькими отделами
- **Функции**:
  - Создание и управление отделами
  - Переключение между отделами
  - Кросс-департментская аналитика
- **Доступ**: Для MANAGER/ADMIN ролей
- **Icon**: 🏢

---

## Backend: Использование

### 1. Защита API endpoints

#### Базовый пример

```python
from fastapi import APIRouter, Depends
from app.core.module_guard import require_module
from app.utils.auth import get_current_active_user

router = APIRouter()

@router.get("/credit-portfolio/contracts")
def get_contracts(
    module_access = Depends(require_module("CREDIT_PORTFOLIO")),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint доступен только если модуль CREDIT_PORTFOLIO включен
    """
    # module_access содержит информацию о модуле
    return db.query(Contract).all()
```

#### С проверкой лимитов

```python
from app.core.module_guard import require_module, check_feature_limit

@router.post("/ai-forecast/predictions")
def create_prediction(
    module_access = Depends(require_module("AI_FORECAST")),
    limit_check = Depends(check_feature_limit("AI_FORECAST", "api_calls_per_month")),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Проверяет доступ к модулю И лимиты использования
    """
    # Если лимит превышен, вернет 403 Forbidden
    # Автоматически инкрементит счетчик после успешного выполнения
    return {"prediction": "..."}
```

#### Инкремент использования

```python
from app.core.module_guard import increment_feature_usage

@router.post("/revenue/actuals")
def create_revenue_actual(
    module_access = Depends(require_module("REVENUE_BUDGET")),
    usage_increment = Depends(increment_feature_usage("REVENUE_BUDGET", "records_created", 1)),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Автоматически увеличивает счетчик использования
    """
    # После создания записи, счетчик увеличится на 1
    revenue_actual = RevenueActual(...)
    db.add(revenue_actual)
    db.commit()
    return revenue_actual
```

### 2. Программная проверка модулей

```python
from app.services.module_service import ModuleService

# В любом месте backend кода
module_service = ModuleService(db)

# Проверить доступ к модулю
if module_service.is_module_enabled(
    organization_id=current_user.organization_id,
    module_code="AI_FORECAST"
):
    # Выполнить функционал AI_FORECAST
    run_ai_forecast()

# Получить все включенные модули
enabled = module_service.get_enabled_modules(
    organization_id=current_user.organization_id
)
```

### 3. Управление модулями (ADMIN только)

```python
from app.services.module_service import ModuleService

module_service = ModuleService(db)

# Включить модуль для организации
module_service.enable_module_for_organization(
    organization_id=1,
    module_code="CREDIT_PORTFOLIO",
    expires_at=datetime(2026, 12, 31),  # Опционально
    limits={"max_contracts": 100},       # Опционально
    enabled_by_user_id=current_user.id
)

# Отключить модуль
module_service.disable_module_for_organization(
    organization_id=1,
    module_code="CREDIT_PORTFOLIO",
    disabled_by_user_id=current_user.id
)

# Проверить лимит
module_service.check_feature_limit(
    organization_id=1,
    module_code="AI_FORECAST",
    limit_type="api_calls_per_month"
)

# Увеличить использование
module_service.increment_usage(
    organization_id=1,
    module_code="AI_FORECAST",
    limit_type="api_calls_per_month",
    increment=1
)
```

---

## Frontend: Использование

### 1. React Context (useModules hook)

```typescript
import { useModules } from '@/contexts/ModulesContext'

const MyComponent = () => {
  const {
    modules,           // Array<EnabledModuleInfo>
    hasModule,         // (code: string) => boolean
    getModule,         // (code: string) => EnabledModuleInfo | undefined
    isModuleExpired,   // (code: string) => boolean
    isLoading,         // boolean
    isError            // boolean
  } = useModules()

  // Простая проверка
  if (hasModule('CREDIT_PORTFOLIO')) {
    return <CreditPortfolioFeature />
  }

  // Получить информацию о модуле
  const aiModule = getModule('AI_FORECAST')
  console.log('Expires at:', aiModule?.expires_at)

  // Проверка на истечение
  if (isModuleExpired('REVENUE_BUDGET')) {
    return <LicenseExpiredWarning />
  }

  return null
}
```

### 2. ModuleGate Component

#### Простое скрытие

```typescript
import { ModuleGate } from '@/components/common/ModuleGate'

const Dashboard = () => (
  <div>
    <h1>Dashboard</h1>

    {/* Показывается только если модуль включен */}
    <ModuleGate moduleCode="AI_FORECAST">
      <AiForecastWidget />
    </ModuleGate>

    {/* Показывается только если модуль включен */}
    <ModuleGate moduleCode="CREDIT_PORTFOLIO">
      <CreditPortfolioSummary />
    </ModuleGate>
  </div>
)
```

#### С fallback

```typescript
<ModuleGate
  moduleCode="ADVANCED_ANALYTICS"
  fallback={<UpgradePrompt moduleName="Advanced Analytics" />}
>
  <AdvancedReports />
</ModuleGate>
```

#### С кастомным сообщением

```typescript
<ModuleGate
  moduleCode="PAYROLL_KPI"
  showMessage={true}
  message="Для доступа к KPI системе необходим модуль PAYROLL_KPI"
>
  <KpiDashboard />
</ModuleGate>
```

### 3. Higher-Order Component (HOC)

```typescript
import { ModuleGuard } from '@/components/common/ModuleGate'

// Защитить целую страницу
const CreditPortfolioPage = () => {
  return <div>Credit Portfolio Content</div>
}

export default ModuleGuard(CreditPortfolioPage, 'CREDIT_PORTFOLIO')
```

### 4. Динамическое меню (пример из AppLayout)

```typescript
import { useModules } from '@/contexts/ModulesContext'

const AppLayout = () => {
  const { hasModule } = useModules()

  const menuItems = [
    // Всегда показывается
    {
      key: '/dashboard',
      label: 'Dashboard'
    },

    // Условное отображение
    ...(hasModule('CREDIT_PORTFOLIO') ? [{
      key: '/credit-portfolio',
      label: 'Credit Portfolio'
    }] : []),

    // Вложенное меню
    ...(hasModule('AI_FORECAST') || hasModule('CREDIT_PORTFOLIO') ? [{
      key: 'finance-submenu',
      label: 'Finance',
      children: [
        ...(hasModule('AI_FORECAST') ? [{
          key: '/bank-transactions',
          label: 'Bank Transactions'
        }] : []),
        ...(hasModule('CREDIT_PORTFOLIO') ? [{
          key: '/credit-portfolio',
          label: 'Credit Portfolio'
        }] : [])
      ]
    }] : [])
  ]

  return <Menu items={menuItems} />
}
```

### 5. Условный рендеринг в компонентах

```typescript
const EmployeePage = () => {
  const { hasModule } = useModules()

  return (
    <div>
      <h1>Employees</h1>

      {/* Базовая таблица сотрудников */}
      <EmployeeTable />

      {/* KPI секция только если модуль включен */}
      {hasModule('PAYROLL_KPI') && (
        <div>
          <h2>KPI Metrics</h2>
          <KpiMetricsTable />
        </div>
      )}
    </div>
  )
}
```

---

## API Reference

### Backend API Endpoints

**Base URL**: `/api/v1/modules`

#### 1. Получить все модули
```http
GET /api/v1/modules
```
**Query Parameters:**
- `active_only` (bool, default: true) - Только активные модули

**Response:**
```json
[
  {
    "id": 1,
    "code": "AI_FORECAST",
    "name": "AI Forecast & Bank Transactions",
    "description": "AI-powered forecasting and bank transaction classification",
    "version": "1.0.0",
    "is_active": true
  }
]
```

#### 2. Получить включенные модули для текущей организации
```http
GET /api/v1/modules/enabled/my
```
**Query Parameters:**
- `include_expired` (bool, default: false) - Включить истекшие модули

**Response:**
```json
{
  "modules": [
    {
      "code": "BUDGET_CORE",
      "name": "Budget Core",
      "enabled_at": "2025-01-01T00:00:00Z",
      "expires_at": null,
      "is_expired": false,
      "limits": {}
    },
    {
      "code": "AI_FORECAST",
      "name": "AI Forecast",
      "enabled_at": "2025-01-01T00:00:00Z",
      "expires_at": "2026-01-01T00:00:00Z",
      "is_expired": false,
      "limits": {
        "api_calls_per_month": 10000
      }
    }
  ],
  "organization_id": 1,
  "organization_name": "IT Department"
}
```

#### 3. Включить модуль (ADMIN только)
```http
POST /api/v1/modules/enable
```
**Body:**
```json
{
  "module_code": "CREDIT_PORTFOLIO",
  "organization_id": 1,
  "expires_at": "2026-12-31T23:59:59Z",
  "limits": {
    "max_contracts": 100,
    "max_organizations": 10
  }
}
```

#### 4. Отключить модуль (ADMIN только)
```http
POST /api/v1/modules/disable
```
**Body:**
```json
{
  "module_code": "CREDIT_PORTFOLIO",
  "organization_id": 1
}
```

#### 5. Получить события модулей (ADMIN только)
```http
GET /api/v1/modules/events/
```
**Query Parameters:**
- `organization_id` (int) - Фильтр по организации
- `module_code` (string) - Фильтр по коду модуля
- `event_type` (string) - Тип события
- `skip` (int, default: 0) - Пагинация
- `limit` (int, default: 100, max: 500) - Лимит результатов

#### 6. Получить статистику модулей (ADMIN только)
```http
GET /api/v1/modules/statistics/
```

**Response:**
```json
[
  {
    "module_code": "AI_FORECAST",
    "module_name": "AI Forecast",
    "total_organizations": 5,
    "active_organizations": 4,
    "expired_organizations": 1,
    "total_events": 127
  }
]
```

---

## Добавление нового модуля

### Шаг 1: Добавить в seed script

**Файл**: `backend/scripts/seed_modules.py`

```python
modules = [
    # ... existing modules ...
    {
        "code": "NEW_MODULE",
        "name": "New Module Name",
        "description": "Description of new module functionality",
        "version": "1.0.0",
        "icon": "🆕",
        "sort_order": 100,
        "is_active": True
    }
]
```

### Шаг 2: Добавить в TypeScript enum

**Файл**: `frontend/src/types/module.ts`

```typescript
export enum ModuleCode {
  // ... existing modules ...
  NEW_MODULE = 'NEW_MODULE',
}
```

### Шаг 3: Защитить backend endpoints

```python
@router.get("/new-feature/data")
def get_new_feature_data(
    module_access = Depends(require_module("NEW_MODULE")),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return {"data": "protected by NEW_MODULE"}
```

### Шаг 4: Добавить в frontend menu (AppLayout)

**Файл**: `frontend/src/components/common/AppLayout.tsx`

```typescript
...(hasModule('NEW_MODULE') ? [{
  key: '/new-feature',
  icon: <NewIcon />,
  label: <Link to='/new-feature'>New Feature</Link>
}] : []),
```

### Шаг 5: Защитить страницы и компоненты

```typescript
// Вариант 1: ModuleGate
<ModuleGate moduleCode="NEW_MODULE">
  <NewFeatureComponent />
</ModuleGate>

// Вариант 2: HOC
export default ModuleGuard(NewFeaturePage, 'NEW_MODULE')

// Вариант 3: useModules hook
const { hasModule } = useModules()
if (!hasModule('NEW_MODULE')) {
  return <NoAccessPage />
}
```

### Шаг 6: Запустить seed script

```bash
cd backend
python scripts/seed_modules.py
```

### Шаг 7: Включить модуль для тестовой организации

```bash
# Через API
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "NEW_MODULE",
    "organization_id": 1
  }'

# Или через SQL
INSERT INTO organization_modules (organization_id, module_id, is_active)
SELECT 1, id, true FROM modules WHERE code = 'NEW_MODULE';
```

---

## Типичные сценарии использования

### Сценарий 1: Проверка доступа к модулю перед отображением кнопки

```typescript
import { useModules } from '@/contexts/ModulesContext'

const Dashboard = () => {
  const { hasModule } = useModules()

  return (
    <div>
      {hasModule('AI_FORECAST') && (
        <Button onClick={openAIForecast}>
          Run AI Forecast
        </Button>
      )}
    </div>
  )
}
```

### Сценарий 2: Защита целой страницы

```typescript
// pages/CreditPortfolioPage.tsx
import { ModuleGuard } from '@/components/common/ModuleGate'

const CreditPortfolioPage = () => {
  return <div>Credit Portfolio Content</div>
}

export default ModuleGuard(CreditPortfolioPage, 'CREDIT_PORTFOLIO')
```

### Сценарий 3: Динамическое меню с вложенными элементами

```typescript
const menuItems = [
  ...(hasModule('AI_FORECAST') || hasModule('CREDIT_PORTFOLIO') ? [{
    key: 'finance',
    label: 'Finance',
    children: [
      ...(hasModule('AI_FORECAST') ? [
        { key: 'bank-transactions', label: 'Bank Transactions' }
      ] : []),
      ...(hasModule('CREDIT_PORTFOLIO') ? [
        { key: 'credit-portfolio', label: 'Credit Portfolio' }
      ] : [])
    ]
  }] : [])
]
```

### Сценарий 4: Backend endpoint с лимитами

```python
@router.post("/ai/forecast")
def create_forecast(
    module_access = Depends(require_module("AI_FORECAST")),
    limit_check = Depends(check_feature_limit("AI_FORECAST", "forecasts_per_month")),
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    - Проверяет доступ к AI_FORECAST
    - Проверяет лимит forecasts_per_month
    - Автоматически инкрементит счетчик после успеха
    """
    forecast = create_ai_forecast(data)
    return forecast
```

### Сценарий 5: Уведомление об истечении лицензии

```typescript
import { useModules } from '@/contexts/ModulesContext'

const LicenseAlert = () => {
  const { modules } = useModules()

  const expiringModules = modules.filter(m => {
    if (!m.expires_at) return false
    const daysLeft = differenceInDays(new Date(m.expires_at), new Date())
    return daysLeft > 0 && daysLeft <= 30
  })

  if (expiringModules.length === 0) return null

  return (
    <Alert type="warning">
      Следующие модули истекают в течение 30 дней:
      <ul>
        {expiringModules.map(m => (
          <li key={m.code}>{m.name} - {m.expires_at}</li>
        ))}
      </ul>
    </Alert>
  )
}
```

---

## Тестирование

### Backend Tests

```python
# tests/test_modules.py
import pytest
from app.services.module_service import ModuleService

def test_module_enabled():
    """Test module access check"""
    module_service = ModuleService(db)

    # Enable module
    module_service.enable_module_for_organization(
        organization_id=1,
        module_code="AI_FORECAST"
    )

    # Check access
    assert module_service.is_module_enabled(1, "AI_FORECAST") == True
    assert module_service.is_module_enabled(1, "NONEXISTENT") == False

def test_feature_limits():
    """Test feature limit enforcement"""
    module_service = ModuleService(db)

    # Set limit
    module_service.enable_module_for_organization(
        organization_id=1,
        module_code="AI_FORECAST",
        limits={"api_calls": 100}
    )

    # Increment usage
    for i in range(100):
        module_service.increment_usage(1, "AI_FORECAST", "api_calls", 1)

    # Should raise exception on 101st call
    with pytest.raises(HTTPException):
        module_service.check_feature_limit(1, "AI_FORECAST", "api_calls")
```

### Frontend Tests

```typescript
// components/ModuleGate.test.tsx
import { render, screen } from '@testing-library/react'
import { ModuleGate } from './ModuleGate'
import { ModulesProvider } from '@/contexts/ModulesContext'

const mockModules = {
  modules: [{ code: 'AI_FORECAST', name: 'AI Forecast', is_expired: false }],
  hasModule: (code: string) => code === 'AI_FORECAST'
}

test('shows content when module enabled', () => {
  render(
    <ModulesProvider value={mockModules}>
      <ModuleGate moduleCode="AI_FORECAST">
        <div>Protected Content</div>
      </ModuleGate>
    </ModulesProvider>
  )

  expect(screen.getByText('Protected Content')).toBeInTheDocument()
})

test('hides content when module disabled', () => {
  render(
    <ModulesProvider value={mockModules}>
      <ModuleGate moduleCode="NONEXISTENT">
        <div>Protected Content</div>
      </ModuleGate>
    </ModulesProvider>
  )

  expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
})
```

---

## Troubleshooting

### Проблема: "Module not found"

**Причина**: Модуль не создан в таблице `modules`

**Решение**:
```bash
cd backend
python scripts/seed_modules.py
```

### Проблема: "Access denied" даже если модуль включен

**Причина**: Модуль включен, но истек срок действия или лимит превышен

**Решение**:
```sql
-- Проверить статус модуля
SELECT om.*, m.code, m.name
FROM organization_modules om
JOIN modules m ON m.id = om.module_id
WHERE om.organization_id = 1;

-- Проверить лимиты
SELECT * FROM feature_limits
WHERE organization_module_id IN (
  SELECT id FROM organization_modules WHERE organization_id = 1
);

-- Продлить срок действия
UPDATE organization_modules
SET expires_at = '2026-12-31'
WHERE organization_id = 1 AND module_id = (
  SELECT id FROM modules WHERE code = 'AI_FORECAST'
);
```

### Проблема: Frontend не скрывает элементы

**Причина**: ModulesProvider не обернул компонент

**Решение**: Убедитесь что App.tsx содержит:
```typescript
<ModulesProvider>
  <YourApp />
</ModulesProvider>
```

### Проблема: "Cannot read property 'hasModule' of undefined"

**Причина**: useModules() вызван вне ModulesProvider

**Решение**: Переместите компонент внутрь ModulesProvider или используйте optional chaining:
```typescript
const { hasModule } = useModules() ?? { hasModule: () => false }
```

---

## Best Practices

### 1. ✅ Всегда используйте require_module() для защиты API

```python
# ✅ Good
@router.get("/feature")
def get_feature(
    module_access = Depends(require_module("MODULE_CODE")),
    current_user = Depends(get_current_active_user)
):
    pass

# ❌ Bad
@router.get("/feature")
def get_feature(current_user = Depends(get_current_active_user)):
    # Нет защиты модулем!
    pass
```

### 2. ✅ Используйте ModuleGate для условного рендеринга

```typescript
// ✅ Good
<ModuleGate moduleCode="AI_FORECAST">
  <AiFeature />
</ModuleGate>

// ❌ Bad - прямая проверка без ModuleGate
{hasModule('AI_FORECAST') ? <AiFeature /> : null}
```

### 3. ✅ Группируйте связанные функции в один модуль

```python
# ✅ Good - все AI функции в одном модуле
AI_FORECAST включает:
- Прогнозирование
- Банковские транзакции
- Smart matching

# ❌ Bad - слишком детальное разделение
AI_FORECAST_PREDICTIONS
AI_FORECAST_BANK_TRANSACTIONS
AI_FORECAST_MATCHING
```

### 4. ✅ Логируйте важные события

```python
# ModuleService автоматически логирует:
# - MODULE_ENABLED
# - MODULE_DISABLED
# - LIMIT_EXCEEDED
# - ACCESS_DENIED

# Для кастомных событий:
module_service.log_event(
    organization_id=1,
    module_id=module.id,
    event_type="CUSTOM_EVENT",
    metadata={"custom": "data"}
)
```

### 5. ✅ Устанавливайте реалистичные лимиты

```python
# ✅ Good
limits = {
    "api_calls_per_month": 10000,      # Достаточно для нормального использования
    "max_records": 1000,                # Разумный лимит
    "concurrent_users": 50              # Реалистичное число
}

# ❌ Bad
limits = {
    "api_calls_per_month": 10,          # Слишком мало
    "max_records": 999999999            # Бесполезный лимит
}
```

---

## Migration Guide (для существующих функций)

Если нужно добавить module protection к существующим endpoints:

### Backend

**До:**
```python
@router.get("/credit-portfolio/contracts")
def get_contracts(
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Contract).all()
```

**После:**
```python
@router.get("/credit-portfolio/contracts")
def get_contracts(
    module_access = Depends(require_module("CREDIT_PORTFOLIO")),  # ← Добавить
    current_user = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Contract).all()
```

### Frontend

**До:**
```typescript
const CreditPortfolioPage = () => {
  return <div>Content</div>
}
```

**После:**
```typescript
import { ModuleGuard } from '@/components/common/ModuleGate'

const CreditPortfolioPage = () => {
  return <div>Content</div>
}

export default ModuleGuard(CreditPortfolioPage, 'CREDIT_PORTFOLIO')  // ← Добавить
```

---

## Дополнительные ресурсы

- **Спецификация**: [MODULE_ENABLEMENT_SPEC.md](../MODULE_ENABLEMENT_SPEC.md)
- **API Документация**: http://localhost:8000/docs
- **Database Models**: [backend/app/db/models.py](../backend/app/db/models.py)
- **Frontend Types**: [frontend/src/types/module.ts](../frontend/src/types/module.ts)
- **Seed Script**: [backend/scripts/seed_modules.py](../backend/scripts/seed_modules.py)

---

## Заключение

Module System предоставляет гибкую и масштабируемую архитектуру для управления доступом к функциям приложения. Система автоматически защищает как backend API, так и frontend UI, обеспечивая последовательный контроль доступа на всех уровнях приложения.

**Основные преимущества:**
- ✅ Централизованное управление доступом
- ✅ Автоматическая защита API и UI
- ✅ Гибкие лимиты использования
- ✅ Полный аудит событий
- ✅ Поддержка временных лицензий
- ✅ Простота добавления новых модулей
