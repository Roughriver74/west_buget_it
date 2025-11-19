"""
API endpoints for Bank Transactions
Управление банковскими операциями (списаниями и поступлениями)
"""
from typing import List, Optional
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import io
import logging

from app.db import get_db
from app.db.session import SessionLocal
from app.db.models import (
    BankTransaction,
    BankTransactionStatusEnum,
    BankTransactionTypeEnum,
    User,
    UserRoleEnum,
    BudgetCategory,
    Expense,
    ExpenseStatusEnum,
    Organization,
    Department,
    RegionEnum,
)
from app.schemas.bank_transaction import (
    BankTransactionCreate,
    BankTransactionUpdate,
    BankTransactionCategorize,
    BankTransactionLink,
    BankTransactionInDB,
    BankTransactionWithRelations,
    BankTransactionList,
    BankTransactionStats,
    BankTransactionImportResult,
    MatchingSuggestion,
    CategorySuggestion,
    BulkCategorizeRequest,
    BulkLinkRequest,
    BulkStatusUpdateRequest,
    ODataSyncRequest,
    ODataSyncResult,
    ODataTestConnectionRequest,
    ODataTestConnectionResult,
    BankTransactionAnalytics,
    BankTransactionKPIs,
    MonthlyFlowData,
    CategoryBreakdown,
    CounterpartyBreakdown,
    RegionalData,
    SourceDistribution,
    ProcessingFunnelData,
    ProcessingFunnelStage,
    AIPerformanceData,
    ConfidenceBracket,
    LowConfidenceItem,
    RegularPaymentSummary,
    ExhibitionData,
    DailyFlowData,
    ActivityHeatmapPoint,
    StatusTimelinePoint,
    ConfidenceScatterPoint,
)
from app.utils.auth import get_current_active_user
from app.utils.excel_export import encode_filename_header
from app.services.bank_transaction_import import BankTransactionImporter
from app.services.transaction_classifier import TransactionClassifier, RegularPaymentDetector
from app.services.odata_sync import ODataBankTransactionSync, ODataSyncConfig
from app.core import constants

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=BankTransactionList)
def get_bank_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[BankTransactionStatusEnum] = None,
    transaction_type: Optional[BankTransactionTypeEnum] = None,
    payment_source: Optional[str] = Query(None, description="Filter by payment source (BANK/CASH)"),
    account_number: Optional[str] = Query(None, description="Filter by our account number"),
    account_is_null: bool = Query(False, description="Filter transactions without account number"),
    category_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    only_unprocessed: bool = Query(False, description="Show only NEW and NEEDS_REVIEW"),
    has_expense: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of bank transactions with filters and pagination

    - USER: Can only see transactions from their department
    - FOUNDER/MANAGER/ADMIN: Can see all departments or filter by department
    """
    query = db.query(BankTransaction).options(
        joinedload(BankTransaction.category_rel),
        joinedload(BankTransaction.suggested_category_rel),
        joinedload(BankTransaction.expense_rel),
        joinedload(BankTransaction.organization_rel),
        joinedload(BankTransaction.department_rel),
    )

    # Department filtering based on user role (Multi-tenancy)
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BankTransaction.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id:
            query = query.filter(BankTransaction.department_id == department_id)

    # Status filter
    if only_unprocessed:
        query = query.filter(BankTransaction.status.in_([
            BankTransactionStatusEnum.NEW,
            BankTransactionStatusEnum.NEEDS_REVIEW
        ]))
    elif status:
        query = query.filter(BankTransaction.status == status)

    # Other filters
    if transaction_type:
        query = query.filter(BankTransaction.transaction_type == transaction_type)
    if payment_source:
        from app.db.models import PaymentSourceEnum
        try:
            payment_source_enum = PaymentSourceEnum(payment_source)
            query = query.filter(BankTransaction.payment_source == payment_source_enum)
        except ValueError:
            pass  # Invalid value, skip filter
    if account_number:
        query = query.filter(BankTransaction.account_number == account_number)
    elif account_is_null:
        query = query.filter(BankTransaction.account_number.is_(None))
    if category_id:
        query = query.filter(BankTransaction.category_id == category_id)
    if organization_id:
        query = query.filter(BankTransaction.organization_id == organization_id)
    if date_from:
        query = query.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(BankTransaction.transaction_date <= date_to)
    if has_expense is not None:
        if has_expense:
            query = query.filter(BankTransaction.expense_id.isnot(None))
        else:
            query = query.filter(BankTransaction.expense_id.is_(None))

    # Search
    if search:
        search_filter = or_(
            BankTransaction.counterparty_name.ilike(f"%{search}%"),
            BankTransaction.counterparty_inn.ilike(f"%{search}%"),
            BankTransaction.payment_purpose.ilike(f"%{search}%"),
            BankTransaction.document_number.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    # Only active
    query = query.filter(BankTransaction.is_active == True)

    # Count total
    total = query.count()

    # Apply pagination
    transactions = query.order_by(
        BankTransaction.transaction_date.desc(),
        BankTransaction.created_at.desc()
    ).offset(skip).limit(limit).all()

    # Convert to response model with relations
    items = []
    for tx in transactions:
        item = BankTransactionWithRelations(
            **{c.name: getattr(tx, c.name) for c in tx.__table__.columns},
            category_name=tx.category_rel.name if tx.category_rel else None,
            suggested_category_name=tx.suggested_category_rel.name if tx.suggested_category_rel else None,
            expense_number=tx.expense_rel.number if tx.expense_rel else None,
            suggested_expense_number=tx.suggested_expense_rel.number if tx.suggested_expense_rel else None,
            organization_name=tx.organization_rel.name if tx.organization_rel else None,
            reviewed_by_name=tx.reviewed_by_rel.full_name if tx.reviewed_by_rel else None,
            department_name=tx.department_rel.name if tx.department_rel else None,
        )
        items.append(item)

    pages = (total + limit - 1) // limit if limit > 0 else 1

    return BankTransactionList(
        total=total,
        items=items,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
        pages=pages
    )


@router.get("/stats", response_model=BankTransactionStats)
def get_bank_transactions_stats(
    department_id: Optional[int] = Query(None, description="Filter by department"),
    status: Optional[BankTransactionStatusEnum] = Query(None, description="Filter by status"),
    transaction_type: Optional[BankTransactionTypeEnum] = Query(None, description="Filter by transaction type (DEBIT/CREDIT)"),
    payment_source: Optional[str] = Query(None, description="Filter by payment source (BANK/CASH)"),
    account_number: Optional[str] = Query(None, description="Filter by our account number"),
    account_is_null: bool = Query(False, description="Filter transactions without account number"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    has_expense: Optional[bool] = Query(None, description="Filter by presence of linked expense"),
    only_unprocessed: bool = Query(False, description="Show NEW and NEEDS_REVIEW only"),
    date_from: Optional[date] = Query(None, description="Filter by date from"),
    date_to: Optional[date] = Query(None, description="Filter by date to"),
    search: Optional[str] = Query(None, description="Search in counterparty_name, counterparty_inn, payment_purpose"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for bank transactions with filters

    All filters from the main list endpoint are supported to ensure
    statistics reflect the filtered data exactly.
    """
    query = db.query(BankTransaction)

    # Department filtering (Multi-tenancy)
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BankTransaction.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(BankTransaction.department_id == department_id)

    # Date filters
    if date_from:
        query = query.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(BankTransaction.transaction_date <= date_to)

    # Status filter
    if only_unprocessed:
        query = query.filter(BankTransaction.status.in_([
            BankTransactionStatusEnum.NEW,
            BankTransactionStatusEnum.NEEDS_REVIEW
        ]))
    elif status:
        query = query.filter(BankTransaction.status == status)

    # Transaction type filter (DEBIT/CREDIT)
    if transaction_type:
        query = query.filter(BankTransaction.transaction_type == transaction_type)

    # Payment source filter (BANK/CASH)
    if payment_source:
        from app.db.models import PaymentSourceEnum
        try:
            payment_source_enum = PaymentSourceEnum(payment_source)
            query = query.filter(BankTransaction.payment_source == payment_source_enum)
        except ValueError:
            pass  # Invalid value, skip filter

    # Account number filters
    if account_number:
        query = query.filter(BankTransaction.account_number == account_number)
    elif account_is_null:
        query = query.filter(BankTransaction.account_number.is_(None))
    if category_id:
        query = query.filter(BankTransaction.category_id == category_id)
    if organization_id:
        query = query.filter(BankTransaction.organization_id == organization_id)
    if has_expense is not None:
        if has_expense:
            query = query.filter(BankTransaction.expense_id.isnot(None))
        else:
            query = query.filter(BankTransaction.expense_id.is_(None))

    # Search filter
    if search:
        search_filter = or_(
            BankTransaction.counterparty_name.ilike(f"%{search}%"),
            BankTransaction.counterparty_inn.ilike(f"%{search}%"),
            BankTransaction.payment_purpose.ilike(f"%{search}%"),
        )
        query = query.filter(search_filter)

    query = query.filter(BankTransaction.is_active == True)

    # Count by status
    total_transactions = query.count()

    # Calculate totals by transaction type
    total_debit_amount = query.filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.DEBIT
    ).with_entities(func.sum(BankTransaction.amount)).scalar() or Decimal('0')

    total_credit_amount = query.filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.CREDIT
    ).with_entities(func.sum(BankTransaction.amount)).scalar() or Decimal('0')

    new_count = query.filter(BankTransaction.status == BankTransactionStatusEnum.NEW).count()
    categorized_count = query.filter(BankTransaction.status == BankTransactionStatusEnum.CATEGORIZED).count()
    matched_count = query.filter(BankTransaction.status == BankTransactionStatusEnum.MATCHED).count()
    approved_count = query.filter(BankTransaction.status == BankTransactionStatusEnum.APPROVED).count()
    needs_review_count = query.filter(BankTransaction.status == BankTransactionStatusEnum.NEEDS_REVIEW).count()

    # Average confidence/scores
    avg_confidence = query.filter(
        BankTransaction.category_confidence.isnot(None)
    ).with_entities(func.avg(BankTransaction.category_confidence)).scalar()

    avg_matching = query.filter(
        BankTransaction.matching_score.isnot(None)
    ).with_entities(func.avg(BankTransaction.matching_score)).scalar()

    return BankTransactionStats(
        total_transactions=total_transactions,
        total_amount=total_debit_amount,  # Deprecated: for backward compatibility
        total_credit_amount=total_credit_amount,
        total_debit_amount=total_debit_amount,
        new_count=new_count,
        categorized_count=categorized_count,
        matched_count=matched_count,
        approved_count=approved_count,
        needs_review_count=needs_review_count,
        avg_category_confidence=float(avg_confidence) if avg_confidence else None,
        avg_matching_score=float(avg_matching) if avg_matching else None,
    )


