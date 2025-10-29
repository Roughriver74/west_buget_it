"""
KPI (Key Performance Indicators) API endpoints
Handles KPI goals, employee KPI tracking, and performance-based bonuses
"""
import io
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, Integer
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pandas as pd

from app.db.session import get_db
from app.db.models import (
    KPIGoal, EmployeeKPI, EmployeeKPIGoal, Employee, User, UserRoleEnum, Department,
    BonusTypeEnum, KPIGoalStatusEnum, EmployeeStatusEnum
)
from app.schemas.kpi import (
    KPIGoalCreate,
    KPIGoalUpdate,
    KPIGoalInDB,
    EmployeeKPICreate,
    EmployeeKPIUpdate,
    EmployeeKPIInDB,
    EmployeeKPIWithGoals,
    EmployeeKPIGoalCreate,
    EmployeeKPIGoalUpdate,
    EmployeeKPIGoalInDB,
    EmployeeKPIGoalWithDetails,
    KPIEmployeeSummary,
    KPIDepartmentSummary,
    KPIGoalProgress,
)
from app.utils.auth import get_current_active_user

router = APIRouter(dependencies=[Depends(get_current_active_user)])


MONTH_NAME_TO_NUMBER: Dict[str, int] = {
    'январь': 1,
    'февраль': 2,
    'март': 3,
    'апрель': 4,
    'май': 5,
    'июнь': 6,
    'июль': 7,
    'август': 8,
    'сентябрь': 9,
    'октябрь': 10,
    'ноябрь': 11,
    'декабрь': 12,
}


def check_department_access(user: User, department_id: int) -> bool:
    """
    Check if user has access to the department

    - ADMIN: Can access all departments
    - MANAGER: Can only access their own department
    - USER: Can only access their own department
    """
    if user.role == UserRoleEnum.ADMIN:
        return True
    # MANAGER and USER can only access their own department
    if user.role in [UserRoleEnum.MANAGER, UserRoleEnum.USER]:
        if not user.department_id:
            return False
        return user.department_id == department_id
    return False


def calculate_bonus(
    base_amount: Decimal,
    bonus_type: BonusTypeEnum,
    kpi_percentage: Optional[Decimal],
    fixed_part: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate bonus based on type and KPI percentage

    Args:
        base_amount: Base bonus amount
        bonus_type: Type of bonus calculation
        kpi_percentage: Employee KPI percentage (0-200)
        fixed_part: Percentage of fixed part for MIXED type (0-100)

    Returns:
        Calculated bonus amount
    """
    if bonus_type == BonusTypeEnum.FIXED:
        return base_amount

    elif bonus_type == BonusTypeEnum.PERFORMANCE_BASED:
        if kpi_percentage is None:
            return Decimal(0)
        return base_amount * (kpi_percentage / Decimal(100))

    elif bonus_type == BonusTypeEnum.MIXED:
        if kpi_percentage is None or fixed_part is None:
            return base_amount
        # Fixed part + performance part
        fixed_amount = base_amount * (fixed_part / Decimal(100))
        performance_amount = base_amount * ((Decimal(100) - fixed_part) / Decimal(100)) * (kpi_percentage / Decimal(100))
        return fixed_amount + performance_amount

    return Decimal(0)


def to_decimal(value) -> Optional[Decimal]:
    """Safely convert value to Decimal or return None."""
    if value is None:
        return None
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, str):
        normalized = value.strip().replace(' ', '').replace(',', '.')
        if not normalized:
            return None
        value = normalized
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


# ==================== KPI Goals Endpoints ====================

@router.get("/goals", response_model=List[KPIGoalInDB])
async def list_kpi_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    year: Optional[int] = None,
    status: Optional[KPIGoalStatusEnum] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all KPI goals with filtering options"""
    query = db.query(KPIGoal)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(KPIGoal.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(KPIGoal.department_id == department_id)

    # Apply filters
    if year:
        query = query.filter(KPIGoal.year == year)
    if status:
        query = query.filter(KPIGoal.status == status)
    if category:
        query = query.filter(KPIGoal.category == category)

    goals = query.offset(skip).limit(limit).all()
    return goals


@router.get("/goals/{goal_id}", response_model=KPIGoalInDB)
async def get_kpi_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific KPI goal by ID"""
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_id).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_id} not found"
        )

    # Check access
    if not check_department_access(current_user, goal.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this goal"
        )

    return goal


@router.post("/goals", response_model=KPIGoalInDB, status_code=status.HTTP_201_CREATED)
async def create_kpi_goal(
    goal_data: KPIGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new KPI goal"""
    # Check access
    if not check_department_access(current_user, goal_data.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create goal for this department"
        )

    goal = KPIGoal(**goal_data.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@router.put("/goals/{goal_id}", response_model=KPIGoalInDB)
async def update_kpi_goal(
    goal_id: int,
    goal_data: KPIGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a KPI goal"""
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_id).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_id} not found"
        )

    # Check access
    if not check_department_access(current_user, goal.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this goal"
        )

    # Update fields
    update_data = goal_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)

    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)

    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi_goal(
    goal_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a KPI goal"""
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_id).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_id} not found"
        )

    # Check access
    if not check_department_access(current_user, goal.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this goal"
        )

    db.delete(goal)
    db.commit()


# ==================== Employee KPI Endpoints ====================

@router.get("/employee-kpis", response_model=List[EmployeeKPIWithGoals])
async def list_employee_kpis(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all employee KPIs with filtering options"""
    query = db.query(EmployeeKPI)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(EmployeeKPI.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(EmployeeKPI.department_id == department_id)

    # Apply filters
    if employee_id:
        query = query.filter(EmployeeKPI.employee_id == employee_id)
    if year:
        query = query.filter(EmployeeKPI.year == year)
    if month:
        query = query.filter(EmployeeKPI.month == month)

    kpis = query.offset(skip).limit(limit).all()
    return kpis


@router.get("/employee-kpis/{kpi_id}", response_model=EmployeeKPIWithGoals)
async def get_employee_kpi(
    kpi_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific employee KPI by ID"""
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.id == kpi_id).first()

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI with id {kpi_id} not found"
        )

    # Check access
    if not check_department_access(current_user, kpi.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this KPI"
        )

    return kpi


