from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io

from app.db import get_db
from app.db.models import Contractor
from app.schemas import ContractorCreate, ContractorUpdate, ContractorInDB

router = APIRouter()


class BulkUpdateRequest(BaseModel):
    ids: List[int]
    is_active: bool


class BulkDeleteRequest(BaseModel):
    ids: List[int]


@router.get("/", response_model=List[ContractorInDB])
def get_contractors(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Get all contractors"""
    query = db.query(Contractor)

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
def get_contractor(contractor_id: int, db: Session = Depends(get_db)):
    """Get contractor by ID"""
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )
    return contractor


@router.post("/", response_model=ContractorInDB, status_code=status.HTTP_201_CREATED)
def create_contractor(contractor: ContractorCreate, db: Session = Depends(get_db)):
    """Create new contractor"""
    # Check if contractor with same INN exists
    if contractor.inn:
        existing = db.query(Contractor).filter(Contractor.inn == contractor.inn).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Contractor with INN '{contractor.inn}' already exists"
            )

    db_contractor = Contractor(**contractor.model_dump())
    db.add(db_contractor)
    db.commit()
    db.refresh(db_contractor)
    return db_contractor


@router.put("/{contractor_id}", response_model=ContractorInDB)
def update_contractor(
    contractor_id: int,
    contractor: ContractorUpdate,
    db: Session = Depends(get_db)
):
    """Update contractor"""
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not db_contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # Update fields
    update_data = contractor.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contractor, field, value)

    db.commit()
    db.refresh(db_contractor)
    return db_contractor


@router.delete("/{contractor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contractor(contractor_id: int, db: Session = Depends(get_db)):
    """Delete contractor (soft delete - mark as inactive)"""
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if not db_contractor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contractor with id {contractor_id} not found"
        )

    # Soft delete - mark as inactive
    db_contractor.is_active = False
    db.commit()
    return None


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_contractors(
    request: BulkUpdateRequest,
    db: Session = Depends(get_db)
):
    """Bulk activate/deactivate contractors"""
    contractors = db.query(Contractor).filter(Contractor.id.in_(request.ids)).all()

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
    db: Session = Depends(get_db)
):
    """Bulk soft delete contractors"""
    contractors = db.query(Contractor).filter(Contractor.id.in_(request.ids)).all()

    for contractor in contractors:
        contractor.is_active = False

    db.commit()

    return {
        "deleted_count": len(contractors),
        "ids": request.ids
    }


@router.get("/export", response_class=StreamingResponse)
def export_contractors(db: Session = Depends(get_db)):
    """Export contractors to Excel"""
    contractors = db.query(Contractor).all()

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
    db: Session = Depends(get_db)
):
    """Import contractors from Excel"""
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

                short_name = str(row.get("Краткое название", "")).strip() if pd.notna(row.get("Краткое название")) else None
                inn = str(row.get("ИНН", "")).strip() if pd.notna(row.get("ИНН")) else None
                contact_info = str(row.get("Контактная информация", "")).strip() if pd.notna(row.get("Контактная информация")) else None
                is_active_str = str(row.get("Активен", "Да")).strip() if pd.notna(row.get("Активен")) else "Да"
                is_active = is_active_str.lower() in ["да", "yes", "true", "1"]

                # Try to find existing contractor by INN or name
                existing_contractor = None
                if inn:
                    existing_contractor = db.query(Contractor).filter(Contractor.inn == inn).first()
                if not existing_contractor:
                    existing_contractor = db.query(Contractor).filter(Contractor.name == name).first()

                if existing_contractor:
                    # Update existing
                    existing_contractor.name = name
                    existing_contractor.short_name = short_name
                    existing_contractor.inn = inn
                    existing_contractor.contact_info = contact_info
                    existing_contractor.is_active = is_active
                    updated_count += 1
                else:
                    # Create new
                    new_contractor = Contractor(
                        name=name,
                        short_name=short_name,
                        inn=inn,
                        contact_info=contact_info,
                        is_active=is_active
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
