from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pandas as pd
import io

from app.db import get_db
from app.db.models import BudgetCategory, User, UserRoleEnum
from app.schemas import BudgetCategoryCreate, BudgetCategoryUpdate, BudgetCategoryInDB
from app.services.cache import cache_service
from app.utils.auth import get_current_active_user
from app.utils.logger import logger, log_error, log_info

router = APIRouter(dependencies=[Depends(get_current_active_user)])

CACHE_NAMESPACE = "categories"

class BulkUpdateRequest(BaseModel):
    """Request for bulk update operations"""
    ids: List[int]
    is_active: bool = None


class BulkDeleteRequest(BaseModel):
    """Request for bulk delete operations"""
    ids: List[int]


@router.get("/", response_model=List[BudgetCategoryInDB])
def get_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    department_id: Optional[int] = Query(None, description="Filter by department (ADMIN/MANAGER only)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all budget categories

    - **USER**: Can only see categories from their own department
    - **MANAGER**: Can see categories from all departments
    - **ADMIN**: Can see categories from all departments
    """
    query = db.query(BudgetCategory)

    # Department filtering based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetCategory.department_id == current_user.department_id)
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            query = query.filter(BudgetCategory.department_id == department_id)

    if is_active is not None:
        query = query.filter(BudgetCategory.is_active == is_active)

    cached_key = cache_service.build_key(
        "list",
        current_user.role,
        current_user.department_id,
        department_id,
        is_active,
        skip,
        limit,
    )

    cached_payload = cache_service.get(CACHE_NAMESPACE, cached_key)
    if cached_payload is not None:
        return [BudgetCategoryInDB.model_validate(item) for item in cached_payload]

    categories = query.offset(skip).limit(limit).all()
    result_models = [BudgetCategoryInDB.model_validate(category) for category in categories]
    cache_service.set(
        CACHE_NAMESPACE,
        cached_key,
        [model.model_dump() for model in result_models],
    )

    return result_models


@router.get("/{category_id}", response_model=BudgetCategoryInDB)
def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get category by ID"""
    category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # USER can only view categories from their department
    # Return 404 instead of 403 to prevent information disclosure
    if current_user.role == UserRoleEnum.USER:
        if category.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )

    return category


@router.post("/", response_model=BudgetCategoryInDB, status_code=status.HTTP_201_CREATED)
def create_category(
    category: BudgetCategoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create new budget category

    Auto-assigns to user's department (or can be specified by ADMIN)
    """
    # USER can only create categories in their own department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )

    # Check if category with same name exists in the same department
    # (name uniqueness is now scoped to department)
    query = db.query(BudgetCategory).filter(BudgetCategory.name == category.name)

    # For USER, only check within their department
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(BudgetCategory.department_id == current_user.department_id)

    existing = query.first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{category.name}' already exists in this department"
        )

    # Create category with department_id
    category_data = category.model_dump()

    # Auto-assign department_id based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER always creates in their own department
        category_data['department_id'] = current_user.department_id
    elif 'department_id' not in category_data or category_data['department_id'] is None:
        # MANAGER/ADMIN must specify department or use their own
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required"
            )
        category_data['department_id'] = current_user.department_id

    db_category = BudgetCategory(**category_data)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    cache_service.invalidate_namespace(CACHE_NAMESPACE)
    return db_category


@router.put("/{category_id}", response_model=BudgetCategoryInDB)
def update_category(
    category_id: int,
    category: BudgetCategoryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update budget category"""
    db_category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # USER can only update categories from their department
    # Return 404 instead of 403 to prevent information disclosure
    if current_user.role == UserRoleEnum.USER:
        if db_category.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )

    # Update fields
    update_data = category.model_dump(exclude_unset=True)

    # Log what we're updating
    from app.utils.logger import log_info
    log_info(f"Updating category {category_id} with data: {update_data}", "CategoryUpdate")

    for field, value in update_data.items():
        old_value = getattr(db_category, field, None)
        setattr(db_category, field, value)
        log_info(f"  {field}: {old_value} -> {value}", "CategoryUpdate")

    db.commit()
    log_info(f"Category {category_id} committed successfully", "CategoryUpdate")
    db.refresh(db_category)
    cache_service.invalidate_namespace(CACHE_NAMESPACE)
    return db_category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete budget category (soft delete - mark as inactive)"""
    db_category = db.query(BudgetCategory).filter(BudgetCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # USER can only delete categories from their department
    # Return 404 instead of 403 to prevent information disclosure
    if current_user.role == UserRoleEnum.USER:
        if db_category.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )

    # Hard delete - permanently remove from database
    db.delete(db_category)
    db.commit()
    cache_service.invalidate_namespace(CACHE_NAMESPACE)
    return None


@router.post("/bulk/update", status_code=status.HTTP_200_OK)
def bulk_update_categories(
    request: BulkUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk update categories (activate/deactivate)"""
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No category IDs provided"
        )

    query = db.query(BudgetCategory).filter(BudgetCategory.id.in_(request.ids))

    # USER can only update categories from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetCategory.department_id == current_user.department_id)

    categories = query.all()

    if len(categories) != len(request.ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some categories not found or not accessible"
        )

    updated_count = 0
    if request.is_active is not None:
        for category in categories:
            category.is_active = request.is_active
            updated_count += 1

    db.commit()
    cache_service.invalidate_namespace(CACHE_NAMESPACE)

    return {
        "message": f"Successfully updated {updated_count} categories",
        "updated_count": updated_count
    }