@router.post("/employee-kpis", response_model=EmployeeKPIInDB, status_code=status.HTTP_201_CREATED)
async def create_employee_kpi(
    kpi_data: EmployeeKPICreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Create a new employee KPI record"""
    # Check access
    if not check_department_access(current_user, kpi_data.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to create KPI for this department"
        )

    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == kpi_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {kpi_data.employee_id} not found"
        )

    # Check for duplicate (employee_id, year, month)
    existing = db.query(EmployeeKPI).filter(
        and_(
            EmployeeKPI.employee_id == kpi_data.employee_id,
            EmployeeKPI.year == kpi_data.year,
            EmployeeKPI.month == kpi_data.month
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Employee KPI for {kpi_data.year}-{kpi_data.month:02d} already exists"
        )

    # Create KPI record
    kpi_dict = kpi_data.model_dump()

    # Calculate bonuses if not provided
    if kpi_data.kpi_percentage is not None:
        if kpi_dict.get('monthly_bonus_calculated') is None:
            kpi_dict['monthly_bonus_calculated'] = calculate_bonus(
                kpi_data.monthly_bonus_base,
                kpi_data.monthly_bonus_type,
                kpi_data.kpi_percentage,
                kpi_data.monthly_bonus_fixed_part
            )

        if kpi_dict.get('quarterly_bonus_calculated') is None:
            kpi_dict['quarterly_bonus_calculated'] = calculate_bonus(
                kpi_data.quarterly_bonus_base,
                kpi_data.quarterly_bonus_type,
                kpi_data.kpi_percentage,
                kpi_data.quarterly_bonus_fixed_part
            )

        if kpi_dict.get('annual_bonus_calculated') is None:
            kpi_dict['annual_bonus_calculated'] = calculate_bonus(
                kpi_data.annual_bonus_base,
                kpi_data.annual_bonus_type,
                kpi_data.kpi_percentage,
                kpi_data.annual_bonus_fixed_part
            )

    kpi = EmployeeKPI(**kpi_dict)
    db.add(kpi)
    db.commit()
    db.refresh(kpi)

    return kpi


@router.put("/employee-kpis/{kpi_id}", response_model=EmployeeKPIInDB)
async def update_employee_kpi(
    kpi_id: int,
    kpi_data: EmployeeKPIUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an employee KPI record"""
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.id == kpi_id).first()

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI with id {kpi_id} not found"
        )

    # Check access
    if not check_department_access(current_user, kpi.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this KPI"
        )

    # Update fields
    update_data = kpi_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(kpi, field, value)

    # Recalculate bonuses if KPI percentage changed
    if 'kpi_percentage' in update_data and kpi.kpi_percentage is not None:
        kpi.monthly_bonus_calculated = calculate_bonus(
            kpi.monthly_bonus_base,
            kpi.monthly_bonus_type,
            kpi.kpi_percentage,
            kpi.monthly_bonus_fixed_part
        )
        kpi.quarterly_bonus_calculated = calculate_bonus(
            kpi.quarterly_bonus_base,
            kpi.quarterly_bonus_type,
            kpi.kpi_percentage,
            kpi.quarterly_bonus_fixed_part
        )
        kpi.annual_bonus_calculated = calculate_bonus(
            kpi.annual_bonus_base,
            kpi.annual_bonus_type,
            kpi.kpi_percentage,
            kpi.annual_bonus_fixed_part
        )

    kpi.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(kpi)

    return kpi


