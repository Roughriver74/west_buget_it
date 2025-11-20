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

from app.db.models import ProcessedInvoice, BudgetCategory, Organization, Department
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
        self.subdivision_guid: Optional[str] = None
        self.subdivision_name: Optional[str] = None

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
                } if self.cash_flow_category_guid else None,
                "subdivision": {
                    "guid": self.subdivision_guid,
                    "name": self.subdivision_name
                } if self.subdivision_guid else None
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
                logger.debug(f"Found cash flow category: {category.name} ({category.external_id_1c})")

        # 3. Проверка наличия контрагента в 1С (по ИНН)
        if invoice.supplier_inn:
            try:
                counterparty = self.odata_client.get_counterparty_by_inn(invoice.supplier_inn)
                if counterparty:
                    result.counterparty_guid = counterparty.get('Ref_Key')
                    result.counterparty_name = counterparty.get('Description')
                    logger.debug(f"Found counterparty in 1C: {result.counterparty_name}")
                else:
                    result.add_error(
                        f"Контрагент с ИНН {invoice.supplier_inn} не найден в 1С. "
                        f"Создайте контрагента '{invoice.supplier_name}' в 1С перед отправкой."
                    )
            except Exception as e:
                result.add_error(f"Ошибка при поиске контрагента в 1С: {str(e)}")
                logger.error(f"Failed to search counterparty: {e}", exc_info=True)

        # 4. Получение организации (покупателя) по ИНН из parsed_data
        try:
            # Извлечь buyer INN из parsed_data
            buyer_inn = None
            buyer_name = None
            if invoice.parsed_data and isinstance(invoice.parsed_data, dict):
                buyer = invoice.parsed_data.get('buyer', {})
                buyer_inn = buyer.get('inn')
                buyer_name = buyer.get('name')

            # Если ИНН не найден, попробуем fallback-стратегии
            organization = None
            if not buyer_inn:
                logger.warning(f"Buyer INN not found in parsed_data, attempting fallback strategies")

                # Стратегия 1: Поиск по названию покупателя
                if buyer_name:
                    logger.debug(f"Trying to find organization by buyer name: {buyer_name}")
                    # Поиск по частичному совпадению названия (например "ДЕМО" в "ООО ДЕМО ЛОГИСТИК")
                    organizations_by_name = self.db.query(Organization).filter(
                        Organization.is_active == True,
                        Organization.external_id_1c.isnot(None),
                        Organization.inn.isnot(None)
                    ).all()

                    for org in organizations_by_name:
                        org_name = (org.short_name or org.name or '').upper()
                        if 'ДЕМО' in buyer_name.upper() and 'ДЕМО' in org_name:
                            organization = org
                            buyer_inn = org.inn
                            logger.debug(f"Found organization by name match: {org.short_name} (INN: {org.inn})")
                            break

                # Стратегия 2: Использовать первую активную организацию с ИНН
                if not organization:
                    logger.info("Trying to use first active organization with INN and 1C sync")
                    organization = self.db.query(Organization).filter(
                        Organization.is_active == True,
                        Organization.external_id_1c.isnot(None),
                        Organization.inn.isnot(None)
                    ).first()

                    if organization:
                        buyer_inn = organization.inn
                        logger.debug(f"Using first active organization as fallback: {organization.short_name} (INN: {organization.inn})")
                    else:
                        result.add_error(
                            f"ИНН покупателя не найден в распознанных данных счета, и не удалось найти подходящую организацию. "
                            f"Проверьте качество распознавания или добавьте данные вручную."
                        )

            if buyer_inn:
                logger.debug(f"Found buyer INN: {buyer_inn}")

                # Если организация еще не найдена (не было fallback), искать в БД по ИНН
                if not organization:
                    organization = self.db.query(Organization).filter(
                        Organization.inn == buyer_inn,
                        Organization.is_active == True
                    ).first()

                if organization and organization.external_id_1c:
                    # Организация найдена в БД и синхронизирована с 1С
                    result.organization_guid = organization.external_id_1c
                    result.organization_name = organization.short_name or organization.name
                    logger.debug(f"Found organization in DB by INN: {result.organization_name} (GUID: {result.organization_guid})")
                else:
                    # Организация не найдена в БД или не синхронизирована - ищем в 1С
                    logger.debug(f"Organization not found in DB or not synced, fetching from 1C by INN: {buyer_inn}")
                    org_1c_data = self.odata_client.get_organization_by_inn(buyer_inn)

                    if org_1c_data:
                        org_guid = org_1c_data.get('Ref_Key')
                        org_name = org_1c_data.get('Description', '') or org_1c_data.get('Наименование', '')

                        result.organization_guid = org_guid
                        result.organization_name = org_name
                        logger.debug(f"Found organization in 1C: {org_name} (GUID: {org_guid})")

                        # Создать или обновить организацию в БД
                        if organization:
                            # Обновить external_id_1c
                            organization.external_id_1c = org_guid
                            if not organization.name:
                                organization.name = org_name
                            logger.debug(f"Updated organization in DB with 1C GUID")
                        else:
                            # Создать новую организацию
                            buyer_data = invoice.parsed_data.get('buyer', {})
                            organization = Organization(
                                name=org_name,
                                short_name=buyer_data.get('name', org_name)[:255],
                                inn=buyer_inn,
                                kpp=buyer_data.get('kpp'),
                                external_id_1c=org_guid,
                                department_id=invoice.department_id,
                                is_active=True
                            )
                            self.db.add(organization)
                            logger.debug(f"Created new organization in DB: {org_name}")

                        self.db.commit()
                    else:
                        result.add_error(
                            f"Организация с ИНН {buyer_inn} не найдена ни в базе данных, ни в 1С. "
                            f"Создайте организацию '{buyer.get('name', 'N/A')}' в 1С или базе данных."
                        )

        except Exception as e:
            result.add_error(f"Ошибка при получении организации: {str(e)}")
            logger.error(f"Failed to fetch organization: {e}", exc_info=True)

        # 5. Получение подразделения (subdivision) из department и поиск GUID в 1С
        try:
            # Получить department
            department = self.db.query(Department).filter_by(id=invoice.department_id).first()

            if department and department.ftp_subdivision_name:
                subdivision_name = department.ftp_subdivision_name.strip()
                logger.debug(f"Found subdivision name from department: '{subdivision_name}'")

                # Попытаться найти подразделение в 1С по имени
                subdivision_data = self.odata_client.get_subdivision_by_name(subdivision_name)

                if subdivision_data:
                    result.subdivision_guid = subdivision_data.get('Ref_Key')
                    result.subdivision_name = subdivision_name
                    logger.debug(f"Found subdivision in 1C: {subdivision_name} (GUID: {result.subdivision_guid})")
                else:
                    result.add_warning(
                        f"Подразделение '{subdivision_name}' не найдено в 1С. "
                        f"Создайте подразделение в 1С или проверьте название в настройках отдела."
                    )
            else:
                result.add_warning(
                    f"Название подразделения (ftp_subdivision_name) не указано в настройках отдела (department_id={invoice.department_id}). "
                    f"Заявка будет создана без указания подразделения."
                )

        except Exception as e:
            result.add_warning(f"Ошибка при получении подразделения: {str(e)}")
            logger.error(f"Failed to fetch subdivision: {e}", exc_info=True)

        # Итоговый результат
        if result.is_valid:
            logger.info(f"Invoice {invoice.id} validation PASSED")
        else:
            logger.warning(f"Invoice {invoice.id} validation FAILED: {len(result.errors)} errors")

        return result

    def create_expense_request_in_1c(
        self,
        invoice: ProcessedInvoice,
        upload_attachment: bool = True,
        user_comment: Optional[str] = None,
        current_user = None
    ) -> str:
        """
        Создать заявку на расход в 1С из invoice

        Args:
            invoice: Обработанный invoice
            upload_attachment: Загружать ли прикрепленный PDF файл (если есть)
            user_comment: Комментарий пользователя для заявки
            current_user: Текущий пользователь (для добавления ФИО в комментарий)

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
        # Желаемая дата платежа из invoice или +3 дня от даты счета
        desired_payment_date = getattr(invoice, 'desired_payment_date', None) or (invoice.invoice_date + timedelta(days=3))

        # Формирование JSON для POST запроса (по формату из рабочего примера curl)
        # ВАЖНО: Суммы должны быть целыми числами (int), как в рабочем примере
        amount_int = int(invoice.total_amount)

        # Определение наличия НДС
        # Если vat_amount указан явно и > 0, то счет с НДС
        # Если vat_amount == 0 или None, то без НДС
        has_vat = bool(invoice.vat_amount and invoice.vat_amount > 0)

        if has_vat:
            # Счет с НДС
            vat_amount = int(invoice.vat_amount)
            amount_without_vat = amount_int - vat_amount
            vat_treatment = "ОблагаетсяНДС"  # Или стандартное значение для 1С
        else:
            # Счет без НДС
            vat_amount = 0
            amount_without_vat = amount_int
            vat_treatment = "ПродажаНеОблагаетсяНДС"

        # Формирование назначения платежа
        payment_purpose = invoice.payment_purpose or f"Оплата по счету №{invoice.invoice_number} от {invoice.invoice_date.strftime('%d.%m.%Y')}"
        if has_vat and vat_amount > 0:
            payment_purpose += f"\nВ т.ч. НДС (20%) {vat_amount} руб."

        # Формирование комментария с ФИО пользователя
        user_full_name = "Система"
        if current_user:
            user_full_name = current_user.full_name or current_user.email or "Система"

        base_comment = user_comment or f"Создано автоматически из счета №{invoice.invoice_number}"
        full_comment = f"{user_full_name}: {base_comment}"

        # Логирование информации о НДС
        logger.info(
            f"📋 Expense request preparation:\n"
            f"   Invoice ID: {invoice.id}\n"
            f"   Total amount: {amount_int} руб.\n"
            f"   Has VAT: {'Да' if has_vat else 'Нет'}\n"
            f"   VAT amount: {vat_amount} руб.\n"
            f"   Amount without VAT: {amount_without_vat} руб.\n"
            f"   VAT treatment: {vat_treatment}\n"
            f"   Payment method: Безналичная\n"
            f"   User: {user_full_name}"
        )

        expense_request_data = {
            # Основные поля
            "Date": invoice.invoice_date.isoformat() + "T00:00:00",
            "Posted": True,  # Провести документ автоматически
            "Организация_Key": validation_result.organization_guid,
            "Статус": "НеСогласована",
            "ХозяйственнаяОперация": "ОплатаПоставщику",

            # Сумма и валюта
            "СуммаДокумента": amount_int,
            "Валюта_Key": self.RUB_CURRENCY_GUID,

            # Формы оплаты (безналичная оплата по умолчанию для счетов)
            "ФормаОплатыНаличная": False,
            "ФормаОплатыБезналичная": True,  # Безналичная оплата (счета от поставщиков)
            "ФормаОплатыПлатежнаяКарта": False,

            # НДС
            "НалогообложениеНДС": vat_treatment,  # "ОблагаетсяНДС" или "ПродажаНеОблагаетсяНДС"

            # Бюджет
            "вс_ЕстьСвободныйБюджетПоПлану": "Есть",

            # Назначение и дата платежа
            "НазначениеПлатежа": payment_purpose,
            "ЖелательнаяДатаПлатежа": desired_payment_date.isoformat() + "T00:00:00",

            # Контрагент
            "Контрагент_Key": validation_result.counterparty_guid,
            "Партнер_Key": validation_result.counterparty_guid,
            "БанковскийСчетКонтрагента_Key": self.EMPTY_GUID,  # Пустой - не знаем конкретный счет

            # Данные счета поставщика
            "вс_НомерПоДаннымПоставщика": invoice.invoice_number or "",
            "вс_ДатаПоДаннымПоставщика": invoice.invoice_date.isoformat() + "T00:00:00",

            # Ответственные
            "КтоЗаявил_Key": self.DEFAULT_REQUESTER_GUID,
            "КтоРешил_Key": self.DEFAULT_RESOLVER_GUID,
            "Автор_Key": self.AUTHOR_GUID,

            # Статьи и планирование
            "СтатьяДвиженияДенежныхСредств_Key": validation_result.cash_flow_category_guid,
            "ПланированиеСуммы": "ВВалютеПлатежа",
            "СтатьяАктивовПассивов_Key": self.EMPTY_GUID,
            "ВариантОплаты": "ПредоплатаДоПоступления",

            # Комментарий (с ФИО пользователя в начале)
            "Комментарий": full_comment,
            "ФормаОплатыЗаявки": "",

            # Табличная часть РасшифровкаПлатежа
            "РасшифровкаПлатежа": [
                {
                    "LineNumber": 1,
                    "Номенклатура_Key": self.EMPTY_GUID,
                    "СтатьяРасходов_Key": validation_result.cash_flow_category_guid,
                    "СтатьяДвиженияДенежныхСредств_Key": validation_result.cash_flow_category_guid,
                    "Сумма": amount_int,
                    "СуммаБезНДС": amount_without_vat,
                    "СуммаНДС": vat_amount,
                    "СтавкаНДС_Key": self.VAT_20_PERCENT_GUID if vat_amount > 0 else self.EMPTY_GUID,
                    "Количество": 1,
                    "Цена": amount_int
                }
            ]
        }

        # Добавить подразделение только если оно найдено (1С не принимает пустой GUID)
        if validation_result.subdivision_guid:
            expense_request_data["Подразделение_Key"] = validation_result.subdivision_guid
            logger.debug(f"Adding subdivision to request: {validation_result.subdivision_name} (GUID: {validation_result.subdivision_guid})")
        else:
            logger.debug("No subdivision found, omitting Подразделение_Key field from request")

        logger.debug(f"1C expense request data prepared (complete format): {expense_request_data}")

        # 3. Создание документа в 1С
        try:
            response = self.odata_client.create_expense_request(expense_request_data)
            ref_key = response.get('Ref_Key')

            if not ref_key:
                raise Exception("1C returned empty Ref_Key")

            logger.debug(f"Expense request created in 1C with Ref_Key: {ref_key}")

            # 4. Загрузка файла invoice как прикрепленного файла
            if upload_attachment and invoice.file_path:
                try:
                    import os
                    from pathlib import Path

                    # Проверка существования файла
                    file_path = Path(invoice.file_path)
                    if not file_path.exists():
                        logger.warning(f"Invoice file not found: {invoice.file_path}, skipping attachment upload")
                    else:
                        # Прочитать файл
                        with open(file_path, 'rb') as f:
                            file_content = f.read()

                        # Определить имя файла и расширение
                        original_filename = invoice.original_filename or file_path.name
                        file_extension = file_path.suffix.lstrip('.')  # .pdf -> pdf

                        logger.info(f"Uploading attachment to 1C: {original_filename} ({len(file_content)} bytes)")

                        # Загрузить в 1С используя правильный endpoint
                        attachment_result = self.odata_client.upload_attachment_to_expense_request(
                            file_content=file_content,
                            filename=original_filename,
                            owner_guid=ref_key,
                            file_extension=file_extension
                        )

                        if attachment_result:
                            logger.info(f"✅ Attachment uploaded successfully to 1C expense request")
                        else:
                            logger.warning(f"⚠️ Failed to upload attachment to 1C (non-critical)")

                except FileNotFoundError:
                    logger.warning(f"Invoice file not found: {invoice.file_path}, skipping attachment upload")
                except Exception as e:
                    logger.warning(f"Failed to upload attachment: {e} (non-critical, continuing)", exc_info=True)
            else:
                if not upload_attachment:
                    logger.debug("Attachment upload disabled by parameter")
                elif not invoice.file_path:
                    logger.debug("No file path in invoice, skipping attachment upload")

            # 5. Обновить invoice
            invoice.external_id_1c = ref_key
            invoice.created_in_1c_at = datetime.utcnow()
            self.db.commit()

            logger.debug(f"Invoice {invoice.id} updated with external_id_1c={ref_key}")

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
                logger.debug(f"Suggested category: {category.name} (id={category.id})")
                return category.id

        logger.debug("No suitable category found")
        return None
