# Module System - Руководство по развертыванию и использованию

## 📋 Текущее состояние

После реализации Module System у нас есть:

✅ **Backend**:
- 4 новые таблицы в БД (modules, organization_modules, feature_limits, module_events)
- ModuleService для управления модулями
- require_module() middleware для защиты API
- API endpoints `/api/v1/modules/*` для управления

✅ **Frontend**:
- ModulesContext для доступа к модулям
- ModuleGate компонент для условного рендеринга
- Динамическое меню в AppLayout
- TypeScript типы и API клиент

## 🎯 Как это работает

### Концепция

```
┌─────────────────────────────────────────────────────────┐
│                     ОРГАНИЗАЦИЯ                         │
│                                                         │
│  Включенные модули:                                     │
│  ✅ BUDGET_CORE (всегда)                               │
│  ✅ AI_FORECAST (до 2026-12-31)                        │
│  ✅ CREDIT_PORTFOLIO                                   │
│  ❌ REVENUE_BUDGET (не куплен)                         │
│  ❌ PAYROLL_KPI (не куплен)                            │
└─────────────────────────────────────────────────────────┘
           │
           ↓
┌──────────────────────┬──────────────────────────────────┐
│   BACKEND            │   FRONTEND                       │
│                      │                                  │
│  API Endpoint        │   UI Menu                        │
│  ✅ /expenses        │   ✅ Заявки                     │
│  ✅ /budget          │   ✅ Бюджет                     │
│  ✅ /bank-trans...   │   ✅ Банк. транзакции           │
│  ✅ /credit-port...  │   ✅ Кредитный портфель         │
│  ❌ /revenue/*       │   ❌ Доходы (скрыто)            │
│  ❌ /payroll/kpi     │   ❌ KPI (скрыто)               │
└──────────────────────┴──────────────────────────────────┘
```

### Автоматическая защита

**Backend**: Если модуль не включен → 403 Forbidden
```python
@router.get("/credit-portfolio/contracts")
def get_contracts(
    module_access = Depends(require_module("CREDIT_PORTFOLIO"))  # ← Автопроверка
):
    # Если CREDIT_PORTFOLIO выключен, пользователь получит 403
    return contracts
```

**Frontend**: Если модуль не включен → элемент скрыт
```typescript
<ModuleGate moduleCode="CREDIT_PORTFOLIO">
  {/* Показывается только если модуль включен */}
  <CreditPortfolioWidget />
</ModuleGate>
```

---

## 🔧 Шаг 1: Применить миграции БД

### 1.1 Проверить текущее состояние БД

```bash
cd backend

# Проверить текущую ревизию
alembic current

# Должно показать что-то вроде:
# 7265be4a81c3 (head)
```

### 1.2 Применить миграции модулей

```bash
# Применить все миграции (включая модули)
alembic upgrade head

# Вывод должен показать:
# INFO  [alembic.runtime.migration] Running upgrade ... -> ..., add modules tables
```

### 1.3 Проверить создание таблиц

```bash
# Подключиться к БД
docker exec -it it_budget_db psql -U budget_user -d it_budget_db

# Проверить таблицы
\dt

# Должны быть:
# modules
# organization_modules
# feature_limits
# module_events
```

---

## 📦 Шаг 2: Загрузить модули в БД

### 2.1 Запустить seed script

```bash
cd backend

# Убедиться что venv активирован
source venv/bin/activate

# Запустить seed
python scripts/seed_modules.py
```

**Вывод должен быть:**
```
Starting module seed...
Creating module: BUDGET_CORE - Budget Core Module
Creating module: AI_FORECAST - AI Forecast & Bank Transactions
Creating module: CREDIT_PORTFOLIO - Credit Portfolio Management
Creating module: REVENUE_BUDGET - Revenue Budget Planning
Creating module: PAYROLL_KPI - Payroll KPI & Bonuses
Creating module: INTEGRATIONS_1C - 1C OData Integration
Creating module: FOUNDER_DASHBOARD - Founder Executive Dashboard
Creating module: ADVANCED_ANALYTICS - Advanced Analytics & Reports
Creating module: MULTI_DEPARTMENT - Multi-Department Management

✓ Successfully created 9 modules
Module seed completed!
```

