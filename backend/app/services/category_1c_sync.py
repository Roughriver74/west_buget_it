"""
Budget Category 1C Synchronization Service

Сервис для синхронизации статей расходов из 1С через OData API
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.models import BudgetCategory, ExpenseTypeEnum
from app.services.odata_1c_client import OData1CClient

logger = logging.getLogger(__name__)


@dataclass
class Category1CSyncResult:
    """Результат синхронизации категорий"""
    success: bool
    total_fetched: int
    total_processed: int
    total_created: int
    total_updated: int
    total_unchanged: int  # Категории без изменений
    total_skipped: int    # Пропущено из-за проблем
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
                "total_unchanged": self.total_unchanged,
                "total_skipped": self.total_skipped,
                "errors": self.errors,
            },
            "message": self.message,
        }


class Category1CSync:
    """Сервис синхронизации категорий бюджета из 1С"""

    def __init__(
        self,
        db: Session,
        odata_client: OData1CClient,
        department_id: int,
    ):
        """
        Инициализация сервиса синхронизации

        Args:
            db: Database session
            odata_client: 1C OData client
            department_id: ID отдела для создания категорий
        """
        self.db = db
        self.odata_client = odata_client
        self.department_id = department_id

    def sync_categories(
        self,
        batch_size: int = 1000,
        include_folders: bool = True  # Включаем папки по умолчанию
    ) -> Category1CSyncResult:
        """
        Синхронизировать категории бюджета из 1С с иерархической структурой

        Процесс:
        1. Загрузить ВСЕ категории из 1С (включая папки)
        2. Первый проход: создать/обновить все категории (без parent_id)
        3. Второй проход: установить parent_id связи

        Args:
            batch_size: Размер батча для пагинации (default 1000)
            include_folders: Включать ли папки (группы) в синхронизацию

        Returns:
            Category1CSyncResult с результатами синхронизации
        """
        logger.info(f"Starting 1C cash flow categories sync for department {self.department_id}")

        total_fetched = 0
        total_processed = 0
        total_created = 0
        total_updated = 0
        total_unchanged = 0  # Без изменений
        total_skipped = 0    # Пропущено из-за проблем
        errors = []

        # Хранилище для всех категорий (для установки parent_id на втором проходе)
        all_categories_data = []

        try:
            # ================== ФАЗА 1: Загрузка ВСЕХ категорий из 1С ==================
            logger.info("Phase 1: Fetching ALL categories from 1C...")
            skip = 0
            while True:
                logger.info(f"Fetching batch: skip={skip}, top={batch_size}")

                try:
                    batch = self.odata_client.get_cash_flow_categories(
                        top=batch_size,
                        skip=skip,
                        include_folders=include_folders
                    )
                except Exception as e:
                    error_msg = f"Failed to fetch categories from 1C: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    break

                if not batch:
                    logger.info("No more categories to fetch")
                    break

                total_fetched += len(batch)
                all_categories_data.extend(batch)
                logger.info(f"Fetched {len(batch)} categories in current batch (total: {total_fetched})")

                skip += batch_size

                # Проверка на окончание
                if len(batch) < batch_size:
                    logger.info("Last batch received (smaller than batch_size)")
                    break

                # Защита от бесконечного цикла
                if skip > 10000:
                    logger.warning("Reached max iterations (10000 records), stopping")
                    break

            logger.info(f"✅ Fetched total {total_fetched} categories from 1C")

            # ================== ФАЗА 2: Создание/обновление категорий (БЕЗ parent_id) ==================
            logger.info("Phase 2: Creating/updating categories (without parent_id)...")

            # Обрабатываем и коммитим батчами для избежания UniqueViolation
            batch_size_commit = 50
            for i, cat_data in enumerate(all_categories_data):
                try:
                    result = self._process_category(cat_data)
                    total_processed += 1

                    if result == "created":
                        total_created += 1
                    elif result == "updated":
                        total_updated += 1
                    elif result == "unchanged":
                        total_unchanged += 1
                    elif result == "skipped":
                        total_skipped += 1

                    # Flush каждые N записей для освобождения памяти
                    if (i + 1) % batch_size_commit == 0:
                        try:
                            self.db.flush()
                            logger.debug(f"Flushed {i + 1} categories")
                        except Exception as e:
                            logger.warning(f"Flush warning at {i + 1}: {e}")
                            self.db.rollback()

                except Exception as e:
                    error_msg = f"Error processing category {cat_data.get('Description', 'N/A')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Коммит после первого прохода
            try:
                self.db.commit()
                logger.info(f"✅ Committed phase 2: {total_created} created, {total_updated} updated")
            except Exception as e:
                self.db.rollback()
                error_msg = f"Failed to commit phase 2: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                # Не прерываем, продолжаем

            # ================== ФАЗА 3: Установка parent_id связей ==================
            logger.info("Phase 3: Setting parent_id relationships...")

            parent_links_set = 0
            for cat_data in all_categories_data:
                try:
                    if self._set_parent_relationship(cat_data):
                        parent_links_set += 1
                except Exception as e:
                    error_msg = f"Error setting parent for {cat_data.get('Description', 'N/A')}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            # Коммит после второго прохода
            try:
                self.db.commit()
                logger.info(f"✅ Committed phase 3: {parent_links_set} parent relationships set")
            except Exception as e:
                self.db.rollback()
                error_msg = f"Failed to commit phase 3: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

            success = total_processed > 0 and len(errors) == 0
            message = f"Sync completed: {total_created} created, {total_updated} updated, {total_unchanged} unchanged, {total_skipped} skipped, {parent_links_set} parent links"

            logger.info(message)

            return Category1CSyncResult(
                success=success,
                total_fetched=total_fetched,
                total_processed=total_processed,
                total_created=total_created,
                total_updated=total_updated,
                total_unchanged=total_unchanged,
                total_skipped=total_skipped,
                errors=errors,
                message=message,
            )

        except Exception as e:
            error_msg = f"Fatal error during sync: {str(e)}"
            logger.error(error_msg)
            self.db.rollback()
            return Category1CSyncResult(
                success=False,
                total_fetched=total_fetched,
                total_processed=total_processed,
                total_created=total_created,
                total_updated=total_updated,
                total_unchanged=total_unchanged,
                total_skipped=total_skipped,
                errors=errors + [error_msg],
                message="Sync failed with errors",
            )

    def _process_category(self, cat_data: Dict[str, Any]) -> str:
        """
        Обработать одну категорию из 1С (создание/обновление без parent_id)

        Args:
            cat_data: Данные категории из 1С

        Returns:
            "created", "updated", "unchanged", or "skipped"
        """
        # Маппинг полей 1С → BudgetCategory
        ref_key = cat_data.get("Ref_Key")
        if not ref_key or ref_key == "00000000-0000-0000-0000-000000000000":
            logger.warning(f"Skipping category with empty Ref_Key (Code: {cat_data.get('Code', 'N/A')})")
            return "skipped"

        # Извлечь данные из 1С
        name = cat_data.get("Description") or cat_data.get("Наименование")
        code = cat_data.get("Code") or cat_data.get("Код")
        is_folder = cat_data.get("IsFolder", False)
        order_index = cat_data.get("РеквизитДопУпорядочивания")  # Сортировка

        if not name:
            logger.warning(f"Skipping category {ref_key} without name (Code: {code})")
            return "skipped"

        # Определить тип категории (OPEX/CAPEX) на основе имени
        expense_type = self._determine_expense_type(name, code)

        # Проверить, существует ли категория с таким external_id_1c в этом отделе
        existing = self.db.query(BudgetCategory).filter(
            BudgetCategory.external_id_1c == ref_key,
            BudgetCategory.department_id == self.department_id
        ).first()

        if existing:
            # Обновить существующую категорию
            updated = False

            if name and existing.name != name:
                existing.name = name
                updated = True

            if code and existing.code_1c != code:
                existing.code_1c = code
                updated = True

            if existing.is_folder != is_folder:
                existing.is_folder = is_folder
                updated = True

            if existing.type != expense_type:
                existing.type = expense_type
                updated = True

            # Обновить order_index если есть
            if order_index is not None:
                try:
                    order_value = int(order_index)
                    if existing.order_index != order_value:
                        existing.order_index = order_value
                        updated = True
                except (ValueError, TypeError):
                    pass

            # Синхронизация обновлена
            existing.updated_at = datetime.utcnow()

            if updated:
                logger.info(f"Updated category: {name} (Code: {code})")
                return "updated"
            else:
                logger.debug(f"Category unchanged: {name}")
                return "unchanged"

        else:
            # Создать новую категорию (БЕЗ parent_id - будет установлен на втором проходе)
            order_value = None
            if order_index is not None:
                try:
                    order_value = int(order_index)
                except (ValueError, TypeError):
                    pass

            new_category = BudgetCategory(
                name=name,
                type=expense_type,
                code_1c=code,
                is_folder=is_folder,
                order_index=order_value,
                external_id_1c=ref_key,
                department_id=self.department_id,
                is_active=True,
                parent_id=None,  # Установим на втором проходе
            )

            self.db.add(new_category)
            logger.info(f"Created new category: {name} (Code: {code}, Type: {expense_type}, Folder: {is_folder})")
            return "created"

    def _set_parent_relationship(self, cat_data: Dict[str, Any]) -> bool:
        """
        Установить parent_id связь для категории

        Args:
            cat_data: Данные категории из 1С

        Returns:
            True если parent_id был установлен, False если нет
        """
        ref_key = cat_data.get("Ref_Key")
        parent_key = cat_data.get("Parent_Key")

        # Если нет Ref_Key или Parent_Key - пропустить
        if not ref_key or not parent_key:
            return False

        # Если Parent_Key = пустой GUID - это корневой элемент
        if parent_key == "00000000-0000-0000-0000-000000000000":
            # Убедиться что parent_id = NULL
            category = self.db.query(BudgetCategory).filter(
                BudgetCategory.external_id_1c == ref_key,
                BudgetCategory.department_id == self.department_id
            ).first()

            if category and category.parent_id is not None:
                category.parent_id = None
                logger.debug(f"Set parent_id=NULL for root category: {category.name}")
                return True

            return False

        # Найти текущую категорию
        category = self.db.query(BudgetCategory).filter(
            BudgetCategory.external_id_1c == ref_key,
            BudgetCategory.department_id == self.department_id
        ).first()

        if not category:
            logger.warning(f"Category with external_id_1c={ref_key} not found")
            return False

        # Найти родительскую категорию
        parent_category = self.db.query(BudgetCategory).filter(
            BudgetCategory.external_id_1c == parent_key,
            BudgetCategory.department_id == self.department_id
        ).first()

        if not parent_category:
            logger.warning(
                f"Parent category with external_id_1c={parent_key} not found for {category.name}"
            )
            return False

        # Установить parent_id
        if category.parent_id != parent_category.id:
            category.parent_id = parent_category.id
            logger.debug(
                f"Set parent_id for '{category.name}' → '{parent_category.name}' (id={parent_category.id})"
            )
            return True

        return False

    def _determine_expense_type(self, name: str, code: Optional[str]) -> ExpenseTypeEnum:
        """
        Определить тип расхода (OPEX/CAPEX) на основе названия и кода

        Args:
            name: Название категории
            code: Код категории

        Returns:
            ExpenseTypeEnum.OPEX или ExpenseTypeEnum.CAPEX
        """
        name_lower = name.lower()

        # Ключевые слова для CAPEX
        capex_keywords = [
            "капитальн", "основные средства", "оборудование", "компьютер",
            "сервер", "инфраструктура", "здание", "сооружение",
            "лицензия", "программное обеспечение", "внеоборотные активы"
        ]

        # Проверить по ключевым словам
        for keyword in capex_keywords:
            if keyword in name_lower:
                return ExpenseTypeEnum.CAPEX

        # Проверить по коду (если код начинается с определенных цифр)
        if code:
            # Пример логики: коды начинающиеся с "02" или "03" - CAPEX
            if code.startswith("02") or code.startswith("03"):
                return ExpenseTypeEnum.CAPEX

        # По умолчанию - OPEX
        return ExpenseTypeEnum.OPEX
