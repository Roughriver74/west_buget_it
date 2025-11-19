# Module System - Quick Start Guide

## 5-минутный старт

### 1. Инициализация БД

```bash
cd backend

# Создать таблицы модулей
alembic upgrade head

# Загрузить модули в БД
python scripts/seed_modules.py
```

### 2. Включить модули для организации

```sql
-- Через SQL (для быстрого теста)
-- Включить все модули для организации с ID=1
INSERT INTO organization_modules (organization_id, module_id, is_active, enabled_at)
SELECT 1, id, true, NOW()
FROM modules
WHERE is_active = true;
```

**Или через API:**

```bash
# Получить токен админа
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | jq -r '.access_token')

# Включить модуль AI_FORECAST
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 1,
    "expires_at": "2026-12-31T23:59:59Z"
  }'
```

### 3. Проверить доступные модули

```bash
# Через API (от имени пользователя организации)
curl "http://localhost:8000/api/v1/modules/enabled/my" \
  -H "Authorization: Bearer $USER_TOKEN"
```

### 4. Frontend автоматически обновится

После включения модулей:
- ✅ Меню автоматически покажет новые разделы
- ✅ Protected компоненты станут доступны
- ✅ API endpoints защищены

---

## Backend: Защита endpoints

### Минимальный пример

```python
from fastapi import APIRouter, Depends
from app.core.module_guard import require_module

router = APIRouter()

@router.get("/my-feature")
def get_my_feature(
    module_access = Depends(require_module("MY_MODULE")),
    current_user = Depends(get_current_active_user)
):
    return {"data": "protected"}
```

### С лимитами

```python
from app.core.module_guard import require_module, check_feature_limit

@router.post("/my-feature/action")
def do_action(
    module_access = Depends(require_module("MY_MODULE")),
    limit_check = Depends(check_feature_limit("MY_MODULE", "actions_per_month")),
    current_user = Depends(get_current_active_user)
):
    # Автоматически проверяет лимиты и инкрементит счетчик
    return {"success": True}
```

---

## Frontend: Условное отображение

### Вариант 1: useModules hook

```typescript
import { useModules } from '@/contexts/ModulesContext'

const MyComponent = () => {
  const { hasModule } = useModules()

  if (!hasModule('MY_MODULE')) {
    return <NoAccessMessage />
  }

  return <MyFeature />
}
```

### Вариант 2: ModuleGate component

```typescript
import { ModuleGate } from '@/components/common/ModuleGate'

const MyPage = () => (
  <div>
    <h1>My Page</h1>

    <ModuleGate moduleCode="MY_MODULE">
      <MyFeature />
    </ModuleGate>
  </div>
)
```

### Вариант 3: HOC для целых страниц

```typescript
import { ModuleGuard } from '@/components/common/ModuleGate'

const MyFeaturePage = () => {
  return <div>Feature content</div>
}

export default ModuleGuard(MyFeaturePage, 'MY_MODULE')
```

---

## Добавление нового модуля

### 1. Добавить в seed script

**Файл**: `backend/scripts/seed_modules.py`

```python
{
    "code": "NEW_FEATURE",
    "name": "New Feature Module",
    "description": "Description of the new feature",
    "version": "1.0.0",
    "icon": "🆕",
    "sort_order": 100,
    "is_active": True
}
```

### 2. Добавить в TypeScript enum

**Файл**: `frontend/src/types/module.ts`

```typescript
export enum ModuleCode {
  // ... existing
  NEW_FEATURE = 'NEW_FEATURE',
}
```

### 3. Защитить backend

```python
@router.get("/new-feature/data")
def get_data(
    module_access = Depends(require_module("NEW_FEATURE")),
    current_user = Depends(get_current_active_user)
):
    return {"data": "..."}
```

### 4. Добавить в меню

**Файл**: `frontend/src/components/common/AppLayout.tsx`

```typescript
...(hasModule('NEW_FEATURE') ? [{
  key: '/new-feature',
  icon: <NewIcon />,
  label: <Link to='/new-feature'>New Feature</Link>
}] : []),
```

### 5. Запустить seed и включить

```bash
# Загрузить новый модуль
python scripts/seed_modules.py

# Включить для организации
INSERT INTO organization_modules (organization_id, module_id, is_active)
SELECT 1, id, true FROM modules WHERE code = 'NEW_FEATURE';
```

---

## Проверка работы

### 1. Backend тесты

```bash
cd backend
pytest tests/test_modules.py -v
```

### 2. Проверка через API

```bash
# Получить все модули
curl "http://localhost:8000/api/v1/modules" \
  -H "Authorization: Bearer $TOKEN"

# Получить включенные модули для текущей организации
curl "http://localhost:8000/api/v1/modules/enabled/my" \
  -H "Authorization: Bearer $TOKEN"

# Получить статистику (ADMIN only)
curl "http://localhost:8000/api/v1/modules/statistics/" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### 3. Проверка в UI

1. Войти в систему
2. Открыть меню - должны быть видны только включенные модули
3. Попробовать перейти на защищенную страницу - должен быть доступ
4. Отключить модуль через API - страница должна скрыться

---

## Управление лицензиями

### Установить срок действия

```bash
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 1,
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

### Установить лимиты

```bash
curl -X POST "http://localhost:8000/api/v1/modules/enable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 1,
    "limits": {
      "api_calls_per_month": 10000,
      "max_records": 1000
    }
  }'
```

### Отключить модуль

```bash
curl -X POST "http://localhost:8000/api/v1/modules/disable" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "module_code": "AI_FORECAST",
    "organization_id": 1
  }'
```

---

## Troubleshooting

### Модуль не отображается в меню

**Проверка:**
```sql
-- Проверить что модуль включен и не истек
SELECT om.*, m.code, m.name
FROM organization_modules om
JOIN modules m ON m.id = om.module_id
WHERE om.organization_id = 1 AND om.is_active = true;
```

### 403 Forbidden на API endpoint

**Причины:**
1. Модуль не включен для организации
2. Лицензия истекла
3. Лимит использования превышен

**Проверка:**
```sql
-- Проверить статус модуля
SELECT
  m.code,
  om.is_active,
  om.expires_at,
  om.expires_at < NOW() as is_expired
FROM organization_modules om
JOIN modules m ON m.id = om.module_id
WHERE om.organization_id = 1;
```

### Frontend не обновляется после включения модуля

**Решение:**
1. Обновить страницу (F5)
2. Проверить что ModulesProvider обернут вокруг компонента
3. Проверить React Query cache (может быть закеширован старый список)

---

## Полная документация

📖 **[MODULES.md](./MODULES.md)** - Полное руководство по Module System

**Содержит:**
- Детальное описание архитектуры
- Все доступные модули
- API Reference
- Примеры использования
- Best practices
- Migration guide
