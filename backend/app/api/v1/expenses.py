from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from datetime import datetime, timezone
import math
import os
from pydantic import BaseModel

from app.db import get_db
from app.db.models import Expense, BudgetCategory, Contractor, Organization, ExpenseStatusEnum, User, UserRoleEnum
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseInDB, ExpenseList, ExpenseStatusUpdate
from app.utils.excel_export import ExcelExporter
from app.services.ftp_import_service import import_from_ftp
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/export")
def export_expenses_to_excel(
    status: Optional[ExpenseStatusEnum] = None,
    category_id: Optional[int] = None,
    contractor_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export expenses to Excel file

    - **USER**: Can only export expenses from their own department
    - **MANAGER**: Can export expenses from all departments
    - **ADMIN**: Can export expenses from all departments
    """
    # Get expenses with same filters as get_expenses endpoint
    query = db.query(Expense)

    # Department filtering based on user role (Row Level Security)
    if current_user.role == UserRoleEnum.USER:
        # USER can only export their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Expense.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(Expense.department_id == department_id)

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

    if year:
        query = query.filter(func.extract('year', Expense.request_date) == year)

    if month:
        query = query.filter(func.extract('month', Expense.request_date) == month)

    if search:
        search_filter = or_(
            Expense.number.ilike(f"%{search}%"),
            Expense.comment.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    # Get all matching expenses with eager loading (fix N+1 queries)
    query = query.options(
        joinedload(Expense.category),
        joinedload(Expense.contractor),
        joinedload(Expense.organization),
        joinedload(Expense.department_rel)
    )
    expenses = query.order_by(Expense.request_date.desc()).all()

    # Convert to dict for export
    expenses_data = []
    for expense in expenses:
        expense_dict = {
            "number": expense.number,
            "request_date": expense.request_date.isoformat() if expense.request_date else None,
            "category": {
                "name": expense.category.name if expense.category else "",
                "type": expense.category.type if expense.category else ""
            },
            "contractor": {
                "name": expense.contractor.name if expense.contractor else ""
            } if expense.contractor else None,
            "organization": {
                "name": expense.organization.name if expense.organization else ""
            },
            "amount": expense.amount,
            "status": expense.status,
            "payment_date": expense.payment_date.isoformat() if expense.payment_date else None,
            "comment": expense.comment or ""
        }
        expenses_data.append(expense_dict)

    # Prepare filters for header
    filters = {}
    if year:
        filters['year'] = year
    if month:
        filters['month'] = month
    if category_id:
        category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
        filters['category'] = category.name if category else f"ID {category_id}"

    # Generate Excel file
    excel_file = ExcelExporter.export_expenses(expenses_data, filters)

    # Generate filename
    filename_parts = ["expenses"]
    if year:
        filename_parts.append(str(year))
    if month:
        filename_parts.append(f"{month:02d}")
    if category_id:
        filename_parts.append(f"cat{category_id}")

    filename = "_".join(filename_parts) + ".xlsx"

    # Return as download
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/", response_model=ExpenseList)
def get_expenses(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[ExpenseStatusEnum] = None,
    category_id: Optional[int] = None,
    contractor_id: Optional[int] = None,
    organization_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    search: Optional[str] = None,
    needs_review: Optional[bool] = None,
    imported_from_ftp: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all expenses with filters and pagination

    - **USER**: Can only see expenses from their own department
    - **MANAGER**: Can see expenses from all departments
    - **ADMIN**: Can see expenses from all departments
    """
    query = db.query(Expense)

    # Department filtering based on user role (Row Level Security)
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Expense.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(Expense.department_id == department_id)

    # Apply other filters
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

    if needs_review is not None:
        query = query.filter(Expense.needs_review == needs_review)

    if imported_from_ftp is not None:
        query = query.filter(Expense.imported_from_ftp == imported_from_ftp)

    # Get total count
    total = query.count()

    # Get items with pagination and eager loading (fix N+1 queries)
    query = query.options(
        joinedload(Expense.category),
        joinedload(Expense.contractor),
        joinedload(Expense.organization),
        joinedload(Expense.department_rel)
    )
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
def create_expense(
    expense: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new expense

    Auto-assigns to user's department (or can be specified by ADMIN/MANAGER)
    """
    # USER can only create expenses in their own department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )

    # Determine the department_id we'll be using
    expense_data = expense.model_dump()
    target_department_id = None

    if current_user.role == UserRoleEnum.USER:
        # USER always creates in their own department
        target_department_id = current_user.department_id
        expense_data['department_id'] = current_user.department_id
    else:
        # MANAGER/ADMIN can specify department or use their own
        target_department_id = expense_data.get('department_id') or current_user.department_id
        if not target_department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required"
            )
        expense_data['department_id'] = target_department_id

    # Check if expense with same number exists in the same department
    # (number uniqueness is now scoped to department)
    existing = db.query(Expense).filter(
        Expense.number == expense.number,
        Expense.department_id == target_department_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expense with number '{expense.number}' already exists in this department"
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

    db_expense = Expense(**expense_data)
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
            db_expense.payment_date = datetime.now(timezone.utc)
    elif status_update.status == ExpenseStatusEnum.CLOSED:
        db_expense.is_closed = True

    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.patch("/{expense_id}/mark-reviewed", response_model=ExpenseInDB)
def mark_expense_reviewed(
    expense_id: int,
    db: Session = Depends(get_db)
):
    """Mark expense as reviewed (снимает пометку 'needs_review')"""
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    db_expense.needs_review = False
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


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_expenses(
    expense_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Bulk delete expenses by IDs (ADMIN only)

    Returns the number of deleted expenses
    """
    # Only ADMIN can bulk delete
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can bulk delete expenses"
        )

    if not expense_ids:
        return {"deleted_count": 0}

    # Delete expenses
    deleted_count = db.query(Expense).filter(
        Expense.id.in_(expense_ids)
    ).delete(synchronize_session=False)

    db.commit()

    return {"deleted_count": deleted_count}


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


class FTPImportRequest(BaseModel):
    """Request schema for FTP import"""
    remote_path: str
    delete_from_year: Optional[int] = None
    delete_from_month: Optional[int] = None
    skip_duplicates: bool = True


@router.post("/import/ftp")
async def import_expenses_from_ftp(
    request: FTPImportRequest,
    db: Session = Depends(get_db)
):
    """
    Import expenses from FTP server

    This endpoint will:
    1. Download Excel file from FTP
    2. Delete expenses from specified month onwards (default: July 2025)
    3. Import new expenses from the file
    4. Skip duplicates based on expense number
    """
    # Get FTP credentials from environment variables
    ftp_host = os.getenv("FTP_HOST", "floppisw.beget.tech")
    ftp_user = os.getenv("FTP_USER", "floppisw_zrds")
    ftp_pass = os.getenv("FTP_PASS", "4yZUaloOBmU!")

    try:
        result = await import_from_ftp(
            db=db,
            host=ftp_host,
            username=ftp_user,
            password=ftp_pass,
            remote_path=request.remote_path,
            delete_from_year=request.delete_from_year,
            delete_from_month=request.delete_from_month,
            skip_duplicates=request.skip_duplicates
        )

        return {
            "success": True,
            "message": "Import completed successfully",
            "statistics": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )
