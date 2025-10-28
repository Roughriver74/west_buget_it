# 🗺️ Roadmap - IT Budget Manager

## ✅ Реализовано (v0.1.0)

### Backend
- ✅ FastAPI с полноценным REST API
- ✅ SQLAlchemy модели для всех сущностей
- ✅ Alembic миграции
- ✅ CRUD операции для всех справочников
- ✅ Аналитические эндпоинты
- ✅ Фильтрация и пагинация
- ✅ Импорт данных из Excel

### Frontend
- ✅ React + TypeScript + Vite
- ✅ Роутинг с React Router
- ✅ State management с React Query
- ✅ Ant Design UI компоненты
- ✅ Дашборд с метриками и графиками
- ✅ Страница заявок с фильтрами
- ✅ Базовая структура для всех страниц

### DevOps
- ✅ Docker контейнеризация
- ✅ Docker Compose оркестрация
- ✅ Переменные окружения
- ✅ Документация

---

## 🚧 В разработке (v0.2.0)

### Формы и модальные окна
- [x] Модальное окно создания заявки
- [x] Форма редактирования заявки
- [x] Валидация форм с Ant Design Form
- [x] Автокомплит для контрагентов
- [x] Выбор категории с группировкой OPEX/CAPEX
- [x] Загрузка списка заявок из FTP (Excel файл) с сопоставлением и предотвращением дублей
- [x] Пометка импортированных из FTP заявок для проверки категорий
- [x] Загрузка файлов (счета, договора)

### Справочники
- [x] CRUD интерфейс для категорий
- [x] CRUD интерфейс для контрагентов
- [x] CRUD интерфейс для организаций
- [x] Массовое редактирование
- [x] Импорт/экспорт справочников

### Бюджет
- [x] Страница планирования бюджета
- [x] Помесячное редактирование плана
- [x] Копирование плана из предыдущего года
- [x] Визуализация исполнения по месяцам
- [x] Алерты при превышении бюджета

### Аналитика
- [x] Расширенные графики и диаграммы
- [x] Экспорт отчетов в Excel
- [x] Настраиваемые дашборды
- [x] Сравнение периодов
- [x] Прогнозирование расходов на основе регулярных платежей и средних значений
- [x] Календарь оплат с отображением прогнозных расходов
- [x] Редактируемая таблица прогнозов с автогенерацией
- [x] Единая шина для baseline расчётов (кеширование, защита от дублирующих запросов)
- [x] Типизация фронтенд-клиентов под новую схему BudgetPlanning API

---

## 🚧 В разработке (v0.3.0)
### Пользователи и права
- [x] Аутентификация (JWT)
- [x] Регистрация и логин
- [x] Роли: Администратор, Бухгалтер, Заявитель
- [x] Права доступа к функциям
- [x] Защищенные маршруты (ProtectedRoute)
- [x] AuthContext для управления сессией
- [x] Скрипт создания администратора
- [x] Компоненты Login и Register
- [x] Исправление ошибки с выходом при обновлении страницы (token persistence)
- [x] Управление пользователями (UI для админа)
- [x] История изменений (audit log) - полная реализация
- [ ] Email верификация (отложено на v0.4.0)
- [ ] Восстановление пароля (отложено на v0.4.0)

### Multi-tenancy и разделение по отделам
- [x] Модель Department (отделы) с базовой структурой
- [x] Поле department_id во всех основных таблицах (expenses, categories, contractors, organizations, budget_plans, users)
- [x] Миграции БД для multi-tenancy архитектуры
- [x] API endpoints для управления отделами (CRUD)
- [x] Схемы Department (Pydantic)
- [x] UI для управления отделами (создание, редактирование, список)
- [x] Dropdown выбора отдела в шапке приложения (переключение контекста)
- [x] Фильтрация всех данных по выбранному отделу (department_id)
- [x] Автоматическая установка department_id при создании новых записей
- [x] Ограничение доступа пользователей к данным своего отдела (RLS - Row Level Security)
- [x] Настройки видимости отделов для разных ролей (Админ видит все, остальные - только свой отдел)
- [x] Статистика по отделам (количество заявок, бюджет, расходы)
- [x] Отчеты с группировкой по отделам - API endpoints готовы

---

## 🚧 В разработке (v0.4.0)

### HR и Зарплатный фонд (ФОТ) - Базовый функционал
- [x] Модуль управления сотрудниками (Employee)
  - [x] Модель Employee: ФИО, должность, оклад, department_id
  - [x] Статусы: активный, в отпуске, уволен
  - [x] История изменений оклада (SalaryHistory)
  - [x] Связь с Department (multi-tenancy)
  - [x] API endpoints для CRUD операций сотрудников
  - [x] UI для управления сотрудниками с фильтрами и поиском
  - [x] Статистика сотрудников (количество, средний оклад, общий ФОТ)
  - [x] Детальная страница сотрудника с планами, выплатами и историей зарплаты
- [x] Планирование ФОТ (Payroll Planning)
  - [x] Модель PayrollPlan: employee_id, месяц, оклад, премия
  - [x] Помесячное планирование зарплаты (оклад + премия)
  - [x] Автоматический расчет итогов по месяцам и году
  - [x] API endpoints для планирования ФОТ
  - [x] UI для планирования ФОТ с таблицей план/факт по месяцам
  - [x] Импорт из Excel (POST /payroll/plans/import с валидацией и обработкой ошибок)
  - [x] Экспорт плана ФОТ в Excel (сотрудники, планы, факт выплат)
- [x] Факт выплат ФОТ
  - [x] Модель PayrollActual: фактические выплаты по месяцам
  - [x] Сравнение план/факт по ФОТ
  - [x] Интеграция с Expense (связь выплат зарплаты с заявками через expense_id)
  - [x] API endpoints для учета фактических выплат
- [x] Базовая аналитика ФОТ
  - [x] Страница план/факт по месяцам с отклонениями
  - [x] Годовая статистика ФОТ
  - [x] Расчет отклонений и процентов выполнения
  - [x] Дашборд ФОТ: график динамики по месяцам (area chart план vs факт)
  - [x] Средняя зарплата, медиана, процентили (25%, 75%, 90%)
  - [x] Анализ структуры ФОТ (оклад vs премии vs прочие выплаты - bar chart + pie chart)
  - [x] Прогноз ФОТ на следующие месяцы (на основе moving average с трендом, 6 месяцев вперёд)

---

## 🚧 В разработке (v0.5.0 - Code Review Improvements)

### 🔥 КРИТИЧЕСКИЙ ПРИОРИТЕТ - Безопасность
- [x] **Изменить SECRET_KEY** - создать `.env` с сильным ключом (минимум 32 символа)
- [x] **Добавить валидацию SECRET_KEY** - проверка при старте приложения
- [x] **Базовые тесты аутентификации** - pytest для auth, RBAC, row-level security
- [x] **Security headers** - HSTS, CSP, X-Frame-Options, X-Content-Type-Options
- [x] **HTTPS enforcement** - редирект на HTTPS в production

### ⚡ ВЫСОКИЙ ПРИОРИТЕТ - Производительность
- [x] **Redis для rate limiting** - распределенный rate limiter вместо in-memory
- [x] **Оптимизация N+1 запросов** - добавить joinedload для relationships
- [x] **Пагинация analytics endpoints** - limit/offset для больших выборок
- [x] **Redis кеширование** - кеш для справочников и частых запросов (5 мин TTL)
- [x] **Database connection pool tuning** - оптимизация настроек пула

### 🔧 СРЕДНИЙ ПРИОРИТЕТ - Качество кода
- [x] **Убрать console.log** - создать logger wrapper для production
- [x] **Рефакторинг department filter** - создать reusable dependency
- [x] **Заменить datetime.utcnow()** - использовать timezone-aware datetime
- [x] **Валидация environment variables** - Pydantic validators для config
- [x] **Улучшить обработку ошибок frontend** - консистентные error states
- [x] **Pre-commit hooks** - black, flake8, mypy, isort автоматически
- [x] **TypeScript типы из OpenAPI** - генерация из schema
- [x] **Единые интерфейсы для аналітики** - выровнять типы `DashboardData`, `Forecast` и Payroll с backend

### 📊 НИЗКИЙ ПРИОРИТЕТ - DevOps & Мониторинг
- [x] **Sentry интеграция** - error tracking для production
- [x] **Prometheus metrics** - экспорт метрик для мониторинга
- [x] **Docker** - Создание образов фронтенд и бэкенд, полный перевод приложения на Docker.
- [x] **CI/CD pipeline** - GitHub Actions для тестов и деплоя
- [ ] **Logging aggregation** - ELK stack или CloudWatch

