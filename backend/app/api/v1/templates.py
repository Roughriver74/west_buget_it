"""
Templates API endpoints
Provides Excel templates for import functionality
"""
import os
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# Templates directory
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

# Available templates
TEMPLATES = {
    "categories": "template_categories.xlsx",
    "contractors": "template_contractors.xlsx",
    "organizations": "template_organizations.xlsx",
    "payroll_plans": "template_payroll_plans.xlsx",
    "kpi": "template_kpi.xlsx",
}


@router.get("/list")
async def list_templates():
    """
    Get list of available Excel templates

    Returns list of template types with metadata
    """
    templates_info = []

    for template_type, filename in TEMPLATES.items():
        file_path = TEMPLATES_DIR / filename

        if file_path.exists():
            file_size = file_path.stat().st_size
            templates_info.append({
                "type": template_type,
                "filename": filename,
                "size": file_size,
                "available": True
            })
        else:
            templates_info.append({
                "type": template_type,
                "filename": filename,
                "size": 0,
                "available": False
            })

    return {
        "templates": templates_info,
        "count": len(templates_info)
    }


@router.get("/download/{template_type}")
async def download_template(template_type: str):
    """
    Download Excel template by type

    Available types:
    - categories: Budget categories import template
    - contractors: Contractors import template
    - organizations: Organizations import template
    - payroll_plans: Payroll plans import template
    - kpi: KPI data import template
    """
    if template_type not in TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template type '{template_type}' not found. Available types: {', '.join(TEMPLATES.keys())}"
        )

    filename = TEMPLATES[template_type]
    file_path = TEMPLATES_DIR / filename

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template file '{filename}' not found on server"
        )

    # Friendly download names
    download_names = {
        "categories": "Шаблон_Категории.xlsx",
        "contractors": "Шаблон_Контрагенты.xlsx",
        "organizations": "Шаблон_Организации.xlsx",
        "payroll_plans": "Шаблон_План_ФОТ.xlsx",
        "kpi": "Шаблон_КПИ.xlsx",
    }

    return FileResponse(
        path=file_path,
        filename=download_names.get(template_type, filename),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
