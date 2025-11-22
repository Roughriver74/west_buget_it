from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from app.db.models import TimesheetStatusEnum, DayTypeEnum


# ============ WorkTimesheet Schemas ============

class WorkTimesheetBase(BaseModel):
    """Base schema for work timesheet"""
    year: int = Field(..., ge=2020, le=2100, description="Год табеля")
    month: int = Field(..., ge=1, le=12, description="Месяц табеля (1-12)")
    employee_id: int = Field(..., description="ID сотрудника")
    total_days_worked: int = Field(0, ge=0, le=31, description="Всего рабочих дней")
    total_hours_worked: Decimal = Field(0, ge=0, description="Всего часов отработано")
    status: TimesheetStatusEnum = Field(TimesheetStatusEnum.DRAFT, description="Статус табеля")
    approved_by_id: Optional[int] = Field(None, description="ID пользователя, утвердившего табель")
    approved_at: Optional[date] = Field(None, description="Дата утверждения")
    notes: Optional[str] = Field(None, description="Примечания")


class WorkTimesheetCreate(BaseModel):
    """Schema for creating work timesheet

    - USER: can only create for themselves in their department
    - MANAGER: can create for any employee in their department
    - HR: can create for any employee in any department
    - department_id is auto-assigned based on employee's department
    """
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    employee_id: int
    notes: Optional[str] = None


class WorkTimesheetUpdate(BaseModel):
    """Schema for updating work timesheet - can only update if status is DRAFT"""
    notes: Optional[str] = None
    # total_days_worked and total_hours_worked are calculated from daily records


class WorkTimesheetApprove(BaseModel):
    """Schema for approving timesheet - changes status from DRAFT to APPROVED"""
    notes: Optional[str] = None


class WorkTimesheetInDB(WorkTimesheetBase):
    """Schema for work timesheet in database"""
    id: UUID
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed properties
    can_edit: bool = Field(default=False, description="Можно ли редактировать табель")
    period_display: str = Field(default="", description="Отображение периода")

    class Config:
        from_attributes = True


class WorkTimesheetWithEmployee(WorkTimesheetInDB):
    """Timesheet with employee details"""
    employee_full_name: str
    employee_position: str
    employee_number: Optional[str] = None

    class Config:
        from_attributes = True


class WorkTimesheetWithRecords(WorkTimesheetInDB):
    """Timesheet with daily records"""
    daily_records: List['DailyWorkRecordInDB'] = []

    class Config:
        from_attributes = True


# ============ DailyWorkRecord Schemas ============

class DailyWorkRecordBase(BaseModel):
    """Base schema for daily work record"""
    work_date: date = Field(..., description="Дата работы")
    is_working_day: bool = Field(False, description="Рабочий день или нет")
    hours_worked: Decimal = Field(0, ge=0, le=24, description="Часов отработано")
    day_type: DayTypeEnum = Field(DayTypeEnum.WORK, description="Тип дня")
    break_hours: Optional[Decimal] = Field(None, ge=0, description="Часов перерыва")
    overtime_hours: Optional[Decimal] = Field(None, ge=0, description="Сверхурочных часов")
    notes: Optional[str] = Field(None, description="Примечания")


class DailyWorkRecordCreate(DailyWorkRecordBase):
    """Schema for creating daily work record"""
    timesheet_id: UUID = Field(..., description="ID табеля")


class DailyWorkRecordUpdate(BaseModel):
    """Schema for updating daily work record"""
    is_working_day: Optional[bool] = None
    hours_worked: Optional[Decimal] = Field(None, ge=0, le=24)
    day_type: Optional[DayTypeEnum] = None
    break_hours: Optional[Decimal] = Field(None, ge=0)
    overtime_hours: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class DailyWorkRecordInDB(DailyWorkRecordBase):
    """Schema for daily work record in database"""
    id: UUID
    timesheet_id: UUID
    department_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Computed property
    net_hours_worked: Decimal = Field(default=0, description="Чистое время работы (без перерывов)")

    class Config:
        from_attributes = True


# ============ Bulk Operations Schemas ============

class DailyWorkRecordBulkCreate(BaseModel):
    """Schema for bulk creating daily work records"""
    timesheet_id: UUID
    records: List[DailyWorkRecordBase]


class DailyWorkRecordBulkUpdate(BaseModel):
    """Schema for bulk updating daily work records"""
    updates: List[dict] = Field(..., description="List of {id: UUID, ...fields}")


# ============ Grid/Calendar Schemas ============

class TimesheetGridDay(BaseModel):
    """Single day data for grid view"""
    date: date
    day_of_week: int = Field(..., ge=1, le=7, description="День недели (1=Пн, 7=Вс)")
    is_working_day: bool
    hours_worked: Decimal = Field(0, ge=0)
    day_type: Optional[DayTypeEnum] = Field(None, description="Тип дня")
    break_hours: Optional[Decimal] = None
    overtime_hours: Optional[Decimal] = None
    net_hours_worked: Decimal = Field(0, description="Чистое время")
    notes: Optional[str] = None
    record_id: Optional[UUID] = Field(None, description="ID записи, если существует")


