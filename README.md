# IT Budget Manager

Веб-платформа на FastAPI + React для управления бюджетами, расходами и смежными финансами с модульной архитектурой и интеграциями.

## Основные возможности
- Заявки на расходы с вложениями, статусы, аудит, остатки бюджета и дашборды CAPEX/OPEX
- Планирование: сценарии/версии, помесячный и понедельный план-факт, отчеты и founder dashboard
- ФОТ, сотрудники, KPI/таски, расчеты премий и налоговых сценариев
- Бюджет доходов и кредитный портфель с FTP импортом, аналитикой и AI-forecast
- Банковские транзакции: импорт/синк, AI-классификация, связи с заявками и регулярные платежи
- Универсальный импорт из Excel + готовые шаблоны (xls/), экспорт отчетов и внешний API с токенами
- Интеграции: 1С (OData, заявки/справочники/банк), модульная лицензия на уровне организации и multi-department

## Требования
- Docker + Docker Compose (для демо/разработки)
- Python 3.11+, Node.js 18+
- PostgreSQL 15+ и Redis 7+ (поднимаются контейнерами по умолчанию)

## Быстрый старт для разработки (1 команда)
1. При первом запуске скопируйте env-файлы и при необходимости заполните интеграционные переменные:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
2. Запустите автоскрипт:
   ```bash
   ./run.sh
   ```
   Скрипт поднимет PostgreSQL в Docker, установит зависимости, применит миграции, загрузит тестовые Excel-данные, создаст админа и запустит backend/frontend.
3. Откройте:
   - http://localhost:5173 — фронт
   - http://localhost:8000 — API
   - http://localhost:8000/docs — Swagger
4. Остановка сервисов: `./stop.sh`.
   Дефолтный логин: `admin/admin` (переопределяется переменными окружения для `create_admin.py`).

## Запуск через Docker Compose
```bash
# Поднять базовые сервисы
docker compose up -d

# Выполнить миграции
docker compose exec backend alembic upgrade head

# Загрузить демо-данные
docker compose exec backend python scripts/import_excel.py

# Создать админа (значения берутся из переменных окружения)
docker compose exec backend python create_admin.py

# Включить все модули для разработки
docker compose exec backend python scripts/setup_modules_dev.py
```
Приложение: frontend http://localhost:5173, backend http://localhost:8000.

## Запуск без Docker (локальная разработка)
**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
cp .env.example .env   # проверьте DB*, CORS_ORIGINS и интеграции
pip install -r requirements.txt
alembic upgrade head
python scripts/import_excel.py
python create_admin.py  # по умолчанию admin/admin
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**
```bash
cd frontend
cp .env.example .env   # обновите VITE_API_URL при необходимости
npm install
npm run dev
```

## Модули и импорт данных
- Автовключение всех модулей: `docker compose exec backend python scripts/setup_modules_dev.py` (или `./setup_modules.sh --quick` если разворачиваете без контейнера).
- Шаблоны и подробные инструкции по Excel-импорту: `docs/README_ИМПОРТ.md` и каталог `xls/`.
- Универсальная система импорта: `/api/v1/import/*`, детали в `docs/UNIVERSAL_IMPORT_SYSTEM.md`.

## Продакшен
- Быстрый гайд: `docs/DEPLOYMENT_QUICK_START.md`
- Полное описание: `docs/PRODUCTION_DEPLOYMENT.md`
- Образы для продакшена собираются GitHub Actions и используются в `docker-compose.prod.yml` (ghcr.io). Перед деплоем заполните `.env.prod` (SECRET_KEY, DB, CORS, интеграции).

## Полезные ссылки
- Настройка окружения: `docs/SETUP.md`
- Модульная система: `docs/MODULES.md`, `docs/MODULES_QUICKSTART.md`
- 1С и банка: `docs/1C_ODATA_INTEGRATION.md`, `docs/BANK_TRANSACTIONS_IMPORT_GUIDE.md`
- CI/CD: `.github/workflows/deploy.yml` (описание в `docs/DEPLOYMENT_QUICK_START.md`)

## Структура
```
west_buget_it/
├── backend/          # FastAPI, Alembic, модули, scheduler, интеграции
├── frontend/         # React 18 + Vite, Ant Design, React Query
├── docs/             # Гайды по запуску, деплою, импорту, интеграциям
├── xls/              # Готовые Excel-шаблоны для импортов
├── run.sh, stop.sh   # Хелперы для локальной разработки
├── docker-compose.yml
└── docker-compose.prod.yml
```
