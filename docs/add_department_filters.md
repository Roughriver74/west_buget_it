# Список страниц для добавления фильтра по отделу

## Уже обновлены ✅
- ExpensesPage
- PayrollPlanPage
- PayrollAnalyticsPage
- EmployeesPage
- BalanceAnalyticsPage
- BudgetPage (через BudgetOverviewTable)
- CategoriesPage (через CategoryTable)
- ContractorsPage

## Требуют обновления 🔧
1. OrganizationsPage
2. DashboardPage
3. BudgetPlanPage (годовой план)
4. ForecastPage
5. AnalyticsPage
6. PaymentCalendarPage

## Frontend API файлы для обновления
- [x] budget.ts - добавлен department_id
- [x] analytics.ts - добавлен department_id
- [x] categories.ts - добавлен department_id
- [x] contractors.ts - добавлен department_id
- [ ] organizations.ts - нужно добавить
- [ ] dashboard API calls

## Backend API endpoints для обновления
- [x] /budget/overview - добавлен department_id
- [x] /analytics/by-category - добавлен department_id
- [x] /categories - уже поддерживает
- [ ] /contractors - проверить
- [ ] /organizations - проверить
- [ ] /dashboard - проверить
