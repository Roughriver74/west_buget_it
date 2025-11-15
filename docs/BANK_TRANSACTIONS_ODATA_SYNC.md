# OData синхронизация банковских транзакций с 1С

## Описание

OData синхронизация позволяет автоматически загружать банковские операции (списания и поступления) из 1С в систему IT Budget Manager через протокол OData.

## Возможности

✅ **Автоматическая синхронизация** - получение данных из 1С по расписанию или по запросу  
✅ **Умное обновление** - создание новых транзакций и обновление существующих (по external_id_1c)  
✅ **Фильтрация по периоду** - выбор даты начала и окончания синхронизации  
✅ **Поддержка типов операций**:
- DEBIT (Списание) - расходные операции
- CREDIT (Поступление) - приходные операции

✅ **Тестирование подключения** - проверка соединения перед синхронизацией

## Требования

1. **Роль пользователя**: ADMIN или MANAGER
2. **Доступ к 1С OData**:
   - URL OData endpoint (например: `http://server:port/base/odata/standard.odata`)
   - Учетные данные пользователя 1С
3. **Выбранный отдел** в фильтрах (для MANAGER/ADMIN)

## Использование

### 1. Через веб-интерфейс

1. Откройте страницу **"Банковские операции"** (`/bank-transactions`)
2. Нажмите кнопку **"Синхронизация с 1С"** (зеленая кнопка)
3. Заполните форму:
   - **OData URL 1С**: адрес OData endpoint (например: `http://192.168.1.100:80/accounting/odata/standard.odata`)
   - **Имя пользователя**: логин пользователя 1С
   - **Пароль**: пароль пользователя 1С
   - **Имя сущности OData**: название документа в 1С (по умолчанию: `Document_BankStatement`)
   - **Период синхронизации**: выберите дату начала и окончания
4. (Опционально) Нажмите **"Проверить соединение"** для тестирования подключения
5. Нажмите **"Синхронизировать"**
6. Дождитесь завершения синхронизации

### 2. Через API

#### Тестирование подключения

```bash
curl -X POST "http://localhost:8000/api/v1/bank-transactions/odata/test-connection" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "odata_url": "http://server:port/base/odata/standard.odata",
    "username": "admin",
    "password": "password"
  }'
```

Ответ:
```json
{
  "success": true,
  "message": "Connection successful",
  "status_code": 200,
  "url": "http://server:port/base/odata/standard.odata/$metadata"
}
```

#### Синхронизация транзакций

```bash
curl -X POST "http://localhost:8000/api/v1/bank-transactions/odata/sync" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "odata_url": "http://server:port/base/odata/standard.odata",
    "username": "admin",
    "password": "password",
    "entity_name": "Document_BankStatement",
    "department_id": 1,
    "date_from": "2025-01-01",
    "date_to": "2025-01-31"
  }'
```

Ответ:
```json
{
  "success": true,
  "total_fetched": 150,
  "created": 120,
  "updated": 30,
  "skipped": 0,
  "errors": []
}
```

## Структура данных из 1С

Сервис ожидает следующую структуру данных из 1С OData:

```json
{
  "Ref_Key": "guid-string",
  "Date": "2025-01-15T00:00:00",
  "Number": "000001",
  "Amount": 150000.00,
  "OperationType": "Списание",
  "Counterparty": "ООО Поставщик",
  "CounterpartyINN": "7727563778",
  "CounterpartyKPP": "772701001",
  "CounterpartyAccount": "40702810100000000001",
  "CounterpartyBank": "ПАО Сбербанк",
  "CounterpartyBIK": "044525225",
  "PaymentPurpose": "Оплата по договору №123 от 01.01.2025",
  "Organization_Key": "guid-string",
  "Account": "40702810100000000002"
}
```

### Поддерживаемые поля

