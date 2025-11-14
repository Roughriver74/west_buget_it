# Справочные данные для Bank Transactions

> Данные извлечены из файла: `xls/Копия ДДС_2025_без доп вкладок_03.10.2025.xlsx`
> Период: январь - сентябрь 2025
> Всего транзакций: 167,598

---

## 1. Статья (Category / Article)

**Назначение**: Категория расхода/дохода
**Всего уникальных значений**: 57
**Самые частые**:

| Статья | Кол-во транзакций |
|--------|-------------------|
| Покупатель | 106,576 |
| Зарплата | 4,248 |
| Товар | 8,435 |
| Услуги банка | 5,363 |
| Перемещение | 4,183 |
| Кредит | 1,599 |
| Возврат | 2,108 |
| Налоги | 604 |
| Аренда | 260 |
| Командировка | 494 |

**Полный список**:
```
Административный отдел (500)
Аренда (226)
Бонус (49)
Бухгалтерия (30)
ВЭД (33)
Вайнер (76)
Возврат (1533)
Возврат  (7)
Дивиденды (105)
Зарплата (3626)
Зарплата  (6)
ИТ Отдел (14)
ИТ отдел (272)
Командировка (262)
Командировка смартвей (232)
Кредит (1224)
Маркетинг (121)
Налоги (535)
Не учитывать (11)
ОЗ (8)
ОП (1318)
Отдел Кадров (124)
Отдел Логистики (215)
Отдел логистики (99)
ПЕремещение (3)
Перемещение (3209)
Покупатель (75657)
Расходы руководителей (39)
СБ (30)
СЦ (147)
Склад (223)
Т21 (24)
Товар (4340)
Товар  (2)
УЦ (222)
Услуги банка (4454)
Услуги банка  (649)
ФО (1)
ЮП (24)
аренда (34)
бонус (22)
бухгалтерия (12)
возврат (568)
зарплата (616)
кредит (375)
маркетинг (10)
налоги (69)
не учитывать (19)
обмен валюты (45)
отдел логистики (662)
перемещение (971)
покупатель (30919)
склад (161)
товар (4092)
товар  (1)
услуги банка (260)
уц (1)
```

**⚠️ Проблемы**:
- Дубликаты с разным регистром (Зарплата/зарплата, Аренда/аренда)
- Лишние пробелы ("Товар ", "Зарплата ")
- Опечатки ("ПЕремещение")

**Рекомендация**: Нормализовать данные (привести к единому регистру, убрать лишние пробелы)

---

## 2. Регион (Region)

**Назначение**: Географическое расположение
**Всего уникальных значений**: 5

| Регион | Кол-во транзакций |
|--------|-------------------|
| СПБ | 132,462 |
| Москва | 2,910 |
| Краснодар | 3,113 |
| Спб | 1 |
| спб | 1 |

**⚠️ Проблемы**:
- Дубликаты: СПБ, Спб, спб (разный регистр)

**Рекомендация enum**:
```python
class RegionEnum(str, enum.Enum):
    SPB = "SPB"           # Санкт-Петербург
    MOSCOW = "MOSCOW"     # Москва
    KRASNODAR = "KRASNODAR"  # Краснодар
    OTHER = "OTHER"       # Прочие регионы
```

**Маппинг при импорте**:
```python
REGION_MAPPING = {
    "СПБ": "SPB",
    "Спб": "SPB",
    "спб": "SPB",
    "Санкт-Петербург": "SPB",
    "Москва": "MOSCOW",
    "Краснодар": "KRASNODAR",
}
```

---

## 3. Вид (Transaction Source / Account Type)

**Назначение**: Банковский счет / источник транзакции
**Всего уникальных значений**: 68

**Топ-20 по частоте**:

| Вид | Кол-во транзакций |
|-----|-------------------|
| МирумедСБ | 37,956 |
| ВестСБ | 18,839 |
| ВДентСБ | 8,653 |
| СмартвейСБ | 5,922 |
| ВСтомСБ | 3,920 |
| ВестТБанк | 3,591 |
| Омни-С Рахат | 2,839 |
| МирумедВТБ | 2,809 |
| ВестАльфа | 2,582 |
| ВЛогистикСБ | 2,407 |
| АртбгСБ | 2,180 |
| ВСервисСБ | 805 |
| ОмниТБанк | 776 |
| ВФармСБ | 667 |
| ВГруппРосбанк | 1,040 |
| ВЛогистикРосбанк | 618 |
| ВДентТБанк | 84 |
| ВСтомТБанк | 43 |
| Вест_Бонус | 56 |
| ВТоргСБ | 163 |

