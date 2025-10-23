from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
import math

from app.db import get_db
from app.db.models import Expense, BudgetCategory, Contractor, Organization, ExpenseStatusEnum
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseInDB, ExpenseList, ExpenseStatusUpdate

router = APIRouter()


@router.get("/", response_model=ExpenseList)
def get_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ExpenseStatusEnum] = None,
    category_id: Optional[int] = None,
    contractor_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all expenses with filters and pagination"""
    query = db.query(Expense)

    # Apply filters
    if status:
        query = query.filter(Expense.status == status)

    if category_id:
        query = query.filter(Expense.category_id == category_id)

    if contractor_id:
        query = query.filter(Expense.contractor_id == contractor_id)

    if organization_id:
        query = query.filter(Expense.organization_id == organization_id)

    if date_from:
        query = query.filter(Expense.request_date >= date_from)

    if date_to:
        query = query.filter(Expense.request_date <= date_to)

    if search:
        query = query.filter(
            or_(
                Expense.number.ilike(f"%{search}%"),
                Expense.comment.ilike(f"%{search}%"),
                Expense.requester.ilike(f"%{search}%")
            )
        )

    # Get total count
    total = query.count()

    # Get items with pagination
    expenses = query.order_by(Expense.request_date.desc()).offset(skip).limit(limit).all()

    # Calculate pagination
    pages = math.ceil(total / limit) if limit > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    return ExpenseList(
        total=total,
        items=expenses,
        page=page,
        page_size=limit,
        pages=pages
    )


@router.get("/{expense_id}", response_model=ExpenseInDB)
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    """Get expense by ID"""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )
    return expense


@router.post("/", response_model=ExpenseInDB, status_code=status.HTTP_201_CREATED)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    """Create new expense"""
    # Check if expense with same number exists
    existing = db.query(Expense).filter(Expense.number == expense.number).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expense with number '{expense.number}' already exists"
        )

    # Validate category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == expense.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {expense.category_id} not found"
        )

    # Validate organization exists
    organization = db.query(Organization).filter(Organization.id == expense.organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {expense.organization_id} not found"
        )

    # Validate contractor if provided
    if expense.contractor_id:
        contractor = db.query(Contractor).filter(Contractor.id == expense.contractor_id).first()
        if not contractor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contractor with id {expense.contractor_id} not found"
            )

    db_expense = Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.put("/{expense_id}", response_model=ExpenseInDB)
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    """Update expense"""
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Update fields
    update_data = expense.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_expense, field, value)

    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.patch("/{expense_id}/status", response_model=ExpenseInDB)
def update_expense_status(
    expense_id: int,
    status_update: ExpenseStatusUpdate,
    db: Session = Depends(get_db)
):
    """Update expense status"""
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    db_expense.status = status_update.status

    # Auto-update related fields based on status
    if status_update.status == ExpenseStatusEnum.PAID:
        db_expense.is_paid = True
        if not db_expense.payment_date:
            db_expense.payment_date = datetime.utcnow()
    elif status_update.status == ExpenseStatusEnum.CLOSED:
        db_expense.is_closed = True

    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    """Delete expense"""
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    db.delete(db_expense)
    db.commit()
    return None


@router.get("/stats/totals")
def get_expense_totals(
    year: Optional[int] = None,
    month: Optional[int] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get expense totals with filters"""
    query = db.query(func.sum(Expense.amount).label("total"))

    if year:
        query = query.filter(func.extract('year', Expense.request_date) == year)

    if month:
        query = query.filter(func.extract('month', Expense.request_date) == month)

    if category_id:
        query = query.filter(Expense.category_id == category_id)

    result = query.first()
    total = float(result.total) if result.total else 0.0

    return {"total": total}
