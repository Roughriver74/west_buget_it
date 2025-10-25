"""
Reusable FastAPI dependencies for common patterns
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import User, UserRoleEnum
from app.utils.auth import get_current_active_user


def get_department_filter(
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user)
) -> Optional[int]:
    """
    Get department ID for filtering based on user role

    Row-Level Security implementation:
    - USER: Can only access their own department
    - MANAGER/ADMIN: Can filter by specific department or see all

    Args:
        department_id: Optional department ID from query parameter
        current_user: Current authenticated user

    Returns:
        Department ID to filter by, or None to see all (ADMIN/MANAGER only)

    Raises:
        HTTPException: If USER has no assigned department
    """
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        return current_user.department_id

    # MANAGER and ADMIN can filter by department or see all
    return department_id


class DepartmentFilterDependency:
    """
    Dependency class for more complex department filtering scenarios

    Usage:
        dept_filter = Depends(DepartmentFilterDependency())
    """

    def __init__(self, require_department: bool = False):
        """
        Initialize department filter dependency

        Args:
            require_department: If True, raises error when no department is specified
        """
        self.require_department = require_department

    def __call__(
        self,
        department_id: Optional[int] = Query(None, description="Filter by department"),
        current_user: User = Depends(get_current_active_user)
    ) -> Optional[int]:
        """Apply department filtering logic"""
        if current_user.role == UserRoleEnum.USER:
            if not current_user.department_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User has no assigned department"
                )
            return current_user.department_id

        # For ADMIN/MANAGER
        if self.require_department and department_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required for this operation"
            )

        return department_id