@router.delete("/employee-kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_kpi(
    kpi_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an employee KPI record"""
    kpi = db.query(EmployeeKPI).filter(EmployeeKPI.id == kpi_id).first()

    if not kpi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI with id {kpi_id} not found"
        )

    # Check access
    if not check_department_access(current_user, kpi.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this KPI"
        )

    db.delete(kpi)
    db.commit()


@router.post("/employee-kpis/import", status_code=status.HTTP_200_OK)
async def import_employee_kpis(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import employee KPI records from Excel file (KPI_Manager_2025.xlsx template).

    The workbook must contain:
    - Sheet "УПРАВЛЕНИЕ КПИ" with summary table (columns: Сотрудник, Базовая премия, Вариант премии, КПИ Общий %).
    - Individual sheets per employee with table that starts with header "Месяц" including "КПИ %" and "Месячная премия".
    """
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can import KPI data"
        )

    # Validate file extension
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty"
        )

    max_size = 10 * 1024 * 1024  # 10 MB
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large. Maximum size is 10MB"
        )

    try:
        sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, header=None)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid Excel file format: {str(exc)}"
        )

    if not sheets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Excel workbook is empty"
        )

    summary_df = None
    for sheet_name, df in sheets.items():
        if isinstance(sheet_name, str) and sheet_name.strip().lower() == 'управление кпи':
            summary_df = df
            break

    if summary_df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sheet 'УПРАВЛЕНИЕ КПИ' not found in workbook"
        )

    # Determine year (first 4-digit value in first column)
    import_year = None
    for value in summary_df.iloc[:, 0].dropna():
        try:
            numeric_value = int(value)
        except (TypeError, ValueError):
            continue
        if 2000 <= numeric_value <= 2100:
            import_year = numeric_value
            break

    if import_year is None:
        import_year = datetime.utcnow().year

    header_row_index = None
    for idx, value in summary_df.iloc[:, 0].items():
        if isinstance(value, str) and value.strip().lower() == 'сотрудник':
            header_row_index = idx
            break

    if header_row_index is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not find header row with column 'Сотрудник' on summary sheet"
        )

    summary_rows = summary_df.iloc[header_row_index + 1:].copy()
    summary_rows = summary_rows[summary_rows.iloc[:, 0].notna()]
    summary_rows = summary_rows[summary_rows.iloc[:, 0].astype(str).str.strip() != 'ИТОГО:']

    employees_info = []
    for _, row in summary_rows.iterrows():
        employee_name = str(row.iloc[0]).strip()
        if not employee_name:
            continue
        base_bonus = to_decimal(row.iloc[4]) if len(row) > 4 else None
        bonus_type_label = str(row.iloc[5]).strip().lower() if len(row) > 5 and isinstance(row.iloc[5], str) else ''
        overall_kpi = to_decimal(row.iloc[6]) if len(row) > 6 else None
        employees_info.append(
            {
                "name": employee_name,
                "base_bonus": base_bonus,
                "bonus_type_label": bonus_type_label,
                "overall_kpi": overall_kpi,
            }
        )

    if not employees_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No employees found on summary sheet"
        )

    bonus_type_map = {
        'результативный': BonusTypeEnum.PERFORMANCE_BASED,
        'performance': BonusTypeEnum.PERFORMANCE_BASED,
        'fixed': BonusTypeEnum.FIXED,
        'фиксированный': BonusTypeEnum.FIXED,
        'mixed': BonusTypeEnum.MIXED,
        'смешанный': BonusTypeEnum.MIXED,
    }

    special_sheets = {'управление кпи', 'аналитика', 'календарь'}

    created_count = 0
    updated_count = 0
    missing_employees: List[str] = []
    missing_sheets: List[str] = []
    permission_skipped: List[str] = []

    for info in employees_info:
        employee_name = info["name"]
        employee = (
            db.query(Employee)
            .filter(func.lower(Employee.full_name) == employee_name.lower())
            .first()
        )

        if not employee:
            missing_employees.append(employee_name)
            continue

        if employee.department_id is None:
            permission_skipped.append(employee_name)
            continue

        if not check_department_access(current_user, employee.department_id):
            permission_skipped.append(employee_name)
            continue

        employee_sheet = None
        for sheet_name, df in sheets.items():
            if not isinstance(sheet_name, str):
                continue
            if sheet_name.strip().lower() in special_sheets:
                continue
            if df.empty:
                continue
            first_cell = df.iloc[0, 0]
            if isinstance(first_cell, str) and employee_name.lower() in first_cell.lower():
                employee_sheet = df
                break

        if employee_sheet is None:
            missing_sheets.append(employee_name)
            continue

        header_idx = None
        for idx, value in employee_sheet.iloc[:, 0].items():
            if isinstance(value, str) and value.strip().lower() == 'месяц':
                header_idx = idx
                break

        if header_idx is None:
            missing_sheets.append(employee_name)
            continue

        headers = []
        for col in employee_sheet.iloc[header_idx].tolist():
            if isinstance(col, str):
                headers.append(col.strip())
            else:
                headers.append('')
        header_map = {col: idx for idx, col in enumerate(headers) if col}

        bonus_type_enum = bonus_type_map.get(info["bonus_type_label"], BonusTypeEnum.PERFORMANCE_BASED)
        monthly_bonus_base = info["base_bonus"] or Decimal(0)

        data_rows = employee_sheet.iloc[header_idx + 1:]

        for _, data_row in data_rows.iterrows():
            month_name_raw = data_row.iloc[0]
            if isinstance(month_name_raw, float) and pd.isna(month_name_raw):
                continue
            if not isinstance(month_name_raw, str):
                continue
            month_name = month_name_raw.strip()
            if not month_name:
                continue
            lower_month = month_name.lower()
            if lower_month.startswith('квартал') or 'итог' in lower_month:
                break
            month_number = MONTH_NAME_TO_NUMBER.get(lower_month)
            if not month_number:
                continue

            kpi_percentage = None
            if 'КПИ %' in header_map:
                kpi_percentage = to_decimal(data_row.iloc[header_map['КПИ %']])

            monthly_bonus_calculated = None
            if 'Месячная премия' in header_map:
                monthly_bonus_calculated = to_decimal(data_row.iloc[header_map['Месячная премия']])

            quarterly_bonus_calculated = None
            if 'Квартальная премия' in header_map:
                quarterly_bonus_calculated = to_decimal(data_row.iloc[header_map['Квартальная премия']])

            notes_value = None
            if 'Комментарии' in header_map:
                notes_cell = data_row.iloc[header_map['Комментарии']]
                if isinstance(notes_cell, str) and notes_cell.strip():
                    notes_value = notes_cell.strip()

            if monthly_bonus_calculated is None and kpi_percentage is not None:
                monthly_bonus_calculated = calculate_bonus(
                    monthly_bonus_base,
                    bonus_type_enum,
                    kpi_percentage,
                )

            kpi_record = (
                db.query(EmployeeKPI)
                .filter(
                    EmployeeKPI.employee_id == employee.id,
                    EmployeeKPI.year == import_year,
                    EmployeeKPI.month == month_number,
                )
                .first()
            )

            is_new_record = False
            if not kpi_record:
                kpi_record = EmployeeKPI(
                    employee_id=employee.id,
                    year=import_year,
                    month=month_number,
                    department_id=employee.department_id,
                )
                db.add(kpi_record)
                is_new_record = True

            kpi_record.kpi_percentage = kpi_percentage
            kpi_record.monthly_bonus_type = bonus_type_enum
            kpi_record.quarterly_bonus_type = bonus_type_enum
            kpi_record.annual_bonus_type = bonus_type_enum
            kpi_record.monthly_bonus_base = monthly_bonus_base
            kpi_record.quarterly_bonus_base = Decimal(0)
            kpi_record.annual_bonus_base = Decimal(0)
            kpi_record.monthly_bonus_calculated = monthly_bonus_calculated or Decimal(0)
            kpi_record.quarterly_bonus_calculated = quarterly_bonus_calculated or Decimal(0)
            kpi_record.annual_bonus_calculated = Decimal(0)
            kpi_record.notes = notes_value
            kpi_record.updated_at = datetime.utcnow()

            if is_new_record:
                created_count += 1
            else:
                updated_count += 1

    db.commit()

    return {
        "created": created_count,
        "updated": updated_count,
        "missing_employees": missing_employees,
        "missing_sheets": missing_sheets,
        "no_access": permission_skipped,
        "year": import_year,
    }


