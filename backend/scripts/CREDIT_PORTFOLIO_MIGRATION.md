# Миграция кредитного портфеля (legacy → финальная БД)

Этот документ описывает, как перенести данные кредитного портфеля из
старого проекта `acme-acme_fin` (PostgreSQL в docker-compose) в новую
схему `fin_*` текущего приложения.

## 1. Источник данных

- Legacy docker-compose поднимает PostgreSQL с параметрами:
  - `POSTGRES_USER=acme_user`
  - `POSTGRES_PASSWORD=acme_secure_password_2025`
  - `POSTGRES_DB=acme_fin_dwh`
  - Порт проброшен на `localhost:25432`
- Можно подключаться напрямую:
  ```bash
  docker compose -f /Users/evgenijsikunov/projects/acme/acme_buget_it/acme-acme_fin/docker-compose.yml \
    exec postgres psql -U acme_user -d acme_fin_dwh
  ```

## 2. Новый скрипт миграции

Создан `backend/scripts/migrate_credit_portfolio.py`, который:

- Подключается к legacy-базе через `LEGACY_DATABASE_URL`
- Использует текущую БД приложения (через `SessionLocal`)
- Копирует таблицы в строгом порядке, маппит ID и сохраняет связи:
  - `organizations → fin_organizations`
  - `bank_accounts → fin_bank_accounts`
  - `contracts → fin_contracts`
  - `receipts → fin_receipts`
  - `expenses → fin_expenses`
  - `expense_details → fin_expense_details`
  - `import_logs → fin_import_logs`
- Автоматически проставляет `department_id` (по умолчанию 8) и делает upsert
  по уникальным ключам, поэтому скрипт идемпотентен.

## 3. Переменные окружения

Перед запуском пропишите:

```bash
export LEGACY_DATABASE_URL="postgresql://acme_user:acme_secure_password_2025@localhost:25432/acme_fin_dwh"
export DATABASE_URL="postgresql://<current_app_user>:<pass>@<host>/<db>"
# либо используйте .env (скрипт берёт SessionLocal с текущих настроек)
```

## 4. Запуск локально

```bash
cd backend
poetry run python scripts/migrate_credit_portfolio.py \
  --department-id 8 \
  --log-level INFO
```

Ключи:

- `--legacy-url` — переопределить строку подключения (если не хотите export)
- `--department-id` — ID отдела, к которому относятся данные (по умолчанию 8)
- `--log-level` — уровень логов (`DEBUG/INFO/WARNING/ERROR`)

После выполнения в логах появится статистика `inserted/updated/skipped` по каждой таблице.

## 5. Запуск на сервере

1. Убедитесь, что legacy БД доступна серверу (порт проброшен или дамп восстановлен во временную БД)
2. Задайте `LEGACY_DATABASE_URL` уже на сервере
3. В контейнере backend выполните:
   ```bash
   cd /app
   poetry run python backend/scripts/migrate_credit_portfolio.py --department-id 8
   ```
4. После миграции проверьте данные:
   ```sql
   SELECT COUNT(*) FROM fin_organizations;
   SELECT COUNT(*) FROM fin_receipts;
   SELECT COUNT(*) FROM fin_expenses;
   ```

## 6. Повторные запуски

Скрипт безопасно обновляет существующие записи:

- `organizations/bank_accounts/contracts` ищутся по `name/account_number/contract_number + department_id`
- `receipts/expenses` — по `operation_id + department_id`
- `expense_details` — по `expense_operation_id + department_id + payment_type + settlement_account + payment_amount`
- `import_logs` — по `department_id + import_date + source_file + table_name`

Счётчик `skipped` показывает строки, которые не удалось сопоставить (например, если в legacy отсутствует организация). Такие случаи выносятся в WARN логи.

## 7. Резервные копии

Перед миграцией рекомендуется сделать бэкап текущей БД:

```bash
cd backend
./scripts/export_db.sh
```

И по завершении удалить/архивировать legacy-доступы, чтобы не держать открытые пароли.