**Полный список** (68 значений):
```
АртбгСБ, ВГруппРосбанк, ВГруппСБ, ВДентББР, ВДентСБ, ВДентСБ_спец, ВДентСолид,
ВДентТБанк, ВЛогистикРосбанк, ВЛогистикСБ, ВСервисСБ, ВСервисСБ_Спец, ВСервисСБ_спец,
ВСервисТБанк, ВСервисТбанк, ВСтомСБ, ВСтомСБ_спец, ВСтомТБанк, ВТоргСБ, ВТоргСБ_спец,
ВФармСБ, ВгруппРосбанк, ВгруппСБ, Вест_Бонус, ВестАльфа, ВестВТБ, ВестВТБ_Спец,
ВестВТБ_спец, ВестРосбанк, ВестСБ, ВестСБ_СП, ВестСБ_Спец, ВестСБ_спец, ВестТБанк,
ВестТбанк, Логистика_СП, МирумедВТБ, МирумедСБ, МирумедСБ_Спец, МирумедСБ_спец,
МирумедТБанк, Наличный, Омни-С, Омни-С Рахат, ОмниТБанк, ОмниТбанк, СмартвейВТБ,
СмартвейВТБ_СП, СмартвейВТБ_Спец, СмартвейВТБ_спец, СмартвейСБ, СмартвейСБ_Спец,
СмартвейСБ_спец, СмартвейТБанк, Спцена_Мирумед, наличный, и др.
```

**⚠️ Проблемы**:
- Дубликаты с разным регистром (_Спец/_спец, ТБанк/Тбанк, Наличный/наличный)
- Смешанная номенклатура (банк + организация)

**Рекомендация enum**:
```python
class BankAccountTypeEnum(str, enum.Enum):
    # По банкам
    SBERBANK = "SBERBANK"          # Сбербанк (СБ)
    TBANK = "TBANK"                # Т-Банк (бывш. Тинькофф)
    VTB = "VTB"                    # ВТБ
    ALFABANK = "ALFABANK"          # Альфа-Банк
    ROSBANK = "ROSBANK"            # Росбанк
    BBR = "BBR"                    # Банк БКС Регионы
    CASH = "CASH"                  # Наличные

    # По типу
    REGULAR = "REGULAR"            # Обычный счет
    SPECIAL_PRICE = "SPECIAL_PRICE" # Спецена (_спец)
    CORP = "CORP"                  # Корпоративный (_СП)
```

**Альтернативный подход**: Хранить как текст (не enum), создать отдельную таблицу `bank_accounts`:
```sql
CREATE TABLE bank_accounts (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,  -- "ВестСБ"
    organization VARCHAR(100),           -- "Вест Групп"
    bank VARCHAR(50),                    -- "Сбербанк"
    account_type VARCHAR(50),            -- "Обычный" / "Спецена"
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## 4. Статус согласования (Approval Status)

**⚠️ КОЛОНКА ПУСТАЯ** - нет данных в текущем файле.

**Рекомендация** - создать enum для будущего использования:

```python
class ApprovalStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"               # Черновик
    PENDING = "PENDING"           # Ожидает согласования
    APPROVED = "APPROVED"         # Согласовано
    REJECTED = "REJECTED"         # Отклонено
    CANCELLED = "CANCELLED"       # Отменено
