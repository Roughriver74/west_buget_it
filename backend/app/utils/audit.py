"""
Audit logging utilities
"""
from typing import Optional, Dict, Any
from fastapi import Request
from sqlalchemy.orm import Session
from app.db.models import AuditLog, AuditActionEnum, User
from app.utils.logger import log_info


def create_audit_log(
    db: Session,
    action: AuditActionEnum,
    entity_type: str,
    entity_id: Optional[int] = None,
    description: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """
    Create an audit log entry

    Args:
        db: Database session
        action: Action performed (CREATE, UPDATE, DELETE, etc.)
        entity_type: Type of entity affected (e.g., "Expense", "User")
        entity_id: ID of the affected entity
        description: Human-readable description of the action
        changes: Detailed changes in JSON format
        user: User who performed the action
        request: FastAPI request object (for IP and user agent)

    Returns:
        Created AuditLog instance
    """
    # Extract user info
    user_id = user.id if user else None
    department_id = user.department_id if user else None

    # Extract request metadata
    ip_address = None
    user_agent = None

    if request:
        # Get client IP (considering proxies)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip_address = forwarded.split(",")[0].strip()
        elif request.headers.get("X-Real-IP"):
            ip_address = request.headers.get("X-Real-IP")
        elif request.client:
            ip_address = request.client.host

        # Get user agent
        user_agent = request.headers.get("User-Agent")

    # Create audit log
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        changes=changes,
        ip_address=ip_address,
        user_agent=user_agent,
        department_id=department_id,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    # Log to application logs as well
    log_info(
        f"Audit: {action.value} on {entity_type}#{entity_id} by User#{user_id} - {description}",
        "Audit"
    )

    return audit_log


def audit_create(
    db: Session,
    entity_type: str,
    entity_id: int,
    description: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
    changes: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Shortcut for CREATE action audit log"""
    return create_audit_log(
        db=db,
        action=AuditActionEnum.CREATE,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        changes=changes,
        user=user,
        request=request,
    )


def audit_update(
    db: Session,
    entity_type: str,
    entity_id: int,
    description: str,
    changes: Dict[str, Any],
    user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Shortcut for UPDATE action audit log"""
    return create_audit_log(
        db=db,
        action=AuditActionEnum.UPDATE,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        changes=changes,
        user=user,
        request=request,
    )


def audit_delete(
    db: Session,
    entity_type: str,
    entity_id: int,
    description: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Shortcut for DELETE action audit log"""
    return create_audit_log(
        db=db,
        action=AuditActionEnum.DELETE,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        user=user,
        request=request,
    )


def audit_login(
    db: Session,
    user: User,
    request: Optional[Request] = None,
) -> AuditLog:
    """Shortcut for LOGIN action audit log"""
    return create_audit_log(
        db=db,
        action=AuditActionEnum.LOGIN,
        entity_type="User",
        entity_id=user.id,
        description=f"User {user.username} logged in",
        user=user,
        request=request,
    )


def audit_export(
    db: Session,
    entity_type: str,
    description: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Shortcut for EXPORT action audit log"""
    return create_audit_log(
        db=db,
        action=AuditActionEnum.EXPORT,
        entity_type=entity_type,
        description=description,
        user=user,
        request=request,
    )


def audit_import(
    db: Session,
    entity_type: str,
    description: str,
    changes: Optional[Dict[str, Any]] = None,
    user: Optional[User] = None,
    request: Optional[Request] = None,
) -> AuditLog:
    """Shortcut for IMPORT action audit log"""
    return create_audit_log(
        db=db,
        action=AuditActionEnum.IMPORT,
        entity_type=entity_type,
        description=description,
        changes=changes,
        user=user,
        request=request,
    )
