"""
API endpoints for Budget Scenarios
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from typing import List, Optional
from decimal import Decimal

from app.db.database import get_db
from app.db.models import BudgetScenario, BudgetScenarioItem, BudgetCategoryTypeEnum
from app.schemas.budget_scenario import (
    BudgetScenario as BudgetScenarioSchema,
    BudgetScenarioCreate,
    BudgetScenarioUpdate,
    BudgetScenarioWithItems,
    BudgetScenarioItem as BudgetScenarioItemSchema,
    BudgetScenarioItemCreate,
    BudgetScenarioItemUpdate,
    BudgetScenarioSummary,
    BudgetScenarioComparison,
    BudgetCategoryComparison,
    BudgetCategoryType,
)

router = APIRouter()


def calculate_item_amount(total_budget: Decimal, percentage: Decimal) -> Decimal:
    """Calculate item amount from percentage"""
    return (total_budget * percentage / 100).quantize(Decimal('0.01'))


# Budget Scenario Endpoints
@router.get("/", response_model=List[BudgetScenarioSchema])
def get_scenarios(
    year: Optional[int] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get list of budget scenarios with filtering"""
    query = db.query(BudgetScenario)

    if year is not None:
        query = query.filter(BudgetScenario.year == year)
    if is_active is not None:
        query = query.filter(BudgetScenario.is_active == is_active)

    scenarios = query.order_by(BudgetScenario.year.desc(), BudgetScenario.created_at.desc()).offset(skip).limit(limit).all()
    return scenarios


@router.get("/summary", response_model=List[BudgetScenarioSummary])
def get_scenarios_summary(
    year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get summary of all scenarios"""
    query = db.query(BudgetScenario).options(joinedload(BudgetScenario.items))

    if year is not None:
        query = query.filter(BudgetScenario.year == year)

    scenarios = query.all()
    summaries = []

    for scenario in scenarios:
        opex_total = sum(item.amount for item in scenario.items if item.category_type == BudgetCategoryTypeEnum.OPEX)
        capex_total = sum(item.amount for item in scenario.items if item.category_type == BudgetCategoryTypeEnum.CAPEX)

        summaries.append(BudgetScenarioSummary(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            year=scenario.year,
            total_budget=scenario.total_budget,
            opex_total=opex_total,
            opex_percentage=(opex_total / scenario.total_budget * 100) if scenario.total_budget > 0 else 0,
            capex_total=capex_total,
            capex_percentage=(capex_total / scenario.total_budget * 100) if scenario.total_budget > 0 else 0,
            items_count=len(scenario.items)
        ))

    return summaries


@router.get("/compare/{year}", response_model=BudgetScenarioComparison)
def compare_scenarios(
    year: int,
    db: Session = Depends(get_db)
):
    """Compare all scenarios for a specific year"""
    scenarios = db.query(BudgetScenario).options(joinedload(BudgetScenario.items)).filter(
        BudgetScenario.year == year
    ).all()

    if not scenarios:
        raise HTTPException(status_code=404, detail=f"Сценарии для {year} года не найдены")

    return BudgetScenarioComparison(year=year, scenarios=scenarios)


@router.get("/compare-category/{year}/{category_name}", response_model=BudgetCategoryComparison)
def compare_category(
    year: int,
    category_name: str,
    db: Session = Depends(get_db)
):
    """Compare a specific category across all scenarios for a year"""
    scenarios = db.query(BudgetScenario).options(joinedload(BudgetScenario.items)).filter(
        BudgetScenario.year == year
    ).all()

    if not scenarios:
        raise HTTPException(status_code=404, detail=f"Сценарии для {year} года не найдены")

    scenarios_data = {}
    category_type = None

    for scenario in scenarios:
        for item in scenario.items:
            if item.category_name == category_name:
                category_type = item.category_type
                scenarios_data[scenario.name] = {
                    "amount": item.amount,
                    "percentage": item.percentage,
                    "priority": item.priority.value,
                    "change_from_previous": item.change_from_previous
                }
                break

    if not scenarios_data:
        raise HTTPException(status_code=404, detail=f"Категория '{category_name}' не найдена в сценариях {year} года")

    return BudgetCategoryComparison(
        category_name=category_name,
        category_type=category_type,
        scenarios_data=scenarios_data
    )


@router.get("/{scenario_id}", response_model=BudgetScenarioWithItems)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Get budget scenario by ID with all items"""
    scenario = db.query(BudgetScenario).options(joinedload(BudgetScenario.items)).filter(
        BudgetScenario.id == scenario_id
    ).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")

    return scenario


@router.post("/", response_model=BudgetScenarioWithItems, status_code=201)
def create_scenario(scenario_data: BudgetScenarioCreate, db: Session = Depends(get_db)):
    """Create new budget scenario with items"""
    # Create scenario
    scenario = BudgetScenario(
        name=scenario_data.name,
        description=scenario_data.description,
        year=scenario_data.year,
        total_budget=scenario_data.total_budget,
        budget_change_percent=scenario_data.budget_change_percent,
        is_active=scenario_data.is_active,
        notes=scenario_data.notes
    )
    db.add(scenario)
    db.flush()  # Get scenario ID

    # Create items
    for item_data in scenario_data.items:
        amount = calculate_item_amount(scenario_data.total_budget, item_data.percentage)
        item = BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=item_data.category_type,
            category_name=item_data.category_name,
            percentage=item_data.percentage,
            amount=amount,
            priority=item_data.priority,
            change_from_previous=item_data.change_from_previous,
            notes=item_data.notes
        )
        db.add(item)

    db.commit()
    db.refresh(scenario)

    return scenario


