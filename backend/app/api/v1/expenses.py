from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from datetime import datetime, timezone
import math
import os
from pydantic import BaseModel, Field

from app.db import get_db
from app.db.models import Expense, BudgetCategory, Contractor, Organization, ExpenseStatusEnum, User, UserRoleEnum
from app.schemas import ExpenseCreate, ExpenseUpdate, ExpenseInDB, ExpenseList, ExpenseStatusUpdate
from app.utils.excel_export import ExcelExporter, encode_filename_header
from app.services.ftp_import_service import import_from_ftp
from app.services.baseline_bus import baseline_bus
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
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
        headers=encode_filename_header(filename)
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
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
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
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get expense by ID

    - USER: Can only view expenses from their own department
    - MANAGER/ADMIN: Can view expenses from any department
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access for USER role
    # Return 404 instead of 403 to prevent information disclosure
    if current_user.role == UserRoleEnum.USER:
        if expense.department_id != current_user.department_id:
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

    # Convert ISO date strings to datetime if needed (fix timezone issues)
    if 'request_date' in expense_data and expense_data['request_date']:
        if isinstance(expense_data['request_date'], str):
            # Parse ISO string and ensure time is set to noon to avoid timezone shift
            dt = datetime.fromisoformat(expense_data['request_date'].replace('Z', '+00:00'))
            expense_data['request_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)

    if 'payment_date' in expense_data and expense_data['payment_date']:
        if isinstance(expense_data['payment_date'], str):
            # Parse ISO string and ensure time is set to noon to avoid timezone shift
            dt = datetime.fromisoformat(expense_data['payment_date'].replace('Z', '+00:00'))
            expense_data['payment_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)

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

    # Validate category exists and belongs to same department (if USER)
    category = db.query(BudgetCategory).filter(BudgetCategory.id == expense.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {expense.category_id} not found"
        )

    # SECURITY: Check that category belongs to same department
    if current_user.role == UserRoleEnum.USER:
        if category.department_id != current_user.department_id:
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

    # Validate contractor if provided and check department
    if expense.contractor_id:
        contractor = db.query(Contractor).filter(Contractor.id == expense.contractor_id).first()
        if not contractor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Contractor with id {expense.contractor_id} not found"
            )

        # SECURITY: Check that contractor belongs to same department
        if current_user.role == UserRoleEnum.USER:
            if contractor.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contractor with id {expense.contractor_id} not found"
                )

    db_expense = Expense(**expense_data)
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    baseline_bus.invalidate_for_expense(
        category_id=db_expense.category_id,
        department_id=db_expense.department_id,
        request_year=db_expense.request_date.year if db_expense.request_date else None,
    )
    return db_expense


@router.put("/{expense_id}", response_model=ExpenseInDB)
def update_expense(
    expense_id: int,
    expense: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update expense

    - USER: Can only update expenses from their own department
    - MANAGER/ADMIN: Can update expenses from any department
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if db_expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only update expenses from your own department"
            )

    original_category_id = db_expense.category_id
    original_department_id = db_expense.department_id
    original_year = db_expense.request_date.year if db_expense.request_date else None

    # Update fields
    update_data = expense.model_dump(exclude_unset=True)

    # Convert ISO date strings to datetime if needed (fix timezone issues)
    if 'request_date' in update_data and update_data['request_date']:
        if isinstance(update_data['request_date'], str):
            # Parse ISO string and ensure time is set to noon to avoid timezone shift
            dt = datetime.fromisoformat(update_data['request_date'].replace('Z', '+00:00'))
            update_data['request_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)

    if 'payment_date' in update_data and update_data['payment_date']:
        if isinstance(update_data['payment_date'], str):
            # Parse ISO string and ensure time is set to noon to avoid timezone shift
            dt = datetime.fromisoformat(update_data['payment_date'].replace('Z', '+00:00'))
            update_data['payment_date'] = dt.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)

    # SECURITY: Validate that new category/contractor belong to same department (for USER)
    if current_user.role == UserRoleEnum.USER:
        # Check category if being updated
        if 'category_id' in update_data and update_data['category_id']:
            category = db.query(BudgetCategory).filter(
                BudgetCategory.id == update_data['category_id']
            ).first()
            if not category:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {update_data['category_id']} not found"
                )
            if category.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Category with id {update_data['category_id']} not found"
                )

        # Check contractor if being updated
        if 'contractor_id' in update_data and update_data['contractor_id']:
            contractor = db.query(Contractor).filter(
                Contractor.id == update_data['contractor_id']
            ).first()
            if not contractor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contractor with id {update_data['contractor_id']} not found"
                )
            if contractor.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Contractor with id {update_data['contractor_id']} not found"
                )
    for field, value in update_data.items():
        setattr(db_expense, field, value)

    db.commit()
    db.refresh(db_expense)
    baseline_bus.invalidate_for_expense(
        category_id=original_category_id,
        department_id=original_department_id,
        request_year=original_year,
    )
    baseline_bus.invalidate_for_expense(
        category_id=db_expense.category_id,
        department_id=db_expense.department_id,
        request_year=db_expense.request_date.year if db_expense.request_date else None,
    )
    return db_expense


