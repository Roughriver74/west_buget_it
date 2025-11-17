# План интеграции AI-обработки счетов в IT Budget Manager

## 📋 Обзор

Интеграция функционала автоматической обработки счетов на оплату из проекта `ai_1c_zayavki` в основной проект IT Budget Manager.

### Что интегрируем:
- 🔍 OCR распознавание текста из PDF/изображений (Tesseract)
- 🤖 AI-парсинг данных через VseGPT API
- 📄 Автоматическое создание заявок на расходование из счетов
- 🔗 Опциональная интеграция с 1С:УТ

## 🎯 Стратегия интеграции

**Выбранный подход**: **Полная интеграция** в основной проект

**Обоснование**:
- ✅ Единая система аутентификации (JWT)
- ✅ Поддержка multi-tenancy (department_id)
- ✅ Унифицированная база данных
- ✅ Общие справочники (контрагенты, категории)
- ✅ Проще управлять и деплоить
- ✅ Единый frontend

## 📦 Архитектурная адаптация

### 1. База данных
Новые таблицы с обязательным `department_id`:

```python
class ProcessedInvoice(Base):
    """История обработанных счетов"""
    __tablename__ = "processed_invoices"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False, index=True)

    # Метаданные файла
    original_filename = Column(String(255))
    file_path = Column(String(500))
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # OCR результаты
    ocr_text = Column(Text)
    ocr_confidence = Column(Float)

    # Распознанные данные
    invoice_number = Column(String(100), index=True)
    invoice_date = Column(Date)
    supplier_name = Column(String(500))
    supplier_inn = Column(String(12), index=True)
    total_amount = Column(Numeric(15, 2))

    # Статус обработки
    status = Column(String(50), default="pending")  # pending, processed, error, manual_review

    # Связь с созданным расходом
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=True)
    contractor_id = Column(Integer, ForeignKey("contractors.id"), nullable=True)

    # AI данные (полный JSON)
    parsed_data = Column(JSON)

    # Ошибки и предупреждения
    errors = Column(JSON)
    warnings = Column(JSON)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    department_rel = relationship("Department")
    uploaded_by_rel = relationship("User")
    expense_rel = relationship("Expense")
    contractor_rel = relationship("Contractor")
```

### 2. API Endpoints

Новые endpoints в `backend/app/api/v1/invoice_processing.py`:

```python
# POST /api/v1/invoice-processing/upload
# - Загрузка файла счета
# - Требует JWT auth
# - Автоматически привязывается к department_id текущего пользователя

# POST /api/v1/invoice-processing/process/{id}
# - Запуск обработки загруженного файла
# - OCR + AI парсинг

# POST /api/v1/invoice-processing/create-expense/{id}
# - Создание expense из распознанного счета
# - Автоматический поиск/создание контрагента

# GET /api/v1/invoice-processing/
# - Список обработанных счетов
# - Фильтрация по department_id (role-based)

# GET /api/v1/invoice-processing/{id}
# - Детали обработанного счета

# PUT /api/v1/invoice-processing/{id}
# - Ручная корректировка распознанных данных

# DELETE /api/v1/invoice-processing/{id}
# - Удаление записи (soft delete)
```

### 3. Сервисы

Адаптированные сервисы:

```
backend/app/services/
├── invoice_ocr.py          # OCR Service (Tesseract)
├── invoice_ai_parser.py    # AI Parser (VseGPT)
├── invoice_processor.py    # Orchestrator для всего процесса
└── invoice_xml_generator.py  # XML для 1С (опционально)
```

### 4. Frontend

Новая страница: `frontend/src/pages/InvoiceProcessingPage.tsx`

**Функционал**:
- 📤 Drag & drop загрузка PDF/изображений
- 🔍 Просмотр OCR результатов
- ✏️ Редактирование распознанных данных
- ✅ Одобрение и создание expense
- 📊 История обработанных счетов
- 🔍 Поиск по номеру счета, ИНН, дате

## 🔧 Технические детали

### Зависимости

Добавить в `backend/requirements.txt`:
```
# OCR и обработка изображений
pytesseract==0.3.13
pdf2image==1.17.0
Pillow==11.0.0
pypdf==5.1.0

# AI для парсинга (VseGPT через OpenAI API)
openai==1.54.0
```

### Системные зависимости (Docker)

