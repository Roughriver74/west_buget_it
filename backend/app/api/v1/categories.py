from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io

from app.db import get_db
from app.db.models import BudgetCategory
from app.schemas import BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCategoryInDB

router = APIRouter()


class BulkUpdateRequest(BaseModel):
    """Request for bulk update operations"""
    ids: List[int]
    is_active: bool = None


class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operations"""
    ids: List[int]


@router.get("/", response_model=List[BudgetCategoryInDB])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    db: Session = Depends(get_db)
):
    """Get all budget categories"""
    query = db.query(BudgetCategory)

    if is_active is not None:
        query = query.filter(BudgetCategory.is_active == is_active)

    categories = query.offset(skip).limit(limit).all()
    return categories


@router.get("/{category_id}", response_model=BudgetCategoryInDB)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get category by ID"""
    category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    return category


@router.post("/", response_model=BudgetCategoryInDB, status_code=status.HTTP_201_CREATED)
def create_category(category: BudgetCategoryCreate, db: Session = Depends(get_db)):
    """Create new budget category"""
    # Check if category with same name exists
    existing = db.query(BudgetCategory).filter(BudgetCategory.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists"
        )

    db_category = BudgetCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=BudgetCategoryInDB)
def update_category(
    category_id: int,
    category: BudgetCategoryUpdate,
    db: Session = Depends(get_db)
):
    """Update budget category"""
    db_category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Update fields
    update_data = category.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete budget category (soft delete - mark as inactive)"""
    db_category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Soft delete - mark as inactive
    db_category.is_active = False
    db.commit()
    return None


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_categories(request: BulkUpdateRequest, db: Session = Depends(get_db)):
    """Bulk update categories (activate/deactivate)"""
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No category IDs provided"
        )

    categories = db.query(BudgetCategory).filter(BudgetCategory.id.in_(request.ids)).all()

    if len(categories) != len(request.ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some categories not found"
        )

    updated_count = 0
    if request.is_active is not None:
        for category in categories:
            category.is_active = request.is_active
            updated_count += 1

    db.commit()

    return {
        "message": f"Successfully updated {updated_count} categories",
        "updated_count": updated_count
    }


@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_categories(request: BulkDeleteRequest, db: Session = Depends(get_db)):
    """Bulk delete categories (soft delete - mark as inactive)"""
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No category IDs provided"
        )

    categories = db.query(BudgetCategory).filter(BudgetCategory.id.in_(request.ids)).all()

    deleted_count = 0
    for category in categories:
        category.is_active = False
        deleted_count += 1

    db.commit()

    return {
        "message": f"Successfully deleted {deleted_count} categories",
        "deleted_count": deleted_count
    }


@router.get("/export", response_class=StreamingResponse)
def export_categories(db: Session = Depends(get_db)):
    """Export all categories to Excel"""
    categories = db.query(BudgetCategory).all()

    # Convert to DataFrame
    data = []
    for cat in categories:
        data.append({
            "ID": cat.id,
            "Название": cat.name,
            "Тип": cat.type,
            "Описание": cat.description or "",
            "Активна": "Да" if cat.is_active else "Нет",
            "Родительская категория ID": cat.parent_id or "",
            "Дата создания": cat.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Категории')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=categories_export.xlsx"}
    )


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_categories(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import categories from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    try:
        # Read Excel file
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))

        # Validate required columns
        required_columns = ['Название', 'Тип']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )

        created_count = 0
        updated_count = 0
        errors = []

        for index, row in df.iterrows():
            try:
                name = str(row['Название']).strip()
                type_val = str(row['Тип']).strip().upper()

                if not name or name == 'nan':
                    errors.append(f"Row {index + 2}: Name is required")
                    continue

                if type_val not in ['OPEX', 'CAPEX']:
                    errors.append(f"Row {index + 2}: Type must be OPEX or CAPEX")
                    continue

                # Check if category exists
                existing = db.query(BudgetCategory).filter(BudgetCategory.name == name).first()

                if existing:
                    # Update existing
                    existing.type = type_val
                    existing.description = str(row.get('Описание', '')) if pd.notna(row.get('Описание')) else None
                    existing.is_active = str(row.get('Активна', 'Да')).strip().lower() in ['да', 'yes', '1', 'true']
                    updated_count += 1
                else:
                    # Create new
                    new_category = BudgetCategory(
                        name=name,
                        type=type_val,
                        description=str(row.get('Описание', '')) if pd.notna(row.get('Описание')) else None,
                        is_active=str(row.get('Активна', 'Да')).strip().lower() in ['да', 'yes', '1', 'true']
                    )
                    db.add(new_category)
                    created_count += 1

            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")

        db.commit()

        return {
            "message": "Import completed",
            "created_count": created_count,
            "updated_count": updated_count,
            "errors": errors if errors else None
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing file: {str(e)}"
        )
