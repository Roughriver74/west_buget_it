"""
API endpoints for Bank Transactions
Управление банковскими операциями (списаниями и поступлениями)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import io
import logging

from app.db import get_db
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
)
from app.utils.auth import get_current_active_user
from app.utils.excel_export import encode_filename_header
from app.services.bank_transaction_import import BankTransactionImporter
from app.services.transaction_classifier import TransactionClassifier, RegularPaymentDetector
from app.services.odata_sync import ODataBankTransactionSync, ODataSyncConfig

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=BankTransactionList)
def get_bank_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status: Optional[BankTransactionStatusEnum] = None,
    transaction_type: Optional[BankTransactionTypeEnum] = None,
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
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for bank transactions
    """
    query = db.query(BankTransaction)

    # Department filtering
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

    query = query.filter(BankTransaction.is_active == True)

    # Count by status
    total_transactions = query.count()
    total_amount = query.filter(
        BankTransaction.transaction_type == BankTransactionTypeEnum.DEBIT
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
        total_amount=total_amount,
        new_count=new_count,
        categorized_count=categorized_count,
        matched_count=matched_count,
        approved_count=approved_count,
        needs_review_count=needs_review_count,
        avg_category_confidence=float(avg_confidence) if avg_confidence else None,
        avg_matching_score=float(avg_matching) if avg_matching else None,
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
    amount_min = tx.amount * Decimal('0.95')
    amount_max = tx.amount * Decimal('1.05')

    # 2. Date range (±30 days from transaction)
    from datetime import timedelta
    date_min = tx.transaction_date - timedelta(days=30)
    date_max = tx.transaction_date + timedelta(days=30)

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
    Soft delete transaction (set is_active=False)
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

    tx.is_active = False
    tx.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Transaction deleted successfully"}


@router.post("/bulk-delete")
def bulk_delete_transactions(
    transaction_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk soft delete transactions (set is_active=False)
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

    # Soft delete all
    deleted_count = 0
    for tx in transactions:
        tx.is_active = False
        tx.updated_at = datetime.utcnow()
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


@router.post("/odata/sync", response_model=ODataSyncResult)
async def sync_from_odata(
    request: ODataSyncRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Sync bank transactions from 1C via OData

    Syncs bank transactions (debits and credits) from 1C OData service.
    Only ADMIN and MANAGER can perform sync.

    Features:
    - Fetches transactions from 1C OData endpoint
    - Creates new transactions or updates existing (by external_id_1c)
    - Supports date range filtering
    - Handles both DEBIT (списания) and CREDIT (поступления) operations

    Example request:
    {
        "odata_url": "http://server:port/base/odata/standard.odata",
        "username": "admin",
        "password": "password",
        "entity_name": "Document_BankStatement",
        "department_id": 1,
        "date_from": "2025-01-01",
        "date_to": "2025-01-31"
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

    try:
        # Create config
        config = ODataSyncConfig(
            base_url=request.odata_url,
            username=request.username,
            password=request.password,
            entity_name=request.entity_name,
            timeout=request.timeout
        )

        # Create sync service
        sync_service = ODataBankTransactionSync(db, config)

        # Perform sync
        result = sync_service.sync_transactions(
            department_id=request.department_id,
            date_from=request.date_from,
            date_to=request.date_to,
            organization_id=request.organization_id
        )

        # Log the operation
        logger.info(
            f"OData sync completed by user {current_user.id}: "
            f"created={result.get('created', 0)}, "
            f"updated={result.get('updated', 0)}, "
            f"skipped={result.get('skipped', 0)}"
        )

        return ODataSyncResult(**result)

    except Exception as e:
        logger.error(f"OData sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )
