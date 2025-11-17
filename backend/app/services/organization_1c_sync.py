"""
Organization 1C Synchronization Service

Сервис для синхронизации организаций из 1С через OData API
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import Organization
from app.services.odata_1c_client import OData1CClient

logger = logging.getLogger(__name__)


@dataclass
class Organization1CSyncResult:
    """Результат синхронизации организаций"""
    success: bool
    total_fetched: int
    total_processed: int
    total_created: int
    total_updated: int
    total_skipped: int
    errors: List[str]
    message: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dict for API response"""
        return {
            "success": self.success,
            "statistics": {
                "total_fetched": self.total_fetched,
                "total_processed": self.total_processed,
                "total_created": self.total_created,
                "total_updated": self.total_updated,
                "total_skipped": self.total_skipped,
                "errors": self.errors,
            },
            "message": self.message,
        }


class Organization1CSync:
    """Сервис синхронизации организаций из 1С"""

    def __init__(
        self,
        db: Session,
        odata_client: OData1CClient,
    ):
        """
        Инициализация сервиса синхронизации

        Args:
            db: Database session
            odata_client: 1C OData client
        """
        self.db = db
        self.odata_client = odata_client

    def sync_organizations(
        self,
        batch_size: int = 100
    ) -> Organization1CSyncResult:
        """
        Синхронизировать организации из 1С

        Args:
            batch_size: Размер батча для пагинации

        Returns:
            Organization1CSyncResult с результатами синхронизации
        """
        logger.info("Starting 1C organizations sync")

        total_fetched = 0
        total_processed = 0
        total_created = 0
        total_updated = 0
        total_skipped = 0
        errors = []

        try:
            # Получить организации из 1С (с пагинацией)
            skip = 0
            while True:
                logger.info(f"Fetching batch: skip={skip}, top={batch_size}")

                try:
                    batch = self.odata_client.get_organizations(
                        top=batch_size,
                        skip=skip
                    )
                except Exception as e:
                    error_msg = f"Failed to fetch organizations from 1C: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    break

                if not batch:
                    logger.info("No more organizations to fetch")
                    break

                total_fetched += len(batch)
                logger.info(f"Fetched {len(batch)} organizations in current batch")

                # Обработать каждую организацию
                for org_data in batch:
                    try:
                        result = self._process_organization(org_data)
                        total_processed += 1

                        if result == "created":
                            total_created += 1
                        elif result == "updated":
                            total_updated += 1
                        elif result == "skipped":
                            total_skipped += 1

                    except Exception as e:
                        error_msg = f"Error processing organization {org_data.get('Description', 'N/A')}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)

                # Коммит после каждого батча
                try:
                    self.db.commit()
                    logger.info(f"Committed batch of {len(batch)} organizations")
                except Exception as e:
                    self.db.rollback()
                    error_msg = f"Failed to commit batch: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    break

                skip += batch_size

                # Защита от бесконечного цикла
                if skip > 10000:
                    logger.warning("Reached max iterations (10000 records), stopping")
                    break

            success = total_processed > 0 and len(errors) == 0
            message = f"Sync completed: {total_created} created, {total_updated} updated, {total_skipped} skipped"

            logger.info(message)

            return Organization1CSyncResult(
                success=success,
                total_fetched=total_fetched,
                total_processed=total_processed,
                total_created=total_created,
                total_updated=total_updated,
                total_skipped=total_skipped,
                errors=errors,
                message=message,
            )

        except Exception as e:
            error_msg = f"Fatal error during sync: {str(e)}"
            logger.error(error_msg)
            self.db.rollback()
            return Organization1CSyncResult(
                success=False,
                total_fetched=total_fetched,
                total_processed=total_processed,
                total_created=total_created,
                total_updated=total_updated,
                total_skipped=total_skipped,
                errors=errors + [error_msg],
                message="Sync failed with errors",
            )

    def _process_organization(self, org_data: Dict[str, Any]) -> str:
        """
        Обработать одну организацию из 1С

        Args:
            org_data: Данные организации из 1С

        Returns:
            "created", "updated", or "skipped"
        """
        # Маппинг полей 1С → Organization
        ref_key = org_data.get("Ref_Key")
        if not ref_key or ref_key == "00000000-0000-0000-0000-000000000000":
            logger.warning("Skipping organization with empty Ref_Key")
            return "skipped"

        # Извлечь данные из 1С
        name = org_data.get("Description") or org_data.get("Наименование")
        inn = org_data.get("ИНН")
        kpp = org_data.get("КПП")

        if not name:
            logger.warning(f"Skipping organization {ref_key} without name")
            return "skipped"

        # Проверить, существует ли организация с таким external_id_1c
        existing = self.db.query(Organization).filter(
            Organization.external_id_1c == ref_key
        ).first()

        if existing:
            # Обновить существующую организацию
            updated = False

            if name and existing.name != name:
                existing.name = name
                updated = True

            if inn and existing.inn != inn:
                existing.inn = inn
                updated = True

            if kpp and existing.kpp != kpp:
                existing.kpp = kpp
                updated = True

            # Синхронизация обновлена
            existing.synced_at = datetime.utcnow()

            if updated:
                logger.info(f"Updated organization: {name} (INN: {inn})")
                return "updated"
            else:
                logger.debug(f"Organization unchanged: {name}")
                return "skipped"

        else:
            # Создать новую организацию
            new_org = Organization(
                name=name,
                short_name=name[:100] if name else None,  # Используем name как short_name
                inn=inn,
                kpp=kpp,
                external_id_1c=ref_key,
                is_active=True,
                synced_at=datetime.utcnow(),
            )

            self.db.add(new_org)
            logger.info(f"Created new organization: {name} (INN: {inn})")
            return "created"