### 2.2 Проверить загрузку

```sql
-- В psql
SELECT code, name, is_active FROM modules;

-- Должно показать 9 модулей
```

---

## 🔑 Шаг 3: Включить модули для организаций

### Вариант A: Через SQL (быстро для теста)

```bash
# Подключиться к БД
docker exec -it it_budget_db psql -U budget_user -d it_budget_db
```

```sql
-- Включить ВСЕ модули для организации с ID=1
INSERT INTO organization_modules (organization_id, module_id, is_active, enabled_at)
SELECT 1, id, true, NOW()
FROM modules
WHERE is_active = true
ON CONFLICT DO NOTHING;

-- Проверить
SELECT
  m.code,
  m.name,
  om.is_active,
  om.enabled_at,
  om.expires_at
FROM organization_modules om
JOIN modules m ON m.id = om.module_id
WHERE om.organization_id = 1;
```

### Вариант B: Через API (рекомендуется для продакшена)

```bash
# 1. Получить токен администратора
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# 2. Включить модуль AI_FORECAST
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 1,
    "expires_at": "2026-12-31T23:59:59Z",
    "limits": {
      "api_calls_per_month": 100000
    }
  }'

# 3. Включить CREDIT_PORTFOLIO
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "CREDIT_PORTFOLIO",
    "organization_id": 1,
    "expires_at": "2026-12-31T23:59:59Z"
  }'

# 4. Включить REVENUE_BUDGET
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "REVENUE_BUDGET",
    "organization_id": 1
  }'

# 5. Включить PAYROLL_KPI
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "PAYROLL_KPI",
    "organization_id": 1
  }'
```

### Включить для ВСЕХ организаций (опционально)

```sql
-- Включить базовые модули для всех организаций
INSERT INTO organization_modules (organization_id, module_id, is_active, enabled_at)
SELECT o.id, m.id, true, NOW()
FROM organizations o
CROSS JOIN modules m
WHERE m.code IN ('BUDGET_CORE', 'AI_FORECAST', 'CREDIT_PORTFOLIO')
ON CONFLICT DO NOTHING;
```

---

## 🌐 Шаг 4: Перезапустить frontend и backend

### 4.1 Перезапустить backend

```bash
# Если используете ./run.sh
./stop.sh
./run.sh

# Или вручную
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### 4.2 Перезапустить frontend

```bash
cd frontend
npm run dev
```

### 4.3 Очистить кэш браузера

```
Ctrl+Shift+R (или Cmd+Shift+R на Mac)
```

---

## ✅ Шаг 5: Проверка работы

### 5.1 Проверка через API

```bash
# Получить токен пользователя организации 1
USER_TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_user&password=your_password" | jq -r '.access_token')

# Получить включенные модули
curl "http://localhost:8000/api/v1/modules/enabled/my" \
  -H "Authorization: Bearer $USER_TOKEN"

# Должен вернуть список включенных модулей:
# {
#   "modules": [
#     {
#       "code": "BUDGET_CORE",
#       "name": "Budget Core Module",
#       "enabled_at": "2025-11-19T...",
#       "expires_at": null,
#       "is_expired": false
#     },
#     {
#       "code": "AI_FORECAST",
#       "name": "AI Forecast & Bank Transactions",
#       "enabled_at": "2025-11-19T...",
#       "expires_at": "2026-12-31T23:59:59Z",
#       "is_expired": false
#     }
#   ],
#   "organization_id": 1,
#   "organization_name": "IT Department"
# }
```

### 5.2 Проверка в UI

1. **Войти в систему**
   - Открыть http://localhost:5173
   - Войти как пользователь организации 1

2. **Проверить меню**
   - Должны быть видны разделы для включенных модулей:
     - ✅ Финансы → Банковские операции (если AI_FORECAST включен)
     - ✅ Финансы → Кредитный портфель (если CREDIT_PORTFOLIO включен)
     - ✅ Доходы (если REVENUE_BUDGET включен)
     - ✅ ФОТ → KPI сотрудников (если PAYROLL_KPI включен)

3. **Проверить скрытие**
   - Отключить модуль через API
   - Обновить страницу (F5)
   - Раздел должен исчезнуть из меню

### 5.3 Тест API защиты

```bash
# Попробовать получить данные защищенного модуля
curl "http://localhost:8000/api/v1/credit-portfolio/contracts" \
  -H "Authorization: Bearer $USER_TOKEN"

