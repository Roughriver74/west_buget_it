# KPI Management Page Refactoring Plan

## Проблема
KpiManagementPage.tsx содержит **1523 строки** - это нарушает принцип единственной ответственности и затрудняет поддержку.

## Текущая структура

### Tabs (5 вкладок):
1. **"Сводка" (summary)** - line 951-991
   - Фильтры: год, месяц
   - Таблица с summaryColumns
   - Данные из summaryQuery

2. **"Цели KPI" (goals)** - line 993-1036
   - Фильтры: год, статус
   - Кнопки: Добавить цель, Импорт
   - Таблица с goalsColumns
   - Данные из goalsQuery
   - Модалы: goalFormModal, importModal

3. **"Показатели сотрудников" (employee-kpi)** - line 1038-1063
   - Кнопка: Добавить показатель
   - Таблица с employeeKpiColumns
   - Данные из employeeKpisQuery
   - Модал: employeeKpiFormModal

4. **"Назначения целей" (assignments)** - line 1065-1082
   - Кнопка: Назначить цель
   - Таблица с assignmentColumns
   - Данные из assignmentsQuery
   - Модал: assignmentFormModal

5. **"Календарь бонусов" (calendar)** - line 1084-конец
   - Календарь с bonusesQuery
   - Drawer: employeeDrawer для деталей

### State Variables (~20+):
- goalFilters, summaryFilters
- activeTab
- goalFormModal (open, editingGoal)
- employeeKpiFormModal (open, editingKpi)
- assignmentFormModal (open, editingAssignment)
- importModal (open)
- employeeDrawer (open, selectedEmployeeId)
- Forms: goalForm, employeeKpiForm, assignmentForm

### Queries (~7):
- goalsQuery
- summaryQuery
- employeeKpisQuery
- assignmentsQuery
- employeesQuery
- bonusesQuery
- employeeDetailsQuery

### Mutations (~6):
- createGoalMutation, updateGoalMutation, deleteGoalMutation
- createEmployeeKpiMutation, updateEmployeeKpiMutation, deleteEmployeeKpiMutation
- createAssignmentMutation, updateAssignmentMutation, deleteAssignmentMutation

## План рефакторинга

### Фаза 1: Создание компонентов (6 новых файлов)

#### 1. `frontend/src/components/kpi/KpiSummaryTab.tsx`
**Размер**: ~150 строк

**Экспорт**:
```typescript
interface KpiSummaryTabProps {
  departmentId?: number
}
export const KpiSummaryTab: React.FC<KpiSummaryTabProps>
```

**Содержимое**:
- useState: summaryFilters (year, month)
- useQuery: summaryQuery
- Фильтры: Select для года и месяца
- Таблица: summaryColumns
- Колонки: employee, month, kpi_percentage, total_bonus_calculated, goals, actions

**Внутренние компоненты**:
- summaryColumns - можно экспортировать отдельно

---

#### 2. `frontend/src/components/kpi/KpiGoalsTab.tsx`
**Размер**: ~350 строк

**Экспорт**:
```typescript
interface KpiGoalsTabProps {
  departmentId?: number
}
export const KpiGoalsTab: React.FC<KpiGoalsTabProps>
```

**Содержимое**:
- useState: goalFilters, goalFormModal, importModal, goalForm
- useQuery: goalsQuery
- useMutation: create/update/deleteGoalMutation
- Фильтры: год, статус
- Кнопки: Добавить цель, Импорт
- Таблица: goalsColumns
- Модалы: GoalFormModal (form), ImportKPIModal

**Колонки**: name, category, metric_name, target_value, weight, year, is_annual, status, actions

**Sub-components** (можно экспортировать отдельно):
- GoalFormModal
- goalsColumns

---

#### 3. `frontend/src/components/kpi/EmployeeKpiTab.tsx`
**Размер**: ~250 строк

**Экспорт**:
```typescript
interface EmployeeKpiTabProps {
  departmentId?: number
}
export const EmployeeKpiTab: React.FC<EmployeeKpiTabProps>
```

**Содержимое**:
- useState: employeeKpiFormModal, employeeKpiForm
- useQuery: employeeKpisQuery, employeesQuery
- useMutation: create/update/deleteEmployeeKpiMutation
- Кнопка: Добавить показатель
- Таблица: employeeKpiColumns
- Модал: EmployeeKpiFormModal

**Колонки**: employee, goal, month, achievement, status, actions

---

#### 4. `frontend/src/components/kpi/KpiAssignmentsTab.tsx`
**Размер**: ~250 строк

**Экспорт**:
```typescript
interface KpiAssignmentsTabProps {
  departmentId?: number
}
export const KpiAssignmentsTab: React.FC<KpiAssignmentsTabProps>
```

**Содержимое**:
- useState: assignmentFormModal, assignmentForm
- useQuery: assignmentsQuery, goalsQuery, employeesQuery
- useMutation: create/update/deleteAssignmentMutation
- Кнопка: Назначить цель
- Таблица: assignmentColumns
- Модал: AssignmentFormModal

**Колонки**: employee, goal, assigned_date, target_achievement, actual_achievement, status, actions

