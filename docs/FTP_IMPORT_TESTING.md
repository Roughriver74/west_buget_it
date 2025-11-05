# Тестирование исправления обновления статуса FTP импорта

## Что было исправлено

При повторной загрузке заявок из FTP теперь обновляются критические поля:
- ✅ `status` - статус заявки
- ✅ `is_paid` / `is_closed` - флаги оплаты/закрытия
- ✅ `amount` - сумма
- ✅ `payment_date` - дата оплаты
- ✅ `comment` - комментарий

## Сценарии тестирования

### Сценарий 1: Обновление статуса существующей заявки

1. **Первый импорт** - создание заявки:
   ```bash
   # Через веб-интерфейс или API
   POST /api/v1/expenses/import/ftp
   {
     "remote_path": "/Zayavki na raszkhod(spisok) XLSX.xlsx",
     "skip_duplicates": true
   }
   ```

2. **Проверка**: Найти созданную заявку в системе, запомнить её статус

3. **Изменение в FTP**: Изменить статус заявки в Excel файле на FTP
   - Например: "К оплате" → "Оплачена"

4. **Повторный импорт**:
   ```bash
   POST /api/v1/expenses/import/ftp
   {
     "remote_path": "/Zayavki na raszkhod(spisok) XLSX.xlsx",
     "skip_duplicates": true
   }
   ```

5. **Ожидаемый результат**:
   - ✅ Статус заявки обновился на "Оплачена" (PAID)
   - ✅ `is_paid` = true
   - ✅ Счетчик `updated` увеличился на 1
   - ✅ Категория НЕ изменилась (если была назначена вручную)

### Сценарий 2: Проверка через cron задачу

1. **Запустить cron вручную**:
   ```bash
   cd backend
   python3 cron_ftp_import.py
   ```

2. **Проверить логи**:
   ```
   [2025-11-05 XX:XX:XX] Import completed successfully!
   [2025-11-05 XX:XX:XX]   Total in file: 150
   [2025-11-05 XX:XX:XX]   Created: 0
   [2025-11-05 XX:XX:XX]   Updated: 15    ← Должно быть > 0 если статусы изменились
   [2025-11-05 XX:XX:XX]   Skipped: 0
   ```

3. **Ожидаемый результат**:
   - ✅ Поле `Updated` показывает количество обновленных заявок
   - ✅ В базе статусы заявок соответствуют FTP файлу

### Сценарий 3: Проверка сохранения ручной категоризации

1. **Создать заявку через импорт** (category_id = null)

2. **Вручную назначить категорию** через веб-интерфейс

3. **Изменить статус в FTP** на "Оплачена"

4. **Повторный импорт**

5. **Ожидаемый результат**:
   - ✅ Статус обновился на "Оплачена"
   - ✅ Категория осталась той же (НЕ перезаписалась на null)
   - ✅ Сумма обновилась (если изменилась в FTP)

### Сценарий 4: Полное обновление (skip_duplicates=False)

1. **Запустить импорт с полным обновлением**:
   ```bash
   POST /api/v1/expenses/import/ftp
   {
     "remote_path": "/Zayavki na raszkhod(spisok) XLSX.xlsx",
     "skip_duplicates": false
   }
   ```

2. **Ожидаемый результат**:
   - ✅ Обновляются ВСЕ поля, включая category_id, contractor_id и т.д.
   - ✅ Ручная категоризация может быть перезаписана

## Проверка через SQL

```sql
-- Проверить обновленные заявки
SELECT
    number,
    status,
    is_paid,
    amount,
    payment_date,
    category_id,
    updated_at
FROM expenses
WHERE imported_from_ftp = true
ORDER BY updated_at DESC
LIMIT 20;
```

## Проверка логов backend

```bash
tail -f backend/logs/app.log | grep -i "import"
```

Искать строки:
- `Import completed: X created, Y updated, Z skipped`
- `Matched category '...' by keyword '...'`
- `Updated existing expense: ...`

## Критерии успешности

✅ **PASS** если:
1. При повторном импорте статусы обновляются
2. Счетчик `updated` корректно отражает количество обновленных заявок
3. Ручная категоризация сохраняется при `skip_duplicates=True`
4. Кэш baseline корректно инвалидируется

❌ **FAIL** если:
1. Статусы не обновляются при повторном импорте
2. Все заявки попадают в `skipped` вместо `updated`
3. Ручная категоризация перезаписывается при `skip_duplicates=True`
4. Возникают ошибки в логах при импорте

## Откат изменений (если необходимо)

Если тестирование выявит проблемы:

```bash
cd /Users/evgenijsikunov/projects/west/west_buget_it
git checkout backend/app/services/ftp_import_service.py
git checkout backend/app/api/v1/expenses.py
git checkout backend/cron_ftp_import.py
```

Затем перезапустить сервер:
```bash
./stop.sh
./run.sh
```
