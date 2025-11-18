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
from app.utils.excel_export import encode_filename_header
from app.db.models import (
    APIToken,
    APITokenScopeEnum,
    Expense,
    BudgetCategory,
    Contractor,
    Organization,
    Employee,
    EmployeeStatusEnum,
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


@router.get(
    "/export/expenses",
    summary="Экспорт расходов",
    description="""
    Экспортирует данные о расходах в формате JSON или CSV.

    **Требуемый scope:** READ

    **Фильтры:**
    - `year` - Фильтр по году (например, 2025)
    - `month` - Фильтр по месяцу (1-12)
    - `format` - Формат вывода: `json` (по умолчанию) или `csv`

    **Изоляция по департаментам:**
    Возвращает только расходы департамента, к которому привязан API токен.

    **Примеры использования:**
    ```bash
    # JSON формат
    curl -X GET "http://localhost:8000/api/v1/external/export/expenses?year=2025&format=json" \\
      -H "Authorization: Bearer itb_your_token_here"

    # CSV формат
    curl -X GET "http://localhost:8000/api/v1/external/export/expenses?year=2025&month=1&format=csv" \\
      -H "Authorization: Bearer itb_your_token_here" -o expenses.csv
    ```
    """,
    responses={
        200: {
            "description": "Успешный экспорт данных",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "amount": 50000.00,
                                "category_id": 1,
                                "contractor_id": 5,
                                "organization_id": 2,
                                "description": "Закупка серверного оборудования",
                                "request_date": "2025-01-15",
                                "payment_date": "2025-01-20",
                                "status": "APPROVED",
                                "department_id": 1
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        401: {"description": "Отсутствует или недействителен API токен"},
        403: {"description": "У токена нет READ scope"}
    },
    tags=["External API - Экспорт"]
)
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


@router.get(
    "/export/revenue-actuals",
    summary="Экспорт фактических доходов",
    description="""
    Экспортирует данные о фактических доходах в формате JSON или CSV.

    **Требуемый scope:** READ

    **Фильтры:**
    - `year` - Фильтр по году (например, 2025)
    - `month` - Фильтр по месяцу (1-12)
    - `format` - Формат вывода: `json` (по умолчанию) или `csv`

    **Изоляция по департаментам:**
    Возвращает только доходы департамента, к которому привязан API токен.

    **Пример ответа включает:**
    - `year`, `month` - Период
    - `revenue_stream_id` - ID потока доходов
    - `revenue_category_id` - ID категории доходов
    - `planned_amount` - Плановая сумма
    - `actual_amount` - Фактическая сумма
    - `variance` - Отклонение (actual - planned)
    - `variance_percent` - Отклонение в процентах
    """,
    responses={
        200: {
            "description": "Успешный экспорт данных",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "year": 2025,
                                "month": 1,
                                "revenue_stream_id": 1,
                                "revenue_category_id": 1,
                                "planned_amount": 95000.00,
                                "actual_amount": 100000.00,
                                "variance": 5000.00,
                                "variance_percent": 5.26,
                                "department_id": 1
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        401: {"description": "Отсутствует или недействителен API токен"},
        403: {"description": "У токена нет READ scope"}
    },
    tags=["External API - Экспорт"]
)
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


@router.get(
    "/export/budget-plans",
    summary="Экспорт планов бюджета",
    description="""
    Экспортирует данные о планах бюджета в формате JSON.

    **Требуемый scope:** READ

    **Фильтры:**
    - `year` - Фильтр по году (например, 2025)
    - `format` - Формат вывода (только `json` поддерживается)

    **Изоляция по департаментам:**
    Возвращает только планы департамента, к которому привязан API токен.

    **Пример использования:**
    ```bash
    curl -X GET "http://localhost:8000/api/v1/external/export/budget-plans?year=2025" \\
      -H "Authorization: Bearer itb_your_token_here"
    ```
    """,
    responses={
        200: {
            "description": "Успешный экспорт данных",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "year": 2025,
                                "month": 1,
                                "category_id": 1,
                                "planned_amount": 150000.00,
                                "department_id": 1
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        401: {"description": "Отсутствует или недействителен API токен"},
        403: {"description": "У токена нет READ scope"}
    },
    tags=["External API - Экспорт"]
)
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


@router.get(
    "/export/employees",
    summary="Экспорт сотрудников",
    description="""
    Экспортирует данные о сотрудниках в формате JSON.

    **Требуемый scope:** READ

    **Особенности:**
    - Экспортируются только активные сотрудники (`is_active = true`)
    - Данные автоматически фильтруются по департаменту токена

    **Пример ответа включает:**
    - `id` - ID сотрудника
    - `full_name` - Полное имя
    - `position` - Должность
    - `base_salary` - Базовый оклад
    - `hire_date` - Дата найма
    - `department_id` - ID департамента
    - `is_active` - Статус активности
    """,
    responses={
        200: {
            "description": "Успешный экспорт данных",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "full_name": "Иванов Иван Иванович",
                                "position": "Системный администратор",
                                "base_salary": 120000.00,
                                "hire_date": "2023-01-15",
                                "department_id": 1,
                                "is_active": True
                            }
                        ],
                        "count": 1
                    }
                }
            }
        },
        401: {"description": "Отсутствует или недействителен API токен"},
        403: {"description": "У токена нет READ scope"}
    },
    tags=["External API - Экспорт"]
)
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

    query = db.query(Employee).filter(Employee.status == EmployeeStatusEnum.ACTIVE)

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
            "is_active": emp.status == EmployeeStatusEnum.ACTIVE,
        })

    return {"data": data, "count": len(data)}


