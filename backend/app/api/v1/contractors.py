from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Contractor
from app.schemas import ContractorCreate, ContractorUpdate, ContractorInDB

router = APIRouter()


@router.get("/", response_model=List[ContractorInDB])
def get_contractors(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Get all contractors"""
    query = db.query(Contractor)

    if is_active is not None:
        query = query.filter(Contractor.is_active == is_active)

    if search:
        query = query.filter(
            (Contractor.name.ilike(f"%{search}%")) |
            (Contractor.short_name.ilike(f"%{search}%")) |
            (Contractor.inn.ilike(f"%{search}%"))
        )

    contractors = query.offset(skip).limit(limit).all()
    return contractors


@router.get("/{contractor_id}", response_model=ContractorInDB)
def get_contractor(contractor_id: int, db: Session = Depends(get_db)):
    """Get contractor by ID"""
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )
    return contractor


@router.post("/", response_model=ContractorInDB, status_code=status.HTTP_201_CREATED)
def create_contractor(contractor: ContractorCreate, db: Session = Depends(get_db)):
    """Create new contractor"""
    # Check if contractor with same INN exists
    if contractor.inn:
        existing = db.query(Contractor).filter(Contractor.inn == contractor.inn).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contractor with INN '{contractor.inn}' already exists"
            )

    db_contractor = Contractor(**contractor.model_dump())
    db.add(db_contractor)
    db.commit()
    db.refresh(db_contractor)
    return db_contractor


@router.put("/{contractor_id}", response_model=ContractorInDB)
def update_contractor(
    contractor_id: int,
    contractor: ContractorUpdate,
    db: Session = Depends(get_db)
):
    """Update contractor"""
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not db_contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # Update fields
    update_data = contractor.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contractor, field, value)

    db.commit()
    db.refresh(db_contractor)
    return db_contractor


@router.delete("/{contractor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contractor(contractor_id: int, db: Session = Depends(get_db)):
    """Delete contractor (soft delete - mark as inactive)"""
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not db_contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # Soft delete - mark as inactive
    db_contractor.is_active = False
    db.commit()
    return None
