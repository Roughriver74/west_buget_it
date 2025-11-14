"""
Pydantic schemas for Credit Portfolio
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# ==================== FinOrganization ====================

class FinOrganizationBase(BaseModel):
    name: str = Field(..., description="Название организации")
    inn: Optional[str] = Field(None, description="ИНН")
    is_active: bool = Field(True, description="Активность")


class FinOrganizationCreate(FinOrganizationBase):
    department_id: Optional[int] = Field(None, description="ID отдела (опционально для ADMIN/MANAGER)")


class FinOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    inn: Optional[str] = None
    is_active: Optional[bool] = None


class FinOrganizationInDB(FinOrganizationBase):
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinBankAccount ====================

class FinBankAccountBase(BaseModel):
    account_number: str = Field(..., description="Номер счета")
    bank_name: Optional[str] = Field(None, description="Название банка")
    is_active: bool = Field(True, description="Активность")


class FinBankAccountCreate(FinBankAccountBase):
    department_id: Optional[int] = Field(None)


class FinBankAccountUpdate(BaseModel):
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    is_active: Optional[bool] = None


class FinBankAccountInDB(FinBankAccountBase):
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinContract ====================

class FinContractBase(BaseModel):
    contract_number: str = Field(..., description="Номер договора")
    contract_date: Optional[date] = Field(None, description="Дата договора")
    contract_type: Optional[str] = Field(None, description="Тип договора (Кредит, Заем)")
    counterparty: Optional[str] = Field(None, description="Контрагент")
    is_active: bool = Field(True, description="Активность")


class FinContractCreate(FinContractBase):
    department_id: Optional[int] = None


class FinContractUpdate(BaseModel):
    contract_number: Optional[str] = None
    contract_date: Optional[date] = None
    contract_type: Optional[str] = None
    counterparty: Optional[str] = None
    is_active: Optional[bool] = None


class FinContractInDB(FinContractBase):
    id: int
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinReceipt ====================

class FinReceiptBase(BaseModel):
    operation_id: str
    organization_id: int
    bank_account_id: Optional[int] = None
    contract_id: Optional[int] = None
    operation_type: Optional[str] = None
    accounting_account: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    payer: Optional[str] = None
    payer_account: Optional[str] = None
    settlement_account: Optional[str] = None
    contract_date: Optional[date] = None
    currency: str = "RUB"
    amount: Decimal
    commission: Optional[Decimal] = None
    payment_purpose: Optional[str] = None
    responsible_person: Optional[str] = None
    comment: Optional[str] = None


class FinReceiptCreate(FinReceiptBase):
    department_id: Optional[int] = None


class FinReceiptInDB(FinReceiptBase):
    id: int
    department_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinExpense ====================

class FinExpenseBase(BaseModel):
    operation_id: str
    organization_id: int
    bank_account_id: Optional[int] = None
    contract_id: Optional[int] = None
    operation_type: Optional[str] = None
    accounting_account: Optional[str] = None
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    recipient: Optional[str] = None
    recipient_account: Optional[str] = None
    debit_account: Optional[str] = None
    contract_date: Optional[date] = None
    currency: str = "RUB"
    amount: Decimal
    expense_article: Optional[str] = None
    payment_purpose: Optional[str] = None
    responsible_person: Optional[str] = None
    comment: Optional[str] = None
    tax_period: Optional[str] = None
    unconfirmed_by_bank: bool = False


class FinExpenseCreate(FinExpenseBase):
    department_id: Optional[int] = None


class FinExpenseInDB(FinExpenseBase):
    id: int
    department_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ==================== FinExpenseDetail ====================

class FinExpenseDetailBase(BaseModel):
    expense_operation_id: str
    contract_number: Optional[str] = None
    repayment_type: Optional[str] = None
    settlement_account: Optional[str] = None
    advance_account: Optional[str] = None
    payment_type: Optional[str] = None
    payment_amount: Optional[Decimal] = None
    settlement_rate: Decimal = Decimal("1.0")
    settlement_amount: Optional[Decimal] = None
    vat_amount: Optional[Decimal] = None
    expense_amount: Optional[Decimal] = None
    vat_in_expense: Optional[Decimal] = None


class FinExpenseDetailCreate(FinExpenseDetailBase):
    department_id: Optional[int] = None


class FinExpenseDetailInDB(FinExpenseDetailBase):
    id: int
    department_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== FinImportLog ====================

class FinImportLogInDB(BaseModel):
    id: int
    import_date: datetime
    source_file: Optional[str]
    table_name: Optional[str]
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_failed: int = 0
    status: Optional[str]
    error_message: Optional[str]
    processed_by: Optional[str]
    processing_time_seconds: Optional[Decimal]
    department_id: int

    class Config:
        from_attributes = True


# ==================== Summary & Stats ====================

class CreditPortfolioSummary(BaseModel):
    """Summary statistics for credit portfolio"""
    total_receipts: Decimal = Field(..., description="Всего поступлений")
    total_expenses: Decimal = Field(..., description="Всего списаний")
    net_balance: Decimal = Field(..., description="Чистый баланс")
    active_contracts_count: int = Field(..., description="Активных договоров")
    total_interest: Decimal = Field(..., description="Всего процентов")
    total_principal: Decimal = Field(..., description="Всего тела кредита")


class MonthlyStats(BaseModel):
    """Monthly statistics"""
    month: str
    receipts: Decimal
    expenses: Decimal
    net: Decimal