# ==================== Employee KPI Goals Endpoints ====================

@router.get("/employee-kpi-goals", response_model=List[EmployeeKPIGoalWithDetails])
async def list_employee_kpi_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    employee_id: Optional[int] = None,
    goal_id: Optional[int] = None,
    year: Optional[int] = None,
    month: Optional[int] = None,
    status: Optional[KPIGoalStatusEnum] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all employee KPI goal assignments

    - USER: Can only see assignments for their own department
    - MANAGER: Can filter by department_id, defaults to own department
    - ADMIN: Can see all departments or filter by department_id
    """
    query = db.query(EmployeeKPIGoal)

    # Apply filters
    if employee_id:
        query = query.filter(EmployeeKPIGoal.employee_id == employee_id)
    if goal_id:
        query = query.filter(EmployeeKPIGoal.goal_id == goal_id)
    if year:
        query = query.filter(EmployeeKPIGoal.year == year)
    if month is not None:
        query = query.filter(EmployeeKPIGoal.month == month)
    if status:
        query = query.filter(EmployeeKPIGoal.status == status)

    # Department filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        # USER must only see their own department
        query = query.join(Employee).filter(Employee.department_id == current_user.department_id)
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager has no assigned department"
            )
        # MANAGER can only see their own department
        query = query.join(Employee).filter(Employee.department_id == current_user.department_id)
    elif current_user.role == UserRoleEnum.ADMIN:
        # ADMIN can optionally filter by department
        if department_id:
            query = query.join(Employee).filter(Employee.department_id == department_id)
        else:
            # Need to join Employee for proper querying
            query = query.join(Employee)

    goal_assignments = query.offset(skip).limit(limit).all()
    return goal_assignments


@router.post("/employee-kpi-goals", response_model=EmployeeKPIGoalInDB, status_code=status.HTTP_201_CREATED)
async def create_employee_kpi_goal(
    goal_data: EmployeeKPIGoalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Assign a KPI goal to an employee"""
    # Check if employee exists
    employee = db.query(Employee).filter(Employee.id == goal_data.employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee with id {goal_data.employee_id} not found"
        )

    # Check access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to assign goal to this employee"
        )

    # Check if goal exists
    goal = db.query(KPIGoal).filter(KPIGoal.id == goal_data.goal_id).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"KPI Goal with id {goal_data.goal_id} not found"
        )

    # Create assignment
    goal_assignment = EmployeeKPIGoal(**goal_data.model_dump())
    db.add(goal_assignment)
    db.commit()
    db.refresh(goal_assignment)

    return goal_assignment


