"""
API Endpoints for 1C Synchronization

Endpoints для синхронизации справочников из 1С через OData
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.utils.auth import get_current_active_user
from app.db.session import get_db
from app.db.models import User, UserRoleEnum
from app.services.odata_1c_client import create_1c_client_from_env
from app.services.catalog_1c_sync import (
    sync_all_catalogs_from_1c,
    OrganizationSync,
    BudgetCategorySync,
    CatalogSyncResult
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class SyncCatalogsRequest(BaseModel):
    """Request для синхронизации справочников"""
    department_id: int
    sync_organizations: bool = True
    sync_categories: bool = True


class SyncCatalogsResponse(BaseModel):
    """Response для синхронизации справочников"""
    success: bool
    message: str
    organizations_result: Optional[dict] = None
    categories_result: Optional[dict] = None
    department: dict


@router.post("/catalogs", response_model=SyncCatalogsResponse)
def sync_catalogs_from_1c(
    request: SyncCatalogsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Синхронизировать справочники из 1С

    - **Catalog_Организации** → Organizations (shared across departments)
    - **Catalog_СтатьиДвиженияДенежныхСредств** → BudgetCategories (per department)

    Требует роли ADMIN или MANAGER.
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN or MANAGER can sync catalogs from 1C"
        )

    try:
        # Create 1C client
        odata_client = create_1c_client_from_env()

        # Test connection
        if not odata_client.test_connection():
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to 1C OData service"
            )

        # Get department info
        from app.db.models import Department
        department = db.query(Department).filter_by(id=request.department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")

        logger.info(
            f"Starting catalog sync for department_id={request.department_id} "
            f"by user {current_user.username}"
        )

        # Sync catalogs
        results = sync_all_catalogs_from_1c(
            db=db,
            odata_client=odata_client,
            department_id=request.department_id,
            sync_organizations=request.sync_organizations,
            sync_categories=request.sync_categories
        )

        # Prepare response
        response = SyncCatalogsResponse(
            success=True,
            message="Catalog synchronization completed",
            organizations_result=results.get('organizations').to_dict() if 'organizations' in results else None,
            categories_result=results.get('budget_categories').to_dict() if 'budget_categories' in results else None,
            department={
                'id': department.id,
                'code': department.code,
                'name': department.name
            }
        )

        logger.info(f"Catalog sync completed: {response}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog sync error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Catalog synchronization failed: {str(e)}"
        )


@router.post("/organizations", response_model=dict)
def sync_organizations_from_1c(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Синхронизировать только организации из 1С

    Organizations are shared across departments, но можно указать department_id
    для tracking кто запустил синхронизацию.

    Требует роли ADMIN или MANAGER.
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN or MANAGER can sync organizations from 1C"
        )

    try:
        # Create 1C client
        odata_client = create_1c_client_from_env()

        # Test connection
        if not odata_client.test_connection():
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to 1C OData service"
            )

        logger.info(f"Starting organizations sync by user {current_user.username}")

        # Sync organizations
        org_sync = OrganizationSync(db, odata_client)
        result = org_sync.sync_organizations(department_id=department_id)

        return {
            'success': result.success,
            'message': 'Organizations synchronization completed',
            'statistics': result.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Organizations sync error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Organizations synchronization failed: {str(e)}"
        )


@router.post("/budget-categories", response_model=dict)
def sync_budget_categories_from_1c(
    department_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Синхронизировать категории бюджета из 1С

    Синхронизирует Catalog_СтатьиДвиженияДенежныхСредств для указанного отдела.
    Категории привязываются к department_id.

    Требует роли ADMIN или MANAGER.
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=403,
            detail="Only ADMIN or MANAGER can sync budget categories from 1C"
        )

    try:
        # Get department info
        from app.db.models import Department
        department = db.query(Department).filter_by(id=department_id).first()
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")

        # Create 1C client
        odata_client = create_1c_client_from_env()

        # Test connection
        if not odata_client.test_connection():
            raise HTTPException(
                status_code=503,
                detail="Failed to connect to 1C OData service"
            )

        logger.info(
            f"Starting budget categories sync for department_id={department_id} "
            f"by user {current_user.username}"
        )

        # Sync categories
        cat_sync = BudgetCategorySync(db, odata_client, department_id)
        result = cat_sync.sync_categories()

        return {
            'success': result.success,
            'message': 'Budget categories synchronization completed',
            'statistics': result.to_dict(),
            'department': {
                'id': department.id,
                'code': department.code,
                'name': department.name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Budget categories sync error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Budget categories synchronization failed: {str(e)}"
        )


@router.get("/status", response_model=dict)
def get_1c_sync_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить статус синхронизации с 1С

    Проверяет подключение к 1С OData и возвращает статистику синхронизированных данных.
    """
    try:
        # Create 1C client
        odata_client = create_1c_client_from_env()

        # Test connection
        connection_ok = odata_client.test_connection()

        # Get statistics
        from app.db.models import Organization, BudgetCategory

        organizations_count = db.query(Organization).filter(
            Organization.external_id_1c.isnot(None)
        ).count()

        categories_count = db.query(BudgetCategory).filter(
            BudgetCategory.external_id_1c.isnot(None)
        ).count()

        return {
            'connection_ok': connection_ok,
            'statistics': {
                'organizations_synced': organizations_count,
                'budget_categories_synced': categories_count
            },
            'odata_url': odata_client.base_url if connection_ok else None
        }

    except Exception as e:
        logger.error(f"Failed to get sync status: {str(e)}")
        return {
            'connection_ok': False,
            'error': str(e)
        }
