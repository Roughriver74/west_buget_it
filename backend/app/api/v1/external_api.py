"""
External API endpoints for data import/export

Provides token-based authentication for external systems to upload and download data.
Supports all major entities: expenses, revenues, budgets, payroll, etc.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import io
import json

from app.db import get_db
from app.db.models import (
    APIToken,
    APITokenScopeEnum,
    Expense,
    BudgetCategory,
    Contractor,
    Organization,
    Employee,
    PayrollPlan,
    PayrollActual,
    BudgetPlan,
    RevenueActual,
    RevenuePlan,
    RevenueStream,
    RevenueCategory,
)
from app.schemas import (
    ExpenseCreate,
    ExpenseInDB,
    BudgetCategoryCreate,
    ContractorCreate,
    OrganizationCreate,
    EmployeeCreate,
    RevenueActualCreate,
)
from app.utils.api_token import check_token_scope
from app.utils.logger import log_info, log_warning, log_error
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer()


async def verify_api_token_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> APIToken:
    """Dependency to verify API token with database session"""
    from app.utils.api_token import verify_api_token
    return await verify_api_token(credentials, db)


def check_read_access(token: APIToken):
    """Check if token has READ access"""
    if not check_token_scope(token, APITokenScopeEnum.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token requires READ scope"
        )


def check_write_access(token: APIToken):
    """Check if token has WRITE access"""
    if not check_token_scope(token, APITokenScopeEnum.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token requires WRITE scope"
        )


# ============================================================================
# Generic Data Export Endpoints
# ============================================================================


@router.get("/export/expenses")
async def export_expenses(
    year: Optional[int] = None,
    month: Optional[int] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Export expenses data

    Requires: READ scope
    """
    check_read_access(token)

    query = db.query(Expense)

    # Department isolation
    if token.department_id:
        query = query.filter(Expense.department_id == token.department_id)

    # Filters
    if year:
        query = query.filter(Expense.request_date.year == year)
    if month:
        query = query.filter(Expense.request_date.month == month)

    expenses = query.all()

    log_info(
        f"External API: Exported {len(expenses)} expenses",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    if format == "csv":
        # CSV export
        import csv
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "id", "amount", "category_id", "contractor_id", "organization_id",
            "description", "request_date", "payment_date", "status", "department_id"
        ])

        # Data
        for expense in expenses:
            writer.writerow([
                expense.id,
                float(expense.amount),
                expense.category_id,
                expense.contractor_id,
                expense.organization_id,
                expense.description,
                expense.request_date.isoformat() if expense.request_date else None,
                expense.payment_date.isoformat() if expense.payment_date else None,
                expense.status.value,
                expense.department_id,
            ])

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=expenses_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    else:
        # JSON export
        data = []
        for expense in expenses:
            data.append({
                "id": expense.id,
                "amount": float(expense.amount),
                "category_id": expense.category_id,
                "contractor_id": expense.contractor_id,
                "organization_id": expense.organization_id,
                "description": expense.description,
                "request_date": expense.request_date.isoformat() if expense.request_date else None,
                "payment_date": expense.payment_date.isoformat() if expense.payment_date else None,
                "status": expense.status.value,
                "department_id": expense.department_id,
            })

        return {"data": data, "count": len(data)}