```

**Использование**:
- Для workflow согласования транзакций
- Отличается от `BankTransactionStatusEnum` (который для обработки)
- Можно использовать для контроля за крупными расходами

---

## 5. За что (Payment Purpose)

**Назначение**: Назначение платежа / описание транзакции
**Всего уникальных значений**: 29,766

**Топ-20 по частоте**:

| За что | Частота |
|--------|---------|
| Командировка | 282 |
| Перемещение ден. средств | 219 |
| Зарплата | 149 |
| Перевод между своими счетами | 123 |
| Бонус | 95 |
| аванс Доброхотова А.Е. | 90 |
| Возврат покупателям | 76 |
| Курьер | 60 |
| Оплата аренды | 52 |
| Налог УСН | 48 |
| Перемещение между р/с | 47 |
| Оплата за товар | 44 |
| НДФЛ | 42 |
| ЗП | 40 |
| Страховые взносы | 38 |
| Возврат | 36 |
| РКО | 35 |
| Комиссия банка | 34 |
| Аренда | 32 |
| Оплата услуг по договору | 30 |

**Примеры описаний**:
```
Командировка
Перемещение ден. средств
Зарплата
Оплата аренды офиса
Налог УСН
НДФЛ
Страховые взносы
Оплата за товар по договору
Комиссия банка
Курьерская доставка
Возврат покупателям
РКО (расчетно-кассовое обслуживание)
Аванс сотруднику
```

**Примечание**: Это поле используется AI-классификатором для определения категории через keyword matching.

---

## 6. Отдел (Department)

**Назначение**: Отдел компании (для multi-tenancy)
**Всего уникальных значений**: 17

| Отдел | Кол-во транзакций |
|-------|-------------------|
| ОП (Отдел продаж) | 147 |
| Командировка | 80 |
| Склад | 84 |
| Расходы руководителей | 54 |
| УЦ (Учебный центр) | 34 |
| СЦ (Сервисный центр) | 24 |
| Маркетинг | 13 |
| ЮП (Юридический отдел) | 14 |
| ВЭД (Внешнеэкономическая деятельность) | 10 |
| ОЗ | 10 |
| Административный отдел | 7 |
| СБ (Служба безопасности) | 7 |
| ИТ отдел | 4 |
| Бухгалтерия | 3 |
| Отдел логистики | 3 |

**⚠️ Проблемы**:
- Дубликаты: "Отдел логистики" / "отдел логистики" / "склад" / "Склад"
- "Командировка" - не отдел, а вид расхода

**Рекомендация**:
1. Сопоставить с существующей таблицей `departments` в БД
2. Создать маппинг при импорте

---

## 7. Кто (Organization / Payer)

**Назначение**: Организация-плательщик
**Всего уникальных значений**: 15

| Организация | Кол-во транзакций |
|-------------|-------------------|
| Вест Групп | 53,774 |
| Мирумед | 45,870 |
| Смартвей | 31,005 |
| Омни-С | 9,967 |
| Вест Логистик | 8,049 |
| Вест Сервис | 6,495 |
| Вест Стоматолог | 5,032 |
| Артбридж-Н | 2,225 |
| Лаборатория 21 век | 1,670 |
| Вест Фарм | 841 |
| Вест Торг | 757 |
| Вест Дент | 652 |
| Омникер | 642 |
| Стоматология МВ | 320 |
| Смартвей Трейд | 102 |

**Примечание**: Это поле сопоставляется с таблицей `organizations` в БД.

---

## Рекомендации по импорту

### 1. Маппинг колонок
```python
COLUMN_MAPPING = {
    "Дата": "transaction_date",
    "Кто": "organization_name",          # → lookup organizations.id
    "Кому": "counterparty_name",
    "за что": "payment_purpose",
    "статья": "article",                 # → custom field или notes
    "Регион": "region",                  # → новое поле (enum)
    "приход руб": "amount_credit",       # если > 0 → transaction_type = CREDIT
    "расход руб": "amount_debit",        # если > 0 → transaction_type = DEBIT
    "вид": "account_type",               # → новое поле (текст или enum)
    "Примечание": "notes",
    "Статус согласования": "approval_status",  # → новое поле (enum, пустое пока)
    "Отдел": "department_name",          # → lookup departments.id
}
```

### 2. Определение суммы и типа
```python
if row["приход руб"] and pd.notna(row["приход руб"]):
    amount = abs(float(row["приход руб"]))
    transaction_type = "CREDIT"
elif row["расход руб"] and pd.notna(row["расход руб"]):
    amount = abs(float(row["расход руб"]))
    transaction_type = "DEBIT"
else:
    amount = 0
    transaction_type = "DEBIT"
```

### 3. Нормализация данных
```python
# Регион
region = row["Регион"].strip().upper() if row["Регион"] else None
region = REGION_MAPPING.get(region, region)

# Статья
article = row["статья"].strip() if row["статья"] else None
article = article.capitalize()  # Приводим к единому регистру

# Вид
account_type = row["вид"].strip() if row["вид"] else None
```

### 4. Lookup существующих сущностей
```python
# Организация (Кто)
org_name = row["Кто"]
organization = db.query(Organization).filter(
    Organization.name.ilike(f"%{org_name}%")
).first()
organization_id = organization.id if organization else None

# Отдел
dept_name = row["Отдел"]
department = db.query(Department).filter(
    Department.name.ilike(f"%{dept_name}%")
).first()
department_id = department.id if department else default_department_id
```

---

## Добавление новых полей в БД

### Миграция 1: Регион
```python
# backend/app/db/models.py
class RegionEnum(str, enum.Enum):
    SPB = "SPB"
    MOSCOW = "MOSCOW"
    KRASNODAR = "KRASNODAR"
    OTHER = "OTHER"

class BankTransaction(Base):
    # ... existing fields ...
    region = Column(Enum(RegionEnum), nullable=True, index=True)
```

### Миграция 2: Вид (тип счета)
```python
# Вариант 1: Как текст (рекомендуется)
class BankTransaction(Base):
    account_type = Column(String(100), nullable=True, index=True)  # "ВестСБ", "МирумедВТБ"

# Вариант 2: Создать отдельную таблицу
class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    bank_name = Column(String(50))
    account_type = Column(String(50))  # "regular", "special_price", "corporate"
    is_active = Column(Boolean, default=True)