# Если модуль включен → 200 OK с данными
# Если модуль НЕ включен → 403 Forbidden:
# {
#   "detail": "Access denied: Module CREDIT_PORTFOLIO not enabled for your organization"
# }
```

---

## 🎮 Практические сценарии использования

### Сценарий 1: Новый клиент с базовой лицензией

```sql
-- Создать организацию
INSERT INTO organizations (full_name, short_name, inn)
VALUES ('ООО Новый Клиент', 'НовыйКлиент', '1234567890');

-- Включить только базовые модули
INSERT INTO organization_modules (organization_id, module_id, is_active)
SELECT
  (SELECT id FROM organizations WHERE short_name = 'НовыйКлиент'),
  id,
  true
FROM modules
WHERE code IN ('BUDGET_CORE');
```

**Результат**: Клиент видит только базовый функционал (заявки, бюджет, категории)

### Сценарий 2: Апгрейд лицензии

```bash
# Клиент купил AI_FORECAST
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 2,
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

**Результат**: У клиента автоматически появляются:
- Раздел "Банковские операции"
- AI-классификация транзакций
- Прогнозирование расходов

### Сценарий 3: Пробный период (trial)

```bash
# Включить на 30 дней
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"module_code\": \"CREDIT_PORTFOLIO\",
    \"organization_id\": 3,
    \"expires_at\": \"$(date -u -d '+30 days' '+%Y-%m-%dT%H:%M:%SZ')\"
  }"
```

**Результат**: Через 30 дней модуль автоматически отключится

### Сценарий 4: Лимиты использования

```bash
# Включить с лимитом API calls
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 4,
    "limits": {
      "api_calls_per_month": 1000,
      "max_bank_transactions": 5000
    }
  }'
```

**Результат**: При превышении 1000 API calls в месяц → 403 Forbidden

---

## 🔒 Защита существующих endpoints (Optional)

Если хотите добавить защиту к существующим endpoints:

### Пример: Защитить Credit Portfolio

```python
# backend/app/api/v1/credit_portfolio.py

# До:
@router.get("/contracts")
def get_contracts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Contract).all()

# После:
from app.core.module_guard import require_module

@router.get("/contracts")
def get_contracts(
    module_access = Depends(require_module("CREDIT_PORTFOLIO")),  # ← Добавить эту строку
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Contract).all()
```

### Пример: Защитить страницу Revenue

```typescript
// frontend/src/pages/RevenueStreamsPage.tsx

// До:
const RevenueStreamsPage = () => {
  return <div>Revenue content</div>
}
export default RevenueStreamsPage

// После:
import { ModuleGuard } from '@/components/common/ModuleGate'

const RevenueStreamsPage = () => {
  return <div>Revenue content</div>
}

export default ModuleGuard(RevenueStreamsPage, 'REVENUE_BUDGET')  // ← Добавить эту строку
```

---

## 📊 Мониторинг и управление

### Посмотреть статистику модулей (ADMIN)

```bash
curl "http://localhost:8000/api/v1/modules/statistics/" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
# [
#   {
#     "module_code": "AI_FORECAST",
#     "module_name": "AI Forecast",
#     "total_organizations": 5,
#     "active_organizations": 4,
#     "expired_organizations": 1,
#     "total_events": 127
#   }
# ]
```

### Посмотреть аудит событий (ADMIN)

```bash
curl "http://localhost:8000/api/v1/modules/events/?organization_id=1&limit=10" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Response:
# [
#   {
#     "id": 1,
#     "organization_id": 1,
#     "module_id": 2,
#     "event_type": "MODULE_ENABLED",
#     "created_by_id": 1,
#     "created_at": "2025-11-19T..."
#   },
#   {
#     "id": 2,
#     "organization_id": 1,
#     "module_id": 3,
#     "event_type": "LIMIT_EXCEEDED",
#     "event_metadata": {"limit_type": "api_calls_per_month"},
#     "created_at": "2025-11-19T..."
#   }
# ]
```