# ============================================================================
# Generic Data Import Endpoints
# ============================================================================


@router.post(
    "/import/revenue-actuals",
    summary="Массовый импорт фактических доходов",
    description="""
    Импортирует фактические доходы с автоматическим расчетом отклонений.

    **Требуемый scope:** WRITE

    **Формат данных:**
    ```json
    [
        {
            "year": 2025,
            "month": 1,
            "revenue_stream_id": 1,
            "revenue_category_id": 1,
            "actual_amount": 100000.00,
            "planned_amount": 95000.00
        }
    ]
    ```

    **Автоматические расчеты:**
    - `variance` = actual_amount - planned_amount
    - `variance_percent` = (variance / planned_amount) * 100
    - `department_id` = из токена

    **Обязательные поля:**
    - `year`, `month` - Период
    - `revenue_stream_id` - ID потока доходов
    - `revenue_category_id` - ID категории
    - `actual_amount` - Фактическая сумма

    **Опциональные поля:**
    - `planned_amount` - Плановая сумма (для расчета отклонений)
    """,
    responses={
        200: {
            "description": "Импорт завершен",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "created_count": 12,
                        "error_count": 0,
                        "errors": []
                    }
                }
            }
        },
        400: {"description": "Данные не предоставлены"},
        401: {"description": "Недействительный токен"},
        403: {"description": "Требуется WRITE scope"}
    },
    tags=["External API - Импорт"]
)
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


