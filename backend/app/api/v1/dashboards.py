from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import User, DashboardConfig
from app.schemas import (
    DashboardConfigCreate,
    DashboardConfigUpdate,
    DashboardConfigInDB,
    DashboardConfigList,
)
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("", response_model=DashboardConfigList)
def get_dashboards(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[str] = None,
    is_public: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all dashboard configurations"""
    query = db.query(DashboardConfig)

    # Filter by user_id or public dashboards
    if user_id is not None:
        query = query.filter(
            (DashboardConfig.user_id == user_id) | (DashboardConfig.is_public == True)
        )
    elif is_public is not None:
        query = query.filter(DashboardConfig.is_public == is_public)

    total = query.count()
    dashboards = query.offset(skip).limit(limit).all()

    return DashboardConfigList(items=dashboards, total=total)


@router.get("/{dashboard_id}", response_model=DashboardConfigInDB)
def get_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Get dashboard configuration by ID"""
    dashboard = db.query(DashboardConfig).filter(DashboardConfig.id == dashboard_id).first()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with id {dashboard_id} not found",
        )

    return dashboard


@router.get("/default/get", response_model=DashboardConfigInDB)
def get_default_dashboard(db: Session = Depends(get_db)):
    """Get default dashboard configuration"""
    dashboard = db.query(DashboardConfig).filter(DashboardConfig.is_default == True).first()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No default dashboard found",
        )

    return dashboard


@router.post("", response_model=DashboardConfigInDB, status_code=status.HTTP_201_CREATED)
def create_dashboard(
    dashboard_create: DashboardConfigCreate, db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new dashboard configuration"""

    # If this is set as default, unset any existing default
    if dashboard_create.is_default:
        db.query(DashboardConfig).filter(DashboardConfig.is_default == True).update(
            {"is_default": False}
        )

    dashboard = DashboardConfig(**dashboard_create.model_dump())
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)

    return dashboard


@router.patch("/{dashboard_id}", response_model=DashboardConfigInDB)
def update_dashboard(
    dashboard_id: int,
    dashboard_update: DashboardConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update dashboard configuration"""
    dashboard = db.query(DashboardConfig).filter(DashboardConfig.id == dashboard_id).first()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with id {dashboard_id} not found",
        )

    # If this is set as default, unset any existing default
    if dashboard_update.is_default:
        db.query(DashboardConfig).filter(
            DashboardConfig.id != dashboard_id, DashboardConfig.is_default == True
        ).update({"is_default": False})

    # Update fields
    update_data = dashboard_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dashboard, field, value)

    db.commit()
    db.refresh(dashboard)

    return dashboard


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Delete dashboard configuration"""
    dashboard = db.query(DashboardConfig).filter(DashboardConfig.id == dashboard_id).first()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with id {dashboard_id} not found",
        )

    # Prevent deletion of default dashboard
    if dashboard.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete default dashboard. Set another dashboard as default first.",
        )

    db.delete(dashboard)
    db.commit()

    return None


@router.post("/{dashboard_id}/set-default", response_model=DashboardConfigInDB)
def set_default_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Set a dashboard as default"""
    dashboard = db.query(DashboardConfig).filter(DashboardConfig.id == dashboard_id).first()

    if not dashboard:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with id {dashboard_id} not found",
        )

    # Unset any existing default
    db.query(DashboardConfig).filter(DashboardConfig.is_default == True).update(
        {"is_default": False}
    )

    # Set this as default
    dashboard.is_default = True
    db.commit()
    db.refresh(dashboard)

    return dashboard


@router.post("/{dashboard_id}/duplicate", response_model=DashboardConfigInDB)
def duplicate_dashboard(dashboard_id: int, db: Session = Depends(get_db)):
    """Duplicate an existing dashboard"""
    original = db.query(DashboardConfig).filter(DashboardConfig.id == dashboard_id).first()

    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dashboard with id {dashboard_id} not found",
        )

    # Create a copy
    duplicate = DashboardConfig(
        name=f"{original.name} (копия)",
        description=original.description,
        user_id=original.user_id,
        is_default=False,  # Duplicate is never default
        is_public=original.is_public,
        config=original.config,
    )

    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)

    return duplicate
