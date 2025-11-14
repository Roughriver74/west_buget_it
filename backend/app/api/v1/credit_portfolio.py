"""
Credit Portfolio API endpoints
Управление кредитным портфелем
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, datetime

from app.db.session import get_db
from app.db.models import (
    FinOrganization, FinBankAccount, FinContract,
    FinReceipt, FinExpense, FinExpenseDetail, FinImportLog,
    User, UserRoleEnum
)
from app.schemas.credit_portfolio import (
    FinOrganizationCreate, FinOrganizationUpdate, FinOrganizationInDB,
    FinBankAccountCreate, FinBankAccountUpdate, FinBankAccountInDB,
    FinContractCreate, FinContractUpdate, FinContractInDB,
    FinReceiptCreate, FinReceiptInDB,
    FinExpenseCreate, FinExpenseInDB,
    FinExpenseDetailInDB,
    FinImportLogInDB,
    CreditPortfolioSummary,
)
from app.utils.auth import get_current_active_user

router = APIRouter()


def check_finance_access(user: User) -> bool:
    """Check if user has access to finance features"""
    return user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN, UserRoleEnum.ACCOUNTANT]


# ==================== Organizations ====================

@router.get("/organizations", response_model=List[FinOrganizationInDB])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Список организаций холдинга

    Доступ: только MANAGER, ADMIN, ACCOUNTANT
    """
    if not check_finance_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Finance features available only for MANAGER, ADMIN, ACCOUNTANT"
        )

    query = db.query(FinOrganization)

    # Department filtering
    if department_id:
        query = query.filter(FinOrganization.department_id == department_id)

    # Active filter
    if is_active is not None:
        query = query.filter(FinOrganization.is_active == is_active)

    organizations = query.offset(skip).limit(limit).all()
    return organizations


