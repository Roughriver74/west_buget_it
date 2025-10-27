from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io

from app.db import get_db
from app.db.models import Organization, User, UserRoleEnum
from app.schemas import OrganizationCreate, OrganizationUpdate, OrganizationInDB
from app.services.cache import cache_service
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "organizations"

class BulkUpdateRequest(BaseModel):
    ids: List[int]
    is_active: bool


class BulkDeleteRequest(BaseModel):
    ids: List[int]


@router.get("/", response_model=List[OrganizationInDB])
def get_organizations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all organizations

    - **USER**: Can only see organizations from their own department
    - **MANAGER**: Can see organizations from all departments
    - **ADMIN**: Can see organizations from all departments
    """
    query = db.query(Organization)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Organization.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(Organization.department_id == department_id)

    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)

    cache_key = cache_service.build_key(
        "list",
        current_user.role,
        current_user.department_id,
        department_id,
        is_active,
        skip,
        limit,
    )
    cached_payload = cache_service.get(CACHE_NAMESPACE, cache_key)
    if cached_payload is not None:
        return [OrganizationInDB.model_validate(item) for item in cached_payload]

    organizations = query.offset(skip).limit(limit).all()
    result_models = [OrganizationInDB.model_validate(organization) for organization in organizations]
    cache_service.set(
        CACHE_NAMESPACE,
        cache_key,
        [model.model_dump() for model in result_models],
    )
    return result_models


@router.get("/{organization_id}", response_model=OrganizationInDB)
def get_organization(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get organization by ID"""
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # USER can only view organizations from their department
    if current_user.role == UserRoleEnum.USER:
        if organization.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this organization"
            )

    return organization


@router.post("/", response_model=OrganizationInDB, status_code=status.HTTP_201_CREATED)
def create_organization(
    organization: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new organization

    Auto-assigns to user's department (or can be specified by ADMIN)
    """
    # USER can only create organizations in their own department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )

    # Check if organization with same name exists in the same department
    # (name uniqueness is now scoped to department)
    query = db.query(Organization).filter(Organization.name == organization.name)

    # For USER, only check within their department
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(Organization.department_id == current_user.department_id)

    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with name '{organization.name}' already exists in this department"
        )

    # Create organization with department_id
    organization_data = organization.model_dump()

    # Auto-assign department_id based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER always creates in their own department
        organization_data['department_id'] = current_user.department_id
    elif 'department_id' not in organization_data or organization_data['department_id'] is None:
        # MANAGER/ADMIN must specify department or use their own
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required"
            )
        organization_data['department_id'] = current_user.department_id

    db_organization = Organization(**organization_data)
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    cache_service.invalidate_namespace(CACHE_NAMESPACE)
    return db_organization


@router.put("/{organization_id}", response_model=OrganizationInDB)
def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update organization"""
    db_organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # USER can only update organizations from their department
    if current_user.role == UserRoleEnum.USER:
        if db_organization.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this organization"
            )

    # Update fields
    update_data = organization.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_organization, field, value)

    db.commit()
    db.refresh(db_organization)
    cache_service.invalidate_namespace(CACHE_NAMESPACE)
    return db_organization


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(
    organization_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete organization (permanently remove from database)"""
    db_organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # USER can only delete organizations from their department
    if current_user.role == UserRoleEnum.USER:
        if db_organization.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this organization"
            )

    # Hard delete - permanently remove from database
    db.delete(db_organization)
    db.commit()
    cache_service.invalidate_namespace(CACHE_NAMESPACE)
    return None


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_organizations(
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk activate/deactivate organizations"""
    query = db.query(Organization).filter(Organization.id.in_(request.ids))

    # USER can only update organizations from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Organization.department_id == current_user.department_id)

    organizations = query.all()

    for organization in organizations:
        organization.is_active = request.is_active

    db.commit()
    cache_service.invalidate_namespace(CACHE_NAMESPACE)

    return {
        "updated_count": len(organizations),
        "ids": request.ids,
        "is_active": request.is_active
    }


@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_organizations(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk delete organizations (permanently remove from database)"""
    query = db.query(Organization).filter(Organization.id.in_(request.ids))

    # USER can only delete organizations from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Organization.department_id == current_user.department_id)

    organizations = query.all()

    for organization in organizations:
        db.delete(organization)

    db.commit()
    cache_service.invalidate_namespace(CACHE_NAMESPACE)

    return {
        "deleted_count": len(organizations),
        "ids": request.ids
    }


@router.get("/export", response_class=StreamingResponse)
def export_organizations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export organizations to Excel"""
    query = db.query(Organization)

    # USER can only export organizations from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Organization.department_id == current_user.department_id)

    organizations = query.all()

    data = []
    for organization in organizations:
        data.append({
            "ID": organization.id,
            "Название": organization.name,
            "Полное юридическое название": organization.legal_name or "",
            "Активна": "Да" if organization.is_active else "Нет",
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Организации')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=organizations.xlsx"}
    )


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_organizations(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import organizations from Excel

    All imported organizations are assigned to the user's department
    """
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )

    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате Excel (.xlsx или .xls)"
        )

    try:
        # Read Excel file
        log_info(f"Starting organizations import from {file.filename}", "Import")
        content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size is 10MB"
            )

        # Try to read Excel file with error handling
        try:
            df = pd.read_excel(io.BytesIO(content))
        except Exception as e:
            log_error(e, "Failed to parse Excel file")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Excel file format: {str(e)}"
            )

        # Check if dataframe is empty
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel file is empty"
            )

        # Validate required columns
        required_columns = ["Название"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}"
            )

        created_count = 0
        updated_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                name = str(row["Название"]).strip() if pd.notna(row["Название"]) else None
                if not name:
                    errors.append(f"Строка {index + 2}: отсутствует название")
                    continue

                legal_name = str(row.get("Полное юридическое название", "")).strip() if pd.notna(row.get("Полное юридическое название")) else None
                is_active_str = str(row.get("Активна", "Да")).strip() if pd.notna(row.get("Активна")) else "Да"
                is_active = is_active_str.lower() in ["да", "yes", "true", "1"]

                # Determine department_id for import
                import_department_id = current_user.department_id

                # Try to find existing organization by name within the same department
                existing_organization = db.query(Organization).filter(
                    Organization.name == name,
                    Organization.department_id == import_department_id
                ).first()

                if existing_organization:
                    # Update existing (only if belongs to user's department)
                    existing_organization.legal_name = legal_name
                    existing_organization.is_active = is_active
                    updated_count += 1
                else:
                    # Create new with department_id
                    new_organization = Organization(
                        name=name,
                        legal_name=legal_name,
                        is_active=is_active,
                        department_id=import_department_id
                    )
                    db.add(new_organization)
                    created_count += 1

            except Exception as e:
                errors.append(f"Строка {index + 2}: {str(e)}")

        db.commit()
        cache_service.invalidate_namespace(CACHE_NAMESPACE)

        return {
            "created_count": created_count,
            "updated_count": updated_count,
            "errors": errors
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при импорте: {str(e)}"
        )
