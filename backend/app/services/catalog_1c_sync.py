"""
1C Catalog Synchronization Service

Синхронизация справочников из 1С:
- Catalog_Организации → Organizations
- Catalog_СтатьиДвиженияДенежныхСредств → BudgetCategories
"""

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models import Organization, BudgetCategory, ExpenseTypeEnum, Department
from app.services.odata_1c_client import OData1CClient

logger = logging.getLogger(__name__)


@dataclass
class CatalogSyncResult:
    """Результат синхронизации справочника"""
    total_fetched: int = 0
    total_processed: int = 0
    total_created: int = 0
    total_updated: int = 0
    total_skipped: int = 0
    errors: List[str] = None
    success: bool = True

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_fetched': self.total_fetched,
            'total_processed': self.total_processed,
            'total_created': self.total_created,
            'total_updated': self.total_updated,
            'total_skipped': self.total_skipped,
            'errors': self.errors,
            'success': self.success
        }


class OrganizationSync:
    """Синхронизация справочника Организации"""

    def __init__(self, db: Session, odata_client: OData1CClient):
        self.db = db
        self.odata_client = odata_client

    def sync_organizations(
        self,
        batch_size: int = 100,
        department_id: Optional[int] = None
    ) -> CatalogSyncResult:
        """
        Синхронизировать организации из 1С

        Args:
            batch_size: Размер батча для пагинации
            department_id: ID отдела (опционально, для tracking)

        Returns:
            Результат синхронизации
        """
        result = CatalogSyncResult()
        skip = 0

        try:
            logger.info("Starting organizations synchronization from 1C")

            while True:
                # Fetch batch from 1C
                orgs_1c = self.odata_client.get_organizations(
                    top=batch_size,
                    skip=skip
                )

                if not orgs_1c:
                    break

                result.total_fetched += len(orgs_1c)

                # Process each organization
                for org_data in orgs_1c:
                    try:
                        self._process_organization(org_data, department_id, result)
                    except Exception as e:
                        error_msg = f"Failed to process organization {org_data.get('Ref_Key')}: {str(e)}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)

                # Commit batch
                self.db.commit()
                logger.info(f"Processed batch: {len(orgs_1c)} organizations (skip={skip})")

                # Check if we should continue
                if len(orgs_1c) < batch_size:
                    break

                skip += batch_size

            logger.info(f"Organizations sync completed: {result.to_dict()}")
            return result

        except Exception as e:
            self.db.rollback()
            error_msg = f"Organizations sync failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
            return result

    def _process_organization(
        self,
        org_data: Dict[str, Any],
        department_id: Optional[int],
        result: CatalogSyncResult
    ):
        """Обработать одну организацию из 1С"""
        external_id = org_data.get('Ref_Key')

        if not external_id or external_id == '00000000-0000-0000-0000-000000000000':
            result.total_skipped += 1
            return

        # Пропустить удаленные
        if org_data.get('DeletionMark', False):
            result.total_skipped += 1
            return

        # Check if organization already exists
        existing_org = self.db.query(Organization).filter_by(external_id_1c=external_id).first()

        description = org_data.get('Description', '')
        inn = org_data.get('ИНН', '')
        kpp = org_data.get('КПП', '')

        # Skip if no meaningful data
        if not description and not inn:
            result.total_skipped += 1
            return

        if existing_org:
            # Update existing
            self._update_organization(existing_org, org_data)
            result.total_updated += 1
            logger.debug(f"Updated organization: {description}")
        else:
            # Create new
            self._create_organization(org_data, department_id)
            result.total_created += 1
            logger.debug(f"Created organization: {description}")

        result.total_processed += 1

    def _create_organization(self, org_data: Dict[str, Any], department_id: Optional[int]) -> Organization:
        """Создать новую организацию"""
        description = org_data.get('Description', '')
        short_name = org_data.get('НаименованиеСокращенное', description)
        full_name = org_data.get('НаименованиеПолное', description)

        org = Organization(
            name=description or short_name or full_name,
            external_id_1c=org_data.get('Ref_Key'),
            full_name=full_name,
            short_name=short_name,
            inn=org_data.get('ИНН', ''),
            kpp=org_data.get('КПП', ''),
            ogrn=org_data.get('ОГРН', ''),
            prefix=org_data.get('Префикс', ''),
            okpo=org_data.get('КодПоОКПО', ''),
            status_1c=org_data.get('Статус', ''),
            department_id=department_id,
            is_active=not org_data.get('DeletionMark', False)
        )

        self.db.add(org)
        return org

    def _update_organization(self, org: Organization, org_data: Dict[str, Any]):
        """Обновить существующую организацию"""
        description = org_data.get('Description', '')
        short_name = org_data.get('НаименованиеСокращенное', description)
        full_name = org_data.get('НаименованиеПолное', description)

        org.name = description or short_name or full_name
        org.full_name = full_name
        org.short_name = short_name
        org.inn = org_data.get('ИНН', '')
        org.kpp = org_data.get('КПП', '')
        org.ogrn = org_data.get('ОГРН', '')
        org.prefix = org_data.get('Префикс', '')
        org.okpo = org_data.get('КодПоОКПО', '')
        org.status_1c = org_data.get('Статус', '')
        org.is_active = not org_data.get('DeletionMark', False)
        org.updated_at = datetime.utcnow()


