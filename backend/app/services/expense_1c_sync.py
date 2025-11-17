"""
1C Expense Requests Sync Service

Сервис для синхронизации заявок на расход из 1С через OData
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import (
    Expense,
    ExpenseStatusEnum,
    Organization,
    Contractor,
    BudgetCategory
)
from app.services.odata_1c_client import OData1CClient

logger = logging.getLogger(__name__)


class Expense1CSyncResult:
    """Результат синхронизации заявок на расход из 1С"""

    def __init__(self):
        self.total_fetched = 0  # Получено из 1С
        self.total_processed = 0  # Обработано
        self.total_created = 0  # Создано новых
        self.total_updated = 0  # Обновлено существующих
        self.total_skipped = 0  # Пропущено (дубликаты без изменений)
        self.errors: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_fetched': self.total_fetched,
            'total_processed': self.total_processed,
            'total_created': self.total_created,
            'total_updated': self.total_updated,
            'total_skipped': self.total_skipped,
            'errors': self.errors,
            'success': len(self.errors) == 0
        }


class Expense1CSync:
    """Синхронизация заявок на расход из 1С"""

    def __init__(
        self,
        db: Session,
        odata_client: OData1CClient,
        department_id: int
    ):
        """
        Initialize sync service

        Args:
            db: Database session
            odata_client: 1C OData client
            department_id: Department ID for multi-tenancy
        """
        self.db = db
        self.odata_client = odata_client
        self.department_id = department_id

    def sync_expenses(
        self,
        date_from: date,
        date_to: date,
        batch_size: int = 100,
        only_posted: bool = True
    ) -> Expense1CSyncResult:
        """
        Синхронизировать заявки на расход из 1С за период

        Args:
            date_from: Начальная дата периода
            date_to: Конечная дата периода
            batch_size: Размер батча для запроса к 1С
            only_posted: Только проведенные документы

        Returns:
            Результат синхронизации
        """
        result = Expense1CSyncResult()

        logger.info(
            f"Starting 1C expense sync: date_from={date_from}, date_to={date_to}, "
            f"department_id={self.department_id}, only_posted={only_posted}"
        )

        skip = 0
        while True:
            try:
                # Получить батч из 1С
                expense_docs = self.odata_client.get_expense_requests(
                    date_from=date_from,
                    date_to=date_to,
                    top=batch_size,
                    skip=skip,
                    only_posted=only_posted
                )

                if not expense_docs:
                    logger.info(f"No more expense documents to fetch (skip={skip})")
                    break

                result.total_fetched += len(expense_docs)
                logger.info(f"Fetched {len(expense_docs)} expense documents from 1C (skip={skip})")

                # Обработать батч
                for doc in expense_docs:
                    try:
                        self._process_expense_document(doc, result)
                        result.total_processed += 1
                    except Exception as e:
                        error_msg = f"Failed to process expense document {doc.get('Ref_Key', 'unknown')}: {str(e)}"
                        logger.error(error_msg, exc_info=True)
                        result.errors.append(error_msg)

                # Коммит после каждого батча
                self.db.commit()
                logger.info(f"Committed batch: {result.total_processed} processed")

                # Пагинация
                skip += batch_size

                # Защита от бесконечного цикла
                if len(expense_docs) < batch_size:
                    logger.info("Reached end of data (batch size smaller than requested)")
                    break

            except Exception as e:
                logger.error(f"Error fetching expense documents: {e}", exc_info=True)
                result.errors.append(f"Fetch error: {str(e)}")
                self.db.rollback()
                break

        logger.info(f"1C expense sync completed: {result.to_dict()}")
        return result

    def _process_expense_document(
        self,
        doc: Dict[str, Any],
        result: Expense1CSyncResult
    ) -> None:
        """
        Обработать один документ заявки на расход из 1С

        Args:
            doc: Документ из 1С OData
            result: Объект результата для накопления статистики
        """
        # Извлечь данные из документа 1С
        external_id = doc.get('Ref_Key')
        if not external_id or external_id == "00000000-0000-0000-0000-000000000000":
            raise ValueError("Missing or invalid Ref_Key")

        # Проверить, существует ли заявка с таким external_id
        existing_expense = self.db.query(Expense).filter(
            and_(
                Expense.external_id_1c == external_id,
                Expense.department_id == self.department_id
            )
        ).first()

        # Маппинг данных из 1С
        expense_data = self._map_1c_to_expense(doc)

        if existing_expense:
            # Обновить существующую заявку
            updated = self._update_expense(existing_expense, expense_data)
            if updated:
                result.total_updated += 1
                logger.debug(f"Updated expense {existing_expense.number} (external_id={external_id})")
            else:
                result.total_skipped += 1
                logger.debug(f"Skipped expense {existing_expense.number} (no changes)")
        else:
            # Создать новую заявку
            new_expense = self._create_expense(expense_data, external_id)
            result.total_created += 1
            logger.debug(f"Created expense {new_expense.number} (external_id={external_id})")

    def _map_1c_to_expense(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Маппинг данных из документа 1С в формат Expense

        Args:
            doc: Документ из 1С OData

        Returns:
            Словарь с данными для создания/обновления Expense

        1C Document fields (actual structure from test):
            - Number: Номер документа (например: "ВЛ0В-000203")
            - Date: Дата документа (ISO format)
            - СуммаДокумента: Сумма документа
            - Организация_Key: GUID организации
            - Контрагент_Key: GUID контрагента
            - Комментарий: Краткий комментарий
            - НазначениеПлатежа: Полное назначение платежа
            - Posted: Проведен ли документ
            - Статус: Статус документа (вс_Оплачена и т.д.)
            - ДатаПлатежа: Дата платежа
        """
        # Дата документа
        date_str = doc.get('Date', '')
        try:
            request_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            request_date = datetime.utcnow()
            logger.warning(f"Invalid date in document {doc.get('Ref_Key')}: {date_str}, using current time")

        # Дата платежа (если указана)
        payment_date = None
        payment_date_str = doc.get('ДатаПлатежа', '')
        if payment_date_str and payment_date_str != '0001-01-01T00:00:00':
            try:
                payment_date = datetime.fromisoformat(payment_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Сумма документа
        amount = Decimal(str(doc.get('СуммаДокумента') or 0))

        # Номер документа
        number = doc.get('Number', '') or 'UNKNOWN'

        # Организация
        org_key = doc.get('Организация_Key')
        organization_id = self._get_or_create_organization(org_key) if org_key else None

        # Контрагент
        contractor_key = doc.get('Контрагент_Key')
        contractor_id = self._get_or_create_contractor(contractor_key) if contractor_key else None

        # Комментарий (используем НазначениеПлатежа как основной, Комментарий как резервный)
        comment = (
            doc.get('НазначениеПлатежа') or
            doc.get('Комментарий') or
            ''
        )

        # Заявитель (не используем пока, т.к. нет в структуре)
        requester = ''

        # Статус на основе проведения и статуса документа
        is_posted = doc.get('Posted', False)
        doc_status = doc.get('Статус', '')

        # Маппинг статусов 1С -> наша система
        if doc_status == 'вс_Оплачена':
            status = ExpenseStatusEnum.PAID
            is_paid = True
            is_closed = True
        elif is_posted:
            status = ExpenseStatusEnum.PENDING
            is_paid = False
            is_closed = False
        else:
            status = ExpenseStatusEnum.DRAFT
            is_paid = False
            is_closed = False

        return {
            'number': str(number),
            'request_date': request_date,
            'payment_date': payment_date,
            'amount': amount,
            'organization_id': organization_id,
            'contractor_id': contractor_id,
            'comment': comment,
            'requester': requester,
            'status': status,
            'is_paid': is_paid,
            'is_closed': is_closed,
            'category_id': None,  # Категория назначается вручную или через AI
            'imported_from_ftp': False  # Импортировано из 1С OData
        }

    def _get_or_create_organization(self, org_key: str) -> Optional[int]:
        """
        Получить или создать организацию по GUID из 1С

        Args:
            org_key: GUID организации

        Returns:
            ID организации в БД или None

        Note:
            Organization.external_id_1c уникален глобально (не per department),
            т.к. организации shared across departments
        """
        if not org_key or org_key == "00000000-0000-0000-0000-000000000000":
            return None

        # Проверить, есть ли уже в БД (external_id_1c уникален глобально)
        org = self.db.query(Organization).filter(
            Organization.external_id_1c == org_key
        ).first()

        if org:
            return org.id

        # Получить данные из 1С
        try:
            org_data = self.odata_client.get_organization_by_key(org_key)
            if not org_data:
                logger.warning(f"Organization {org_key} not found in 1C")
                return None

            # Извлечь данные (НаименованиеСокращенное - основное поле)
            short_name = org_data.get('НаименованиеСокращенное', '')
            full_name = org_data.get('Наименование', short_name) or short_name or 'Unknown Organization'

            # Generate unique name (since name has unique constraint)
            # Use short_name or create from full_name
            name = short_name or full_name
            if not name:
                name = f"Organization_{org_key[:8]}"

            # Check if name already exists and make unique
            existing_name = self.db.query(Organization).filter(
                Organization.name == name
            ).first()
            if existing_name:
                # Append INN or key to make unique
                inn = org_data.get('ИНН', '')
                name = f"{name}_{inn}" if inn else f"{name}_{org_key[:8]}"

            # Создать организацию
            new_org = Organization(
                name=name,
                full_name=full_name,
                short_name=short_name or 'Unknown',
                inn=org_data.get('ИНН', ''),
                kpp=org_data.get('КПП', ''),
                external_id_1c=org_key,
                department_id=self.department_id,  # Track which department imported
                is_active=True
            )
            self.db.add(new_org)
            self.db.flush()  # Получить ID без коммита

            logger.info(f"Created organization from 1C: {new_org.short_name} (external_id={org_key})")
            return new_org.id

        except Exception as e:
            logger.error(f"Failed to create organization {org_key}: {e}")
            return None

    def _get_or_create_contractor(self, contractor_key: str) -> Optional[int]:
        """
        Получить или создать контрагента по GUID из 1С

        Args:
            contractor_key: GUID контрагента

        Returns:
            ID контрагента в БД или None
        """
        if not contractor_key or contractor_key == "00000000-0000-0000-0000-000000000000":
            return None

        # Проверить, есть ли уже в БД
        contractor = self.db.query(Contractor).filter(
            and_(
                Contractor.external_id_1c == contractor_key,
                Contractor.department_id == self.department_id
            )
        ).first()

        if contractor:
            return contractor.id

        # Получить данные из 1С
        try:
            contractor_data = self.odata_client.get_counterparty_by_key(contractor_key)
            if not contractor_data:
                logger.warning(f"Contractor {contractor_key} not found in 1C")
                return None

            # Извлечь данные (Наименование - основное поле для контрагентов)
            name = contractor_data.get('Наименование', '') or 'Unknown Contractor'

            # Создать контрагента
            new_contractor = Contractor(
                name=name,
                inn=contractor_data.get('ИНН', ''),
                kpp=contractor_data.get('КПП', ''),
                external_id_1c=contractor_key,
                department_id=self.department_id,
                is_active=True
            )
            self.db.add(new_contractor)
            self.db.flush()  # Получить ID без коммита

            logger.info(f"Created contractor from 1C: {new_contractor.name} (external_id={contractor_key})")
            return new_contractor.id

        except Exception as e:
            logger.error(f"Failed to create contractor {contractor_key}: {e}")
            return None

    def _create_expense(self, expense_data: Dict[str, Any], external_id: str) -> Expense:
        """
        Создать новую заявку на расход

        Args:
            expense_data: Данные заявки
            external_id: External ID из 1С

        Returns:
            Созданная заявка
        """
        new_expense = Expense(
            **expense_data,
            external_id_1c=external_id,
            department_id=self.department_id
        )
        self.db.add(new_expense)
        self.db.flush()
        return new_expense

    def _update_expense(self, expense: Expense, expense_data: Dict[str, Any]) -> bool:
        """
        Обновить существующую заявку на расход

        Args:
            expense: Существующая заявка
            expense_data: Новые данные

        Returns:
            True если были изменения, False если нет
        """
        updated = False

        # Список полей для обновления
        fields_to_update = [
            'amount', 'request_date', 'organization_id', 'contractor_id',
            'comment', 'requester', 'status'
        ]

        for field in fields_to_update:
            new_value = expense_data.get(field)
            current_value = getattr(expense, field)

            # Сравнение с учетом типов
            if new_value != current_value:
                setattr(expense, field, new_value)
                updated = True
                logger.debug(f"Updated field {field}: {current_value} -> {new_value}")

        if updated:
            expense.updated_at = datetime.utcnow()

        return updated
