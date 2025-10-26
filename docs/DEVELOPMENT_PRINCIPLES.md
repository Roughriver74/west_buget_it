# 🔐 Принципы разработки IT Budget Manager

## ⚠️ КРИТИЧЕСКИ ВАЖНО - Читать перед любой разработкой!

Этот документ описывает **обязательные** принципы и архитектурные решения системы.
**ВСЯ новая разработка ДОЛЖНА следовать этим принципам!**

---

## 1. 🔐 JWT Авторизация - ОБЯЗАТЕЛЬНО

### Принцип:
**ВСЯ** функциональность системы работает **ТОЛЬКО** с JWT токеном авторизации.

### Правила:

#### Backend (FastAPI):
```python
# ✅ ПРАВИЛЬНО - каждый endpoint защищён
@router.get("/endpoint")
def get_data(
    current_user: User = Depends(get_current_active_user),  # ОБЯЗАТЕЛЬНО!
    db: Session = Depends(get_db)
):
    # Пользователь уже авторизован
    pass

# ✅ ПРАВИЛЬНО - роутер защищён целиком
router = APIRouter(dependencies=[Depends(get_current_active_user)])

# ❌ НЕПРАВИЛЬНО - endpoint без авторизации
@router.get("/endpoint")
def get_data(db: Session = Depends(get_db)):
    # КТО УГОДНО может вызвать этот endpoint!
    pass
```

#### Frontend (React):
```typescript
// ✅ ПРАВИЛЬНО - все страницы обёрнуты в ProtectedRoute
<Routes>
  <Route path="/dashboard" element={
    <ProtectedRoute>
      <DashboardPage />
    </ProtectedRoute>
  } />
</Routes>

// ✅ ПРАВИЛЬНО - токен автоматически добавляется к запросам
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### Текущая реализация:
- ✅ JWT токены генерируются при логине
- ✅ Токены хранятся в localStorage
- ✅ Все API endpoints защищены через `Depends(get_current_active_user)`
- ✅ Все страницы обёрнуты в `ProtectedRoute`
- ✅ Автоматический logout при истечении токена

---

## 2. 🏢 Привязка к отделам (Multi-tenancy) - ОБЯЗАТЕЛЬНО

### Принцип:
**ВСЕ** данные в системе **ДОЛЖНЫ** быть привязаны к отделу (department_id).

### Правила:

#### 1. Модели (Database):
```python
# ✅ ПРАВИЛЬНО - есть department_id
class BudgetCategory(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)  # ОБЯЗАТЕЛЬНО!

    # Relationship
    department = relationship("Department", back_populates="categories")

# ❌ НЕПРАВИЛЬНО - нет department_id
class SomeEntity(Base):
    __tablename__ = "some_entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    # Где department_id?! ❌
