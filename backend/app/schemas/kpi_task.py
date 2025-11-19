"""
KPI Task Schemas

Pydantic models for KPI task management API.
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator

from app.db.models import KPITaskStatusEnum, KPITaskPriorityEnum


# Base schema with common fields
class KPITaskBase(BaseModel):
    """Base schema for KPI Task"""
    title: str = Field(..., min_length=1, max_length=255, description="Название задачи")
    description: Optional[str] = Field(None, description="Подробное описание задачи")
    status: KPITaskStatusEnum = Field(
        default=KPITaskStatusEnum.TODO,
        description="Статус задачи"
    )
    priority: KPITaskPriorityEnum = Field(
        default=KPITaskPriorityEnum.MEDIUM,
        description="Приоритет задачи"
    )
    complexity: Optional[int] = Field(
        None,
        ge=1,
        le=10,
        description="Сложность задачи по шкале 1-10"
    )
    estimated_hours: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Оценка времени выполнения в часах"
    )
    actual_hours: Optional[Decimal] = Field(
        None,
        ge=0,
        description="Фактическое время выполнения в часах"
    )
    completion_percentage: Optional[Decimal] = Field(
        default=Decimal("0"),
        ge=0,
        le=100,
        description="Процент выполнения задачи"
    )
    due_date: Optional[datetime] = Field(None, description="Срок выполнения")
    start_date: Optional[datetime] = Field(None, description="Дата начала работы")
    notes: Optional[str] = Field(None, description="Комментарии и заметки")


class KPITaskCreate(KPITaskBase):
    """Schema for creating a new KPI Task"""
    employee_kpi_goal_id: int = Field(..., description="ID цели KPI")
    employee_id: int = Field(..., description="ID сотрудника")
    # department_id берется из current_user, assigned_by_id тоже

    @field_validator('due_date', 'start_date')
    @classmethod
    def validate_dates(cls, v):
        """Validate that dates are not in the past (optional)"""
        # Optional: можно добавить валидацию, что due_date >= start_date
        return v


class KPITaskUpdate(BaseModel):
    """Schema for updating an existing KPI Task"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[KPITaskStatusEnum] = None
    priority: Optional[KPITaskPriorityEnum] = None
    complexity: Optional[int] = Field(None, ge=1, le=10)
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    notes: Optional[str] = None


class KPITaskInDB(KPITaskBase):
    """Schema for KPI Task from database"""
    id: int
    employee_kpi_goal_id: int
    employee_id: int
    assigned_by_id: Optional[int]
    department_id: int
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KPITaskResponse(KPITaskInDB):
    """Schema for KPI Task API response with related data"""
    # Optional: можно добавить связанные данные
    employee_name: Optional[str] = None
    goal_name: Optional[str] = None
    assigned_by_name: Optional[str] = None


class KPITaskStatusUpdate(BaseModel):
    """Schema for updating task status"""
    status: KPITaskStatusEnum
    completion_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = None

    @field_validator('completion_percentage')
    @classmethod
    def validate_completion(cls, v, info):
        """Auto-set completion based on status"""
        status = info.data.get('status')
        if status == KPITaskStatusEnum.DONE and v is None:
            return Decimal("100")
        if status == KPITaskStatusEnum.TODO and v is None:
            return Decimal("0")
        return v


class KPITaskComplexityUpdate(BaseModel):
    """Schema for updating task complexity and estimation"""
    complexity: int = Field(..., ge=1, le=10)
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class KPITaskBulkStatusUpdate(BaseModel):
    """Schema for bulk status update"""
    task_ids: list[int] = Field(..., min_length=1, description="Список ID задач")
    status: KPITaskStatusEnum
    notes: Optional[str] = None


class KPITaskStatistics(BaseModel):
    """Schema for task statistics"""
    total_tasks: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    avg_complexity: Optional[Decimal]
    total_estimated_hours: Optional[Decimal]
    total_actual_hours: Optional[Decimal]
    completion_rate: Decimal  # % задач в статусе DONE
    overdue_tasks: int