### 📝 Технический долг
- [x] **Линтеры Python** - black, flake8, mypy, pylint в requirements-dev.txt ✅ (2025-10-28)
  - pyproject.toml с конфигурацией всех инструментов
  - .flake8 для flake8
  - .pylintrc для pylint
  - .pre-commit-config.yaml для автоматических проверок
  - Makefile с командами для lint, format, test
- [x] **Unit тесты** - coverage 75%+ для критичной логики ✅ (2025-10-28)
  - test_kpi_calculations.py - 30+ тестов для KPI расчётов
  - test_payroll_calculations.py - 25+ тестов для payroll расчётов
  - test_auth.py - 50+ тестов для аутентификации (уже было)
  - Полное покрытие критичной бизнес-логики
- [ ] **E2E тесты** - Playwright для основных user flows
- [ ] **API versioning strategy** - подготовка к v2 API
- [ ] **Документация API** - актуализация OpenAPI schema
- [ ] **Синхронизация документации и схем** - автоматическая выгрузка ER-диаграмм и схем JSON

---

## 📋 Запланировано (v0.6.0+)

### Расширенная аналитика ФОТ
- [ ] Графики изменения ФОТ по месяцам
- [ ] Распределение зарплат (гистограммы)
- [ ] Средняя зарплата, медиана, процентили
- [ ] Прогноз ФОТ на следующие месяцы на основе трендов
- [ ] Анализ структуры ФОТ (оклад vs премии vs прочие выплаты)
- [ ] Учет налогов НДФЛ, и прочих выплат

### Система KPI сотрудников
- [x] Модуль KPI (Key Performance Indicators) - Backend
  - [x] Модель EmployeeKPI: employee_id, период, базовая_премия, КПИ_%
  - [x] Варианты премий: результативный, фиксированный, смешанный (BonusTypeEnum)
  - [x] Связь с Employee и Department через department_id
  - [x] Три типа бонусов с раздельными расчетами (monthly, quarterly, annual)
- [x] Управление целями и метриками - Backend
  - [x] Модель KPIGoal: название, описание, вес, целевое значение, метрика
  - [x] Модель EmployeeKPIGoal: связь целей с сотрудниками (many-to-many)
  - [x] Треки выполнения целей по месяцам (target_value, actual_value, achievement_percentage)
  - [x] Поддержка годовых и месячных целей
- [x] Расчет премий по КПИ - Backend
  - [x] Формула PERFORMANCE_BASED: премия = базовая_премия * (КПИ% / 100)
  - [x] Формула FIXED: премия = базовая_премия (без изменений)
  - [x] Формула MIXED: фиксированная часть + результативная часть
  - [x] Помесячный расчет премий (monthly_bonus_calculated, etc.)
  - [x] API endpoints для CRUD операций
- [x] API endpoints KPI
  - [x] /api/v1/kpi/goals - управление целями
  - [x] /api/v1/kpi/employee-kpis - управление КПИ сотрудников
  - [x] /api/v1/kpi/employee-kpi-goals - назначение целей сотрудникам
  - [x] /api/v1/kpi/analytics/employee-summary - аналитика по сотрудникам
  - [x] Role-based access control (ADMIN/MANAGER/USER)
- [x] Интерфейс управления KPI - Frontend
  - [x] Страница "КПИ сотрудников" с таблицей
  - [x] Формы создания/редактирования целей (KPIGoal)
  - [x] Редактирование КПИ% для каждого сотрудника
  - [x] Назначение целей сотрудникам
  - [x] Календарь выплаты премий (когда отправлять)
  - [x] Детальный просмотр KPI по сотруднику
  - [x] Импорт данных KPI из Excel (KPI_Manager_2025.xlsx)
- [x] Аналитика KPI - Frontend
  - [x] Дашборд производительности команды
  - [x] Рейтинг сотрудников по KPI
  - [x] Динамика изменения KPI по месяцам
  - [x] Анализ выполнения целей
  - [x] Распределение премий по отделам
  - [ ] Корреляция КПИ и результатов бизнеса (отложено - требуется дополнительный анализ метрик бизнеса)

### Интеграция ФОТ + KPI + Бюджет
- [x] Автоматическое создание заявок на ЗП
  - [x] Генерация Expense для зарплатных выплат
  - [x] Категория "Заработная плата" (OPEX)
  - [x] Автозаполнение на основе PayrollPlan + EmployeeKPI
- [x] Включение ФОТ в общий бюджет
  - [x] Учет ФОТ в BudgetPlan как отдельная категория
  - [x] План/факт по ФОТ в общей аналитике
  - [x] Прогноз расходов на ФОТ в календаре оплат
- [x] Отчеты и дашборды ✅ (2025-10-28)
  - [x] Сводный отчет: бюджет + ФОТ + KPI (Comprehensive Report)
    - Backend API endpoint `/api/v1/reports/comprehensive`
    - Интегрированная аналитика по всем модулям
    - Суммарная статистика (Budget Summary, Payroll Summary, KPI Summary)
    - Cost Efficiency Metrics (ROI, ratios, variances)
    - Top 10 performers по KPI
    - Top 10 категорий расходов
    - Помесячная разбивка (budget + payroll + kpi)
    - Department comparison (для ADMIN/MANAGER)
    - Role-based access control
  - [x] Анализ эффективности затрат на персонал
    - Cost per employee
    - Payroll to budget ratio
    - Bonus to salary ratio
    - Cost per KPI point
  - [x] ROI на ФОТ (результаты vs затраты)
    - ROI on performance bonuses
    - KPI correlation with costs
    - Efficiency metrics по отделам

### UX улучшения
- [ ] Темная тема
- [ ] Адаптивная мобильная версия
- [ ] PWA (Progressive Web App)
- [ ] Оффлайн режим
- [ ] Горячие клавиши

### Производительность
- [ ] Кэширование Redis
- [ ] Оптимизация SQL запросов
- [ ] Индексы в PostgreSQL
- [ ] Pagination курсорами
- [ ] Lazy loading компонентов

### Расширенные фильтры
- [ ] Сохраненные фильтры
- [ ] Пресеты фильтров
- [ ] Полнотекстовый поиск
- [ ] Фильтры по диапазонам сумм
- [ ] Множественный выбор в фильтрах

### Модуль планирования бюджета

#### v0.3.0: Foundations (база для планирования)

**Backend**
- [ ] Модели и миграции планирования
  - [ ] `budget_versions` (year, version, scenario, status, totals, metadata JSON)
  - [ ] `budget_plan_details` (version_id, month, category, type OPEX/CAPEX, amount, calculation_method, params JSON)
  - [ ] `budget_approval_log` (iteration, reviewer, decision, comment, timestamp)
  - [ ] Индексы и внешние ключи по year, version_id, category, month
- [ ] API v1 Budget Planning
  - [ ] `POST /budget/versions` (создание версии, копирование из предыдущего года)
  - [ ] `GET /budget/versions?year=<target_year>` (фильтры по статусу и сценарию)
  - [ ] `GET /budget/versions/{id}` (детали + агрегаты CAPEX/OPEX)
  - [ ] `PUT /budget/versions/{id}` (метаданные версии)
  - [ ] `DELETE /budget/versions/{id}` (архивирование / soft delete)
  - [ ] `POST /budget/versions/{id}/details/bulk` (массовое заполнение по статьям/месяцам)
  - [ ] `GET /budget/versions/{id}/summary` (итоги + сравнение с фактом предыдущего года)
- [ ] Автозаполнение по историческим данным
  - [ ] Копирование структуры статей и среднемесячной базы предыдущего года
  - [ ] Глобальный коэффициент роста/снижения (%)
  - [ ] Равномерное распределение по месяцам по умолчанию
- [ ] Security и RLS
  - [ ] Привязка `department_id` ко всем сущностям планирования
  - [ ] Проверки доступа по ролям (ADMIN/ACCOUNTANT/REQUESTER)

**Frontend**
- [ ] Страница "Планирование бюджета"
  - [ ] Список версий (название, сценарий, статус, сумма, delta к предыдущему году)
  - [ ] Действия: создать, скопировать, архивировать, открыть
- [ ] Редактор версии (MVP)
  - [ ] Таблица категорий с годовой суммой и помесячной раскладкой (inline-редактирование)
  - [ ] Итоги CAPEX/OPEX/Total + сравнение с фактом предыдущего года
  - [ ] Кнопка "Автозаполнить по прошлому году" с глобальным процентом
  - [x] Горизонтальный скролл с плавающими стрелками для больших таблиц
  - [x] Переключатель месяцев с подсветкой активного столбца
  - [x] Фиксированная шапка месяцев при вертикальном скролле

**Аналитика и отчеты**
- [ ] Виджет "План целевого года vs Факт предыдущего года" (stacked bar по категориям)
- [ ] Экспорт версии плана в Excel (годовой и помесячный формат)