@router.put("/{scenario_id}", response_model=BudgetScenarioWithItems)
def update_scenario(
    scenario_id: int,
    scenario_data: BudgetScenarioUpdate,
    db: Session = Depends(get_db)
):
    """Update budget scenario"""
    scenario = db.query(BudgetScenario).filter(BudgetScenario.id == scenario_id).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")

    # Update fields
    update_data = scenario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scenario, field, value)

    # If total_budget changed, recalculate all item amounts
    if scenario_data.total_budget is not None:
        for item in scenario.items:
            item.amount = calculate_item_amount(scenario.total_budget, item.percentage)

    db.commit()
    db.refresh(scenario)

    return scenario


@router.delete("/{scenario_id}", status_code=204)
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """Delete budget scenario"""
    scenario = db.query(BudgetScenario).filter(BudgetScenario.id == scenario_id).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")

    db.delete(scenario)
    db.commit()

    return None


# Budget Scenario Item Endpoints
@router.get("/{scenario_id}/items", response_model=List[BudgetScenarioItemSchema])
def get_scenario_items(
    scenario_id: int,
    category_type: Optional[BudgetCategoryType] = None,
    db: Session = Depends(get_db)
):
    """Get all items for a scenario"""
    # Check scenario exists
    scenario = db.query(BudgetScenario).filter(BudgetScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")

    query = db.query(BudgetScenarioItem).filter(BudgetScenarioItem.scenario_id == scenario_id)

    if category_type:
        query = query.filter(BudgetScenarioItem.category_type == category_type)

    items = query.order_by(BudgetScenarioItem.category_type, BudgetScenarioItem.category_name).all()
    return items


@router.post("/{scenario_id}/items", response_model=BudgetScenarioItemSchema, status_code=201)
def create_scenario_item(
    scenario_id: int,
    item_data: BudgetScenarioItemCreate,
    db: Session = Depends(get_db)
):
    """Add new item to scenario"""
    # Check scenario exists
    scenario = db.query(BudgetScenario).filter(BudgetScenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Сценарий не найден")

    # Check total percentage doesn't exceed 100%
    current_total = db.query(func.sum(BudgetScenarioItem.percentage)).filter(
        BudgetScenarioItem.scenario_id == scenario_id
    ).scalar() or 0

    if current_total + item_data.percentage > 100:
        raise HTTPException(
            status_code=400,
            detail=f"Превышен лимит: текущая сумма {current_total}% + новый {item_data.percentage}% = {current_total + item_data.percentage}% > 100%"
        )

    # Calculate amount
    amount = calculate_item_amount(scenario.total_budget, item_data.percentage)

    # Create item
    item = BudgetScenarioItem(
        scenario_id=scenario_id,
        category_type=item_data.category_type,
        category_name=item_data.category_name,
        percentage=item_data.percentage,
        amount=amount,
        priority=item_data.priority,
        change_from_previous=item_data.change_from_previous,
        notes=item_data.notes
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.put("/items/{item_id}", response_model=BudgetScenarioItemSchema)
def update_scenario_item(
    item_id: int,
    item_data: BudgetScenarioItemUpdate,
    db: Session = Depends(get_db)
):
    """Update scenario item"""
    item = db.query(BudgetScenarioItem).filter(BudgetScenarioItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Статья бюджета не найдена")

    # Get scenario for amount calculation
    scenario = db.query(BudgetScenario).filter(BudgetScenario.id == item.scenario_id).first()

    # Update fields
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    # Recalculate amount if percentage changed
    if item_data.percentage is not None:
        item.amount = calculate_item_amount(scenario.total_budget, item.percentage)

    db.commit()
    db.refresh(item)

    return item


@router.delete("/items/{item_id}", status_code=204)
def delete_scenario_item(item_id: int, db: Session = Depends(get_db)):
    """Delete scenario item"""
    item = db.query(BudgetScenarioItem).filter(BudgetScenarioItem.id == item_id).first()

    if not item:
        raise HTTPException(status_code=404, detail="Статья бюджета не найдена")

    db.delete(item)
    db.commit()

    return None
