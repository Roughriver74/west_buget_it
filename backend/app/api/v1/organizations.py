from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Organization
from app.schemas import OrganizationCreate, OrganizationUpdate, OrganizationInDB

router = APIRouter()


@router.get("/", response_model=List[OrganizationInDB])
def get_organizations(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Get all organizations"""
    query = db.query(Organization)

    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)

    organizations = query.offset(skip).limit(limit).all()
    return organizations


@router.get("/{organization_id}", response_model=OrganizationInDB)
def get_organization(organization_id: int, db: Session = Depends(get_db)):
    """Get organization by ID"""
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )
    return organization


@router.post("/", response_model=OrganizationInDB, status_code=status.HTTP_201_CREATED)
def create_organization(organization: OrganizationCreate, db: Session = Depends(get_db)):
    """Create new organization"""
    # Check if organization with same name exists
    existing = db.query(Organization).filter(Organization.name == organization.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with name '{organization.name}' already exists"
        )

    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.put("/{organization_id}", response_model=OrganizationInDB)
def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization"""
    db_organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # Update fields
    update_data = organization.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_organization, field, value)

    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(organization_id: int, db: Session = Depends(get_db)):
    """Delete organization (soft delete - mark as inactive)"""
    db_organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # Soft delete - mark as inactive
    db_organization.is_active = False
    db.commit()
    return None
