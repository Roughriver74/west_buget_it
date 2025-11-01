"""
Unified Import API

Single endpoint for importing any entity with preview and validation.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json

from app.db.session import get_db
from app.api.v1.auth import get_current_active_user
from app.db.models import User
from app.services.unified_import_service import UnifiedImportService
from app.services.template_generator import get_template_generator

router = APIRouter()


@router.get("/entities")
def get_available_entities(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of entities available for import

    Returns entity information including fields and requirements.
    """
    service = UnifiedImportService(db, current_user)
    entities = service.get_available_entities()

    return {
        "success": True,
        "entities": entities
    }


@router.post("/preview")
async def preview_import(
    entity_type: str = Form(...),
    file: UploadFile = File(...),
    sheet_name: Optional[str] = Form(None),
    header_row: int = Form(0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Preview import file

    Analyzes Excel file and suggests column mapping.

    **Parameters:**
    - `entity_type`: Type of entity to import (e.g., "employees", "contractors")
    - `file`: Excel file to import
    - `sheet_name`: Sheet name or index (optional, default: first sheet)
    - `header_row`: Row index for column headers (default: 0)

    **Returns:**
    - File structure analysis
    - Detected data types for each column
    - Suggested column mapping
    - Preview of first rows
    - Required fields for entity
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")

    # Read file content
    content = await file.read()

    # Parse sheet_name
    sheet = sheet_name
    if sheet_name and sheet_name.isdigit():
        sheet = int(sheet_name)

    # Preview
    service = UnifiedImportService(db, current_user)
    result = service.preview_import(
        entity_type=entity_type,
        file_content=content,
        sheet_name=sheet if sheet is not None else 0,
        header_row=header_row
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Preview failed"))

    return result


@router.post("/validate")
async def validate_import(
    entity_type: str = Form(...),
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    header_row: int = Form(0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Validate import data without saving

    **Parameters:**
    - `entity_type`: Type of entity to import
    - `file`: Excel file to import
    - `column_mapping`: JSON string mapping Excel columns to entity fields
      Example: `{"Название": "name", "ИНН": "inn"}`
    - `sheet_name`: Sheet name or index (optional)
    - `header_row`: Row index for headers (default: 0)

    **Returns:**
    - Validation results with errors and warnings
    - Statistics about valid/invalid rows
    - Preview of mapped data
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")

    # Parse column mapping
    try:
        mapping_dict = json.loads(column_mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid column_mapping JSON")

    # Read file
    content = await file.read()

    # Parse sheet_name
    sheet = sheet_name
    if sheet_name and sheet_name.isdigit():
        sheet = int(sheet_name)

    # Validate
    service = UnifiedImportService(db, current_user)
    result = service.validate_import(
        entity_type=entity_type,
        file_content=content,
        column_mapping=mapping_dict,
        sheet_name=sheet if sheet is not None else 0,
        header_row=header_row
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Validation failed"))

    return result


@router.post("/execute")
async def execute_import(
    entity_type: str = Form(...),
    file: UploadFile = File(...),
    column_mapping: str = Form(...),
    sheet_name: Optional[str] = Form(None),
    header_row: int = Form(0),
    skip_errors: bool = Form(False),
    dry_run: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Execute import and save to database

    **Parameters:**
    - `entity_type`: Type of entity to import
    - `file`: Excel file to import
    - `column_mapping`: JSON string mapping Excel columns to entity fields
    - `sheet_name`: Sheet name or index (optional)
    - `header_row`: Row index for headers (default: 0)
    - `skip_errors`: Skip rows with errors and import valid rows only (default: False)
    - `dry_run`: Validate only without saving (default: False)

    **Returns:**
    - Import statistics (created, updated, skipped)
    - List of errors if any
    - Validation results
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are supported")

    # Parse column mapping
    try:
        mapping_dict = json.loads(column_mapping)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid column_mapping JSON")

    # Read file
    content = await file.read()

    # Parse sheet_name
    sheet = sheet_name
    if sheet_name and sheet_name.isdigit():
        sheet = int(sheet_name)

    # Execute import
    service = UnifiedImportService(db, current_user)
    result = service.execute_import(
        entity_type=entity_type,
        file_content=content,
        column_mapping=mapping_dict,
        sheet_name=sheet if sheet is not None else 0,
        header_row=header_row,
        skip_errors=skip_errors,
        dry_run=dry_run
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Import failed"))

    return result


@router.get("/template/{entity_type}")
def download_template(
    entity_type: str,
    language: str = "ru",
    include_examples: bool = True,
    include_instructions: bool = True,
    current_user: User = Depends(get_current_active_user)
):
    """
    Download Excel template for entity

    **Parameters:**
    - `entity_type`: Type of entity (e.g., "employees", "contractors")
    - `language`: Template language ("ru" or "en", default: "ru")
    - `include_examples`: Include example rows (default: True)
    - `include_instructions`: Include instructions sheet (default: True)

    **Returns:**
    - Excel file with formatted template
    """
    generator = get_template_generator()

    # Generate template
    template_file = generator.generate_template(
        entity_type=entity_type,
        language=language,
        include_examples=include_examples,
        include_instructions=include_instructions
    )

    if not template_file:
        raise HTTPException(
            status_code=404,
            detail=f"Template not found for entity type: {entity_type}"
        )

    # Get entity display name for filename
    config_manager = generator.config_manager
    entity_info = config_manager.get_entity_info(entity_type, language)
    display_name = entity_info["display_name"] if entity_info else entity_type

    filename = f"template_{entity_type}_{language}.xlsx"

    return StreamingResponse(
        template_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Description": f"Template: {display_name}"
        }
    )
