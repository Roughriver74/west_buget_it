from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io

from app.db import get_db
from app.db.models import Contractor, User, UserRoleEnum
from app.schemas import ContractorCreate, ContractorUpdate, ContractorInDB
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])


class BulkUpdateRequest(BaseModel):
    ids: List[int]
    is_active: bool


class BulkDeleteRequest(BaseModel):
    ids: List[int]


@router.get("/", response_model=List[ContractorInDB])
def get_contractors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all contractors

    - **USER**: Can only see contractors from their own department
    - **MANAGER**: Can see contractors from all departments
    - **ADMIN**: Can see contractors from all departments
    """
    query = db.query(Contractor)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Contractor.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(Contractor.department_id == department_id)

    if is_active is not None:
        query = query.filter(Contractor.is_active == is_active)

    if search:
        query = query.filter(
            (Contractor.name.ilike(f"%{search}%")) |
            (Contractor.short_name.ilike(f"%{search}%")) |
            (Contractor.inn.ilike(f"%{search}%"))
        )

    contractors = query.offset(skip).limit(limit).all()
    return contractors


@router.get("/{contractor_id}", response_model=ContractorInDB)
def get_contractor(
    contractor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get contractor by ID"""
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # USER can only view contractors from their department
    if current_user.role == UserRoleEnum.USER:
        if contractor.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to view this contractor"
            )

    return contractor


@router.post("/", response_model=ContractorInDB, status_code=status.HTTP_201_CREATED)
def create_contractor(
    contractor: ContractorCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new contractor

    Auto-assigns to user's department (or can be specified by ADMIN)
    """
    # USER can only create contractors in their own department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )

    # Check if contractor with same INN exists in the same department
    # (INN uniqueness is now scoped to department)
    if contractor.inn:
        query = db.query(Contractor).filter(Contractor.inn == contractor.inn)

        # For USER, only check within their department
        if current_user.role == UserRoleEnum.USER:
            query = query.filter(Contractor.department_id == current_user.department_id)

        existing = query.first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contractor with INN '{contractor.inn}' already exists in this department"
            )

    # Create contractor with department_id
    contractor_data = contractor.model_dump()

    # Auto-assign department_id based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER always creates in their own department
        contractor_data['department_id'] = current_user.department_id
    elif 'department_id' not in contractor_data or contractor_data['department_id'] is None:
        # MANAGER/ADMIN must specify department or use their own
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required"
            )
        contractor_data['department_id'] = current_user.department_id

    db_contractor = Contractor(**contractor_data)
    db.add(db_contractor)
    db.commit()
    db.refresh(db_contractor)
    return db_contractor


@router.put("/{contractor_id}", response_model=ContractorInDB)
def update_contractor(
    contractor_id: int,
    contractor: ContractorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update contractor"""
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not db_contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # USER can only update contractors from their department
    if current_user.role == UserRoleEnum.USER:
        if db_contractor.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to update this contractor"
            )

    # Update fields
    update_data = contractor.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contractor, field, value)

    db.commit()
    db.refresh(db_contractor)
    return db_contractor


@router.delete("/{contractor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contractor(
    contractor_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete contractor (permanently remove from database)"""
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not db_contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # USER can only delete contractors from their department
    if current_user.role == UserRoleEnum.USER:
        if db_contractor.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions to delete this contractor"
            )

    # Hard delete - permanently remove from database
    db.delete(db_contractor)
    db.commit()
    return None


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_contractors(
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk activate/deactivate contractors"""
    query = db.query(Contractor).filter(Contractor.id.in_(request.ids))

    # USER can only update contractors from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Contractor.department_id == current_user.department_id)

    contractors = query.all()

    for contractor in contractors:
        contractor.is_active = request.is_active

    db.commit()

    return {
        "updated_count": len(contractors),
        "ids": request.ids,
        "is_active": request.is_active
    }


@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_contractors(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk delete contractors (permanently remove from database)"""
    query = db.query(Contractor).filter(Contractor.id.in_(request.ids))

    # USER can only delete contractors from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Contractor.department_id == current_user.department_id)

    contractors = query.all()

    for contractor in contractors:
        db.delete(contractor)

    db.commit()

    return {
        "deleted_count": len(contractors),
        "ids": request.ids
    }


@router.get("/export", response_class=StreamingResponse)
def export_contractors(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export contractors to Excel"""
    query = db.query(Contractor)

    # USER can only export contractors from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Contractor.department_id == current_user.department_id)

    contractors = query.all()

    data = []
    for contractor in contractors:
        data.append({
            "ID": contractor.id,
            "Название": contractor.name,
            "Краткое название": contractor.short_name or "",
            "ИНН": contractor.inn or "",
            "Контактная информация": contractor.contact_info or "",
            "Активен": "Да" if contractor.is_active else "Нет",
        })

    df = pd.DataFrame(data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Контрагенты')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=contractors.xlsx"}
    )


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_contractors(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import contractors from Excel

    All imported contractors are assigned to the user's department
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
        log_info(f"Starting contractors import from {file.filename}", "Import")
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

                short_name = str(row.get("Краткое название", "")).strip() if pd.notna(row.get("Краткое название")) else None
                inn = str(row.get("ИНН", "")).strip() if pd.notna(row.get("ИНН")) else None
                contact_info = str(row.get("Контактная информация", "")).strip() if pd.notna(row.get("Контактная информация")) else None
                is_active_str = str(row.get("Активен", "Да")).strip() if pd.notna(row.get("Активен")) else "Да"
                is_active = is_active_str.lower() in ["да", "yes", "true", "1"]

                # Determine department_id for import
                import_department_id = current_user.department_id

                # Try to find existing contractor by INN or name within the same department
                existing_contractor = None
                if inn:
                    existing_contractor = db.query(Contractor).filter(
                        Contractor.inn == inn,
                        Contractor.department_id == import_department_id
                    ).first()
                if not existing_contractor:
                    existing_contractor = db.query(Contractor).filter(
                        Contractor.name == name,
                        Contractor.department_id == import_department_id
                    ).first()

                if existing_contractor:
                    # Update existing (only if belongs to user's department)
                    existing_contractor.name = name
                    existing_contractor.short_name = short_name
                    existing_contractor.inn = inn
                    existing_contractor.contact_info = contact_info
                    existing_contractor.is_active = is_active
                    updated_count += 1
                else:
                    # Create new with department_id
                    new_contractor = Contractor(
                        name=name,
                        short_name=short_name,
                        inn=inn,
                        contact_info=contact_info,
                        is_active=is_active,
                        department_id=import_department_id
                    )
                    db.add(new_contractor)
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
