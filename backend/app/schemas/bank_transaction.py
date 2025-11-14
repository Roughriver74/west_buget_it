"""
Pydantic schemas for Bank Transactions
"""
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class BankTransactionBase(BaseModel):
    """Base schema for bank transaction"""
    transaction_date: date
    amount: Decimal
    transaction_type: str = Field(..., description="DEBIT or CREDIT")
    counterparty_name: Optional[str] = None
    counterparty_inn: Optional[str] = None
    counterparty_kpp: Optional[str] = None
    counterparty_account: Optional[str] = None
    counterparty_bank: Optional[str] = None
    counterparty_bik: Optional[str] = None
    payment_purpose: Optional[str] = None
    organization_id: Optional[int] = None
    account_number: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    notes: Optional[str] = None


class BankTransactionCreate(BankTransactionBase):
    """Schema for creating bank transaction"""
    department_id: int


class BankTransactionUpdate(BaseModel):
    """Schema for updating bank transaction"""
    category_id: Optional[int] = None
    expense_id: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    is_regular_payment: Optional[bool] = None


class BankTransactionCategorize(BaseModel):
    """Schema for categorizing transaction"""
    category_id: int
    notes: Optional[str] = None


class BankTransactionLink(BaseModel):
    """Schema for linking transaction to expense"""
    expense_id: int
    notes: Optional[str] = None


class BankTransactionInDB(BankTransactionBase):
    """Schema for bank transaction from database"""
    id: int
    department_id: int

    # Classification
    category_id: Optional[int] = None
    category_confidence: Optional[Decimal] = None
    suggested_category_id: Optional[int] = None

    # Matching
    expense_id: Optional[int] = None
    matching_score: Optional[Decimal] = None
    suggested_expense_id: Optional[int] = None

    # Status
    status: str
    is_regular_payment: bool
    regular_payment_pattern_id: Optional[int] = None

    # Audit
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None

    # Import
    import_source: Optional[str] = None
    import_file_name: Optional[str] = None
    imported_at: Optional[datetime] = None
    external_id_1c: Optional[str] = None

    # System fields
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BankTransactionWithRelations(BankTransactionInDB):
    """Bank transaction with related entities"""
    category_name: Optional[str] = None
    suggested_category_name: Optional[str] = None
    expense_number: Optional[str] = None
    suggested_expense_number: Optional[str] = None
    organization_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None
    department_name: Optional[str] = None


class BankTransactionList(BaseModel):
    """List of bank transactions with pagination"""
    total: int
    items: List[BankTransactionWithRelations]
    page: int
    page_size: int
    pages: int


class BankTransactionStats(BaseModel):
    """Statistics for bank transactions"""
    total_transactions: int
    total_amount: Decimal
    new_count: int
    categorized_count: int
    matched_count: int
    approved_count: int
    needs_review_count: int
    avg_category_confidence: Optional[float] = None
    avg_matching_score: Optional[float] = None


class BankTransactionImportResult(BaseModel):
    """Result of bank transaction import"""
    total_rows: int
    imported: int
    skipped: int
    errors: List[dict]
    warnings: List[dict]


class MatchingSuggestion(BaseModel):
    """Suggestion for matching transaction to expense"""
    expense_id: int
    expense_number: str
    expense_amount: Decimal
    expense_date: date
    expense_category_id: Optional[int] = None
    expense_contractor_name: Optional[str] = None
    matching_score: float
    match_reasons: List[str]


class CategorySuggestion(BaseModel):
    """AI suggestion for transaction category"""
    category_id: int
    category_name: str
    confidence: float
    reasoning: List[str]


class RegularPaymentPattern(BaseModel):
    """Pattern for regular payments"""
    id: int
    counterparty_inn: Optional[str] = None
    counterparty_name: Optional[str] = None
    category_id: int
    category_name: str
    avg_amount: Decimal
    frequency_days: int  # Average days between payments
    last_payment_date: date
    transaction_count: int


class BulkCategorizeRequest(BaseModel):
    """Request for bulk categorization"""
    transaction_ids: List[int]
    category_id: int
    notes: Optional[str] = None


class BulkLinkRequest(BaseModel):
    """Request for bulk linking to expenses"""
    links: List[dict]  # [{"transaction_id": 1, "expense_id": 10}, ...]


class BulkStatusUpdateRequest(BaseModel):
    """Request for bulk status update"""
    transaction_ids: List[int]
    status: str
