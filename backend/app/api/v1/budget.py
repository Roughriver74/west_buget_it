from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from decimal import Decimal

from app.db import get_db
from app.db.models import User, BudgetPlan, BudgetCategory, Expense, ExpenseTypeEnum
from app.schemas import BudgetPlanCreate, BudgetPlanUpdate, BudgetPlanInDB
from app.utils.excel_export import ExcelExporter
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


class CellUpdateRequest(BaseModel):
    """Request to update a single budget cell"""
    year: int
    month: int
    category_id: int
    planned_amount: Decimal


class CopyPlanRequest(BaseModel):
    """Request to copy budget plan from another year"""
    coefficient: float = 1.0  # Коэффициент корректировки (1.0 = без изменений, 1.1 = +10%)


@router.get("/plans", response_model=List[BudgetPlanInDB])
def get_budget_plans(
    year: Optional[int] = None,
    month: Optional[int] = None,
    category_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get budget plans

    - USER: Can only see budget plans from their own department
    - MANAGER/ADMIN: Can see budget plans from all departments or filter by department
    """
    query = db.query(BudgetPlan)

    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetPlan.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(BudgetPlan.department_id == department_id)

    if year:
        query = query.filter(BudgetPlan.year == year)

    if month:
        query = query.filter(BudgetPlan.month == month)

    if category_id:
        query = query.filter(BudgetPlan.category_id == category_id)

    plans = query.order_by(BudgetPlan.year, BudgetPlan.month).offset(skip).limit(limit).all()
    return plans


@router.get("/plans/{plan_id}", response_model=BudgetPlanInDB)
def get_budget_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get budget plan by ID

    - USER: Can only view budget plans from their own department
    - MANAGER/ADMIN: Can view budget plans from any department
    """
    plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with id {plan_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if plan.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only view budget plans from your own department"
            )

    return plan


@router.post("/plans", response_model=BudgetPlanInDB, status_code=status.HTTP_201_CREATED)
def create_budget_plan(
    plan: BudgetPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new budget plan

    - USER: Can only create budget plans in their own department
    - MANAGER/ADMIN: Can create budget plans in any department
    """
    # Validate category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == plan.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {plan.category_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if category.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only create budget plans for categories in your own department"
            )

    # Check if plan for this period already exists
    existing = db.query(BudgetPlan).filter(
        BudgetPlan.year == plan.year,
        BudgetPlan.month == plan.month,
        BudgetPlan.category_id == plan.category_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Budget plan for {plan.year}-{plan.month:02d} and category {plan.category_id} already exists"
        )

    # Create plan with department_id from category
    plan_data = plan.model_dump()
    plan_data['department_id'] = category.department_id
    db_plan = BudgetPlan(**plan_data)
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.put("/plans/{plan_id}", response_model=BudgetPlanInDB)
def update_budget_plan(
    plan_id: int,
    plan: BudgetPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update budget plan

    - USER: Can only update budget plans from their own department
    - MANAGER/ADMIN: Can update budget plans from any department
    """
    db_plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with id {plan_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if db_plan.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only update budget plans from your own department"
            )

    # Update fields
    update_data = plan.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_plan, field, value)

    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete budget plan

    - USER: Can only delete budget plans from their own department
    - MANAGER/ADMIN: Can delete budget plans from any department
    """
    db_plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with id {plan_id} not found"
        )

    # Check department access for USER role
    if current_user.role == UserRoleEnum.USER:
        if db_plan.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only delete budget plans from your own department"
            )

    db.delete(db_plan)
    db.commit()
    return None


@router.get("/summary")
def get_budget_summary(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get budget summary (plan vs actual)

    - USER: Can only see budget summary for their own department
    - MANAGER/ADMIN: Can see budget summary for all departments or filter by department
    """
    # Enforce department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        department_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        pass

    # Get planned amounts
    plan_query = db.query(
        BudgetPlan.category_id,
        func.sum(BudgetPlan.planned_amount).label("planned"),
        func.sum(BudgetPlan.capex_planned).label("capex_plan"),
        func.sum(BudgetPlan.opex_planned).label("opex_plan")
    ).filter(BudgetPlan.year == year)

    if month:
        plan_query = plan_query.filter(BudgetPlan.month == month)

    if department_id:
        plan_query = plan_query.filter(BudgetPlan.department_id == department_id)

    plan_query = plan_query.group_by(BudgetPlan.category_id)
    plans = plan_query.all()

    # Get actual amounts
    actual_query = db.query(
        Expense.category_id,
        func.sum(Expense.amount).label("actual")
    ).filter(func.extract('year', Expense.request_date) == year)

    if month:
        actual_query = actual_query.filter(func.extract('month', Expense.request_date) == month)

    if department_id:
        actual_query = actual_query.filter(Expense.department_id == department_id)

    actual_query = actual_query.group_by(Expense.category_id)
    actuals = {item.category_id: float(item.actual) for item in actual_query.all()}

    # Combine results
    result = []
    for plan in plans:
        category = db.query(BudgetCategory).filter(BudgetCategory.id == plan.category_id).first()
        actual = actuals.get(plan.category_id, 0.0)
        planned = float(plan.planned) if plan.planned else 0.0

        result.append({
            "category_id": plan.category_id,
            "category_name": category.name if category else "Unknown",
            "category_type": category.type if category else None,
            "planned": planned,
            "actual": actual,
            "remaining": planned - actual,
            "execution_percent": round((actual / planned * 100) if planned > 0 else 0, 2),
            "capex_plan": float(plan.capex_plan) if plan.capex_plan else 0.0,
            "opex_plan": float(plan.opex_plan) if plan.opex_plan else 0.0,
        })

    # Calculate totals
    total_planned = sum(item["planned"] for item in result)
    total_actual = sum(item["actual"] for item in result)

    return {
        "year": year,
        "month": month,
        "categories": result,
        "totals": {
            "planned": total_planned,
            "actual": total_actual,
            "remaining": total_planned - total_actual,
            "execution_percent": round((total_actual / total_planned * 100) if total_planned > 0 else 0, 2)
        }
    }


@router.get("/plans/year/{year}")
def get_budget_plan_for_year(
    year: int,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get budget plan for entire year in pivot format (categories x months)"""
    # Get all active categories
    categories_query = db.query(BudgetCategory).filter(BudgetCategory.is_active == True)
    if department_id:
        categories_query = categories_query.filter(BudgetCategory.department_id == department_id)
    categories = categories_query.order_by(BudgetCategory.name).all()

    # Get all plans for the year
    plans_query = db.query(BudgetPlan).filter(BudgetPlan.year == year)
    if department_id:
        plans_query = plans_query.filter(BudgetPlan.department_id == department_id)
    plans = plans_query.all()

    # Create a lookup dictionary for plans
    plan_lookup = {}
    for plan in plans:
        key = (plan.category_id, plan.month)
        plan_lookup[key] = {
            "id": plan.id,
            "planned_amount": float(plan.planned_amount),
            "capex_planned": float(plan.capex_planned),
            "opex_planned": float(plan.opex_planned)
        }

    # Get actual expenses for the year
    actual_query = db.query(
        Expense.category_id,
        func.extract('month', Expense.request_date).label('month'),
        func.sum(Expense.amount).label("actual")
    ).filter(
        func.extract('year', Expense.request_date) == year
    )
    if department_id:
        actual_query = actual_query.filter(Expense.department_id == department_id)
    actual_query = actual_query.group_by(Expense.category_id, func.extract('month', Expense.request_date))

    actual_lookup = {}
    for item in actual_query.all():
        key = (item.category_id, int(item.month))
        actual_lookup[key] = float(item.actual)

    # Build result
    result = []
    for category in categories:
        row = {
            "category_id": category.id,
            "category_name": category.name,
            "category_type": category.type,
            "parent_id": category.parent_id,
            "months": {}
        }

        # Add data for each month
        for month in range(1, 13):
            key = (category.id, month)
            planned_amount = plan_lookup[key]["planned_amount"] if key in plan_lookup else 0
            actual_amount = actual_lookup.get(key, 0)

            row["months"][str(month)] = {
                "id": plan_lookup[key]["id"] if key in plan_lookup else None,
                "planned_amount": planned_amount,
                "actual_amount": actual_amount,
                "remaining": planned_amount - actual_amount,
                "capex_planned": plan_lookup[key]["capex_planned"] if key in plan_lookup else 0,
                "opex_planned": plan_lookup[key]["opex_planned"] if key in plan_lookup else 0
            }

        result.append(row)

    return {
        "year": year,
        "categories": result
    }


@router.post("/plans/year/{year}/init")
def initialize_budget_plan(
    year: int,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Initialize budget plan for the year (create empty entries for all categories and months)"""
    # Get department_id from query params or use user's department
    target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required. Please specify department_id parameter or ensure user has a department."
        )

    # Get all active categories for this department
    categories = db.query(BudgetCategory).filter(
        BudgetCategory.is_active == True,
        BudgetCategory.department_id == target_department_id
    ).all()

    created_count = 0
    for category in categories:
        for month in range(1, 13):
            # Check if plan already exists
            existing = db.query(BudgetPlan).filter(
                BudgetPlan.year == year,
                BudgetPlan.month == month,
                BudgetPlan.category_id == category.id,
                BudgetPlan.department_id == target_department_id
            ).first()

            if not existing:
                new_plan = BudgetPlan(
                    year=year,
                    month=month,
                    category_id=category.id,
                    department_id=target_department_id,
                    planned_amount=0,
                    capex_planned=0 if category.type == ExpenseTypeEnum.OPEX else 0,
                    opex_planned=0 if category.type == ExpenseTypeEnum.CAPEX else 0
                )
                db.add(new_plan)
                created_count += 1

    db.commit()

    return {
        "message": f"Initialized budget plan for {year} (department #{target_department_id})",
        "created_entries": created_count,
        "department_id": target_department_id
    }


@router.post("/plans/year/{year}/copy-from/{source_year}")
def copy_budget_plan(
    year: int,
    source_year: int,
    request: CopyPlanRequest,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Copy budget plan from source year to target year with optional coefficient"""
    # Get department_id from query params or use user's department
    target_department_id = department_id if department_id is not None else current_user.department_id

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required. Please specify department_id parameter or ensure user has a department."
        )

    # Get source plans for this department only
    source_plans = db.query(BudgetPlan).filter(
        BudgetPlan.year == source_year,
        BudgetPlan.department_id == target_department_id
    ).all()

    if not source_plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No budget plans found for year {source_year} in department #{target_department_id}"
        )

    created_count = 0
    updated_count = 0

    for source_plan in source_plans:
        # Check if target plan already exists
        existing = db.query(BudgetPlan).filter(
            BudgetPlan.year == year,
            BudgetPlan.month == source_plan.month,
            BudgetPlan.category_id == source_plan.category_id,
            BudgetPlan.department_id == target_department_id
        ).first()

        new_amount = float(source_plan.planned_amount) * request.coefficient
        new_capex = float(source_plan.capex_planned) * request.coefficient
        new_opex = float(source_plan.opex_planned) * request.coefficient

        if existing:
            # Update existing plan
            existing.planned_amount = Decimal(str(round(new_amount, 2)))
            existing.capex_planned = Decimal(str(round(new_capex, 2)))
            existing.opex_planned = Decimal(str(round(new_opex, 2)))
            updated_count += 1
        else:
            # Create new plan
            new_plan = BudgetPlan(
                year=year,
                month=source_plan.month,
                category_id=source_plan.category_id,
                department_id=target_department_id,
                planned_amount=Decimal(str(round(new_amount, 2))),
                capex_planned=Decimal(str(round(new_capex, 2))),
                opex_planned=Decimal(str(round(new_opex, 2)))
            )
            db.add(new_plan)
            created_count += 1

    db.commit()

    return {
        "message": f"Copied budget plan from {source_year} to {year} with coefficient {request.coefficient} (department #{target_department_id})",
        "created_entries": created_count,
        "updated_entries": updated_count,
        "department_id": target_department_id
    }


@router.patch("/plans/cell")
def update_budget_cell(
    request: CellUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a single budget plan cell (upsert)"""
    # Check if category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == request.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {request.category_id} not found"
        )

    # Get department_id from category (since category belongs to department)
    department_id = category.department_id

    # Try to find existing plan (must match department too!)
    existing = db.query(BudgetPlan).filter(
        BudgetPlan.year == request.year,
        BudgetPlan.month == request.month,
        BudgetPlan.category_id == request.category_id,
        BudgetPlan.department_id == department_id
    ).first()

    # Calculate capex/opex based on category type
    if category.type == ExpenseTypeEnum.CAPEX:
        capex_amount = request.planned_amount
        opex_amount = Decimal(0)
    else:
        capex_amount = Decimal(0)
        opex_amount = request.planned_amount

    if existing:
        # Update existing plan
        existing.planned_amount = request.planned_amount
        existing.capex_planned = capex_amount
        existing.opex_planned = opex_amount
        db.commit()
        db.refresh(existing)
        return {
            "message": "Budget cell updated",
            "plan": {
                "id": existing.id,
                "year": existing.year,
                "month": existing.month,
                "category_id": existing.category_id,
                "department_id": existing.department_id,
                "planned_amount": float(existing.planned_amount)
            }
        }
    else:
        # Create new plan (WITH department_id from category!)
        new_plan = BudgetPlan(
            year=request.year,
            month=request.month,
            category_id=request.category_id,
            department_id=department_id,
            planned_amount=request.planned_amount,
            capex_planned=capex_amount,
            opex_planned=opex_amount
        )
        db.add(new_plan)
        db.commit()
        db.refresh(new_plan)
        return {
            "message": "Budget cell created",
            "plan": {
                "id": new_plan.id,
                "year": new_plan.year,
                "month": new_plan.month,
                "category_id": new_plan.category_id,
                "department_id": new_plan.department_id,
                "planned_amount": float(new_plan.planned_amount)
            }
        }


@router.get("/overview/{year}/{month}")
def get_budget_overview(
    year: int,
    month: int,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get budget overview (plan vs actual) for specific month"""
    # Get all active categories
    categories_query = db.query(BudgetCategory).filter(
        BudgetCategory.is_active == True
    )

    if department_id:
        categories_query = categories_query.filter(BudgetCategory.department_id == department_id)

    categories = categories_query.order_by(BudgetCategory.name).all()

    # Get plans for the month
    plans_query = db.query(BudgetPlan).filter(
        BudgetPlan.year == year,
        BudgetPlan.month == month
    )

    if department_id:
        plans_query = plans_query.filter(BudgetPlan.department_id == department_id)

    plans = plans_query.all()

    plan_lookup = {p.category_id: float(p.planned_amount) for p in plans}

    # Get actual expenses for the month
    actual_query = db.query(
        Expense.category_id,
        func.sum(Expense.amount).label("actual")
    ).filter(
        func.extract('year', Expense.request_date) == year,
        func.extract('month', Expense.request_date) == month
    )

    if department_id:
        actual_query = actual_query.filter(Expense.department_id == department_id)

    actual_query = actual_query.group_by(Expense.category_id)

    actual_lookup = {item.category_id: float(item.actual) for item in actual_query.all()}

    # Build result
    result = []
    for category in categories:
        planned = plan_lookup.get(category.id, 0.0)
        actual = actual_lookup.get(category.id, 0.0)
        remaining = planned - actual
        execution_percent = round((actual / planned * 100) if planned > 0 else 0, 2)
        is_overspent = actual > planned

        result.append({
            "category_id": category.id,
            "category_name": category.name,
            "category_type": category.type,
            "parent_id": category.parent_id,
            "planned": planned,
            "actual": actual,
            "remaining": remaining,
            "execution_percent": execution_percent,
            "is_overspent": is_overspent
        })

    # Calculate totals
    total_planned = sum(item["planned"] for item in result)
    total_actual = sum(item["actual"] for item in result)
    total_remaining = total_planned - total_actual
    total_execution = round((total_actual / total_planned * 100) if total_planned > 0 else 0, 2)

    # Calculate OPEX totals
    opex_items = [item for item in result if item["category_type"] == ExpenseTypeEnum.OPEX]
    opex_planned = sum(item["planned"] for item in opex_items)
    opex_actual = sum(item["actual"] for item in opex_items)
    opex_remaining = opex_planned - opex_actual
    opex_execution = round((opex_actual / opex_planned * 100) if opex_planned > 0 else 0, 2)

    # Calculate CAPEX totals
    capex_items = [item for item in result if item["category_type"] == ExpenseTypeEnum.CAPEX]
    capex_planned = sum(item["planned"] for item in capex_items)
    capex_actual = sum(item["actual"] for item in capex_items)
    capex_remaining = capex_planned - capex_actual
    capex_execution = round((capex_actual / capex_planned * 100) if capex_planned > 0 else 0, 2)

    return {
        "year": year,
        "month": month,
        "categories": result,
        "totals": {
            "planned": total_planned,
            "actual": total_actual,
            "remaining": total_remaining,
            "execution_percent": total_execution
        },
        "opex_totals": {
            "planned": opex_planned,
            "actual": opex_actual,
            "remaining": opex_remaining,
            "execution_percent": opex_execution
        },
        "capex_totals": {
            "planned": capex_planned,
            "actual": capex_actual,
            "remaining": capex_remaining,
            "execution_percent": capex_execution
        }
    }


@router.get("/plans/year/{year}/export")
def export_budget_plan_to_excel(year: int, db: Session = Depends(get_db)):
    """Export budget plan for year to Excel file"""
    # Get budget plan data
    categories = db.query(BudgetCategory).filter(BudgetCategory.is_active == True).order_by(BudgetCategory.name).all()
    plans = db.query(BudgetPlan).filter(BudgetPlan.year == year).all()

    # Create a lookup dictionary for plans
    plan_lookup = {}
    for plan in plans:
        key = (plan.category_id, plan.month)
        plan_lookup[key] = {
            "id": plan.id,
            "planned_amount": float(plan.planned_amount),
            "capex_planned": float(plan.capex_planned),
            "opex_planned": float(plan.opex_planned)
        }

    # Build result
    categories_data = []
    for category in categories:
        row = {
            "category_id": category.id,
            "category_name": category.name,
            "category_type": category.type,
            "months": {}
        }

        # Add data for each month
        for month in range(1, 13):
            key = (category.id, month)
            if key in plan_lookup:
                row["months"][str(month)] = plan_lookup[key]
            else:
                row["months"][str(month)] = {
                    "id": None,
                    "planned_amount": 0,
                    "capex_planned": 0,
                    "opex_planned": 0
                }

        categories_data.append(row)

    # Generate Excel file
    excel_file = ExcelExporter.export_budget_plan(year, categories_data)

    # Return as download
    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=budget_plan_{year}.xlsx"}
    )


@router.get("/overview/{year}/{month}/export")
def export_budget_overview_to_excel(
    year: int,
    month: int,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Export budget overview for specific month to Excel file"""
    # Get budget overview data (reuse the logic from get_budget_overview)
    overview_data = get_budget_overview(year, month, department_id, db, current_user)

    # Generate Excel file
    excel_file = ExcelExporter.export_budget_overview(year, month, overview_data)

    # Return as download
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    filename = f"budget_overview_{year}_{month:02d}_{month_names.get(month, month)}.xlsx"

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
