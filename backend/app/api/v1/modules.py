"""
API endpoints for Module Management
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Organization, UserRoleEnum
from app.utils.auth import get_current_active_user
from app.services.module_service import ModuleService
from app.schemas.module import (
    ModuleInDB,
    ModuleCreate,
    ModuleUpdate,
    EnabledModulesResponse,
    ModuleEnableRequest,
    ModuleDisableRequest,
    OrganizationModuleInDB,
    ModuleEventInDB,
    ModuleStatistics,
    OrganizationModuleStatus,
)

router = APIRouter()


# ==================== Helper Functions ====================

def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Dependency to require ADMIN role"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ==================== Module CRUD ====================

@router.get("/", response_model=List[ModuleInDB])
def get_modules(
    active_only: bool = True,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get list of all available modules.

    **Access**: All authenticated users

    **Query Parameters**:
    - `active_only`: Filter only active modules (default: True)

    **Returns**: List of modules
    """
    module_service = ModuleService(db)
    modules = module_service.get_all_modules(active_only=active_only)
    return modules


@router.get("/{module_id}", response_model=ModuleInDB)
def get_module(
    module_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get details of a specific module.

    **Access**: All authenticated users

    **Returns**: Module details
    """
    from app.db.models import Module

    module = db.query(Module).filter_by(id=module_id).first()

    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID {module_id} not found",
        )

    return module


@router.post("/", response_model=ModuleInDB, status_code=status.HTTP_201_CREATED)
def create_module(
    module_data: ModuleCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a new module.

    **Access**: ADMIN only

    **Body**: ModuleCreate schema

    **Returns**: Created module
    """
    from app.db.models import Module

    # Check if module code already exists
    existing = db.query(Module).filter_by(code=module_data.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Module with code '{module_data.code}' already exists",
        )

    # Create module
    module = Module(**module_data.model_dump())
    db.add(module)
    db.commit()
    db.refresh(module)

    return module


@router.put("/{module_id}", response_model=ModuleInDB)
def update_module(
    module_id: int,
    module_data: ModuleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Update an existing module.

    **Access**: ADMIN only

    **Body**: ModuleUpdate schema

    **Returns**: Updated module
    """
    from app.db.models import Module

    module = db.query(Module).filter_by(id=module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID {module_id} not found",
        )

    # Update fields
    update_data = module_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(module, field, value)

    db.commit()
    db.refresh(module)

    return module


@router.delete("/{module_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_module(
    module_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Delete a module (soft delete - sets is_active=False).

    **Access**: ADMIN only

    **Returns**: 204 No Content
    """
    from app.db.models import Module

    module = db.query(Module).filter_by(id=module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module with ID {module_id} not found",
        )

    # Soft delete
    module.is_active = False
    db.commit()


# ==================== User's Enabled Modules ====================

@router.get("/enabled/my", response_model=EnabledModulesResponse)
def get_my_enabled_modules(
    include_expired: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get list of modules enabled for current user's organization.

    **Access**: All authenticated users

    **Query Parameters**:
    - `include_expired`: Include expired modules (default: False)

    **Returns**: EnabledModulesResponse with list of enabled modules
    """
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not belong to an organization",
        )

    module_service = ModuleService(db)

    # Get enabled modules
    modules = module_service.get_enabled_modules(
        organization_id=current_user.organization_id,
        include_expired=include_expired,
    )

    # Get organization details
    organization = db.query(Organization).filter_by(id=current_user.organization_id).first()

    return EnabledModulesResponse(
        modules=modules,
        organization_id=current_user.organization_id,
        organization_name=organization.short_name if organization else "Unknown",
    )


@router.get("/enabled/{organization_id}", response_model=EnabledModulesResponse)
def get_organization_enabled_modules(
    organization_id: int,
    include_expired: bool = False,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get list of modules enabled for a specific organization.

    **Access**: ADMIN only

    **Query Parameters**:
    - `include_expired`: Include expired modules (default: False)

    **Returns**: EnabledModulesResponse with list of enabled modules
    """
    module_service = ModuleService(db)

    # Get enabled modules
    modules = module_service.get_enabled_modules(
        organization_id=organization_id,
        include_expired=include_expired,
    )

    # Get organization details
    organization = db.query(Organization).filter_by(id=organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found",
        )

    return EnabledModulesResponse(
        modules=modules,
        organization_id=organization_id,
        organization_name=organization.short_name,
    )


# ==================== Enable/Disable Modules ====================

@router.post("/enable", response_model=OrganizationModuleInDB, status_code=status.HTTP_201_CREATED)
def enable_module_for_organization(
    request_data: ModuleEnableRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Enable a module for an organization.

    **Access**: ADMIN only

    **Body**: ModuleEnableRequest schema

    **Returns**: Created/updated OrganizationModule
    """
    module_service = ModuleService(db)

    try:
        org_module = module_service.enable_module_for_organization(
            organization_id=request_data.organization_id,
            module_code=request_data.module_code,
            expires_at=request_data.expires_at,
            limits=request_data.limits,
            enabled_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return org_module


@router.post("/disable", status_code=status.HTTP_204_NO_CONTENT)
def disable_module_for_organization(
    request_data: ModuleDisableRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Disable a module for an organization.

    **Access**: ADMIN only

    **Body**: ModuleDisableRequest schema

    **Returns**: 204 No Content
    """
    module_service = ModuleService(db)

    try:
        module_service.disable_module_for_organization(
            organization_id=request_data.organization_id,
            module_code=request_data.module_code,
            disabled_by_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== Module Events (Audit Log) ====================

@router.get("/events/", response_model=List[ModuleEventInDB])
def get_module_events(
    organization_id: Optional[int] = None,
    module_code: Optional[str] = None,
    event_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get module events for auditing.

    **Access**: ADMIN only

    **Query Parameters**:
    - `organization_id`: Filter by organization
    - `module_code`: Filter by module code
    - `event_type`: Filter by event type
    - `skip`: Offset for pagination
    - `limit`: Limit results (max 500)

    **Returns**: List of module events
    """
    from app.db.models import ModuleEvent, Module

    query = db.query(ModuleEvent)

    # Apply filters
    if organization_id:
        query = query.filter(ModuleEvent.organization_id == organization_id)

    if module_code:
        module = db.query(Module).filter_by(code=module_code).first()
        if module:
            query = query.filter(ModuleEvent.module_id == module.id)

    if event_type:
        query = query.filter(ModuleEvent.event_type == event_type)

    # Order by created_at desc
    query = query.order_by(ModuleEvent.created_at.desc())

    # Pagination
    limit = min(limit, 500)
    events = query.offset(skip).limit(limit).all()

    return events


# ==================== Statistics & Analytics ====================

@router.get("/statistics/", response_model=List[ModuleStatistics])
def get_module_statistics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get statistics for all modules.

    **Access**: ADMIN only

    **Returns**: List of module statistics
    """
    from app.db.models import Module, OrganizationModule, ModuleEvent
    from sqlalchemy import func
    from datetime import datetime

    modules = db.query(Module).filter_by(is_active=True).all()

    stats = []
    for module in modules:
        # Count organizations
        total_orgs = db.query(OrganizationModule).filter_by(module_id=module.id).count()

        active_orgs = (
            db.query(OrganizationModule)
            .filter(
                OrganizationModule.module_id == module.id,
                OrganizationModule.is_active == True,
                (
                    OrganizationModule.expires_at.is_(None)
                    | (OrganizationModule.expires_at > datetime.utcnow())
                ),
            )
            .count()
        )

        expired_orgs = (
            db.query(OrganizationModule)
            .filter(
                OrganizationModule.module_id == module.id,
                OrganizationModule.is_active == True,
                OrganizationModule.expires_at <= datetime.utcnow(),
            )
            .count()
        )

        # Count events
        total_events = db.query(ModuleEvent).filter_by(module_id=module.id).count()

        stats.append(
            ModuleStatistics(
                module_code=module.code,
                module_name=module.name,
                total_organizations=total_orgs,
                active_organizations=active_orgs,
                expired_organizations=expired_orgs,
                total_events=total_events,
            )
        )

    return stats


@router.get("/status/{organization_id}", response_model=OrganizationModuleStatus)
def get_organization_module_status(
    organization_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get module status summary for an organization.

    **Access**: ADMIN only

    **Returns**: OrganizationModuleStatus with summary
    """
    from app.db.models import OrganizationModule
    from datetime import datetime

    # Get organization
    organization = db.query(Organization).filter_by(id=organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with ID {organization_id} not found",
        )

    # Get module service
    module_service = ModuleService(db)

    # Get all modules for org
    all_modules = module_service.get_enabled_modules(
        organization_id=organization_id, include_expired=True
    )

    # Count totals
    total_modules = len(all_modules)
    enabled_modules = sum(1 for m in all_modules if not m["is_expired"])
    expired_modules = sum(1 for m in all_modules if m["is_expired"])

    return OrganizationModuleStatus(
        organization_id=organization_id,
        organization_name=organization.short_name,
        total_modules=total_modules,
        enabled_modules=enabled_modules,
        expired_modules=expired_modules,
        modules=all_modules,
    )
