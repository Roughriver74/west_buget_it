from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from decimal import Decimal

from app.db import get_db
from app.db.models import BudgetPlan, BudgetCategory, Expense, ExpenseTypeEnum
from app.schemas import BudgetPlanCreate, BudgetPlanUpdate, BudgetPlanInDB

router = APIRouter()


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
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get budget plans"""
    query = db.query(BudgetPlan)

    if year:
        query = query.filter(BudgetPlan.year == year)

    if month:
        query = query.filter(BudgetPlan.month == month)

    if category_id:
        query = query.filter(BudgetPlan.category_id == category_id)

    plans = query.order_by(BudgetPlan.year, BudgetPlan.month).offset(skip).limit(limit).all()
    return plans


@router.get("/plans/{plan_id}", response_model=BudgetPlanInDB)
def get_budget_plan(plan_id: int, db: Session = Depends(get_db)):
    """Get budget plan by ID"""
    plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with id {plan_id} not found"
        )
    return plan


@router.post("/plans", response_model=BudgetPlanInDB, status_code=status.HTTP_201_CREATED)
def create_budget_plan(plan: BudgetPlanCreate, db: Session = Depends(get_db)):
    """Create new budget plan"""
    # Validate category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == plan.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {plan.category_id} not found"
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

    db_plan = BudgetPlan(**plan.model_dump())
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.put("/plans/{plan_id}", response_model=BudgetPlanInDB)
def update_budget_plan(
    plan_id: int,
    plan: BudgetPlanUpdate,
    db: Session = Depends(get_db)
):
    """Update budget plan"""
    db_plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with id {plan_id} not found"
        )

    # Update fields
    update_data = plan.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_plan, field, value)

    db.commit()
    db.refresh(db_plan)
    return db_plan


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget_plan(plan_id: int, db: Session = Depends(get_db)):
    """Delete budget plan"""
    db_plan = db.query(BudgetPlan).filter(BudgetPlan.id == plan_id).first()
    if not db_plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Budget plan with id {plan_id} not found"
        )

    db.delete(db_plan)
    db.commit()
    return None


@router.get("/summary")
def get_budget_summary(
    year: int,
    month: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get budget summary (plan vs actual)"""
    # Get planned amounts
    plan_query = db.query(
        BudgetPlan.category_id,
        func.sum(BudgetPlan.planned_amount).label("planned"),
        func.sum(BudgetPlan.capex_planned).label("capex_plan"),
        func.sum(BudgetPlan.opex_planned).label("opex_plan")
    ).filter(BudgetPlan.year == year)

    if month:
        plan_query = plan_query.filter(BudgetPlan.month == month)

    plan_query = plan_query.group_by(BudgetPlan.category_id)
    plans = plan_query.all()

    # Get actual amounts
    actual_query = db.query(
        Expense.category_id,
        func.sum(Expense.amount).label("actual")
    ).filter(func.extract('year', Expense.request_date) == year)

    if month:
        actual_query = actual_query.filter(func.extract('month', Expense.request_date) == month)

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
def get_budget_plan_for_year(year: int, db: Session = Depends(get_db)):
    """Get budget plan for entire year in pivot format (categories x months)"""
    # Get all active categories
    categories = db.query(BudgetCategory).filter(BudgetCategory.is_active == True).order_by(BudgetCategory.name).all()

    # Get all plans for the year
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
    result = []
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

        result.append(row)

    return {
        "year": year,
        "categories": result
    }


@router.post("/plans/year/{year}/init")
def initialize_budget_plan(year: int, db: Session = Depends(get_db)):
    """Initialize budget plan for the year (create empty entries for all categories and months)"""
    # Get all active categories
    categories = db.query(BudgetCategory).filter(BudgetCategory.is_active == True).all()

    created_count = 0
    for category in categories:
        for month in range(1, 13):
            # Check if plan already exists
            existing = db.query(BudgetPlan).filter(
                BudgetPlan.year == year,
                BudgetPlan.month == month,
                BudgetPlan.category_id == category.id
            ).first()

            if not existing:
                new_plan = BudgetPlan(
                    year=year,
                    month=month,
                    category_id=category.id,
                    planned_amount=0,
                    capex_planned=0 if category.type == ExpenseTypeEnum.OPEX else 0,
                    opex_planned=0 if category.type == ExpenseTypeEnum.CAPEX else 0
                )
                db.add(new_plan)
                created_count += 1

    db.commit()

    return {
        "message": f"Initialized budget plan for {year}",
        "created_entries": created_count
    }


@router.post("/plans/year/{year}/copy-from/{source_year}")
def copy_budget_plan(
    year: int,
    source_year: int,
    request: CopyPlanRequest,
    db: Session = Depends(get_db)
):
    """Copy budget plan from source year to target year with optional coefficient"""
    # Get source plans
    source_plans = db.query(BudgetPlan).filter(BudgetPlan.year == source_year).all()

    if not source_plans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No budget plans found for year {source_year}"
        )

    created_count = 0
    updated_count = 0

    for source_plan in source_plans:
        # Check if target plan already exists
        existing = db.query(BudgetPlan).filter(
            BudgetPlan.year == year,
            BudgetPlan.month == source_plan.month,
            BudgetPlan.category_id == source_plan.category_id
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
                planned_amount=Decimal(str(round(new_amount, 2))),
                capex_planned=Decimal(str(round(new_capex, 2))),
                opex_planned=Decimal(str(round(new_opex, 2)))
            )
            db.add(new_plan)
            created_count += 1

    db.commit()

    return {
        "message": f"Copied budget plan from {source_year} to {year} with coefficient {request.coefficient}",
        "created_entries": created_count,
        "updated_entries": updated_count
    }


@router.patch("/plans/cell")
def update_budget_cell(request: CellUpdateRequest, db: Session = Depends(get_db)):
    """Update a single budget plan cell (upsert)"""
    # Check if category exists
    category = db.query(BudgetCategory).filter(BudgetCategory.id == request.category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {request.category_id} not found"
        )

    # Try to find existing plan
    existing = db.query(BudgetPlan).filter(
        BudgetPlan.year == request.year,
        BudgetPlan.month == request.month,
        BudgetPlan.category_id == request.category_id
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
                "planned_amount": float(existing.planned_amount)
            }
        }
    else:
        # Create new plan
        new_plan = BudgetPlan(
            year=request.year,
            month=request.month,
            category_id=request.category_id,
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
                "planned_amount": float(new_plan.planned_amount)
            }
        }
