# Исправление ошибки OCR/PDF обработки в Production

## Проблема

При обработке PDF файлов на production сервере возникала ошибка:
```
processing: Критическая ошибка: Unable to get page count. Is poppler installed and in PATH?
```

## Причина

В production Dockerfile ([backend/Dockerfile.prod](../backend/Dockerfile.prod)) отсутствовали необходимые системные зависимости для работы с OCR и PDF:
- `tesseract-ocr` - движок для распознавания текста (OCR)
- `tesseract-ocr-rus` - русский языковой пакет для Tesseract
- `tesseract-ocr-eng` - английский языковой пакет для Tesseract
- `poppler-utils` - утилиты для работы с PDF (требуется для pdf2image)

Эти зависимости были установлены в development версии (`backend/Dockerfile`), но забыли добавить в production версию.

## Решение

### 1. Обновлен Dockerfile.prod

Добавлены недостающие системные зависимости в секцию runtime dependencies:

```dockerfile
# Install runtime dependencies including OCR and PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq5 \
    curl \
    cron \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

### 2. Используемые Python библиотеки

Проект использует следующие библиотеки для работы с PDF и OCR (см. [requirements.txt](../backend/requirements.txt)):

```
pytesseract==0.3.13    # Python обертка для Tesseract OCR
pdf2image==1.17.0      # Конвертация PDF в изображения (требует poppler)
pypdf==5.1.0           # Работа с PDF (извлечение текста)
Pillow==11.0.0         # Обработка изображений
```

### 3. Как работает OCR система

См. [backend/app/services/invoice_ocr.py](../backend/app/services/invoice_ocr.py):

1. **Сначала пытается извлечь текстовый слой** из PDF напрямую (быстро, без OCR)
2. **Проверяет качество текста** - если кириллицы меньше 10%, возможна проблема с кодировкой
3. **Если текста нет или некачественный** - использует OCR:
   - Конвертирует PDF в изображения (используя `pdf2image` → требует `poppler-utils`)
   - Распознает текст на изображениях (используя `pytesseract` → требует `tesseract-ocr`)

## Инструкции по деплою

### Вариант A: Coolify (Рекомендуется)

#### Шаг 1: Закоммитьте изменения

```bash
git add backend/Dockerfile.prod
git commit -m "fix: add OCR dependencies (tesseract, poppler-utils) to production Dockerfile"
git push origin main
```

#### Шаг 2: Rebuild в Coolify

1. Откройте Coolify веб-интерфейс: https://west-it.ru
2. Перейдите в Backend приложение
3. Нажмите **"Rebuild"** (важно: НЕ "Restart"!)
4. Дождитесь завершения сборки (займет 3-5 минут)
5. Проверьте логи на наличие ошибок

#### Шаг 3: Проверьте установку зависимостей

На сервере запустите:

```bash
ssh root@93.189.228.52
cd /path/to/project
./check_ocr_deps.sh
```

Скрипт проверит наличие всех необходимых зависимостей.

**Ожидаемый результат:**
```
✅ poppler-utils установлен: pdfinfo version 22.02.0
✅ tesseract-ocr установлен: tesseract 5.3.0
✅ Русский язык (rus) установлен
✅ Английский язык (eng) установлен
```

#### Шаг 4: Тестирование

Попробуйте загрузить PDF файл для обработки:

```bash
# Проверьте endpoint
curl -X POST "https://api.budget-west.shknv.ru/api/v1/invoice-processing/process" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_invoice.pdf"
```

### Вариант B: Ручной деплой через Docker Compose

Если не используете Coolify:

```bash
ssh root@93.189.228.52
cd /path/to/project

# Pull latest changes
git pull origin main

# Rebuild backend image
docker-compose -f docker-compose.prod.yml build backend

# Restart backend service
docker-compose -f docker-compose.prod.yml up -d backend

# Check logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Вариант C: Локальная проверка перед деплоем

Проверьте что изменения работают локально:

```bash
# Build production image
cd backend
docker build -f Dockerfile.prod -t it-budget-backend:test .

# Run container
docker run --rm -it it-budget-backend:test bash

# Inside container, check dependencies
which pdfinfo          # Should return: /usr/bin/pdfinfo
which tesseract        # Should return: /usr/bin/tesseract
tesseract --list-langs # Should show: eng, rus
pdfinfo -v            # Should show version info
```

