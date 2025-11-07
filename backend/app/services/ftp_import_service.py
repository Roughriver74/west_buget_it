"""
Service for importing expenses from FTP Excel files
"""
import asyncio
import aioftp
import pandas as pd
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import extract, and_, or_
from io import BytesIO
import logging

from app.db.models import Expense, BudgetCategory, Contractor, Organization, Department, ExpenseStatusEnum
from app.services.baseline_bus import baseline_bus

logger = logging.getLogger(__name__)


class FTPImportService:
    """Service for importing expenses from FTP server"""

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 21
    ):
        self.host = host
        self.username = username
        self.password = password
        self.port = port

    async def download_file(self, remote_path: str) -> bytes:
        """Download file from FTP server"""
        try:
            async with aioftp.Client.context(
                self.host,
                port=self.port,
                user=self.username,
                password=self.password
            ) as client:
                logger.info(f"Connected to FTP server: {self.host}")

                # Download file to memory
                data = BytesIO()
                async with client.download_stream(remote_path) as stream:
                    async for block in stream.iter_by_block():
                        data.write(block)

                data.seek(0)

                logger.info(f"Downloaded file: {remote_path}, size: {len(data.getvalue())} bytes")
                return data.getvalue()

        except Exception as e:
            logger.error(f"Failed to download file from FTP: {e}")
            raise Exception(f"FTP download error: {str(e)}")

    async def list_files(self, remote_dir: str = "/") -> List[str]:
        """List files in remote directory"""
        try:
            async with aioftp.Client.context(
                self.host,
                port=self.port,
                user=self.username,
                password=self.password
            ) as client:
                files = []
                async for path, info in client.list(remote_dir):
                    if info["type"] == "file":
                        files.append(str(path))

                logger.info(f"Found {len(files)} files in {remote_dir}")
                return files

        except Exception as e:
            logger.error(f"Failed to list FTP files: {e}")
            raise Exception(f"FTP list error: {str(e)}")

    def parse_excel(self, file_data: bytes) -> pd.DataFrame:
        """Parse Excel file to DataFrame"""
        try:
            # Read Excel file
            df = pd.read_excel(BytesIO(file_data), engine='openpyxl')

            logger.info(f"Parsed Excel file: {len(df)} rows, columns: {list(df.columns)}")
            return df

        except Exception as e:
            logger.error(f"Failed to parse Excel: {e}")
            raise Exception(f"Excel parsing error: {str(e)}")

    def normalize_expense_data(self, df: pd.DataFrame) -> List[Dict]:
        """Normalize DataFrame to expense format"""
        expenses = []

        # Map column names based on actual Excel structure
        column_mapping = {
            'Заявка на расходование денежных средств': 'number',
            'Желательная дата платежа': 'request_date',
            'Статья ДДС': 'category_name',
            'Получатель': 'contractor_name',
            'Организация': 'organization_name',
            'Подразделение': 'subdivision_name',  # FTP subdivision field
            'Сумма документа': 'amount',
            'Дата оплаты': 'payment_date',
            'Статус': 'status',
            'Комментарий': 'comment',
            'Кто заявил': 'requester',
            'Назначение платежа': 'purpose',  # For keyword matching
        }

        for _, row in df.iterrows():
            try:
                expense = {}

                # Map columns
                for excel_col, db_col in column_mapping.items():
                    if excel_col in row:
                        value = row[excel_col]
                        # Handle NaN/None values
                        if pd.isna(value):
                            expense[db_col] = None
                        else:
                            expense[db_col] = value

                # Extract number from full string
                # Example: "Заявка на расходование ДС ВГ0В-000019 от 21.07.2025 15:28:39"
                # Extract: "ВГ0В-000019"
                if expense.get('number'):
                    import re
                    match = re.search(r'([А-ЯA-Z0-9]{2,4}0В-\d{6})', expense['number'])
                    if match:
                        expense['number'] = match.group(1)
                    else:
                        # Fallback: use as is if pattern not found
                        logger.warning(f"Could not extract number from: {expense['number']}")
                        continue

                # Skip if no number
                if not expense.get('number'):
                    continue

                # Normalize status
                # Map Russian statuses to English enum values
                status_mapping = {
                    'К оплате': 'PENDING',
                    'Оплачена': 'PAID',
                    'Оплачено': 'PAID',
                    'Черновик': 'DRAFT',
                    'Отклонена': 'REJECTED',
                    'Закрыта': 'CLOSED',
                }
                if expense.get('status') and expense['status'] in status_mapping:
                    expense['status'] = status_mapping[expense['status']]
                else:
                    expense['status'] = 'PENDING'  # Default status

                # Parse dates (format: dd.mm.yyyy)
                # Set time to 12:00 (noon) to avoid timezone conversion issues
                if expense.get('request_date'):
                    if isinstance(expense['request_date'], str):
                        # Parse date in format dd.mm.yyyy
                        expense['request_date'] = pd.to_datetime(expense['request_date'], format='%d.%m.%Y', errors='coerce')
                        if pd.notna(expense['request_date']):
                            # Set time to 12:00 to avoid timezone issues (prevents day shift)
                            dt = expense['request_date'].to_pydatetime()
                            expense['request_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0)
                    elif isinstance(expense['request_date'], pd.Timestamp):
                        dt = expense['request_date'].to_pydatetime()
                        expense['request_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0)

                if expense.get('payment_date'):
                    if isinstance(expense['payment_date'], str):
                        # Parse date in format dd.mm.yyyy
                        expense['payment_date'] = pd.to_datetime(expense['payment_date'], format='%d.%m.%Y', errors='coerce')
                        if pd.notna(expense['payment_date']):
                            # Set time to 12:00 to avoid timezone issues (prevents day shift)
                            dt = expense['payment_date'].to_pydatetime()
                            expense['payment_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0)
                    elif isinstance(expense['payment_date'], pd.Timestamp):
                        dt = expense['payment_date'].to_pydatetime()
                        expense['payment_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0)

                # Parse amount - IMPORTANT: Skip if amount is empty/invalid
                if expense.get('amount') is not None and expense.get('amount') != '':
                    try:
                        expense['amount'] = Decimal(str(expense['amount']))
                        # Skip if amount is 0 or negative
                        if expense['amount'] <= 0:
                            logger.warning(f"Skipping expense {expense.get('number')} with zero/negative amount: {expense['amount']}")
                            continue
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Skipping expense {expense.get('number')} with invalid amount: {expense.get('amount')}")
                        continue
                else:
                    logger.warning(f"Skipping expense {expense.get('number')} with empty amount")
                    continue

                expenses.append(expense)

            except Exception as e:
                logger.warning(f"Failed to parse row: {e}")
                continue

        logger.info(f"Normalized {len(expenses)} expenses from Excel")
        return expenses

    def find_category_by_keywords(
        self,
        db: Session,
        comment: str = None,
        purpose: str = None,
        dds_category: str = None
    ) -> Optional[BudgetCategory]:
        """Find category by keywords in comment, purpose, or DDS category"""

        # Combine all text for keyword search
        search_text = " ".join(filter(None, [comment or "", purpose or "", dds_category or ""])).lower()

        # Keyword mapping to category names
        keyword_mapping = {
            # Техника
            'техника': ['Техника'],
            'сканер': ['Техника Склад'],
            'склад': ['Техника Склад'],
            'краснодар': ['Техника Краснодар'],
            'логистик': ['Техника Логистика'],
            'москв': ['Техника Москва'],
            'спб': ['Техника ОП СПб'],
            'сервис': ['Техника Сервис'],
            'вэд': ['Техника ВЭД'],
            'юр': ['Техника Юр. отдел'],
            'маркетинг': ['Техника отдел маркетинга'],

            # Обслуживание
            'обслуживание': ['Обслуживание оргтехники', 'Ремонты и тех обслуживание'],
            'ремонт': ['Ремонты и тех обслуживание', 'Обслуживание и ремонт'],
            'заправка': ['Заправка картриджей'],
            'картридж': ['Заправка картриджей'],
            'расходн': ['Расходные материалы'],

            # Связь
            'интернет': ['Связь (телефон/интернет)', 'Связь и коммуникации'],
            'телефон': ['Связь (телефон/интернет)', 'Связь и коммуникации'],
            'связь': ['Связь (телефон/интернет)', 'Связь и коммуникации'],
            'мобильн': ['Связь (телефон/интернет)'],

            # Серверы и хостинг
            'сервер': ['Сервер 1с', 'Серверы и хостинг', 'Почтовый Сервер'],
            'хостинг': ['Хостинг CRM', 'Серверы и хостинг'],
            'почтов': ['Почтовый Сервер'],
            '1с': ['1с', '1с(лицензии)', 'Сервер 1с'],

            # Разработка
            'разработк': ['Битрикс 24 Разработка', 'Приложение визитов(разработка)', 'Разработка и настройка'],
            'битрикс': ['Битрикс 24 Разработка', 'Битрикс 24(настройка)', 'Битрикс24(лицензии)'],
            'настройк': ['Битрикс 24(настройка)', 'Разработка и настройка'],
            'интеграц': ['Интегарции телефонии чатов и пр'],
            'приложение': ['Приложение визитов(разработка)'],

            # Прочее
            'аутсорс': ['Аутсорс'],
            'принтер': ['Покупка принтеров и прочей орг техники(обновление)'],
            'лицензи': ['Лицензии и ПО', '1с(лицензии)', 'Битрикс24(лицензии)'],
            'покупка по': ['Покупка ПО', 'Лицензии и ПО'],
            'аналитик': ['Аналитика данных'],
        }

        # Try to find by keywords
        for keyword, category_names in keyword_mapping.items():
            if keyword in search_text:
                for cat_name in category_names:
                    category = db.query(BudgetCategory).filter(
                        BudgetCategory.name.ilike(f"%{cat_name}%"),
                        BudgetCategory.is_active == True
                    ).first()
                    if category:
                        logger.info(f"Matched category '{category.name}' by keyword '{keyword}'")
                        return category

        # Fallback: try exact match with DDS category
        if dds_category:
            category = db.query(BudgetCategory).filter(
                BudgetCategory.name.ilike(f"%{dds_category}%"),
                BudgetCategory.is_active == True
            ).first()
            if category:
                return category

        # Last resort: return default category "Прочие расходы"
        default_category = db.query(BudgetCategory).filter(
            BudgetCategory.name.ilike("%Прочие расходы%"),
            BudgetCategory.is_active == True
        ).first()

        if default_category:
            logger.warning(f"No matching category found, using default: {default_category.name}")
            return default_category

        return None

    def find_or_create_category(
        self,
        db: Session,
        category_name: str
    ) -> Optional[BudgetCategory]:
        """Find existing category or create new one"""
        if not category_name:
            return None

        # Try to find existing
        category = db.query(BudgetCategory).filter(
            BudgetCategory.name.ilike(f"%{category_name}%")
        ).first()

        if category:
            return category

        # Create new category as OPEX by default
        from app.db.models import ExpenseTypeEnum
        new_category = BudgetCategory(
            name=category_name,
            type=ExpenseTypeEnum.OPEX,
            is_active=True
        )
        db.add(new_category)
        db.flush()

        logger.info(f"Created new category: {category_name}")
        return new_category

    def find_or_create_contractor(
        self,
        db: Session,
        contractor_name: str,
        department_id: int
    ) -> Optional[Contractor]:
        """Find existing contractor or create new one"""
        if not contractor_name:
            return None

        # Try to find existing
        contractor = db.query(Contractor).filter(
            Contractor.name.ilike(f"%{contractor_name}%")
        ).first()

        if contractor:
            return contractor

        # Create new contractor
        new_contractor = Contractor(
            name=contractor_name,
            department_id=department_id,
            is_active=True
        )
        db.add(new_contractor)
        db.flush()

        logger.info(f"Created new contractor: {contractor_name} (department_id: {department_id})")
        return new_contractor

    def find_organization(
        self,
        db: Session,
        organization_name: str
    ) -> Optional[Organization]:
        """Find existing organization"""
        if not organization_name:
            return None

        organization = db.query(Organization).filter(
            Organization.name.ilike(f"%{organization_name}%")
        ).first()

        return organization

    def find_department_by_subdivision(
        self,
        db: Session,
        subdivision_name: str
    ) -> Optional[Department]:
        """Find department by FTP subdivision name"""
        if not subdivision_name:
            return None

        # Try to find by exact match first
        department = db.query(Department).filter(
            Department.ftp_subdivision_name == subdivision_name,
            Department.is_active == True
        ).first()

        if department:
            logger.info(f"Found department '{department.name}' for subdivision '{subdivision_name}'")
            return department

        # Try partial match
        department = db.query(Department).filter(
            Department.ftp_subdivision_name.ilike(f"%{subdivision_name}%"),
            Department.is_active == True
        ).first()

        if department:
            logger.info(f"Found department '{department.name}' for subdivision '{subdivision_name}' (partial match)")

        return department

    def map_status(self, status_str: Optional[str]) -> ExpenseStatusEnum:
        """Map status string to ExpenseStatusEnum"""
        if not status_str:
            return ExpenseStatusEnum.DRAFT

        status_str = str(status_str).upper().strip()

        status_mapping = {
            'ЧЕРНОВИК': ExpenseStatusEnum.DRAFT,
            'DRAFT': ExpenseStatusEnum.DRAFT,
            'К ОПЛАТЕ': ExpenseStatusEnum.PENDING,
            'PENDING': ExpenseStatusEnum.PENDING,
            'ОПЛАЧЕНА': ExpenseStatusEnum.PAID,
            'PAID': ExpenseStatusEnum.PAID,
            'ОТКЛОНЕНА': ExpenseStatusEnum.REJECTED,
            'REJECTED': ExpenseStatusEnum.REJECTED,
            'ЗАКРЫТА': ExpenseStatusEnum.CLOSED,
            'CLOSED': ExpenseStatusEnum.CLOSED,
        }

        return status_mapping.get(status_str, ExpenseStatusEnum.DRAFT)

    def delete_expenses_from_month(
        self,
        db: Session,
        year: int,
        month: int
    ) -> int:
        """Delete all expenses from specified month onwards"""
        impacted_rows = db.query(
            Expense.category_id,
            Expense.department_id,
            Expense.request_date,
        ).filter(
            or_(
                and_(
                    extract('year', Expense.request_date) == year,
                    extract('month', Expense.request_date) >= month
                ),
                extract('year', Expense.request_date) > year
            )
        ).all()

        deleted_count = db.query(Expense).filter(
            or_(
                and_(
                    extract('year', Expense.request_date) == year,
                    extract('month', Expense.request_date) >= month
                ),
                extract('year', Expense.request_date) > year
            )
        ).delete(synchronize_session=False)

        db.flush()
        logger.info(f"Deleted {deleted_count} expenses from {year}-{month:02d} onwards")

        for category_id, department_id, request_date in impacted_rows:
            baseline_bus.invalidate_for_expense(
                category_id=category_id,
                department_id=department_id,
                request_year=request_date.year if request_date else None,
            )

        return deleted_count

    def import_expenses(
        self,
        db: Session,
        expenses_data: List[Dict],
        skip_duplicates: bool = True,
        default_department_id: Optional[int] = None,
        batch_size: int = 50  # Commit every N records to avoid memory issues
    ) -> Tuple[int, int, int]:
        """
        Import expenses to database with batched commits

        Args:
            db: Database session
            expenses_data: List of expense dictionaries
            skip_duplicates: If True, updates only critical fields (status, amount, payment_date, comment).
                           If False, performs full update of all fields.
            default_department_id: Default department ID if no mapping found
            batch_size: Number of records to process before committing (default: 50)

        Returns:
            Tuple of (created, updated, skipped) counts
        """
        created = 0
        updated = 0
        skipped = 0
        impacted_cache_keys: Set[Tuple[int, int, int]] = set()
        processed_in_batch = 0

        def track_cache_invalidation(
            category_id: Optional[int],
            department_id: Optional[int],
            request_date_value: Optional[datetime],
        ) -> None:
            if category_id is None or department_id is None or request_date_value is None:
                return
            impacted_cache_keys.add(
                (category_id, department_id, request_date_value.year)
            )

        for idx, expense_data in enumerate(expenses_data):
            try:
                # Validate required fields
                if not expense_data.get('number'):
                    logger.warning(f"Skipping expense without number at index {idx}")
                    skipped += 1
                    continue

                if not expense_data.get('amount'):
                    logger.warning(f"Skipping expense {expense_data.get('number')} without amount")
                    skipped += 1
                    continue

                # Check for existing expense by number
                existing = db.query(Expense).filter(
                    Expense.number == expense_data.get('number')
                ).first()

                # Find department by subdivision name from FTP
                department = self.find_department_by_subdivision(
                    db,
                    expense_data.get('subdivision_name')
                )

                # Skip if department not found (no fallback to default)
                if not department:
                    logger.warning(f"No department mapping found for subdivision '{expense_data.get('subdivision_name')}' in expense {expense_data.get('number')}, skipping")
                    skipped += 1
                    continue

                # Find/create related entities
                # Don't auto-assign category - leave it None for manual assignment
                category = None

                contractor = self.find_or_create_contractor(
                    db,
                    expense_data.get('contractor_name'),
                    department.id
                )

                organization = self.find_organization(
                    db,
                    expense_data.get('organization_name')
                )

                # Default to first organization if not found
                if not organization:
                    organization = db.query(Organization).first()

                if not organization:
                    logger.warning(f"No organization found, skipping expense {expense_data.get('number')}")
                    skipped += 1
                    continue

                # Map status
                status = self.map_status(expense_data.get('status'))

                # Prepare expense fields with validation
                expense_fields = {
                    'number': expense_data.get('number'),
                    'department_id': department.id,
                    'category_id': category.id if category else None,
                    'contractor_id': contractor.id if contractor else None,
                    'organization_id': organization.id,
                    'amount': expense_data.get('amount'),  # Already validated above
                    'request_date': expense_data.get('request_date') or datetime.now(),
                    'payment_date': expense_data.get('payment_date'),
                    'status': status,
                    'is_paid': status == ExpenseStatusEnum.PAID,
                    'is_closed': status == ExpenseStatusEnum.CLOSED,
                    'comment': expense_data.get('comment'),
                    'requester': expense_data.get('requester'),
                    'imported_from_ftp': True,
                    'needs_review': True,
                }

                if existing:
                    # Always update critical fields from FTP (even if skip_duplicates=True)
                    track_cache_invalidation(
                        existing.category_id,
                        existing.department_id,
                        existing.request_date,
                    )

                    if skip_duplicates:
                        # Update only critical fields that change frequently
                        critical_fields = ['status', 'is_paid', 'is_closed', 'amount', 'payment_date', 'comment']
                        for field in critical_fields:
                            if field in expense_fields:
                                setattr(existing, field, expense_fields[field])
                        updated += 1
                    else:
                        # Full update of all fields
                        for key, value in expense_fields.items():
                            setattr(existing, key, value)
                        updated += 1

                    track_cache_invalidation(
                        expense_fields.get('category_id'),
                        expense_fields.get('department_id'),
                        expense_fields.get('request_date'),
                    )
                else:
                    # Create new
                    new_expense = Expense(**expense_fields)
                    db.add(new_expense)
                    track_cache_invalidation(
                        expense_fields.get('category_id'),
                        expense_fields.get('department_id'),
                        expense_fields.get('request_date'),
                    )
                    created += 1

                processed_in_batch += 1

                # Commit in batches to avoid memory issues with large imports
                if processed_in_batch >= batch_size:
                    try:
                        db.commit()
                        logger.info(f"Batch commit: {created} created, {updated} updated so far (processed {idx + 1}/{len(expenses_data)})")
                        processed_in_batch = 0
                    except Exception as commit_error:
                        logger.error(f"Batch commit failed at record {idx}: {commit_error}")
                        db.rollback()
                        # Continue with next batch
                        processed_in_batch = 0

            except Exception as e:
                logger.error(f"Failed to import expense {expense_data.get('number')}: {e}")
                # Rollback this record and continue
                db.rollback()
                skipped += 1
                processed_in_batch = 0
                continue

        # Final commit for remaining records
        try:
            if processed_in_batch > 0:
                db.commit()
                logger.info(f"Final commit: {created} created, {updated} updated, {skipped} skipped")
        except Exception as final_commit_error:
            logger.error(f"Final commit failed: {final_commit_error}")
            db.rollback()

        for category_id, department_id, year in impacted_cache_keys:
            baseline_bus.invalidate(
                category_id=category_id,
                department_id=department_id,
                year=year,
            )

        return created, updated, skipped


async def import_from_ftp(
    db: Session,
    host: str,
    username: str,
    password: str,
    remote_path: str,
    delete_from_year: Optional[int] = None,
    delete_from_month: Optional[int] = None,
    skip_duplicates: bool = True,
    default_department_id: Optional[int] = None
) -> Dict:
    """
    Main function to import expenses from FTP

    Args:
        db: Database session
        host: FTP host
        username: FTP username
        password: FTP password
        remote_path: Path to Excel file on FTP
        delete_from_year: Year to start deleting from (None = skip deletion)
        delete_from_month: Month to start deleting from (None = skip deletion)
        skip_duplicates: If True, updates only critical fields (status, amount, payment_date) for existing expenses.
                        If False, performs full update of all fields.
        default_department_id: Default department ID if no mapping found

    Returns:
        Dict with import statistics
    """
    service = FTPImportService(host, username, password)

    # Download file
    file_data = await service.download_file(remote_path)

    # Parse Excel
    df = service.parse_excel(file_data)

    # Normalize data
    expenses_data = service.normalize_expense_data(df)

    # Delete old expenses (only if parameters are provided)
    deleted = 0
    if delete_from_year is not None and delete_from_month is not None:
        deleted = service.delete_expenses_from_month(db, delete_from_year, delete_from_month)

    # Import expenses
    created, updated, skipped = service.import_expenses(
        db,
        expenses_data,
        skip_duplicates,
        default_department_id
    )

    return {
        'deleted': deleted,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'total_in_file': len(expenses_data)
    }
