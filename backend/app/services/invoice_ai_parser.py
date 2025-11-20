"""
AI Parser Service for invoice data extraction
Uses VseGPT API (OpenAI-compatible) to extract structured data from OCR text
"""
from openai import OpenAI
import json
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.invoice_processing import ParsedInvoiceData, SupplierData, BuyerData, InvoiceItem
from app.services.admin_settings_service import AdminSettingsService


class InvoiceAIParser:
    """Сервис извлечения структурированных данных из текста счета через AI"""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize AI Parser with VseGPT configuration

        Args:
            db: Database session (optional) - if provided, reads config from DB, otherwise uses .env
        """
        # Get config from DB or fallback to .env
        if db:
            config = AdminSettingsService.get_vsegpt_config(db)
            api_key = config["api_key"]
            base_url = config["base_url"]
            model = config["model"]
        else:
            api_key = settings.VSEGPT_API_KEY
            base_url = settings.VSEGPT_BASE_URL
            model = settings.VSEGPT_MODEL

        if not api_key:
            raise ValueError("VSEGPT_API_KEY не указан. Добавьте токен в настройках администратора или в .env файл.")

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model

    def parse_invoice(self, ocr_text: str, filename: str = "") -> ParsedInvoiceData:
        """
        Парсинг текста счета в структурированные данные

        Args:
            ocr_text: Текст счета из OCR
            filename: Имя файла (для логирования)

        Returns:
            ParsedInvoiceData: Распознанные данные счета

        Raises:
            Exception: При ошибке парсинга или валидации
        """
        prompt = self._build_prompt(ocr_text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по обработке российских бухгалтерских документов. "
                                  "Ты всегда возвращаешь только валидный JSON без дополнительного текста."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )

            response_text = response.choices[0].message.content
            logger.info(f"Получен ответ от AI для файла {filename}")

            # Извлекаем JSON из ответа (может быть обернут в ```json```)
            json_text = self._extract_json(response_text)

            # Парсим JSON
            invoice_dict = json.loads(json_text)

            # Преобразуем в Pydantic модель
            invoice_data = self._dict_to_parsed_data(invoice_dict)

            logger.info(f"Счет успешно распознан: №{invoice_data.invoice_number or 'N/A'} "
                       f"от {invoice_data.invoice_date or 'N/A'}")
            return invoice_data

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от AI: {e}")
            logger.debug(f"Ответ AI: {response_text[:500]}...")
            raise ValueError(f"AI вернул невалидный JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка парсинга через AI: {e}")
            raise

    def _build_prompt(self, ocr_text: str) -> str:
        """Построение промпта для AI"""
        return f"""Ты эксперт по обработке российских бухгалтерских документов.
Проанализируй текст счета на оплату и извлеки все данные в структурированном JSON формате.

ТЕКСТ СЧЕТА:
{ocr_text}

ИЗВЛЕКИ СЛЕДУЮЩИЕ ДАННЫЕ:

1. Номер счета (обычно "Счет на оплату №..." или просто "Счет №...")
2. Дата счета (формат ДД.ММ.ГГГГ или ДД.ММ.ГГ)
3. Данные поставщика (Получатель / Продавец / Поставщик / Исполнитель):
   - Наименование организации (полное или сокращенное)
   - ИНН (10 или 12 цифр)
   - КПП (9 цифр, если есть)
   - Наименование банка
   - БИК (9 цифр)
   - Расчетный счет (20 цифр)
   - Корреспондентский счет (если есть)
4. Данные покупателя - КРИТИЧЕСКИ ВАЖНО НАЙТИ:
   - Наименование организации (полное или сокращенное)
   - ИНН (10 или 12 цифр)
   - КПП (9 цифр, если есть)

   ОБЯЗАТЕЛЬНО ищи покупателя по ВСЕМ возможным вариантам:
   - "Плательщик:", "Покупатель:", "Заказчик:", "Клиент:"
   - "Абонент:", "Пользователь:", "Потребитель:"
   - "Грузополучатель:", "Получатель услуг:", "Получатель:"
   - "Заявитель:", "Адресат:", "Организация:"
   - "Для:", "От:", "Кому:", "Счет для:"

   МЕСТА ГДЕ ИСКАТЬ:
   - В самом начале счета (первые 5-10 строк)
   - В шапке документа перед "Счет №"
   - После слов "Договор:" или "Абонент:"
   - Между адресом и реквизитами поставщика
   - Строка с адресом часто указывает на покупателя

   ПРИМЕРЫ ФОРМАТОВ:
   - "Абонент: ООО "КОМПАНИЯ"\nАдрес: 123456, город..."
   - "Плательщик: ИНН 1234567890 ООО "КОМПАНИЯ""
   - "Заказчик\nООО "КОМПАНИЯ", ИНН 1234567890"
5. Суммы:
   - Сумма без НДС
   - Сумма НДС (если есть, если "Без налога НДС" или "НДС не облагается" = 0)
   - Итого к оплате (обычно написано жирным шрифтом или в отдельной строке)
