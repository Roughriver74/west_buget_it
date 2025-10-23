# 📋 План разработки CRUD функционала

## 🎯 Цель
Реализовать полноценный CRUD (Create, Read, Update, Delete) для всех сущностей с удобным UI интерфейсом.

---

## ✅ Что уже сделано

### Backend (FastAPI)
- ✅ Все модели данных (SQLAlchemy)
- ✅ Все API endpoints (CRUD)
- ✅ Pydantic схемы валидации
- ✅ База данных PostgreSQL
- ✅ Миграции Alembic
- ✅ Импорт данных из Excel

### Frontend (React)
- ✅ Структура проекта
- ✅ API клиенты (Axios)
- ✅ TypeScript типы
- ✅ Базовый Layout
- ✅ Роутинг (React Router)
- ✅ State management (React Query)
- ✅ Страница просмотра заявок (read-only)
- ✅ Дашборд с аналитикой

---

## 🚧 Что нужно доработать

### 1. Заявки на расходы (Expenses) - ПРИОРИТЕТ 1

#### ✅ Уже работает:
- Просмотр списка заявок
- Фильтрация по статусу, категории, дате
- Поиск
- Пагинация

#### 🔧 Нужно добавить:

**1.1. Модальное окно создания заявки**
```tsx
// frontend/src/components/expenses/ExpenseCreateModal.tsx
- Форма с полями:
  - Номер заявки (автогенерация или ручной ввод)
  - Категория (Select с группировкой OPEX/CAPEX)
  - Контрагент (Select с поиском)
  - Организация (Select)
  - Сумма (Number input с валидацией)
  - Дата заявки (DatePicker)
  - Дата платежа (DatePicker, опционально)
  - Статус (Select)
  - Комментарий (TextArea)
  - Заявитель (Input)

- Валидация:
  - Обязательные поля: номер, категория, организация, сумма, дата заявки
  - Проверка уникальности номера
  - Сумма > 0

- UI/UX:
  - Ant Design Modal + Form
  - Автокомплит для контрагента
  - Подсказки и плейсхолдеры
  - Сообщения об успехе/ошибке
```

**1.2. Модальное окно редактирования заявки**
```tsx
// frontend/src/components/expenses/ExpenseEditModal.tsx
- Те же поля что и при создании
- Предзаполнение текущими значениями
- Возможность изменить все поля кроме ID
- Подтверждение при важных изменениях (статус, сумма)
```

**1.3. Изменение статуса заявки**
```tsx
// frontend/src/components/expenses/ExpenseStatusChanger.tsx
- Быстрое изменение статуса без открытия формы
- Dropdown в строке таблицы
- Workflow: Черновик → К оплате → Оплачена
- Валидация переходов между статусами
- Автозаполнение даты оплаты при статусе "Оплачена"
```

**1.4. Удаление заявки**
```tsx
// Кнопка удаления с подтверждением
- Modal.confirm с предупреждением
- Проверка прав (в будущем)
- Каскадное удаление связанных данных
- Сообщение об успехе
```

**1.5. Массовые операции**
```tsx
// frontend/src/components/expenses/ExpenseBulkActions.tsx
- Чекбоксы для выбора нескольких заявок
- Массовое изменение статуса
- Массовое удаление
- Экспорт выбранных в Excel
```

**Файлы для создания:**
```
frontend/src/components/expenses/
├── ExpenseCreateModal.tsx       [NEW]
├── ExpenseEditModal.tsx         [NEW]
├── ExpenseStatusChanger.tsx     [NEW]
├── ExpenseDeleteButton.tsx      [NEW]
├── ExpenseBulkActions.tsx       [NEW]
├── ExpenseForm.tsx              [NEW] (общая форма для create/edit)
└── ExpenseTable.tsx             [MODIFY] (добавить кнопки действий)
```

---

### 2. Категории расходов (Categories) - ПРИОРИТЕТ 2

#### 🔧 Что нужно:

**2.1. Страница управления категориями**
```tsx
// frontend/src/pages/CategoriesPage.tsx
- Таблица всех категорий
- Колонки: ID, Название, Тип (OPEX/CAPEX), Описание, Активность
- Фильтр по типу и активности
- Поиск по названию
```

**2.2. CRUD для категорий**
```tsx
// frontend/src/components/references/categories/
├── CategoryCreateModal.tsx      [NEW]
├── CategoryEditModal.tsx        [NEW]
├── CategoryDeleteButton.tsx     [NEW]
└── CategoryTable.tsx            [NEW]

Форма категории:
- Название (обязательно, уникальное)
- Тип: OPEX или CAPEX (Radio buttons)
- Описание (опционально)
- Активность (Checkbox)
```