| Поле 1С | Поле БД | Описание |
|---------|---------|----------|
| Ref_Key / Number | external_id_1c | Уникальный ID (для обновления) |
| Date | transaction_date | Дата операции |
| Amount | amount | Сумма |
| OperationType | transaction_type | Тип: "Списание" → DEBIT, "Поступление" → CREDIT |
| Counterparty | counterparty_name | Контрагент |
| CounterpartyINN | counterparty_inn | ИНН контрагента |
| CounterpartyKPP | counterparty_kpp | КПП контрагента |
| CounterpartyAccount | counterparty_account | Счет контрагента |
| CounterpartyBank | counterparty_bank | Банк контрагента |
| CounterpartyBIK | counterparty_bik | БИК банка |
| PaymentPurpose | payment_purpose | Назначение платежа |
| Account | account_number | Наш счет |

## Логика работы

1. **Получение данных** - запрос к OData endpoint 1С с фильтрами по дате
2. **Парсинг** - преобразование данных из формата 1С в формат БД
3. **Проверка дубликатов** - поиск существующих транзакций по `external_id_1c`
4. **Создание/Обновление**:
   - Если `external_id_1c` найден → обновление существующей транзакции
   - Если не найден → создание новой транзакции
5. **Установка статуса** - все новые транзакции получают статус `NEW`
6. **Коммит** - сохранение изменений в БД каждые 100 записей

## Настройка 1С

### 1. Включение OData

В 1С необходимо:
1. Открыть конфигурацию
2. Перейти в **"Основное" → "OData"**
3. Включить публикацию через OData
4. Создать или настроить публикацию **"standard.odata"**
5. Добавить документ **"БанковскаяВыписка"** (или аналогичный) в публикацию

### 2. Права доступа

Убедитесь, что пользователь имеет права:
- Чтение документов "БанковскаяВыписка"
- Доступ к OData интерфейсу

### 3. Проверка доступности

Откройте в браузере:
```
http://server:port/base/odata/standard.odata/$metadata
```

Если появляется XML с метаданными → OData настроен корректно.

## Troubleshooting

### Ошибка "Connection failed"

**Причины:**
- Неверный URL OData
- 1С не доступен по сети
- OData не включен в 1С
- Firewall блокирует доступ

**Решение:**
1. Проверьте доступность 1С: `ping server`
2. Проверьте порт: `telnet server port`
3. Откройте URL в браузере: `http://server:port/base/odata/standard.odata/$metadata`
4. Проверьте настройки firewall

### Ошибка "401 Unauthorized"

**Причины:**
- Неверные учетные данные
- Пользователь заблокирован в 1С
- Нет прав на OData

**Решение:**
1. Проверьте логин/пароль
2. Проверьте статус пользователя в 1С
3. Проверьте права доступа к OData

### Ошибка "404 Not Found"

**Причины:**
- Неверное имя сущности (`entity_name`)
- Документ не опубликован через OData

**Решение:**
1. Проверьте список доступных сущностей в `$metadata`
2. Убедитесь что документ добавлен в публикацию OData

### Транзакции дублируются

**Причина:** Поле `external_id_1c` не уникально

**Решение:**
1. Проверьте, что в 1С используется `Ref_Key` (GUID)
2. Если используется `Number`, убедитесь что номера уникальны

## Производительность

- **Рекомендуемый размер пакета**: до 1000 транзакций за раз
- **Частота синхронизации**: 
  - Ежедневно для небольших объемов (< 500 операций/день)
  - Несколько раз в день для больших объемов
- **Timeout**: по умолчанию 30 секунд (можно увеличить в настройках)

## Безопасность

⚠️ **Важно:**
- Пароль 1С передается через HTTPS (используйте HTTPS в production!)
- Пароль НЕ сохраняется в БД
- Доступ ограничен ролями ADMIN и MANAGER
- Логи содержат информацию о синхронизации (без паролей)

## См. также

- [Документация по банковским транзакциям](BANK_TRANSACTIONS_IMPORT_GUIDE.md)
- [API документация](../backend/README.md)
- [Swagger UI](http://localhost:8000/docs) - интерактивная документация API