@router.get("/export/revenue-actuals")
async def export_revenue_actuals(
    year: Optional[int] = None,
    month: Optional[int] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Export revenue actuals data

    Requires: READ scope
    """
    check_read_access(token)

    query = db.query(RevenueActual)

    # Department isolation
    if token.department_id:
        query = query.filter(RevenueActual.department_id == token.department_id)

    # Filters
    if year:
        query = query.filter(RevenueActual.year == year)
    if month:
        query = query.filter(RevenueActual.month == month)

    actuals = query.all()

    log_info(
        f"External API: Exported {len(actuals)} revenue actuals",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    if format == "csv":
        # CSV export
        import csv
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "id", "year", "month", "revenue_stream_id", "revenue_category_id",
            "planned_amount", "actual_amount", "variance", "variance_percent", "department_id"
        ])

        # Data
        for actual in actuals:
            writer.writerow([
                actual.id,
                actual.year,
                actual.month,
                actual.revenue_stream_id,
                actual.revenue_category_id,
                float(actual.planned_amount) if actual.planned_amount else None,
                float(actual.actual_amount),
                float(actual.variance) if actual.variance else None,
                float(actual.variance_percent) if actual.variance_percent else None,
                actual.department_id,
            ])

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=revenue_actuals_{datetime.now().strftime('%Y%m%d')}.csv"}
        )
    else:
        # JSON export
        data = []
        for actual in actuals:
            data.append({
                "id": actual.id,
                "year": actual.year,
                "month": actual.month,
                "revenue_stream_id": actual.revenue_stream_id,
                "revenue_category_id": actual.revenue_category_id,
                "planned_amount": float(actual.planned_amount) if actual.planned_amount else None,
                "actual_amount": float(actual.actual_amount),
                "variance": float(actual.variance) if actual.variance else None,
                "variance_percent": float(actual.variance_percent) if actual.variance_percent else None,
                "department_id": actual.department_id,
            })

        return {"data": data, "count": len(data)}


@router.get("/export/budget-plans")
async def export_budget_plans(
    year: Optional[int] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Export budget plans data

    Requires: READ scope
    """
    check_read_access(token)

    query = db.query(BudgetPlan)

    # Department isolation
    if token.department_id:
        query = query.filter(BudgetPlan.department_id == token.department_id)

    # Filters
    if year:
        query = query.filter(BudgetPlan.year == year)

    plans = query.all()

    log_info(
        f"External API: Exported {len(plans)} budget plans",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    data = []
    for plan in plans:
        data.append({
            "id": plan.id,
            "year": plan.year,
            "month": plan.month,
            "category_id": plan.category_id,
            "planned_amount": float(plan.planned_amount),
            "department_id": plan.department_id,
        })

    return {"data": data, "count": len(data)}


@router.get("/export/employees")
async def export_employees(
    format: str = Query("json", regex="^(json|csv)$"),
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Export employees data

    Requires: READ scope
    """
    check_read_access(token)

    query = db.query(Employee).filter(Employee.is_active == True)

    # Department isolation
    if token.department_id:
        query = query.filter(Employee.department_id == token.department_id)

    employees = query.all()

    log_info(
        f"External API: Exported {len(employees)} employees",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    data = []
    for emp in employees:
        data.append({
            "id": emp.id,
            "full_name": emp.full_name,
            "position": emp.position,
            "base_salary": float(emp.base_salary),
            "hire_date": emp.hire_date.isoformat() if emp.hire_date else None,
            "department_id": emp.department_id,
            "is_active": emp.is_active,
        })

    return {"data": data, "count": len(data)}


# ============================================================================
# Generic Data Import Endpoints
# ============================================================================


@router.post("/import/revenue-actuals")
async def import_revenue_actuals(
    data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Import revenue actuals data in bulk

    Requires: WRITE scope

    Data format:
    [
        {
            "year": 2025,
            "month": 1,
            "revenue_stream_id": 1,
            "revenue_category_id": 1,
            "actual_amount": 100000.00,
            "planned_amount": 95000.00
        },
        ...
    ]
    """
    check_write_access(token)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided"
        )

    created_count = 0
    errors = []

    for idx, item in enumerate(data):
        try:
            # Auto-assign department from token
            item["department_id"] = token.department_id

            # Create RevenueActual
            actual = RevenueActual(**item, created_by=token.created_by)

            # Calculate variance
            if actual.planned_amount is not None and actual.planned_amount != 0:
                actual.variance = actual.actual_amount - actual.planned_amount
                actual.variance_percent = (actual.variance / actual.planned_amount) * 100

            db.add(actual)
            created_count += 1

        except Exception as e:
            errors.append({"index": idx, "error": str(e), "data": item})
            log_error(f"Error importing revenue actual at index {idx}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {str(e)}"
        )

    log_info(
        f"External API: Imported {created_count} revenue actuals ({len(errors)} errors)",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    return {
        "success": True,
        "created_count": created_count,
        "error_count": len(errors),
        "errors": errors
    }


@router.post("/import/expenses")
async def import_expenses(
    data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Import expenses data in bulk

    Requires: WRITE scope

    Data format:
    [
        {
            "amount": 10000.00,
            "category_id": 1,
            "contractor_id": 1,
            "organization_id": 1,
            "description": "Equipment purchase",
            "request_date": "2025-01-15",
            "status": "DRAFT"
        },
        ...
    ]
    """
    check_write_access(token)

    if not data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data provided"
        )

    created_count = 0
    errors = []

    for idx, item in enumerate(data):
        try:
            # Auto-assign department from token
            item["department_id"] = token.department_id

            # Parse dates
            if "request_date" in item and isinstance(item["request_date"], str):
                item["request_date"] = datetime.fromisoformat(item["request_date"])
            if "payment_date" in item and isinstance(item["payment_date"], str):
                item["payment_date"] = datetime.fromisoformat(item["payment_date"])

            # Create Expense
            expense = Expense(**item, created_by=token.created_by)
            db.add(expense)
            created_count += 1

        except Exception as e:
            errors.append({"index": idx, "error": str(e), "data": item})
            log_error(f"Error importing expense at index {idx}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {str(e)}"
        )

    log_info(
        f"External API: Imported {created_count} expenses ({len(errors)} errors)",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    return {
        "success": True,
        "created_count": created_count,
        "error_count": len(errors),
        "errors": errors
    }


# ============================================================================
# Reference Data Endpoints
# ============================================================================


@router.get("/reference/categories")
async def get_categories(
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """Get all budget categories (READ scope)"""
    check_read_access(token)

    query = db.query(BudgetCategory).filter(BudgetCategory.is_active == True)

    if token.department_id:
        query = query.filter(BudgetCategory.department_id == token.department_id)

    categories = query.all()

    return {
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "category_type": c.category_type.value,
                "department_id": c.department_id,
            }
            for c in categories
        ]
    }


@router.get("/reference/contractors")
async def get_contractors(
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """Get all contractors (READ scope)"""
    check_read_access(token)

    query = db.query(Contractor).filter(Contractor.is_active == True)

    if token.department_id:
        query = query.filter(Contractor.department_id == token.department_id)

    contractors = query.all()

    return {
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "inn": c.inn,
                "department_id": c.department_id,
            }
            for c in contractors
        ]
    }


@router.get("/reference/revenue-streams")
async def get_revenue_streams(
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """Get all revenue streams (READ scope)"""
    check_read_access(token)

    query = db.query(RevenueStream).filter(RevenueStream.is_active == True)

    if token.department_id:
        query = query.filter(RevenueStream.department_id == token.department_id)

    streams = query.all()

    return {
        "data": [
            {
                "id": s.id,
                "name": s.name,
                "stream_type": s.stream_type.value,
                "department_id": s.department_id,
            }
            for s in streams
        ]
    }


@router.get("/health")
async def health_check():
    """Public health check endpoint"""
    return {"status": "ok", "service": "IT Budget Manager External API"}