**2.3. Особенности**
- Проверка перед удалением (есть ли заявки с этой категорией)
- Soft delete (is_active = false) вместо удаления
- Подсчет количества заявок по каждой категории

---

### 3. Контрагенты (Contractors) - ПРИОРИТЕТ 2

**3.1. Страница управления контрагентами**
```tsx
// frontend/src/pages/ContractorsPage.tsx
- Таблица контрагентов
- Колонки: ID, Название, Короткое название, ИНН, Контакты, Активность
- Поиск по названию, ИНН
- Фильтр по активности
```

**3.2. CRUD для контрагентов**
```tsx
// frontend/src/components/references/contractors/
├── ContractorCreateModal.tsx    [NEW]
├── ContractorEditModal.tsx      [NEW]
├── ContractorDeleteButton.tsx   [NEW]
└── ContractorTable.tsx          [NEW]

Форма контрагента:
- Название (обязательно)
- Короткое название
- ИНН (валидация формата)
- Контактная информация (телефон, email, адрес)
- Активность
```

**3.3. Особенности**
- Валидация ИНН (10 или 12 цифр)
- Проверка уникальности ИНН
- Автозаполнение данных по ИНН (API Dadata в будущем)
- Подсчет суммы заявок по контрагенту

---

### 4. Организации (Organizations) - ПРИОРИТЕТ 3

**4.1. CRUD для организаций**
```tsx
// frontend/src/components/references/organizations/
├── OrganizationCreateModal.tsx  [NEW]
├── OrganizationEditModal.tsx    [NEW]
├── OrganizationDeleteButton.tsx [NEW]
└── OrganizationTable.tsx        [NEW]

Форма организации:
- Название (обязательно, уникальное)
- Полное юридическое название
- Активность
```

**4.2. Особенности**
- Проверка перед удалением (есть ли заявки)
- Soft delete

---

### 5. Планирование бюджета (Budget Plans) - ПРИОРИТЕТ 3

**5.1. Страница планирования бюджета**
```tsx
// frontend/src/pages/BudgetPlanPage.tsx
- Таблица помесячного плана
- Строки: месяцы (Январь-Декабрь)
- Колонки: План общий, CAPEX, OPEX, Факт, Остаток, % исполнения
- Фильтр по году
- Inline редактирование сумм
```

**5.2. CRUD для планов**
```tsx
// frontend/src/components/budget/
├── BudgetPlanTable.tsx          [NEW]
├── BudgetPlanEditCell.tsx       [NEW]
├── BudgetYearSelector.tsx       [NEW]
└── BudgetCopyFromYear.tsx       [NEW] (копирование из предыдущего года)

Функционал:
- Создание плана на год
- Редактирование сумм по месяцам
- Копирование плана из другого года с коэффициентом
- Автоматический расчет CAPEX/OPEX по категориям
```

---

### 6. Страница справочников - ПРИОРИТЕТ 2

**6.1. Общая страница справочников**
```tsx
// frontend/src/pages/ReferencesPage.tsx
- Tabs для переключения между справочниками:
  - Категории расходов
  - Контрагенты
  - Организации

- Каждый таб содержит соответствующую таблицу с CRUD
```

---

## 📅 План реализации (по приоритетам)

### Этап 1: Заявки (1-2 дня)
1. ✅ Создать ExpenseForm.tsx - общая форма
2. ✅ Создать ExpenseCreateModal.tsx
3. ✅ Создать ExpenseEditModal.tsx
4. ✅ Добавить кнопки в ExpenseTable.tsx
5. ✅ Создать ExpenseStatusChanger.tsx
6. ✅ Создать ExpenseDeleteButton.tsx
7. ✅ Тестирование CRUD заявок

### Этап 2: Справочники (1-2 дня)
1. ✅ Реализовать CRUD категорий
2. ✅ Реализовать CRUD контрагентов
3. ✅ Реализовать CRUD организаций
4. ✅ Создать страницу References с табами
5. ✅ Тестирование справочников

### Этап 3: Планирование бюджета (1 день)
1. ✅ Создать BudgetPlanTable
2. ✅ Реализовать inline редактирование
3. ✅ Добавить копирование из другого года
4. ✅ Интеграция с аналитикой

