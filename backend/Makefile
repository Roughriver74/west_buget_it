# Makefile для IT Budget Manager Backend

.PHONY: help install install-dev format lint test test-cov clean run migrate docker-build docker-up docker-down

# Цвета для вывода
BLUE = \033[0;34m
GREEN = \033[0;32m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)IT Budget Manager Backend - Доступные команды:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Установить production зависимости
	@echo "$(BLUE)Установка production зависимостей...$(NC)"
	pip install -r requirements.txt

install-dev: ## Установить dev зависимости
	@echo "$(BLUE)Установка dev зависимостей...$(NC)"
	pip install -r requirements-dev.txt
	pre-commit install

format: ## Форматировать код (black + isort)
	@echo "$(BLUE)Форматирование кода...$(NC)"
	black app/ tests/
	isort app/ tests/

lint: ## Запустить все линтеры
	@echo "$(BLUE)Запуск линтеров...$(NC)"
	@echo "$(GREEN)Black...$(NC)"
	black --check app/ tests/
	@echo "$(GREEN)isort...$(NC)"
	isort --check-only app/ tests/
	@echo "$(GREEN)Flake8...$(NC)"
	flake8 app/ tests/
	@echo "$(GREEN)MyPy...$(NC)"
	mypy app/
	@echo "$(GREEN)Pylint...$(NC)"
	pylint app/
	@echo "$(GREEN)Bandit...$(NC)"
	bandit -r app/ -c pyproject.toml

lint-fix: format ## Исправить проблемы линтеров (форматирование)
	@echo "$(GREEN)Код отформатирован!$(NC)"

test: ## Запустить тесты
	@echo "$(BLUE)Запуск тестов...$(NC)"
	pytest tests/ -v

test-cov: ## Запустить тесты с coverage
	@echo "$(BLUE)Запуск тестов с coverage...$(NC)"
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

test-unit: ## Запустить только unit тесты
	@echo "$(BLUE)Запуск unit тестов...$(NC)"
	pytest tests/ -v -m unit

test-integration: ## Запустить только integration тесты
	@echo "$(BLUE)Запуск integration тестов...$(NC)"
	pytest tests/ -v -m integration

test-watch: ## Запустить тесты в watch mode
	@echo "$(BLUE)Запуск тестов в watch mode...$(NC)"
	pytest-watch tests/ -- -v

clean: ## Очистить временные файлы
	@echo "$(BLUE)Очистка временных файлов...$(NC)"
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name '.mypy_cache' -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name 'htmlcov' -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '.coverage' -delete
	find . -type f -name 'coverage.xml' -delete
	@echo "$(GREEN)Очистка завершена!$(NC)"

run: ## Запустить dev сервер
	@echo "$(BLUE)Запуск dev сервера...$(NC)"
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate: ## Применить миграции БД
	@echo "$(BLUE)Применение миграций...$(NC)"
	alembic upgrade head

migrate-create: ## Создать новую миграцию (использование: make migrate-create msg="описание")
	@echo "$(BLUE)Создание миграции...$(NC)"
	alembic revision --autogenerate -m "$(msg)"

migrate-rollback: ## Откатить последнюю миграцию
	@echo "$(BLUE)Откат миграции...$(NC)"
	alembic downgrade -1

docker-build: ## Собрать Docker образ
	@echo "$(BLUE)Сборка Docker образа...$(NC)"
	docker-compose build backend

docker-up: ## Запустить Docker контейнеры
	@echo "$(BLUE)Запуск Docker контейнеров...$(NC)"
	docker-compose up -d

docker-down: ## Остановить Docker контейнеры
	@echo "$(BLUE)Остановка Docker контейнеров...$(NC)"
	docker-compose down

docker-logs: ## Показать логи Docker
	@echo "$(BLUE)Логи Docker...$(NC)"
	docker-compose logs -f backend

safety: ## Проверка безопасности зависимостей
	@echo "$(BLUE)Проверка безопасности зависимостей...$(NC)"
	safety check --json

pre-commit: ## Запустить pre-commit на всех файлах
	@echo "$(BLUE)Запуск pre-commit hooks...$(NC)"
	pre-commit run --all-files

ci: lint test ## Запустить все проверки CI
	@echo "$(GREEN)Все проверки CI пройдены!$(NC)"

all: install-dev format lint test ## Установить, форматировать, проверить и протестировать
	@echo "$(GREEN)Все задачи выполнены!$(NC)"