```

#### 2. API Endpoints (Backend):
```python
# ✅ ПРАВИЛЬНО - фильтрация по отделу
@router.get("/")
def get_items(
    department_id: Optional[int] = None,  # ОБЯЗАТЕЛЬНЫЙ параметр!
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Item)

    # Фильтрация по роли пользователя
    if current_user.role == UserRoleEnum.USER:
        # USER видит только свой отдел
        if not current_user.department_id:
            raise HTTPException(status_code=403, detail="User has no department")
        query = query.filter(Item.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER/ADMIN могут фильтровать по отделу
        if department_id:
            query = query.filter(Item.department_id == department_id)

    return query.all()

# ❌ НЕПРАВИЛЬНО - нет фильтрации по отделу
@router.get("/")
def get_items(db: Session = Depends(get_db)):
    return db.query(Item).all()  # Возвращает ВСЕ данные всех отделов! ❌
```

#### 3. Frontend (React):
```typescript
// ✅ ПРАВИЛЬНО - используется selectedDepartment
import { useDepartment } from '@/contexts/DepartmentContext'

const MyPage = () => {
  const { selectedDepartment } = useDepartment()  // ОБЯЗАТЕЛЬНО!

  const { data } = useQuery({
    queryKey: ['items', selectedDepartment?.id],  // department_id в ключе кэша
    queryFn: () => api.getItems({
      department_id: selectedDepartment?.id  // передаём в API
    })
  })
}

// ❌ НЕПРАВИЛЬНО - не используется selectedDepartment
const MyPage = () => {
  const { data } = useQuery({
    queryKey: ['items'],
    queryFn: () => api.getItems()  // Запрашивает ВСЕ данные! ❌
  })
}
```

#### 4. Создание новых записей:
```python
# ✅ ПРАВИЛЬНО - department_id берётся от пользователя
@router.post("/")
def create_item(
    item: ItemCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    new_item = Item(
        **item.dict(),
        department_id=current_user.department_id  # ОБЯЗАТЕЛЬНО!
    )
    db.add(new_item)
    db.commit()
    return new_item

# ❌ НЕПРАВИЛЬНО - department_id не устанавливается
@router.post("/")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    new_item = Item(**item.dict())  # department_id будет NULL! ❌
    db.add(new_item)
    db.commit()
    return new_item
```

### Текущая реализация:
- ✅ Все основные модели имеют `department_id` (NOT NULL, indexed)
- ✅ Все API endpoints фильтруют по `department_id`
- ✅ Все frontend страницы используют `useDepartment()`
- ✅ DepartmentContext управляет выбранным отделом
- ✅ Role-based access control (USER/MANAGER/ADMIN)

---

## 3. 🎭 Роли пользователей

### Три роли в системе:

#### USER (Пользователь):
- Видит **ТОЛЬКО** данные своего отдела
- Не может переключаться между отделами
- `current_user.department_id` **обязательно** должен быть установлен

#### MANAGER (Менеджер):
- Может видеть данные **всех** отделов
- Может переключаться между отделами
- При выборе конкретного отдела видит только его данные

#### ADMIN (Администратор):
- Полный доступ ко всем данным всех отделов
- Может управлять пользователями, отделами, настройками
- Может переключаться между отделами

### Backend проверка роли:
```python
from app.db.models import UserRoleEnum

if current_user.role == UserRoleEnum.USER:
    # Только свой отдел
    query = query.filter(Model.department_id == current_user.department_id)
elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
    # Может фильтровать или видеть все
    if department_id:
        query = query.filter(Model.department_id == department_id)
```

---

## 4. 📊 Все сущности с department_id

### Полный список сущностей с обязательной привязкой к отделу:

1. ✅ **BudgetCategory** - Категории бюджета
2. ✅ **Contractor** - Контрагенты
3. ✅ **Organization** - Организации
4. ✅ **Expense** - Заявки на расход
5. ✅ **ForecastExpense** - Прогнозные расходы
6. ✅ **BudgetPlan** - Планы бюджета
7. ✅ **Employee** - Сотрудники
8. ✅ **PayrollPlan** - Планы по ФОТ
9. ✅ **PayrollActual** - Фактический ФОТ
10. ✅ **AuditLog** - Журнал аудита (nullable для системных операций)

### Сущности с косвенной привязкой:
- **Attachment** → привязан через `expense_id` → Expense → `department_id`
- **SalaryHistory** → привязан через `employee_id` → Employee → `department_id`
- **DashboardConfig** → привязан через `user_id` → User → `department_id`

---

## 5. 🔄 Принципы работы с данными

### При создании новой функциональности ВСЕГДА:

1. **Модель данных**:
   - Добавить `department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)`
   - Добавить relationship: `department = relationship("Department")`

2. **Pydantic схемы**:
   - В `Create` схеме: `department_id` НЕ должно быть (берётся от пользователя)
   - В `InDB` схеме: `department_id: int` обязательно

3. **API endpoint**:
   - GET: добавить параметр `department_id: Optional[int] = None`
   - POST: брать `department_id` из `current_user.department_id`
   - PUT: проверять, что пользователь может редактировать (свой отдел)
   - DELETE: проверять, что пользователь может удалять (свой отдел)

4. **Frontend API**:
   - Добавить `department_id?: number` в параметры функции
   - Передавать в params если указан

5. **Frontend Page/Component**:
   - Использовать `const { selectedDepartment } = useDepartment()`
   - Добавить `selectedDepartment?.id` в `queryKey`
   - Передать `department_id: selectedDepartment?.id` в API call

6. **Миграция (Alembic)**:
   - При добавлении нового поля `department_id` в существующую таблицу:
     ```python
     # Сначала добавить nullable
     op.add_column('table', sa.Column('department_id', sa.Integer(), nullable=True))

     # Заполнить существующие записи
     op.execute("UPDATE table SET department_id = 1 WHERE department_id IS NULL")

     # Потом сделать NOT NULL
     op.alter_column('table', 'department_id', nullable=False)

     # Добавить FK и индекс
     op.create_foreign_key('fk_table_department', 'table', 'departments', ['department_id'], ['id'])
     op.create_index('ix_table_department_id', 'table', ['department_id'])
     ```

---

## 6. 🚫 Что НИКОГДА нельзя делать

### ❌ Создавать endpoint без авторизации
```python
# НИКОГДА так не делать!
@router.get("/public-data")
def get_public_data(db: Session = Depends(get_db)):
    return db.query(SensitiveData).all()
```

### ❌ Создавать модель без department_id
```python
# НИКОГДА так не делать!
class ImportantEntity(Base):
    __tablename__ = "important_entities"
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    # department_id отсутствует! ❌
```

### ❌ Возвращать все данные без фильтрации
```python
# НИКОГДА так не делать!
@router.get("/all-expenses")
def get_all_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).all()  # Все данные всех отделов! ❌
```

### ❌ Игнорировать selectedDepartment на frontend
```typescript
// НИКОГДА так не делать!
const { data } = useQuery({
  queryKey: ['expenses'],  // Нет department_id! ❌
  queryFn: () => api.getExpenses()  // Нет фильтрации! ❌
})
```

### ❌ Создавать записи без department_id
```python
# НИКОГДА так не делать!
new_expense = Expense(
    amount=1000,
    category_id=5
    # department_id не установлен! ❌
)
```

---

## 7. ✅ Чек-лист для новой функциональности

Перед коммитом новой функциональности проверьте:

### Database & Models:
- [ ] Модель имеет `department_id` (NOT NULL, indexed)
- [ ] Добавлен relationship к Department
- [ ] Миграция создана и применена
- [ ] Данные в таблице проверены (все записи имеют department_id)

### Backend API:
- [ ] Endpoint защищён `Depends(get_current_active_user)`
- [ ] GET endpoints принимают `department_id: Optional[int]`
- [ ] Фильтрация работает для всех ролей (USER/MANAGER/ADMIN)
- [ ] POST создаёт записи с `current_user.department_id`
- [ ] PUT/DELETE проверяют права доступа

### Frontend API:
- [ ] Функция принимает `department_id?: number`
- [ ] Параметр передаётся в API call если указан

### Frontend UI:
- [ ] Компонент использует `useDepartment()`
- [ ] `queryKey` включает `selectedDepartment?.id`
- [ ] API call передаёт `department_id: selectedDepartment?.id`
- [ ] Тестирование: данные меняются при переключении отдела

### Testing:
- [ ] Проверено для роли USER (видит только свой отдел)
- [ ] Проверено для роли MANAGER (может переключать отделы)
- [ ] Проверено для роли ADMIN (полный доступ)
- [ ] Экспорт/импорт учитывает department_id

---

## 8. 📚 Документация и примеры

### Примеры правильной реализации:

Смотрите эти файлы как эталонные примеры:

#### Backend:
- `backend/app/api/v1/expenses.py` - полная реализация с ролями и фильтрацией
- `backend/app/api/v1/budget.py` - фильтрация в сложных запросах
- `backend/app/api/v1/analytics.py` - агрегации с department_id

#### Frontend:
- `frontend/src/pages/ExpensesPage.tsx` - правильное использование useDepartment
- `frontend/src/pages/DashboardPage.tsx` - фильтрация analytics
- `frontend/src/components/budget/BudgetOverviewTable.tsx` - компонент с фильтрацией

#### Models:
- `backend/app/db/models.py` - все модели с department_id

---

## 9. 🔍 Проверка существующего кода

Если вы сомневаетесь, правильно ли реализован код:

### Backend endpoint:
```bash
# Проверить наличие авторизации
grep -n "Depends(get_current_active_user)" backend/app/api/v1/yourfile.py