# =====================================================================
# Analytics Endpoints (MUST be before /{transaction_id} to avoid conflicts)
# =====================================================================

@router.get("/analytics", response_model=BankTransactionAnalytics)
def get_bank_transactions_analytics(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter (1-4)"),
    transaction_type: Optional[BankTransactionTypeEnum] = None,
    payment_source: Optional[str] = Query(None, description="BANK or CASH"),
    status: Optional[BankTransactionStatusEnum] = None,
    region: Optional[str] = Query(None, description="MOSCOW/SPB/REGIONS/FOREIGN"),
    category_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department"),
    compare_previous_period: bool = Query(True, description="Include comparison with previous period"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive analytics for bank transactions

    NOTE: This endpoint MUST be defined BEFORE /{transaction_id} route
    to avoid FastAPI treating 'analytics' as a transaction_id parameter.
    """
    from calendar import month_name as month_names_en
    from datetime import timedelta

    # Import the actual implementation from end of file
    # This is a forward reference to avoid duplicate code
    return _get_bank_transactions_analytics_impl(
        date_from=date_from,
        date_to=date_to,
        year=year,
        month=month,
        quarter=quarter,
        transaction_type=transaction_type,
        payment_source=payment_source,
        status=status,
        region=region,
        category_id=category_id,
        department_id=department_id,
        compare_previous_period=compare_previous_period,
        current_user=current_user,
        db=db
    )


@router.get("/{transaction_id}", response_model=BankTransactionWithRelations)
def get_bank_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get bank transaction by ID"""
    tx = db.query(BankTransaction).options(
        joinedload(BankTransaction.category_rel),
        joinedload(BankTransaction.suggested_category_rel),
        joinedload(BankTransaction.expense_rel),
        joinedload(BankTransaction.organization_rel),
        joinedload(BankTransaction.department_rel),
        joinedload(BankTransaction.reviewed_by_rel),
    ).filter(BankTransaction.id == transaction_id).first()

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.USER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return BankTransactionWithRelations(
        **{c.name: getattr(tx, c.name) for c in tx.__table__.columns},
        category_name=tx.category_rel.name if tx.category_rel else None,
        suggested_category_name=tx.suggested_category_rel.name if tx.suggested_category_rel else None,
        expense_number=tx.expense_rel.number if tx.expense_rel else None,
        suggested_expense_number=tx.suggested_expense_rel.number if tx.suggested_expense_rel else None,
        organization_name=tx.organization_rel.name if tx.organization_rel else None,
        reviewed_by_name=tx.reviewed_by_rel.full_name if tx.reviewed_by_rel else None,
        department_name=tx.department_rel.name if tx.department_rel else None,
    )


@router.put("/{transaction_id}", response_model=BankTransactionWithRelations)
def update_transaction(
    transaction_id: int,
    data: BankTransactionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update transaction (category, status, notes)
    """
    tx = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.USER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Update fields if provided
    if data.category_id is not None:
        category = db.query(BudgetCategory).filter(BudgetCategory.id == data.category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        tx.category_id = data.category_id

    if data.status is not None:
        tx.status = BankTransactionStatusEnum(data.status)

    if data.notes is not None:
        tx.notes = data.notes

    tx.reviewed_by = current_user.id
    tx.reviewed_at = datetime.utcnow()
    tx.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(tx)

    return get_bank_transaction(transaction_id, current_user, db)


@router.put("/{transaction_id}/categorize", response_model=BankTransactionWithRelations)
def categorize_transaction(
    transaction_id: int,
    data: BankTransactionCategorize,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Set category for transaction
    """
    tx = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.USER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Verify category exists and belongs to same department
    category = db.query(BudgetCategory).filter(BudgetCategory.id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Update transaction
    tx.category_id = data.category_id
    tx.notes = data.notes if data.notes else tx.notes
    tx.status = BankTransactionStatusEnum.CATEGORIZED
    tx.reviewed_by = current_user.id
    tx.reviewed_at = datetime.utcnow()
    tx.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(tx)

    return get_bank_transaction(transaction_id, current_user, db)


@router.put("/{transaction_id}/link", response_model=BankTransactionWithRelations)
def link_transaction_to_expense(
    transaction_id: int,
    data: BankTransactionLink,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Link transaction to expense (заявка)
    """
    tx = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.USER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Verify expense exists
    expense = db.query(Expense).filter(Expense.id == data.expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # Update transaction
    tx.expense_id = data.expense_id
    tx.notes = data.notes if data.notes else tx.notes
    tx.status = BankTransactionStatusEnum.MATCHED
    tx.reviewed_by = current_user.id
    tx.reviewed_at = datetime.utcnow()
    tx.updated_at = datetime.utcnow()

    # Optionally set category from expense
    if expense.category_id and not tx.category_id:
        tx.category_id = expense.category_id

    db.commit()
    db.refresh(tx)

    return get_bank_transaction(transaction_id, current_user, db)


@router.post("/bulk-categorize")
def bulk_categorize_transactions(
    data: BulkCategorizeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk categorize transactions
    """
    # Verify category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == data.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Get transactions
    query = db.query(BankTransaction).filter(BankTransaction.id.in_(data.transaction_ids))

    # Department filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(BankTransaction.department_id == current_user.department_id)

    transactions = query.all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Update all
    updated_count = 0
    for tx in transactions:
        tx.category_id = data.category_id
        if data.notes:
            tx.notes = data.notes
        tx.status = BankTransactionStatusEnum.CATEGORIZED
        tx.reviewed_by = current_user.id
        tx.reviewed_at = datetime.utcnow()
        tx.updated_at = datetime.utcnow()
        updated_count += 1

    db.commit()

    return {"message": f"Successfully categorized {updated_count} transactions", "updated": updated_count}


@router.post("/bulk-status-update")
def bulk_update_status(
    data: BulkStatusUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk update transaction status
    """
    # Get transactions
    query = db.query(BankTransaction).filter(BankTransaction.id.in_(data.transaction_ids))

    # Department filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(BankTransaction.department_id == current_user.department_id)

    transactions = query.all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Update all
    updated_count = 0
    for tx in transactions:
        tx.status = BankTransactionStatusEnum(data.status)
        tx.reviewed_by = current_user.id
        tx.reviewed_at = datetime.utcnow()
        tx.updated_at = datetime.utcnow()
        updated_count += 1

    db.commit()

    return {"message": f"Successfully updated status for {updated_count} transactions", "updated": updated_count}


@router.get("/{transaction_id}/matching-expenses", response_model=List[MatchingSuggestion])
def get_matching_expenses(
    transaction_id: int,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Find matching expenses for transaction
    Simple matching based on amount, date, and counterparty
    """
    tx = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.USER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Search for expenses
    # 1. Same amount (±5%)
    amount_min = tx.amount * Decimal(str(constants.AMOUNT_MATCHING_TOLERANCE_MIN))
    amount_max = tx.amount * Decimal(str(constants.AMOUNT_MATCHING_TOLERANCE_MAX))

    # 2. Date range (±30 days from transaction)
    from datetime import timedelta
    date_min = tx.transaction_date - timedelta(days=constants.DATE_MATCHING_TOLERANCE_DAYS)
    date_max = tx.transaction_date + timedelta(days=constants.DATE_MATCHING_TOLERANCE_DAYS)

    query = db.query(Expense).filter(
        and_(
            Expense.department_id == tx.department_id,
            Expense.amount >= amount_min,
            Expense.amount <= amount_max,
            Expense.request_date >= date_min,
            Expense.request_date <= date_max,
            Expense.is_active == True
        )
    ).options(joinedload(Expense.contractor))

    expenses = query.all()

    # Calculate matching scores
    suggestions = []
    for exp in expenses:
        score = 0.0
        reasons = []

        # Amount match
        amount_diff_percent = abs(float(exp.amount - tx.amount) / float(tx.amount)) * 100
        if amount_diff_percent < 1:
            score += 40
            reasons.append("Точное совпадение суммы")
        elif amount_diff_percent < 5:
            score += 30
            reasons.append(f"Сумма близка ({amount_diff_percent:.1f}% разница)")

        # Date match
        date_diff_days = abs((exp.request_date - tx.transaction_date).days)
        if date_diff_days <= 7:
            score += 20
            reasons.append(f"Дата близка ({date_diff_days} дней)")
        elif date_diff_days <= 30:
            score += 10
            reasons.append(f"Дата в пределах месяца ({date_diff_days} дней)")

        # Contractor match (if we have INN)
        if tx.counterparty_inn and exp.contractor and exp.contractor.inn == tx.counterparty_inn:
            score += 30
            reasons.append("Совпадает ИНН контрагента")
        elif tx.counterparty_name and exp.contractor:
            # Fuzzy name match
            if tx.counterparty_name.lower() in exp.contractor.name.lower() or \
               exp.contractor.name.lower() in tx.counterparty_name.lower():
                score += 15
                reasons.append("Похожее имя контрагента")

        # Category match
        if tx.category_id and exp.category_id == tx.category_id:
            score += 10
            reasons.append("Совпадает категория")

        if score > 0:
            suggestions.append(MatchingSuggestion(
                expense_id=exp.id,
                expense_number=exp.number,
                expense_amount=exp.amount,
                expense_date=exp.request_date,
                expense_category_id=exp.category_id,
                expense_contractor_name=exp.contractor.name if exp.contractor else None,
                matching_score=score,
                match_reasons=reasons
            ))

    # Sort by score
    suggestions.sort(key=lambda x: x.matching_score, reverse=True)

    return suggestions[:limit]


@router.get("/{transaction_id}/category-suggestions", response_model=List[CategorySuggestion])
def get_category_suggestions(
    transaction_id: int,
    top_n: int = Query(3, ge=1, le=10),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get AI-powered category suggestions for transaction
    Uses keyword matching and historical data
    """
    tx = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.USER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Get suggestions from AI classifier
    classifier = TransactionClassifier(db)
    suggestions = classifier.get_category_suggestions(
        payment_purpose=tx.payment_purpose,
        counterparty_name=tx.counterparty_name,
        counterparty_inn=tx.counterparty_inn,
        amount=tx.amount,
        department_id=tx.department_id,
        transaction_type=tx.transaction_type,  # Pass transaction type for better suggestions
        top_n=top_n
    )

    return [
        CategorySuggestion(
            category_id=s['category_id'],
            category_name=s['category_name'],
            confidence=s['confidence'],
            reasoning=s['reasoning']
        )
        for s in suggestions
    ]


@router.get("/regular-patterns", response_model=List[dict])
def get_regular_payment_patterns(
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/FOUNDER/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Detect regular payment patterns (subscriptions, rent, etc.)
    Returns patterns with frequency and last payment date
    """
    # Determine department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    elif department_id:
        target_department_id = department_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="department_id is required for non-USER roles"
        )

    detector = RegularPaymentDetector(db)
    patterns = detector.detect_patterns(target_department_id)

    return patterns


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Permanently delete transaction from database
    Only ADMIN and MANAGER can delete
    """
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(status_code=403, detail="Only ADMIN and MANAGER can delete transactions")

    tx = db.query(BankTransaction).filter(BankTransaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Check department access
    if current_user.role == UserRoleEnum.MANAGER:
        if tx.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Physical delete from database
    db.delete(tx)
    db.commit()

    return {"message": "Transaction deleted successfully"}


@router.post("/bulk-delete")
def bulk_delete_transactions(
    transaction_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Permanently bulk delete transactions from database
    Only ADMIN and MANAGER can delete
    """
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(status_code=403, detail="Only ADMIN and MANAGER can delete transactions")

    # Get transactions
    query = db.query(BankTransaction).filter(BankTransaction.id.in_(transaction_ids))

    # Department filtering for MANAGER
    if current_user.role == UserRoleEnum.MANAGER:
        query = query.filter(BankTransaction.department_id == current_user.department_id)

    transactions = query.all()

    if not transactions:
        raise HTTPException(status_code=404, detail="No transactions found")

    # Physical delete all from database
    deleted_count = 0
    for tx in transactions:
        db.delete(tx)
        deleted_count += 1

    db.commit()

    return {"message": f"Successfully deleted {deleted_count} transactions", "deleted": deleted_count}


@router.post("/import/preview")
async def preview_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Preview Excel file for import
    Returns available columns, auto-detected mapping, and sample data
    """
    # Read file content
    content = await file.read()

    # Preview
    importer = BankTransactionImporter(db)
    result = importer.preview_import(
        file_content=content,
        filename=file.filename
    )

    if not result.get('success'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Failed to preview file')
        )

    return result


@router.post("/import", response_model=BankTransactionImportResult)
async def import_transactions(
    file: UploadFile = File(...),
    department_id: Optional[int] = Query(None, description="Department ID (required for MANAGER/ADMIN roles, auto-detected for USER)"),
    column_mapping: Optional[str] = Query(None, description="JSON string with column mapping"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import bank transactions from Excel file

    Expected columns (auto-detected):
    - Дата операции / Date
    - Сумма / Amount
    - Контрагент / Counterparty
    - ИНН / INN
    - Назначение платежа / Payment Purpose
    - Номер документа / Document Number
    """
    # Determine department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        target_department_id = current_user.department_id
    elif department_id:
        target_department_id = department_id
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="department_id is required for non-USER roles"
        )

    # Verify department exists
    department = db.query(Department).filter(Department.id == target_department_id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    # Read file content
    content = await file.read()

    # Parse column mapping if provided
    parsed_mapping = None
    if column_mapping:
        import json
        try:
            parsed_mapping = json.loads(column_mapping)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid column_mapping JSON format"
            )

    # Import
    importer = BankTransactionImporter(db)
    result = importer.import_from_excel(
        file_content=content,
        filename=file.filename,
        department_id=target_department_id,
        user_id=current_user.id,
        column_mapping=parsed_mapping
    )

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get('error', 'Import failed')
        )

    return BankTransactionImportResult(
        total_rows=result['total_rows'],
        imported=result['imported'],
        skipped=result['skipped'],
        errors=result['errors'],
        warnings=[]
    )


@router.post("/odata/test-connection", response_model=ODataTestConnectionResult)
async def test_odata_connection(
    request: ODataTestConnectionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Test OData connection to 1C

    Tests connection to 1C OData service before syncing.
    Only ADMIN and MANAGER can test connections.
    """
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER can test OData connections"
        )

    try:
        # Create config
        config = ODataSyncConfig(
            base_url=request.odata_url,
            username=request.username,
            password=request.password,
            timeout=request.timeout
        )

        # Create sync service
        sync_service = ODataBankTransactionSync(db, config)

        # Test connection
        result = sync_service.test_connection()

        return ODataTestConnectionResult(**result)

    except Exception as e:
        logger.error(f"Failed to test OData connection: {e}", exc_info=True)
        return ODataTestConnectionResult(
            success=False,
            message=f"Connection test failed: {e}",
            error=str(e)
        )


@router.post("/odata/sync", response_model=dict)
async def sync_from_odata(
    request: ODataSyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Sync bank transactions from 1C via OData (Background Task)

    Запускает синхронизацию в фоновом режиме и возвращает task_id.
    Используйте GET /odata/sync/status/{task_id} для проверки статуса.

    Syncs bank transactions (debits and credits) from 1C OData service using:
    - Document_ПоступлениеБезналичныхДенежныхСредств (поступления)
    - Document_СписаниеБезналичныхДенежныхСредств (списания)

    Only ADMIN and MANAGER can perform sync.

    Features:
    - Runs in background (non-blocking)
    - Fetches transactions from correct 1C documents
    - Parses data from "ДанныеВыписки" field with bank statement details
    - Creates new transactions or updates existing (by external_id_1c)
    - Supports AI auto-classification
    - Handles batch processing for large datasets

    Example request:
    {
        "odata_url": "http://10.10.100.77/trade/odata/standard.odata",
        "username": "odata.user",
        "password": "ak228Hu2hbs28",
        "department_id": 1,
        "date_from": "2025-01-01",
        "date_to": "2025-01-07",
        "auto_classify": true,
        "batch_size": 100
    }

    Returns:
    {
        "task_id": "uuid-string",
        "message": "Синхронизация запущена в фоновом режиме",
        "status": "STARTED"
    }
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN and MANAGER can sync from OData"
        )

    # Verify department exists
    department = db.query(Department).filter(Department.id == request.department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {request.department_id} not found"
        )

    # For MANAGER role, verify they belong to the department
    if current_user.role == UserRoleEnum.MANAGER:
        if current_user.department_id != request.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="MANAGER can only sync to their own department"
            )

    # Generate unique task ID
    import uuid
    task_id = str(uuid.uuid4())

    # Store task status in cache/database (simplified version - using global dict)
    # In production, use Redis or database table
    if not hasattr(sync_from_odata, 'tasks'):
        sync_from_odata.tasks = {}

    sync_from_odata.tasks[task_id] = {
        'status': 'STARTED',
        'department_id': request.department_id,
        'user_id': current_user.id,
        'started_at': datetime.now().isoformat(),
        'result': None,
        'error': None
    }

    # Define background task function
    def run_sync_task():
        task_db = SessionLocal()
        try:
            # Create config
            config = ODataSyncConfig(
                base_url=request.odata_url,
                username=request.username,
                password=request.password
            )

            # Create sync service
            sync_service = ODataBankTransactionSync(task_db, config)

            # Perform sync
            result = sync_service.sync_transactions(
                department_id=request.department_id,
                date_from=request.date_from,
                date_to=request.date_to,
                auto_classify=request.auto_classify,
                batch_size=request.batch_size
            )

            # Update task status
            sync_from_odata.tasks[task_id]['status'] = 'COMPLETED'
            sync_from_odata.tasks[task_id]['result'] = result
            sync_from_odata.tasks[task_id]['completed_at'] = datetime.now().isoformat()

            # Log the operation
            logger.info(
                f"OData sync completed (task {task_id}) by user {current_user.id}: "
                f"fetched={result.get('total_fetched', 0)}, "
                f"created={result.get('created', 0)}, "
                f"updated={result.get('updated', 0)}, "
                f"auto_categorized={result.get('auto_categorized', 0)}"
            )

        except Exception as e:
            logger.error(f"OData sync failed (task {task_id}): {e}", exc_info=True)
            sync_from_odata.tasks[task_id]['status'] = 'FAILED'
            sync_from_odata.tasks[task_id]['error'] = str(e)
            sync_from_odata.tasks[task_id]['completed_at'] = datetime.now().isoformat()
        finally:
            task_db.close()

    # Add task to background
    background_tasks.add_task(run_sync_task)

    return {
        'task_id': task_id,
        'message': f'Синхронизация запущена в фоновом режиме для отдела "{department.name}"',
        'status': 'STARTED',
        'department': {
            'id': department.id,
            'name': department.name
        }
    }


@router.get("/odata/sync/status/{task_id}", response_model=dict)
async def get_sync_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Get status of background OData sync task

    Проверяет статус фоновой задачи синхронизации.

    Returns:
    {
        "task_id": "uuid-string",
        "status": "STARTED | COMPLETED | FAILED",
        "started_at": "ISO datetime",
        "completed_at": "ISO datetime (если завершено)",
        "result": {...} (если успешно завершено),
        "error": "error message" (если ошибка)
    }
    """
    # Get tasks from sync_from_odata function attribute
    if not hasattr(sync_from_odata, 'tasks') or task_id not in sync_from_odata.tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )

    task_info = sync_from_odata.tasks[task_id]

    # Check if user has permission to view this task
    # ADMIN can view all, MANAGER can view only their department's tasks
    if current_user.role == UserRoleEnum.MANAGER:
        if task_info['department_id'] != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to view this task"
            )

    return {
        'task_id': task_id,
        **task_info
    }


# =====================================================================
# Analytics Implementation (called by analytics endpoint above)
# =====================================================================

def _get_bank_transactions_analytics_impl(
    date_from: Optional[date],
    date_to: Optional[date],
    year: Optional[int],
    month: Optional[int],
    quarter: Optional[int],
    transaction_type: Optional[BankTransactionTypeEnum],
    payment_source: Optional[str],
    status: Optional[BankTransactionStatusEnum],
    region: Optional[str],
    category_id: Optional[int],
    department_id: Optional[int],
    compare_previous_period: bool,
    current_user: User,
    db: Session
) -> BankTransactionAnalytics:
    """
    Implementation of comprehensive analytics for bank transactions

    This function is called by the /analytics endpoint defined above.
    It's kept separate to ensure proper route ordering.

    Returns:
    - KPI metrics (totals, counts, averages, comparisons)
    - Monthly cash flow data
    - Category breakdowns (top categories, OPEX vs CAPEX)
    - Counterparty analysis
    - Regional distribution
    - Payment source distribution
    - Processing funnel and efficiency metrics
    - AI performance metrics
    - Low confidence items needing review
    - Regular payment patterns
    - Exhibition/event related transactions

    Access:
    - USER: Only their department data
    - MANAGER/ADMIN: Can filter by department or see all
    """
    from calendar import month_name as month_names_en
    from datetime import timedelta

    # Russian month names
    MONTH_NAMES_RU = [
        '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]

    # Base query with department filtering (multi-tenancy)
    query = db.query(BankTransaction).filter(BankTransaction.is_active == True)

    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BankTransaction.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(BankTransaction.department_id == department_id)

    # Apply date filters
    if year and month:
        query = query.filter(
            extract('year', BankTransaction.transaction_date) == year,
            extract('month', BankTransaction.transaction_date) == month
        )
    elif year and quarter:
        start_month = (quarter - 1) * 3 + 1
        end_month = start_month + 2
        query = query.filter(
            extract('year', BankTransaction.transaction_date) == year,
            extract('month', BankTransaction.transaction_date).between(start_month, end_month)
        )
    elif year:
        query = query.filter(extract('year', BankTransaction.transaction_date) == year)

    if date_from:
        query = query.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        query = query.filter(BankTransaction.transaction_date <= date_to)

    # Apply other filters
    if transaction_type:
        query = query.filter(BankTransaction.transaction_type == transaction_type)
    if payment_source:
        query = query.filter(BankTransaction.payment_source == payment_source)
    if status:
        query = query.filter(BankTransaction.status == status)
    if region:
        try:
            region_enum = RegionEnum(region)
            query = query.filter(BankTransaction.region == region_enum)
        except ValueError:
            pass
    if category_id:
        query = query.filter(BankTransaction.category_id == category_id)

    # Get all matching transactions
    transactions = query.all()
    total_count = len(transactions)

    # ==============================
    # 1. KPIs Calculation
    # ==============================

    debit_transactions = [t for t in transactions if t.transaction_type == BankTransactionTypeEnum.DEBIT]
    credit_transactions = [t for t in transactions if t.transaction_type == BankTransactionTypeEnum.CREDIT]

    total_debit = sum(t.amount for t in debit_transactions)
    total_credit = sum(t.amount for t in credit_transactions)
    net_flow = total_credit - total_debit

    # Status counts
    status_counts = {}
    for status_enum in BankTransactionStatusEnum:
        status_counts[status_enum.value] = len([t for t in transactions if t.status == status_enum])

    # AI metrics
    categorized_transactions = [t for t in transactions if t.category_id is not None]
    auto_categorized = [t for t in categorized_transactions if t.category_confidence and t.category_confidence >= constants.CONFIDENCE_HIGH_THRESHOLD]
    regular_payments = [t for t in transactions if t.is_regular_payment]

    avg_confidence = None
    if categorized_transactions:
        confidences = [t.category_confidence for t in categorized_transactions if t.category_confidence]
        if confidences:
            avg_confidence = float(sum(confidences) / len(confidences))

    # Previous period comparison (if requested)
    debit_change_percent = None
    credit_change_percent = None
    net_flow_change_percent = None
    transactions_change = None

    if compare_previous_period and (date_from and date_to):
        period_days = (date_to - date_from).days + 1
        prev_date_from = date_from - timedelta(days=period_days)
        prev_date_to = date_from - timedelta(days=1)

        prev_query = db.query(BankTransaction).filter(
            BankTransaction.is_active == True,
            BankTransaction.transaction_date >= prev_date_from,
            BankTransaction.transaction_date <= prev_date_to
        )

        if current_user.role == UserRoleEnum.USER:
            prev_query = prev_query.filter(BankTransaction.department_id == current_user.department_id)
        elif department_id:
            prev_query = prev_query.filter(BankTransaction.department_id == department_id)

        prev_transactions = prev_query.all()
        prev_debit = sum(t.amount for t in prev_transactions if t.transaction_type == BankTransactionTypeEnum.DEBIT)
        prev_credit = sum(t.amount for t in prev_transactions if t.transaction_type == BankTransactionTypeEnum.CREDIT)
        prev_net_flow = prev_credit - prev_debit

        if prev_debit > 0:
            debit_change_percent = float((total_debit - prev_debit) / prev_debit * 100)
        if prev_credit > 0:
            credit_change_percent = float((total_credit - prev_credit) / prev_credit * 100)
        if prev_net_flow != 0:
            net_flow_change_percent = float((net_flow - prev_net_flow) / abs(prev_net_flow) * 100)
        transactions_change = total_count - len(prev_transactions)

    kpis = BankTransactionKPIs(
        total_debit_amount=total_debit,
        total_credit_amount=total_credit,
        net_flow=net_flow,
        total_transactions=total_count,
        debit_change_percent=debit_change_percent,
        credit_change_percent=credit_change_percent,
        net_flow_change_percent=net_flow_change_percent,
        transactions_change=transactions_change,
        new_count=status_counts.get(BankTransactionStatusEnum.NEW.value, 0),
        categorized_count=status_counts.get(BankTransactionStatusEnum.CATEGORIZED.value, 0),
        matched_count=status_counts.get(BankTransactionStatusEnum.MATCHED.value, 0),
        approved_count=status_counts.get(BankTransactionStatusEnum.APPROVED.value, 0),
        needs_review_count=status_counts.get(BankTransactionStatusEnum.NEEDS_REVIEW.value, 0),
        ignored_count=status_counts.get(BankTransactionStatusEnum.IGNORED.value, 0),
        new_percent=float(status_counts.get(BankTransactionStatusEnum.NEW.value, 0) / total_count * 100) if total_count > 0 else 0,
        categorized_percent=float(status_counts.get(BankTransactionStatusEnum.CATEGORIZED.value, 0) / total_count * 100) if total_count > 0 else 0,
        matched_percent=float(status_counts.get(BankTransactionStatusEnum.MATCHED.value, 0) / total_count * 100) if total_count > 0 else 0,
        approved_percent=float(status_counts.get(BankTransactionStatusEnum.APPROVED.value, 0) / total_count * 100) if total_count > 0 else 0,
        needs_review_percent=float(status_counts.get(BankTransactionStatusEnum.NEEDS_REVIEW.value, 0) / total_count * 100) if total_count > 0 else 0,
        ignored_percent=float(status_counts.get(BankTransactionStatusEnum.IGNORED.value, 0) / total_count * 100) if total_count > 0 else 0,
        avg_category_confidence=avg_confidence,
        auto_categorized_count=len(auto_categorized),
        auto_categorized_percent=float(len(auto_categorized) / total_count * 100) if total_count > 0 else 0,
        regular_payments_count=len(regular_payments),
        regular_payments_percent=float(len(regular_payments) / total_count * 100) if total_count > 0 else 0,
    )

    # ==============================
    # 2. Monthly Flow Data
    # ==============================

    monthly_data = db.query(
        extract('year', BankTransaction.transaction_date).label('year'),
        extract('month', BankTransaction.transaction_date).label('month'),
        BankTransaction.transaction_type,
        func.sum(BankTransaction.amount).label('total_amount'),
        func.count(BankTransaction.id).label('count'),
        func.avg(BankTransaction.category_confidence).label('avg_confidence')
    ).filter(BankTransaction.is_active == True)

    # Apply same filters as main query
    if current_user.role == UserRoleEnum.USER:
        monthly_data = monthly_data.filter(BankTransaction.department_id == current_user.department_id)
    elif department_id:
        monthly_data = monthly_data.filter(BankTransaction.department_id == department_id)

    if date_from:
        monthly_data = monthly_data.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        monthly_data = monthly_data.filter(BankTransaction.transaction_date <= date_to)
    if year:
        monthly_data = monthly_data.filter(extract('year', BankTransaction.transaction_date) == year)

    monthly_data = monthly_data.group_by('year', 'month', BankTransaction.transaction_type).all()

    # Organize by month
    monthly_dict = {}
    for row in monthly_data:
        key = (int(row.year), int(row.month))
        if key not in monthly_dict:
            monthly_dict[key] = {
                'debit': Decimal(0),
                'credit': Decimal(0),
                'count': 0,
                'confidences': []
            }

        if row.transaction_type == BankTransactionTypeEnum.DEBIT:
            monthly_dict[key]['debit'] = row.total_amount or Decimal(0)
        else:
            monthly_dict[key]['credit'] = row.total_amount or Decimal(0)

        monthly_dict[key]['count'] += row.count
        if row.avg_confidence:
            monthly_dict[key]['confidences'].append(float(row.avg_confidence))

    monthly_flow = []
    for (year_val, month_val), data in sorted(monthly_dict.items()):
        avg_conf = None
        if data['confidences']:
            avg_conf = sum(data['confidences']) / len(data['confidences'])

        monthly_flow.append(MonthlyFlowData(
            year=year_val,
            month=month_val,
            month_name=f"{MONTH_NAMES_RU[month_val]} {year_val}",
            debit_amount=data['debit'],
            credit_amount=data['credit'],
            net_flow=data['credit'] - data['debit'],
            transaction_count=data['count'],
            avg_confidence=avg_conf
        ))

    # ==============================
    # 2b. Daily flow & activity signals
    # ==============================

    daily_flow_buckets = defaultdict(lambda: {'debit': Decimal(0), 'credit': Decimal(0), 'count': 0})
    activity_buckets = defaultdict(lambda: {'count': 0, 'amount': Decimal(0)})
    status_timeline_buckets = defaultdict(lambda: {
        BankTransactionStatusEnum.NEW.value: 0,
        BankTransactionStatusEnum.CATEGORIZED.value: 0,
        BankTransactionStatusEnum.MATCHED.value: 0,
        BankTransactionStatusEnum.APPROVED.value: 0,
        BankTransactionStatusEnum.NEEDS_REVIEW.value: 0,
        BankTransactionStatusEnum.IGNORED.value: 0,
    })

    for tx in transactions:
        bucket = daily_flow_buckets[tx.transaction_date]
        if tx.transaction_type == BankTransactionTypeEnum.DEBIT:
            bucket['debit'] += tx.amount
        else:
            bucket['credit'] += tx.amount
        bucket['count'] += 1

        status_bucket = status_timeline_buckets[tx.transaction_date]
        status_bucket[tx.status.value] = status_bucket.get(tx.status.value, 0) + 1

        activity_dt = tx.created_at or datetime.combine(tx.transaction_date, datetime.min.time())
        hour = activity_dt.hour
        weekday = activity_dt.weekday()
        activity_bucket = activity_buckets[(weekday, hour)]
        activity_bucket['count'] += 1
        activity_bucket['amount'] += abs(tx.amount)

    daily_flow = []
    for day_key, values in sorted(daily_flow_buckets.items()):
        daily_flow.append(DailyFlowData(
            date=day_key,
            debit_amount=values['debit'],
            credit_amount=values['credit'],
            net_flow=values['credit'] - values['debit'],
            transaction_count=values['count'],
        ))

    activity_heatmap = []
    for (weekday, hour), values in activity_buckets.items():
        avg_amount = values['amount'] / values['count'] if values['count'] > 0 else Decimal(0)
        activity_heatmap.append(ActivityHeatmapPoint(
            day_of_week=weekday,
            hour=hour,
            transaction_count=values['count'],
            total_amount=values['amount'],
            avg_amount=avg_amount,
        ))

    status_timeline = []
    for date_key, values in sorted(status_timeline_buckets.items()):
        status_timeline.append(StatusTimelinePoint(
            date=date_key,
            new_count=values.get(BankTransactionStatusEnum.NEW.value, 0),
            categorized_count=values.get(BankTransactionStatusEnum.CATEGORIZED.value, 0),
            matched_count=values.get(BankTransactionStatusEnum.MATCHED.value, 0),
            approved_count=values.get(BankTransactionStatusEnum.APPROVED.value, 0),
            needs_review_count=values.get(BankTransactionStatusEnum.NEEDS_REVIEW.value, 0),
            ignored_count=values.get(BankTransactionStatusEnum.IGNORED.value, 0),
        ))

    # ==============================
    # 3. Category Breakdown
    # ==============================

    category_data = db.query(
        BudgetCategory.id,
        BudgetCategory.name,
        BudgetCategory.type,
        func.count(BankTransaction.id).label('count'),
        func.sum(BankTransaction.amount).label('total_amount'),
        func.avg(BankTransaction.amount).label('avg_amount'),
        func.avg(BankTransaction.category_confidence).label('avg_confidence')
    ).join(
        BankTransaction, BankTransaction.category_id == BudgetCategory.id
    ).filter(
        BankTransaction.is_active == True,
        BankTransaction.category_id.isnot(None)
    )

    # Apply same filters
    if current_user.role == UserRoleEnum.USER:
        category_data = category_data.filter(BankTransaction.department_id == current_user.department_id)
    elif department_id:
        category_data = category_data.filter(BankTransaction.department_id == department_id)

    if date_from:
        category_data = category_data.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        category_data = category_data.filter(BankTransaction.transaction_date <= date_to)

    category_data = category_data.group_by(BudgetCategory.id, BudgetCategory.name, BudgetCategory.type).all()

    total_categorized_amount = sum(row.total_amount for row in category_data if row.total_amount)

    top_categories = []
    for row in sorted(category_data, key=lambda x: x.total_amount or Decimal(0), reverse=True)[:10]:
        top_categories.append(CategoryBreakdown(
            category_id=row.id,
            category_name=row.name,
            category_type=row.type,
            transaction_count=row.count,
            total_amount=row.total_amount or Decimal(0),
            avg_amount=row.avg_amount or Decimal(0),
            avg_confidence=float(row.avg_confidence) if row.avg_confidence else None,
            percent_of_total=float((row.total_amount or Decimal(0)) / total_categorized_amount * 100) if total_categorized_amount > 0 else 0
        ))

    # Category type distribution (OPEX vs CAPEX)
    type_dict = {}
    for row in category_data:
        cat_type = row.type or 'OTHER'
        if cat_type not in type_dict:
            type_dict[cat_type] = {
                'count': 0,
                'total': Decimal(0),
                'confidences': []
            }
        type_dict[cat_type]['count'] += row.count
        type_dict[cat_type]['total'] += row.total_amount or Decimal(0)
        if row.avg_confidence:
            type_dict[cat_type]['confidences'].append(float(row.avg_confidence))

    category_type_distribution = []
    for cat_type, data in type_dict.items():
        avg_conf = None
        if data['confidences']:
            avg_conf = sum(data['confidences']) / len(data['confidences'])

        category_type_distribution.append(CategoryBreakdown(
            category_id=0,  # Placeholder
            category_name=cat_type,
            category_type=cat_type,
            transaction_count=data['count'],
            total_amount=data['total'],
            avg_amount=data['total'] / data['count'] if data['count'] > 0 else Decimal(0),
            avg_confidence=avg_conf,
            percent_of_total=float(data['total'] / total_categorized_amount * 100) if total_categorized_amount > 0 else 0
        ))

    # ==============================
    # 4. Counterparty Breakdown
    # ==============================

    counterparty_data = db.query(
        BankTransaction.counterparty_inn,
        BankTransaction.counterparty_name,
        func.count(BankTransaction.id).label('count'),
        func.sum(BankTransaction.amount).label('total_amount'),
        func.avg(BankTransaction.amount).label('avg_amount'),
        func.min(BankTransaction.transaction_date).label('first_date'),
        func.max(BankTransaction.transaction_date).label('last_date'),
        func.bool_or(BankTransaction.is_regular_payment).label('is_regular')
    ).filter(
        BankTransaction.is_active == True,
        BankTransaction.counterparty_name.isnot(None)
    )

    # Apply same filters
    if current_user.role == UserRoleEnum.USER:
        counterparty_data = counterparty_data.filter(BankTransaction.department_id == current_user.department_id)
    elif department_id:
        counterparty_data = counterparty_data.filter(BankTransaction.department_id == department_id)

    if date_from:
        counterparty_data = counterparty_data.filter(BankTransaction.transaction_date >= date_from)
    if date_to:
        counterparty_data = counterparty_data.filter(BankTransaction.transaction_date <= date_to)

    counterparty_data = counterparty_data.group_by(
        BankTransaction.counterparty_inn,
        BankTransaction.counterparty_name
    ).all()

    top_counterparties = []
    for row in sorted(counterparty_data, key=lambda x: x.total_amount or Decimal(0), reverse=True)[:20]:
        top_counterparties.append(CounterpartyBreakdown(
            counterparty_inn=row.counterparty_inn,
            counterparty_name=row.counterparty_name or 'Неизвестно',
            transaction_count=row.count,
            total_amount=row.total_amount or Decimal(0),
            avg_amount=row.avg_amount or Decimal(0),
            first_transaction_date=row.first_date,
            last_transaction_date=row.last_date,
            is_regular=row.is_regular or False
        ))

    # ==============================
    # 5-11. Other Analytics
    # ==============================

    # Regional distribution
    regional_distribution = []
    # Source distribution
    source_distribution = []

    # Processing funnel
    approved_count = status_counts.get(BankTransactionStatusEnum.APPROVED.value, 0)
    conversion_rate = float(approved_count / total_count * 100) if total_count > 0 else 0

    funnel_stages = []
    for status_enum in BankTransactionStatusEnum:
        count = status_counts.get(status_enum.value, 0)
        amount = sum(t.amount for t in transactions if t.status == status_enum)

        funnel_stages.append(ProcessingFunnelStage(
            status=status_enum.value,
            count=count,
            amount=amount,
            percent_of_total=float(count / total_count * 100) if total_count > 0 else 0,
            avg_processing_hours=None  # TODO: Calculate from reviewed_at - created_at
        ))

    processing_funnel = ProcessingFunnelData(
        stages=funnel_stages,
        total_count=total_count,
        conversion_rate_to_approved=conversion_rate
    )

    # AI Performance
    confidence_brackets = [
        ('High (≥90%)', constants.CONFIDENCE_HIGH_THRESHOLD, 1.0),
        ('Medium (70-90%)', constants.CONFIDENCE_MEDIUM_THRESHOLD, constants.CONFIDENCE_HIGH_THRESHOLD),
        ('Low (50-70%)', constants.CONFIDENCE_LOW_THRESHOLD, constants.CONFIDENCE_MEDIUM_THRESHOLD),
        ('Very Low (<50%)', 0.0, constants.CONFIDENCE_LOW_THRESHOLD),
    ]

    confidence_distribution = []
    for bracket_name, min_conf, max_conf in confidence_brackets:
        bracket_transactions = [
            t for t in categorized_transactions
            if t.category_confidence and min_conf <= t.category_confidence < max_conf
        ]
        count = len(bracket_transactions)
        amount = sum(t.amount for t in bracket_transactions)

        confidence_distribution.append(ConfidenceBracket(
            bracket=bracket_name,
            min_confidence=min_conf,
            max_confidence=max_conf,
            count=count,
            total_amount=amount,
            percent_of_total=float(count / len(categorized_transactions) * 100) if categorized_transactions else 0
        ))

    high_confidence_count = len([t for t in categorized_transactions if t.category_confidence and t.category_confidence >= constants.CONFIDENCE_HIGH_THRESHOLD])
    low_confidence_count = len([t for t in categorized_transactions if t.category_confidence and t.category_confidence < constants.CONFIDENCE_MEDIUM_THRESHOLD])

    ai_performance = AIPerformanceData(
        confidence_distribution=confidence_distribution,
        avg_confidence=avg_confidence or 0.0,
        high_confidence_count=high_confidence_count,
        high_confidence_percent=float(high_confidence_count / len(categorized_transactions) * 100) if categorized_transactions else 0,
        low_confidence_count=low_confidence_count,
        low_confidence_percent=float(low_confidence_count / len(categorized_transactions) * 100) if categorized_transactions else 0
    )

    # Low confidence items
    low_confidence_items = []
    for t in [t for t in transactions if t.category_confidence and t.category_confidence < constants.CONFIDENCE_MEDIUM_THRESHOLD][:50]:
        low_confidence_items.append(LowConfidenceItem(
            transaction_id=t.id,
            transaction_date=t.transaction_date,
            counterparty_name=t.counterparty_name or 'Неизвестно',
            amount=t.amount,
            payment_purpose=t.payment_purpose,
            suggested_category_name=t.suggested_category_rel.name if t.suggested_category_rel else None,
            category_confidence=float(t.category_confidence),
            status=t.status.value
        ))

    # Confidence scatter (limit to biggest operations for performance)
    confidence_candidates = [
        t for t in transactions
        if t.category_confidence is not None
    ]
    confidence_candidates.sort(key=lambda tx: abs(tx.amount), reverse=True)
    confidence_scatter = []
    for t in confidence_candidates[:500]:
        confidence_scatter.append(ConfidenceScatterPoint(
            transaction_id=t.id,
            transaction_date=t.transaction_date,
            counterparty_name=t.counterparty_name or 'Неизвестно',
            amount=t.amount,
            category_confidence=float(t.category_confidence) if t.category_confidence is not None else None,
            status=t.status.value,
            transaction_type=t.transaction_type,
            is_regular_payment=bool(t.is_regular_payment),
        ))

    # Regular payments
    regular_payments_list = []

    # Exhibitions
    exhibitions = []

    return BankTransactionAnalytics(
        kpis=kpis,
        monthly_flow=monthly_flow,
        daily_flow=daily_flow,
        top_categories=top_categories,
        category_type_distribution=category_type_distribution,
        top_counterparties=top_counterparties,
        regional_distribution=regional_distribution,
        source_distribution=source_distribution,
        processing_funnel=processing_funnel,
        ai_performance=ai_performance,
        low_confidence_items=low_confidence_items,
        activity_heatmap=activity_heatmap,
        status_timeline=status_timeline,
        confidence_scatter=confidence_scatter,
        regular_payments=regular_payments_list,
        exhibitions=exhibitions
    )