## Проверка работы

### 1. Проверка через Web UI

1. Откройте https://budget-west.shknv.ru
2. Перейдите в раздел **"Обработка счетов"** или **"Invoice Processing"**
3. Загрузите тестовый PDF файл
4. Убедитесь что обработка проходит без ошибок

### 2. Проверка через API

```bash
# Get auth token
TOKEN=$(curl -X POST "https://api.budget-west.shknv.ru/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' | jq -r '.access_token')

# Upload and process PDF
curl -X POST "https://api.budget-west.shknv.ru/api/v1/invoice-processing/process" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.pdf" \
  -F "use_ai=true"
```

### 3. Проверка логов

```bash
# На сервере
ssh root@93.189.228.52

# Посмотреть логи backend
docker logs it_budget_backend_prod -f --tail 100

# Искать ошибки OCR
docker logs it_budget_backend_prod 2>&1 | grep -i "ocr\|pdf\|poppler\|tesseract"
```

## Возможные проблемы

### Проблема: "tesseract: command not found"

**Причина**: tesseract-ocr не установлен в контейнере

**Решение**:
1. Проверьте что Dockerfile.prod содержит `tesseract-ocr`
2. Пересоберите образ: `docker-compose build backend`
3. Проверьте в контейнере: `docker exec backend which tesseract`

### Проблема: "Unable to get page count"

**Причина**: poppler-utils не установлен

**Решение**:
1. Проверьте что Dockerfile.prod содержит `poppler-utils`
2. Пересоберите образ
3. Проверьте в контейнере: `docker exec backend which pdfinfo`

### Проблема: OCR не распознает русский текст

**Причина**: отсутствует языковой пакет `tesseract-ocr-rus`

**Решение**:
1. Убедитесь что `tesseract-ocr-rus` в Dockerfile.prod
2. Пересоберите образ
3. Проверьте языки: `docker exec backend tesseract --list-langs`
4. Должно быть в списке: `rus`

### Проблема: Ошибка "Unable to find sRGB profile"

**Причина**: отсутствует color profile для Pillow/Tesseract

**Решение**: Добавить в Dockerfile.prod:
```dockerfile
RUN apt-get install -y --no-install-recommends \
    ...
    liblcms2-2 \
    ...
```

## Конфигурация OCR

Настройки OCR находятся в [backend/app/core/config.py](../backend/app/core/config.py):

```python
class Settings(BaseSettings):
    # OCR Settings
    OCR_LANGUAGE: str = "rus+eng"  # Языки для распознавания
    OCR_DPI: int = 300             # Разрешение для конвертации PDF
```

**Изменение настроек через environment variables:**

```bash
# В Coolify или docker-compose.prod.yml
OCR_LANGUAGE=rus+eng  # Русский и английский
OCR_DPI=300          # Высокое качество (медленно но точно)
# или
OCR_DPI=200          # Среднее качество (быстрее)
```

## Оптимизация производительности

### Кэширование OCR результатов

Рассмотрите кэширование результатов OCR для одинаковых файлов:

```python
# В invoice_ocr.py добавить кэш (пример)
from functools import lru_cache
import hashlib

def get_file_hash(file_path: Path) -> str:
    """Вычисление хеша файла для кэширования"""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()
```

### Асинхронная обработка

Для больших файлов используйте фоновые задачи:

```python
# Пример с Celery или FastAPI BackgroundTasks
from fastapi import BackgroundTasks

@router.post("/process-async")
def process_invoice_async(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    ...
):
    background_tasks.add_task(process_invoice_in_background, file)
    return {"status": "processing", "task_id": task_id}
```

## Дополнительные ресурсы

- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **pdf2image**: https://github.com/Belval/pdf2image
- **pytesseract**: https://github.com/madmaze/pytesseract
- **Poppler**: https://poppler.freedesktop.org/

## История изменений

- **2025-11-06**: Добавлены OCR зависимости в production Dockerfile
- **Проблема**: Missing poppler-utils and tesseract in production
- **Решение**: Updated Dockerfile.prod to include all OCR dependencies
- **Статус**: ✅ Исправлено

## Контакты

При возникновении проблем:
1. Проверьте логи backend: `docker logs it_budget_backend_prod`
2. Запустите проверочный скрипт: `./check_ocr_deps.sh`
3. Создайте issue в GitHub репозитории
