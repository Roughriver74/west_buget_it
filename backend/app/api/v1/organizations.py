from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io

from app.db import get_db
from app.db.models import Organization
from app.schemas import OrganizationCreate, OrganizationUpdate, OrganizationInDB

router = APIRouter()


class BulkUpdateRequest(BaseModel):
    ids: List[int]
    is_active: bool


class BulkDeleteRequest(BaseModel):
    ids: List[int]


@router.get("/", response_model=List[OrganizationInDB])
def get_organizations(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Get all organizations"""
    query = db.query(Organization)

    if is_active is not None:
        query = query.filter(Organization.is_active == is_active)

    organizations = query.offset(skip).limit(limit).all()
    return organizations


@router.get("/{organization_id}", response_model=OrganizationInDB)
def get_organization(organization_id: int, db: Session = Depends(get_db)):
    """Get organization by ID"""
    organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )
    return organization


@router.post("/", response_model=OrganizationInDB, status_code=status.HTTP_201_CREATED)
def create_organization(organization: OrganizationCreate, db: Session = Depends(get_db)):
    """Create new organization"""
    # Check if organization with same name exists
    existing = db.query(Organization).filter(Organization.name == organization.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Organization with name '{organization.name}' already exists"
        )

    db_organization = Organization(**organization.model_dump())
    db.add(db_organization)
    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.put("/{organization_id}", response_model=OrganizationInDB)
def update_organization(
    organization_id: int,
    organization: OrganizationUpdate,
    db: Session = Depends(get_db)
):
    """Update organization"""
    db_organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # Update fields
    update_data = organization.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_organization, field, value)

    db.commit()
    db.refresh(db_organization)
    return db_organization


@router.delete("/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(organization_id: int, db: Session = Depends(get_db)):
    """Delete organization (soft delete - mark as inactive)"""
    db_organization = db.query(Organization).filter(Organization.id == organization_id).first()
    if not db_organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Organization with id {organization_id} not found"
        )

    # Soft delete - mark as inactive
    db_organization.is_active = False
    db.commit()
    return None


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_organizations(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db)
):
    """Bulk activate/deactivate organizations"""
    organizations = db.query(Organization).filter(Organization.id.in_(request.ids)).all()

    for organization in organizations:
        organization.is_active = request.is_active

    db.commit()

    return {
        "updated_count": len(organizations),
        "ids": request.ids,
        "is_active": request.is_active
    }


@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_organizations(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db)
):
    """Bulk soft delete organizations"""
    organizations = db.query(Organization).filter(Organization.id.in_(request.ids)).all()

    for organization in organizations:
        organization.is_active = False

    db.commit()

    return {
        "deleted_count": len(organizations),
        "ids": request.ids
    }


@router.get("/export", response_class=StreamingResponse)
def export_organizations(db: Session = Depends(get_db)):
    """Export organizations to Excel"""
    organizations = db.query(Organization).all()

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
    db: Session = Depends(get_db)
):
    """Import organizations from Excel"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Файл должен быть в формате Excel (.xlsx или .xls)"
        )

    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))

        # Validate required columns
        required_columns = ["Название"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}"
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

                # Try to find existing organization by name
                existing_organization = db.query(Organization).filter(Organization.name == name).first()

                if existing_organization:
                    # Update existing
                    existing_organization.legal_name = legal_name
                    existing_organization.is_active = is_active
                    updated_count += 1
                else:
                    # Create new
                    new_organization = Organization(
                        name=name,
                        legal_name=legal_name,
                        is_active=is_active
                    )
                    db.add(new_organization)
                    created_count += 1

            except Exception as e:
                errors.append(f"Строка {index + 2}: {str(e)}")

        db.commit()

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
