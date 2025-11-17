"""
Invoice to 1C Expense Request Converter Service

Сервис для создания заявок на расходование денежных средств в 1С
на основе распознанных счетов (ProcessedInvoice).
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

from app.db.models import ProcessedInvoice, BudgetCategory
from app.services.odata_1c_client import OData1CClient

logger = logging.getLogger(__name__)


class InvoiceValidationError(Exception):
    """Ошибка валидации invoice перед отправкой в 1С"""
    pass


class Invoice1CValidationResult:
    """Результат валидации invoice перед отправкой в 1С"""

    def __init__(self):
        self.is_valid: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []

        # Найденные данные из 1С
        self.counterparty_guid: Optional[str] = None
        self.counterparty_name: Optional[str] = None
        self.organization_guid: Optional[str] = None
        self.organization_name: Optional[str] = None
        self.cash_flow_category_guid: Optional[str] = None
        self.cash_flow_category_name: Optional[str] = None

    def add_error(self, message: str):
        """Добавить ошибку"""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str):
        """Добавить предупреждение"""
        self.warnings.append(message)

    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "found_data": {
                "counterparty": {
                    "guid": self.counterparty_guid,
                    "name": self.counterparty_name
                } if self.counterparty_guid else None,
                "organization": {
                    "guid": self.organization_guid,
                    "name": self.organization_name
                } if self.organization_guid else None,
                "cash_flow_category": {
                    "guid": self.cash_flow_category_guid,
                    "name": self.cash_flow_category_name
                } if self.cash_flow_category_guid else None
            }
        }


class InvoiceTo1CConverter:
    """
    Сервис для конвертации ProcessedInvoice в заявку на расход в 1С
    """

    # GUID валюты RUB в 1С (из работающего примера)
    RUB_CURRENCY_GUID = "f04b98ee-b430-11ea-a43c-b42e994e04d3"

    # GUID пользователей (из работающего примера)
    DEFAULT_REQUESTER_GUID = "be7e04e0-4eaf-11e3-8632-50e549c4019a"  # КтоЗаявил
    DEFAULT_RESOLVER_GUID = "be7e04e0-4eaf-11e3-8632-50e549c4019a"   # КтоРешил
    AUTHOR_GUID = "be7e04e0-4eaf-11e3-8632-50e549c4019a"             # Автор

    # Пустые GUID для различных справочников
    EMPTY_GUID = "00000000-0000-0000-0000-000000000000"

    # Ставка НДС 20% (из работающего примера)
    VAT_20_PERCENT_GUID = "ed59436e-f9dc-11ee-ad54-74563c634acb"

    def __init__(self, db: Session, odata_client: OData1CClient):
        """
        Инициализация конвертера

        Args:
            db: Database session
            odata_client: OData 1C client
        """
        self.db = db
        self.odata_client = odata_client

    def validate_invoice_for_1c(self, invoice: ProcessedInvoice) -> Invoice1CValidationResult:
        """
        Валидировать invoice перед отправкой в 1С

        Args:
            invoice: Обработанный invoice

        Returns:
            Результат валидации с найденными данными из 1С
        """
        result = Invoice1CValidationResult()

        logger.info(f"Validating invoice {invoice.id} for 1C export")

        # 1. Проверка обязательных полей invoice
        if not invoice.invoice_number:
            result.add_error("Номер счета (invoice_number) не заполнен")

        if not invoice.invoice_date:
            result.add_error("Дата счета (invoice_date) не заполнена")

        if not invoice.total_amount or invoice.total_amount <= 0:
            result.add_error("Сумма счета (total_amount) не заполнена или <= 0")

        if not invoice.supplier_inn:
            result.add_error("ИНН поставщика (supplier_inn) не заполнен")

        if not invoice.payment_purpose:
            result.add_warning("Назначение платежа (payment_purpose) не заполнено")

        # 2. Проверка category_id (статья ДДС)
        if not invoice.category_id:
            result.add_error(
                "Статья ДДС не выбрана. Выберите категорию бюджета перед отправкой в 1С."
            )
        else:
            # Получить категорию и проверить external_id_1c
            category = self.db.query(BudgetCategory).filter_by(
                id=invoice.category_id
            ).first()

            if not category:
                result.add_error(f"Категория бюджета с id={invoice.category_id} не найдена")
            elif not category.external_id_1c:
                result.add_error(
                    f"Категория '{category.name}' не синхронизирована с 1С. "
                    f"external_id_1c не заполнен. Синхронизируйте справочник статей ДДС из 1С."
                )
            else:
                result.cash_flow_category_guid = category.external_id_1c
                result.cash_flow_category_name = category.name
                logger.info(f"Found cash flow category: {category.name} ({category.external_id_1c})")

        # 3. Проверка наличия контрагента в 1С (по ИНН)
        if invoice.supplier_inn:
            try:
                counterparty = self.odata_client.get_counterparty_by_inn(invoice.supplier_inn)
                if counterparty:
                    result.counterparty_guid = counterparty.get('Ref_Key')
                    result.counterparty_name = counterparty.get('Description')
                    logger.info(f"Found counterparty in 1C: {result.counterparty_name}")
                else:
                    result.add_error(
                        f"Контрагент с ИНН {invoice.supplier_inn} не найден в 1С. "
                        f"Создайте контрагента '{invoice.supplier_name}' в 1С перед отправкой."
                    )
            except Exception as e:
                result.add_error(f"Ошибка при поиске контрагента в 1С: {str(e)}")
                logger.error(f"Failed to search counterparty: {e}", exc_info=True)

        # 4. Проверка наличия организации в 1С (по buyer INN из parsed_data)
        buyer_inn = None
        if invoice.parsed_data and isinstance(invoice.parsed_data, dict):
            buyer = invoice.parsed_data.get('buyer', {})
            if isinstance(buyer, dict):
                buyer_inn = buyer.get('inn')

        if buyer_inn:
            try:
                organization = self.odata_client.get_organization_by_inn(buyer_inn)
                if organization:
                    result.organization_guid = organization.get('Ref_Key')
                    result.organization_name = organization.get('Description')
                    logger.info(f"Found organization in 1C: {result.organization_name}")
                else:
                    result.add_error(
                        f"Организация с ИНН {buyer_inn} не найдена в 1С. "
                        f"Создайте организацию в 1С перед отправкой."
                    )
            except Exception as e:
                result.add_error(f"Ошибка при поиске организации в 1С: {str(e)}")
                logger.error(f"Failed to search organization: {e}", exc_info=True)
        else:
            result.add_error(
                "ИНН покупателя (buyer.inn) не найден в parsed_data. "
                "Возможно, AI не распознал данные покупателя. Проверьте invoice."
            )

        # Итоговый результат
        if result.is_valid:
            logger.info(f"Invoice {invoice.id} validation PASSED")
        else:
            logger.warning(f"Invoice {invoice.id} validation FAILED: {len(result.errors)} errors")

        return result

    def create_expense_request_in_1c(
        self,
        invoice: ProcessedInvoice,
        upload_attachment: bool = True
    ) -> str:
        """
        Создать заявку на расход в 1С из invoice

        Args:
            invoice: Обработанный invoice
            upload_attachment: Загружать ли прикрепленный PDF файл (если есть)

        Returns:
            GUID созданной заявки в 1С (Ref_Key)

        Raises:
            InvoiceValidationError: Если validation не прошла
            Exception: При ошибке создания в 1С
        """
        logger.info(f"Starting 1C expense request creation for invoice {invoice.id}")

        # 1. Валидация
        validation_result = self.validate_invoice_for_1c(invoice)
        if not validation_result.is_valid:
            error_msg = f"Invoice validation failed: {'; '.join(validation_result.errors)}"
            logger.error(error_msg)
            raise InvoiceValidationError(error_msg)

        # 2. Подготовка данных для 1С
        # Дата платежа: +3 дня от даты счета
        payment_date = invoice.invoice_date + timedelta(days=3)

        # Формирование JSON для POST запроса (по формату из рабочего примера curl)
        # ВАЖНО: Суммы должны быть целыми числами (int), как в рабочем примере
        amount_int = int(invoice.total_amount)

        expense_request_data = {
            "Date": invoice.invoice_date.isoformat() + "T00:00:00",  # ИЗМЕНЕНО: "Date" вместо "Дата"
            "Posted": False,  # ДОБАВЛЕНО: документ не проведен
            "Статус": "НеСогласована",  # ДОБАВЛЕНО: статус заявки
            "Организация_Key": validation_result.organization_guid,
            "КтоЗаявил_Key": self.DEFAULT_REQUESTER_GUID,  # ДОБАВЛЕНО: кто заявил
            "Контрагент_Key": validation_result.counterparty_guid,  # ИЗМЕНЕНО: "Контрагент_Key" вместо "Получатель_Key"
            "Партнер_Key": validation_result.counterparty_guid,  # ДОБАВЛЕНО: партнер (тот же что и контрагент)
            "СуммаДокумента": amount_int,  # ИЗМЕНЕНО: int вместо float
            "Валюта_Key": self.RUB_CURRENCY_GUID,  # RUB (правильный GUID)
            "СтатьяДДС_Key": validation_result.cash_flow_category_guid,
            "НазначениеПлатежа": invoice.payment_purpose or f"Оплата по счету №{invoice.invoice_number}",
            "ДатаПлатежа": payment_date.isoformat() + "T00:00:00",
            "ХозяйственнаяОперация": "ОплатаПоставщику",  # Фиксированная операция
            "Автор_Key": self.AUTHOR_GUID,  # ДОБАВЛЕНО: автор документа
            "РасшифровкаПлатежа": [  # ДОБАВЛЕНО: табличная часть с расшифровкой
                {
                    "НомерСтроки": 1,
                    "Номенклатура_Key": self.EMPTY_NOMENCLATURE_GUID,
                    "СтатьяРасходов_Key": validation_result.cash_flow_category_guid,
                    "Сумма": amount_int  # ИЗМЕНЕНО: int вместо float
                }
            ]
        }

        logger.info(f"1C expense request data prepared (new format): {expense_request_data}")

        # 3. Создание документа в 1С
        try:
            response = self.odata_client.create_expense_request(expense_request_data)
            ref_key = response.get('Ref_Key')

            if not ref_key:
                raise Exception("1C returned empty Ref_Key")

            logger.info(f"Expense request created in 1C with Ref_Key: {ref_key}")

            # 4. (Опционально) Загрузка файла invoice
            if upload_attachment and invoice.file_path:
                try:
                    # Прочитать файл
                    with open(invoice.file_path, 'rb') as f:
                        file_content = f.read()

                    # Загрузить в 1С
                    attachment_result = self.odata_client.upload_attachment_base64(
                        file_content=file_content,
                        filename=invoice.file_name or f"invoice_{invoice.id}.pdf",
                        owner_guid=ref_key
                    )

                    if attachment_result:
                        logger.info(f"Attachment uploaded successfully to 1C")
                    else:
                        logger.warning(f"Failed to upload attachment to 1C (non-critical)")

                except Exception as e:
                    logger.warning(f"Failed to upload attachment: {e} (non-critical)", exc_info=True)

            # 5. Обновить invoice
            invoice.external_id_1c = ref_key
            invoice.created_in_1c_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Invoice {invoice.id} updated with external_id_1c={ref_key}")

            return ref_key

        except Exception as e:
            logger.error(f"Failed to create expense request in 1C: {e}", exc_info=True)
            self.db.rollback()
            raise

    def suggest_cash_flow_category(
        self,
        payment_purpose: str,
        supplier_name: Optional[str] = None,
        total_amount: Optional[Decimal] = None,
        department_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Предложить статью ДДС на основе назначения платежа

        Args:
            payment_purpose: Назначение платежа
            supplier_name: Наименование поставщика (опционально)
            total_amount: Сумма (опционально)
            department_id: ID отдела (для фильтрации категорий)

        Returns:
            ID предложенной категории или None
        """
        if not payment_purpose:
            return None

        logger.info(f"Suggesting cash flow category for: {payment_purpose[:50]}...")

        # Ключевые слова для определения категории
        # TODO: Можно расширить и улучшить логику
        keywords_mapping = {
            "аренд": ["Аренда", "аренд"],
            "связь": ["Услуги связи", "связь", "интернет", "телефон"],
            "канцтовар": ["Канцтовары", "канцтовар", "бумага"],
            "компьютер": ["Компьютеры и оргтехника", "компьютер", "ноутбук"],
            "лицензи": ["Лицензии ПО", "лицензи", "подписк", "Microsoft", "Adobe"],
            "реклам": ["Реклама", "реклам", "маркетинг"],
            "транспорт": ["Транспортные услуги", "транспорт", "доставк"],
        }

        # Нормализовать текст
        payment_purpose_lower = payment_purpose.lower()

        # Поиск по ключевым словам
        matched_keywords = []
        for keyword, terms in keywords_mapping.items():
            if any(term.lower() in payment_purpose_lower for term in terms):
                matched_keywords.append(keyword)

        # Поиск категории в БД
        query = self.db.query(BudgetCategory).filter(
            BudgetCategory.is_active == True,
            BudgetCategory.external_id_1c.isnot(None),  # Только синхронизированные
            BudgetCategory.is_folder == False  # Только элементы
        )

        if department_id:
            query = query.filter(BudgetCategory.department_id == department_id)

        # Попробовать найти по названию
        for keyword in matched_keywords:
            category = query.filter(
                BudgetCategory.name.ilike(f"%{keyword}%")
            ).first()

            if category:
                logger.info(f"Suggested category: {category.name} (id={category.id})")
                return category.id

        logger.info("No suitable category found")
        return None