@router.post(
    "/import/expenses",
    summary="Массовый импорт расходов",
    description="""
    Импортирует несколько записей расходов за один запрос.

    **Требуемый scope:** WRITE

    **Формат данных:**
    ```json
    [
        {
            "amount": 10000.00,
            "category_id": 1,
            "contractor_id": 1,
            "organization_id": 1,
            "description": "Закупка оборудования",
            "request_date": "2025-01-15",
            "payment_date": "2025-01-20",
            "status": "DRAFT"
        }
    ]
    ```

    **Особенности:**
    - `department_id` автоматически назначается из токена
    - Даты принимаются в ISO формате (YYYY-MM-DD)
    - Частичный успех: продолжает импорт при ошибках в отдельных записях
    - Возвращает список ошибок с индексами и описаниями

    **Обязательные поля:**
    - `amount` - Сумма (должна быть больше 0)
    - `category_id` - ID категории бюджета
    - `request_date` - Дата запроса

    **Опциональные поля:**
    - `contractor_id` - ID контрагента
    - `organization_id` - ID организации
    - `description` - Описание
    - `payment_date` - Дата оплаты
    - `status` - Статус (DRAFT, PENDING, APPROVED, REJECTED, PAID)

    **Пример использования:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/external/import/expenses" \\
      -H "Authorization: Bearer itb_your_token_here" \\
      -H "Content-Type: application/json" \\
      -d '[{"amount": 50000, "category_id": 1, "contractor_id": 5, "description": "Серверы", "request_date": "2025-01-15", "status": "DRAFT"}]'
    ```
    """,
    responses={
        200: {
            "description": "Импорт завершен (возможны частичные ошибки)",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "created_count": 45,
                        "error_count": 2,
                        "errors": [
                            {
                                "index": 15,
                                "error": "category_id: invalid foreign key",
                                "data": {"amount": 1000, "category_id": 999}
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Данные не предоставлены или неверный формат"},
        401: {"description": "Отсутствует или недействителен API токен"},
        403: {"description": "У токена нет WRITE scope"},
        500: {"description": "Ошибка при сохранении в базу данных"}
    },
    tags=["External API - Импорт"]
)
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


@router.get(
    "/reference/categories",
    summary="Справочник категорий бюджета",
    description="Получить список всех активных категорий бюджета (OPEX/CAPEX). **Требуемый scope:** READ",
    tags=["External API - Справочники"]
)
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


@router.get(
    "/reference/contractors",
    summary="Справочник контрагентов",
    description="Получить список всех активных контрагентов (поставщики, подрядчики). **Требуемый scope:** READ",
    tags=["External API - Справочники"]
)
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


@router.get(
    "/reference/revenue-streams",
    summary="Справочник потоков доходов",
    description="Получить список всех активных потоков доходов. **Требуемый scope:** READ",
    tags=["External API - Справочники"]
)
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


@router.get(
    "/reference/revenue-categories",
    summary="Справочник категорий доходов",
    description="Получить список всех активных категорий доходов. **Требуемый scope:** READ",
    tags=["External API - Справочники"]
)
async def get_revenue_categories(
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """Get all revenue categories (READ scope)"""
    check_read_access(token)

    query = db.query(RevenueCategory).filter(RevenueCategory.is_active == True)

    if token.department_id:
        query = query.filter(RevenueCategory.department_id == token.department_id)

    categories = query.all()

    return {
        "data": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "department_id": c.department_id,
            }
            for c in categories
        ]
    }


@router.get(
    "/reference/organizations",
    summary="Справочник организаций",
    description="Получить список всех активных организаций (юридических лиц). **Требуемый scope:** READ",
    tags=["External API - Справочники"]
)
async def get_organizations(
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """Get all organizations (READ scope)"""
    check_read_access(token)

    query = db.query(Organization).filter(Organization.is_active == True)

    if token.department_id:
        query = query.filter(Organization.department_id == token.department_id)

    orgs = query.all()

    return {
        "data": [
            {
                "id": o.id,
                "name": o.name,
                "legal_name": o.legal_name,
                "inn": o.inn,
                "kpp": o.kpp,
                "department_id": o.department_id,
            }
            for o in orgs
        ]
    }


# ============================================================================
# Additional Import Endpoints
# ============================================================================


@router.post(
    "/import/contractors",
    summary="Импорт/обновление контрагентов",
    description="""
    Массовый импорт контрагентов с поддержкой upsert (создание или обновление по ИНН).

    **Требуемый scope:** WRITE

    **Логика upsert:**
    - Если контрагент с таким ИНН существует → обновление
    - Если не существует → создание нового

    **Обязательные поля:**
    - `name` - Название контрагента
    - `inn` - ИНН (используется для поиска дубликатов)

    **Опциональные поля:**
    - `contact_person`, `email`, `phone`, `address`
    """,
    responses={
        200: {
            "description": "Импорт завершен",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "created_count": 5,
                        "updated_count": 3,
                        "error_count": 0,
                        "errors": []
                    }
                }
            }
        }
    },
    tags=["External API - Импорт"]
)
async def import_contractors(
    data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Import contractors data in bulk

    Requires: WRITE scope

    Data format:
    [
        {
            "name": "ООО Поставщик",
            "inn": "1234567890",
            "contact_person": "Иванов И.И.",
            "email": "contact@supplier.ru",
            "phone": "+7 (495) 123-45-67"
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
    updated_count = 0
    errors = []

    for idx, item in enumerate(data):
        try:
            # Auto-assign department from token
            item["department_id"] = token.department_id

            # Check if contractor exists by INN
            existing = None
            if item.get("inn"):
                existing = db.query(Contractor).filter(
                    Contractor.inn == item["inn"],
                    Contractor.department_id == token.department_id
                ).first()

            if existing:
                # Update existing
                for key, value in item.items():
                    if key != "id":
                        setattr(existing, key, value)
                updated_count += 1
            else:
                # Create new
                contractor = Contractor(**item)
                db.add(contractor)
                created_count += 1

        except Exception as e:
            errors.append({"index": idx, "error": str(e), "data": item})
            log_error(f"Error importing contractor at index {idx}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {str(e)}"
        )

    log_info(
        f"External API: Imported {created_count} contractors, updated {updated_count} ({len(errors)} errors)",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    return {
        "success": True,
        "created_count": created_count,
        "updated_count": updated_count,
        "error_count": len(errors),
        "errors": errors
    }


@router.post(
    "/import/organizations",
    summary="Импорт/обновление организаций",
    description="""
    Массовый импорт организаций с upsert по ИНН.

    **Требуемый scope:** WRITE

    **Обязательные поля:**  `name`, `inn`

    **Опциональные поля:** `legal_name`, `kpp`, `address`
    """,
    tags=["External API - Импорт"]
)
async def import_organizations(
    data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Import organizations data in bulk

    Requires: WRITE scope

    Data format:
    [
        {
            "name": "ООО Компания",
            "legal_name": "Общество с ограниченной ответственностью Компания",
            "inn": "1234567890",
            "kpp": "123456789"
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
    updated_count = 0
    errors = []

    for idx, item in enumerate(data):
        try:
            # Auto-assign department from token
            item["department_id"] = token.department_id

            # Check if organization exists by INN
            existing = None
            if item.get("inn"):
                existing = db.query(Organization).filter(
                    Organization.inn == item["inn"],
                    Organization.department_id == token.department_id
                ).first()

            if existing:
                # Update existing
                for key, value in item.items():
                    if key != "id":
                        setattr(existing, key, value)
                updated_count += 1
            else:
                # Create new
                org = Organization(**item)
                db.add(org)
                created_count += 1

        except Exception as e:
            errors.append({"index": idx, "error": str(e), "data": item})
            log_error(f"Error importing organization at index {idx}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {str(e)}"
        )

    log_info(
        f"External API: Imported {created_count} organizations, updated {updated_count} ({len(errors)} errors)",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    return {
        "success": True,
        "created_count": created_count,
        "updated_count": updated_count,
        "error_count": len(errors),
        "errors": errors
    }


@router.post(
    "/import/budget-categories",
    summary="Импорт/обновление категорий бюджета",
    description="""
    Массовый импорт категорий бюджета с upsert по названию.

    **Требуемый scope:** WRITE

    **Обязательные поля:** `name`, `category_type` (OPEX или CAPEX)

    **Опциональные поля:** `description`
    """,
    tags=["External API - Импорт"]
)
async def import_budget_categories(
    data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Import budget categories data in bulk

    Requires: WRITE scope

    Data format:
    [
        {
            "name": "Оборудование",
            "category_type": "CAPEX",
            "description": "Закупка оборудования"
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
    updated_count = 0
    errors = []

    for idx, item in enumerate(data):
        try:
            # Auto-assign department from token
            item["department_id"] = token.department_id

            # Check if category exists by name
            existing = db.query(BudgetCategory).filter(
                BudgetCategory.name == item["name"],
                BudgetCategory.department_id == token.department_id
            ).first()

            if existing:
                # Update existing
                for key, value in item.items():
                    if key != "id":
                        setattr(existing, key, value)
                updated_count += 1
            else:
                # Create new
                category = BudgetCategory(**item)
                db.add(category)
                created_count += 1

        except Exception as e:
            errors.append({"index": idx, "error": str(e), "data": item})
            log_error(f"Error importing budget category at index {idx}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {str(e)}"
        )

    log_info(
        f"External API: Imported {created_count} budget categories, updated {updated_count} ({len(errors)} errors)",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    return {
        "success": True,
        "created_count": created_count,
        "updated_count": updated_count,
        "error_count": len(errors),
        "errors": errors
    }


@router.post(
    "/import/payroll-plans",
    summary="Импорт/обновление планов ФОТ",
    description="""
    Массовый импорт планов фонда оплаты труда с upsert по (year, month, employee_id).

    **Требуемый scope:** WRITE

    **Обязательные поля:** `year`, `month`, `employee_id`, `base_salary`

    **Опциональные поля:** `bonus_type`, `bonus_amount`, `social_contributions`

    **Типы бонусов:** FIXED, PERFORMANCE_BASED, MIXED
    """,
    tags=["External API - Импорт"]
)
async def import_payroll_plans(
    data: List[Dict[str, Any]],
    db: Session = Depends(get_db),
    token: APIToken = Depends(verify_api_token_dependency)
):
    """
    Import payroll plans data in bulk

    Requires: WRITE scope

    Data format:
    [
        {
            "year": 2025,
            "month": 1,
            "employee_id": 1,
            "base_salary": 100000.00,
            "bonus_type": "FIXED",
            "bonus_amount": 20000.00,
            "social_contributions": 30000.00
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
    updated_count = 0
    errors = []

    for idx, item in enumerate(data):
        try:
            # Auto-assign department from token
            item["department_id"] = token.department_id

            # Check if payroll plan exists
            existing = db.query(PayrollPlan).filter(
                PayrollPlan.year == item["year"],
                PayrollPlan.month == item["month"],
                PayrollPlan.employee_id == item["employee_id"],
                PayrollPlan.department_id == token.department_id
            ).first()

            if existing:
                # Update existing
                for key, value in item.items():
                    if key != "id":
                        setattr(existing, key, value)
                updated_count += 1
            else:
                # Create new
                plan = PayrollPlan(**item)
                db.add(plan)
                created_count += 1

        except Exception as e:
            errors.append({"index": idx, "error": str(e), "data": item})
            log_error(f"Error importing payroll plan at index {idx}: {str(e)}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to commit data: {str(e)}"
        )

    log_info(
        f"External API: Imported {created_count} payroll plans, updated {updated_count} ({len(errors)} errors)",
        context=f"Token: {token.name} (ID: {token.id})"
    )

    return {
        "success": True,
        "created_count": created_count,
        "updated_count": updated_count,
        "error_count": len(errors),
        "errors": errors
    }


@router.get(
    "/health",
    summary="Проверка работоспособности API",
    description="Публичный эндпоинт для проверки доступности External API. **Не требует авторизации.**",
    tags=["External API - Служебное"]
)
async def health_check():
    """Public health check endpoint"""
    return {"status": "ok", "service": "IT Budget Manager External API"}
