from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from decimal import Decimal

from app.db import get_db
from app.db.models import RevenueCategory, User, UserRoleEnum, RevenueCategoryTypeEnum
from app.schemas import (
    RevenueCategoryCreate,
    RevenueCategoryUpdate,
    RevenueCategoryInDB,
    RevenueCategoryTree,
)
from app.services.cache import cache_service
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "revenue_categories"


class BulkUpdateRequest(BaseModel):
    """Request for bulk update operations"""
    ids: List[int]
    is_active: Optional[bool] = None
    default_margin: Optional[Decimal] = None


class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operations"""
    ids: List[int]


def check_department_access(db: Session, category_id: int, user: User) -> RevenueCategory:
    """
    Check if user has access to revenue category based on department.
    Raises 404 if category not found or user lacks access.
    """
    category = db.query(RevenueCategory).filter(RevenueCategory.id == category_id).first()

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue category with id {category_id} not found"
        )

    # USER role can only access their own department
    if user.role == UserRoleEnum.USER:
        if category.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Revenue category with id {category_id} not found"
            )

    return category


@router.get("/", response_model=List[RevenueCategoryInDB])
def get_revenue_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    category_type: Optional[RevenueCategoryTypeEnum] = None,
    parent_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all revenue categories with filtering

    - **USER**: Can only see categories from their own department
    - **MANAGER**: Can see categories from all departments
    - **ADMIN**: Can see categories from all departments
    """
    query = db.query(RevenueCategory)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(RevenueCategory.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id is not None:
            query = query.filter(RevenueCategory.department_id == department_id)

    if is_active is not None:
        query = query.filter(RevenueCategory.is_active == is_active)

    if category_type is not None:
        query = query.filter(RevenueCategory.category_type == category_type)

    if parent_id is not None:
        query = query.filter(RevenueCategory.parent_id == parent_id)

    # Cache key
    cached_key = cache_service.build_key(
        "list",
        current_user.role,
        current_user.department_id,
        department_id,
        is_active,
        category_type,
        parent_id,
        skip,
        limit,
    )

    cached_payload = cache_service.get(CACHE_NAMESPACE, cached_key)
    if cached_payload is not None:
        return [RevenueCategoryInDB.model_validate(item) for item in cached_payload]

    categories = query.order_by(RevenueCategory.name).offset(skip).limit(limit).all()

    # Cache the result
    cache_service.set(
        CACHE_NAMESPACE,
        cached_key,
        [RevenueCategoryInDB.model_validate(cat) for cat in categories],
    )

    log_info(f"Retrieved {len(categories)} revenue categories", user_id=current_user.id)
    return categories


@router.get("/tree", response_model=List[RevenueCategoryTree])
def get_revenue_categories_tree(
    category_type: Optional[RevenueCategoryTypeEnum] = None,
    is_active: Optional[bool] = True,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get revenue categories in tree structure (hierarchical)

    Returns only root-level categories with their subcategories populated.
    """
    query = db.query(RevenueCategory).filter(RevenueCategory.parent_id.is_(None))

    # Department filtering
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(RevenueCategory.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id is not None:
            query = query.filter(RevenueCategory.department_id == department_id)

    if is_active is not None:
        query = query.filter(RevenueCategory.is_active == is_active)

    if category_type is not None:
        query = query.filter(RevenueCategory.category_type == category_type)

    root_categories = query.order_by(RevenueCategory.name).all()

    def build_tree(category: RevenueCategory) -> RevenueCategoryTree:
        """Recursively build tree structure"""
        children = db.query(RevenueCategory).filter(
            RevenueCategory.parent_id == category.id
        ).order_by(RevenueCategory.name).all()

        return RevenueCategoryTree(
            **RevenueCategoryInDB.model_validate(category).model_dump(),
            subcategories=[build_tree(child) for child in children]
        )

    tree = [build_tree(cat) for cat in root_categories]
    log_info(f"Retrieved revenue categories tree with {len(tree)} root nodes", user_id=current_user.id)
    return tree


@router.get("/{category_id}", response_model=RevenueCategoryInDB)
def get_revenue_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific revenue category by ID"""
    category = check_department_access(db, category_id, current_user)

    log_info(f"Retrieved revenue category {category_id}", user_id=current_user.id)
    return RevenueCategoryInDB.model_validate(category)


@router.post("/", response_model=RevenueCategoryInDB, status_code=status.HTTP_201_CREATED)
def create_revenue_category(
    category: RevenueCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new revenue category

    - Department ID is automatically assigned from current user if not provided
    - Only ADMIN and MANAGER can create categories for other departments
    """
    # Validate department assignment
    if category.department_id:
        if current_user.role == UserRoleEnum.USER:
            if category.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create categories for your own department"
                )
    else:
        # Auto-assign department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no assigned department"
            )
        category.department_id = current_user.department_id

    # Check for duplicate code
    if category.code:
        existing = db.query(RevenueCategory).filter(
            RevenueCategory.code == category.code
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Revenue category with code '{category.code}' already exists"
            )

    # Validate parent exists and belongs to same department
    if category.parent_id:
        parent = db.query(RevenueCategory).filter(RevenueCategory.id == category.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id {category.parent_id} not found"
            )
        if parent.department_id != category.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category must belong to the same department"
            )

    db_category = RevenueCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Created revenue category {db_category.id}: {db_category.name}", user_id=current_user.id)
    return RevenueCategoryInDB.model_validate(db_category)


@router.put("/{category_id}", response_model=RevenueCategoryInDB)
def update_revenue_category(
    category_id: int,
    category_update: RevenueCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing revenue category"""
    db_category = check_department_access(db, category_id, current_user)

    # Check for duplicate code if updating
    if category_update.code is not None:
        existing = db.query(RevenueCategory).filter(
            RevenueCategory.code == category_update.code,
            RevenueCategory.id != category_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Revenue category with code '{category_update.code}' already exists"
            )

    # Validate parent if updating
    if category_update.parent_id is not None:
        if category_update.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        parent = db.query(RevenueCategory).filter(RevenueCategory.id == category_update.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id {category_update.parent_id} not found"
            )

    # Update fields
    update_data = category_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Updated revenue category {category_id}", user_id=current_user.id)
    return RevenueCategoryInDB.model_validate(db_category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revenue_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a revenue category (soft delete by setting is_active=False)

    Also deactivates all subcategories.
    """
    db_category = check_department_access(db, category_id, current_user)

    # Soft delete
    db_category.is_active = False

    # Also deactivate children
    def deactivate_children(parent_id: int):
        children = db.query(RevenueCategory).filter(RevenueCategory.parent_id == parent_id).all()
        for child in children:
            child.is_active = False
            deactivate_children(child.id)

    deactivate_children(category_id)

    db.commit()

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Deleted revenue category {category_id}", user_id=current_user.id)
    return None


@router.post("/bulk/update", response_model=List[RevenueCategoryInDB])
def bulk_update_revenue_categories(
    bulk_request: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk update revenue categories (e.g., activate/deactivate multiple, set default margin)"""

    # Get categories and validate access
    categories = db.query(RevenueCategory).filter(RevenueCategory.id.in_(bulk_request.ids)).all()

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No revenue categories found with provided IDs"
        )

    # Check department access for all categories
    for category in categories:
        if current_user.role == UserRoleEnum.USER:
            if category.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No access to revenue category {category.id}"
                )

    # Apply updates
    if bulk_request.is_active is not None:
        for category in categories:
            category.is_active = bulk_request.is_active

    if bulk_request.default_margin is not None:
        for category in categories:
            category.default_margin = bulk_request.default_margin

    db.commit()
    for category in categories:
        db.refresh(category)

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Bulk updated {len(categories)} revenue categories", user_id=current_user.id)
    return [RevenueCategoryInDB.model_validate(cat) for cat in categories]


@router.delete("/bulk/delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_revenue_categories(
    bulk_request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk delete revenue categories (soft delete)"""

    categories = db.query(RevenueCategory).filter(RevenueCategory.id.in_(bulk_request.ids)).all()

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No revenue categories found with provided IDs"
        )

    # Check department access
    for category in categories:
        if current_user.role == UserRoleEnum.USER:
            if category.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No access to revenue category {category.id}"
                )

    # Soft delete
    for category in categories:
        category.is_active = False

    db.commit()

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Bulk deleted {len(categories)} revenue categories", user_id=current_user.id)
    return None