# Проверить фильтрацию по отделу
grep -n "department_id" backend/app/api/v1/yourfile.py
```

### Frontend page:
```bash
# Проверить использование useDepartment
grep -n "useDepartment" frontend/src/pages/YourPage.tsx

# Проверить передачу department_id
grep -n "selectedDepartment" frontend/src/pages/YourPage.tsx
```

### Database model:
```bash
# Проверить наличие department_id
grep -A 5 "class YourModel" backend/app/db/models.py | grep "department_id"
```

---

## 10. 🚀 Проверка перед деплоем

### Pre-deployment checklist:

1. **Безопасность**:
   - [ ] Все endpoints защищены JWT
   - [ ] Нет публичных endpoints с чувствительными данными
   - [ ] SECRET_KEY изменён в продакшене
   - [ ] CORS настроен правильно

2. **Multi-tenancy**:
   - [ ] Все данные привязаны к отделам
   - [ ] Скрипт проверки: `python scripts/verify_all_department_associations.py`
   - [ ] Нет записей с NULL department_id (кроме audit logs)

3. **Функциональность**:
   - [ ] Переключение отделов работает на всех страницах
   - [ ] USER видит только свой отдел
   - [ ] MANAGER может переключать отделы
   - [ ] Экспорт учитывает выбранный отдел

---

## 📋 Быстрая шпаргалка

### Новый endpoint:
```python
@router.get("/items")
def get_items(
    department_id: Optional[int] = None,  # ✅ Добавить
    current_user: User = Depends(get_current_active_user),  # ✅ Авторизация
    db: Session = Depends(get_db)
):
    query = db.query(Item)

    # ✅ Фильтрация по роли
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(Item.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Item.department_id == department_id)

    return query.all()
