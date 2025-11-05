# Исправление ошибки экспорта прогноза (Missing Excel Templates)

## Проблема

При попытке экспорта прогноза в Excel возникает ошибка 500:

```
FileNotFoundError: Шаблон не найден: /xls/Планирование_10.2025-3.xlsx
```

**Причина**: Директория `/xls` с Excel-шаблонами не копируется в Docker-контейнер при сборке.

## Решение для Coolify

### Вариант 1: Использование нового Dockerfile с правильным build context (Рекомендуется) ⭐

1. **Новый Dockerfile создан**: `Dockerfile.backend.prod` в корне проекта
   - Использует корень репозитория как build context
   - Копирует `backend/` → `/app`
   - Копирует `xls/` → `/xls`

2. **В Coolify обновите настройки Backend сервиса**:

   a. Перейдите в **Build Settings**

   b. Измените **Dockerfile Location**:
   ```
   Dockerfile.backend.prod
   ```

   c. Убедитесь что **Build Context** = `.` (корень репозитория)

   d. Сохраните изменения

3. **Rebuild Backend**:
   ```bash
   # В Coolify нажмите "Force Rebuild Without Cache"
   ```

4. **Проверка**:
   ```bash
   # SSH на сервер
   ssh root@93.189.228.52

   # Проверить что /xls существует в контейнере
   docker exec <backend_container_id> ls -la /xls

   # Должно показать:
   # -rw-r--r-- 1 appuser appuser 2930081 Oct 26 22:11 Планирование_10.2025-3.xlsx
   # ... другие файлы
   ```

5. **Тест экспорта**:
   - Откройте https://budget-west.shknv.ru
   - Перейдите в раздел "Прогнозы"
   - Нажмите "Экспорт в Excel"
   - Файл должен скачаться без ошибок

---

### Вариант 2: Копирование xls в backend директорию (Альтернатива)

Если вариант 1 не работает или Coolify не позволяет изменить build context:

1. **Скопируйте xls в backend**:
   ```bash
   # На локальной машине
   cp -r xls backend/xls
   ```

2. **Обновите backend/Dockerfile.prod**:
   ```dockerfile
   # После копирования application code, добавьте:

   # Copy Excel templates to container root
   COPY --chown=appuser:appuser xls /xls
   ```

3. **Обновите .gitignore** (если нужно):
   ```
   # НЕ игнорировать xls в backend
   !backend/xls/
   ```

4. **Commit и Push**:
   ```bash
   git add backend/xls
   git add backend/Dockerfile.prod
   git commit -m "fix: add xls templates to backend for Coolify deployment"
   git push
   ```

5. **Rebuild в Coolify**

---

### Вариант 3: Volume mount (Временное решение для тестирования)

1. **SSH на сервер**:
   ```bash
   ssh root@93.189.228.52
   ```

2. **Создать /xls директорию на хосте**:
   ```bash
   mkdir -p /opt/it-budget/xls
   ```

3. **Скопировать файлы с локальной машины**:
   ```bash
   # На локальной машине
   scp -r xls/* root@93.189.228.52:/opt/it-budget/xls/
   ```

4. **В Coolify добавить Volume**:
   - Перейдите в Backend → **Storage**
   - Добавьте новый volume:
     - **Source (Host)**: `/opt/it-budget/xls`
     - **Destination (Container)**: `/xls`
   - Restart backend

⚠️ **Примечание**: Этот вариант требует ручного управления файлами на сервере при обновлениях шаблонов.

---

## Структура файлов после исправления

```
/
├── backend/
│   ├── app/
│   ├── Dockerfile.prod        # Старый (для docker-compose)
│   └── requirements.txt
├── xls/                        # Excel templates
│   ├── Планирование_10.2025-3.xlsx
│   └── ...другие шаблоны
└── Dockerfile.backend.prod     # Новый (для Coolify) ⭐
```

## Проверка работы

### 1. Проверить наличие шаблонов в контейнере

```bash
ssh root@93.189.228.52
docker exec <backend_container_id> ls -la /xls
```

Ожидаемый вывод:
```
total 9792
-rw-r--r-- 1 appuser appuser 2930081 Oct 26 22:11 Планирование_10.2025-3.xlsx
-rw-r--r-- 1 appuser appuser  116480 Nov  1 16:31 Бюджет ЗП склад 2025_3.xlsx
...
```

### 2. Проверить endpoint прогноза

```bash
# Получить JWT token
TOKEN="your-jwt-token"

# Тест экспорта прогноза
curl -X GET "https://api.budget-west.shknv.ru/api/v1/forecast/export/2025/12?department_id=2" \
  -H "Authorization: Bearer $TOKEN" \
  -o forecast_test.xlsx

# Проверить что файл скачался
file forecast_test.xlsx
# Должно быть: forecast_test.xlsx: Microsoft Excel 2007+
```

### 3. Проверить логи

```bash
docker logs <backend_container_id> --tail 100 | grep -i "template\|xls\|forecast"
```

Не должно быть ошибок `FileNotFoundError`.

## Важные замечания

1. **Build Context в Coolify**:
   - Coolify по умолчанию использует корень репозитория как build context
   - Поэтому `Dockerfile.backend.prod` в корне проекта работает корректно

2. **Шаблоны Excel**:
   - Находятся в `/xls` в корне контейнера
   - Используются для экспорта прогнозов с форматированием
   - При обновлении шаблонов нужно rebuild контейнера

3. **После исправления**:
   - CORS ошибка исчезнет (она была следствием 500 ошибки)
   - Экспорт прогнозов будет работать
   - Все другие функции работают как обычно

## Rollback (если что-то пошло не так)

1. **Вернуть старый Dockerfile**:
   ```bash
   # В Coolify изменить Dockerfile Location обратно на:
   backend/Dockerfile.prod
   ```

2. **Rebuild**

3. **Использовать Вариант 3 (volume mount)** как временное решение

## Дополнительная информация

- [Coolify Setup Guide](COOLIFY_SETUP.md)
- [Coolify Fix Guide](COOLIFY_FIX.md)
- [Auto Proxy Restart](AUTO_PROXY_RESTART.md)
