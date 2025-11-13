"""
API endpoints for forecast management
"""
from datetime import datetime, date, timedelta
from typing import List, Optional
from decimal import Decimal
import calendar
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_, or_
from pydantic import BaseModel, Field

from app.db import get_db
from app.db.models import User, UserRoleEnum, ForecastExpense, Expense, BudgetCategory, Contractor, Organization, PayrollPlan
from app.utils.excel_export import ExcelExporter
from app.utils.auth import get_current_active_user
from app.services.ai_forecast_service import AIForecastService

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def check_department_access(current_user: User, department_id: int) -> None:
    """
    Check if user has access to the specified department.
    Raises HTTPException if access is denied.

    - USER: Can only access their own department
    - MANAGER/ADMIN: Can access any department
    """
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        if department_id != current_user.department_id:
            # Return 404 instead of 403 to prevent information disclosure
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found"
            )
    # MANAGER and ADMIN can access any department


# Helper functions for working days
def is_weekend(date_obj: date) -> bool:
    """Проверяет, является ли дата выходным днем (суббота=5, воскресенье=6)"""
    return date_obj.weekday() in (5, 6)


def get_previous_workday(date_obj: date) -> date:
    """Возвращает предыдущий рабочий день (пропускает выходные)"""
    current = date_obj
    while True:
        current = current - timedelta(days=1)
        if not is_weekend(current):
            return current


def adjust_to_workday(date_obj: date) -> date:
    """
    Переносит дату на рабочий день согласно правилам:
    - Если дата попадает на выходные (суббота или воскресенье) - переносит на предыдущий рабочий день
    - Если дата - рабочий день, оставляет как есть
    """
    # Если дата на выходные, переносим на предыдущий рабочий день
    if is_weekend(date_obj):
        return get_previous_workday(date_obj)

    return date_obj


def round_to_hundreds(amount: Decimal) -> Decimal:
    """
    Округляет сумму до сотен (например: 12345 -> 12300, 12380 -> 12400)
    """
    amount_float = float(amount)
    rounded = round(amount_float / 100) * 100
    return Decimal(str(rounded))


# Pydantic schemas
class ForecastExpenseBase(BaseModel):
    department_id: int
    category_id: int
    contractor_id: Optional[int] = None
    organization_id: int
    forecast_date: date
    amount: Decimal = Field(ge=0)
    comment: Optional[str] = None
    is_regular: bool = False
    based_on_expense_id: Optional[int] = None


class ForecastExpenseCreate(ForecastExpenseBase):
    pass


class ForecastExpenseUpdate(BaseModel):
    category_id: Optional[int] = None
    contractor_id: Optional[int] = None
    organization_id: Optional[int] = None
    forecast_date: Optional[date] = None
    amount: Optional[Decimal] = None
    comment: Optional[str] = None
    is_regular: Optional[bool] = None


class ForecastExpenseInDB(ForecastExpenseBase):
    id: int
    created_at: datetime
    updated_at: datetime

    # Include related objects
    category: Optional[dict] = None
    contractor: Optional[dict] = None
    organization: Optional[dict] = None

    class Config:
        from_attributes = True


class GenerateForecastRequest(BaseModel):
    """Request for generating forecast"""
    target_month: int = Field(ge=1, le=12)
    target_year: int
    department_id: int  # Department to generate forecast for
    include_regular: bool = True  # Включить регулярные расходы
    include_average: bool = True  # Включить средние по нерегулярным


class GenerateAIForecastRequest(BaseModel):
    """Request for generating AI-powered forecast"""
    target_month: int = Field(ge=1, le=12)
    target_year: int
    department_id: int
    category_id: Optional[int] = None  # Optional category filter for AI context