@router.post("/bulk/delete", status_code=status.HTTP_200_OK)
def bulk_delete_categories(
    request: BulkDeleteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Bulk delete categories (soft delete - mark as inactive)"""
    if not request.ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No category IDs provided"
        )

    query = db.query(BudgetCategory).filter(BudgetCategory.id.in_(request.ids))

    # USER can only delete categories from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetCategory.department_id == current_user.department_id)

    categories = query.all()

    # Validate all requested categories were found and accessible
    if len(categories) != len(request.ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some categories not found or not accessible"
        )

    deleted_count = 0
    for category in categories:
        db.delete(category)
        deleted_count += 1

    db.commit()
    cache_service.invalidate_namespace(CACHE_NAMESPACE)

    return {
        "message": f"Successfully deleted {deleted_count} categories",
        "deleted_count": deleted_count
    }


@router.get("/export", response_class=StreamingResponse)
def export_categories(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Export all categories to Excel"""
    query = db.query(BudgetCategory)

    # USER can only export categories from their department
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(BudgetCategory.department_id == current_user.department_id)

    categories = query.all()

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
async def import_categories(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import categories from Excel file

    All imported categories are assigned to the user's department
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
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    try:
        # Read Excel file
        log_info(f"Starting categories import from {file.filename}", "Import")
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
        required_columns = ['Название', 'Тип']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {', '.join(missing_columns)}. Found columns: {', '.join(df.columns)}"
            )

        created_count = 0
        updated_count = 0
        errors = []
        total_rows = len(df)

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

                # Determine department_id for import
                import_department_id = current_user.department_id

                # Check if category exists within the same department
                existing = db.query(BudgetCategory).filter(
                    BudgetCategory.name == name,
                    BudgetCategory.department_id == import_department_id
                ).first()

                if existing:
                    # Update existing
                    existing.type = type_val
                    existing.description = str(row.get('Описание', '')) if pd.notna(row.get('Описание')) else None
                    existing.is_active = str(row.get('Активна', 'Да')).strip().lower() in ['да', 'yes', '1', 'true']
                    updated_count += 1
                else:
                    # Create new with department_id
                    new_category = BudgetCategory(
                        name=name,
                        type=type_val,
                        description=str(row.get('Описание', '')) if pd.notna(row.get('Описание')) else None,
                        is_active=str(row.get('Активна', 'Да')).strip().lower() in ['да', 'yes', '1', 'true'],
                        department_id=import_department_id
                    )
                    db.add(new_category)
                    created_count += 1

            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")

        db.commit()
        cache_service.invalidate_namespace(CACHE_NAMESPACE)

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
