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
from app.db.models import ForecastExpense, Expense, BudgetCategory, Contractor, Organization
from app.utils.excel_export import ExcelExporter

router = APIRouter()


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
    1. Если дата на выходные - переносит на предыдущий рабочий день
    2. Если дата 10 число или 25 число - переносит на предыдущий рабочий день
    3. Если предыдущий день от 10/25 тоже выходной - переносит еще раньше
    """
    day = date_obj.day

    # Правило для 10 и 25 числа: всегда переносим на предыдущий рабочий день
    if day in (10, 25):
        return get_previous_workday(date_obj)

    # Если дата на выходные, переносим на предыдущий рабочий день
    if is_weekend(date_obj):
        return get_previous_workday(date_obj)

    return date_obj


# Pydantic schemas
class ForecastExpenseBase(BaseModel):
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
    include_regular: bool = True  # Включить регулярные расходы
    include_average: bool = True  # Включить средние по нерегулярным


@router.post("/generate", response_model=dict)
def generate_forecast(
    request: GenerateForecastRequest,
    db: Session = Depends(get_db)
):
    """
    Generate forecast for next month based on:
    1. Regular expenses (repeating monthly)
    2. Average of non-regular expenses
    """
    target_date = date(request.target_year, request.target_month, 1)

    # Удаляем существующий прогноз на этот месяц
    db.query(ForecastExpense).filter(
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
            else:
                day_of_month = 15

            # Проверяем, что день существует в целевом месяце
            max_day = calendar.monthrange(request.target_year, request.target_month)[1]
            if day_of_month > max_day:
                day_of_month = max_day
            elif day_of_month < 1:
                day_of_month = 1

            # Применяем правила рабочих дней
            original_date = date(request.target_year, request.target_month, day_of_month)
            adjusted_date = adjust_to_workday(original_date)

            forecast = ForecastExpense(
                category_id=reg.category_id,
                contractor_id=reg.contractor_id,
                organization_id=reg.organization_id,
                forecast_date=adjusted_date,
                amount=reg.avg_amount,
                is_regular=True,
                comment=f"Автоматически: регулярный расход (среднее за 3 месяца, обычно ~{day_of_month} числа)"
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
            else:
                day_of_month = 20

            # Проверяем, что день существует в целевом месяце
            max_day = calendar.monthrange(request.target_year, request.target_month)[1]
            if day_of_month > max_day:
                day_of_month = max_day
            elif day_of_month < 1:
                day_of_month = 1

            # Применяем правила рабочих дней
            original_date = date(request.target_year, request.target_month, day_of_month)
            adjusted_date = adjust_to_workday(original_date)

            forecast = ForecastExpense(
                category_id=avg.category_id,
                contractor_id=None,
                organization_id=avg.organization_id,
                forecast_date=adjusted_date,
                amount=avg.avg_amount,
                is_regular=False,
                comment=f"Автоматически: средний расход по категории ({avg.count} раз за 6 мес., обычно ~{day_of_month} числа)"
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
    db: Session = Depends(get_db)
):
    """Get all forecasts for specified month"""
    forecasts = db.query(ForecastExpense).filter(
        extract('year', ForecastExpense.forecast_date) == year,
        extract('month', ForecastExpense.forecast_date) == month
    ).all()

    # Добавляем related objects
    result = []
    for f in forecasts:
        forecast_dict = {
            "id": f.id,
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
    db: Session = Depends(get_db)
):
    """Create new forecast expense"""
    db_forecast = ForecastExpense(**forecast.model_dump())
    db.add(db_forecast)
    db.commit()
    db.refresh(db_forecast)
    return db_forecast


@router.put("/{forecast_id}", response_model=ForecastExpenseInDB)
def update_forecast(
    forecast_id: int,
    forecast: ForecastExpenseUpdate,
    db: Session = Depends(get_db)
):
    """Update forecast expense"""
    db_forecast = db.query(ForecastExpense).filter(ForecastExpense.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with id {forecast_id} not found"
        )

    update_data = forecast.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_forecast, field, value)

    db.commit()
    db.refresh(db_forecast)
    return db_forecast


@router.delete("/{forecast_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_forecast(forecast_id: int, db: Session = Depends(get_db)):
    """Delete forecast expense"""
    db_forecast = db.query(ForecastExpense).filter(ForecastExpense.id == forecast_id).first()
    if not db_forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Forecast with id {forecast_id} not found"
        )

    db.delete(db_forecast)
    db.commit()
    return None


@router.delete("/clear/{year}/{month}", status_code=status.HTTP_204_NO_CONTENT)
def clear_forecasts(year: int, month: int, db: Session = Depends(get_db)):
    """Clear all forecasts for specified month"""
    db.query(ForecastExpense).filter(
        extract('year', ForecastExpense.forecast_date) == year,
        extract('month', ForecastExpense.forecast_date) == month
    ).delete()
    db.commit()
    return None


@router.get("/export/{year}/{month}")
def export_forecast_calendar(
    year: int,
    month: int,
    db: Session = Depends(get_db)
):
    """
    Export forecast data as Excel calendar format
    Dates in columns, categories/contractors in rows
    """
    # Get forecasts for the month
    forecasts = db.query(ForecastExpense).filter(
        extract('year', ForecastExpense.forecast_date) == year,
        extract('month', ForecastExpense.forecast_date) == month
    ).all()

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

    # Generate Excel file
    excel_file = ExcelExporter.export_forecast_calendar(year, month, forecast_dicts)

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
