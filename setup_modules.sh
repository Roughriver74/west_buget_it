#!/bin/bash

# ============================================================================
# Setup Modules - Быстрая настройка модулей для разработки
# ============================================================================
#
# Этот скрипт автоматически настраивает модульную систему:
# 1. Применяет миграции БД
# 2. Загружает модули в БД
# 3. Включает ВСЕ модули для ВСЕХ организаций
# 4. Показывает результат
#
# Использование:
#   ./setup_modules.sh              # Полная настройка
#   ./setup_modules.sh --quick      # Без миграций (только включить модули)
#   ./setup_modules.sh --org-id 1   # Только для организации с ID=1
#
# ============================================================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║          🎛️  MODULE SYSTEM - DEV SETUP 🎛️                    ║"
echo "║                                                                ║"
echo "║  Автоматическая настройка модулей для разработки              ║"
echo "║                                                                ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Parse arguments
APPLY_MIGRATIONS=true
ORG_ID=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --quick)
      APPLY_MIGRATIONS=false
      shift
      ;;
    --org-id)
      ORG_ID="--org-id $2"
      shift 2
      ;;
    --help|-h)
      echo "Использование: $0 [OPTIONS]"
      echo ""
      echo "Опции:"
      echo "  --quick        Быстрый режим (без применения миграций)"
      echo "  --org-id ID    Включить модули только для организации с ID"
      echo "  --help, -h     Показать эту справку"
      echo ""
      exit 0
      ;;
    *)
      echo -e "${RED}❌ Неизвестный параметр: $1${NC}"
      echo "Используйте --help для справки"
      exit 1
      ;;
  esac
done

# Check if we're in the right directory
if [ ! -d "backend" ]; then
  echo -e "${RED}❌ Ошибка: Запустите скрипт из корневой директории проекта${NC}"
  exit 1
fi

cd backend

# Activate virtual environment if exists
if [ -d "venv" ]; then
  echo -e "${BLUE}🔄 Активация виртуального окружения...${NC}"
  source venv/bin/activate
else
  echo -e "${YELLOW}⚠️  Виртуальное окружение не найдено. Используем системный Python.${NC}"
fi

# Check if database is running
echo -e "${BLUE}🔍 Проверка подключения к БД...${NC}"
if ! docker ps | grep -q "it_budget_db"; then
  echo -e "${YELLOW}⚠️  База данных не запущена. Запускаем...${NC}"
  cd ..
  docker-compose up -d db
  echo -e "${GREEN}✅ База данных запущена${NC}"
  echo -e "${BLUE}⏳ Ждем 5 секунд для инициализации...${NC}"
  sleep 5
  cd backend
fi

# Apply migrations if needed
if [ "$APPLY_MIGRATIONS" = true ]; then
  echo ""
  echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}🔄 ШАГ 1: Применение миграций БД${NC}"
  echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

  alembic upgrade head

  echo -e "${GREEN}✅ Миграции применены${NC}"
else
  echo -e "${YELLOW}⏩ Пропускаем миграции (режим --quick)${NC}"
fi

# Run Python setup script
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}🔄 ШАГ 2: Настройка модулей${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

python scripts/setup_modules_dev.py $ORG_ID

# Final instructions
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 НАСТРОЙКА ЗАВЕРШЕНА!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📝 СЛЕДУЮЩИЕ ШАГИ:${NC}"
echo ""
echo -e "1️⃣  ${BLUE}Перезапустить backend:${NC}"
echo "   cd backend"
echo "   uvicorn app.main:app --reload"
echo ""
echo -e "2️⃣  ${BLUE}Перезапустить frontend (в новом терминале):${NC}"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo -e "3️⃣  ${BLUE}Обновить страницу в браузере:${NC}"
echo "   Ctrl+Shift+R (или Cmd+Shift+R на Mac)"
echo ""
echo -e "${GREEN}✅ Все модули должны быть видны в меню!${NC}"
echo ""

# Offer to restart services
echo -e "${YELLOW}Хотите перезапустить сервисы сейчас? (y/n)${NC}"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY]|д|Д)$ ]]; then
  echo -e "${BLUE}🔄 Перезапуск сервисов...${NC}"

  cd ..

  # Stop services
  echo -e "${YELLOW}⏸️  Остановка сервисов...${NC}"
  ./stop.sh

  # Start services
  echo -e "${BLUE}▶️  Запуск сервисов...${NC}"
  ./run.sh

  echo -e "${GREEN}✅ Сервисы перезапущены!${NC}"
  echo ""
  echo -e "${GREEN}Откройте http://localhost:5173 в браузере${NC}"
else
  echo -e "${BLUE}Перезапустите сервисы вручную когда будете готовы.${NC}"
fi

echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