### SQL запросы для мониторинга

```sql
-- Какие модули включены для каждой организации
SELECT
  o.short_name as organization,
  m.code as module,
  om.enabled_at,
  om.expires_at,
  CASE
    WHEN om.expires_at IS NULL THEN 'Never'
    WHEN om.expires_at < NOW() THEN 'Expired'
    ELSE 'Active'
  END as status
FROM organization_modules om
JOIN organizations o ON o.id = om.organization_id
JOIN modules m ON m.id = om.module_id
WHERE om.is_active = true
ORDER BY o.short_name, m.code;

-- Модули которые скоро истекут (в течение 30 дней)
SELECT
  o.short_name,
  m.code,
  om.expires_at,
  om.expires_at - NOW() as time_left
FROM organization_modules om
JOIN organizations o ON o.id = om.organization_id
JOIN modules m ON m.id = om.module_id
WHERE om.expires_at IS NOT NULL
  AND om.expires_at > NOW()
  AND om.expires_at < NOW() + INTERVAL '30 days'
ORDER BY om.expires_at;

-- Топ событий по типам
SELECT
  event_type,
  COUNT(*) as count
FROM module_events
GROUP BY event_type
ORDER BY count DESC;
```

---

## ❓ FAQ и Troubleshooting

### Q: Модули не отображаются в меню после включения

**A**:
1. Проверьте что ModulesProvider обернут вокруг роутов в App.tsx
2. Очистите кэш браузера (Ctrl+Shift+R)
3. Проверьте React Query cache - может быть закеширован старый список
4. Проверьте в DevTools Network tab что `/api/v1/modules/enabled/my` возвращает нужные модули

### Q: 403 Forbidden на API endpoint

**A**:
1. Проверьте что модуль включен для организации пользователя
2. Проверьте что лицензия не истекла (`expires_at > NOW()`)
3. Проверьте лимиты использования в таблице `feature_limits`

```sql
-- Диагностика
SELECT
  m.code,
  om.is_active,
  om.expires_at,
  om.expires_at < NOW() as is_expired,
  fl.limit_type,
  fl.current_usage,
  fl.limit_value
FROM organization_modules om
JOIN modules m ON m.id = om.module_id
LEFT JOIN feature_limits fl ON fl.organization_module_id = om.id
WHERE om.organization_id = YOUR_ORG_ID;
```

### Q: Как добавить новый модуль?

**A**: См. раздел "Добавление нового модуля" в [MODULES_QUICKSTART.md](MODULES_QUICKSTART.md)

### Q: Как временно отключить модуль для тестирования?

**A**:
```bash
# Через API
curl -X POST "http://localhost:8000/api/v1/modules/disable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{"module_code": "AI_FORECAST", "organization_id": 1}'

# Через SQL
UPDATE organization_modules
SET is_active = false
WHERE organization_id = 1
  AND module_id = (SELECT id FROM modules WHERE code = 'AI_FORECAST');
```

---

## 🎯 Следующие шаги

1. ✅ **Применить миграции** (`alembic upgrade head`)
2. ✅ **Загрузить модули** (`python scripts/seed_modules.py`)
3. ✅ **Включить модули для организаций** (через SQL или API)
4. ✅ **Перезапустить приложение**
5. ✅ **Протестировать** доступ к модулям
6. 🔄 **Опционально**: Добавить защиту к существующим endpoints
7. 🔄 **Опционально**: Настроить лимиты и лицензии для клиентов

---

## 📚 Дополнительные ресурсы

- **[MODULES.md](./MODULES.md)** - Полная документация
- **[MODULES_QUICKSTART.md](./MODULES_QUICKSTART.md)** - Быстрый старт
- **[MODULE_ENABLEMENT_SPEC.md](../MODULE_ENABLEMENT_SPEC.md)** - Исходная спецификация
- **API Docs**: http://localhost:8000/docs#/Modules
