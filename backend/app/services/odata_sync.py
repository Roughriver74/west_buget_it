"""
OData Sync Service for 1C Integration
Синхронизация банковских операций из 1С через OData протокол

ОБНОВЛЕНО: Использует правильные документы из 1С:
- Document_ПоступлениеБезналичныхДенежныхСредств (поступления)
- Document_СписаниеБезналичныхДенежныхСредств (списания)
"""
import logging
from typing import Dict, Any, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.services.odata_1c_client import OData1CClient
from app.services.bank_transaction_1c_import import (
    BankTransaction1CImporter,
    BankTransaction1CImportResult
)

logger = logging.getLogger(__name__)


# Backward compatibility
class ODataSyncConfig:
    """Configuration for OData connection to 1C"""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        entity_name: str = "Document_BankStatement",  # Deprecated, not used
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.entity_name = entity_name  # Deprecated
        self.timeout = timeout


class ODataBankTransactionSync:
    """
    Service for syncing bank transactions from 1C via OData

    Использует правильные документы из 1С:
    - Поступления: Document_ПоступлениеБезналичныхДенежныхСредств
    - Списания: Document_СписаниеБезналичныхДенежныхСредств

    Парсинг данных из поля "ДанныеВыписки" с деталями платежа.
    """

    def __init__(self, db: Session, config: ODataSyncConfig):
        self.db = db
        self.config = config

        # Create 1C OData client
        self.odata_client = OData1CClient(
            base_url=config.base_url,
            username=config.username,
            password=config.password
        )

    def sync_transactions(
        self,
        department_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        organization_id: Optional[int] = None,  # Deprecated, not used
        auto_classify: bool = True,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Синхронизация банковских транзакций из 1С

        Args:
            department_id: ID отдела (обязательно для multi-tenancy)
            date_from: Дата начала периода
            date_to: Дата окончания периода
            organization_id: Deprecated, not used
            auto_classify: Применять AI классификацию автоматически
            batch_size: Размер батча для запроса к 1С

        Returns:
            Dict с результатами синхронизации
        """
        if not date_from or not date_to:
            return {
                'success': False,
                'error': 'date_from and date_to are required',
                'total_fetched': 0,
                'total_processed': 0,
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'auto_categorized': 0,
                'errors': []
            }

        try:
            # Create importer
            importer = BankTransaction1CImporter(
                db=self.db,
                odata_client=self.odata_client,
                department_id=department_id,
                auto_classify=auto_classify
            )

            # Import transactions
            result: BankTransaction1CImportResult = importer.import_transactions(
                date_from=date_from,
                date_to=date_to,
                batch_size=batch_size
            )

            # Convert to dict format
            result_dict = {
                'success': len(result.errors) == 0,
                'total_fetched': result.total_fetched,
                'total_processed': result.total_processed,
                'created': result.total_created,
                'updated': result.total_updated,
                'skipped': result.total_skipped,
                'auto_categorized': result.auto_categorized,
                'errors': result.errors
            }

            if result.errors:
                result_dict['message'] = f"Completed with {len(result.errors)} errors"
            else:
                result_dict['message'] = "Sync completed successfully"

            return result_dict

        except Exception as e:
            logger.error(f"OData sync failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'total_fetched': 0,
                'total_processed': 0,
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'auto_categorized': 0,
                'errors': [str(e)]
            }

    def test_connection(self) -> Dict[str, Any]:
        """
        Тестирование подключения к 1С OData

        Returns:
            {
                'success': True/False,
                'message': 'Connection successful',
                'status_code': 200,
                'url': '...'
            }
        """
        try:
            success = self.odata_client.test_connection()

            if success:
                return {
                    'success': True,
                    'message': 'Connection successful',
                    'status_code': 200,
                    'url': self.config.base_url
                }
            else:
                return {
                    'success': False,
                    'message': 'Connection failed',
                    'error': 'Authentication or connection error'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Connection failed: {e}',
                'error': str(e)
            }