---

#### 5. `frontend/src/components/kpi/KpiCalendar.tsx`
**Размер**: ~200 строк

**Экспорт**:
```typescript
interface KpiCalendarProps {
  departmentId?: number
}
export const KpiCalendar: React.FC<KpiCalendarProps>
```

**Содержимое**:
- useState: selectedDate
- useQuery: bonusesQuery
- Calendar с dateCellRender
- Отображение бонусов по датам

---

#### 6. `frontend/src/components/kpi/EmployeeKpiDrawer.tsx`
**Размер**: ~150 строк

**Экспорт**:
```typescript
interface EmployeeKpiDrawerProps {
  employeeId: number | null
  open: boolean
  onClose: () => void
  departmentId?: number
}
export const EmployeeKpiDrawer: React.FC<EmployeeKpiDrawerProps>
```

**Содержимое**:
- useQuery: employeeDetailsQuery (conditional based on employeeId)
- Drawer с деталями сотрудника
- Descriptions: ФИО, должность, отдел, статус
- Таблица KPI за период
- Общие показатели

---

### Фаза 2: Обновление главного файла

#### `frontend/src/pages/KpiManagementPage.tsx`
**Новый размер**: ~150 строк (вместо 1523!)

**Содержимое**:
```typescript
import { useState } from 'react'
import { Tabs, Typography } from 'antd'
import { useDepartment } from '@/contexts/DepartmentContext'
import { useAuth } from '@/contexts/AuthContext'
import { KpiSummaryTab } from '@/components/kpi/KpiSummaryTab'
import { KpiGoalsTab } from '@/components/kpi/KpiGoalsTab'
import { EmployeeKpiTab } from '@/components/kpi/EmployeeKpiTab'
import { KpiAssignmentsTab } from '@/components/kpi/KpiAssignmentsTab'
import { KpiCalendar } from '@/components/kpi/KpiCalendar'

const { Title } = Typography

const KPIManagementPage = () => {
  const { selectedDepartment } = useDepartment()
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('summary')

  const departmentId = selectedDepartment?.id ?? user?.department_id ?? undefined

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>Управление KPI сотрудников</Title>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <Tabs.TabPane tab="Сводка" key="summary">
          <KpiSummaryTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Цели KPI" key="goals">
          <KpiGoalsTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Показатели сотрудников" key="employee-kpi">
          <EmployeeKpiTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Назначения целей" key="assignments">
          <KpiAssignmentsTab departmentId={departmentId} />
        </Tabs.TabPane>

        <Tabs.TabPane tab="Календарь бонусов" key="calendar">
          <KpiCalendar departmentId={departmentId} />
        </Tabs.TabPane>
      </Tabs>
    </div>
  )
}

export default KPIManagementPage
```

---

## Преимущества рефакторинга

### ✅ Читаемость
- Каждый файл < 400 строк (вместо 1523)
- Четкая структура и ответственность
- Легко найти нужный код

### ✅ Поддерживаемость
- Изолированные компоненты
- Локализованные изменения
- Простое тестирование

### ✅ Переиспользование
- Компоненты можно использовать отдельно
- Легко добавить новые вкладки
- Модальные формы изолированы

### ✅ Performance
- React может лучше мемоизировать маленькие компоненты
- Ленивая загрузка вкладок (future improvement)
- Меньше ре-рендеров

---

## Порядок выполнения

1. ✅ **Создать документацию** (этот файл) - DONE
2. ⬜ Создать `KpiSummaryTab.tsx` (самый простой)
3. ⬜ Создать `KpiGoalsTab.tsx` (самый сложный, есть модалы)
4. ⬜ Создать `EmployeeKpiTab.tsx`
5. ⬜ Создать `KpiAssignmentsTab.tsx`
6. ⬜ Создать `KpiCalendar.tsx`
7. ⬜ Создать `EmployeeKpiDrawer.tsx`
8. ⬜ Обновить главный `KpiManagementPage.tsx`
9. ⬜ Тестирование каждой вкладки
10. ⬜ Удалить старый код (сохранить backup)

---

## Оценка времени
- Создание компонентов: ~2-3 часа
- Тестирование: ~1 час
- Отладка: ~30 минут

**Итого**: ~3.5-4.5 часа работы

---

## Риски и митигация

### ⚠️ Риск: Потеря функциональности
**Митигация**:
- Пошаговый подход (по одному компоненту)
- Тестирование каждого компонента
- Git commit после каждого шага

### ⚠️ Риск: Дублирование логики
**Митигация**:
- Общие типы и утилиты вынести в `/api/kpi.ts`
- Переиспользовать колонки где возможно

### ⚠️ Риск: Сложность синхронизации state
**Митигация**:
- Каждый компонент управляет своим состоянием
- Использовать React Query для кэширования
- departmentId передается через props

---

## Примечания

- Все компоненты должны поддерживать multi-tenancy через `departmentId`
- Использовать существующие API из `/api/kpi.ts`
- Сохранить существующую UX (фильтры, кнопки, модалы)
- Добавить комментарии для сложной логики