@router.patch("/{expense_id}/status", response_model=ExpenseInDB)
def update_expense_status(
    expense_id: int,
    status_update: ExpenseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update expense status

    - USER: Can only update status of expenses from their own department
    - MANAGER/ADMIN: Can update status of expenses from any department
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if db_expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only update expenses from your own department"
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Mark expense as reviewed (снимает пометку 'needs_review')

    - USER: Can only mark expenses from their own department
    - MANAGER/ADMIN: Can mark expenses from any department
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if db_expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only review expenses from your own department"
            )

    db_expense.needs_review = False
    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete expense

    - USER: Can only delete expenses from their own department
    - MANAGER/ADMIN: Can delete expenses from any department
    """
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Expense with id {expense_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if db_expense.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only delete expenses from your own department"
            )

    category_id = db_expense.category_id
    department_id = db_expense.department_id
    request_year = db_expense.request_date.year if db_expense.request_date else None

    db.delete(db_expense)
    db.commit()
    baseline_bus.invalidate_for_expense(
        category_id=category_id,
        department_id=department_id,
        request_year=request_year,
    )
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

    impacted_rows = db.query(
        Expense.category_id,
        Expense.department_id,
        Expense.request_date,
    ).filter(
        Expense.id.in_(expense_ids)
    ).all()

    # Delete expenses
    deleted_count = db.query(Expense).filter(
        Expense.id.in_(expense_ids)
    ).delete(synchronize_session=False)

    db.commit()

    for category_id, department_id, request_date in impacted_rows:
        baseline_bus.invalidate_for_expense(
            category_id=category_id,
            department_id=department_id,
            request_year=request_date.year if request_date else None,
        )

    return {"deleted_count": deleted_count}


@router.get("/stats/totals")
def get_expense_totals(
    year: Optional[int] = None,
    month: Optional[int] = None,
    category_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get expense totals with filters

    - USER: Can only see totals from their own department
    - MANAGER/ADMIN: Can see totals from all departments or filter by department
    """
    query = db.query(func.sum(Expense.amount).label("total"))

    # Department filtering based on user role (Row Level Security)
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Expense.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.FOUNDER, UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(Expense.department_id == department_id)

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
    skip_duplicates: bool = Field(
        default=True,
        description="If True, updates only critical fields (status, amount, payment_date) for existing expenses. "
                    "If False, performs full update of all fields."
    )