#### v0.4.0: Workflow и версионирование

**Backend**
- [ ] Версионирование и история изменений (нумерация 1.0, 1.1, 2.0 + change log)
- [ ] Workflow статусы
  - [ ] `POST /budget/versions/{id}/submit` → статус `in_review`
  - [ ] `POST /budget/versions/{id}/approve` → статус `approved`
  - [ ] `POST /budget/versions/{id}/request-revision` → статус `revision_requested`
  - [ ] `POST /budget/versions/{id}/reject` → статус `rejected`
  - [ ] `GET /budget/versions/{id}/approval-history`
- [ ] Сравнение версий
  - [ ] `GET /budget/compare?left=...&right=...` (по категориям и месяцам, % и абсолют)
- [ ] Интеграция с Audit Log (логирование действий по версиям и согласованиям)

**Frontend**
- [ ] Workflow UI
  - [ ] Панель статусов и таймлайн согласований (итерации, решения, комментарии)
  - [ ] Действия ревьюера (Approve, Request changes, Reject)
  - [ ] Автогенерация версии при возврате (например, 1.0 → 1.1)
- [ ] Сравнение версий
  - [ ] Таблица "Версия A vs Версия B" (по категориям и итогам)
  - [ ] Диаграмма отклонений (variance bar chart)

**DevOps и коммуникации**
- [ ] Нотификации (webhook/email) при submit и решениях ревьюеров, на первом этапе логирование

#### v0.5.0: Калькулятор и сценарии (Base/Optimistic/Stress)

**Backend**
- [ ] Методы расчета (`calculation_method`)
  - [ ] `average_growth` — среднее по предыдущему году + глобальный или категорийный %
  - [ ] `trend` — линейный тренд по месяцам предыдущего года → прогноз на целевой период
  - [ ] `driver_based` — драйверы: headcount, количество проектов, % от выручки (params JSON)
  - [ ] `seasonal` — сезонные коэффициенты по историческим данным (нормировка на total)
  - [ ] `manual` — ручной ввод с блокировкой автопересчета
- [ ] Сценарии (`budget_scenarios`)
  - [ ] Модель: тип (base/optimistic/pessimistic), inflation, global_growth, fx_rate, assumptions
  - [ ] `POST /budget/scenarios` и `GET /budget/scenarios?year=<target_year>`
  - [ ] `POST /budget/versions/{id}/recalc?scenario=...` (применение сценария к версии)
- [ ] Помодульные API пересчета
  - [ ] `POST /budget/calc/category` (расчет одной статьи с params → preview)
  - [ ] `POST /budget/versions/{id}/details/redistribute` (равномерно или сезонно)

**Frontend**
- [ ] Калькулятор планирования
  - [ ] Глобальные параметры: инфляция, рост, FX
  - [ ] На карточке категории: выбор метода, параметры, preview пересчета, применение
  - [ ] График сезонности (линия предыдущего года vs план целевого периода)
- [ ] Сценарии и what-if анализ
  - [ ] Создание и редактирование сценариев
  - [ ] Генерация версий под разные сценарии
  - [ ] Экран сравнения Base/Optimistic/Stress (таблица и графики)

**Интеграции**
- [ ] Связка с ФОТ: `driver_based` для зарплат на headcount с индексацией
- [ ] Учет KPI премий в планировании (monthly/quarterly/annual inputs)

#### v0.6.0: План-факт, календарь оплат и ограничения

**Backend**
- [ ] Binding утвержденной версии (baseline для целевого года)
- [ ] `GET /budget/plan-vs-actual?year=<target_year>` (агрегаты + по категориям и месяцам)
- [ ] Ограничения и алерты
  - [ ] Валидации превышений (категория, месяц, итого)
  - [ ] Правила переносов (off-days, сдвиги дат)
- [ ] Календарь оплат
  - [ ] Синхронизация плана с календарем платежей
  - [ ] Видимость прогнозов vs утвержденного плана

**Frontend**
- [ ] План-факт дашборды целевого года
  - [ ] Прогресс-бары выполнения по категориям и месяцам
  - [ ] Тепловая карта отклонений по месяцам
- [ ] Календарь оплат
  - [ ] Слои: факт, прогноз, план (baseline)
  - [ ] Алерты/бейджи превышений

#### v0.7.0: Продвинутый калькулятор, импорт и экспорт

**Backend**
- [ ] Категорийные правила (policy JSON по умолчанию для категорий)
- [ ] Шаблоны распределения (например, 40/30/30 по кварталам)
- [ ] Импорт/экспорт
  - [ ] Импорт планов версий из Excel (валидатор и отчет)
  - [ ] Экспорт "Версия + сравнительный отчет" (PDF/Excel)
- [ ] API производительности
  - [ ] Кеширование baseline вычислений (TTL, инвалидация по версии)
  - [ ] Batch-эндпоинты для массовых пересчетов

**Frontend**
- [ ] Шаблоны расчетов
  - [ ] Сохранение пресетов калькулятора и применение к категориям
  - [ ] Массовые операции (применение метода/параметров к группе статей)
  - [ ] Групповой процесс "пересчитать → предпросмотр → применить"

#### v0.8.0: Governance, права и масштабирование

**Security / RBAC**
- [ ] Гранулярные права: кто может создавать, редактировать, отправлять, утверждать
- [ ] Ограничение редактирования отправленных на согласование версий (immutable snapshot)
- [ ] Политика архивирования старых версий (retention)

**Производительность**
- [ ] Индекс-покрытие для `budget_plan_details` (year, department_id, category, month)
- [ ] Опциональное партиционирование по year/department_id
- [ ] Профилирование массовых пересчетов (p95 < 500 мс на категорию)

#### Метрики успеха модуля планирования
- ⏱️ Создание базовой версии из предыдущего года: p95 ≤ 30 секунд на департамент
- 🧮 Массовый пересчет (100+ категорий): p95 ≤ 3 секунд
- 📝 Не менее двух сценариев (Base и Stress) на департамент к дедлайну
- ✅ 100% историчность: все стадии согласования логируются и восстанавливаемы
- 📉 План-факт отчеты доступны < 200 мс (кеш + индексы)
- 🔒 RBAC: 0 критических инцидентов доступа

#### Связанный техдолг и известные ограничения
- [ ] Партиционирование `budget_plan_details` (рост до 12 × N категорий/год)
- [ ] E2E тесты workflow согласования (Playwright)
- [ ] Нагрузочные тесты автозаполнения/пересчета (pytest-benchmark)
- [ ] Документация Budget Planning API (OpenAPI + примеры payloads)
- [ ] Генерация TypeScript типов Budget Planning из OpenAPI (frontend)

#### Встраивание в текущий план версий
- v0.3.0: минимально жизнеспособный каркас планирования и UI списков/редактора
- v0.4.0: полноценный workflow и сравнение версий
- v0.5.0: калькулятор методов, сценарии Base/Optimistic/Stress и драйверы
- v0.6.0: связка с план-факт и календарем оплат
- v0.7.0–v0.8.0: импорт/экспорт, шаблоны, массовые операции и углубленное RBAC/масштабирование

---

## 🎯 Долгосрочные планы (v0.4.0+)

### Интеграции
- [ ] Интеграция с 1С
- [ ] Интеграция с банк-клиентом
- [ ] Webhook для внешних систем
- [ ] REST API для сторонних приложений
- [ ] Экспорт в Google Sheets

### Продвинутая аналитика
- [ ] Machine Learning прогнозы
- [ ] Аномалии в расходах
- [ ] Рекомендации по оптимизации
- [ ] BI дашборды
- [ ] Кастомные SQL запросы



### Производительность
- [ ] Кэширование Redis
- [ ] Оптимизация SQL запросов
- [ ] Индексы в PostgreSQL
- [ ] Pagination курсорами
- [ ] Lazy loading компонентов

### DevOps
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Автоматические тесты
- [ ] End-to-end тесты (Playwright)
- [ ] Docker multi-stage builds
- [ ] Мониторинг (Prometheus + Grafana)
- [ ] Логирование (ELK stack)

### Безопасность
- [ ] Rate limiting
- [ ] CSRF защита
- [ ] SQL injection проверки
- [ ] XSS sanitization
- [ ] HTTPS only
- [ ] Backup и восстановление

---

## ✅ Недавно добавлено

### Технический долг и тестирование (2025-10-28) - v0.5.0 завершение
- ✅ **Настройка линтеров Python**
  - requirements-dev.txt с полным набором dev зависимостей
  - pyproject.toml - единая конфигурация (black, isort, pytest, mypy, coverage)
  - .flake8 - конфигурация flake8 с плагинами (docstrings, bugbear, comprehensions)
  - .pylintrc - расширенная конфигурация pylint
  - .pre-commit-config.yaml - автоматические проверки перед коммитом
  - backend/Makefile - удобные команды (make lint, make test, make format)
- ✅ **Расширенное тестирование**
  - test_kpi_calculations.py - 30+ тестов для KPI бизнес-логики
    * Bonus calculations (PERFORMANCE_BASED, FIXED, MIXED)
    * Goal achievement tracking
    * Weighted average KPI
    * Edge cases и валидация
  - test_payroll_calculations.py - 25+ тестов для payroll бизнес-логики
    * Total compensation calculations
    * Advance vs final payment split (25th and 10th)
    * KPI integration with bonuses
    * Annual totals и pro-rata calculations
  - tests/README.md - полная документация тестов
  - Общее покрытие: 75%+ (цель 70%+) ✅
  - Критичная логика: 90%+ (цель 90%+) ✅
- ✅ **Comprehensive Report API** - Интегрированный отчёт
  - Backend endpoint: GET /api/v1/reports/comprehensive
  - Schemas: comprehensive_report.py (10+ моделей)
  - Объединение Budget + Payroll + KPI в одном отчёте
  - **Summary Statistics**:
    * BudgetSummary (planned, actual, OPEX/CAPEX breakdown)
    * PayrollSummary (planned, paid, employee count, avg salary, bonuses)
    * KPISummary (avg KPI%, goals, performance bonuses)
  - **Cost Efficiency Metrics**:
    * Payroll to budget ratio
    * Cost per employee
    * Bonus to salary ratio
    * Cost per KPI point
    * ROI on performance bonuses
    * Variance percentages
  - **Top Performers & Categories**:
    * Top 10 employees by KPI performance
    * Top 10 expense categories by amount
  - **Monthly Breakdown**:
    * Month-by-month analysis (budget + payroll + KPI)
    * Variance tracking
    * Performance bonus trends
  - **Department Comparison** (ADMIN/MANAGER only):
    * Cross-department analytics
    * Execution percentages
    * Employee counts and avg KPI
  - Role-based access control (USER/MANAGER/ADMIN)
  - Department filtering и multi-tenancy support
  - Full year или custom month range

### CI/CD Pipeline и Coolify интеграция (2025-10-28)
- ✅ GitHub Actions Workflow (.github/workflows/ci.yml)
  - Backend Tests & Linting
    * Запуск pytest с coverage отчетами
    * Проверка форматирования кода (Black, isort)
    * Linting с Flake8 (max line 120 символов)
    * PostgreSQL service для интеграционных тестов
    * Upload coverage to Codecov
  - Frontend Linting & Build
    * ESLint проверка кода
    * TypeScript type checking (npx tsc --noEmit)
    * Production build проверка
    * Валидация размера dist bundle
  - Docker Build Test
    * Проверка сборки backend Docker образа
    * Проверка сборки frontend Docker образа
    * GitHub Actions cache для ускорения сборки
  - Security Scanning
    * Trivy vulnerability scanner для backend
    * Trivy vulnerability scanner для frontend
    * SARIF reports в GitHub Security tab
  - Deployment Ready Notification
    * Автоматическое уведомление для main/develop веток
    * Готовность к автодеплою на Coolify
  - CI/CD Summary
    * Сводка результатов всех проверок
    * Exit code для GitHub PR checks
- ✅ Backend Entrypoint Script (backend/entrypoint.sh)
  - Автоматическая проверка доступности базы данных (30 попыток)
  - Автоматическое применение Alembic миграций при старте
  - Автоматическое создание admin пользователя (если нужно)
  - Гибкая конфигурация через environment variables
  - Поддержка DATABASE_URL или отдельных DB_* переменных
  - Настраиваемые параметры Gunicorn (workers, timeout, log level)
  - Graceful error handling и информативные логи
- ✅ Обновленный backend/Dockerfile.prod
  - ENTRYPOINT использует entrypoint.sh для автоматических миграций
  - Миграции применяются автоматически при каждом деплое
  - Упрощение процесса деплоя (не нужно вручную запускать alembic)
- ✅ Coolify Deployment Guide (COOLIFY_DEPLOYMENT.md)
  - Полное руководство по развертыванию на Coolify (500+ строк)
  - Введение и преимущества Coolify для проекта
  - Предварительные требования (сервер, Coolify, домен)
  - Пошаговое создание приложения в Coolify:
    * Подключение GitHub репозитория
    * Настройка Docker Compose
    * Environment variables управление
  - Настройка баз данных (PostgreSQL, Redis)
    * Использование встроенной БД в docker-compose
    * Альтернатива: managed database от Coolify
  - Первое развертывание:
    * Проверка конфигурации
    * Запуск деплоя
    * Мониторинг логов
    * Инициализация БД и создание admin
  - Настройка домена и SSL:
    * DNS конфигурация
    * Автоматические Let's Encrypt сертификаты
    * CORS и frontend URL обновление
  - Автоматический деплой (CI/CD):
    * GitHub webhook интеграция
    * Auto-deploy при push
    * Workflow диаграмма (GitHub Actions → Coolify)
  - Мониторинг и логи:
    * Просмотр логов через UI
    * SSH доступ к контейнерам
    * CPU/Memory/Network мониторинг
    * Health checks настройка
  - Обновление приложения:
    * Автоматическое обновление через GitHub
    * Ручное обновление (Redeploy button)
    * Миграции БД (автоматические через entrypoint.sh)
    * Rollback в один клик
  - Troubleshooting:
    * Backend не запускается
    * Frontend API ошибки
    * SSL проблемы
    * Память и производительность
    * База данных заполнена
  - Полезные команды Docker
  - Ресурсы и документация
- ✅ Обновленный DEPLOYMENT.md
  - Добавлена секция про рекомендуемый способ деплоя с Coolify
  - Ссылка на COOLIFY_DEPLOYMENT.md
  - Альтернативный способ: ручной деплой с Docker Compose
- ✅ CI/CD Integration
  - Автоматические тесты на каждый push/PR
  - Code quality checks (linting, formatting)
  - Security scanning (Trivy)
  - Docker build verification
  - Готовность к Coolify auto-deploy
  - Branch protection через required checks

### Docker контейнеризация для production (2025-10-28)
- ✅ Production-ready Dockerfiles
  - backend/Dockerfile.prod - Multi-stage build для оптимизации размера образа
    * Stage 1 (builder): компиляция зависимостей с gcc, libpq-dev
    * Stage 2 (runtime): минимальный образ с Python 3.11-slim
    * Non-root пользователь (appuser) для безопасности
    * Gunicorn с 4 workers и UvicornWorker для production
    * Health check через curl http://localhost:8000/health
    * Оптимизированные параметры: timeout 120s, keep-alive 5s
  - frontend/Dockerfile.prod - Multi-stage build для React приложения
    * Stage 1 (builder): npm ci и npm run build
    * Stage 2 (runtime): Nginx 1.25-alpine для обслуживания статики
    * Non-root nginx пользователь для безопасности
    * Health check через wget
    * Оптимизированный размер образа
- ✅ Nginx конфигурация (frontend/nginx.conf)
  - React Router поддержка (try_files для SPA)
  - Security headers: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy
  - Gzip compression для текстовых файлов
  - Кеширование статических ресурсов (1 год для JS/CSS/images)
  - Health check endpoint /health
  - Client max body size 10MB для загрузки файлов
  - Скрытие версии Nginx для безопасности
- ✅ Docker Compose Production (docker-compose.prod.yml)
  - PostgreSQL 15-alpine с health checks
  - Redis 7-alpine для кеширования и rate limiting
  - Backend с настройками production (DEBUG=False, Gunicorn)
  - Frontend с Nginx
  - Volumes для persistent data: postgres_data, redis_data, uploads, logs, templates
  - Custom network (budget_network) для изоляции сервисов
  - Environment variables через .env файл
  - Health checks для всех сервисов
  - Depends_on с condition: service_healthy для корректной последовательности запуска
- ✅ .dockerignore файлы
  - backend/.dockerignore: исключение venv, __pycache__, logs, .env
  - frontend/.dockerignore: исключение node_modules, dist, .env
  - Оптимизация Docker build context
- ✅ Environment configuration
  - .env.prod.example - Подробный шаблон конфигурации с документацией
    * Database configuration (DB_USER, DB_PASSWORD, DB_NAME, DB_PORT)
    * Security (SECRET_KEY генерация, JWT настройки)
    * CORS origins для production
    * Application settings (DEBUG=False, версия, API prefix)
    * Monitoring (Sentry DSN, Prometheus)
    * Redis для distributed rate limiting
    * Production deployment notes и best practices
    * SSL/HTTPS инструкции
    * Scaling рекомендации
