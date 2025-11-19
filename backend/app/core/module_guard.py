"""
Module Guard - Dependency for protecting endpoints with module access control
"""

from typing import Callable
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.api.dependencies import get_current_active_user
from app.services.module_service import ModuleService


def require_module(module_code: str) -> Callable:
    """
    Dependency factory that creates a dependency to check if a module is enabled
    for the current user's organization.

    Usage:
        @router.get("/endpoint")
        def protected_endpoint(
            current_user: User = Depends(require_module("AI_FORECAST")),
            db: Session = Depends(get_db)
        ):
            # This endpoint only accessible if AI_FORECAST is enabled
            pass

    Args:
        module_code: Module code to check (e.g., "AI_FORECAST", "CREDIT_PORTFOLIO")

    Returns:
        Dependency function that validates module access

    Raises:
        HTTPException 403: If module is not enabled for user's organization
        HTTPException 404: If module doesn't exist
    """

    async def _check_module_access(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db),
    ) -> User:
        """
        Check if current user's organization has access to the specified module
        
        TEMPORARILY DISABLED: Module system is disabled - all modules are accessible to everyone.

        Returns:
            User object if access is granted

        Raises:
            HTTPException 403: If module is not enabled
            HTTPException 404: If module doesn't exist
        """
        # TEMPORARILY DISABLED: Module system is disabled - allow all access
        return current_user
        
        # # Get user's organization
        # if not current_user.organization_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail=f"User does not belong to an organization. Module '{module_code}' access denied.",
        #     )

        # # Create module service
        # module_service = ModuleService(db)

        # # Check if module exists
        # module = module_service.get_module_by_code(module_code)
        # if not module:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail=f"Module '{module_code}' not found",
        #     )

        # # Check if module is enabled for user's organization
        # is_enabled = module_service.is_module_enabled(
        #     organization_id=current_user.organization_id,
        #     module_code=module_code,
        # )

        # if not is_enabled:
        #     # Emit access denied event
        #     module_service.emit_event(
        #         organization_id=current_user.organization_id,
        #         module_id=module.id,
        #         event_type="ACCESS_DENIED",
        #         metadata={
        #             "user_id": current_user.id,
        #             "module_code": module_code,
        #             "reason": "Module not enabled or expired",
        #         },
        #         user_id=current_user.id,
        #     )

        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail=f"Module '{module_code}' ({module.name}) is not enabled for your organization. Please contact your administrator to enable this feature.",
        #     )

        # return current_user

    return _check_module_access


def check_feature_limit(module_code: str, limit_type: str) -> Callable:
    """
    Dependency factory that checks if a feature limit has been reached.

    Usage:
        @router.post("/users")
        def create_user(
            current_user: User = Depends(check_feature_limit("MULTI_DEPARTMENT", "users")),
            db: Session = Depends(get_db)
        ):
            # This will fail if user limit is reached
            pass

    Args:
        module_code: Module code
        limit_type: Type of limit to check (e.g., "users", "departments", "api_calls")

    Returns:
        Dependency function that validates limit

    Raises:
        HTTPException 429: If limit is exceeded
    """

    async def _check_limit(
        current_user: User = Depends(require_module(module_code)),
        db: Session = Depends(get_db),
    ) -> User:
        """
        Check if feature limit is exceeded
        
        TEMPORARILY DISABLED: Module system is disabled - limits are not checked.

        Returns:
            User object if limit not exceeded

        Raises:
            HTTPException 429: If limit is exceeded
        """
        # TEMPORARILY DISABLED: Module system is disabled - allow all access
        return current_user
        
        # module_service = ModuleService(db)

        # limit_info = module_service.check_feature_limit(
        #     organization_id=current_user.organization_id,
        #     module_code=module_code,
        #     limit_type=limit_type,
        # )

        # if limit_info["is_exceeded"]:
        #     raise HTTPException(
        #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        #         detail=f"Feature limit exceeded: {limit_type}. "
        #         f"Current: {limit_info['current_usage']}, "
        #         f"Limit: {limit_info['limit_value']}. "
        #         f"Please upgrade your plan or contact support.",
        #     )

        # return current_user

    return _check_limit


def increment_feature_usage(module_code: str, limit_type: str, increment: int = 1) -> Callable:
    """
    Dependency factory that increments feature usage counter.

    Usage:
        @router.post("/api-call")
        def api_endpoint(
            current_user: User = Depends(increment_feature_usage("AI_FORECAST", "api_calls")),
            db: Session = Depends(get_db)
        ):
            # Usage counter is incremented before endpoint execution
            pass

    Args:
        module_code: Module code
        limit_type: Type of limit to increment
        increment: Amount to increment by (default 1)

    Returns:
        Dependency function that increments usage

    Raises:
        HTTPException 429: If incrementing would exceed limit
    """

    async def _increment_usage(
        current_user: User = Depends(require_module(module_code)),
        db: Session = Depends(get_db),
    ) -> User:
        """
        Increment feature usage counter
        
        TEMPORARILY DISABLED: Module system is disabled - usage is not tracked.

        Returns:
            User object if increment successful

        Raises:
            HTTPException 429: If limit would be exceeded
        """
        # TEMPORARILY DISABLED: Module system is disabled - allow all access
        return current_user
        
        # module_service = ModuleService(db)

        # success = module_service.increment_usage(
        #     organization_id=current_user.organization_id,
        #     module_code=module_code,
        #     limit_type=limit_type,
        #     increment=increment,
        # )

        # if not success:
        #     limit_info = module_service.check_feature_limit(
        #         organization_id=current_user.organization_id,
        #         module_code=module_code,
        #         limit_type=limit_type,
        #     )

        #     raise HTTPException(
        #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        #         detail=f"Feature limit would be exceeded: {limit_type}. "
        #         f"Current: {limit_info['current_usage']}, "
        #         f"Limit: {limit_info['limit_value']}. "
        #         f"Please upgrade your plan or contact support.",
        #     )

        # return current_user

    return _increment_usage
