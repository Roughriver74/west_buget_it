"""
API endpoints for Business Operation Mappings (Маппинг хозяйственных операций)

Allows ADMIN/MANAGER to configure mappings between 1C business operations
and budget categories through UI.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import (
    User,
    UserRoleEnum,
    BusinessOperationMapping,
    BudgetCategory,
)
from app.api.v1.auth import get_current_active_user
from app.schemas.business_operation_mapping import (
    BusinessOperationMappingCreate,
    BusinessOperationMappingUpdate,
    BusinessOperationMappingInDB,
    BusinessOperationMappingList,
)
from app.services.business_operation_mapper import BusinessOperationMapper


router = APIRouter(prefix="/business-operation-mappings", tags=["business-operation-mappings"])


def check_admin_or_manager(current_user: User):
    """Check if user has ADMIN or MANAGER role"""
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN or MANAGER can manage business operation mappings"
        )


@router.get("/", response_model=BusinessOperationMappingList)
def get_mappings(
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    business_operation: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get list of business operation mappings

    Filters:
    - department_id: Filter by department
    - is_active: Filter by active status
    - business_operation: Filter by operation name (partial match)
    - skip, limit: Pagination
    """
    check_admin_or_manager(current_user)

    query = (
        db.query(BusinessOperationMapping)
        .outerjoin(BudgetCategory, BusinessOperationMapping.category_id == BudgetCategory.id)
    )

    # Apply filters
    if department_id:
        query = query.filter(BusinessOperationMapping.department_id == department_id)
    elif current_user.role == UserRoleEnum.MANAGER:
        # MANAGER can see all departments
        pass
    else:
        # Should not happen due to check_admin_or_manager
        query = query.filter(BusinessOperationMapping.department_id == current_user.department_id)

    if is_active is not None:
        query = query.filter(BusinessOperationMapping.is_active == is_active)

    if business_operation:
        query = query.filter(
            BusinessOperationMapping.business_operation.ilike(f"%{business_operation}%")
        )

    # Count total
    total = query.count()

    # Get items with pagination
    items = (
        query
        .order_by(
            BusinessOperationMapping.department_id,
            BusinessOperationMapping.priority.desc(),
            BusinessOperationMapping.business_operation
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Convert to response format
    items_data = []
    for item in items:
        items_data.append({
            'id': item.id,
            'business_operation': item.business_operation,
            'category_id': item.category_id,
            'category_name': item.category_rel.name if item.category_rel else None,
            'category_type': item.category_rel.type if item.category_rel else None,
            'priority': item.priority,
            'confidence': float(item.confidence),
            'notes': item.notes,
            'department_id': item.department_id,
            'department_name': item.department_rel.name if item.department_rel else None,
            'is_active': item.is_active,
            'created_at': item.created_at,
            'updated_at': item.updated_at,
        })

    return {
        'items': items_data,
        'total': total,
        'skip': skip,
        'limit': limit,
    }


@router.get("/{mapping_id}", response_model=BusinessOperationMappingInDB)
def get_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get single business operation mapping by ID"""
    check_admin_or_manager(current_user)

    mapping = db.query(BusinessOperationMapping).filter(BusinessOperationMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping with id={mapping_id} not found"
        )

    return {
        'id': mapping.id,
        'business_operation': mapping.business_operation,
        'category_id': mapping.category_id,
        'category_name': mapping.category_rel.name if mapping.category_rel else None,
        'category_type': mapping.category_rel.type if mapping.category_rel else None,
        'priority': mapping.priority,
        'confidence': float(mapping.confidence),
        'notes': mapping.notes,
        'department_id': mapping.department_id,
        'department_name': mapping.department_rel.name if mapping.department_rel else None,
        'is_active': mapping.is_active,
        'created_at': mapping.created_at,
        'updated_at': mapping.updated_at,
    }


@router.post("/", response_model=BusinessOperationMappingInDB, status_code=status.HTTP_201_CREATED)
def create_mapping(
    data: BusinessOperationMappingCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create new business operation mapping"""
    check_admin_or_manager(current_user)

    # Check if category exists
    category = db.query(BudgetCategory).filter(
        BudgetCategory.id == data.category_id,
        BudgetCategory.department_id == data.department_id,
        BudgetCategory.is_active == True
    ).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id={data.category_id} not found in department {data.department_id}"
        )

    # Check for duplicate
    existing = db.query(BusinessOperationMapping).filter(
        BusinessOperationMapping.business_operation == data.business_operation,
        BusinessOperationMapping.category_id == data.category_id,
        BusinessOperationMapping.department_id == data.department_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mapping for '{data.business_operation}' → category {data.category_id} already exists"
        )

    # Create mapping
    mapping = BusinessOperationMapping(
        business_operation=data.business_operation,
        category_id=data.category_id,
        priority=data.priority,
        confidence=data.confidence,
        notes=data.notes,
        department_id=data.department_id,
        created_by=current_user.id,
    )

    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    # Clear mapper cache
    mapper = BusinessOperationMapper(db)
    mapper.clear_cache()

    return {
        'id': mapping.id,
        'business_operation': mapping.business_operation,
        'category_id': mapping.category_id,
        'category_name': mapping.category_rel.name,
        'category_type': mapping.category_rel.type,
        'priority': mapping.priority,
        'confidence': float(mapping.confidence),
        'notes': mapping.notes,
        'department_id': mapping.department_id,
        'department_name': mapping.department_rel.name,
        'is_active': mapping.is_active,
        'created_at': mapping.created_at,
        'updated_at': mapping.updated_at,
    }


@router.put("/{mapping_id}", response_model=BusinessOperationMappingInDB)
def update_mapping(
    mapping_id: int,
    data: BusinessOperationMappingUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update business operation mapping"""
    check_admin_or_manager(current_user)

    mapping = db.query(BusinessOperationMapping).filter(BusinessOperationMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping with id={mapping_id} not found"
        )

    # Update fields
    if data.category_id is not None:
        # Check if category exists
        category = db.query(BudgetCategory).filter(
            BudgetCategory.id == data.category_id,
            BudgetCategory.department_id == mapping.department_id,
            BudgetCategory.is_active == True
        ).first()

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id={data.category_id} not found"
            )

        mapping.category_id = data.category_id

    if data.priority is not None:
        mapping.priority = data.priority

    if data.confidence is not None:
        mapping.confidence = data.confidence

    if data.notes is not None:
        mapping.notes = data.notes

    if data.is_active is not None:
        mapping.is_active = data.is_active

    db.commit()
    db.refresh(mapping)

    # Clear mapper cache
    mapper = BusinessOperationMapper(db)
    mapper.clear_cache()

    return {
        'id': mapping.id,
        'business_operation': mapping.business_operation,
        'category_id': mapping.category_id,
        'category_name': mapping.category_rel.name,
        'category_type': mapping.category_rel.type,
        'priority': mapping.priority,
        'confidence': float(mapping.confidence),
        'notes': mapping.notes,
        'department_id': mapping.department_id,
        'department_name': mapping.department_rel.name,
        'is_active': mapping.is_active,
        'created_at': mapping.created_at,
        'updated_at': mapping.updated_at,
    }


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mapping(
    mapping_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete business operation mapping"""
    check_admin_or_manager(current_user)

    mapping = db.query(BusinessOperationMapping).filter(BusinessOperationMapping.id == mapping_id).first()

    if not mapping:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mapping with id={mapping_id} not found"
        )

    db.delete(mapping)
    db.commit()

    # Clear mapper cache
    mapper = BusinessOperationMapper(db)
    mapper.clear_cache()

    return None


@router.post("/bulk-deactivate", status_code=status.HTTP_200_OK)
def bulk_deactivate(
    mapping_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Bulk deactivate mappings"""
    check_admin_or_manager(current_user)

    updated = (
        db.query(BusinessOperationMapping)
        .filter(BusinessOperationMapping.id.in_(mapping_ids))
        .update({BusinessOperationMapping.is_active: False}, synchronize_session=False)
    )

    db.commit()

    # Clear mapper cache
    mapper = BusinessOperationMapper(db)
    mapper.clear_cache()

    return {"updated": updated}


@router.post("/bulk-activate", status_code=status.HTTP_200_OK)
def bulk_activate(
    mapping_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Bulk activate mappings"""
    check_admin_or_manager(current_user)

    updated = (
        db.query(BusinessOperationMapping)
        .filter(BusinessOperationMapping.id.in_(mapping_ids))
        .update({BusinessOperationMapping.is_active: True}, synchronize_session=False)
    )

    db.commit()

    # Clear mapper cache
    mapper = BusinessOperationMapper(db)
    mapper.clear_cache()

    return {"updated": updated}


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete(
    mapping_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Bulk delete mappings"""
    check_admin_or_manager(current_user)

    deleted = (
        db.query(BusinessOperationMapping)
        .filter(BusinessOperationMapping.id.in_(mapping_ids))
        .delete(synchronize_session=False)
    )

    db.commit()

    # Clear mapper cache
    mapper = BusinessOperationMapper(db)
    mapper.clear_cache()

    return {"deleted": deleted}