@router.put("/employee-kpi-goals/{assignment_id}", response_model=EmployeeKPIGoalInDB)
async def update_employee_kpi_goal(
    assignment_id: int,
    goal_data: EmployeeKPIGoalUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update an employee KPI goal assignment"""
    assignment = db.query(EmployeeKPIGoal).filter(EmployeeKPIGoal.id == assignment_id).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI goal assignment with id {assignment_id} not found"
        )

    # Check access through employee
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee or not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to update this assignment"
        )

    # Update fields
    update_data = goal_data.model_dump(exclude_unset=True)

    # Auto-calculate achievement percentage if actual_value provided
    if 'actual_value' in update_data and assignment.target_value and assignment.target_value > 0:
        achievement_pct = (update_data['actual_value'] / assignment.target_value) * Decimal(100)
        update_data['achievement_percentage'] = achievement_pct

    for field, value in update_data.items():
        setattr(assignment, field, value)

    assignment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assignment)

    return assignment


@router.delete("/employee-kpi-goals/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee_kpi_goal(
    assignment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete an employee KPI goal assignment"""
    assignment = db.query(EmployeeKPIGoal).filter(EmployeeKPIGoal.id == assignment_id).first()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee KPI goal assignment with id {assignment_id} not found"
        )

    # Check access
    employee = db.query(Employee).filter(Employee.id == assignment.employee_id).first()
    if not employee or not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to delete this assignment"
        )

    db.delete(assignment)
    db.commit()


# ==================== KPI Analytics Endpoints ====================