Обновить `backend/Dockerfile`:
```dockerfile
# Добавить установку Tesseract и Poppler
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

### Environment Variables

Добавить в `backend/.env`:
```env
# AI API для обработки счетов
VSEGPT_API_KEY=sk-or-vv-...
VSEGPT_BASE_URL=https://api.vsegpt.ru/v1
VSEGPT_MODEL=vis-openai/gpt-5-mini

# 1С интеграция (опционально)
C1_BASE_URL=http://your-1c-server:8080/your-base
C1_USERNAME=api_user
C1_PASSWORD=api_password
C1_ENABLED=false

# Настройки OCR
OCR_LANGUAGE=rus+eng
OCR_DPI=300
```

## 📋 Пошаговый план реализации

### Phase 1: Backend Infrastructure (2-3 дня)

1. **Database Models & Migrations**
   - [ ] Создать модель `ProcessedInvoice` в `backend/app/db/models.py`
   - [ ] Создать миграцию Alembic
   - [ ] Применить миграцию

2. **Pydantic Schemas**
   - [ ] Создать schemas в `backend/app/schemas/invoice_processing.py`
   - [ ] Схемы для: Upload, ParsedInvoice, InvoiceResponse

3. **Services**
   - [ ] Портировать `OCRService` из ai_1c_zayavki
   - [ ] Портировать `AIParser` с адаптацией под VseGPT
   - [ ] Создать `InvoiceProcessor` - оркестратор процесса
   - [ ] Добавить логику создания expense из распознанных данных

4. **API Endpoints**
   - [ ] Создать `backend/app/api/v1/invoice_processing.py`
   - [ ] Реализовать все endpoints с JWT auth
   - [ ] Добавить role-based фильтрацию по department_id

### Phase 2: Frontend (2-3 дня)

1. **API Client**
   - [ ] Добавить functions в `frontend/src/api/invoiceProcessing.ts`

2. **Components**
   - [ ] `InvoiceUploader` - drag & drop загрузка
   - [ ] `InvoicePreview` - предпросмотр файла
   - [ ] `ParsedDataEditor` - редактирование распознанных данных
   - [ ] `InvoiceHistoryTable` - таблица истории

3. **Page**
   - [ ] Создать `InvoiceProcessingPage.tsx`
   - [ ] Интеграция с DepartmentContext
   - [ ] React Query для data fetching

4. **Navigation**
   - [ ] Добавить раздел в меню (только для USER/MANAGER/ADMIN)
   - [ ] Обновить `AppLayout.tsx`

### Phase 3: Integration & Testing (1-2 дня)

1. **Integration**
   - [ ] Связать с существующими Contractors
   - [ ] Автоматический поиск контрагента по ИНН
   - [ ] Создание нового контрагента если не найден
   - [ ] Создание expense с привязкой к contractor

2. **Testing**
   - [ ] Тесты для OCR service
   - [ ] Тесты для AI parser
   - [ ] Тесты для API endpoints
   - [ ] E2E тесты для процесса

3. **Documentation**
   - [ ] Обновить CLAUDE.md
   - [ ] Добавить инструкцию по использованию
   - [ ] Документировать API endpoints

### Phase 4: Docker & Deployment (1 день)

1. **Docker**
   - [ ] Обновить Dockerfile с Tesseract
   - [ ] Обновить docker-compose.yml
   - [ ] Тестировать локально в Docker

2. **Docker**
   - [ ] Обновить build configuration
   - [ ] Добавить env variables
   - [ ] Деплой на production

## 🔐 Security & Permissions

### Role-Based Access

- **USER**:
  - ✅ Может загружать счета для своего отдела
  - ✅ Видит только счета своего отдела
  - ✅ Может создавать expenses из счетов

- **MANAGER/ADMIN**:
  - ✅ Может загружать счета для любого отдела
  - ✅ Видит все счета (с фильтрацией по отделам)
  - ✅ Может редактировать/удалять

- **ACCOUNTANT**:
  - ❌ Нет доступа (не работает с expenses)

### Data Isolation

Все запросы **ОБЯЗАТЕЛЬНО** фильтруются по `department_id`:
```python
@router.get("/")
def get_invoices(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(ProcessedInvoice)

    if current_user.role == UserRoleEnum.USER:
        query = query.filter(ProcessedInvoice.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(ProcessedInvoice.department_id == department_id)

    return query.all()
```

## 🎨 UI/UX Design

### Основная страница

```
┌─────────────────────────────────────────────────────────┐
│ Обработка счетов AI                                     │
├─────────────────────────────────────────────────────────┤
│ [Department Filter ▼]  [Status Filter ▼]  [+ Загрузить]│
├─────────────────────────────────────────────────────────┤
│                                                          │
│  📤 Перетащите файл сюда или нажмите для загрузки      │
│     Поддерживаются: PDF, JPG, PNG                       │
│                                                          │
├─────────────────────────────────────────────────────────┤
│ История обработанных счетов                             │
├──────┬──────────┬────────────┬─────────────┬──────────┤
│ Дата │ Счет №   │ Поставщик  │ Сумма       │ Статус   │
├──────┼──────────┼────────────┼─────────────┼──────────┤
│ 05.11│ 2635     │ ООО ТРАСТ  │ 2,000 ₽     │ ✅ Созд. │
│ 04.11│ 1842     │ ООО Рога   │ 15,000 ₽    │ 🔍 Ожид. │
│ 03.11│ 9921     │ АО Копыта  │ 50,000 ₽    │ ⚠️ Ошибка│
└──────┴──────────┴────────────┴─────────────┴──────────┘
```

### Модальное окно обработки

```
┌─────────────────────────────────────────────────────────┐
│ Обработка счета: invoice_2635.pdf                    [×]│
├─────────────────────────────────────────────────────────┤
│ Шаг 1/3: OCR распознавание...                ⏳ 3 сек  │
│ Шаг 2/3: AI-парсинг данных...                ⏳ 5 сек  │
│ Шаг 3/3: Создание записи...                  ✅        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Распознанные данные:                                    │
│                                                          │
│ Номер счета:    [2635________________]                  │
│ Дата:           [31.10.2025__________]                  │
│ Поставщик:      [ООО ТРАСТ ТЕЛЕКОМ___] 🔍              │
│ ИНН:            [7734640247__________]                  │
│ Сумма:          [2,000.00 ₽__________]                  │
│                                                          │
│ [❌ Отменить]  [✏️ Редактировать]  [✅ Создать расход] │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Workflow

### Автоматический процесс

```
1. Пользователь загружает PDF/фото счета
   ↓
2. OCR извлекает текст (Tesseract)
   ↓
3. AI парсит структурированные данные (VseGPT)
   ↓
4. Система ищет контрагента по ИНН
   ↓
5. Показывается preview распознанных данных
   ↓
6. Пользователь проверяет/редактирует
   ↓
7. Создается Expense с attachment
   ↓
8. ✅ Готово! Expense можно найти в разделе "Расходы"
```

## 📊 Метрики и мониторинг

### Логирование
- Время OCR обработки
- Время AI парсинга
- Успешность распознавания
- Частые ошибки

### Алерты
- Превышение времени обработки
- Ошибки AI API
- Низкая confidence OCR

## 💰 Стоимость

### VseGPT API
- Модель: `gpt-5-mini`
- ~0.5-1₽ за счет
- Бюджет: ~100-200₽/месяц на 200-400 счетов

### Инфраструктура
- Tesseract: бесплатно (open source)
- Хранилище файлов: ~1GB на 1000 PDF
- CPU: +10-15% нагрузка при обработке

## ❓ FAQ

**Q: Какие форматы поддерживаются?**
A: PDF, JPG, PNG, TIFF, BMP

**Q: Нужна ли интеграция с 1С?**
A: Нет, это опциональная функция. Можно использовать только для создания expenses в IT Budget Manager.

**Q: Насколько точно распознавание?**
A: OCR: 85-95%, AI парсинг: 90-98% для стандартных форматов счетов.

**Q: Можно ли отключить AI и парсить вручную?**
A: Да, можно загрузить файл без обработки и ввести данные вручную.

**Q: Где хранятся файлы?**
A: В `backend/uploads/invoices/{department_id}/{year}/{filename}` или в S3-совместимом хранилище.

## 📚 Ссылки

- [AI 1C Zayavki README](../ai_1c_zayavki/1c_zayavki/README.md)
- [VseGPT API Docs](https://vsegpt.ru/docs)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [FastAPI File Upload](https://fastapi.tiangolo.com/tutorial/request-files/)

---

**Статус**: 🟡 План готов, ожидается реализация
**Приоритет**: Средний
**Оценка времени**: 6-9 дней разработки
**Команда**: 1 fullstack разработчик
