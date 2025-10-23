from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import BudgetCategory
from app.schemas import BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCategoryInDB

router = APIRouter()


@router.get("/", response_model=List[BudgetCategoryInDB])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Get all budget categories"""
    query = db.query(BudgetCategory)

    if is_active is not None:
        query = query.filter(BudgetCategory.is_active == is_active)

    categories = query.offset(skip).limit(limit).all()
    return categories


@router.get("/{category_id}", response_model=BudgetCategoryInDB)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    return category


@router.post("/", response_model=BudgetCategoryInDB, status_code=status.HTTP_201_CREATED)
def create_category(category: BudgetCategoryCreate, db: Session = Depends(get_db)):
    """Create new budget category"""
    # Check if category with same name exists
    existing = db.query(BudgetCategory).filter(BudgetCategory.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )

    db_category = BudgetCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=BudgetCategoryInDB)
def update_category(
    category_id: int,
    category: BudgetCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update budget category"""
    db_category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Update fields
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete budget category (soft delete - mark as inactive)"""
    db_category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Soft delete - mark as inactive
    db_category.is_active = False
    db.commit()
    return None
