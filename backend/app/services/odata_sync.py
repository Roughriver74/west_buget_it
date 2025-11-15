"""
OData Sync Service for 1C Integration
Синхронизация банковских операций из 1С через OData протокол
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from decimal import Decimal
import requests
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import Session

from app.db.models import (
    BankTransaction,
    BankTransactionTypeEnum,
    BankTransactionStatusEnum,
    Organization,
    Department,
)

logger = logging.getLogger(__name__)


class ODataSyncConfig:
    """Configuration for OData connection to 1C"""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        entity_name: str = "Document_BankStatement",  # Имя сущности в 1С
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.entity_name = entity_name
        self.timeout = timeout
        self.auth = HTTPBasicAuth(username, password)


class ODataBankTransactionSync:
    """
    Service for syncing bank transactions from 1C via OData

    Поддерживаемые операции:
    - Списания (DEBIT) - расходные операции
    - Поступления (CREDIT) - приходные операции

    Использование:
        config = ODataSyncConfig(
            base_url="http://server:port/base/odata/standard.odata",
            username="username",
            password="password"
        )
        sync = ODataBankTransactionSync(db, config)
        result = sync.sync_transactions(
            department_id=1,
            date_from=date(2025, 1, 1),
            date_to=date(2025, 1, 31)
        )
    """

    def __init__(self, db: Session, config: ODataSyncConfig):
        self.db = db
        self.config = config

    def sync_transactions(
        self,
        department_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Синхронизация банковских транзакций из 1С

        Args:
            department_id: ID отдела (обязательно для multi-tenancy)
            date_from: Дата начала периода
            date_to: Дата окончания периода
            organization_id: ID организации (для фильтрации)

        Returns:
            Dict с результатами синхронизации:
            {
                'success': True/False,
                'total_fetched': 150,
                'created': 120,
                'updated': 30,
                'skipped': 0,
                'errors': []
            }
        """
        try:
            # Validate department
            department = self.db.query(Department).filter(Department.id == department_id).first()
            if not department:
                return {
                    'success': False,
                    'error': f'Department with id {department_id} not found',
                    'total_fetched': 0,
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'errors': []
                }

            # Fetch data from 1C OData
            transactions_data = self._fetch_from_odata(date_from, date_to, organization_id)

            if not transactions_data:
                return {
                    'success': True,
                    'total_fetched': 0,
                    'created': 0,
                    'updated': 0,
                    'skipped': 0,
                    'errors': [],
                    'message': 'No transactions found in 1C for specified period'
                }

            # Process transactions
            result = self._process_transactions(
                transactions_data,
                department_id,
                organization_id
            )

            return result

        except Exception as e:
            logger.error(f"OData sync failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total_fetched': 0,
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': []
            }

    def _fetch_from_odata(
        self,
        date_from: Optional[date],
        date_to: Optional[date],
        organization_id: Optional[int]
    ) -> List[Dict[str, Any]]:
        """
        Получить данные из 1С через OData

        Запрос к 1С:
        GET /odata/standard.odata/Document_BankStatement?$format=json
            &$filter=Date ge datetime'2025-01-01' and Date le datetime'2025-01-31'
            &$orderby=Date desc
        """
        try:
            # Build OData filter
            filters = []
            if date_from:
                filters.append(f"Date ge datetime'{date_from.isoformat()}'")
            if date_to:
                filters.append(f"Date le datetime'{date_to.isoformat()}'")

            # Build URL
            url = f"{self.config.base_url}/{self.config.entity_name}"
            params = {
                '$format': 'json',
                '$orderby': 'Date desc',
            }

            if filters:
                params['$filter'] = ' and '.join(filters)

            logger.info(f"Fetching from OData: {url} with params: {params}")

            # Make request
            response = requests.get(
                url,
                params=params,
                auth=self.config.auth,
                timeout=self.config.timeout,
                headers={'Accept': 'application/json'}
            )

            response.raise_for_status()

            data = response.json()

            # OData обычно возвращает данные в поле 'value'
            items = data.get('value', [])

            logger.info(f"Fetched {len(items)} transactions from 1C OData")

            return items

        except requests.RequestException as e:
            logger.error(f"OData request failed: {e}", exc_info=True)
            raise Exception(f"Failed to fetch data from 1C: {e}")

    def _process_transactions(
        self,
        transactions_data: List[Dict[str, Any]],
        department_id: int,
        organization_id: Optional[int]
    ) -> Dict[str, Any]:
        """
        Обработка и сохранение транзакций
        """
        created_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        for idx, tx_data in enumerate(transactions_data):
            try:
                # Parse transaction data from 1C format
                parsed = self._parse_transaction_data(tx_data, department_id, organization_id)

                if not parsed:
                    skipped_count += 1
                    continue

                # Check if transaction exists (by external_id_1c)
                external_id = parsed.get('external_id_1c')
                existing = None

                if external_id:
                    existing = self.db.query(BankTransaction).filter(
                        BankTransaction.external_id_1c == external_id
                    ).first()

                if existing:
                    # Update existing transaction
                    self._update_transaction(existing, parsed)
                    updated_count += 1
                else:
                    # Create new transaction
                    new_tx = BankTransaction(**parsed)
                    self.db.add(new_tx)
                    created_count += 1

                # Commit every 100 records to avoid memory issues
                if (idx + 1) % 100 == 0:
                    self.db.commit()
                    logger.info(f"Processed {idx + 1} transactions...")

            except Exception as e:
                logger.error(f"Failed to process transaction {idx}: {e}", exc_info=True)
                errors.append({
                    'index': idx,
                    'error': str(e),
                    'data': tx_data
                })
                skipped_count += 1

        # Final commit
        try:
            self.db.commit()
            logger.info(f"Sync completed: created={created_count}, updated={updated_count}, skipped={skipped_count}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to commit transactions: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to commit: {e}',
                'total_fetched': len(transactions_data),
                'created': 0,
                'updated': 0,
                'skipped': len(transactions_data),
                'errors': errors
            }

        return {
            'success': True,
            'total_fetched': len(transactions_data),
            'created': created_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'errors': errors
        }

    def _parse_transaction_data(
        self,
        tx_data: Dict[str, Any],
        department_id: int,
        organization_id: Optional[int]
    ) -> Optional[Dict[str, Any]]:
        """
        Парсинг данных транзакции из формата 1С OData

        Типичная структура данных из 1С:
        {
            "Ref_Key": "guid-string",
            "Date": "2025-01-15T00:00:00",
            "Number": "000001",
            "Amount": 150000.00,
            "OperationType": "Списание" / "Поступление",
            "Counterparty": "ООО Поставщик",
            "CounterpartyINN": "7727563778",
            "CounterpartyKPP": "772701001",
            "CounterpartyAccount": "40702810100000000001",
            "CounterpartyBank": "ПАО Сбербанк",
            "CounterpartyBIK": "044525225",
            "PaymentPurpose": "Оплата по договору №123 от 01.01.2025",
            "Organization_Key": "guid-string",
            "Account": "40702810100000000002",
            ...
        }
        """
        try:
            # External ID (уникальный идентификатор из 1С)
            external_id = tx_data.get('Ref_Key') or tx_data.get('Number')
            if not external_id:
                logger.warning(f"Transaction has no Ref_Key or Number, skipping: {tx_data}")
                return None

            # Transaction date
            date_str = tx_data.get('Date')
            if not date_str:
                logger.warning(f"Transaction has no Date, skipping: {tx_data}")
                return None

            transaction_date = self._parse_date(date_str)

            # Amount
            amount = Decimal(str(tx_data.get('Amount', 0)))
            if amount <= 0:
                logger.warning(f"Transaction has invalid amount: {amount}, skipping")
                return None

            # Transaction type (DEBIT or CREDIT)
            operation_type = tx_data.get('OperationType', '').lower()
            if 'списан' in operation_type or 'debit' in operation_type or 'расход' in operation_type:
                transaction_type = BankTransactionTypeEnum.DEBIT
            elif 'поступ' in operation_type or 'credit' in operation_type or 'приход' in operation_type:
                transaction_type = BankTransactionTypeEnum.CREDIT
            else:
                # По умолчанию - списание
                transaction_type = BankTransactionTypeEnum.DEBIT

            # Counterparty info
            counterparty_name = tx_data.get('Counterparty') or tx_data.get('CounterpartyName')
            counterparty_inn = tx_data.get('CounterpartyINN') or tx_data.get('INN')
            counterparty_kpp = tx_data.get('CounterpartyKPP') or tx_data.get('KPP')
            counterparty_account = tx_data.get('CounterpartyAccount') or tx_data.get('Account')
            counterparty_bank = tx_data.get('CounterpartyBank') or tx_data.get('Bank')
            counterparty_bik = tx_data.get('CounterpartyBIK') or tx_data.get('BIK')

            # Payment purpose
            payment_purpose = tx_data.get('PaymentPurpose') or tx_data.get('Purpose')

            # Document info
            document_number = tx_data.get('Number')
            document_date_str = tx_data.get('DocumentDate') or tx_data.get('Date')
            document_date = self._parse_date(document_date_str) if document_date_str else transaction_date

            # Organization (наша организация)
            org_id = organization_id
            if not org_id and tx_data.get('Organization_Key'):
                # Попытаться найти организацию по external_id из 1С
                org = self.db.query(Organization).filter(
                    Organization.department_id == department_id
                ).first()
                if org:
                    org_id = org.id

            # Account number (наш счет)
            account_number = tx_data.get('Account') or tx_data.get('BankAccount')

            # Build transaction dict
            parsed = {
                'external_id_1c': str(external_id),
                'transaction_date': transaction_date,
                'amount': amount,
                'transaction_type': transaction_type,
                'counterparty_name': counterparty_name,
                'counterparty_inn': counterparty_inn,
                'counterparty_kpp': counterparty_kpp,
                'counterparty_account': counterparty_account,
                'counterparty_bank': counterparty_bank,
                'counterparty_bik': counterparty_bik,
                'payment_purpose': payment_purpose,
                'organization_id': org_id,
                'account_number': account_number,
                'document_number': document_number,
                'document_date': document_date,
                'department_id': department_id,
                'import_source': 'ODATA_1C',
                'imported_at': datetime.utcnow(),
                'status': BankTransactionStatusEnum.NEW,
                'is_active': True,
            }

            # Extract month/year from transaction date
            if transaction_date:
                parsed['transaction_month'] = transaction_date.month
                parsed['transaction_year'] = transaction_date.year

            return parsed

        except Exception as e:
            logger.error(f"Failed to parse transaction data: {e}", exc_info=True)
            return None

    def _update_transaction(self, existing: BankTransaction, parsed: Dict[str, Any]):
        """
        Обновление существующей транзакции

        Обновляем только если данные изменились
        """
        fields_to_update = [
            'transaction_date',
            'amount',
            'transaction_type',
            'counterparty_name',
            'counterparty_inn',
            'counterparty_kpp',
            'counterparty_account',
            'counterparty_bank',
            'counterparty_bik',
            'payment_purpose',
            'organization_id',
            'account_number',
            'document_number',
            'document_date',
            'transaction_month',
            'transaction_year',
        ]

        updated = False
        for field in fields_to_update:
            if field in parsed:
                current_value = getattr(existing, field)
                new_value = parsed[field]

                # Compare values (handle Decimal/date comparison)
                if current_value != new_value:
                    setattr(existing, field, new_value)
                    updated = True

        if updated:
            existing.updated_at = datetime.utcnow()
            logger.debug(f"Updated transaction {existing.id} (external_id: {existing.external_id_1c})")

    def _parse_date(self, date_str: str) -> date:
        """
        Парсинг даты из различных форматов 1С

        Поддерживаемые форматы:
        - ISO 8601: "2025-01-15T00:00:00"
        - OData: "2025-01-15T00:00:00Z"
        - Date only: "2025-01-15"
        """
        if not date_str:
            return None

        # Remove timezone info if present
        date_str = date_str.split('T')[0] if 'T' in date_str else date_str

        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            # Try other formats
            for fmt in ['%d.%m.%Y', '%Y/%m/%d', '%d/%m/%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def test_connection(self) -> Dict[str, Any]:
        """
        Тестирование подключения к 1С OData

        Returns:
            {
                'success': True/False,
                'message': 'Connection successful',
                'server_info': {...}
            }
        """
        try:
            url = f"{self.config.base_url}/$metadata"

            response = requests.get(
                url,
                auth=self.config.auth,
                timeout=self.config.timeout
            )

            response.raise_for_status()

            return {
                'success': True,
                'message': 'Connection successful',
                'status_code': response.status_code,
                'url': url
            }

        except requests.RequestException as e:
            return {
                'success': False,
                'message': f'Connection failed: {e}',
                'error': str(e)
            }
