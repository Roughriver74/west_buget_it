from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel

from app.db import get_db
from app.db.models import RevenueStream, User, UserRoleEnum, RevenueStreamTypeEnum
from app.schemas import (
    RevenueStreamCreate,
    RevenueStreamUpdate,
    RevenueStreamInDB,
    RevenueStreamTree,
)
from app.services.cache import cache_service
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "revenue_streams"


class BulkUpdateRequest(BaseModel):
    """Request for bulk update operations"""
    ids: List[int]
    is_active: Optional[bool] = None


class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operations"""
    ids: List[int]


def check_department_access(db: Session, stream_id: int, user: User) -> RevenueStream:
    """
    Check if user has access to revenue stream based on department.
    Raises 404 if stream not found or user lacks access.
    """
    stream = db.query(RevenueStream).filter(RevenueStream.id == stream_id).first()

    if not stream:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Revenue stream with id {stream_id} not found"
        )

    # USER role can only access their own department
    if user.role == UserRoleEnum.USER:
        if stream.department_id != user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Revenue stream with id {stream_id} not found"
            )

    return stream


@router.get("/", response_model=List[RevenueStreamInDB])
def get_revenue_streams(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    stream_type: Optional[RevenueStreamTypeEnum] = None,
    parent_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all revenue streams with filtering

    - **USER**: Can only see streams from their own department
    - **MANAGER**: Can see streams from all departments
    - **ADMIN**: Can see streams from all departments
    """
    query = db.query(RevenueStream)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(RevenueStream.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(RevenueStream.department_id == department_id)

    if is_active is not None:
        query = query.filter(RevenueStream.is_active == is_active)

    if stream_type is not None:
        query = query.filter(RevenueStream.stream_type == stream_type)

    if parent_id is not None:
        query = query.filter(RevenueStream.parent_id == parent_id)

    # Cache key
    cached_key = cache_service.build_key(
        "list",
        current_user.role,
        current_user.department_id,
        department_id,
        is_active,
        stream_type,
        parent_id,
        skip,
        limit,
    )

    cached_payload = cache_service.get(CACHE_NAMESPACE, cached_key)
    if cached_payload is not None:
        return [RevenueStreamInDB.model_validate(item) for item in cached_payload]

    streams = query.order_by(RevenueStream.name).offset(skip).limit(limit).all()

    # Cache the result
    cache_service.set(
        CACHE_NAMESPACE,
        cached_key,
        [RevenueStreamInDB.model_validate(stream) for stream in streams],
    )

    log_info(f"Retrieved {len(streams)} revenue streams", context=f"User {current_user.id}")
    return streams


@router.get("/tree", response_model=List[RevenueStreamTree])
def get_revenue_streams_tree(
    stream_type: Optional[RevenueStreamTypeEnum] = None,
    is_active: Optional[bool] = True,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get revenue streams in tree structure (hierarchical)

    Returns only root-level streams with their children populated.
    """
    query = db.query(RevenueStream).filter(RevenueStream.parent_id.is_(None))

    # Department filtering
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(RevenueStream.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        if department_id is not None:
            query = query.filter(RevenueStream.department_id == department_id)

    if is_active is not None:
        query = query.filter(RevenueStream.is_active == is_active)

    if stream_type is not None:
        query = query.filter(RevenueStream.stream_type == stream_type)

    root_streams = query.order_by(RevenueStream.name).all()

    def build_tree(stream: RevenueStream) -> RevenueStreamTree:
        """Recursively build tree structure"""
        children = db.query(RevenueStream).filter(
            RevenueStream.parent_id == stream.id
        ).order_by(RevenueStream.name).all()

        return RevenueStreamTree(
            **RevenueStreamInDB.model_validate(stream).model_dump(),
            children=[build_tree(child) for child in children]
        )

    tree = [build_tree(stream) for stream in root_streams]
    log_info(f"Retrieved revenue streams tree with {len(tree)} root nodes", context=f"User {current_user.id}")
    return tree


@router.get("/{stream_id}", response_model=RevenueStreamInDB)
def get_revenue_stream(
    stream_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific revenue stream by ID"""
    stream = check_department_access(db, stream_id, current_user)

    log_info(f"Retrieved revenue stream {stream_id}", context=f"User {current_user.id}")
    return RevenueStreamInDB.model_validate(stream)


@router.post("/", response_model=RevenueStreamInDB, status_code=status.HTTP_201_CREATED)
def create_revenue_stream(
    stream: RevenueStreamCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new revenue stream

    - Department ID is automatically assigned from current user if not provided
    - Only ADMIN and MANAGER can create streams for other departments
    """
    # Validate department assignment
    if stream.department_id:
        if current_user.role == UserRoleEnum.USER:
            if stream.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You can only create streams for your own department"
                )
    else:
        # Auto-assign department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User has no assigned department"
            )
        stream.department_id = current_user.department_id

    # Check for duplicate code
    if stream.code:
        existing = db.query(RevenueStream).filter(
            RevenueStream.code == stream.code,
            RevenueStream.department_id == stream.department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Revenue stream with code '{stream.code}' already exists"
            )

    # Validate parent exists and belongs to same department
    if stream.parent_id:
        parent = db.query(RevenueStream).filter(RevenueStream.id == stream.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent stream with id {stream.parent_id} not found"
            )
        if parent.department_id != stream.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent stream must belong to the same department"
            )

    db_stream = RevenueStream(**stream.model_dump())
    db.add(db_stream)
    db.commit()
    db.refresh(db_stream)

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Created revenue stream {db_stream.id}: {db_stream.name}", context=f"User {current_user.id}")
    return RevenueStreamInDB.model_validate(db_stream)


@router.put("/{stream_id}", response_model=RevenueStreamInDB)
def update_revenue_stream(
    stream_id: int,
    stream_update: RevenueStreamUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an existing revenue stream"""
    db_stream = check_department_access(db, stream_id, current_user)

    # Check for duplicate code if updating
    if stream_update.code is not None:
        existing = db.query(RevenueStream).filter(
            RevenueStream.code == stream_update.code,
            RevenueStream.department_id == db_stream.department_id,
            RevenueStream.id != stream_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Revenue stream with code '{stream_update.code}' already exists"
            )

    # Validate parent if updating
    if stream_update.parent_id is not None:
        if stream_update.parent_id == stream_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stream cannot be its own parent"
            )
        parent = db.query(RevenueStream).filter(RevenueStream.id == stream_update.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent stream with id {stream_update.parent_id} not found"
            )

    # Update fields
    update_data = stream_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_stream, field, value)

    db.commit()
    db.refresh(db_stream)

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Updated revenue stream {stream_id}", context=f"User {current_user.id}")
    return RevenueStreamInDB.model_validate(db_stream)


@router.delete("/{stream_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_revenue_stream(
    stream_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a revenue stream (soft delete by setting is_active=False)

    Also deactivates all child streams.
    """
    db_stream = check_department_access(db, stream_id, current_user)

    # Soft delete
    db_stream.is_active = False

    # Also deactivate children
    def deactivate_children(parent_id: int):
        children = db.query(RevenueStream).filter(RevenueStream.parent_id == parent_id).all()
        for child in children:
            child.is_active = False
            deactivate_children(child.id)

    deactivate_children(stream_id)

    db.commit()

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Deleted revenue stream {stream_id}", context=f"User {current_user.id}")
    return None


@router.post("/bulk/update", response_model=List[RevenueStreamInDB])
def bulk_update_revenue_streams(
    bulk_request: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk update revenue streams (e.g., activate/deactivate multiple)"""

    # Get streams and validate access
    streams = db.query(RevenueStream).filter(RevenueStream.id.in_(bulk_request.ids)).all()

    if not streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No revenue streams found with provided IDs"
        )

    # Check department access for all streams
    for stream in streams:
        if current_user.role == UserRoleEnum.USER:
            if stream.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No access to revenue stream {stream.id}"
                )

    # Apply updates
    if bulk_request.is_active is not None:
        for stream in streams:
            stream.is_active = bulk_request.is_active

    db.commit()
    for stream in streams:
        db.refresh(stream)

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Bulk updated {len(streams)} revenue streams", context=f"User {current_user.id}")
    return [RevenueStreamInDB.model_validate(stream) for stream in streams]


@router.delete("/bulk/delete", status_code=status.HTTP_204_NO_CONTENT)
def bulk_delete_revenue_streams(
    bulk_request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk delete revenue streams (soft delete)"""

    streams = db.query(RevenueStream).filter(RevenueStream.id.in_(bulk_request.ids)).all()

    if not streams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No revenue streams found with provided IDs"
        )

    # Check department access
    for stream in streams:
        if current_user.role == UserRoleEnum.USER:
            if stream.department_id != current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"No access to revenue stream {stream.id}"
                )

    # Soft delete
    for stream in streams:
        stream.is_active = False

    db.commit()

    # Invalidate cache
    cache_service.clear_namespace(CACHE_NAMESPACE)

    log_info(f"Bulk deleted {len(streams)} revenue streams", context=f"User {current_user.id}")
    return None