@router.post("/generate", response_model=dict)
def generate_forecast(
    request: GenerateForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate forecast for next month based on:
    1. Regular expenses (repeating monthly)
    2. Average of non-regular expenses

    - USER: Can only generate forecasts for their own department
    - MANAGER/ADMIN: Can generate forecasts for any department
    """
    # Check department access
    check_department_access(current_user, request.department_id)

    target_date = date(request.target_year, request.target_month, 1)

    # Удаляем существующий прогноз на этот месяц для этого отдела
    db.query(ForecastExpense).filter(
        ForecastExpense.department_id == request.department_id,
        extract('year', ForecastExpense.forecast_date) == request.target_year,
        extract('month', ForecastExpense.forecast_date) == request.target_month
    ).delete()

    created_count = 0

    # 1. Определяем регулярные расходы (те, что повторяются каждый месяц)
    if request.include_regular:
        # Берем расходы за последние 3 месяца
        three_months_ago = target_date - timedelta(days=90)

        # Ищем контрагентов+категории, которые встречаются в каждом из последних 3 месяцев
        regular_expenses = db.query(
            Expense.category_id,
            Expense.contractor_id,
            Expense.organization_id,
            func.avg(Expense.amount).label('avg_amount'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.department_id == request.department_id,
            Expense.category_id.is_not(None),  # Только заявки с категорией
            Expense.request_date >= three_months_ago,
            Expense.request_date < target_date,
            Expense.status.in_(['PAID', 'PENDING'])
        ).group_by(
            Expense.category_id,
            Expense.contractor_id,
            Expense.organization_id
        ).having(
            func.count(Expense.id) >= 3  # Минимум 3 раза за 3 месяца
        ).all()

        for reg in regular_expenses:
            # Находим все заявки этого типа для вычисления среднего дня оплаты
            expenses = db.query(Expense).filter(
                Expense.department_id == request.department_id,
                Expense.category_id == reg.category_id,
                Expense.contractor_id == reg.contractor_id,
                Expense.organization_id == reg.organization_id,
                Expense.request_date >= three_months_ago,
                Expense.request_date < target_date,
                Expense.status.in_(['PAID', 'PENDING'])
            ).all()

            # Вычисляем среднее число месяца когда происходит оплата
            if expenses:
                avg_day = sum(e.request_date.day for e in expenses) / len(expenses)
                day_of_month = round(avg_day)
                # Берем комментарий из самой свежей заявки с описанием
                comment = None
                for exp in sorted(expenses, key=lambda x: x.request_date, reverse=True):
                    if exp.comment and exp.comment.strip():
                        comment = exp.comment.strip()
                        break
                # Если нет комментария, используем простое описание
                if not comment:
                    comment = "Регулярная оплата"
            else:
                day_of_month = 15
                comment = "Регулярная оплата"

            # Проверяем, что день существует в целевом месяце
            max_day = calendar.monthrange(request.target_year, request.target_month)[1]
            if day_of_month > max_day:
                day_of_month = max_day
            elif day_of_month < 1:
                day_of_month = 1

            # Применяем правила рабочих дней
            original_date = date(request.target_year, request.target_month, day_of_month)
            adjusted_date = adjust_to_workday(original_date)

            # Round amount to hundreds
            rounded_amount = round_to_hundreds(reg.avg_amount)

            forecast = ForecastExpense(
                department_id=request.department_id,
                category_id=reg.category_id,
                contractor_id=reg.contractor_id,
                organization_id=reg.organization_id,
                forecast_date=adjusted_date,
                amount=rounded_amount,
                is_regular=True,
                comment=comment
            )
            db.add(forecast)
            created_count += 1

    # 2. Добавляем средние по категориям (для нерегулярных)
    if request.include_average:
        # Берем статистику за последние 6 месяцев по категориям
        six_months_ago = target_date - timedelta(days=180)

        # Исключаем уже добавленные регулярные расходы
        existing_regular = db.query(
            ForecastExpense.category_id,
            ForecastExpense.contractor_id
        ).filter(
            ForecastExpense.department_id == request.department_id,
            ForecastExpense.is_regular == True,
            extract('year', ForecastExpense.forecast_date) == request.target_year,
            extract('month', ForecastExpense.forecast_date) == request.target_month
        ).all()

        regular_pairs = {(r.category_id, r.contractor_id) for r in existing_regular}

        # Получаем средние по категориям
        category_averages = db.query(
            Expense.category_id,
            Expense.organization_id,
            func.avg(Expense.amount).label('avg_amount'),
            func.count(Expense.id).label('count')
        ).filter(
            Expense.department_id == request.department_id,
            Expense.category_id.is_not(None),  # Только заявки с категорией
            Expense.request_date >= six_months_ago,
            Expense.request_date < target_date,
            Expense.status.in_(['PAID', 'PENDING'])
        ).group_by(
            Expense.category_id,
            Expense.organization_id
        ).having(
            func.count(Expense.id) >= 2  # Минимум 2 раза за 6 месяцев
        ).all()

        for avg in category_averages:
            # Пропускаем если эта категория уже есть в регулярных
            if any((reg[0] == avg.category_id) for reg in regular_pairs):
                continue

            # Находим все заявки этой категории для вычисления среднего дня оплаты
            expenses = db.query(Expense).filter(
                Expense.department_id == request.department_id,
                Expense.category_id == avg.category_id,
                Expense.organization_id == avg.organization_id,
                Expense.request_date >= six_months_ago,
                Expense.request_date < target_date,
                Expense.status.in_(['PAID', 'PENDING'])
            ).all()

            # Вычисляем среднее число месяца когда происходит оплата
            if expenses:
                avg_day = sum(e.request_date.day for e in expenses) / len(expenses)
                day_of_month = round(avg_day)
                # Берем комментарий из самой свежей заявки с описанием
                comment = None
                for exp in sorted(expenses, key=lambda x: x.request_date, reverse=True):
                    if exp.comment and exp.comment.strip():
                        comment = exp.comment.strip()
                        break
                # Если нет комментария, используем название категории
                if not comment:
                    category = db.query(BudgetCategory).filter(BudgetCategory.id == avg.category_id).first()
                    comment = category.name if category else "Прочие расходы"
            else:
                day_of_month = 20
                category = db.query(BudgetCategory).filter(BudgetCategory.id == avg.category_id).first()
                comment = category.name if category else "Прочие расходы"

            # Проверяем, что день существует в целевом месяце
            max_day = calendar.monthrange(request.target_year, request.target_month)[1]
            if day_of_month > max_day:
                day_of_month = max_day
            elif day_of_month < 1:
                day_of_month = 1

            # Применяем правила рабочих дней
            original_date = date(request.target_year, request.target_month, day_of_month)
            adjusted_date = adjust_to_workday(original_date)

            # Round amount to hundreds
            rounded_amount = round_to_hundreds(avg.avg_amount)

            forecast = ForecastExpense(
                department_id=request.department_id,
                category_id=avg.category_id,
                contractor_id=None,
                organization_id=avg.organization_id,
                forecast_date=adjusted_date,
                amount=rounded_amount,
                is_regular=False,
                comment=comment
            )
            db.add(forecast)
            created_count += 1

    db.commit()

    return {
        "created": created_count,
        "target_month": request.target_month,
        "target_year": request.target_year
    }


@router.get("/", response_model=List[ForecastExpenseInDB])
def get_forecasts(
    year: int,
    month: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all forecasts for specified month and department

    - USER: Can only view forecasts for their own department
    - MANAGER/ADMIN: Can view forecasts for any department
    """
    # Check department access
    check_department_access(current_user, department_id)

    forecasts = db.query(ForecastExpense).filter(
        ForecastExpense.department_id == department_id,
        extract('year', ForecastExpense.forecast_date) == year,
        extract('month', ForecastExpense.forecast_date) == month
    ).all()

    # Добавляем related objects
    result = []
    for f in forecasts:
        forecast_dict = {
            "id": f.id,
            "department_id": f.department_id,
            "category_id": f.category_id,
            "contractor_id": f.contractor_id,
            "organization_id": f.organization_id,
            "forecast_date": f.forecast_date,
            "amount": f.amount,
            "comment": f.comment,
            "is_regular": f.is_regular,
            "based_on_expense_id": f.based_on_expense_id,
            "created_at": f.created_at,
            "updated_at": f.updated_at,
            "category": {"id": f.category.id, "name": f.category.name} if f.category else None,
            "contractor": {"id": f.contractor.id, "name": f.contractor.name} if f.contractor else None,
            "organization": {"id": f.organization.id, "name": f.organization.name} if f.organization else None,
        }
        result.append(forecast_dict)

    return result


@router.post("/", response_model=ForecastExpenseInDB)
def create_forecast(
    forecast: ForecastExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create new forecast expense

    - USER: Can only create forecasts for their own department
    - MANAGER/ADMIN: Can create forecasts for any department
    """
    # Check department access
    check_department_access(current_user, forecast.department_id)

    db_forecast = ForecastExpense(**forecast.model_dump())
    db.add(db_forecast)
    db.commit()
    db.refresh(db_forecast)

    # Return as dict with related objects
    return {
        "id": db_forecast.id,
        "department_id": db_forecast.department_id,
        "category_id": db_forecast.category_id,
        "contractor_id": db_forecast.contractor_id,
        "organization_id": db_forecast.organization_id,
        "forecast_date": db_forecast.forecast_date,
        "amount": db_forecast.amount,
        "comment": db_forecast.comment,
        "is_regular": db_forecast.is_regular,
        "based_on_expense_id": db_forecast.based_on_expense_id,
        "created_at": db_forecast.created_at,
        "updated_at": db_forecast.updated_at,
        "category": {"id": db_forecast.category.id, "name": db_forecast.category.name} if db_forecast.category else None,
        "contractor": {"id": db_forecast.contractor.id, "name": db_forecast.contractor.name} if db_forecast.contractor else None,
        "organization": {"id": db_forecast.organization.id, "name": db_forecast.organization.name} if db_forecast.organization else None,
    }


@router.put("/{forecast_id}", response_model=ForecastExpenseInDB)
def update_forecast(
    forecast_id: int,
    forecast: ForecastExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update forecast expense

    - USER: Can only update forecasts from their own department
    - MANAGER/ADMIN: Can update forecasts from any department
    """
    db_forecast = db.query(ForecastExpense).filter(ForecastExpense.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with id {forecast_id} not found"
        )

    # Check department access
    check_department_access(current_user, db_forecast.department_id)

    update_data = forecast.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_forecast, field, value)

    db.commit()
    db.refresh(db_forecast)

    # Return as dict with related objects
    return {
        "id": db_forecast.id,
        "department_id": db_forecast.department_id,
        "category_id": db_forecast.category_id,
        "contractor_id": db_forecast.contractor_id,
        "organization_id": db_forecast.organization_id,
        "forecast_date": db_forecast.forecast_date,
        "amount": db_forecast.amount,
        "comment": db_forecast.comment,
        "is_regular": db_forecast.is_regular,
        "based_on_expense_id": db_forecast.based_on_expense_id,
        "created_at": db_forecast.created_at,
        "updated_at": db_forecast.updated_at,
        "category": {"id": db_forecast.category.id, "name": db_forecast.category.name} if db_forecast.category else None,
        "contractor": {"id": db_forecast.contractor.id, "name": db_forecast.contractor.name} if db_forecast.contractor else None,
        "organization": {"id": db_forecast.organization.id, "name": db_forecast.organization.name} if db_forecast.organization else None,
    }


@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete forecast expense

    - USER: Can only delete forecasts from their own department
    - MANAGER/ADMIN: Can delete forecasts from any department
    """
    db_forecast = db.query(ForecastExpense).filter(ForecastExpense.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with id {forecast_id} not found"
        )

    # Check department access
    check_department_access(current_user, db_forecast.department_id)

    db.delete(db_forecast)
    db.commit()
    return None


@router.delete("/clear/{year}/{month}", status_code=status.HTTP_204_NO_CONTENT)
def clear_forecasts(
    year: int,
    month: int,
    department_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Clear all forecasts for specified month and department

    - USER: Can only clear forecasts for their own department
    - MANAGER/ADMIN: Can clear forecasts for any department
    """
    # Check department access
    check_department_access(current_user, department_id)

    db.query(ForecastExpense).filter(
        ForecastExpense.department_id == department_id,
        extract('year', ForecastExpense.forecast_date) == year,
        extract('month', ForecastExpense.forecast_date) == month
    ).delete()
    db.commit()
    return None


@router.get("/export/{year}/{month}")
def export_forecast_calendar(
    year: int,
    month: int,
    department_id: Optional[int] = Query(default=None, description="Filter by department (MANAGER/ADMIN only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Export forecast data as Excel calendar format using template
    Dates in columns, categories/contractors in rows

    - USER: Can only export forecasts for their own department
    - MANAGER/ADMIN: Can export forecasts for any department
    """
    # Determine department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only export their own department
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        dept_id = current_user.department_id
    elif current_user.role in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        # MANAGER and ADMIN can filter by department or see all
        if department_id is not None:
            dept_id = department_id
        else:
            # If no department specified, require it for security
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department ID is required for export"
            )
    else:
        dept_id = None

    # Get forecasts for the month and department
    query = db.query(ForecastExpense).filter(
        extract('year', ForecastExpense.forecast_date) == year,
        extract('month', ForecastExpense.forecast_date) == month
    )

    if dept_id:
        query = query.filter(ForecastExpense.department_id == dept_id)

    forecasts = query.all()

    # Convert to dict format for export
    forecast_dicts = []
    for f in forecasts:
        forecast_dict = {
            "id": f.id,
            "category_id": f.category_id,
            "contractor_id": f.contractor_id,
            "organization_id": f.organization_id,
            "date": f.forecast_date,
            "amount": float(f.amount),
            "comment": f.comment,
            "is_regular": f.is_regular,
            "category": {"id": f.category.id, "name": f.category.name} if f.category else None,
            "contractor": {"id": f.contractor.id, "name": f.contractor.name} if f.contractor else None,
            "organization": {"id": f.organization.id, "name": f.organization.name} if f.organization else None,
        }
        forecast_dicts.append(forecast_dict)

    # Добавляем ФОТ (фонд оплаты труда)
    if dept_id:
        # Получаем планы по зарплате за этот месяц
        payroll_plans = db.query(PayrollPlan).filter(
            PayrollPlan.department_id == dept_id,
            PayrollPlan.year == year,
            PayrollPlan.month == month
        ).all()

        if payroll_plans:
            # Суммируем все выплаты по всем сотрудникам
            total_payroll = sum(float(p.total_planned) for p in payroll_plans)

            if total_payroll > 0:
                # Найдем или создадим категорию "ФОТ"
                fot_category = db.query(BudgetCategory).filter(
                    BudgetCategory.department_id == dept_id,
                    BudgetCategory.name.ilike("%фот%")
                ).first()

                if not fot_category:
                    # Используем первую активную категорию как fallback
                    fot_category = db.query(BudgetCategory).filter(
                        BudgetCategory.department_id == dept_id,
                        BudgetCategory.is_active == True
                    ).first()

                # Получаем первую активную организацию
                default_org = db.query(Organization).filter(
                    Organization.is_active == True
                ).first()
                org_id = default_org.id if default_org else 1

                # Делим на аванс и оклад+премия (по 50%)
                advance_amount = round_to_hundreds(Decimal(str(total_payroll * 0.5)))
                salary_bonus_amount = round_to_hundreds(Decimal(str(total_payroll * 0.5)))

                # НДФЛ = 13% от общей суммы
                ndfl_amount = round_to_hundreds(Decimal(str(total_payroll * 0.13)))

                # Даты выплат с учетом рабочих дней
                # Аванс - 10 число
                max_day_in_month = calendar.monthrange(year, month)[1]
                advance_day = min(10, max_day_in_month)
                advance_date = adjust_to_workday(date(year, month, advance_day))

                # Оклад + премия - 25 число
                salary_day = min(25, max_day_in_month)
                salary_date = adjust_to_workday(date(year, month, salary_day))

                # НДФЛ - платится вместе с зарплатой (25 число)
                ndfl_date = salary_date

                # Добавляем 3 строки ФОТ
                if fot_category:
                    # 1. Аванс
                    forecast_dicts.append({
                        "id": -1,
                        "category_id": fot_category.id,
                        "contractor_id": None,
                        "organization_id": org_id,
                        "date": advance_date,
                        "amount": float(advance_amount),
                        "comment": "Аванс сотрудникам",
                        "is_regular": True,
                        "category": {"id": fot_category.id, "name": fot_category.name},
                        "contractor": None,
                        "organization": {"id": org_id, "name": default_org.name} if default_org else None,
                    })

                    # 2. Оклад + премия
                    forecast_dicts.append({
                        "id": -2,
                        "category_id": fot_category.id,
                        "contractor_id": None,
                        "organization_id": org_id,
                        "date": salary_date,
                        "amount": float(salary_bonus_amount),
                        "comment": "Оклад и премии сотрудникам",
                        "is_regular": True,
                        "category": {"id": fot_category.id, "name": fot_category.name},
                        "contractor": None,
                        "organization": {"id": org_id, "name": default_org.name} if default_org else None,
                    })

                    # 3. НДФЛ
                    forecast_dicts.append({
                        "id": -3,
                        "category_id": fot_category.id,
                        "contractor_id": None,
                        "organization_id": org_id,
                        "date": ndfl_date,
                        "amount": float(ndfl_amount),
                        "comment": "НДФЛ с заработной платы",
                        "is_regular": True,
                        "category": {"id": fot_category.id, "name": fot_category.name},
                        "contractor": None,
                        "organization": {"id": org_id, "name": default_org.name} if default_org else None,
                    })

    # Get department name for template sheet selection
    department_name = "Шикунов"  # Default to IT department
    if dept_id:
        from app.db.models import Department
        dept = db.query(Department).filter(Department.id == dept_id).first()
        if dept and dept.code:
            # Use department code or name for sheet selection
            department_name = dept.code if dept.code else dept.name

    # Generate Excel file using template
    excel_file = ExcelExporter.export_forecast_from_template(year, month, forecast_dicts, department_name)

    # Month names in Russian
    month_names = [
        '', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
        'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
    ]

    from urllib.parse import quote

    filename = f"Планирование_{month:02d}.{year}.xlsx"
    filename_encoded = quote(filename)

    return StreamingResponse(
        excel_file,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
        }
    )


@router.post("/ai-generate", response_model=dict)
async def generate_ai_forecast(
    request: GenerateAIForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate HYBRID forecast: Base statistical + AI enhancements

    Process:
    1. Delete all existing forecasts for the target month
    2. Generate base forecast (regular + average expenses with proper categories/contractors)
    3. AI analyzes patterns and suggests additional items
    4. Round all amounts to hundreds
    5. Match AI items to real categories and contractors from historical data

    - USER: Can only generate forecasts for their own department
    - MANAGER/ADMIN: Can generate forecasts for any department
    """
    # Check department access
    check_department_access(current_user, request.department_id)

    # STEP 1: Delete ALL existing forecasts for this month
    db.query(ForecastExpense).filter(
        ForecastExpense.department_id == request.department_id,
        extract('year', ForecastExpense.forecast_date) == request.target_year,
        extract('month', ForecastExpense.forecast_date) == request.target_month
    ).delete(synchronize_session=False)
    db.commit()

    # STEP 2: Generate BASE forecast using statistical method
    target_date = date(request.target_year, request.target_month, 1)
    base_created = 0

    # 2a. Regular expenses (repeating monthly)
    three_months_ago = target_date - timedelta(days=90)
    regular_expenses = db.query(
        Expense.category_id,
        Expense.contractor_id,
        Expense.organization_id,
        func.avg(Expense.amount).label('avg_amount'),
        func.count(Expense.id).label('count')
    ).filter(
        Expense.department_id == request.department_id,
        Expense.category_id.is_not(None),
        Expense.request_date >= three_months_ago,
        Expense.request_date < target_date,
        Expense.status.in_(['PAID', 'PENDING'])
    ).group_by(
        Expense.category_id,
        Expense.contractor_id,
        Expense.organization_id
    ).having(
        func.count(Expense.id) >= 3  # Минимум 3 раза за 3 месяца
    ).all()

    for reg in regular_expenses:
        expenses = db.query(Expense).filter(
            Expense.department_id == request.department_id,
            Expense.category_id == reg.category_id,
            Expense.contractor_id == reg.contractor_id,
            Expense.organization_id == reg.organization_id,
            Expense.request_date >= three_months_ago,
            Expense.request_date < target_date
        ).all()

        if expenses:
            avg_day = sum(e.request_date.day for e in expenses) / len(expenses)
            day_of_month = round(avg_day)
            # Берем комментарий из самой свежей заявки с описанием
            comment = None
            for exp in sorted(expenses, key=lambda x: x.request_date, reverse=True):
                if exp.comment and exp.comment.strip():
                    comment = exp.comment.strip()
                    break
            if not comment:
                comment = "Регулярная оплата"
        else:
            day_of_month = 15
            comment = "Регулярная оплата"

        max_day = calendar.monthrange(request.target_year, request.target_month)[1]
        if day_of_month > max_day:
            day_of_month = max_day
        elif day_of_month < 1:
            day_of_month = 1

        original_date = date(request.target_year, request.target_month, day_of_month)
        adjusted_date = adjust_to_workday(original_date)

        # Round amount to hundreds
        rounded_amount = round_to_hundreds(reg.avg_amount)

        forecast = ForecastExpense(
            department_id=request.department_id,
            category_id=reg.category_id,
            contractor_id=reg.contractor_id,
            organization_id=reg.organization_id,
            forecast_date=adjusted_date,
            amount=rounded_amount,
            is_regular=True,
            comment=comment
        )
        db.add(forecast)
        base_created += 1

    db.commit()

    # STEP 3: Initialize AI forecast service
    ai_service = AIForecastService(db)

    # STEP 4: Generate AI forecast
    ai_result = await ai_service.generate_ai_forecast(
        department_id=request.department_id,
        year=request.target_year,
        month=request.target_month,
        category_id=request.category_id,
    )

    # STEP 5: Add AI suggestions as ADDITIONAL items
    ai_created = 0
    if ai_result.get("success") and ai_result.get("items"):
        # Get existing categories for better matching
        all_categories = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == request.department_id,
            BudgetCategory.is_active == True
        ).all()

        category_map = {cat.name.lower(): cat.id for cat in all_categories}

        # Create forecast records from AI suggestions
        for idx, item in enumerate(ai_result["items"], start=1):
            description = item.get("description", "")
            description_lower = description.lower()

            # Determine forecast date (spread across month, avoiding base forecast dates)
            day_of_month = min(12 + (idx * 3), 28)  # 12, 15, 18, 21, 24, 27
            max_day = calendar.monthrange(request.target_year, request.target_month)[1]
            if day_of_month > max_day:
                day_of_month = max_day

            # Apply workday rules
            original_date = date(request.target_year, request.target_month, day_of_month)
            adjusted_date = adjust_to_workday(original_date)

            # Advanced category matching using historical data
            category_id = request.category_id
            contractor_id = None

            category_hint = item.get("category_hint")
            if category_hint:
                try:
                    category_id = int(category_hint)
                except (TypeError, ValueError):
                    category_id = category_hint

            if not category_id:
                # Try to find category from historical expenses matching description
                keywords = description_lower.split()[:5]  # First 5 words

                for keyword in keywords:
                    if len(keyword) < 3:
                        continue

                    # Search for matching expense in history
                    matching_expense = db.query(Expense).filter(
                        Expense.department_id == request.department_id,
                        Expense.category_id.is_not(None),
                        or_(
                            Expense.comment.ilike(f"%{keyword}%"),
                            BudgetCategory.name.ilike(f"%{keyword}%")
                        )
                    ).join(BudgetCategory, Expense.category_id == BudgetCategory.id).first()

                    if matching_expense:
                        category_id = matching_expense.category_id
                        contractor_id = matching_expense.contractor_id
                        break

                # Fallback: keyword-based category matching
                if not category_id:
                    category_keywords = {
                        'связь': ['связь', 'телефон', 'интернет', 'сим'],
                        'лицензи': ['лицензи', 'подписк', '1с', 'битрикс'],
                        'разработ': ['разработ', 'програм', 'приложени'],
                        'серв': ['серв', 'облак', 'хостинг', 'vps'],
                        'оборудован': ['оборуд', 'техник', 'компьютер', 'ноутбук'],
                    }

                    for cat_key, keywords in category_keywords.items():
                        if any(kw in description_lower for kw in keywords):
                            # Find category matching this key
                            for cat_name, cat_id in category_map.items():
                                if cat_key in cat_name:
                                    category_id = cat_id
                                    break
                            if category_id:
                                break

                # Ultimate fallback: most used category
                if not category_id:
                    most_used = db.query(
                        Expense.category_id,
                        func.count(Expense.id).label('count')
                    ).filter(
                        Expense.department_id == request.department_id,
                        Expense.category_id.is_not(None)
                    ).group_by(Expense.category_id).order_by(
                        func.count(Expense.id).desc()
                    ).first()

                    if most_used:
                        category_id = most_used.category_id

            # Get default organization
            organization = db.query(Organization).filter(
                Organization.is_active == True
            ).first()
            organization_id = organization.id if organization else 1

            # Round amount to hundreds
            amount = item.get("amount", 0)
            rounded_amount = round_to_hundreds(Decimal(str(amount)))

            # Create forecast expense
            if category_id and rounded_amount > 0:
                forecast = ForecastExpense(
                    department_id=request.department_id,
                    category_id=category_id,
                    contractor_id=contractor_id,
                    organization_id=organization_id,
                    forecast_date=adjusted_date,
                    amount=rounded_amount,
                    is_regular=False,
                    comment=description[:150] if description else "Прогнозируемый расход"
                )
                db.add(forecast)
                ai_created += 1

        db.commit()

    ai_result["created_forecast_records"] = ai_created

    # Return comprehensive result
    return {
        **ai_result,
        "base_forecast_records": base_created,
        "ai_forecast_records": ai_created,
        "total_forecast_records": base_created + ai_created,
        "target_month": request.target_month,
        "target_year": request.target_year,
    }