@router.get("/analytics/employee-summary", response_model=List[KPIEmployeeSummary])
async def get_employee_kpi_summary(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get KPI summary for employees"""
    query = db.query(
        EmployeeKPI.employee_id,
        Employee.full_name.label('employee_name'),
        Employee.position,
        EmployeeKPI.year,
        EmployeeKPI.month,
        EmployeeKPI.kpi_percentage,
        (EmployeeKPI.monthly_bonus_calculated +
         EmployeeKPI.quarterly_bonus_calculated +
         EmployeeKPI.annual_bonus_calculated).label('total_bonus_calculated'),
        EmployeeKPI.monthly_bonus_calculated,
        EmployeeKPI.quarterly_bonus_calculated,
        EmployeeKPI.annual_bonus_calculated,
        func.count(EmployeeKPIGoal.id).label('goals_count'),
        func.sum(
            func.cast(EmployeeKPIGoal.status == KPIGoalStatusEnum.ACHIEVED, Integer)
        ).label('goals_achieved')
    ).join(Employee).outerjoin(EmployeeKPIGoal).filter(
        EmployeeKPI.year == year
    )

    if month is not None:
        query = query.filter(EmployeeKPI.month == month)

    # Department filter
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    query = query.group_by(
        EmployeeKPI.employee_id,
        Employee.full_name,
        Employee.position,
        EmployeeKPI.year,
        EmployeeKPI.month,
        EmployeeKPI.kpi_percentage,
        EmployeeKPI.monthly_bonus_calculated,
        EmployeeKPI.quarterly_bonus_calculated,
        EmployeeKPI.annual_bonus_calculated
    )

    results = query.all()

    return [
        KPIEmployeeSummary(
            employee_id=r.employee_id,
            employee_name=r.employee_name,
            position=r.position,
            year=r.year,
            month=r.month,
            kpi_percentage=r.kpi_percentage,
            total_bonus_calculated=r.total_bonus_calculated or Decimal(0),
            monthly_bonus_calculated=r.monthly_bonus_calculated or Decimal(0),
            quarterly_bonus_calculated=r.quarterly_bonus_calculated or Decimal(0),
            annual_bonus_calculated=r.annual_bonus_calculated or Decimal(0),
            goals_count=r.goals_count or 0,
            goals_achieved=r.goals_achieved or 0
        )
        for r in results
    ]


@router.get("/analytics/department-summary", response_model=List[KPIDepartmentSummary])
async def get_department_kpi_summary(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get KPI summary grouped by department"""
    query = db.query(
        Department.id.label('department_id'),
        Department.name.label('department_name'),
        EmployeeKPI.year,
        EmployeeKPI.month,
        func.avg(EmployeeKPI.kpi_percentage).label('avg_kpi_percentage'),
        func.count(func.distinct(EmployeeKPI.employee_id)).label('total_employees'),
        func.sum(
            EmployeeKPI.monthly_bonus_calculated +
            EmployeeKPI.quarterly_bonus_calculated +
            EmployeeKPI.annual_bonus_calculated
        ).label('total_bonus_calculated'),
        func.count(func.distinct(EmployeeKPIGoal.id)).label('goals_count'),
        func.sum(
            func.cast(EmployeeKPIGoal.status == KPIGoalStatusEnum.ACHIEVED, Integer)
        ).label('goals_achieved')
    ).join(Employee, Employee.department_id == Department.id).join(
        EmployeeKPI, EmployeeKPI.employee_id == Employee.id
    ).outerjoin(EmployeeKPIGoal).filter(
        EmployeeKPI.year == year
    )

    if month is not None:
        query = query.filter(EmployeeKPI.month == month)

    # Department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Department.id == current_user.department_id)
    elif department_id:
        query = query.filter(Department.id == department_id)

    query = query.group_by(
        Department.id,
        Department.name,
        EmployeeKPI.year,
        EmployeeKPI.month
    )

    results = query.all()

    return [
        KPIDepartmentSummary(
            department_id=r.department_id,
            department_name=r.department_name,
            year=r.year,
            month=r.month,
            avg_kpi_percentage=r.avg_kpi_percentage or Decimal(0),
            total_employees=r.total_employees or 0,
            total_bonus_calculated=r.total_bonus_calculated or Decimal(0),
            goals_count=r.goals_count or 0,
            goals_achieved=r.goals_achieved or 0
        )
        for r in results
    ]


@router.get("/analytics/goal-progress", response_model=List[KPIGoalProgress])
async def get_goal_progress(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get progress tracking for all KPI goals"""
    query = db.query(
        KPIGoal.id.label('goal_id'),
        KPIGoal.name.label('goal_name'),
        KPIGoal.category,
        KPIGoal.target_value,
        KPIGoal.metric_unit,
        func.count(func.distinct(EmployeeKPIGoal.employee_id)).label('employees_assigned'),
        func.sum(
            func.cast(EmployeeKPIGoal.status == KPIGoalStatusEnum.ACHIEVED, Integer)
        ).label('employees_achieved'),
        func.avg(EmployeeKPIGoal.achievement_percentage).label('avg_achievement_percentage'),
        func.sum(EmployeeKPIGoal.weight).label('total_weight')
    ).outerjoin(
        EmployeeKPIGoal,
        and_(
            EmployeeKPIGoal.goal_id == KPIGoal.id,
            EmployeeKPIGoal.year == year
        )
    ).filter(
        KPIGoal.year == year
    )

    if month is not None:
        query = query.filter(
            or_(
                EmployeeKPIGoal.month == month,
                EmployeeKPIGoal.month.is_(None)  # Include annual goals
            )
        )

    # Department filter
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(KPIGoal.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(KPIGoal.department_id == department_id)

    query = query.group_by(
        KPIGoal.id,
        KPIGoal.name,
        KPIGoal.category,
        KPIGoal.target_value,
        KPIGoal.metric_unit
    )

    results = query.all()

    return [
        KPIGoalProgress(
            goal_id=r.goal_id,
            goal_name=r.goal_name,
            category=r.category,
            target_value=r.target_value,
            metric_unit=r.metric_unit,
            employees_assigned=r.employees_assigned or 0,
            employees_achieved=r.employees_achieved or 0,
            avg_achievement_percentage=r.avg_achievement_percentage or Decimal(0),
            total_weight=r.total_weight or Decimal(0)
        )
        for r in results
    ]


@router.get("/analytics/kpi-trends")
async def get_kpi_trends(
    year: int,
    employee_id: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get KPI trends over months"""
    query = db.query(
        EmployeeKPI.month,
        func.avg(EmployeeKPI.kpi_percentage).label('avg_kpi'),
        func.min(EmployeeKPI.kpi_percentage).label('min_kpi'),
        func.max(EmployeeKPI.kpi_percentage).label('max_kpi'),
        func.count(func.distinct(EmployeeKPI.employee_id)).label('employee_count'),
        func.sum(
            EmployeeKPI.monthly_bonus_calculated +
            EmployeeKPI.quarterly_bonus_calculated +
            EmployeeKPI.annual_bonus_calculated
        ).label('total_bonus')
    ).filter(EmployeeKPI.year == year)

    # Department filter
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(EmployeeKPI.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(EmployeeKPI.department_id == department_id)

    if employee_id:
        query = query.filter(EmployeeKPI.employee_id == employee_id)

    query = query.group_by(EmployeeKPI.month).order_by(EmployeeKPI.month)

    results = query.all()

    return [
        {
            "month": r.month,
            "avg_kpi": float(r.avg_kpi or 0),
            "min_kpi": float(r.min_kpi or 0),
            "max_kpi": float(r.max_kpi or 0),
            "employee_count": r.employee_count or 0,
            "total_bonus": float(r.total_bonus or 0)
        }
        for r in results
    ]


@router.get("/analytics/bonus-distribution")
async def get_bonus_distribution(
    year: int,
    month: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get bonus distribution by department and type

    - USER: Can only see their own department
    - MANAGER: Can only see their own department
    - ADMIN: Can see all departments or filter by department_id
    """
    query = db.query(
        Department.id.label('department_id'),
        Department.name.label('department_name'),
        func.sum(EmployeeKPI.monthly_bonus_calculated).label('monthly_total'),
        func.sum(EmployeeKPI.quarterly_bonus_calculated).label('quarterly_total'),
        func.sum(EmployeeKPI.annual_bonus_calculated).label('annual_total'),
        func.sum(
            EmployeeKPI.monthly_bonus_calculated +
            EmployeeKPI.quarterly_bonus_calculated +
            EmployeeKPI.annual_bonus_calculated
        ).label('total_bonus'),
        func.count(func.distinct(EmployeeKPI.employee_id)).label('employee_count')
    ).join(Employee, Employee.department_id == Department.id).join(
        EmployeeKPI, EmployeeKPI.employee_id == Employee.id
    ).filter(EmployeeKPI.year == year)

    if month is not None:
        query = query.filter(EmployeeKPI.month == month)

    # Department filter based on role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Department.id == current_user.department_id)
    elif current_user.role == UserRoleEnum.MANAGER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Manager has no assigned department"
            )
        # MANAGER can only see their own department
        query = query.filter(Department.id == current_user.department_id)
    elif current_user.role == UserRoleEnum.ADMIN:
        # ADMIN can optionally filter by department
        if department_id:
            query = query.filter(Department.id == department_id)

    query = query.group_by(Department.id, Department.name)

    results = query.all()

    return [
        {
            "department_id": r.department_id,
            "department_name": r.department_name,
            "monthly_total": float(r.monthly_total or 0),
            "quarterly_total": float(r.quarterly_total or 0),
            "annual_total": float(r.annual_total or 0),
            "total_bonus": float(r.total_bonus or 0),
            "employee_count": r.employee_count or 0
        }
        for r in results
    ]


@router.post("/import", status_code=status.HTTP_200_OK)
async def import_kpi_from_excel(
    file: UploadFile = File(...),
    year: int = Query(..., description="Year for KPI data"),
    month: int = Query(..., ge=1, le=12, description="Month for KPI data (1-12)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Import KPI data from Excel file (KPI_Manager_2025.xlsx format)

    Expected structure:
    - Sheet "УПРАВЛЕНИЕ КПИ" with table starting at row 6:
        - Column A: Сотрудник (Employee full name)
        - Column B: Оклад (Base salary)
        - Column C: Должность (Position)
        - Column E: Базовая премия (Monthly bonus base)
        - Column F: Вариант премии (Bonus type: Результативный/Фиксированный/Смешанный)
        - Column G: КПИ Общий % (KPI percentage)

    Only ADMIN and MANAGER can import KPI data
    """
    # Only ADMIN and MANAGER can import
    if current_user.role not in [UserRoleEnum.ADMIN, UserRoleEnum.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators and managers can import KPI data"
        )

    # Get user's department
    if not current_user.department_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no assigned department"
        )
    department_id = current_user.department_id

    # Validate file extension
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    try:
        # Read file content
        content = await file.read()

        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 10MB"
            )

        # Parse Excel file - read "УПРАВЛЕНИЕ КПИ" sheet
        try:
            df = pd.read_excel(io.BytesIO(content), sheet_name='УПРАВЛЕНИЕ КПИ', header=None)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid Excel file format or missing 'УПРАВЛЕНИЕ КПИ' sheet: {str(e)}"
            )

        # Check if dataframe is empty
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel file is empty"
            )

        # Find the header row (row 6, index 5)
        # Expected columns at row 6: Сотрудник, Оклад, Должность, ЗП Год, Базовая премия, Вариант премии, КПИ Общий %
        header_row_idx = 5  # Row 6 in Excel = index 5

        if len(df) <= header_row_idx:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Excel file structure is invalid. Expected header at row 6"
            )

        # Parse data starting from row 7 (index 6)
        employees_created = 0
        employees_updated = 0
        kpi_records_created = 0
        kpi_records_updated = 0
        errors = []

        # Mapping of bonus type names to enum
        bonus_type_mapping = {
            'результативный': BonusTypeEnum.PERFORMANCE_BASED,
            'фиксированный': BonusTypeEnum.FIXED,
            'смешанный': BonusTypeEnum.MIXED
        }

        for idx in range(header_row_idx + 1, len(df)):
            row = df.iloc[idx]

            # Column indices (0-based)
            employee_name = row[0]  # Column A
            base_salary = row[1]     # Column B
            position = row[2]        # Column C
            # Skip column D (ЗП Год - formula)
            bonus_base = row[4]      # Column E
            bonus_type_str = row[5]  # Column F
            kpi_percentage = row[6]  # Column G

            # Skip empty rows or totals
            if pd.isna(employee_name) or str(employee_name).strip().upper() in ['', 'ИТОГО:', 'ИТОГО']:
                continue

            try:
                # Validate required fields
                if pd.isna(base_salary) or pd.isna(position):
                    errors.append(f"Строка {idx + 1}: Пропущены обязательные поля (оклад или должность) для {employee_name}")
                    continue

                # Convert and validate numeric fields
                try:
                    base_salary = Decimal(str(base_salary))
                except (ValueError, InvalidOperation):
                    errors.append(f"Строка {idx + 1}: Некорректное значение оклада для {employee_name}")
                    continue

                # Handle optional bonus base
                if pd.isna(bonus_base):
                    bonus_base = Decimal(0)
                else:
                    try:
                        bonus_base = Decimal(str(bonus_base))
                    except (ValueError, InvalidOperation):
                        errors.append(f"Строка {idx + 1}: Некорректное значение базовой премии для {employee_name}")
                        continue

                # Handle optional KPI percentage
                if pd.isna(kpi_percentage):
                    kpi_percentage = None
                else:
                    try:
                        kpi_percentage = Decimal(str(kpi_percentage))
                    except (ValueError, InvalidOperation):
                        errors.append(f"Строка {idx + 1}: Некорректное значение КПИ% для {employee_name}")
                        continue

                # Map bonus type
                bonus_type = BonusTypeEnum.PERFORMANCE_BASED  # Default
                if not pd.isna(bonus_type_str):
                    bonus_type_lower = str(bonus_type_str).strip().lower()
                    bonus_type = bonus_type_mapping.get(bonus_type_lower, BonusTypeEnum.PERFORMANCE_BASED)

                # Find or create employee
                employee = db.query(Employee).filter(
                    and_(
                        Employee.full_name == str(employee_name).strip(),
                        Employee.department_id == department_id
                    )
                ).first()

                if employee:
                    # Update existing employee
                    employee.base_salary = base_salary
                    employee.position = str(position).strip()
                    employee.monthly_bonus_base = bonus_base
                    employee.updated_at = datetime.utcnow()
                    employees_updated += 1
                else:
                    # Create new employee
                    employee = Employee(
                        full_name=str(employee_name).strip(),
                        position=str(position).strip(),
                        base_salary=base_salary,
                        monthly_bonus_base=bonus_base,
                        department_id=department_id,
                        status=EmployeeStatusEnum.ACTIVE
                    )
                    db.add(employee)
                    db.flush()  # Get employee.id
                    employees_created += 1

                # Create or update EmployeeKPI record for the specified period
                employee_kpi = db.query(EmployeeKPI).filter(
                    and_(
                        EmployeeKPI.employee_id == employee.id,
                        EmployeeKPI.year == year,
                        EmployeeKPI.month == month
                    )
                ).first()

                # Calculate bonus based on type and KPI percentage
                monthly_bonus_calculated = None
                if kpi_percentage is not None:
                    monthly_bonus_calculated = calculate_bonus(
                        bonus_base,
                        bonus_type,
                        kpi_percentage
                    )

                if employee_kpi:
                    # Update existing KPI record
                    employee_kpi.kpi_percentage = kpi_percentage
                    employee_kpi.monthly_bonus_type = bonus_type
                    employee_kpi.monthly_bonus_base = bonus_base
                    employee_kpi.monthly_bonus_calculated = monthly_bonus_calculated
                    employee_kpi.updated_at = datetime.utcnow()
                    kpi_records_updated += 1
                else:
                    # Create new KPI record
                    employee_kpi = EmployeeKPI(
                        employee_id=employee.id,
                        year=year,
                        month=month,
                        kpi_percentage=kpi_percentage,
                        monthly_bonus_type=bonus_type,
                        monthly_bonus_base=bonus_base,
                        monthly_bonus_calculated=monthly_bonus_calculated,
                        quarterly_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
                        quarterly_bonus_base=Decimal(0),
                        annual_bonus_type=BonusTypeEnum.PERFORMANCE_BASED,
                        annual_bonus_base=Decimal(0),
                        department_id=department_id
                    )
                    db.add(employee_kpi)
                    kpi_records_created += 1

            except Exception as e:
                errors.append(f"Строка {idx + 1}: Ошибка обработки {employee_name}: {str(e)}")
                continue

        # Commit all changes
        db.commit()

        return {
            "success": True,
            "message": "KPI data imported successfully",
            "statistics": {
                "employees_created": employees_created,
                "employees_updated": employees_updated,
                "kpi_records_created": kpi_records_created,
                "kpi_records_updated": kpi_records_updated,
                "total_processed": employees_created + employees_updated,
                "errors": len(errors)
            },
            "errors": errors if errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import KPI data: {str(e)}"
        )
