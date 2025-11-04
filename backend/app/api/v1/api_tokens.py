"""
API endpoints for API Token Management

Allows admins to create, manage, and revoke API tokens for external integrations.
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import (
    APIToken,
    User,
    UserRoleEnum,
    APITokenStatusEnum,
    APITokenScopeEnum,
)
from app.schemas import (
    APITokenCreate,
    APITokenUpdate,
    APITokenInDB,
    APITokenWithKey,
    APITokenRevoke,
)
from app.utils.auth import get_current_active_user
from app.utils.api_token import generate_token_key
from app.utils.logger import log_info, log_warning

router = APIRouter()


def check_admin_access(current_user: User):
    """Only admins can manage API tokens"""
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can manage API tokens"
        )


@router.get("/", response_model=List[APITokenInDB])
def get_api_tokens(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[APITokenStatusEnum] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all API tokens (Admin only)

    Tokens are returned without token_key for security
    """
    check_admin_access(current_user)

    query = db.query(APIToken)

    if status_filter:
        query = query.filter(APIToken.status == status_filter)

    if department_id is not None:
        query = query.filter(APIToken.department_id == department_id)

    tokens = query.order_by(APIToken.created_at.desc()).offset(skip).limit(limit).all()

    log_info(f"Retrieved {len(tokens)} API tokens", context=f"Admin {current_user.id}")

    return tokens


@router.get("/{token_id}", response_model=APITokenInDB)
def get_api_token(
    token_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get specific API token by ID (Admin only)"""
    check_admin_access(current_user)

    token = db.query(APIToken).filter(APIToken.id == token_id).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API token with id {token_id} not found"
        )

    log_info(f"Retrieved API token {token_id}", context=f"Admin {current_user.id}")

    return token


@router.post("/", response_model=APITokenWithKey, status_code=status.HTTP_201_CREATED)
def create_api_token(
    token_data: APITokenCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new API token (Admin only)

    Returns token with token_key - SAVE IT SECURELY!
    Token key will not be retrievable after creation.
    """
    check_admin_access(current_user)

    # Generate secure token key
    token_key = generate_token_key()

    # Validate scopes
    if not token_data.scopes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one scope is required"
        )

    # Create token
    new_token = APIToken(
        name=token_data.name,
        description=token_data.description,
        token_key=token_key,
        scopes=[scope.value for scope in token_data.scopes],
        status=APITokenStatusEnum.ACTIVE,
        department_id=token_data.department_id,
        created_by=current_user.id,
        expires_at=token_data.expires_at,
        request_count=0,
    )

    db.add(new_token)
    db.commit()
    db.refresh(new_token)

    log_info(
        f"Created API token: {new_token.name} (ID: {new_token.id})",
        context=f"Admin {current_user.id}"
    )

    # Return token with key (only time it's shown)
    return APITokenWithKey(
        id=new_token.id,
        name=new_token.name,
        description=new_token.description,
        token_key=new_token.token_key,
        scopes=[APITokenScopeEnum(s) for s in new_token.scopes],
        status=new_token.status,
        department_id=new_token.department_id,
        created_by=new_token.created_by,
        created_at=new_token.created_at,
        expires_at=new_token.expires_at,
        last_used_at=new_token.last_used_at,
        revoked_at=new_token.revoked_at,
        revoked_by=new_token.revoked_by,
        request_count=new_token.request_count,
    )


@router.put("/{token_id}", response_model=APITokenInDB)
def update_api_token(
    token_id: int,
    token_data: APITokenUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update API token (Admin only)"""
    check_admin_access(current_user)

    token = db.query(APIToken).filter(APIToken.id == token_id).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API token with id {token_id} not found"
        )

    # Update fields
    update_data = token_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "scopes" and value is not None:
            # Convert enum to values
            setattr(token, field, [scope.value for scope in value])
        else:
            setattr(token, field, value)

    db.commit()
    db.refresh(token)

    log_info(
        f"Updated API token: {token.name} (ID: {token.id})",
        context=f"Admin {current_user.id}"
    )

    return token


@router.post("/{token_id}/revoke", response_model=APITokenInDB)
def revoke_api_token(
    token_id: int,
    revoke_data: Optional[APITokenRevoke] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Revoke API token (Admin only)

    Revoked tokens cannot be reactivated - create new token instead
    """
    check_admin_access(current_user)

    token = db.query(APIToken).filter(APIToken.id == token_id).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API token with id {token_id} not found"
        )

    if token.status == APITokenStatusEnum.REVOKED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Token is already revoked"
        )

    # Revoke token
    token.status = APITokenStatusEnum.REVOKED
    token.revoked_at = datetime.now()
    token.revoked_by = current_user.id

    db.commit()
    db.refresh(token)

    log_warning(
        f"Revoked API token: {token.name} (ID: {token.id}). Reason: {revoke_data.reason if revoke_data else 'Not specified'}",
        context=f"Admin {current_user.id}"
    )

    return token


@router.delete("/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_api_token(
    token_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete API token permanently (Admin only)

    WARNING: This is irreversible. Consider revoking instead.
    """
    check_admin_access(current_user)

    token = db.query(APIToken).filter(APIToken.id == token_id).first()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API token with id {token_id} not found"
        )

    db.delete(token)
    db.commit()

    log_warning(
        f"DELETED API token: {token.name} (ID: {token.id})",
        context=f"Admin {current_user.id}"
    )

    return None