@router.post("/import/ftp")
async def import_expenses_from_ftp(
    request: FTPImportRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import expenses from FTP server (ADMIN only)

    This endpoint will:
    1. Download Excel file from FTP
    2. Delete expenses from specified month onwards (if delete_from_year/month provided)
    3. Import new expenses from the file
    4. For existing expenses (matched by number):
       - If skip_duplicates=True: Update only critical fields (status, amount, payment_date, comment)
       - If skip_duplicates=False: Update all fields

    Note: Only ADMIN can import expenses from FTP
    """
    # Only ADMIN can import from FTP
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can import expenses from FTP"
        )

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


class BulkDepartmentTransferRequest(BaseModel):
    """Request model for bulk department transfer"""
    expense_ids: List[int] = Field(..., description="List of expense IDs to transfer")
    target_department_id: int = Field(..., description="Target department ID")


@router.post("/bulk/transfer-department")
def bulk_transfer_department(
    request: BulkDepartmentTransferRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Transfer multiple expenses to another department

    - **ADMIN/MANAGER**: Can transfer any expenses between departments
    - **USER**: Can only transfer expenses from their own department

    This endpoint will:
    1. Validate that all expense IDs exist
    2. Check permissions (USER can only transfer from their department)
    3. Transfer expenses to target department
    4. Invalidate affected baseline caches
    """
    # Only ADMIN and MANAGER can transfer between any departments
    # USER can only transfer from their own department
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER, UserRoleEnum.USER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to transfer expenses"
        )

    # Validate target department exists
    from app.db.models import Department
    target_department = db.query(Department).filter(
        Department.id == request.target_department_id,
        Department.is_active == True
    ).first()

    if not target_department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target department {request.target_department_id} not found"
        )

    # Get expenses to transfer
    expenses_query = db.query(Expense).filter(
        Expense.id.in_(request.expense_ids)
    )

    # USER can only transfer from their own department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no department assigned"
            )
        expenses_query = expenses_query.filter(
            Expense.department_id == current_user.department_id
        )

    expenses = expenses_query.all()

    if not expenses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No expenses found with provided IDs (or no permission to transfer them)"
        )

    # Track affected cache keys for invalidation
    affected_cache_keys = set()

    # Transfer expenses
    transferred_count = 0
    for expense in expenses:
        # Track old department for cache invalidation
        if expense.category_id and expense.department_id and expense.request_date:
            affected_cache_keys.add((
                expense.category_id,
                expense.department_id,
                expense.request_date.year
            ))

        # Update department
        old_department_id = expense.department_id
        expense.department_id = request.target_department_id
        transferred_count += 1

        # Track new department for cache invalidation
        if expense.category_id and expense.request_date:
            affected_cache_keys.add((
                expense.category_id,
                request.target_department_id,
                expense.request_date.year
            ))

    db.commit()

    # Invalidate affected baseline caches
    for category_id, department_id, year in affected_cache_keys:
        baseline_bus.invalidate(
            category_id=category_id,
            department_id=department_id,
            year=year
        )

    return {
        "success": True,
        "message": f"Successfully transferred {transferred_count} expense(s) to department '{target_department.name}'",
        "transferred_count": transferred_count,
        "target_department": {
            "id": target_department.id,
            "name": target_department.name
        }
    }


class Expense1CSyncRequest(BaseModel):
    """Request model for 1C expense sync"""
    date_from: datetime = Field(..., description="Start date for sync")
    date_to: datetime = Field(..., description="End date for sync")
    department_id: int = Field(..., description="Department ID for multi-tenancy")
    only_posted: bool = Field(default=True, description="Only sync posted documents")


@router.post("/sync/1c")
def sync_expenses_from_1c(
    request: Expense1CSyncRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Sync expense requests from 1C via OData (ADMIN/MANAGER only)

    This endpoint will:
    1. Connect to 1C OData API
    2. Fetch expense documents for the specified period
    3. Create/update expenses in the database
    4. Auto-create organizations and contractors if needed

    Features:
    - Uses external_id_1c to prevent duplicates
    - Updates existing expenses if data changes
    - Creates new organizations/contractors from 1C
    - Supports pagination for large datasets

    Note: Only ADMIN and MANAGER can sync expenses from 1C
    """
    # Permission check
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can sync expenses from 1C"
        )

    # Validate department exists
    from app.db.models import Department
    department = db.query(Department).filter(
        Department.id == request.department_id,
        Department.is_active == True
    ).first()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department {request.department_id} not found"
        )

    # Get 1C OData credentials from environment
    odata_url = os.getenv('ODATA_1C_URL', 'http://10.10.100.77/trade/odata/standard.odata')
    odata_username = os.getenv('ODATA_1C_USERNAME', 'odata.user')
    odata_password = os.getenv('ODATA_1C_PASSWORD', 'ak228Hu2hbs28')

    try:
        # Create OData client
        from app.services.odata_1c_client import OData1CClient
        odata_client = OData1CClient(
            base_url=odata_url,
            username=odata_username,
            password=odata_password
        )

        # Test connection
        if not odata_client.test_connection():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to connect to 1C OData service"
            )

        # Create sync service
        from app.services.expense_1c_sync import Expense1CSync
        sync_service = Expense1CSync(
            db=db,
            odata_client=odata_client,
            department_id=request.department_id
        )

        # Run sync
        result = sync_service.sync_expenses(
            date_from=request.date_from.date(),
            date_to=request.date_to.date(),
            batch_size=100,
            only_posted=request.only_posted
        )

        return {
            "success": result.to_dict()['success'],
            "message": "Sync completed" if result.to_dict()['success'] else "Sync completed with errors",
            "statistics": result.to_dict(),
            "department": {
                "id": department.id,
                "name": department.name
            }
        }

    except Exception as e:
        import traceback
        error_detail = f"Sync failed: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail
        )
