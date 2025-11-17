# Инструкции для проверки и очистки на продакшн сервере

## Шаг 1: Подключитесь к серверу

```bash
ssh root@31.129.107.178
```

## Шаг 2: Перейдите в директорию проекта

```bash
# Найдите директорию проекта (обычно в /root или /app)
cd /root/west_buget_it
# или
cd /app/west_buget_it
# или используйте find
find / -name "west_buget_it" -type d 2>/dev/null
```

## Шаг 3: Обновите код с GitHub

```bash
git pull origin main
```

## Шаг 4: Проверьте дубликаты

```bash
cd backend
./scripts/check_duplicates_prod.sh
```

Этот скрипт покажет:
- ✅ Есть ли дубликаты в таблицах
- 📊 Суммы по department_id=8
- 📋 Примеры дублей (если есть)
- 🔍 UNIQUE индексы
- 📝 История импортов

## Шаг 5: Если найдены дубликаты - очистите данные

### A. Dry Run (безопасно, ничего не удалит)

```bash
source venv/bin/activate
python scripts/clean_credit_data.py --department-id 8 --dry-run
```

### B. Реальная очистка

```bash
python scripts/clean_credit_data.py --department-id 8
# Введите 'yes' для подтверждения
```

## Шаг 6: Очистите Redis кэш

```bash
# Найдите Redis контейнер
docker ps | grep redis

# Подключитесь к Redis
docker exec -it <redis_container_name> redis-cli

# Очистите кэш кредитного портфолио
KEYS credit_portfolio:*
# Если есть ключи, удалите их
DEL credit_portfolio:summary
DEL credit_portfolio:monthly_stats
# Или очистите весь кэш (ОСТОРОЖНО!)
# FLUSHDB

# Выйдите
exit
```

## Шаг 7: Перезапустите импорт (опционально)

```bash
# Через API
curl -X POST http://localhost:8000/api/v1/credit-portfolio/import/trigger \
  -H "Authorization: Bearer <YOUR_TOKEN>"

# Или подождите автоматического импорта в 08:00 MSK
```

## Шаг 8: Перезапустите контейнеры (если нужно)

### Через Docker Compose

```bash
cd /путь/к/проекту
docker-compose restart backend
docker-compose restart frontend
```

### Через Docker

Зайдите в панель Docker и сделайте **Restart** для:
- Backend service
- Frontend service

## Проверка результата

Откройте в браузере:
```
https://your-domain.com/credit-portfolio/dashboard
```

Проверьте:
- ✅ Суммы отображаются корректно (не как "-15413831348")
- ✅ "Получено кредитов" ≈ 4.5 млрд
- ✅ "Погашено тела" ≈ 4.3 млрд
- ✅ "Уплачено процентов" ≈ 185 млн
- ✅ "Остаток задолженности" ≈ 104 млн

## Если проблема не решена

### Проверьте версию фронтенда

```bash
cd frontend
grep "Number(r.amount" src/legacy/pages/CreditDashboard.tsx
```

Должно быть `Number(r.amount || 0)`. Если нет:

```bash
npm install
npm run build
```

### Проверьте логи

```bash
# Backend logs
docker logs <backend_container> --tail 100

# Frontend logs (в браузере)
# Откройте DevTools -> Console
```

### Проверьте базу данных напрямую

```bash
docker exec <postgres_container> psql -U budget_user -d it_budget_db

# Проверьте суммы
SELECT SUM(amount) FROM fin_receipts WHERE department_id = 8;
SELECT SUM(amount) FROM fin_expenses WHERE department_id = 8;

# Выход
\q
```

## Быстрая команда (всё в одной строке)

```bash
ssh root@31.129.107.178 "cd /root/west_buget_it/backend && ./scripts/check_duplicates_prod.sh"
```

## Помощь

Если что-то не работает:
1. Проверьте логи: `docker logs <container>`
2. Проверьте статус: `docker ps`
3. Проверьте диск: `df -h`
4. Проверьте память: `free -h`
