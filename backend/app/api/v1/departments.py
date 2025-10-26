"""
Department management API endpoints
Multi-tenancy core: departments are the basis for data isolation
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import Department, User, UserRoleEnum, Expense, BudgetPlan
from app.schemas.department import (
    Department as DepartmentSchema,
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentListItem,
    DepartmentWithStats,
)
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/", response_model=List[DepartmentListItem])
async def list_departments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all departments

    - **ADMIN**: Can see all departments
    - **MANAGER**: Can see all departments
    - **USER**: Can only see their own department
    """
    query = db.query(Department)

    # Filter by active status if specified
    if is_active is not None:
        query = query.filter(Department.is_active == is_active)

    # USER role can only see their own department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Department.id == current_user.department_id)

    # ADMIN and MANAGER can see all departments
    departments = query.offset(skip).limit(limit).all()
    return departments


@router.post("/", response_model=DepartmentSchema, status_code=status.HTTP_201_CREATED)
async def create_department(
    department_data: DepartmentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new department (ADMIN only)

    - **name**: Department name (unique, 2-255 characters)
    - **code**: Department code (unique, 2-50 characters)
    - **description**: Optional description
    - **manager_name**: Optional manager name
    - **contact_email**: Optional contact email
    - **contact_phone**: Optional contact phone
    - **is_active**: Active status (default: true)
    """
    # Only ADMIN can create departments
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create departments"
        )

    # Check if name already exists
    existing_name = db.query(Department).filter(Department.name == department_data.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department name already exists"
        )

    # Check if code already exists
    existing_code = db.query(Department).filter(Department.code == department_data.code).first()
    if existing_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department code already exists"
        )

    # Create new department
    new_department = Department(
        name=department_data.name,
        code=department_data.code,
        description=department_data.description,
        ftp_subdivision_name=department_data.ftp_subdivision_name,
        manager_name=department_data.manager_name,
        contact_email=department_data.contact_email,
        contact_phone=department_data.contact_phone,
        is_active=department_data.is_active,
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    return new_department


@router.get("/{department_id}", response_model=DepartmentSchema)
async def get_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get department by ID

    - **ADMIN/MANAGER**: Can view any department
    - **USER**: Can only view their own department
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # USER role can only view their own department
    if current_user.role == UserRoleEnum.USER:
        if current_user.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this department"
            )

    return department


@router.get("/{department_id}/stats", response_model=DepartmentWithStats)
async def get_department_stats(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get department with statistics

    Returns department info with:
    - users_count: Number of users in department
    - expenses_count: Number of expenses
    - total_budget: Sum of all budget plans

    - **ADMIN/MANAGER**: Can view any department stats
    - **USER**: Can only view their own department stats
    """
    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # USER role can only view their own department
    if current_user.role == UserRoleEnum.USER:
        if current_user.department_id != department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this department"
            )

    # Calculate statistics
    users_count = db.query(func.count(User.id)).filter(User.department_id == department_id).scalar() or 0
    expenses_count = db.query(func.count(Expense.id)).filter(Expense.department_id == department_id).scalar() or 0
    total_budget = db.query(func.sum(BudgetPlan.planned_amount)).filter(
        BudgetPlan.department_id == department_id
    ).scalar() or 0.0

    # Create response with stats
    department_dict = {
        "id": department.id,
        "name": department.name,
        "code": department.code,
        "description": department.description,
        "ftp_subdivision_name": department.ftp_subdivision_name,
        "manager_name": department.manager_name,
        "contact_email": department.contact_email,
        "contact_phone": department.contact_phone,
        "is_active": department.is_active,
        "created_at": department.created_at,
        "updated_at": department.updated_at,
        "users_count": users_count,
        "expenses_count": expenses_count,
        "total_budget": float(total_budget),
    }

    return department_dict


@router.put("/{department_id}", response_model=DepartmentSchema)
async def update_department(
    department_id: int,
    department_update: DepartmentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update department by ID (ADMIN only)
    """
    # Only ADMIN can update departments
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update departments"
        )

    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Check name uniqueness if changing
    if department_update.name and department_update.name != department.name:
        existing_name = db.query(Department).filter(Department.name == department_update.name).first()
        if existing_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department name already exists"
            )

    # Check code uniqueness if changing
    if department_update.code and department_update.code != department.code:
        existing_code = db.query(Department).filter(Department.code == department_update.code).first()
        if existing_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department code already exists"
            )

    # Update fields
    update_data = department_update.model_dump(exclude_unset=True)

    # Log what we're updating
    from app.utils.logger import log_info
    log_info(f"Updating department {department_id} with data: {update_data}", "DepartmentUpdate")

    for field, value in update_data.items():
        old_value = getattr(department, field, None)
        setattr(department, field, value)
        log_info(f"  {field}: {old_value} -> {value}", "DepartmentUpdate")

    db.commit()
    log_info(f"Department {department_id} committed successfully", "DepartmentUpdate")
    db.refresh(department)

    return department


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate department by ID (ADMIN only)

    Note: This is a soft delete (sets is_active = false).
    Department data is preserved for historical reporting.
    """
    # Only ADMIN can deactivate departments
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can deactivate departments"
        )

    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Check if department has active users
    active_users_count = db.query(func.count(User.id)).filter(
        User.department_id == department_id,
        User.is_active == True
    ).scalar()

    if active_users_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department with {active_users_count} active users. Please reassign or deactivate users first."
        )

    # Hard delete: permanently remove from database
    db.delete(department)
    db.commit()

    return None


@router.post("/{department_id}/activate", response_model=DepartmentSchema)
async def activate_department(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Reactivate a deactivated department (ADMIN only)
    """
    # Only ADMIN can activate departments
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can activate departments"
        )

    department = db.query(Department).filter(Department.id == department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    if department.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department is already active"
        )

    department.is_active = True
    db.commit()
    db.refresh(department)

    return department