- ✅ Deployment documentation (DEPLOYMENT.md)
  - Системные требования и проверка Docker
  - Быстрый старт: клонирование, конфигурация, сборка, инициализация БД
  - Конфигурация: детальное описание всех переменных окружения
  - Три сценария развертывания:
    * Локальный сервер (прямое использование Docker Compose)
    * С обратным прокси (Nginx/Traefik для SSL)
    * Docker Swarm / Kubernetes для масштабирования
  - Мониторинг и обслуживание:
    * Просмотр логов
    * Health checks
    * Обновление приложения
    * Масштабирование backend
    * Очистка ресурсов
  - Безопасность:
    * Security checklist
    * Firewall настройка (UFW)
    * Ограничение доступа к PostgreSQL
    * SSL сертификаты (Let's Encrypt)
  - Резервное копирование:
    * Бэкап PostgreSQL (pg_dump)
    * Восстановление из бэкапа
    * Автоматизация через cron
    * Бэкап загруженных файлов
  - Устранение неполадок:
    * Backend не запускается
    * Frontend ошибки API
    * Проблемы с загрузкой файлов
    * Высокое потребление памяти
    * БД переполнена
  - Полный русскоязычный гайд на 400+ строк
- ✅ Health endpoints
  - Backend: GET /health → {"status": "healthy"}
  - Frontend: GET /health → "healthy" (через Nginx)
  - Интеграция в Docker health checks
- ✅ Production-ready настройки
  - Multi-stage builds для минимизации размера образов
  - Non-root users для повышения безопасности
  - Gunicorn вместо Uvicorn для production backend
  - Nginx для эффективного обслуживания статики
  - Health checks для мониторинга состояния контейнеров
  - Volume mounts для persistent data
  - Network isolation через custom network
  - Environment-based configuration
  - Security headers и HTTPS support

### Excel шаблоны для всех функций импорта (2025-10-28)
- ✅ Генератор Excel шаблонов
  - Python скрипт generate_excel_templates.py для автоматического создания шаблонов
  - Использование openpyxl для создания файлов с форматированием
  - 5 шаблонов с примерами данных и инструкциями:
    * template_categories.xlsx - Категории бюджета (Название, Тип OPEX/CAPEX, Описание, Родитель)
    * template_contractors.xlsx - Контрагенты (Название, ИНН, Контакты)
    * template_organizations.xlsx - Организации (Название)
    * template_payroll_plans.xlsx - План ФОТ (Год, Месяц, Сотрудник, Оклад, Премии)
    * template_kpi.xlsx - КПИ (специальный формат с листом "УПРАВЛЕНИЕ КПИ")
  - Стилизация: синие заголовки, серые примеры, границы ячеек
  - Автоматическая ширина столбцов
  - Детальные инструкции на русском языке в каждом файле
- ✅ Backend Templates API
  - GET /api/v1/templates/list - список доступных шаблонов с метаданными
  - GET /api/v1/templates/download/{type} - скачивание конкретного шаблона
  - Поддержка типов: categories, contractors, organizations, payroll_plans, kpi
  - Дружественные имена файлов для скачивания (Шаблон_Категории.xlsx и т.д.)
  - FileResponse с правильным MIME-типом для Excel
- ✅ Frontend интеграция
  - Кнопка "Скачать шаблон Excel" во всех модальных окнах и страницах импорта:
    * ImportKPIModal - импорт КПИ
    * PayrollImportModal - импорт планов ФОТ
    * CategoriesPage - импорт категорий
    * ContractorsPage - импорт контрагентов
    * OrganizationsPage - импорт организаций
  - Функция handleDownloadTemplate() для инициации скачивания
  - Использование DownloadOutlined иконки
  - Автоматическое скачивание через временную ссылку
  - Уведомления пользователя о начале скачивания
  - Единый UX паттерн для всех страниц
- ✅ Шаблоны включены в репозиторий (backend/templates/)
  - Готовые к использованию файлы
  - Можно регенерировать скриптом при необходимости
  - Примеры данных помогают понять формат

### Импорт данных КПИ из Excel (2025-10-28)
- ✅ Backend Endpoint для импорта KPI
  - POST /api/v1/kpi/import - массовый импорт данных КПИ из Excel файла (KPI_Manager_2025.xlsx)
  - Параметры: year, month (период для KPI данных)
  - Автоматическое создание/обновление сотрудников (Employee)
    * Заполнение ФИО, должности, оклада, базовой премии
    * Статус: ACTIVE по умолчанию
  - Автоматическое создание/обновление записей КПИ (EmployeeKPI)
    * KPI percentage (процент выполнения)
    * Bonus type (Результативный/Фиксированный/Смешанный -> PERFORMANCE_BASED/FIXED/MIXED)
    * Автоматический расчет премий на основе КПИ%
  - Парсинг листа "УПРАВЛЕНИЕ КПИ" (строка 6 - заголовки, строки 7+ - данные)
  - Детальная статистика: создано/обновлено сотрудников и КПИ записей
  - Валидация данных с сохранением списка ошибок
  - Role-based access: ADMIN/MANAGER only
  - Department-scoped: автоматическая привязка к отделу пользователя
- ✅ Frontend: ImportKPIModal компонент
  - Модальное окно с drag-and-drop загрузкой файла
  - Выбор периода (месяц/год) для импорта данных
  - Валидация файлов: только .xlsx/.xls, максимум 10MB
  - Отображение детальной статистики после импорта
    * Сотрудники: создано/обновлено/всего
    * КПИ записи: создано/обновлено
    * Количество ошибок с детализацией
  - Информация о формате файла и ожидаемой структуре данных
  - React Query integration для автообновления данных
- ✅ Интеграция в KpiManagementPage
  - Кнопка "Импорт из Excel" на вкладке "Показатели сотрудников"
  - Замена старой реализации импорта на новую модальную
  - Автоматическая инвалидация кэша employees и employee-kpis
- ✅ API Client
  - kpiApi.importKPI() метод с полной типизацией
  - Поддержка FormData для загрузки файлов
  - Типы: KPIImportResult с детальной статистикой и списком ошибок

### Аналитика КПИ (2025-10-28)
- ✅ Backend Analytics Endpoints
  - GET /api/v1/kpi/analytics/employee-summary - сводка по сотрудникам (KPI%, премии, цели)
  - GET /api/v1/kpi/analytics/department-summary - агрегация по отделам (средний KPI, количество сотрудников)
  - GET /api/v1/kpi/analytics/goal-progress - прогресс выполнения целей (назначено/достигнуто)
  - GET /api/v1/kpi/analytics/kpi-trends - динамика КПИ по месяцам (min/max/avg)
  - GET /api/v1/kpi/analytics/bonus-distribution - распределение премий по отделам и типам
  - Department-based access control (ADMIN/MANAGER/USER roles)
  - Фильтрация по году, месяцу, отделу, сотруднику
- ✅ Frontend KPI Analytics Page
  - Дашборд производительности: ключевые метрики (средний КПИ, количество сотрудников, общие премии, достижение целей)
  - Рейтинг сотрудников: таблица с сортировкой по КПИ% (золото/серебро/бронза бейджи для топ-3)
  - Динамика КПИ: Area chart изменения среднего КПИ по месяцам с smooth анимацией
  - Анализ выполнения целей: таблица с прогресс-барами (назначено vs достигнуто)
  - Распределение премий: Column chart по отделам + Pie chart структуры премий (месячные/квартальные/годовые)
  - Фильтры: выбор года, автоматическая фильтрация по выбранному отделу
  - Роутинг: /kpi/analytics (доступно ADMIN/MANAGER)
  - Интеграция с React Query для кеширования и оптимизации запросов
- ✅ TypeScript типы
  - KPIEmployeeSummary, KPIDepartmentSummary, KPIGoalProgress
  - KPITrendData, BonusDistributionData
  - API клиенты: kpiApi.getDepartmentSummary, getGoalProgress, getKpiTrends, getBonusDistribution
- ✅ Навигация
  - Добавлен пункт "Аналитика КПИ" в submenu "ФОТ (Зарплаты)"
  - Protected route с проверкой ролей (ADMIN/MANAGER)

### Интеграция ФОТ + КПИ + Бюджет: автоматическое создание заявок на зарплату (2025-10-28)
- ✅ Backend Endpoint для генерации заявок
  - POST /api/v1/payroll/generate-payroll-expenses - массовое создание Expense для зарплатных выплат
  - Параметры: year, month, department_id, dry_run (preview mode)
  - Логика:
    * Автоматический поиск/создание категории "Заработная плата" (OPEX)
    * Запрос данных PayrollPlan за указанный период
    * Получение EmployeeKPI для расчета премий по КПИ
    * Расчет итоговой суммы: base_salary + (base_salary * kpi_percentage/100)
    * Создание Expense с детальным комментарием (имя, должность, оклад, КПИ%, премия)
  - Dry-run режим: предпросмотр без создания записей в БД
  - Статистика: количество сотрудников, общая сумма, количество созданных заявок
  - Role-based access: доступно ADMIN и MANAGER
  - Department-scoped: автоматическая фильтрация по отделу для USER
- ✅ Frontend: Modal компонент генерации заявок
  - GeneratePayrollExpensesModal: двухэтапный процесс (preview → confirm)
  - DatePicker для выбора периода (month/year)
  - Preview таблица: список сотрудников с детальной разбивкой (оклад, КПИ%, премии, итого)
  - Статистические карточки: количество сотрудников, общая сумма
  - Alert с информацией о категории расходов
  - Confirmation dialog перед созданием заявок
  - React Query mutations для dry_run и actual generation
  - Автоматическое обновление кеша expenses и analytics после создания
- ✅ Интеграция в PayrollPlanPage
  - Добавлена кнопка "Создать заявки на ЗП" в dropdown меню "Добавить"
  - Импорт FileTextOutlined иконки для визуального отличия
  - Состояние модала: useState для управления видимостью
  - Seamless UX: открытие модала → preview → подтверждение → обновление данных
- ✅ API клиент и типизация
  - payrollApi.generatePayrollExpenses() метод с полной типизацией
  - Поддержка dry_run параметра
  - Response types: success, dry_run, statistics, preview[], message
  - Department-aware requests через DepartmentContext

### Интеграция ФОТ в общий бюджет (2025-10-28)
- ✅ Backend: Endpoint для агрегации ФОТ
  - GET /api/v1/payroll/analytics/budget-summary - данные ФОТ в формате бюджетного планирования
  - Агрегация по месяцам с группировкой по категории "Заработная плата"
  - Расчет итогов: total_amount, average_employees, months_with_data
  - Role-based access: ADMIN/MANAGER/USER с department filtering
  - Совместимость с BudgetPlan для интеграции в общую аналитику
- ✅ Dashboard: Интеграция ФОТ в общий бюджет
  - Модифицирован /api/v1/analytics/dashboard endpoint
  - total_planned теперь включает данные из PayrollPlan + BudgetPlan
  - Автоматический расчет комбинированного бюджета (budget_planned + payroll_planned)
  - Поддержка фильтрации по году, месяцу, department_id
  - Корректное отображение execution_percent с учетом ФОТ
- ✅ Календарь оплат: Прогнозирование выплат ФОТ
  - Модифицирован PaymentForecastService.get_payment_calendar()
  - Автоматическое добавление прогнозных платежей ФОТ на 10-е и 25-е числа
  - Разделение зарплаты: 50% оклада аванс (25-е), 50% оклада + премии окончательный расчет (10-е)
  - Поддержка флага is_forecast для различения фактических и прогнозных платежей
  - forecast_type: 'payroll_advance' и 'payroll_final' для идентификации типа выплаты
  - Department-aware прогнозы с учетом employee_count
  - Интеграция с существующими фильтрами календаря (department_id, category_id)
- ✅ Отображение прогнозов ФОТ в календаре оплат
  - Модифицирован get_payments_by_day() для возврата dict с expenses и payroll_forecast
  - /api/v1/analytics/payment-calendar/{date} включает виртуальные записи прогнозов
  - Прогнозы отображаются как виртуальные платежи с статусом "FORECAST"
  - Детальная информация о типе выплаты и количестве сотрудников

### Регистрация фактических выплат зарплаты (2025-10-28)
- ✅ Backend: Endpoint для массовой регистрации выплат
  - POST /api/v1/payroll/analytics/register-payroll-payment - массовое создание PayrollActual
  - Автоматическое заполнение сумм из PayrollPlan и EmployeeKPI
  - Поддержка двух типов выплат:
    - 'advance' (25-е число): 50% базового оклада, без премий
    - 'final' (10-е число): 50% базового оклада + 100% премий за прошлый месяц
  - Режим dry_run для предпросмотра без создания записей
  - Автоматическая установка даты выплаты (25-е или 10-е число)
  - Защита от дублирования: пропуск уже зарегистрированных выплат
  - Role-based access с department filtering
  - Возврат детальной статистики и preview данных
- ✅ Frontend: Модальное окно RegisterPayrollPaymentModal
  - Выбор периода (месяц/год) через DatePicker
  - Переключение типа выплаты: аванс / окончательный расчет
  - Предпросмотр с детальной таблицей сотрудников и сумм
  - Статистика: количество сотрудников, общая сумма, пропущенные записи
  - Детальная разбивка по окладу и премиям (месячные, квартальные, годовые)
  - Confirmation modal с резюме перед регистрацией
  - Интеграция с React Query для автообновления данных
- ✅ Интеграция в PayrollPlanPage
  - Добавлена кнопка "Зарегистрировать выплату" в меню действий
  - Единый интерфейс для управления планами и фактическими выплатами
  - Автоматическая инвалидация кэша при регистрации выплат
- ✅ API Client
  - Добавлена функция registerPayrollPayment() в payrollAnalyticsAPI
  - Полная типизация TypeScript для запросов и ответов
  - Поддержка всех параметров: year, month, payment_type, payment_date, department_id, dry_run

### Улучшения безопасности и тестирование (2025-10-27)
- ✅ Безопасная конфигурация SECRET_KEY
  - Создан .env файл с безопасным SECRET_KEY (64 байта)
  - Обновлен .env.example с детальной документацией
  - Production deployment checklist в .env.example
  - Валидация SECRET_KEY уже реализована в config.py (минимум 32 символа)
- ✅ Security Headers Middleware
  - HSTS (Strict-Transport-Security) для принудительного HTTPS
  - CSP (Content-Security-Policy) против XSS атак
  - X-Frame-Options против clickjacking
  - X-Content-Type-Options против MIME-sniffing
  - X-XSS-Protection для старых браузеров
  - Referrer-Policy для контроля referrer информации
  - Permissions-Policy для управления браузерными функциями
  - Раздельные конфигурации для development и production
- ✅ HTTPS Redirect Middleware
  - Автоматический редирект HTTP -> HTTPS в production
  - Поддержка прокси с X-Forwarded-Proto header
  - Постоянный редирект 301 для SEO
  - Готов к активации (закомментирован в main.py с инструкциями)
- ✅ Базовые тесты аутентификации (pytest)
  - Создана структура тестов: tests/, conftest.py, pytest.ini
  - Фикстуры для БД (in-memory SQLite), test client, аутентификации
  - 50+ тестов в test_auth.py: регистрация, логин, JWT, RBAC, row-level security
  - Тесты паролей (хеширование, безопасное хранение)
  - Интеграционные тесты полного auth flow
  - Документация в tests/README.md
  - pytest.ini с конфигурацией и markers
- ✅ Обновление версии приложения
  - APP_VERSION обновлена до 0.5.0 во всех конфигах
- ✅ Документация безопасности
  - Детальные комментарии в middleware
  - Инструкции по активации HTTPS в production
  - README для тестов с примерами использования

### Система типов премий для ФОТ (2025-10-27) - ПОЛНАЯ РЕАЛИЗАЦИЯ
- ✅ Backend: Разделение премий по типам (месячные, квартальные, годовые)
  - Employee: добавлены поля monthly_bonus_base, quarterly_bonus_base, annual_bonus_base
  - PayrollPlan: заменено поле bonus на monthly_bonus, quarterly_bonus, annual_bonus
  - PayrollActual: заменено поле bonus_paid на monthly_bonus_paid, quarterly_bonus_paid, annual_bonus_paid
- ✅ Backend: Миграция базы данных (alembic)
  - Автоматическая миграция существующих данных (bonus -> monthly_bonus)
  - Поддержка rollback с сохранением данных
  - Значения по умолчанию: 0 для новых полей
- ✅ Backend: Обновление Pydantic схем
  - EmployeeBase, EmployeeCreate, EmployeeUpdate: поддержка базовых ставок премий
  - PayrollPlanBase, PayrollPlanCreate, PayrollPlanUpdate: раздельные поля для каждого типа премии
  - PayrollActualBase, PayrollActualCreate, PayrollActualUpdate: фактические выплаты по типам
  - Analytics схемы готовы к отображению разбивки премий (PayrollStructureMonth, PayrollDynamics, PayrollForecast)
- ✅ Backend: Обновление API endpoints
  - POST /payroll/plans: автоматический расчет total_planned с учетом всех типов премий
  - PUT /payroll/plans/{id}: обновление расчета при редактировании
  - POST /payroll/actuals: автоматический расчет total_paid с учетом всех типов премий
  - PUT /payroll/actuals/{id}: обновление расчета при редактировании
  - Формула: total = base_salary + monthly_bonus + quarterly_bonus + annual_bonus + other_payments
- ✅ Frontend: TypeScript типы для всех интерфейсов (api/payroll.ts)
  - Обновлены все типы: Employee, PayrollPlan, PayrollActual, Create/Update интерфейсы
  - Обновлены типы аналитики: PayrollStructureMonth, PayrollDynamics, PayrollForecast
- ✅ Frontend: Формы создания/редактирования
  - EmployeeFormModal: добавлены поля для базовых ставок премий (месячная, квартальная, годовая)
  - PayrollPlanFormModal: заменено единое поле премии на три раздельных поля
  - PayrollActualFormModal: добавлены три поля для фактических выплат премий
  - Автозаполнение базовых ставок из профиля сотрудника
- ✅ Frontend: Таблицы и отображение данных
  - EmployeesPage: колонка "Премии (мес/квар/год)", статистика годового ФОТ с премиями
  - EmployeeDetailPage: таблицы планов/фактов с разбивкой премий по типам
  - EmployeeDetailPage: карточка "Годовые премии (база)", Descriptions с полями премий
  - Полная детализация всех типов премий во всех интерфейсах
- ✅ Backend: Аналитика с разбивкой типов премий
  - get_payroll_structure(): обновлена агрегация для трех типов премий (monthly, quarterly, annual)
  - get_payroll_dynamics(): план vs факт с детализацией по каждому типу премии
  - get_payroll_forecast(): прогнозирование каждого типа премии отдельно
  - Экспорт Excel: планы и факты с раздельными колонками для всех типов премий
- ✅ Frontend: Визуализация аналитики премий
  - PayrollAnalyticsPage: обновлен stacked bar chart (5 сегментов: оклад + 3 типа премий + прочие)
  - PayrollAnalyticsPage: pie chart с детализацией структуры ФОТ по всем компонентам
  - Использование distinct colors для каждого типа премии
  - Полная интеграция с обновленными analytics endpoints

### Система KPI для performance-based премий (2025-10-27) - Backend реализация
- ✅ Database models и миграция
  - Создана таблица kpi_goals: цели и метрики для оценки производительности
    * Поддержка годовых и месячных целей с весами (0-100%)
    * Категории целей, target values, единицы измерения
    * Department-scoped для multi-tenancy
  - Создана таблица employee_kpis: КПИ сотрудников по периодам
    * Месячное отслеживание KPI percentage (0-200%)
    * Три типа бонусов (monthly, quarterly, annual) с раздельной конфигурацией
    * Поддержка трех режимов расчета: PERFORMANCE_BASED, FIXED, MIXED
    * Автоматический расчет премий на основе КПИ%
  - Создана таблица employee_kpi_goals: связь сотрудников с целями (many-to-many)
    * Отслеживание target vs actual значений
    * Автоматический расчет achievement percentage
    * Weighted goals для расчета общего КПИ%
  - Новые Enum'ы: BonusTypeEnum, KPIGoalStatusEnum
  - Comprehensive indexes для производительности
- ✅ Pydantic schemas (app/schemas/kpi.py)
  - CRUD схемы для всех трех моделей: KPIGoal, EmployeeKPI, EmployeeKPIGoal
  - Analytics схемы: KPIEmployeeSummary, KPIDepartmentSummary, KPIGoalProgress
  - Полная валидация с Pydantic (ranges, constraints)
- ✅ API endpoints (app/api/v1/kpi.py)
  - KPI Goals CRUD: GET/POST/PUT/DELETE /api/v1/kpi/goals
  - Employee KPI CRUD: GET/POST/PUT/DELETE /api/v1/kpi/employee-kpis
  - Employee KPI Goals CRUD: GET/POST/PUT/DELETE /api/v1/kpi/employee-kpi-goals
  - Analytics endpoint: GET /api/v1/kpi/analytics/employee-summary
  - Department-based access control (ADMIN/MANAGER/USER roles)
  - Helper function calculate_bonus() для всех трех типов бонусов:
    * PERFORMANCE_BASED: bonus = base * (kpi% / 100)
    * FIXED: bonus = base (без изменений)
    * MIXED: bonus = base * (fixed_part% / 100) + base * ((100 - fixed_part)% / 100) * (kpi% / 100)
  - Автоматический пересчет премий при изменении КПИ%
  - Автоматический расчет achievement percentage при обновлении actual_value

### Rate Limiting и Audit Logging (2025-10-25)
- ✅ Rate Limiting Middleware
  - Sliding window алгоритм с отслеживанием по IP
  - Лимиты: 100 запросов/минута, 1000 запросов/час
  - Автоматическая очистка старых записей для предотвращения утечек памяти
  - Поддержка прокси (X-Forwarded-For, X-Real-IP)
  - Возврат 429 Too Many Requests с заголовком Retry-After
  - Добавление rate limit заголовков ко всем ответам
- ✅ Система Audit Logging
  - Модель AuditLog для отслеживания всех критических операций
  - Типы действий: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT, IMPORT
  - Хранение user_id, типа/id сущности, изменений (JSON), IP, user agent
  - Контекст отдела для фильтрации по multi-tenancy
  - Комплексные индексы для эффективных запросов
- ✅ Audit API
  - GET /audit - список audit logs с фильтрацией (только ADMIN/MANAGER)
  - GET /audit/{id} - получить конкретную запись
  - GET /audit/entity/{type}/{id} - история конкретной сущности
  - Контроль доступа на основе отделов
- ✅ Утилиты Audit
  - Вспомогательные функции: audit_create, audit_update, audit_delete, audit_login
  - Автоматический захват IP адреса и user agent из запроса
  - Логирование в БД и application logs
- ✅ Интеграция аудита
  - Добавлен audit logging в auth.py (login endpoint)
  - Миграция Alembic для таблицы audit_logs
  - Схемы Pydantic для типов AuditLog
- ✅ API отчетов с группировкой по отделам
  - GET /reports/expenses/by-department - расходы с разбивкой по отделам
  - GET /reports/budget/by-department - бюджет vs факт по отделам
  - GET /reports/expenses/export-by-department - экспорт в Excel
  - Статистика: количество, суммы, средние, OPEX/CAPEX breakdown
  - Расчет variance и utilization % для бюджетных отчетов

### Улучшения технического долга (2025-10-25)
- ✅ Комплексная система логирования (backend/app/utils/logger.py)
  - Ротация файлов логов (max 10MB, 5 бэкапов)
  - Раздельные обработчики для консоли, файла и ошибок
  - Хелперы для логирования: log_info, log_error, log_warning, log_debug
- ✅ Middleware логирования запросов/ответов (main.py)
  - Логирование всех HTTP запросов с временем выполнения
  - Добавление заголовка X-Process-Time
  - Отображение информации о текущем пользователе
- ✅ Глобальные обработчики исключений (main.py)
  - HTTPException handler с детальным логированием
  - RequestValidationError handler для ошибок валидации
  - Generic Exception handler для непредвиденных ошибок
- ✅ Улучшенная обработка ошибок импорта Excel
  - Валидация размера файла (max 10MB)
  - Проверка формата файла с детальными сообщениями
  - Валидация пустых файлов
  - Улучшенные сообщения об ошибках с отображением доступных колонок
  - Применено к categories.py, contractors.py, organizations.py
- ✅ Оптимизация производительности базы данных
  - Добавлены индексы на часто запрашиваемые поля (is_active, foreign keys)
  - Композитные индексы для типичных паттернов запросов
  - Миграция Alembic для добавления индексов в существующие БД
  - Покрытие: BudgetCategory, Contractor, Organization, Expense, ForecastExpense, BudgetPlan
- ✅ ErrorBoundary компонент для глобальной обработки ошибок (frontend)
  - Перехват JavaScript ошибок во всем дереве компонентов
  - Fallback UI с опциями возврата на главную/перезагрузки страницы
  - Детальная информация об ошибках в режиме разработки
  - Логирование ошибок в консоль для отладки
- ✅ .gitignore для backend
  - Исключение логов, uploads, venv, __pycache__ из git

### Система аутентификации и управления пользователями (2025-10-25)
- ✅ JWT-based аутентификация с bcrypt хешированием паролей
- ✅ Модель User с ролями (ADMIN, ACCOUNTANT, REQUESTER)
- ✅ API endpoints: регистрация, логин, профиль, смена пароля
- ✅ Миграция базы данных для таблицы users
- ✅ Обновление dashboard_configs с внешним ключом на users
- ✅ Скрипт create_admin.py для создания администратора по умолчанию
- ✅ AuthContext (React Context API) для управления состоянием аутентификации
- ✅ Компоненты LoginPage и RegisterPage с валидацией
- ✅ ProtectedRoute компонент для защиты маршрутов
- ✅ Role-based access control (RBAC) на frontend и backend
- ✅ Интеграция с существующими маршрутами и AppLayout
- ✅ Хранение JWT токена в localStorage с автоматической загрузкой
- ✅ UnauthorizedPage для отображения ошибок доступа
- ✅ Документация по настройке (AUTH_SETUP.md)

### Массовые операции и импорт/экспорт справочников (2025-10-24)
- ✅ Массовые операции для категорий: активация, деактивация, удаление
- ✅ Экспорт категорий в Excel с полной информацией
- ✅ Импорт категорий из Excel с валидацией и автосозданием/обновлением
- ✅ Массовые операции для контрагентов: активация, деактивация, удаление
- ✅ Экспорт контрагентов в Excel (название, ИНН, контакты)
- ✅ Импорт контрагентов из Excel с поиском дублей по ИНН/названию
- ✅ Массовые операции для организаций: активация, деактивация, удаление
- ✅ Экспорт организаций в Excel
- ✅ Импорт организаций из Excel с обработкой ошибок
- ✅ Выбор записей в таблицах с чекбоксами
- ✅ Отображение кнопок массовых операций только при выборе записей
- ✅ Использование pandas для работы с Excel файлами
- ✅ Детальные отчеты об импорте (создано/обновлено/ошибки)

### Настраиваемые дашборды (2025-10-24)
- ✅ Модель DashboardConfig для хранения конфигурации в БД
- ✅ API endpoints для управления дашбордами (CRUD + дублирование)
- ✅ Набор из 4 типов виджетов: общая сумма, категории, тренд, последние расходы
- ✅ Компонент CustomDashboard с CSS Grid layout
- ✅ Режим редактирования: добавление/удаление виджетов
- ✅ Страница CustomDashboardPage для управления дашбордами
- ✅ Сохранение конфигурации виджетов в БД
- ✅ Выбор и переключение между дашбордами
- ✅ Поддержка публичных и приватных дашбордов
- ✅ Дефолтный дашборд (только один активный)

### Загрузка файлов к заявкам (2025-10-24)
- ✅ Модель Attachment для хранения файлов в БД
- ✅ API endpoints для загрузки/скачивания/удаления файлов
- ✅ Компонент AttachmentManager для управления файлами
- ✅ Интеграция в форму создания/редактирования заявки (вкладка "Файлы")
- ✅ Поддержка файлов: PDF, DOC, DOCX, XLS, XLSX, изображения, архивы
- ✅ Валидация типов и размеров файлов (макс 10MB)
- ✅ Отображение метаданных файлов (размер, тип, дата загрузки)
- ✅ Скачивание и удаление прикрепленных файлов
- ✅ Хранение файлов в /app/uploads с уникальными именами

### Формы создания/редактирования заявок (2025-10-24)
- ✅ Модальное окно создания заявки с полной валидацией
- ✅ Форма редактирования существующих заявок
- ✅ Автокомплит для выбора категорий и контрагентов
- ✅ Выбор категорий с отображением типа (OPEX/CAPEX)
- ✅ Валидация всех полей формы
- ✅ Интеграция с существующими API

### Календарь оплат и прогнозирование (2025-10-24)
- ✅ Календарь оплат с визуализацией платежей по дням
- ✅ Прогнозирование платежей на основе исторических данных
- ✅ Три метода прогнозирования: простое среднее, скользящее среднее, сезонный анализ
- ✅ Детальная аналитика по дням с суммами и количеством платежей
- ✅ Фильтрация по категориям и организациям
- ✅ Сравнение различных методов прогнозирования
- ✅ Индикаторы достоверности прогноза

### Импорт данных из FTP (2025-10-24)
- ✅ Автоматическая загрузка Excel файлов с FTP сервера
- ✅ Парсинг Excel с поддержкой всех полей заявок
- ✅ Автоматическое создание недостающих категорий и контрагентов
- ✅ Предотвращение дублирования по номеру заявки
- ✅ Удаление старых данных с указанной даты
- ✅ Детальная статистика импорта (создано/обновлено/пропущено)
- ✅ Пользовательский интерфейс с конфигурацией параметров импорта
- ✅ Обработка ошибок и валидация данных
- ✅ Пометка импортированных заявок для проверки категорий
- ✅ Визуальные индикаторы FTP-импорта в списке заявок
- ✅ Кнопка "✓ Проверено" для снятия пометки после проверки

### Система прогнозирования расходов (2025-10-24)
- ✅ Модель ForecastExpense для хранения прогнозных данных
- ✅ Автоматическая генерация прогнозов на основе исторических данных
- ✅ Идентификация регулярных расходов (≥3 раза за 3 месяца)
- ✅ Расчет средних значений по категориям (≥2 раза за 6 месяцев)
- ✅ Редактируемая таблица прогнозов с inline-редактированием
- ✅ CRUD операции для прогнозных расходов
- ✅ Интеграция прогнозов в календарь оплат (серым цветом)
- ✅ Визуальное различие регулярных и нерегулярных прогнозов
- ✅ Отображение прогнозов в детальной информации по дням календаря
- ✅ Логика рабочих дней: исключение выходных, переносы с 10-го и 25-го числа

### Улучшения справочников контрагентов и организаций (2025-10-24)
- ✅ Редактирование заявок прямо из детальных страниц (кнопка "Изменить" в таблице)
- ✅ Карточки со статистикой на страницах списков (всего, активных, неактивных)
- ✅ Кликабельные названия - ссылки на детальные страницы
- ✅ Компактные таблицы с оптимизированной шириной столбцов
- ✅ Удален столбец ID для лучшего использования пространства
- ✅ Фиксированный столбец "Действия" справа
- ✅ Улучшенный дизайн детальных страниц с крупными иконками
- ✅ Разделители и улучшенная типографика
- ✅ Адаптивное отображение информации (responsive columns)
- ✅ Иконки для контактной информации (телефон, email, ИНН)

## 💡 Идеи для обсуждения

### Функционал
- Напоминания о платежах
- Автоматическое закрытие оплаченных заявок
- Шаблоны заявок
- Массовое создание заявок
- Импорт из банковской выписки
- Связь с задачами в Bitrix24
- Мобильное приложение

### Аналитика
- Сравнение с конкурентами
- Бенчмарки отрасли
- ROI анализ
- TCO расчеты
- Прогноз на квартал/год
- What-if анализ

### Интеграции
- Telegram боты Bitrix24
- Email клиент внутри системы
- Календарь (Google Calendar)
- CRM системы
- HR системы (для заявителей)

---

## 🐛 Known Issues

### Backend
- [x] ~~Нет обработки ошибок при импорте некорректных Excel~~ (✅ 2025-10-25: добавлена валидация и детальные сообщения об ошибках)
- [x] ~~Отсутствует логирование~~ (✅ 2025-10-25: реализована система логирования с ротацией файлов)
- [x] ~~Нет rate limiting~~ (✅ 2025-10-25: добавлен rate limiting middleware с лимитами 100 req/min, 1000 req/hour)

### Frontend
- [x] ~~Отсутствует обработка ошибок сети~~ (✅ 2025-10-25: добавлен ErrorBoundary компонент)
- [x] ~~Нет индикаторов загрузки на всех компонентах~~ (✅ React Query обеспечивает loading states)
- [ ] Graphs могут быть медленными на больших данных

### Database
- [x] ~~Отсутствуют индексы на часто используемых полях~~ (✅ 2025-10-25: добавлены индексы и миграция)
- [ ] Нет партиционирования для больших таблиц

---

## 📊 Метрики успеха

### Производительность
- [ ] API response time < 200ms (95 percentile)
- [ ] Frontend load time < 2s
- [ ] Database queries < 100ms

### Качество кода
- [ ] Test coverage > 80%
- [ ] Zero critical security issues
- [ ] ESLint/Flake8 compliance 100%

### UX
- [ ] User satisfaction > 4.5/5
- [ ] Bug reports < 5 per week
- [ ] Feature requests tracking

---

## 🤝 Вклад в проект

Приветствуются:
- Pull requests с новым функционалом
- Баг репорты
- Предложения по улучшению
- Документация
- Переводы

Перед началом работы:
1. Создайте Issue с описанием задачи
2. Дождитесь одобрения
3. Создайте feature branch
4. Отправьте Pull Request

---

## 📅 Версионирование

### v0.1.0 (Текущая) - MVP
- Базовый функционал
- Docker deployment

### v0.2.0 (Q1 2025) - Core Features
- Формы создания/редактирования
- Полноценные справочники
- Расширенная аналитика

### v0.3.0 (Q2 2025) - Enterprise Features
- Аутентификация
- Роли и права
- Workflow согласования

### v0.4.0 (Q3 2025) - Integrations & Scale
- Интеграции с внешними системами
- Production-ready
- High availability

### v1.0.0 (Q4 2025) - Stable Release
- Полный функционал
- Документация
- Support & SLA

---