```

### Новая страница:
```typescript
import { useDepartment } from '@/contexts/DepartmentContext'

const MyPage = () => {
  const { selectedDepartment } = useDepartment()  // ✅

  const { data } = useQuery({
    queryKey: ['items', selectedDepartment?.id],  // ✅
    queryFn: () => api.getItems({
      department_id: selectedDepartment?.id  // ✅
    })
  })
}
```

### Новая модель:
```python
class MyModel(Base):
    __tablename__ = "my_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)  # ✅

    department = relationship("Department")  # ✅
```

---

## ⚠️ ПОМНИТЕ

**Каждая новая функция, каждый endpoint, каждая страница ДОЛЖНЫ:**
1. ✅ Работать с JWT авторизацией
2. ✅ Быть привязаны к отделу
3. ✅ Соблюдать role-based access control

**Если что-то из этого отсутствует - это БАГ безопасности!**

---

## 📞 Контакты

При сомнениях в реализации:
1. Проверьте этот документ
2. Посмотрите примеры в эталонных файлах
3. Запустите скрипт проверки: `python scripts/verify_all_department_associations.py`

---

**Документ обновлён**: 2025-10-25
**Версия**: 1.0
**Статус**: ✅ ОБЯЗАТЕЛЕН К ИСПОЛНЕНИЮ