6. Номер и дата договора (если указаны, формат "Договор №... от ...")
7. Назначение платежа (обычно "Оплата по счету №... от ...")
8. Табличная часть - позиции счета (наименование, количество, цена, сумма)

ВЕРНИ ТОЛЬКО ВАЛИДНЫЙ JSON в следующем формате:
{{
  "invoice_number": "2635",
  "invoice_date": "2025-10-31",
  "supplier": {{
    "name": "ООО ТРАСТ ТЕЛЕКОМ",
    "inn": "7734640247",
    "kpp": "504701001",
    "bank_name": "ПАО Сбербанк г. Москва",
    "bik": "044525225",
    "account": "40702810540000031808",
    "corr_account": "30101810400000000225"
  }},
  "buyer": {{
    "name": "ООО ДЕМО ГРУПП",
    "inn": "7806623324",
    "kpp": "780601001"
  }},
  "amount_without_vat": 2000.00,
  "vat_amount": 0,
  "total_amount": 2000.00,
  "contract_number": "t205150",
  "contract_date": "2025-04-01",
  "payment_purpose": "Оплата по счету №2635 от 31.10.2025",
  "items": [
    {{
      "description": "Услуги связи Т2024 Малый бизнес 5 по л/с t205150 за Октябрь 2025 г.",
      "quantity": 1,
      "unit": "-",
      "price": 2000.00,
      "amount": 2000.00
    }}
  ]
}}

ВАЖНО:
- Все числовые значения как числа (не строки)
- Даты в формате YYYY-MM-DD
- ИНН, КПП, БИК, счета - только цифры (без пробелов и дефисов)
- ОБЯЗАТЕЛЬНО заполни поле "buyer" - это критически важно!
- Если ИНН/КПП покупателя не найдены, но есть название - всё равно заполни buyer с name
- Если данные не найдены - используй null только в крайнем случае
- Верни ТОЛЬКО JSON, без дополнительных комментариев и markdown разметки

ПРОВЕРКА:
- Убедись что поле "buyer" заполнено (не null)!
- Если не можешь найти явного указания покупателя, посмотри на адрес в начале счета
- Часто покупатель указан в первых строках документа без явного маркера

ПРОБЛЕМЫ С КОДИРОВКОЙ:
- Если видишь странные символы вместо русских букв (ɋɱɟɬ вместо Счет) - это проблема OCR
- Попробуй распознать слова по контексту и структуре:
  * ɋɱɟɬ → Счет
  * ɉɨɫɬɚɜɳɢɤ → Поставщик
  * ɉɨɤɭɩɚɬɟɥɶ → Покупатель
  * ɂɇɇ → ИНН
- Цифры и знаки препинания обычно распознаются правильно"""

    def _extract_json(self, text: str) -> str:
        """Извлечение JSON из ответа (может быть обернут в markdown)"""
        text = text.strip()

        # Если есть markdown код блок
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            return text[start:end].strip()

        return text

    def _dict_to_parsed_data(self, data: Dict[str, Any]) -> ParsedInvoiceData:
        """Преобразование словаря в Pydantic модель"""

        # Преобразуем поставщика
        supplier = None
        if data.get('supplier'):
            supplier = SupplierData(**data['supplier'])

        # Преобразуем покупателя
        buyer = None
        if data.get('buyer'):
            buyer = BuyerData(**data['buyer'])

        # Преобразуем позиции
        items = []
        if data.get('items'):
            items = [InvoiceItem(**item) for item in data['items']]

        # Преобразуем даты
        invoice_date = None
        if data.get('invoice_date'):
            try:
                invoice_date = datetime.fromisoformat(data['invoice_date']).date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Не удалось распарсить invoice_date: {e}")

        contract_date = None
        if data.get('contract_date'):
            try:
                contract_date = datetime.fromisoformat(data['contract_date']).date()
            except (ValueError, TypeError) as e:
                logger.warning(f"Не удалось распарсить contract_date: {e}")

        # Формируем назначение платежа если не указано
        payment_purpose = data.get('payment_purpose')
        if not payment_purpose and data.get('invoice_number') and invoice_date:
            payment_purpose = f"Оплата по счету №{data['invoice_number']} от {invoice_date.strftime('%d.%m.%Y')}"

        return ParsedInvoiceData(
            invoice_number=data.get('invoice_number'),
            invoice_date=invoice_date,
            supplier=supplier,
            buyer=buyer,
            amount_without_vat=Decimal(str(data['amount_without_vat'])) if data.get('amount_without_vat') is not None else None,
            vat_amount=Decimal(str(data['vat_amount'])) if data.get('vat_amount') is not None else None,
            total_amount=Decimal(str(data['total_amount'])) if data.get('total_amount') is not None else None,
            payment_purpose=payment_purpose,
            contract_number=data.get('contract_number'),
            contract_date=contract_date,
            items=items
        )
