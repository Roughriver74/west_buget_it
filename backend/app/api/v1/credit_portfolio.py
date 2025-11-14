"""
Credit Portfolio API endpoints
Управление кредитным портфелем
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import date, datetime

logger = logging.getLogger(__name__)

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
    MonthlyStats,
)
from app.utils.auth import get_current_active_user

router = APIRouter()


def check_finance_access(user: User) -> bool:
    """Check if user has access to finance features"""
    return user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]


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

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Finance features available only for MANAGER, ADMIN"
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


@router.get("/contracts/stats/summary")
async def get_contracts_summary(
    department_id: Optional[int] = None,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by contract number or organization"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить агрегированную статистику по договорам

    Возвращает для каждого договора:
    - contractNumber: номер договора
    - organization: организация
    - contractType: тип договора
    - counterparty: контрагент
    - totalPaid: всего выплачено
    - principal: тело кредита
    - interest: проценты
    - operationsCount: количество операций
    - lastPayment: дата последнего платежа

    С пагинацией

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    from sqlalchemy import case
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Build aggregated query
    principal_expr = func.coalesce(
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%тело%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ),
        0
    ).label("principal")

    interest_expr = func.coalesce(
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%процент%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ),
        0
    ).label("interest")

    base_query = db.query(
        FinContract.id.label("contract_id"),
        FinContract.contract_number.label("contract_number"),
        FinContract.contract_type.label("contract_type"),
        FinContract.counterparty.label("counterparty"),
        FinOrganization.name.label("organization"),
        func.sum(FinExpense.amount).label('total_paid'),
        func.count(FinExpense.id).label('operations_count'),
        func.max(FinExpense.document_date).label('last_payment'),
        principal_expr,
        interest_expr
    ).join(
        FinExpense, FinExpense.contract_id == FinContract.id
    ).join(
        FinOrganization, FinExpense.organization_id == FinOrganization.id
    ).outerjoin(
        FinExpenseDetail, FinExpenseDetail.expense_operation_id == FinExpense.operation_id
    )

    # Apply filters
    if target_department_id:
        base_query = base_query.filter(FinContract.department_id == target_department_id)
    if date_from_obj:
        base_query = base_query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        base_query = base_query.filter(FinExpense.document_date <= date_to_obj)
    if organization_id:
        base_query = base_query.filter(FinExpense.organization_id == organization_id)
    if search:
        pattern = f"%{search}%"
        base_query = base_query.filter(
            (FinContract.contract_number.ilike(pattern)) |
            (FinOrganization.name.ilike(pattern)) |
            (FinContract.counterparty.ilike(pattern))
        )

    base_query = base_query.group_by(
        FinContract.id,
        FinContract.contract_number,
        FinContract.contract_type,
        FinContract.counterparty,
        FinOrganization.name
    )

    # Get total count for pagination
    total = base_query.count()

    # Apply pagination and sorting
    skip = (page - 1) * limit
    contracts_data = base_query.order_by(
        func.sum(FinExpense.amount).desc()
    ).offset(skip).limit(limit).all()

    # Format results
    contracts = []
    for row in contracts_data:
        contracts.append({
            "contractNumber": row.contract_number,
            "contractType": row.contract_type,
            "counterparty": row.counterparty,
            "organization": row.organization,
            "totalPaid": float(row.total_paid or 0),
            "principal": float(row.principal or 0),
            "interest": float(row.interest or 0),
            "operationsCount": int(row.operations_count or 0),
            "lastPayment": row.last_payment.isoformat() if row.last_payment else None
        })

    return {
        "data": contracts,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }


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


@router.get("/receipts/{receipt_id}", response_model=FinReceiptInDB)
async def get_receipt(
    receipt_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить поступление по ID

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    receipt = db.query(FinReceipt).filter(FinReceipt.id == receipt_id).first()

    if not receipt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER and receipt.department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to other department's data")

    return receipt


@router.get("/receipts/stats/summary")
async def get_receipts_summary(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    bank_account_id: Optional[int] = Query(None, description="Filter by bank account ID"),
    contract_id: Optional[int] = Query(None, description="Filter by contract ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить сводную статистику по поступлениям

    Возвращает:
    - total_records: количество записей
    - total_amount: общая сумма поступлений
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Build query
    query = db.query(FinReceipt)

    if target_department_id:
        query = query.filter(FinReceipt.department_id == target_department_id)
    if date_from_obj:
        query = query.filter(FinReceipt.document_date >= date_from_obj)
    if date_to_obj:
        query = query.filter(FinReceipt.document_date <= date_to_obj)
    if organization_id:
        query = query.filter(FinReceipt.organization_id == organization_id)
    if bank_account_id:
        query = query.filter(FinReceipt.bank_account_id == bank_account_id)
    if contract_id:
        query = query.filter(FinReceipt.contract_id == contract_id)

    # Get count and sum
    total_count = query.count()
    total_amount = query.with_entities(func.sum(FinReceipt.amount)).scalar() or 0

    return {
        "total_records": total_count,
        "total_amount": float(total_amount)
    }


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


@router.get("/expenses/{expense_id}", response_model=FinExpenseInDB)
async def get_expense(
    expense_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить списание по ID

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    expense = db.query(FinExpense).filter(FinExpense.id == expense_id).first()

    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER and expense.department_id != current_user.department_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to other department's data")

    return expense


@router.get("/expenses/stats/summary")
async def get_expenses_summary(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    bank_account_id: Optional[int] = Query(None, description="Filter by bank account ID"),
    contract_id: Optional[int] = Query(None, description="Filter by contract ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить сводную статистику по списаниям

    Возвращает:
    - total_records: количество записей
    - total_amount: общая сумма списаний
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Build query
    query = db.query(FinExpense)

    if target_department_id:
        query = query.filter(FinExpense.department_id == target_department_id)
    if date_from_obj:
        query = query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        query = query.filter(FinExpense.document_date <= date_to_obj)
    if organization_id:
        query = query.filter(FinExpense.organization_id == organization_id)
    if bank_account_id:
        query = query.filter(FinExpense.bank_account_id == bank_account_id)
    if contract_id:
        query = query.filter(FinExpense.contract_id == contract_id)

    # Get count and sum
    total_count = query.count()
    total_amount = query.with_entities(func.sum(FinExpense.amount)).scalar() or 0

    return {
        "total_records": total_count,
        "total_amount": float(total_amount)
    }


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


# ==================== Import from FTP ====================

@router.post("/import/trigger", status_code=status.HTTP_200_OK)
async def trigger_ftp_import(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Запустить автоматический импорт данных из 1С через FTP

    Процесс:
    1. Подключение к FTP серверу
    2. Загрузка XLSX файлов
    3. Парсинг файлов (поступления, списания, расшифровка)
    4. Импорт в БД с UPSERT логикой
    5. Авто-создание организаций, счетов, договоров

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id (общий FTP для всех отделов по умолчанию)
    target_department_id = department_id if department_id else current_user.department_id
    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID must be specified"
        )

    try:
        from app.services.credit_portfolio_ftp import download_credit_portfolio_files
        from app.services.credit_portfolio_importer import CreditPortfolioImporter

        # Step 1: Download files from FTP
        downloaded_files = download_credit_portfolio_files()

        if not downloaded_files:
            return {
                "success": False,
                "message": "No files downloaded from FTP server",
                "files_processed": 0,
                "files_failed": 0
            }

        # Step 2: Import files
        importer = CreditPortfolioImporter(db, target_department_id)
        summary = importer.import_files(downloaded_files)

        return {
            "success": summary["success"] > 0,
            "message": f"Import completed: {summary['success']}/{summary['total']} files imported",
            "files_processed": summary["success"],
            "files_failed": summary["failed"],
            "total_files": summary["total"],
            "department_id": target_department_id
        }

    except Exception as e:
        logger.error(f"Error during FTP import: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


# ==================== Advanced Analytics ====================

@router.get("/analytics/monthly-efficiency")
async def get_monthly_efficiency(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    bank_account_id: Optional[int] = Query(None, description="Filter by bank account ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить месячную эффективность платежей (тело кредита vs проценты)

    Возвращает данные для графиков по месяцам:
    - principal: тело кредита
    - interest: проценты
    - total: общая сумма
    - efficiency: эффективность (principal/total * 100)

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Build query with date grouping
    from sqlalchemy import case, extract

    month_col = func.date_trunc('month', FinExpense.document_date)
    query = db.query(
        month_col.label('month'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%тело%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('principal'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%процент%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('interest')
    ).join(
        FinExpenseDetail,
        FinExpense.operation_id == FinExpenseDetail.expense_operation_id
    )

    # Apply filters
    if target_department_id:
        query = query.filter(FinExpense.department_id == target_department_id)
    if date_from_obj:
        query = query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        query = query.filter(FinExpense.document_date <= date_to_obj)
    if organization_id:
        query = query.filter(FinExpense.organization_id == organization_id)
    if bank_account_id:
        query = query.filter(FinExpense.bank_account_id == bank_account_id)

    query = query.group_by(month_col).order_by(month_col)

    results = query.all()

    # Format data
    data = []
    for row in results:
        if row.month:
            principal = float(row.principal or 0)
            interest = float(row.interest or 0)
            total = principal + interest
            efficiency = (principal / total * 100) if total > 0 else 0

            data.append({
                "month": row.month.strftime('%Y-%m'),
                "principal": principal,
                "interest": interest,
                "total": total,
                "efficiency": round(efficiency, 2)
            })

    return {"data": data}


@router.get("/analytics/org-efficiency")
async def get_org_efficiency(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить эффективность по организациям

    Возвращает данные для сравнения организаций:
    - totalPaid: всего выплачено
    - principal: тело кредита
    - interest: проценты
    - received: получено
    - efficiency: эффективность (principal/totalPaid * 100)
    - debtRatio: коэффициент долга ((received-principal)/received * 100)

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Subquery for receipts per organization
    from sqlalchemy import case

    receipts_subq = db.query(
        FinOrganization.id.label("organization_id"),
        func.sum(FinReceipt.amount).label('received')
    ).join(
        FinReceipt, FinReceipt.organization_id == FinOrganization.id
    )

    if target_department_id:
        receipts_subq = receipts_subq.filter(FinReceipt.department_id == target_department_id)
    if date_from_obj:
        receipts_subq = receipts_subq.filter(FinReceipt.document_date >= date_from_obj)
    if date_to_obj:
        receipts_subq = receipts_subq.filter(FinReceipt.document_date <= date_to_obj)

    receipts_subq = receipts_subq.group_by(FinOrganization.id).subquery()

    # Main query for expenses with principal/interest breakdown
    query = db.query(
        FinOrganization.id.label("organization_id"),
        FinOrganization.name.label("organization"),
        func.sum(FinExpense.amount).label('total_paid'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%тело%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('principal'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%процент%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('interest'),
        func.coalesce(receipts_subq.c.received, 0).label('received')
    ).join(
        FinExpenseDetail,
        FinExpense.operation_id == FinExpenseDetail.expense_operation_id
    ).join(
        FinOrganization,
        FinExpense.organization_id == FinOrganization.id
    ).outerjoin(
        receipts_subq,
        FinOrganization.id == receipts_subq.c.organization_id
    )

    if target_department_id:
        query = query.filter(FinExpense.department_id == target_department_id)
    if date_from_obj:
        query = query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        query = query.filter(FinExpense.document_date <= date_to_obj)

    query = query.group_by(
        FinOrganization.id,
        FinOrganization.name,
        receipts_subq.c.received
    ).order_by(func.sum(FinExpense.amount).desc())

    results = query.all()

    # Format data
    data = []
    for row in results:
        total_paid = float(row.total_paid or 0)
        principal = float(row.principal or 0)
        interest = float(row.interest or 0)
        received = float(row.received or 0)

        efficiency = (principal / total_paid * 100) if total_paid > 0 else 0
        debt_ratio = ((received - principal) / received * 100) if received > 0 else 0

        data.append({
            "name": row.organization or 'Не указано',
            "totalPaid": total_paid,
            "principal": principal,
            "interest": interest,
            "received": received,
            "efficiency": round(efficiency, 2),
            "debtRatio": round(debt_ratio, 2)
        })

    return {"data": data}


@router.get("/analytics/cashflow-monthly")
async def get_monthly_cashflow(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    organization_id: Optional[int] = Query(None, description="Filter by organization ID"),
    bank_account_id: Optional[int] = Query(None, description="Filter by bank account ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить месячный денежный поток (поступления vs списания)

    Возвращает данные для графиков:
    - inflow: поступления
    - outflow: списания
    - net: чистый поток (inflow - outflow)
    - cumulative: накопительный итог

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Receipts by month
    receipts_month_col = func.date_trunc('month', FinReceipt.document_date)
    receipts_query = db.query(
        receipts_month_col.label('month'),
        func.sum(FinReceipt.amount).label('inflow')
    )

    if target_department_id:
        receipts_query = receipts_query.filter(FinReceipt.department_id == target_department_id)
    if date_from_obj:
        receipts_query = receipts_query.filter(FinReceipt.document_date >= date_from_obj)
    if date_to_obj:
        receipts_query = receipts_query.filter(FinReceipt.document_date <= date_to_obj)
    if organization_id:
        receipts_query = receipts_query.filter(FinReceipt.organization_id == organization_id)
    if bank_account_id:
        receipts_query = receipts_query.filter(FinReceipt.bank_account_id == bank_account_id)

    receipts_query = receipts_query.group_by(receipts_month_col)
    receipts_subq = receipts_query.subquery()

    # Expenses by month
    expenses_month_col = func.date_trunc('month', FinExpense.document_date)
    expenses_query = db.query(
        expenses_month_col.label('month'),
        func.sum(FinExpense.amount).label('outflow')
    )

    if target_department_id:
        expenses_query = expenses_query.filter(FinExpense.department_id == target_department_id)
    if date_from_obj:
        expenses_query = expenses_query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        expenses_query = expenses_query.filter(FinExpense.document_date <= date_to_obj)
    if organization_id:
        expenses_query = expenses_query.filter(FinExpense.organization_id == organization_id)
    if bank_account_id:
        expenses_query = expenses_query.filter(FinExpense.bank_account_id == bank_account_id)

    expenses_query = expenses_query.group_by(expenses_month_col)
    expenses_subq = expenses_query.subquery()

    # Combine receipts and expenses using full outer join
    query = db.query(
        func.coalesce(receipts_subq.c.month, expenses_subq.c.month).label('month'),
        func.coalesce(receipts_subq.c.inflow, 0).label('inflow'),
        func.coalesce(expenses_subq.c.outflow, 0).label('outflow')
    ).select_from(receipts_subq).outerjoin(
        expenses_subq,
        receipts_subq.c.month == expenses_subq.c.month,
        full=True
    ).order_by(func.coalesce(receipts_subq.c.month, expenses_subq.c.month))

    results = query.all()

    # Calculate cumulative and format data
    cumulative = 0
    data = []

    for row in results:
        if row.month:
            inflow = float(row.inflow or 0)
            outflow = float(row.outflow or 0)
            net = inflow - outflow
            cumulative += net

            data.append({
                "month": row.month.strftime('%Y-%m'),
                "inflow": inflow,
                "outflow": outflow,
                "net": net,
                "cumulative": cumulative
            })

    return {"data": data}


@router.get("/analytics/yearly-comparison")
async def get_yearly_comparison(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить сравнение по годам

    Возвращает данные для year-over-year анализа:
    - year: год
    - received: получено
    - principal: тело кредита
    - interest: проценты
    - paid: всего выплачено
    - receivedGrowth: рост поступлений (%)
    - paidGrowth: рост выплат (%)

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Determine department_id based on role
    target_department_id = department_id
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif not target_department_id and current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        target_department_id = current_user.department_id

    # Parse dates
    from datetime import datetime as dt
    from sqlalchemy import case, extract
    date_from_obj = dt.strptime(date_from, '%Y-%m-%d').date() if date_from else None
    date_to_obj = dt.strptime(date_to, '%Y-%m-%d').date() if date_to else None

    # Receipts by year
    receipts_query = db.query(
        extract('year', FinReceipt.document_date).label('year'),
        func.sum(FinReceipt.amount).label('received')
    )

    if target_department_id:
        receipts_query = receipts_query.filter(FinReceipt.department_id == target_department_id)
    if date_from_obj:
        receipts_query = receipts_query.filter(FinReceipt.document_date >= date_from_obj)
    if date_to_obj:
        receipts_query = receipts_query.filter(FinReceipt.document_date <= date_to_obj)

    receipts_query = receipts_query.group_by(extract('year', FinReceipt.document_date)).order_by(
        extract('year', FinReceipt.document_date)
    )

    receipts_by_year = receipts_query.all()

    # Expenses by year
    expenses_query = db.query(
        extract('year', FinExpense.document_date).label('year'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%тело%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('principal'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type.ilike('%процент%'), FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('interest')
    ).outerjoin(
        FinExpenseDetail,
        FinExpense.operation_id == FinExpenseDetail.expense_operation_id
    )

    if target_department_id:
        expenses_query = expenses_query.filter(FinExpense.department_id == target_department_id)
    if date_from_obj:
        expenses_query = expenses_query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        expenses_query = expenses_query.filter(FinExpense.document_date <= date_to_obj)

    expenses_query = expenses_query.group_by(extract('year', FinExpense.document_date)).order_by(
        extract('year', FinExpense.document_date)
    )

    expenses_by_year = expenses_query.all()

    # Combine results
    years_data = {}

    for row in receipts_by_year:
        if row.year:
            year_key = str(int(row.year))
            years_data[year_key] = {
                "year": year_key,
                "received": float(row.received or 0),
                "principal": 0,
                "interest": 0,
                "paid": 0
            }

    for row in expenses_by_year:
        if row.year:
            year_key = str(int(row.year))
            if year_key not in years_data:
                years_data[year_key] = {
                    "year": year_key,
                    "received": 0,
                    "principal": 0,
                    "interest": 0,
                    "paid": 0
                }

            principal = float(row.principal or 0)
            interest = float(row.interest or 0)

            years_data[year_key]["principal"] = principal
            years_data[year_key]["interest"] = interest
            years_data[year_key]["paid"] = principal + interest

    # Calculate growth rates
    data = sorted(years_data.values(), key=lambda x: x['year'])

    for i in range(1, len(data)):
        current = data[i]
        previous = data[i - 1]

        received_growth = 0
        if previous['received'] > 0:
            received_growth = ((current['received'] - previous['received']) / previous['received'] * 100)

        paid_growth = 0
        if previous['paid'] > 0:
            paid_growth = ((current['paid'] - previous['paid']) / previous['paid'] * 100)

        current['receivedGrowth'] = round(received_growth, 2)
        current['paidGrowth'] = round(paid_growth, 2)

    return {"data": data}
