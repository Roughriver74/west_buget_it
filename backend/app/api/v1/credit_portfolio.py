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
from app.services.cache import cache_service

router = APIRouter()


FINANCE_DEPARTMENT_ID = 8  # ID отдела "Финансы"
FINANCE_DEPARTMENT_CODE = "FIN"

# Cache namespace for credit portfolio analytics
CACHE_NAMESPACE = "credit_portfolio"


def check_finance_access(user: User) -> bool:
    """
    Check if user has access to credit portfolio features

    Access rules:
    - ADMIN: ALWAYS has access (regardless of department)
    - MANAGER: Must belong to Finance department (ID=8)
    - USER: No access
    """
    # ADMIN sees everything
    if user.role == UserRoleEnum.ADMIN:
        return True

    # MANAGER must be from Finance department
    if user.role == UserRoleEnum.MANAGER:
        return user.department_id == FINANCE_DEPARTMENT_ID

    # USER has no access
    return False


def invalidate_analytics_cache():
    """Invalidate all analytics cache when data changes"""
    cache_service.invalidate_namespace(CACHE_NAMESPACE)


# ==================== Organizations ====================

@router.get("/organizations", response_model=List[FinOrganizationInDB])
async def list_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.CREDIT_PORTFOLIO_PAGE_SIZE, ge=1, le=settings.MAX_CREDIT_PORTFOLIO_PAGE_SIZE),
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

    # Credit portfolio is ALWAYS tied to Finance department
    department_id = FINANCE_DEPARTMENT_ID

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
    limit: int = Query(settings.CREDIT_PORTFOLIO_PAGE_SIZE, ge=1, le=settings.MAX_CREDIT_PORTFOLIO_PAGE_SIZE),
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

    # Credit portfolio is ALWAYS tied to Finance department
    department_id = FINANCE_DEPARTMENT_ID

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
    limit: int = Query(settings.CREDIT_PORTFOLIO_PAGE_SIZE, ge=1, le=settings.MAX_CREDIT_PORTFOLIO_PAGE_SIZE),
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    contract_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Список кредитных договоров с расчетными полями"""
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    from sqlalchemy import case

    # Build query with calculated fields
    principal_expr = func.coalesce(
        func.sum(
            case(
                (FinExpenseDetail.payment_type == 'Погашение долга', FinExpenseDetail.payment_amount),
                else_=0
            )
        ),
        0
    ).label("principal")

    interest_expr = func.coalesce(
        func.sum(
            case(
                (FinExpenseDetail.payment_type == 'Уплата процентов', FinExpenseDetail.payment_amount),
                else_=0
            )
        ),
        0
    ).label("interest")

    query = db.query(
        FinContract,
        func.coalesce(func.sum(FinExpense.amount), 0).label('total_paid'),
        principal_expr,
        interest_expr
    ).outerjoin(
        FinExpense, FinExpense.contract_id == FinContract.id
    ).outerjoin(
        FinExpenseDetail, FinExpenseDetail.expense_operation_id == FinExpense.operation_id
    )

    if department_id:
        query = query.filter(FinContract.department_id == department_id)

    if is_active is not None:
        query = query.filter(FinContract.is_active == is_active)

    if contract_type:
        query = query.filter(FinContract.contract_type == contract_type)

    query = query.group_by(FinContract.id)

    results = query.offset(skip).limit(limit).all()

    # Build response with calculated fields
    contracts = []
    for contract, total_paid, principal, interest in results:
        contract_dict = {
            "id": contract.id,
            "contract_number": contract.contract_number,
            "contract_date": contract.contract_date,
            "contract_type": contract.contract_type,
            "counterparty": contract.counterparty,
            "is_active": contract.is_active,
            "department_id": contract.department_id,
            "created_at": contract.created_at,
            "updated_at": contract.updated_at,
            "total_paid": total_paid,
            "principal": principal,
            "interest": interest
        }
        contracts.append(FinContractInDB(**contract_dict))

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

    # Credit portfolio is ALWAYS tied to Finance department
    department_id = FINANCE_DEPARTMENT_ID

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
                (FinExpenseDetail.payment_type == 'Погашение долга', FinExpenseDetail.payment_amount),
                else_=0
            )
        ),
        0
    ).label("principal")

    interest_expr = func.coalesce(
        func.sum(
            case(
                (FinExpenseDetail.payment_type == 'Уплата процентов', FinExpenseDetail.payment_amount),
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


@router.get("/contract-stats")
async def get_contract_stats(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить базовую статистику по договорам

    Возвращает:
    - total_count: всего договоров
    - active_count: активных договоров
    - closed_count: закрытых договоров

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

    # Build base query
    query = db.query(FinContract)

    if target_department_id:
        query = query.filter(FinContract.department_id == target_department_id)

    # Total count
    total_count = query.count()

    # Active count
    active_count = query.filter(FinContract.is_active == True).count()

    # Closed count
    closed_count = total_count - active_count

    return {
        "total_count": total_count,
        "active_count": active_count,
        "closed_count": closed_count
    }


# ==================== Receipts ====================

@router.get("/receipts", response_model=List[FinReceiptInDB])
async def list_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.CREDIT_PORTFOLIO_PAGE_SIZE, ge=1, le=settings.MAX_CREDIT_PORTFOLIO_PAGE_SIZE),
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
    limit: int = Query(settings.CREDIT_PORTFOLIO_PAGE_SIZE, ge=1, le=settings.MAX_CREDIT_PORTFOLIO_PAGE_SIZE),
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


# ==================== Expense Details ====================

@router.get("/expense-details", response_model=List[FinExpenseDetailInDB])
async def list_expense_details(
    skip: int = Query(0, ge=0),
    limit: int = Query(settings.CREDIT_PORTFOLIO_PAGE_SIZE, ge=1, le=settings.MAX_CREDIT_PORTFOLIO_PAGE_SIZE),
    department_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить детализированные записи списаний (тело/проценты)

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    query = db.query(FinExpenseDetail).join(
        FinExpense, FinExpense.operation_id == FinExpenseDetail.expense_operation_id
    )

    if department_id:
        query = query.filter(FinExpenseDetail.department_id == department_id)

    if date_from:
        query = query.filter(FinExpense.document_date >= date_from)

    if date_to:
        query = query.filter(FinExpense.document_date <= date_to)

    details = query.order_by(FinExpense.document_date.desc()).offset(skip).limit(limit).all()
    return details


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

    # Build cache key
    cache_key = cache_service.build_key(
        "summary",
        department_id,
        date_from.isoformat() if date_from else None,
        date_to.isoformat() if date_to else None
    )

    # Try to get from cache
    cached_result = cache_service.get(CACHE_NAMESPACE, cache_key)
    if cached_result is not None:
        return CreditPortfolioSummary(**cached_result)

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
        FinExpenseDetail.payment_type == 'Погашение долга'
    )
    total_principal = principal_query.scalar() or 0

    # Interest (проценты)
    interest_query = details_query.filter(
        FinExpenseDetail.payment_type == 'Уплата процентов'
    )
    total_interest = interest_query.scalar() or 0

    result = CreditPortfolioSummary(
        total_receipts=total_receipts,
        total_expenses=total_expenses,
        net_balance=total_receipts - total_expenses,
        active_contracts_count=active_contracts_count,
        total_principal=total_principal,
        total_interest=total_interest
    )

    # Cache the result (5 minutes)
    cache_service.set(CACHE_NAMESPACE, cache_key, result.model_dump())

    return result


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

    # Credit portfolio is ALWAYS tied to Finance department
    target_department_id = FINANCE_DEPARTMENT_ID

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

        # Invalidate analytics cache after successful import
        if summary["success"] > 0:
            invalidate_analytics_cache()
            logger.info(f"Invalidated analytics cache after importing {summary['success']} files")

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

@router.get("/monthly-stats", response_model=list[MonthlyStats])
async def get_monthly_stats(
    department_id: Optional[int] = None,
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить помесячную статистику (поступления vs списания)

    Возвращает данные по месяцам:
    - month: месяц (YYYY-MM-01)
    - receipts: сумма поступлений
    - expenses: сумма списаний
    - net: чистый баланс (receipts - expenses)

    Доступ: только MANAGER, ADMIN
    """
    if not check_finance_access(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Build cache key
    cache_key = cache_service.build_key(
        "monthly_stats",
        department_id,
        date_from,
        date_to
    )

    # Try to get from cache
    cached_result = cache_service.get(CACHE_NAMESPACE, cache_key)
    if cached_result is not None:
        cleaned_result = [item for item in cached_result if item.get('month')]
        if len(cleaned_result) != len(cached_result):
            cache_service.set(CACHE_NAMESPACE, cache_key, cleaned_result)
        return [MonthlyStats(**item) for item in cleaned_result]

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
        func.sum(FinReceipt.amount).label('receipts')
    ).filter(
        FinReceipt.is_active == True,
        FinReceipt.document_date.isnot(None)
    )

    if target_department_id:
        receipts_query = receipts_query.filter(FinReceipt.department_id == target_department_id)
    if date_from_obj:
        receipts_query = receipts_query.filter(FinReceipt.document_date >= date_from_obj)
    if date_to_obj:
        receipts_query = receipts_query.filter(FinReceipt.document_date <= date_to_obj)

    receipts_subq = receipts_query.group_by(receipts_month_col).subquery()

    # Expenses by month
    expenses_month_col = func.date_trunc('month', FinExpense.document_date)
    expenses_query = db.query(
        expenses_month_col.label('month'),
        func.sum(FinExpense.amount).label('expenses')
    ).filter(
        FinExpense.is_active == True,
        FinExpense.document_date.isnot(None)
    )

    if target_department_id:
        expenses_query = expenses_query.filter(FinExpense.department_id == target_department_id)
    if date_from_obj:
        expenses_query = expenses_query.filter(FinExpense.document_date >= date_from_obj)
    if date_to_obj:
        expenses_query = expenses_query.filter(FinExpense.document_date <= date_to_obj)

    expenses_subq = expenses_query.group_by(expenses_month_col).subquery()

    # Combine receipts and expenses
    query = db.query(
        func.coalesce(receipts_subq.c.month, expenses_subq.c.month).label('month'),
        func.coalesce(receipts_subq.c.receipts, 0).label('receipts'),
        func.coalesce(expenses_subq.c.expenses, 0).label('expenses')
    ).select_from(receipts_subq).outerjoin(
        expenses_subq,
        receipts_subq.c.month == expenses_subq.c.month,
        full=True
    ).order_by(func.coalesce(receipts_subq.c.month, expenses_subq.c.month))

    results = query.all()

    # Format response
    data = []
    for row in results:
        if not row.month:
            continue
        month_str = row.month.strftime('%Y-%m-%d')
        receipts = float(row.receipts) if row.receipts else 0
        expenses = float(row.expenses) if row.expenses else 0
        net = receipts - expenses

        data.append({
            "month": month_str,
            "receipts": receipts,
            "expenses": expenses,
            "net": net
        })

    # Cache the result (5 minutes)
    cache_service.set(CACHE_NAMESPACE, cache_key, data)

    return data


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

    # Build cache key
    cache_key = cache_service.build_key(
        "monthly_efficiency",
        department_id,
        date_from,
        date_to,
        organization_id,
        bank_account_id
    )

    # Try to get from cache
    cached_result = cache_service.get(CACHE_NAMESPACE, cache_key)
    if cached_result is not None:
        return cached_result

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
                (FinExpenseDetail.payment_type == 'Погашение долга', FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('principal'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type == 'Уплата процентов', FinExpenseDetail.payment_amount),
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

    result = {"data": data}

    # Cache the result (5 minutes)
    cache_service.set(CACHE_NAMESPACE, cache_key, result)

    return result


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
                (FinExpenseDetail.payment_type == 'Погашение долга', FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('principal'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type == 'Уплата процентов', FinExpenseDetail.payment_amount),
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
                (FinExpenseDetail.payment_type == 'Погашение долга', FinExpenseDetail.payment_amount),
                else_=0
            )
        ).label('principal'),
        func.sum(
            case(
                (FinExpenseDetail.payment_type == 'Уплата процентов', FinExpenseDetail.payment_amount),
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


# ==================== Test Data ====================

@router.post("/load-test-data")
async def load_test_data(
    force: bool = Query(False, description="Force reload, deleting existing data"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Загрузить тестовые данные для кредитного портфеля

    Создает:
    - 3 организации (Сбербанк, ВТБ, Альфа-Банк)
    - 3 банковских счета
    - 3 кредитных договора
    - Поступления (получение кредитов) за 2023-2025
    - Списания (погашение кредитов) за 2023-2025
    - Детализацию платежей (тело/проценты)

    Доступ: только ADMIN
    """
    # Only ADMIN can load test data
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can load test data"
        )

    try:
        # Use Finance department (ID=8)
        department_id = FINANCE_DEPARTMENT_ID

        # Check if test data already exists
        existing_orgs = db.query(FinOrganization).filter(
            FinOrganization.department_id == department_id,
            FinOrganization.inn.in_(['7707083893', '7702070139', '7728168971'])  # Test INNs
        ).count()

        if existing_orgs > 0 and not force:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test data already exists ({existing_orgs} test organizations found). Use force=true to reload."
            )

        if existing_orgs > 0 and force:
            logger.info(f"Deleting existing test data for department {department_id}...")

            # Get test organization IDs
            test_org_ids = [org.id for org in db.query(FinOrganization).filter(
                FinOrganization.department_id == department_id,
                FinOrganization.inn.in_(['7707083893', '7702070139', '7728168971'])
            ).all()]

            # Delete in correct order (respecting foreign keys)
            db.query(FinExpenseDetail).filter(
                FinExpenseDetail.expense_operation_id.in_(
                    db.query(FinExpense.operation_id).filter(
                        FinExpense.organization_id.in_(test_org_ids)
                    )
                )
            ).delete(synchronize_session=False)

            db.query(FinExpense).filter(
                FinExpense.organization_id.in_(test_org_ids)
            ).delete(synchronize_session=False)

            db.query(FinReceipt).filter(
                FinReceipt.organization_id.in_(test_org_ids)
            ).delete(synchronize_session=False)

            db.query(FinContract).filter(
                FinContract.department_id == department_id,
                FinContract.counterparty.in_(['ПАО Сбербанк', 'ВТБ (ПАО)', "АО 'Альфа-Банк'"])
            ).delete(synchronize_session=False)

            db.query(FinBankAccount).filter(
                FinBankAccount.department_id == department_id,
                FinBankAccount.account_number.like('4070281000000000%')
            ).delete(synchronize_session=False)

            db.query(FinOrganization).filter(
                FinOrganization.id.in_(test_org_ids)
            ).delete(synchronize_session=False)

            db.commit()
            logger.info("Deleted existing test data")

        # Import the test data creation function
        from datetime import timedelta
        from decimal import Decimal

        logger.info(f"Creating test data for department_id={department_id}")

        # 1. Create Organizations
        organizations = []
        org_data = [
            {"name": "ПАО Сбербанк", "inn": "7707083893"},
            {"name": "ВТБ (ПАО)", "inn": "7702070139"},
            {"name": "АО 'Альфа-Банк'", "inn": "7728168971"},
        ]

        for data in org_data:
            org = FinOrganization(
                name=data["name"],
                inn=data["inn"],
                is_active=True,
                department_id=department_id,
            )
            db.add(org)
            organizations.append(org)

        db.commit()
        db.refresh(organizations[0])
        db.refresh(organizations[1])
        db.refresh(organizations[2])

        # 2. Create Bank Accounts
        bank_accounts = []
        bank_names = ["Сбербанк", "ВТБ", "Альфа-Банк"]
        for i, org in enumerate(organizations, 1):
            account = FinBankAccount(
                account_number=f"4070281000000000{i:04d}",
                bank_name=bank_names[i-1],
                is_active=True,
                department_id=department_id,
            )
            db.add(account)
            bank_accounts.append(account)

        db.commit()
        db.refresh(bank_accounts[0])
        db.refresh(bank_accounts[1])
        db.refresh(bank_accounts[2])

        # 3. Create Contracts
        contracts = []
        contract_data = [
            {"number": "КД-001/2023", "date": "2023-01-15", "type": "Кредитный договор", "counterparty": "ПАО Сбербанк"},
            {"number": "КД-002/2023", "date": "2023-06-20", "type": "Кредитный договор", "counterparty": "ВТБ (ПАО)"},
            {"number": "КД-003/2024", "date": "2024-01-10", "type": "Кредитный договор", "counterparty": "АО 'Альфа-Банк'"},
        ]

        for data in contract_data:
            contract = FinContract(
                contract_number=data["number"],
                contract_date=datetime.strptime(data["date"], "%Y-%m-%d").date(),
                contract_type=data["type"],
                counterparty=data["counterparty"],
                is_active=True,
                department_id=department_id,
            )
            db.add(contract)
            contracts.append(contract)

        db.commit()
        db.refresh(contracts[0])
        db.refresh(contracts[1])
        db.refresh(contracts[2])

        # 4. Create Receipts
        receipts_count = 0

        # Contract 1 - 2023
        for date_str, amount in [("2023-02-01", 5000000), ("2023-07-01", 3000000)]:
            receipt = FinReceipt(
                operation_id=f"RCP-{date_str}-001",
                organization_id=organizations[0].id,
                bank_account_id=bank_accounts[0].id,
                contract_id=contracts[0].id,
                operation_type="Получение кредита",
                document_number=f"ПП-{date_str}",
                document_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                payer=organizations[0].name,
                payment_purpose=f"Предоставление кредита по договору {contracts[0].contract_number}",
                currency="RUB",
                amount=Decimal(str(amount)),
                is_active=True,
                department_id=department_id,
            )
            db.add(receipt)
            receipts_count += 1

        # Contract 2 - 2023
        receipt = FinReceipt(
            operation_id="RCP-2023-08-01-002",
            organization_id=organizations[1].id,
            bank_account_id=bank_accounts[1].id,
            contract_id=contracts[1].id,
            operation_type="Получение кредита",
            document_number="ПП-2023-08-01",
            document_date=datetime.strptime("2023-08-01", "%Y-%m-%d").date(),
            payer=organizations[1].name,
            payment_purpose=f"Предоставление кредита по договору {contracts[1].contract_number}",
            currency="RUB",
            amount=Decimal("4000000"),
            is_active=True,
            department_id=department_id,
        )
        db.add(receipt)
        receipts_count += 1

        # Contract 3 - 2024
        for date_str, amount in [("2024-02-01", 6000000), ("2024-08-01", 2000000)]:
            receipt = FinReceipt(
                operation_id=f"RCP-{date_str}-003",
                organization_id=organizations[2].id,
                bank_account_id=bank_accounts[2].id,
                contract_id=contracts[2].id,
                operation_type="Получение кредита",
                document_number=f"ПП-{date_str}",
                document_date=datetime.strptime(date_str, "%Y-%m-%d").date(),
                payer=organizations[2].name,
                payment_purpose=f"Предоставление кредита по договору {contracts[2].contract_number}",
                currency="RUB",
                amount=Decimal(str(amount)),
                is_active=True,
                department_id=department_id,
            )
            db.add(receipt)
            receipts_count += 1

        # 2025 data
        receipt = FinReceipt(
            operation_id="RCP-2025-01-15-001",
            organization_id=organizations[0].id,
            bank_account_id=bank_accounts[0].id,
            contract_id=contracts[0].id,
            operation_type="Получение кредита",
            document_number="ПП-2025-01-15",
            document_date=datetime.strptime("2025-01-15", "%Y-%m-%d").date(),
            payer=organizations[0].name,
            payment_purpose=f"Предоставление кредита по договору {contracts[0].contract_number}",
            currency="RUB",
            amount=Decimal("3500000"),
            is_active=True,
            department_id=department_id,
        )
        db.add(receipt)
        receipts_count += 1

        db.commit()

        # 5. Create Expenses (simplified version)
        expenses_count = 0
        details_count = 0

        # Contract 1 - 2024 payments (12 months)
        start_date = datetime(2024, 1, 1)
        for month in range(12):
            payment_date = start_date + timedelta(days=30 * month)
            expense = FinExpense(
                operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-001",
                organization_id=organizations[0].id,
                bank_account_id=bank_accounts[0].id,
                contract_id=contracts[0].id,
                operation_type="Погашение кредита",
                document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}",
                document_date=payment_date.date(),
                recipient=organizations[0].name,
                payment_purpose=f"Погашение кредита по договору {contracts[0].contract_number}",
                currency="RUB",
                amount=Decimal("420000"),
                expense_article="Погашение кредитов",
                unconfirmed_by_bank=False,
                is_active=True,
                department_id=department_id,
            )
            db.add(expense)
            db.flush()

            # Add details
            total = 420000
            principal_amount = total * 0.75
            interest_amount = total * 0.25

            detail_principal = FinExpenseDetail(
                expense_operation_id=expense.operation_id,
                payment_type="Погашение долга",
                payment_amount=Decimal(str(principal_amount)),
                settlement_amount=Decimal(str(principal_amount)),
                expense_amount=Decimal(str(principal_amount)),
                department_id=department_id,
            )
            db.add(detail_principal)

            detail_interest = FinExpenseDetail(
                expense_operation_id=expense.operation_id,
                payment_type="проценты",
                payment_amount=Decimal(str(interest_amount)),
                settlement_amount=Decimal(str(interest_amount)),
                expense_amount=Decimal(str(interest_amount)),
                department_id=department_id,
            )
            db.add(detail_interest)

            expenses_count += 1
            details_count += 2

        # 2025 payments for all contracts
        start_date = datetime(2025, 1, 1)
        for month in range(3):  # January to March 2025
            for contract_idx, org in enumerate(organizations):
                payment_date = start_date + timedelta(days=30 * month)
                amounts = [400000, 350000, 480000]

                expense = FinExpense(
                    operation_id=f"EXP-{payment_date.strftime('%Y-%m-%d')}-{contract_idx+1:03d}",
                    organization_id=org.id,
                    bank_account_id=bank_accounts[contract_idx].id,
                    contract_id=contracts[contract_idx].id,
                    operation_type="Погашение кредита",
                    document_number=f"ПП-{payment_date.strftime('%Y-%m-%d')}-{contract_idx+1}",
                    document_date=payment_date.date(),
                    recipient=org.name,
                    payment_purpose=f"Погашение кредита по договору {contracts[contract_idx].contract_number}",
                    currency="RUB",
                    amount=Decimal(str(amounts[contract_idx])),
                    expense_article="Погашение кредитов",
                    unconfirmed_by_bank=False,
                    is_active=True,
                    department_id=department_id,
                )
                db.add(expense)
                db.flush()

                # Add details
                total = amounts[contract_idx]
                principal_amount = total * 0.75
                interest_amount = total * 0.25

                detail_principal = FinExpenseDetail(
                    expense_operation_id=expense.operation_id,
                    payment_type="Погашение долга",
                    payment_amount=Decimal(str(principal_amount)),
                    settlement_amount=Decimal(str(principal_amount)),
                    expense_amount=Decimal(str(principal_amount)),
                    department_id=department_id,
                )
                db.add(detail_principal)

                detail_interest = FinExpenseDetail(
                    expense_operation_id=expense.operation_id,
                    payment_type="проценты",
                    payment_amount=Decimal(str(interest_amount)),
                    settlement_amount=Decimal(str(interest_amount)),
                    expense_amount=Decimal(str(interest_amount)),
                    department_id=department_id,
                )
                db.add(detail_interest)

                expenses_count += 1
                details_count += 2

        db.commit()

        # Invalidate cache
        invalidate_analytics_cache()

        logger.info(f"Test data created successfully: {len(organizations)} orgs, {len(bank_accounts)} accounts, "
                   f"{len(contracts)} contracts, {receipts_count} receipts, {expenses_count} expenses, {details_count} details")

        return {
            "success": True,
            "message": "Test data loaded successfully",
            "data": {
                "organizations": len(organizations),
                "bank_accounts": len(bank_accounts),
                "contracts": len(contracts),
                "receipts": receipts_count,
                "expenses": expenses_count,
                "expense_details": details_count
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error loading test data: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load test data: {str(e)}"
        )
