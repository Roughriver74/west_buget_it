# 🚀 Быстрый деплой исправления OCR/PDF

## Что исправлено?

✅ Добавлены зависимости для обработки PDF и OCR в production:
- `poppler-utils` - для конвертации PDF в изображения
- `tesseract-ocr` - для распознавания текста
- Русский и английский языковые пакеты

## Деплой на Coolify (3 шага)

### 1️⃣ Откройте Coolify
```
https://budget-west.shknv.ru
```

### 2️⃣ Rebuild Backend
1. Перейдите в проект **"IT Budget Manager"**
2. Откройте приложение **Backend**
3. Нажмите кнопку **"Rebuild"** (НЕ "Restart"!)
4. Дождитесь окончания сборки (3-5 минут)

### 3️⃣ Проверьте работу
После успешного rebuild:

```bash
# Подключитесь к серверу
ssh root@93.189.228.52

# Проверьте зависимости (опционально)
cd /root/west_buget_it  # или ваш путь к проекту
./check_ocr_deps.sh
```

**Ожидаемый результат:**
```
✅ poppler-utils установлен: pdfinfo version 22.02.0
✅ tesseract-ocr установлен: tesseract 5.3.0
✅ Русский язык (rus) установлен
✅ Английский язык (eng) установлен
```

## Альтернатива: Ручной деплой через SSH

Если не используете Coolify:

```bash
# Подключитесь к серверу
ssh root@93.189.228.52

# Перейдите в директорию проекта
cd /path/to/west_buget_it

# Обновите код
git pull origin main

# Rebuild backend образ
docker-compose -f docker-compose.prod.yml build backend

# Перезапустите backend
docker-compose -f docker-compose.prod.yml up -d backend

# Проверьте логи
docker-compose -f docker-compose.prod.yml logs -f backend
```

## Проверка работы

### Способ 1: Через Web UI

1. Откройте https://budget-west.shknv.ru
2. Перейдите в раздел "Обработка счетов"
3. Загрузите тестовый PDF файл
4. Убедитесь что обработка проходит без ошибок

### Способ 2: Через API

```bash
# Get token
TOKEN=$(curl -X POST "https://api.budget-west.shknv.ru/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' | jq -r '.access_token')

# Test PDF processing
curl -X POST "https://api.budget-west.shknv.ru/api/v1/invoice-processing/process" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_invoice.pdf" \
  -F "use_ai=true"
```

### Способ 3: Проверка в контейнере

```bash
# Найдите имя backend контейнера
docker ps | grep backend

# Проверьте установку poppler
docker exec <backend_container_name> which pdfinfo
# Должно вернуть: /usr/bin/pdfinfo

# Проверьте установку tesseract
docker exec <backend_container_name> tesseract --version
# Должно показать версию tesseract

# Проверьте языки
docker exec <backend_container_name> tesseract --list-langs
# Должно показать: eng, rus
```

## Возможные проблемы

### ❌ Проблема: "Still getting the same error after rebuild"

**Решение:**
1. Убедитесь что вы нажали **"Rebuild"**, а не "Restart"
2. Проверьте что используется правильный Dockerfile:
   ```bash
   # На сервере
   docker inspect <backend_container> | grep -i dockerfile
   # Должно быть: Dockerfile.prod
   ```
3. Удалите старый образ и пересоберите:
   ```bash
   docker rmi it-budget-backend:prod
   docker-compose -f docker-compose.prod.yml build --no-cache backend
   ```

### ❌ Проблема: "Coolify not using updated Dockerfile"

**Решение:**
Coolify кэширует слои Docker. Принудительно пересоберите:
1. В Coolify откройте Backend settings
2. Найдите опцию **"Build Options"** или **"Advanced"**
3. Включите **"No Cache"** или **"Force Rebuild"**
4. Нажмите **"Rebuild"**

### ❌ Проблема: "Cannot find check_ocr_deps.sh"

**Решение:**
```bash
# На сервере
cd /path/to/project
git pull origin main  # Убедитесь что код обновлен
chmod +x check_ocr_deps.sh
./check_ocr_deps.sh
```

## Дополнительная документация

📖 Полная документация: [docs/OCR_PDF_FIX.md](docs/OCR_PDF_FIX.md)

Включает:
- Подробное объяснение проблемы
- Техническую документацию
- Расширенные инструкции по отладке
- Конфигурацию OCR
- Оптимизацию производительности

## Поддержка

Если проблемы продолжаются:

1. **Проверьте логи backend:**
   ```bash
   docker logs <backend_container> -f --tail 100
   ```

2. **Проверьте логи Coolify:**
   - В веб-интерфейсе: Logs → Backend

3. **Создайте issue в GitHub:**
   - https://github.com/Roughriver74/west_buget_it/issues

---

✅ **Коммит:** 1df11be
📅 **Дата:** 2025-11-06
🤖 **Сгенерировано с помощью Claude Code**
