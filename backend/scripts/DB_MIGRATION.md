# Миграция данных БД на сервер

Инструкция по переносу данных из локальной БД на сервер Coolify.

## Предварительные требования

- `pg_dump` и `psql` должны быть установлены локально
- Доступ к серверу по SSH (если используете Coolify)
- Права на чтение локальной БД и запись в удаленную

---

## Шаг 1: Экспорт локальной БД

### Вариант A: Используя скрипт (рекомендуется)

```bash
cd backend
./scripts/export_db.sh
```

Скрипт:
- Создаст директорию `backend/backups/` если её нет
- Экспортирует БД в файл `db_export_YYYYMMDD_HHMMSS.sql`
- Покажет размер файла и следующие шаги

### Вариант B: Вручную

```bash
# Для Docker PostgreSQL (локальный)
pg_dump -h localhost -p 54329 -U budget_user -d it_budget_db \
  --no-owner --no-acl --clean --if-exists \
  -f backup.sql

# Введите пароль: budget_pass
```

**Параметры:**
- `--no-owner` - не включать владельца объектов
- `--no-acl` - не включать права доступа
- `--clean` - добавить команды DROP перед CREATE
- `--if-exists` - использовать IF EXISTS при DROP

---

## Шаг 2: Копирование файла на сервер

### Если используете Coolify с прямым доступом к БД:

```bash
# Скопируйте файл на сервер через SCP
scp backend/backups/db_export_*.sql user@your-server:/path/to/backups/

# Или используйте любой другой способ передачи файла
```

### Если используете веб-интерфейс:

1. Сохраните файл локально
2. Подключитесь к серверу через SSH
3. Загрузите файл любым удобным способом (scp, sftp, wget и т.д.)

---

## Шаг 3: Импорт в БД на сервере

### ⚠️ ВАЖНО: Создайте бэкап текущей БД на сервере!

```bash
# На сервере, перед импортом
PGPASSWORD=your_password pg_dump -h postgres_host -p 5432 \
  -U budget_user -d it_budget_db \
  -f backup_before_import_$(date +%Y%m%d).sql
```

### Вариант A: Используя скрипт (рекомендуется)

На сервере (или локально, если настроен доступ к удаленной БД):

```bash
cd backend
./scripts/import_db.sh /path/to/backups/db_export_20251029_120000.sql
```

Скрипт:
- Покажет параметры подключения
- Запросит подтверждение
- Выполнит импорт с проверкой ошибок

### Вариант B: Вручную

```bash
# Подключитесь к контейнеру БД в Coolify или используйте удаленное подключение
PGPASSWORD=your_password psql -h postgres_host -p 5432 \
  -U budget_user -d it_budget_db \
  -f db_export_20251029_120000.sql \
  -v ON_ERROR_STOP=1
```

---

## Шаг 4: Проверка данных

После импорта проверьте:

```sql
-- Количество записей в основных таблицах
SELECT 'departments' as table_name, COUNT(*) as count FROM departments
UNION ALL
SELECT 'users', COUNT(*) FROM users
UNION ALL
SELECT 'expenses', COUNT(*) FROM expenses
UNION ALL
SELECT 'budget_categories', COUNT(*) FROM budget_categories
UNION ALL
SELECT 'employees', COUNT(*) FROM employees;

-- Проверка последних записей
SELECT * FROM expenses ORDER BY created_at DESC LIMIT 10;
```

---

## Важные примечания

### 🔒 Безопасность

1. **НЕ коммитьте SQL дампы в Git** - они содержат чувствительные данные
2. Файлы `*.sql` уже добавлены в `.gitignore`
3. После импорта удалите временные файлы с сервера

### ⚠️ Миграции

- Скрипт экспорта включает схему БД (структуру таблиц)
- Убедитесь, что версии миграций совпадают:
  ```bash
  # Локально
  alembic current

  # На сервере (в логах Coolify или через exec)
  alembic current
  ```
- Если версии разные, сначала синхронизируйте миграции!

### 🔄 Альтернативный способ (только данные, без схемы)

Если хотите перенести ТОЛЬКО данные (без схемы):

```bash
# Экспорт только данных
pg_dump -h localhost -p 54329 -U budget_user -d it_budget_db \
  --no-owner --no-acl --data-only \
  -f data_only.sql

# Импорт
psql -h postgres_host -p 5432 -U budget_user -d it_budget_db \
  -f data_only.sql
```

Этот способ полезен если:
- На сервере уже применены все миграции
- Нужно только обновить данные

---

## Переменные окружения

Скрипты используют следующие переменные (с fallback на defaults):

### export_db.sh (локальная БД)
```bash
DB_HOST=localhost
DB_PORT=54329
DB_NAME=it_budget_db
DB_USER=budget_user
DB_PASS=budget_pass
```

### import_db.sh (удаленная БД)
```bash
DATABASE_HOST=your-postgres-host
DATABASE_PORT=5432
DATABASE_NAME=it_budget_db
DATABASE_USER=budget_user
DATABASE_PASSWORD=your-production-password
```

---

## Troubleshooting

### Ошибка: "relation already exists"

Значит таблица уже существует. Используйте опцию `--clean`:

```bash
pg_dump --clean --if-exists ...
```

### Ошибка: "permission denied"

Проверьте права пользователя БД:

```sql
GRANT ALL PRIVILEGES ON DATABASE it_budget_db TO budget_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO budget_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO budget_user;
```

### Ошибка: "password authentication failed"

Проверьте:
1. Правильность пароля
2. Настройки pg_hba.conf на сервере
3. Используйте переменную `PGPASSWORD` или файл `.pgpass`

---

## Автоматизация (опционально)

Для регулярных бэкапов можно добавить в cron:

```bash
# Ежедневный бэкап в 3:00 ночи
0 3 * * * cd /app/backend && ./scripts/export_db.sh >> /var/log/db_backup.log 2>&1
```

---

## Дополнительная информация

- [PostgreSQL Documentation: pg_dump](https://www.postgresql.org/docs/current/app-pgdump.html)
- [PostgreSQL Documentation: pg_restore](https://www.postgresql.org/docs/current/app-pgrestore.html)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
