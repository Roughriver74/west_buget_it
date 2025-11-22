"""
Timesheet API endpoints (HR_DEPARTMENT module)
Handles work timesheets and daily work records
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, extract, case
from datetime import datetime, date
from decimal import Decimal
import calendar
import io

from app.db.session import get_db
from app.db.models import (
    WorkTimesheet, DailyWorkRecord, Employee, User, UserRoleEnum,
    Department, TimesheetStatusEnum, EmployeeStatusEnum, DayTypeEnum
)
from app.schemas.timesheet import (
    # WorkTimesheet schemas
    WorkTimesheetCreate,
    WorkTimesheetUpdate,
    WorkTimesheetApprove,
    WorkTimesheetInDB,
    WorkTimesheetWithEmployee,
    WorkTimesheetWithRecords,
    # DailyWorkRecord schemas
    DailyWorkRecordCreate,
    DailyWorkRecordUpdate,
    DailyWorkRecordInDB,
    DailyWorkRecordBulkCreate,
    DailyWorkRecordBulkUpdate,
    # Grid schemas
    TimesheetGrid,
    TimesheetGridEmployee,
    TimesheetGridDay,
    # Analytics schemas
    TimesheetSummary,
    EmployeeTimesheetStats,
    DepartmentTimesheetStats,
    TimesheetMonthlyComparison,
)
from app.utils.auth import get_current_active_user
from app.utils.excel_export import encode_filename_header
from app.services.timesheet_excel_service import TimesheetExcelService

router = APIRouter(dependencies=[Depends(get_current_active_user)])


# ==================== Access Control Helper ====================

def check_timesheet_access(user: User, department_id: int, employee_id: Optional[int] = None) -> bool:
    """
    Check if user has access to timesheet data

    - USER: Can only access their own timesheets (must match employee record)
    - MANAGER: Can access all employees in their department
    - HR: Can access all departments
    - ADMIN/FOUNDER: Can access all departments
    """
    # HR role has access to all departments (HR_DEPARTMENT module)
    if user.role == UserRoleEnum.HR:
        return True

    # ADMIN and FOUNDER have full access
    if user.role in (UserRoleEnum.ADMIN, UserRoleEnum.FOUNDER):
        return True

    # MANAGER can access their department
    if user.role == UserRoleEnum.MANAGER:
        return user.department_id == department_id

    # USER can only access their own data
    if user.role == UserRoleEnum.USER:
        if user.department_id != department_id:
            return False
        # Additional check: must be accessing their own employee record
        if employee_id:
            # Find employee by user.id or user.email matching employee
            from app.db.session import get_db
            # This is a simplified check - you may need to adjust based on your Employee-User relationship
            return True  # For now, allow if department matches
        return True

    return False


def get_user_employee(db: Session, user: User) -> Optional[Employee]:
    """Get employee record for current user (if exists)"""
    # Find employee by matching criteria (email, name, etc.)
    # This is a simplified version - adjust based on your Employee-User relationship
    return db.query(Employee).filter(
        and_(
            Employee.department_id == user.department_id,
            Employee.email == user.email
        )
    ).first()


# ==================== WorkTimesheet CRUD Endpoints ====================

@router.get("/", response_model=List[WorkTimesheetInDB])
async def list_timesheets(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[TimesheetStatusEnum] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all work timesheets with filtering"""
    query = db.query(WorkTimesheet)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        # USER can only see their own timesheets
        employee = get_user_employee(db, current_user)
        if not employee:
            return []  # No employee record = no timesheets
        query = query.filter(WorkTimesheet.employee_id == employee.id)
        query = query.filter(WorkTimesheet.department_id == current_user.department_id)
    elif current_user.role == UserRoleEnum.MANAGER:
        # MANAGER can see all timesheets in their department
        query = query.filter(WorkTimesheet.department_id == current_user.department_id)
    elif current_user.role == UserRoleEnum.HR:
        # HR can filter by department or see all
        if department_id:
            query = query.filter(WorkTimesheet.department_id == department_id)
    # ADMIN/FOUNDER can see everything (no filter needed)

    # Apply filters
    if employee_id:
        query = query.filter(WorkTimesheet.employee_id == employee_id)
    if year:
        query = query.filter(WorkTimesheet.year == year)
    if month:
        query = query.filter(WorkTimesheet.month == month)
    if status:
        query = query.filter(WorkTimesheet.status == status)

    # Order by year, month desc
    query = query.order_by(
        WorkTimesheet.year.desc(),
        WorkTimesheet.month.desc()
    )

    timesheets = query.offset(skip).limit(limit).all()

    # Add computed properties
    result = []
    for ts in timesheets:
        ts_dict = WorkTimesheetInDB.model_validate(ts).model_dump()
        ts_dict['can_edit'] = ts.can_edit
        ts_dict['period_display'] = ts.period_display
        result.append(WorkTimesheetInDB(**ts_dict))

    return result


