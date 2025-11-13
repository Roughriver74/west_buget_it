"""
Service for importing bank transactions from Excel files
Support for various bank statement formats
"""
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime, date
import pandas as pd
import io
from sqlalchemy.orm import Session

from app.db.models import (
    BankTransaction,
    BankTransactionTypeEnum,
    BankTransactionStatusEnum,
    Organization,
    Department,
)


class BankTransactionImporter:
    """
    Import bank transactions from Excel files
    Supports common bank statement formats
    """

    def __init__(self, db: Session):
        self.db = db

    def import_from_excel(
        self,
        file_content: bytes,
        filename: str,
        department_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Import bank transactions from Excel file

        Expected columns (flexible mapping):
        - Дата операции / Дата / Date
        - Сумма / Amount
        - Контрагент / Counterparty / Плательщик/Получатель
        - ИНН контрагента / INN
        - Назначение платежа / Payment Purpose / Описание
        - Номер документа / Document Number
        - Дебет/Кредит / Type (optional)
        """
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(file_content))

            # Normalize column names
            df.columns = df.columns.str.strip()

            # Map columns to our schema
            column_mapping = self._detect_columns(df.columns)

            if not column_mapping.get('date') or not column_mapping.get('amount'):
                return {
                    'success': False,
                    'error': 'Required columns not found. Need at least: Date and Amount',
                    'imported': 0,
                    'skipped': 0,
                    'errors': []
                }

            imported = 0
            skipped = 0
            errors = []

            for idx, row in df.iterrows():
                try:
                    # Parse date
                    transaction_date = self._parse_date(row[column_mapping['date']])
                    if not transaction_date:
                        errors.append({
                            'row': idx + 2,  # Excel row number (1-indexed + header)
                            'error': 'Invalid date format'
                        })
                        skipped += 1
                        continue

                    # Parse amount
                    amount = self._parse_amount(row[column_mapping['amount']])
                    if amount is None or amount == 0:
                        errors.append({
                            'row': idx + 2,
                            'error': 'Invalid amount'
                        })
                        skipped += 1
                        continue

                    # Determine transaction type
                    transaction_type = BankTransactionTypeEnum.DEBIT  # Default to debit (expense)
                    if column_mapping.get('type'):
                        type_value = str(row[column_mapping['type']]).strip().lower()
                        if 'кредит' in type_value or 'credit' in type_value or 'приход' in type_value:
                            transaction_type = BankTransactionTypeEnum.CREDIT
                        elif 'дебет' in type_value or 'debit' in type_value or 'расход' in type_value:
                            transaction_type = BankTransactionTypeEnum.DEBIT

                    # If amount is negative, it's a debit
                    if amount < 0:
                        transaction_type = BankTransactionTypeEnum.DEBIT
                        amount = abs(amount)

                    # Extract other fields
                    counterparty_name = self._get_value(row, column_mapping.get('counterparty'))
                    counterparty_inn = self._get_value(row, column_mapping.get('inn'))
                    payment_purpose = self._get_value(row, column_mapping.get('payment_purpose'))
                    document_number = self._get_value(row, column_mapping.get('document_number'))

                    # Check if transaction already exists (by date, amount, and counterparty)
                    existing = self.db.query(BankTransaction).filter(
                        BankTransaction.transaction_date == transaction_date,
                        BankTransaction.amount == amount,
                        BankTransaction.counterparty_inn == counterparty_inn,
                        BankTransaction.department_id == department_id,
                        BankTransaction.is_active == True
                    ).first()

                    if existing:
                        skipped += 1
                        continue

                    # Create new transaction
                    transaction = BankTransaction(
                        transaction_date=transaction_date,
                        amount=amount,
                        transaction_type=transaction_type,
                        counterparty_name=counterparty_name,
                        counterparty_inn=counterparty_inn,
                        payment_purpose=payment_purpose,
                        document_number=document_number,
                        department_id=department_id,
                        status=BankTransactionStatusEnum.NEW,
                        import_source='MANUAL_UPLOAD',
                        import_file_name=filename,
                        imported_at=datetime.utcnow(),
                    )

                    self.db.add(transaction)
                    imported += 1

                except Exception as e:
                    errors.append({
                        'row': idx + 2,
                        'error': str(e)
                    })
                    skipped += 1

            self.db.commit()

            return {
                'success': True,
                'imported': imported,
                'skipped': skipped,
                'total_rows': len(df),
                'errors': errors
            }

        except Exception as e:
            self.db.rollback()
            return {
                'success': False,
                'error': f'Failed to process file: {str(e)}',
                'imported': 0,
                'skipped': 0,
                'errors': []
            }

    def _detect_columns(self, columns: List[str]) -> Dict[str, str]:
        """
        Auto-detect column names
        """
        mapping = {}

        # Normalize column names
        normalized = {col: col.strip().lower() for col in columns}

        # Date column
        date_keywords = ['дата', 'date', 'дата операции', 'transaction date']
        for col, norm in normalized.items():
            if any(kw in norm for kw in date_keywords):
                mapping['date'] = col
                break

        # Amount column
        amount_keywords = ['сумма', 'amount', 'sum', 'значение']
        for col, norm in normalized.items():
            if any(kw in norm for kw in amount_keywords):
                mapping['amount'] = col
                break

        # Counterparty
        counterparty_keywords = ['контрагент', 'counterparty', 'плательщик', 'получатель', 'payer', 'recipient']
        for col, norm in normalized.items():
            if any(kw in norm for kw in counterparty_keywords):
                mapping['counterparty'] = col
                break

        # INN
        inn_keywords = ['инн', 'inn']
        for col, norm in normalized.items():
            if any(kw in norm for kw in inn_keywords):
                mapping['inn'] = col
                break

        # Payment purpose
        purpose_keywords = ['назначение', 'purpose', 'описание', 'description', 'комментарий', 'comment']
        for col, norm in normalized.items():
            if any(kw in norm for kw in purpose_keywords):
                mapping['payment_purpose'] = col
                break

        # Document number
        doc_keywords = ['номер', 'number', 'документ', 'document']
        for col, norm in normalized.items():
            if any(kw in norm for kw in doc_keywords):
                mapping['document_number'] = col
                break

        # Transaction type
        type_keywords = ['тип', 'type', 'дебет', 'debit', 'кредит', 'credit']
        for col, norm in normalized.items():
            if any(kw in norm for kw in type_keywords):
                mapping['type'] = col
                break

        return mapping

    def _parse_date(self, value: Any) -> Optional[date]:
        """Parse date from various formats"""
        if pd.isna(value):
            return None

        if isinstance(value, (date, datetime)):
            return value if isinstance(value, date) else value.date()

        # Try parsing string
        if isinstance(value, str):
            try:
                return pd.to_datetime(value, dayfirst=True).date()
            except:
                return None

        return None

    def _parse_amount(self, value: Any) -> Optional[Decimal]:
        """Parse amount from various formats"""
        if pd.isna(value):
            return None

        try:
            # Remove spaces and replace comma with dot
            if isinstance(value, str):
                value = value.replace(' ', '').replace(',', '.')

            return Decimal(str(value))
        except:
            return None

    def _get_value(self, row: pd.Series, column: Optional[str]) -> Optional[str]:
        """Get value from row by column name"""
        if not column or column not in row.index:
            return None

        value = row[column]
        if pd.isna(value):
            return None

        return str(value).strip() if value else None
