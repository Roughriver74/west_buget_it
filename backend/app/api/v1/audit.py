"""
Audit Log API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.db import get_db
from app.db.models import AuditLog, User, UserRoleEnum, AuditActionEnum
from app.schemas import AuditLogInDB, AuditLogWithUser
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


@router.get("/", response_model=List[AuditLogWithUser])
def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    action: Optional[AuditActionEnum] = None,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    user_id: Optional[int] = None,
    department_id: Optional[int] = Query(None, description="Filter by department"),
    search: Optional[str] = Query(None, description="Search in description"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get audit logs

    - **ADMIN**: Can view all audit logs
    - **MANAGER**: Can view audit logs for all departments
    - **USER**: Can only view audit logs for their department
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view audit logs"
        )

    query = db.query(AuditLog)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department's audit logs
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(AuditLog.department_id == current_user.department_id)
    elif current_user.role == UserRoleEnum.MANAGER:
        # MANAGER can filter by department or see all
        if department_id is not None:
            query = query.filter(AuditLog.department_id == department_id)

    # Apply filters
    if action:
        query = query.filter(AuditLog.action == action)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if search:
        query = query.filter(AuditLog.description.ilike(f"%{search}%"))

    # Order by timestamp descending (most recent first)
    query = query.order_by(desc(AuditLog.timestamp))

    # Pagination
    audit_logs = query.offset(skip).limit(limit).all()

    # Enrich with user information
    result = []
    for log in audit_logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "changes": log.changes,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "department_id": log.department_id,
            "timestamp": log.timestamp,
            "username": log.user.username if log.user else None,
            "user_full_name": log.user.full_name if log.user else None,
        }
        result.append(log_dict)

    return result


@router.get("/{audit_log_id}", response_model=AuditLogWithUser)
def get_audit_log(
    audit_log_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get audit log by ID"""
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view audit logs"
        )

    audit_log = db.query(AuditLog).filter(AuditLog.id == audit_log_id).first()
    if not audit_log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with id {audit_log_id} not found"
        )

    # Department check for non-ADMIN users
    if current_user.role == UserRoleEnum.USER:
        if audit_log.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this audit log"
            )

    # Enrich with user information
    return {
        "id": audit_log.id,
        "user_id": audit_log.user_id,
        "action": audit_log.action,
        "entity_type": audit_log.entity_type,
        "entity_id": audit_log.entity_id,
        "description": audit_log.description,
        "changes": audit_log.changes,
        "ip_address": audit_log.ip_address,
        "user_agent": audit_log.user_agent,
        "department_id": audit_log.department_id,
        "timestamp": audit_log.timestamp,
        "username": audit_log.user.username if audit_log.user else None,
        "user_full_name": audit_log.user.full_name if audit_log.user else None,
    }


@router.get("/entity/{entity_type}/{entity_id}", response_model=List[AuditLogWithUser])
def get_entity_audit_logs(
    entity_type: str,
    entity_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all audit logs for a specific entity

    Useful for viewing history of changes to a particular record
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to view audit logs"
        )

    query = db.query(AuditLog).filter(
        AuditLog.entity_type == entity_type,
        AuditLog.entity_id == entity_id
    )

    # Department filtering for USER role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(AuditLog.department_id == current_user.department_id)

    # Order by timestamp descending
    audit_logs = query.order_by(desc(AuditLog.timestamp)).all()

    # Enrich with user information
    result = []
    for log in audit_logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "changes": log.changes,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "department_id": log.department_id,
            "timestamp": log.timestamp,
            "username": log.user.username if log.user else None,
            "user_full_name": log.user.full_name if log.user else None,
        }
        result.append(log_dict)

    return result