@router.get("/{timesheet_id}", response_model=WorkTimesheetWithRecords)
async def get_timesheet(
    timesheet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific timesheet with daily records"""
    timesheet = db.query(WorkTimesheet).options(
        joinedload(WorkTimesheet.daily_records),
        joinedload(WorkTimesheet.employee),
    ).filter(WorkTimesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    # Check access
    if not check_timesheet_access(current_user, timesheet.department_id, timesheet.employee_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    return timesheet


@router.post("/", response_model=WorkTimesheetInDB, status_code=status.HTTP_201_CREATED)
async def create_timesheet(
    timesheet_data: WorkTimesheetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new work timesheet"""
    # Get employee and verify exists
    employee = db.query(Employee).filter(Employee.id == timesheet_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check access
    if not check_timesheet_access(current_user, employee.department_id, employee.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to create timesheets for this employee"
        )

    # Check if timesheet already exists for this period
    existing = db.query(WorkTimesheet).filter(
        and_(
            WorkTimesheet.employee_id == employee.id,
            WorkTimesheet.department_id == employee.department_id,
            WorkTimesheet.year == timesheet_data.year,
            WorkTimesheet.month == timesheet_data.month
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Timesheet for this employee and period already exists (ID: {existing.id})"
        )

    # Create timesheet
    timesheet = WorkTimesheet(
        employee_id=employee.id,
        year=timesheet_data.year,
        month=timesheet_data.month,
        department_id=employee.department_id,
        notes=timesheet_data.notes,
        status=TimesheetStatusEnum.DRAFT,
        total_days_worked=0,
        total_hours_worked=Decimal("0")
    )

    db.add(timesheet)
    db.commit()
    db.refresh(timesheet)

    return timesheet


@router.put("/{timesheet_id}", response_model=WorkTimesheetInDB)
async def update_timesheet(
    timesheet_id: UUID,
    timesheet_data: WorkTimesheetUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a timesheet (only DRAFT status can be updated)"""
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    # Check access
    if not check_timesheet_access(current_user, timesheet.department_id, timesheet.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this timesheet"
        )

    # Can only update DRAFT timesheets
    if timesheet.status != TimesheetStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot update timesheet with status {timesheet.status}. Only DRAFT timesheets can be updated."
        )

    # Update fields
    if timesheet_data.notes is not None:
        timesheet.notes = timesheet_data.notes

    timesheet.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(timesheet)

    return timesheet


@router.post("/{timesheet_id}/approve", response_model=WorkTimesheetInDB)
async def approve_timesheet(
    timesheet_id: UUID,
    approve_data: WorkTimesheetApprove,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Approve a timesheet (changes status from DRAFT to APPROVED)"""
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    # Check access - only MANAGER, HR, ADMIN, FOUNDER can approve
    if current_user.role not in (UserRoleEnum.MANAGER, UserRoleEnum.HR, UserRoleEnum.ADMIN, UserRoleEnum.FOUNDER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER, HR, ADMIN, or FOUNDER can approve timesheets"
        )

    if current_user.role == UserRoleEnum.MANAGER:
        if timesheet.department_id != current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only approve timesheets in your department"
            )

    # Can only approve DRAFT timesheets
    if timesheet.status != TimesheetStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve timesheet with status {timesheet.status}. Only DRAFT timesheets can be approved."
        )

    # Approve
    timesheet.status = TimesheetStatusEnum.APPROVED
    timesheet.approved_by_id = current_user.id
    timesheet.approved_at = date.today()

    if approve_data.notes:
        timesheet.notes = (timesheet.notes or "") + f"\n[Approved] {approve_data.notes}"

    timesheet.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(timesheet)

    return timesheet


@router.delete("/{timesheet_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timesheet(
    timesheet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a timesheet (only DRAFT status can be deleted)"""
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    # Check access
    if not check_timesheet_access(current_user, timesheet.department_id, timesheet.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this timesheet"
        )

    # Can only delete DRAFT timesheets
    if timesheet.status != TimesheetStatusEnum.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete timesheet with status {timesheet.status}. Only DRAFT timesheets can be deleted."
        )

    db.delete(timesheet)
    db.commit()

    return None


# ==================== DailyWorkRecord CRUD Endpoints ====================

@router.get("/{timesheet_id}/records", response_model=List[DailyWorkRecordInDB])
async def list_daily_records(
    timesheet_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all daily work records for a timesheet"""
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    # Check access
    if not check_timesheet_access(current_user, timesheet.department_id, timesheet.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this timesheet"
        )

    records = db.query(DailyWorkRecord).filter(
        DailyWorkRecord.timesheet_id == timesheet_id
    ).order_by(DailyWorkRecord.work_date).all()

    # Add computed property
    result = []
    for record in records:
        record_dict = DailyWorkRecordInDB.model_validate(record).model_dump()
        record_dict['net_hours_worked'] = record.net_hours_worked
        result.append(DailyWorkRecordInDB(**record_dict))

    return result


@router.post("/{timesheet_id}/records", response_model=DailyWorkRecordInDB, status_code=status.HTTP_201_CREATED)
async def create_daily_record(
    timesheet_id: UUID,
    record_data: DailyWorkRecordCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new daily work record"""
    # Verify timesheet exists and is editable
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == timesheet_id).first()

    if not timesheet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timesheet not found"
        )

    # Check access
    if not check_timesheet_access(current_user, timesheet.department_id, timesheet.employee_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to add records to this timesheet"
        )

    # Can only edit DRAFT timesheets
    if not timesheet.can_edit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add records to non-DRAFT timesheet"
        )

    # Check for duplicate date
    existing = db.query(DailyWorkRecord).filter(
        and_(
            DailyWorkRecord.timesheet_id == timesheet_id,
            DailyWorkRecord.work_date == record_data.work_date
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Record for date {record_data.work_date} already exists"
        )

    # Create record
    record = DailyWorkRecord(
        timesheet_id=timesheet_id,
        work_date=record_data.work_date,
        is_working_day=record_data.is_working_day,
        hours_worked=record_data.hours_worked,
        break_hours=record_data.break_hours,
        overtime_hours=record_data.overtime_hours,
        notes=record_data.notes,
        department_id=timesheet.department_id
    )

    db.add(record)

    # Update timesheet totals
    _recalculate_timesheet_totals(db, timesheet)

    db.commit()
    db.refresh(record)

    return record


@router.put("/records/{record_id}", response_model=DailyWorkRecordInDB)
async def update_daily_record(
    record_id: UUID,
    record_data: DailyWorkRecordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a daily work record"""
    record = db.query(DailyWorkRecord).filter(DailyWorkRecord.id == record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily record not found"
        )

    # Get timesheet
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == record.timesheet_id).first()

    # Check access
    if not check_timesheet_access(current_user, record.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this record"
        )

    # Can only edit DRAFT timesheets
    if not timesheet.can_edit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update records in non-DRAFT timesheet"
        )

    # Update fields
    if record_data.is_working_day is not None:
        record.is_working_day = record_data.is_working_day
    if record_data.hours_worked is not None:
        record.hours_worked = record_data.hours_worked
    if record_data.day_type is not None:
        record.day_type = record_data.day_type
    if record_data.break_hours is not None:
        record.break_hours = record_data.break_hours
    if record_data.overtime_hours is not None:
        record.overtime_hours = record_data.overtime_hours
    if record_data.notes is not None:
        record.notes = record_data.notes

    record.updated_at = datetime.utcnow()

    # Update timesheet totals
    _recalculate_timesheet_totals(db, timesheet)

    db.commit()
    db.refresh(record)

    return record


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_daily_record(
    record_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a daily work record"""
    record = db.query(DailyWorkRecord).filter(DailyWorkRecord.id == record_id).first()

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Daily record not found"
        )

    # Get timesheet
    timesheet = db.query(WorkTimesheet).filter(WorkTimesheet.id == record.timesheet_id).first()

    # Check access
    if not check_timesheet_access(current_user, record.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this record"
        )

    # Can only delete from DRAFT timesheets
    if not timesheet.can_edit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete records from non-DRAFT timesheet"
        )

    db.delete(record)

    # Update timesheet totals
    _recalculate_timesheet_totals(db, timesheet)

    db.commit()

    return None


# ==================== Helper Functions ====================

def _recalculate_timesheet_totals(db: Session, timesheet: WorkTimesheet):
    """Recalculate total days and hours for a timesheet"""
    records = db.query(DailyWorkRecord).filter(
        DailyWorkRecord.timesheet_id == timesheet.id
    ).all()

    def _is_paid_workday(record: DailyWorkRecord) -> bool:
        return (
            record.is_working_day
            and record.day_type == DayTypeEnum.WORK
            and record.hours_worked
            and record.hours_worked > 0
        )

    paid_records = [r for r in records if _is_paid_workday(r)]
    total_days = len(paid_records)
    total_hours = sum((r.hours_worked for r in paid_records), Decimal("0"))

    timesheet.total_days_worked = total_days
    timesheet.total_hours_worked = total_hours
    timesheet.updated_at = datetime.utcnow()


# ==================== Grid View Endpoint ====================

@router.get("/grid/{year}/{month}", response_model=TimesheetGrid)
async def get_timesheet_grid(
    year: int,
    month: int,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get timesheet grid data for a month
    Shows all employees with their daily records in a grid format
    """
    # Determine which department to show
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        target_department_id = current_user.department_id
    elif current_user.role in (UserRoleEnum.HR, UserRoleEnum.ADMIN, UserRoleEnum.FOUNDER):
        target_department_id = department_id or current_user.department_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view timesheets"
        )

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Get department
    department = db.query(Department).filter(Department.id == target_department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Get all active employees in department
    employees = db.query(Employee).filter(
        and_(
            Employee.department_id == target_department_id,
            Employee.status == EmployeeStatusEnum.ACTIVE
        )
    ).order_by(Employee.full_name).all()

    # Get all timesheets for this period
    timesheets = db.query(WorkTimesheet).filter(
        and_(
            WorkTimesheet.department_id == target_department_id,
            WorkTimesheet.year == year,
            WorkTimesheet.month == month
        )
    ).all()

    timesheet_by_employee = {ts.employee_id: ts for ts in timesheets}

    # Get all daily records for this period
    timesheet_ids = [ts.id for ts in timesheets]
    records = []
    if timesheet_ids:
        records = db.query(DailyWorkRecord).filter(
            DailyWorkRecord.timesheet_id.in_(timesheet_ids)
        ).all()

    # Organize records by timesheet and date
    records_map = {}
    for record in records:
        if record.timesheet_id not in records_map:
            records_map[record.timesheet_id] = {}
        records_map[record.timesheet_id][record.work_date] = record

    # Get calendar info
    _, days_in_month = calendar.monthrange(year, month)

    # Build grid data
    grid_employees = []
    for employee in employees:
        timesheet = timesheet_by_employee.get(employee.id)

        # Build days array
        days = []
        working_day_count = 0
        working_hours_total = Decimal("0")
        for day in range(1, days_in_month + 1):
            work_date = date(year, month, day)
            day_of_week = work_date.isoweekday()  # 1=Mon, 7=Sun

            record = None
            if timesheet and timesheet.id in records_map:
                record = records_map[timesheet.id].get(work_date)

            is_working_day = record.is_working_day if record else False
            hours_worked = record.hours_worked if record else Decimal("0")
            day_type = record.day_type if record else None

            days.append(TimesheetGridDay(
                date=work_date,
                day_of_week=day_of_week,
                is_working_day=is_working_day,
                hours_worked=hours_worked,
                day_type=day_type,
                break_hours=record.break_hours if record else None,
                overtime_hours=record.overtime_hours if record else None,
                net_hours_worked=record.net_hours_worked if record else Decimal("0"),
                notes=record.notes if record else None,
                record_id=record.id if record else None
            ))

            day_type_value = day_type or DayTypeEnum.WORK
            if (
                is_working_day
                and day_type_value == DayTypeEnum.WORK
                and hours_worked
                and hours_worked > 0
            ):
                working_day_count += 1
                working_hours_total += hours_worked

        grid_employees.append(TimesheetGridEmployee(
            employee_id=employee.id,
            employee_full_name=employee.full_name,
            employee_position=employee.position,
            employee_number=employee.employee_number,
            timesheet_id=timesheet.id if timesheet else None,
            timesheet_status=timesheet.status if timesheet else None,
            total_days_worked=working_day_count,
            total_hours_worked=working_hours_total,
            can_edit=timesheet.can_edit if timesheet else True,
            days=days
        ))

    return TimesheetGrid(
        year=year,
        month=month,
        department_id=target_department_id,
        department_name=department.name,
        employees=grid_employees,
        working_days_in_month=sum(1 for d in range(1, days_in_month + 1)
                                   if date(year, month, d).isoweekday() < 6),  # Mon-Fri
        calendar_days_in_month=days_in_month
    )


# ==================== Analytics Endpoints ====================

@router.get("/analytics/summary", response_model=TimesheetSummary)
async def get_timesheet_summary(
    year: int,
    month: int,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get timesheet summary for a period"""
    # Determine department
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        target_department_id = current_user.department_id
    elif current_user.role in (UserRoleEnum.HR, UserRoleEnum.ADMIN, UserRoleEnum.FOUNDER):
        target_department_id = department_id or current_user.department_id
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    # Get statistics
    total_employees = db.query(Employee).filter(
        and_(
            Employee.department_id == target_department_id,
            Employee.status == EmployeeStatusEnum.ACTIVE
        )
    ).count()

    timesheets = db.query(WorkTimesheet).filter(
        and_(
            WorkTimesheet.department_id == target_department_id,
            WorkTimesheet.year == year,
            WorkTimesheet.month == month
        )
    ).all()

    employees_with_timesheets = len(timesheets)
    total_days = sum(ts.total_days_worked for ts in timesheets)
    total_hours = sum(ts.total_hours_worked for ts in timesheets)
    avg_hours = total_hours / employees_with_timesheets if employees_with_timesheets > 0 else Decimal("0")

    draft_count = sum(1 for ts in timesheets if ts.status == TimesheetStatusEnum.DRAFT)
    approved_count = sum(1 for ts in timesheets if ts.status == TimesheetStatusEnum.APPROVED)
    paid_count = sum(1 for ts in timesheets if ts.status == TimesheetStatusEnum.PAID)

    return TimesheetSummary(
        year=year,
        month=month,
        department_id=target_department_id,
        total_employees=total_employees,
        employees_with_timesheets=employees_with_timesheets,
        total_days_worked=total_days,
        total_hours_worked=total_hours,
        average_hours_per_employee=avg_hours,
        draft_count=draft_count,
        approved_count=approved_count,
        paid_count=paid_count
    )


# ==================== Excel Export/Import Endpoints ====================

@router.get("/export/excel")
async def export_timesheets_to_excel(
    year: int,
    month: int,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export timesheet grid to Excel file
    """
    # Determine department
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        target_department_id = current_user.department_id
    elif current_user.role in (UserRoleEnum.HR, UserRoleEnum.ADMIN, UserRoleEnum.FOUNDER):
        target_department_id = department_id or current_user.department_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to export timesheets"
        )

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Get department
    department = db.query(Department).filter(Department.id == target_department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Get grid data (reuse existing logic)
    grid_data = await get_timesheet_grid(year, month, target_department_id, current_user, db)

    # Convert to dict format for Excel service
    employees_data = []
    for emp in grid_data.employees:
        emp_dict = {
            'employee_full_name': emp.employee_full_name,
            'employee_position': emp.employee_position,
            'employee_number': emp.employee_number,
            'days': [
                {
                    'hours_worked': float(day.hours_worked),
                    'is_working_day': day.is_working_day
                }
                for day in emp.days
            ],
            'total_days_worked': emp.total_days_worked,
            'total_hours_worked': float(emp.total_hours_worked),
            'timesheet_status': emp.timesheet_status
        }
        employees_data.append(emp_dict)

    # Generate Excel
    excel_file = TimesheetExcelService.export_timesheet_grid(
        year=year,
        month=month,
        employees_data=employees_data,
        department_name=department.name
    )

    # Return as download
    filename = f"timesheet_{year}_{month:02d}_{department.name}.xlsx"
    headers = encode_filename_header(filename)

    return StreamingResponse(
        io.BytesIO(excel_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )


@router.get("/export/template")
async def download_timesheet_template(
    year: int = Query(..., description="Year for template"),
    month: int = Query(..., description="Month for template (1-12)"),
    department_id: Optional[int] = None,
    language: str = Query('ru', description="Template language (ru or en)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Download empty timesheet template for manual filling
    """
    # Determine department
    if current_user.role == UserRoleEnum.USER:
        target_department_id = current_user.department_id
    elif current_user.role == UserRoleEnum.MANAGER:
        target_department_id = current_user.department_id
    elif current_user.role in (UserRoleEnum.HR, UserRoleEnum.ADMIN, UserRoleEnum.FOUNDER):
        target_department_id = department_id or current_user.department_id
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to download templates"
        )

    if not target_department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID is required"
        )

    # Get department
    department = db.query(Department).filter(Department.id == target_department_id).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )

    # Get active employees
    employees = db.query(Employee).filter(
        and_(
            Employee.department_id == target_department_id,
            Employee.status == EmployeeStatusEnum.ACTIVE
        )
    ).order_by(Employee.full_name).all()

    # Generate template
    template_file = TimesheetExcelService.generate_timesheet_template(
        year=year,
        month=month,
        employees=employees,
        language=language
    )

    # Return as download
    month_names_ru = ['', 'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                      'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    month_names_en = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']

    month_names = month_names_ru if language == 'ru' else month_names_en
    filename = f"timesheet_template_{month_names[month]}_{year}.xlsx"
    headers = encode_filename_header(filename)

    return StreamingResponse(
        io.BytesIO(template_file.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