### Этап 4: Улучшения UX (1 день)
1. ✅ Добавить индикаторы загрузки
2. ✅ Улучшить сообщения об ошибках
3. ✅ Добавить подтверждения действий
4. ✅ Оптимизировать производительность

---

## 🔧 Технические детали

### Используемые библиотеки

**Формы:**
```tsx
import { Form, Input, Select, DatePicker, InputNumber } from 'antd'
import { useForm } from 'antd/es/form/Form'
```

**Модальные окна:**
```tsx
import { Modal } from 'antd'
```

**Таблицы:**
```tsx
import { Table, Button, Space, Tag, Popconfirm } from 'antd'
```

**React Query:**
```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
```

### Паттерн для CRUD операций

```tsx
// Пример Create
const CreateModal = ({ open, onClose }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data) => api.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries(['items'])
      message.success('Создано успешно!')
      onClose()
      form.resetFields()
    },
    onError: (error) => {
      message.error(`Ошибка: ${error.message}`)
    }
  })

  const handleSubmit = (values) => {
    createMutation.mutate(values)
  }

  return (
    <Modal
      title="Создать"
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={createMutation.isPending}
    >
      <Form form={form} onFinish={handleSubmit} layout="vertical">
        {/* Fields */}
      </Form>
    </Modal>
  )
}
```

---

## 📊 Метрики успеха

### После завершения должно быть:

**Функционал:**
- ✅ Создание, редактирование, удаление заявок через UI
- ✅ Управление всеми справочниками
- ✅ Планирование бюджета на год
- ✅ Все операции работают без ошибок

**UX:**
- ✅ Формы понятные и интуитивные
- ✅ Валидация работает корректно
- ✅ Сообщения об ошибках информативны
- ✅ Индикаторы загрузки на всех операциях

**Производительность:**
- ✅ Операции выполняются < 1 сек
- ✅ Нет лагов при работе с таблицами
- ✅ Кэширование работает

---

## 🎯 Quick Start для разработки

### 1. Создать компонент формы

```bash
# Создать файл
touch frontend/src/components/expenses/ExpenseCreateModal.tsx

# Использовать шаблон:
```

```tsx
import React from 'react'
import { Modal, Form, Input, Select, InputNumber, DatePicker, message } from 'antd'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { expensesApi } from '@/api'
import type { ExpenseCreate } from '@/types'

interface Props {
  open: boolean
  onClose: () => void
}

const ExpenseCreateModal: React.FC<Props> = ({ open, onClose }) => {
  const [form] = Form.useForm()
  const queryClient = useQueryClient()

  const createMutation = useMutation({
    mutationFn: (data: ExpenseCreate) => expensesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['expenses'] })
      message.success('Заявка создана!')
      onClose()
      form.resetFields()
    },
    onError: (error: any) => {
      message.error(`Ошибка: ${error.response?.data?.detail || error.message}`)
    },
  })

  return (
    <Modal
      title="Создать заявку"
      open={open}
      onCancel={onClose}
      onOk={() => form.submit()}
      confirmLoading={createMutation.isPending}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={(values) => createMutation.mutate(values)}
      >
        <Form.Item
          name="number"
          label="Номер заявки"
          rules={[{ required: true, message: 'Введите номер' }]}
        >
          <Input placeholder="0В0В-001234" />
        </Form.Item>

        {/* Добавить остальные поля */}
      </Form>
    </Modal>
  )
}

export default ExpenseCreateModal
```

### 2. Интегрировать в страницу

```tsx
// В ExpensesPage.tsx
const [createModalOpen, setCreateModalOpen] = useState(false)

<Button
  type="primary"
  icon={<PlusOutlined />}
  onClick={() => setCreateModalOpen(true)}
>
  Создать заявку
</Button>

<ExpenseCreateModal
  open={createModalOpen}
  onClose={() => setCreateModalOpen(false)}
/>
```

---

## 📝 Чеклист разработки

### Для каждой сущности:

- [ ] Создать компонент формы
- [ ] Добавить валидацию полей
- [ ] Создать modal для Create
- [ ] Создать modal для Edit
- [ ] Добавить кнопку Delete с подтверждением
- [ ] Интегрировать с React Query
- [ ] Добавить обработку ошибок
- [ ] Добавить success messages
- [ ] Протестировать все операции
- [ ] Проверить на edge cases

---

**Начать с**: Заявки (Expenses) → Самый важный функционал!

После реализации CRUD для заявок, остальные сущности делаются по аналогии за несколько часов каждая.