class BankTransaction(Base):
    bank_account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)
```

### Миграция 3: Статус согласования
```python
class ApprovalStatusEnum(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class BankTransaction(Base):
    approval_status = Column(Enum(ApprovalStatusEnum), nullable=True, index=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
```

### Миграция 4: Статья (article)
```python
# Если нужно хранить как отдельное поле
class BankTransaction(Base):
    article = Column(String(255), nullable=True, index=True)  # "Командировка", "Зарплата"

# Или категоризировать при импорте:
# "Командировка" → category = "Командировки"
# "Зарплата" → category = "ФОТ"
# и т.д.
```

---

## Создание миграции

```bash
cd backend

# Добавить новые поля в models.py
# Затем создать миграцию
alembic revision --autogenerate -m "add region, account_type, approval_status, article to bank_transactions"

# Просмотреть миграцию
cat alembic/versions/XXXXX_add_region_*.py

# Применить
alembic upgrade head
```

---

## Скрипт импорта данных

Создать `backend/scripts/import_bank_transactions_dds.py`:

```python
#!/usr/bin/env python3
"""
Import bank transactions from DDS Excel file
"""
import pandas as pd
from app.db import get_db
from app.db.models import BankTransaction, Organization, Department
from app.services.transaction_classifier import TransactionClassifier

FILE_PATH = "../xls/Копия ДДС_2025_без доп вкладок_03.10.2025.xlsx"

REGION_MAPPING = {
    "СПБ": "SPB", "Спб": "SPB", "спб": "SPB",
    "Москва": "MOSCOW",
    "Краснодар": "KRASNODAR",
}

def import_transactions():
    db = next(get_db())
    df = pd.read_excel(FILE_PATH, sheet_name='2025г')

    classifier = TransactionClassifier(db)
    imported = 0
    errors = []

    for idx, row in df.iterrows():
        try:
            # Определяем сумму и тип
            if pd.notna(row.get("приход руб")):
                amount = abs(float(row["приход руб"]))
                tx_type = "CREDIT"
            elif pd.notna(row.get("расход руб")):
                amount = abs(float(row["расход руб"]))
                tx_type = "DEBIT"
            else:
                continue  # Пропускаем строки без суммы

            # Lookup organization
            org_name = row.get("Кто")
            org = db.query(Organization).filter(
                Organization.name.ilike(f"%{org_name}%")
            ).first()

            # Lookup department
            dept_name = row.get("Отдел")
            dept = db.query(Department).filter(
                Department.name.ilike(f"%{dept_name}%")
            ).first() if dept_name else None

            # Normalize region
            region_raw = row.get("Регион")
            region = REGION_MAPPING.get(region_raw, region_raw) if region_raw else None

            # Create transaction
            transaction = BankTransaction(
                transaction_date=pd.to_datetime(row["Дата"]).date(),
                amount=amount,
                transaction_type=tx_type,
                counterparty_name=row.get("Кому"),
                payment_purpose=row.get("за что"),
                organization_id=org.id if org else None,
                department_id=dept.id if dept else 1,  # default dept
                region=region,
                account_type=row.get("вид"),
                article=row.get("статья"),
                notes=row.get("Примечание"),
                import_source="MANUAL_UPLOAD",
                import_file_name=FILE_PATH.split("/")[-1],
            )

            # AI Classification
            if transaction.payment_purpose:
                category_id, confidence, reasoning = classifier.classify(
                    payment_purpose=transaction.payment_purpose,
                    counterparty_name=transaction.counterparty_name,
                    counterparty_inn=None,
                    amount=amount,
                    department_id=transaction.department_id
                )

                if confidence >= 0.9:
                    transaction.category_id = category_id
                    transaction.category_confidence = confidence
                    transaction.status = "CATEGORIZED"
                elif category_id:
                    transaction.suggested_category_id = category_id
                    transaction.category_confidence = confidence
                    transaction.status = "NEEDS_REVIEW"

            db.add(transaction)
            imported += 1

            if imported % 100 == 0:
                db.commit()
                print(f"Imported {imported} transactions...")

        except Exception as e:
            errors.append({"row": idx, "error": str(e)})
            continue

    db.commit()
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Imported: {imported}")
    print(f"Errors: {len(errors)}")

if __name__ == "__main__":
    import_transactions()
```

---

## Итого

1. ✅ **Статья** - добавить как текстовое поле `article`
2. ✅ **Регион** - добавить enum `RegionEnum` (SPB, MOSCOW, KRASNODAR, OTHER)
3. ✅ **Вид** - добавить как текст `account_type` (или создать таблицу `bank_accounts`)
4. ✅ **Статус согласования** - добавить enum `ApprovalStatusEnum` (пока пустое)
5. ✅ Создать скрипт импорта с нормализацией и AI-классификацией