class BudgetCategorySync:
    """Синхронизация справочника Статьи движения денежных средств"""

    def __init__(self, db: Session, odata_client: OData1CClient, department_id: int):
        self.db = db
        self.odata_client = odata_client
        self.department_id = department_id

    def sync_categories(
        self,
        batch_size: int = 100,
        default_type: ExpenseTypeEnum = ExpenseTypeEnum.OPEX
    ) -> CatalogSyncResult:
        """
        Синхронизировать категории из 1С

        Args:
            batch_size: Размер батча для пагинации
            default_type: Тип расхода по умолчанию (OPEX/CAPEX)

        Returns:
            Результат синхронизации
        """
        result = CatalogSyncResult()
        skip = 0

        # Mapping for parent_id resolution
        ref_key_to_db_id: Dict[str, int] = {}

        try:
            logger.info(f"Starting budget categories sync from 1C for department_id={self.department_id}")

            # First pass: create/update all categories
            while True:
                categories_1c = self.odata_client.get_cash_flow_categories(
                    top=batch_size,
                    skip=skip,
                    include_folders=True
                )

                if not categories_1c:
                    break

                result.total_fetched += len(categories_1c)

                # Process each category
                for cat_data in categories_1c:
                    try:
                        db_id = self._process_category(cat_data, default_type, result)
                        if db_id:
                            ref_key_to_db_id[cat_data.get('Ref_Key')] = db_id
                    except Exception as e:
                        error_msg = f"Failed to process category {cat_data.get('Ref_Key')}: {str(e)}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)

                # Commit batch
                self.db.commit()
                logger.info(f"Processed batch: {len(categories_1c)} categories (skip={skip})")

                if len(categories_1c) < batch_size:
                    break

                skip += batch_size

            # Second pass: update parent_id relationships
            self._update_parent_relationships(ref_key_to_db_id)
            self.db.commit()

            logger.info(f"Budget categories sync completed: {result.to_dict()}")
            return result

        except Exception as e:
            self.db.rollback()
            error_msg = f"Budget categories sync failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            result.success = False
            return result

    def _process_category(
        self,
        cat_data: Dict[str, Any],
        default_type: ExpenseTypeEnum,
        result: CatalogSyncResult
    ) -> Optional[int]:
        """Обработать одну категорию из 1С"""
        external_id = cat_data.get('Ref_Key')

        if not external_id or external_id == '00000000-0000-0000-0000-000000000000':
            result.total_skipped += 1
            return None

        # Пропустить удаленные
        if cat_data.get('DeletionMark', False):
            result.total_skipped += 1
            return None

        # Check if category already exists
        existing_cat = self.db.query(BudgetCategory).filter_by(
            external_id_1c=external_id,
            department_id=self.department_id
        ).first()

        description = cat_data.get('Description', '')

        if not description:
            result.total_skipped += 1
            return None

        if existing_cat:
            # Update existing
            self._update_category(existing_cat, cat_data)
            result.total_updated += 1
            logger.debug(f"Updated category: {description}")
            return existing_cat.id
        else:
            # Create new
            new_cat = self._create_category(cat_data, default_type)
            result.total_created += 1
            logger.debug(f"Created category: {description}")
            return new_cat.id

        result.total_processed += 1

    def _create_category(
        self,
        cat_data: Dict[str, Any],
        default_type: ExpenseTypeEnum
    ) -> BudgetCategory:
        """Создать новую категорию"""
        description = cat_data.get('Description', '')
        is_folder = cat_data.get('IsFolder', False)

        # Determine expense type
        # You can customize this logic based on category name or other fields
        expense_type = default_type

        cat = BudgetCategory(
            name=description,
            type=expense_type,
            external_id_1c=cat_data.get('Ref_Key'),
            code_1c=cat_data.get('Code', ''),
            is_folder=is_folder,
            order_index=self._parse_order_index(cat_data.get('РеквизитДопУпорядочивания')),
            department_id=self.department_id,
            is_active=not cat_data.get('DeletionMark', False)
        )

        self.db.add(cat)
        self.db.flush()  # To get the ID
        return cat

    def _update_category(self, cat: BudgetCategory, cat_data: Dict[str, Any]):
        """Обновить существующую категорию"""
        cat.name = cat_data.get('Description', '')
        cat.code_1c = cat_data.get('Code', '')
        cat.is_folder = cat_data.get('IsFolder', False)
        cat.order_index = self._parse_order_index(cat_data.get('РеквизитДопУпорядочивания'))
        cat.is_active = not cat_data.get('DeletionMark', False)
        cat.updated_at = datetime.utcnow()

    def _update_parent_relationships(self, ref_key_to_db_id: Dict[str, int]):
        """Обновить parent_id связи после создания всех категорий"""
        logger.info("Updating parent relationships...")

        categories = self.db.query(BudgetCategory).filter_by(
            department_id=self.department_id
        ).filter(
            BudgetCategory.external_id_1c.isnot(None)
        ).all()

        for cat in categories:
            # Fetch from 1C to get Parent_Key
            try:
                cat_1c = self.odata_client._make_request(
                    method='GET',
                    endpoint=f"Catalog_СтатьиДвиженияДенежныхСредств(guid'{cat.external_id_1c}')",
                    params={'$format': 'json'}
                )

                parent_key = cat_1c.get('Parent_Key')

                if parent_key and parent_key != '00000000-0000-0000-0000-000000000000':
                    # Find parent in our DB
                    parent_db_id = ref_key_to_db_id.get(parent_key)
                    if parent_db_id:
                        cat.parent_id = parent_db_id
                        logger.debug(f"Set parent for {cat.name}: {parent_db_id}")

            except Exception as e:
                logger.warning(f"Failed to update parent for category {cat.external_id_1c}: {e}")

    def _parse_order_index(self, value: Any) -> Optional[int]:
        """Преобразовать РеквизитДопУпорядочивания в int"""
        if value is None:
            return None

        try:
            return int(value)
        except (ValueError, TypeError):
            return None


def sync_all_catalogs_from_1c(
    db: Session,
    odata_client: OData1CClient,
    department_id: int,
    sync_organizations: bool = True,
    sync_categories: bool = True
) -> Dict[str, CatalogSyncResult]:
    """
    Синхронизировать все справочники из 1С

    Args:
        db: Database session
        odata_client: OData client
        department_id: Department ID for categories (organizations are shared)
        sync_organizations: Синхронизировать организации
        sync_categories: Синхронизировать категории

    Returns:
        Dictionary with sync results
    """
    results = {}

    if sync_organizations:
        logger.info("Syncing organizations...")
        org_sync = OrganizationSync(db, odata_client)
        results['organizations'] = org_sync.sync_organizations(department_id=department_id)

    if sync_categories:
        logger.info("Syncing budget categories...")
        cat_sync = BudgetCategorySync(db, odata_client, department_id)
        results['budget_categories'] = cat_sync.sync_categories()

    return results
