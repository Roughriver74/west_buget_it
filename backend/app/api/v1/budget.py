from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.db.models import BudgetPlan, BudgetCategory, Expense, ExpenseTypeEnum
from app.schemas import BudgetPlanCreate, BudgetPlanUpdate, BudgetPlanInDB

router = APIRouter()


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