@router.post("/organizations", response_model=FinOrganizationInDB, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: FinOrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать организацию"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id
    department_id = org_data.department_id if org_data.department_id else current_user.department_id
    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID must be specified"
        )

    # Create organization
    new_org = FinOrganization(
        name=org_data.name,
        inn=org_data.inn,
        is_active=org_data.is_active,
        department_id=department_id
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org


@router.put("/organizations/{org_id}", response_model=FinOrganizationInDB)
async def update_organization(
    org_id: int,
    org_data: FinOrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Обновить организацию"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    org = db.query(FinOrganization).filter(FinOrganization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Update fields
    update_data = org_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    db.commit()
    db.refresh(org)
    return org


# ==================== Bank Accounts ====================

@router.get("/bank-accounts", response_model=List[FinBankAccountInDB])
async def list_bank_accounts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Список банковских счетов"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(FinBankAccount)

    if department_id:
        query = query.filter(FinBankAccount.department_id == department_id)

    if is_active is not None:
        query = query.filter(FinBankAccount.is_active == is_active)

    accounts = query.offset(skip).limit(limit).all()
    return accounts


@router.post("/bank-accounts", response_model=FinBankAccountInDB, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account_data: FinBankAccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать банковский счет"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    department_id = account_data.department_id if account_data.department_id else current_user.department_id
    if not department_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department ID required")

    new_account = FinBankAccount(
        account_number=account_data.account_number,
        bank_name=account_data.bank_name,
        is_active=account_data.is_active,
        department_id=department_id
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


# ==================== Contracts ====================

@router.get("/contracts", response_model=List[FinContractInDB])
async def list_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Список кредитных договоров"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(FinContract)

    if department_id:
        query = query.filter(FinContract.department_id == department_id)

    if is_active is not None:
        query = query.filter(FinContract.is_active == is_active)

    contracts = query.offset(skip).limit(limit).all()
    return contracts


@router.post("/contracts", response_model=FinContractInDB, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract_data: FinContractCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Создать кредитный договор"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    department_id = contract_data.department_id if contract_data.department_id else current_user.department_id
    if not department_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department ID required")

    new_contract = FinContract(
        contract_number=contract_data.contract_number,
        contract_date=contract_data.contract_date,
        contract_type=contract_data.contract_type,
        counterparty=contract_data.counterparty,
        is_active=contract_data.is_active,
        department_id=department_id
    )
    db.add(new_contract)
    db.commit()
    db.refresh(new_contract)
    return new_contract


# ==================== Receipts ====================

@router.get("/receipts", response_model=List[FinReceiptInDB])
async def list_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    organization_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Список поступлений кредитов

    Фильтры:
    - department_id: фильтр по отделу
    - date_from/date_to: период
    - organization_id: по организации
    - contract_id: по договору
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(FinReceipt)

    if department_id:
        query = query.filter(FinReceipt.department_id == department_id)

    if date_from:
        query = query.filter(FinReceipt.document_date >= date_from)

    if date_to:
        query = query.filter(FinReceipt.document_date <= date_to)

    if organization_id:
        query = query.filter(FinReceipt.organization_id == organization_id)

    if contract_id:
        query = query.filter(FinReceipt.contract_id == contract_id)

    receipts = query.order_by(FinReceipt.document_date.desc()).offset(skip).limit(limit).all()
    return receipts


# ==================== Expenses ====================

@router.get("/expenses", response_model=List[FinExpenseInDB])
async def list_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    organization_id: Optional[int] = None,
    contract_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Список списаний по кредитам"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(FinExpense)

    if department_id:
        query = query.filter(FinExpense.department_id == department_id)

    if date_from:
        query = query.filter(FinExpense.document_date >= date_from)

    if date_to:
        query = query.filter(FinExpense.document_date <= date_to)

    if organization_id:
        query = query.filter(FinExpense.organization_id == organization_id)

    if contract_id:
        query = query.filter(FinExpense.contract_id == contract_id)

    expenses = query.order_by(FinExpense.document_date.desc()).offset(skip).limit(limit).all()
    return expenses


# ==================== Analytics ====================

@router.get("/summary", response_model=CreditPortfolioSummary)
async def get_summary(
    department_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить общую статистику кредитного портфеля
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Receipts query
    receipts_query = db.query(func.sum(FinReceipt.amount)).filter(FinReceipt.is_active == True)
    if department_id:
        receipts_query = receipts_query.filter(FinReceipt.department_id == department_id)
    if date_from:
        receipts_query = receipts_query.filter(FinReceipt.document_date >= date_from)
    if date_to:
        receipts_query = receipts_query.filter(FinReceipt.document_date <= date_to)

    total_receipts = receipts_query.scalar() or 0

    # Expenses query
    expenses_query = db.query(func.sum(FinExpense.amount)).filter(FinExpense.is_active == True)
    if department_id:
        expenses_query = expenses_query.filter(FinExpense.department_id == department_id)
    if date_from:
        expenses_query = expenses_query.filter(FinExpense.document_date >= date_from)
    if date_to:
        expenses_query = expenses_query.filter(FinExpense.document_date <= date_to)

    total_expenses = expenses_query.scalar() or 0

    # Active contracts count
    contracts_query = db.query(func.count(FinContract.id)).filter(FinContract.is_active == True)
    if department_id:
        contracts_query = contracts_query.filter(FinContract.department_id == department_id)

    active_contracts_count = contracts_query.scalar() or 0

    # Calculate principal and interest from expense details
    details_query = db.query(
        func.sum(FinExpenseDetail.payment_amount)
    ).join(
        FinExpense, FinExpense.operation_id == FinExpenseDetail.expense_operation_id
    ).filter(FinExpense.is_active == True)

    if department_id:
        details_query = details_query.filter(FinExpenseDetail.department_id == department_id)

    # Principal (тело кредита)
    principal_query = details_query.filter(
        FinExpenseDetail.payment_type.ilike('%тело%')
    )
    total_principal = principal_query.scalar() or 0

    # Interest (проценты)
    interest_query = details_query.filter(
        FinExpenseDetail.payment_type.ilike('%процент%')
    )
    total_interest = interest_query.scalar() or 0

    return CreditPortfolioSummary(
        total_receipts=total_receipts,
        total_expenses=total_expenses,
        net_balance=total_receipts - total_expenses,
        active_contracts_count=active_contracts_count,
        total_principal=total_principal,
        total_interest=total_interest
    )


# ==================== Import Logs ====================

@router.get("/import-logs", response_model=List[FinImportLogInDB])
async def list_import_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """История импортов из 1С"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(FinImportLog)

    if department_id:
        query = query.filter(FinImportLog.department_id == department_id)

    logs = query.order_by(FinImportLog.import_date.desc()).offset(skip).limit(limit).all()
    return logs