class TimesheetGridEmployee(BaseModel):
    """Employee row in grid view"""
    employee_id: int
    employee_full_name: str
    employee_position: str
    employee_number: Optional[str] = None
    timesheet_id: Optional[UUID] = None
    timesheet_status: Optional[TimesheetStatusEnum] = None
    total_days_worked: int = 0
    total_hours_worked: Decimal = 0
    can_edit: bool = False
    days: List[TimesheetGridDay] = []


class TimesheetGrid(BaseModel):
    """Complete grid data for a month"""
    year: int
    month: int
    department_id: int
    department_name: str
    employees: List[TimesheetGridEmployee]
    working_days_in_month: int
    calendar_days_in_month: int


# ============ Analytics Schemas ============

class TimesheetSummary(BaseModel):
    """Timesheet summary for analytics"""
    year: int
    month: int
    department_id: int
    total_employees: int
    employees_with_timesheets: int
    total_days_worked: int
    total_hours_worked: Decimal
    average_hours_per_employee: Decimal
    draft_count: int
    approved_count: int
    paid_count: int


class EmployeeTimesheetStats(BaseModel):
    """Employee timesheet statistics"""
    employee_id: int
    employee_full_name: str
    employee_position: str
    department_id: int
    months_count: int
    total_days_worked: int
    total_hours_worked: Decimal
    average_hours_per_month: Decimal
    last_timesheet_date: Optional[date] = None


class DepartmentTimesheetStats(BaseModel):
    """Department timesheet statistics"""
    department_id: int
    department_name: str
    year: int
    month: int
    total_employees: int
    employees_with_approved: int
    total_hours_worked: Decimal
    average_hours_per_employee: Decimal
    completion_rate: float = Field(..., description="Процент заполнения табелей")


class TimesheetMonthlyComparison(BaseModel):
    """Monthly comparison of timesheets"""
    year: int
    month: int
    current_hours: Decimal
    previous_hours: Decimal
    variance: Decimal
    variance_percent: float
    employee_count: int


# ============ Excel Import/Export Schemas ============

class TimesheetExcelRow(BaseModel):
    """Single row for Excel import/export"""
    employee_full_name: str
    employee_number: Optional[str] = None
    employee_position: str
    day_1: Optional[Decimal] = None
    day_2: Optional[Decimal] = None
    day_3: Optional[Decimal] = None
    day_4: Optional[Decimal] = None
    day_5: Optional[Decimal] = None
    day_6: Optional[Decimal] = None
    day_7: Optional[Decimal] = None
    day_8: Optional[Decimal] = None
    day_9: Optional[Decimal] = None
    day_10: Optional[Decimal] = None
    day_11: Optional[Decimal] = None
    day_12: Optional[Decimal] = None
    day_13: Optional[Decimal] = None
    day_14: Optional[Decimal] = None
    day_15: Optional[Decimal] = None
    day_16: Optional[Decimal] = None
    day_17: Optional[Decimal] = None
    day_18: Optional[Decimal] = None
    day_19: Optional[Decimal] = None
    day_20: Optional[Decimal] = None
    day_21: Optional[Decimal] = None
    day_22: Optional[Decimal] = None
    day_23: Optional[Decimal] = None
    day_24: Optional[Decimal] = None
    day_25: Optional[Decimal] = None
    day_26: Optional[Decimal] = None
    day_27: Optional[Decimal] = None
    day_28: Optional[Decimal] = None
    day_29: Optional[Decimal] = None
    day_30: Optional[Decimal] = None
    day_31: Optional[Decimal] = None
    total_days: int = 0
    total_hours: Decimal = 0
    notes: Optional[str] = None


class TimesheetExcelImport(BaseModel):
    """Schema for Excel import request"""
    year: int = Field(..., ge=2020, le=2100)
    month: int = Field(..., ge=1, le=12)
    department_id: int
    auto_create_employees: bool = Field(False, description="Автоматически создавать сотрудников, если не найдены")


class TimesheetExcelImportResult(BaseModel):
    """Result of Excel import operation"""
    success: bool
    imported_count: int
    created_count: int
    updated_count: int
    errors: List[str] = []
    warnings: List[str] = []


# ============ Payroll Integration Schemas (для будущего) ============

class TimesheetPayrollData(BaseModel):
    """Timesheet data for payroll calculation"""
    employee_id: int
    year: int
    month: int
    total_hours_worked: Decimal
    standard_hours: Decimal = Field(..., description="Норма часов в месяце")
    overtime_hours: Decimal = Field(0, description="Сверхурочные часы")
    hours_completion_percent: float = Field(..., description="Процент выполнения нормы часов")
    salary_coefficient: Decimal = Field(..., description="Коэффициент для расчета ЗП (hours_worked / standard_hours)")
