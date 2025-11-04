"""
Utilities for API Token management and authentication
"""
import secrets
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.models import APIToken, APITokenStatusEnum, APITokenScopeEnum
from app.utils.logger import log_info, log_warning


security = HTTPBearer()


def generate_token_key() -> str:
    """
    Generate a secure random token key

    Format: itb_<64 hex characters>
    Example: itb_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
    """
    return f"itb_{secrets.token_hex(32)}"


async def verify_api_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = None
) -> APIToken:
    """
    Verify API token and return token object if valid

    Checks:
    - Token exists
    - Token is active
    - Token is not expired
    - Token has not been revoked

    Updates last_used_at and request_count on successful verification
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )

    token_key = credentials.credentials

    if not token_key.startswith("itb_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format"
        )

    # Query token from database
    token = db.query(APIToken).filter(APIToken.token_key == token_key).first()

    if not token:
        log_warning(f"API token not found: {token_key[:20]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token"
        )

    # Check if token is active
    if token.status != APITokenStatusEnum.ACTIVE:
        log_warning(f"API token not active: {token.name} (status: {token.status})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"API token is {token.status.lower()}"
        )

    # Check if token is expired
    if token.expires_at and token.expires_at < datetime.now():
        log_warning(f"API token expired: {token.name}")
        # Auto-update status to EXPIRED
        token.status = APITokenStatusEnum.EXPIRED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API token has expired"
        )

    # Update usage tracking
    token.last_used_at = datetime.now()
    token.request_count += 1
    db.commit()

    log_info(f"API token verified: {token.name} (ID: {token.id})")

    return token


def check_token_scope(token: APIToken, required_scope: APITokenScopeEnum) -> bool:
    """
    Check if token has required scope

    ADMIN scope grants all permissions
    """
    if not token.scopes:
        return False

    scopes = token.scopes if isinstance(token.scopes, list) else []

    # ADMIN has all permissions
    if APITokenScopeEnum.ADMIN.value in scopes:
        return True

    # Check specific scope
    return required_scope.value in scopes


def require_scope(required_scope: APITokenScopeEnum):
    """
    Decorator to require specific scope for API endpoint

    Usage:
        @router.post("/data")
        @require_scope(APITokenScopeEnum.WRITE)
        async def create_data(token: APIToken = Depends(verify_api_token)):
            ...
    """
    def decorator(token: APIToken):
        if not check_token_scope(token, required_scope):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token does not have required scope: {required_scope.value}"
            )
        return token

    return decorator
