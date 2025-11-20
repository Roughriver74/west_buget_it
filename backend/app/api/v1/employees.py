"""
Employee management API endpoints for Payroll (FOT)
Handles CRUD operations for employees
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
import pandas as pd
import io

from app.db.session import get_db
from app.utils.excel_export import encode_filename_header
from app.db.models import (
    Employee, User, UserRoleEnum, Department, SalaryHistory, EmployeeStatusEnum,
    PayrollPlan, PayrollActual, EmployeeKPI, TaxTypeEnum, TaxRate
)
from app.schemas.payroll import (
    EmployeeCreate,
    EmployeeUpdate,
    EmployeeInDB,
    EmployeeWithSalaryHistory,
    SalaryHistoryCreate,
    SalaryHistoryInDB,
)
from app.utils.auth import get_current_active_user
from app.services.tax_rate_utils import merge_tax_rates_with_defaults
from app.services.salary_calculator import SalaryCalculator
from app.utils.ndfl_calculator import calculate_progressive_ndfl, calculate_gross_from_net
from app.db.models import SalaryTypeEnum

router = APIRouter(dependencies=[Depends(get_current_active_user)])


def check_department_access(user: User, department_id: int) -> bool:
    """Check if user has access to the department"""
    if user.role in (
        UserRoleEnum.ADMIN,
        UserRoleEnum.MANAGER,
        UserRoleEnum.ACCOUNTANT,
        UserRoleEnum.FOUNDER,
    ):
        return True
    if user.role == UserRoleEnum.USER:
        return user.department_id == department_id
    if user.role == UserRoleEnum.REQUESTER:
        return user.department_id == department_id
    return False


@router.get("/", response_model=List[EmployeeInDB])
async def list_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    department_id: Optional[int] = None,
    status_filter: Optional[EmployeeStatusEnum] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all employees with filtering options

    - **ADMIN/MANAGER**: Can see all employees from all departments
    - **USER**: Can only see employees from their own department
    """
    query = db.query(Employee)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    # Apply status filter
    if status_filter:
        query = query.filter(Employee.status == status_filter)

    # Apply search filter
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Employee.full_name.ilike(search_pattern),
                Employee.position.ilike(search_pattern),
                Employee.employee_number.ilike(search_pattern)
            )
        )

    employees = query.offset(skip).limit(limit).all()
    return employees


# ==================== Export Endpoints ====================

@router.get("/export")
async def export_employees(
    department_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export employees list to Excel
    """
    query = db.query(Employee).join(Department)

    # Apply department filter based on user role
    if current_user.role == UserRoleEnum.USER:
        if not current_user.department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User has no assigned department"
            )
        query = query.filter(Employee.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(Employee.department_id == department_id)

    # Apply status filter
    if status:
        query = query.filter(Employee.status == status)

    employees = query.all()

    # Define status labels
    status_labels = {
        "ACTIVE": "Активен",
        "ON_VACATION": "В отпуске",
        "ON_LEAVE": "В отпуске/Больничный",
        "FIRED": "Уволен",
    }

    # Convert to DataFrame
    data = []
    for emp in employees:
        data.append({
            "ID": emp.id,
            "ФИО": emp.full_name,
            "Должность": emp.position,
            "Табельный номер": emp.employee_number or "",
            "Оклад": float(emp.base_salary),
            "Отдел": emp.department_rel.name if emp.department_rel else "",
            "Статус": status_labels.get(emp.status, emp.status),
            "Дата приема": emp.hire_date.strftime("%Y-%m-%d") if emp.hire_date else "",
            "Дата увольнения": emp.fire_date.strftime("%Y-%m-%d") if emp.fire_date else "",
            "Email": emp.email or "",
            "Телефон": emp.phone or "",
            "Примечания": emp.notes or "",
            "Дата создания": emp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        })

    df = pd.DataFrame(data)

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Сотрудники')

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=encode_filename_header("employees_export.xlsx")
    )


@router.get("/{employee_id}", response_model=EmployeeWithSalaryHistory)
async def get_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific employee by ID with salary history
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee


@router.post("/", response_model=EmployeeInDB, status_code=status.HTTP_201_CREATED)
async def create_employee(
    employee_data: EmployeeCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new employee

    - **USER**: Can create employees only in their own department (auto-assigned)
    - **MANAGER/ADMIN**: Can specify department_id in request, or uses their own department_id
    """
    # Determine department_id based on user role
    if current_user.role == UserRoleEnum.USER:
        # USER can only create employees in their own department
        department_id = current_user.department_id
        if not department_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your user account has no assigned department. Contact administrator."
            )
    else:
        # ADMIN/MANAGER: use provided department_id or fall back to current_user.department_id
        department_id = employee_data.department_id if employee_data.department_id else current_user.department_id

    # Validate that department_id is set
    if not department_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Department ID must be specified. Either provide department_id in request or ensure your user account has an assigned department."
        )

    # Check if department exists
    department = db.query(Department).filter(
        Department.id == department_id
    ).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {department_id} not found"
        )

    # Check if employee number already exists (if provided)
    if employee_data.employee_number:
        existing = db.query(Employee).filter(
            Employee.employee_number == employee_data.employee_number,
            Employee.department_id == department_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee number already exists in this department"
            )

    # Create new employee with assigned department_id
    employee_dict = employee_data.model_dump(exclude={'department_id'})
    employee_dict['department_id'] = department_id

    # Calculate gross/net salary values (Task 1.4: Брутто ↔ Нетто)
    salary_calc_result = SalaryCalculator.calculate_salaries(
        base_salary=employee_data.base_salary,
        salary_type=employee_data.salary_type,
        ndfl_rate=employee_data.ndfl_rate
    )
    employee_dict['base_salary_gross'] = salary_calc_result['base_salary_gross']
    employee_dict['base_salary_net'] = salary_calc_result['base_salary_net']
    employee_dict['ndfl_amount'] = salary_calc_result['ndfl_amount']

    new_employee = Employee(**employee_dict)
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)

    # Create initial salary history record
    salary_history = SalaryHistory(
        employee_id=new_employee.id,
        old_salary=None,
        new_salary=employee_data.base_salary,
        effective_date=employee_data.hire_date or datetime.now().date(),
        reason="Initial hire",
        notes="Created during employee registration"
    )
    db.add(salary_history)
    db.commit()

    return new_employee


@router.put("/{employee_id}", response_model=EmployeeInDB)
async def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an employee

    - **USER**: Can update employees only in their own department
    - **MANAGER/ADMIN**: Can update employees in any department
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Track salary change
    old_salary = employee.base_salary

    # Update employee fields
    update_data = employee_data.model_dump(exclude_unset=True)

    # If salary-related fields are being updated, recalculate gross/net values (Task 1.4: Брутто ↔ Нетто)
    salary_changed = any(field in update_data for field in ['base_salary', 'salary_type', 'ndfl_rate'])
    if salary_changed:
        # Get current values or use updated ones
        base_salary = update_data.get('base_salary', employee.base_salary)
        salary_type = update_data.get('salary_type', employee.salary_type)
        ndfl_rate = update_data.get('ndfl_rate', employee.ndfl_rate)

        # Skip salary calculation if base_salary is 0 or employee is fired
        # SalaryCalculator requires positive salary values
        is_fired = update_data.get('status') == EmployeeStatusEnum.FIRED or employee.status == EmployeeStatusEnum.FIRED
        if base_salary > 0 and not is_fired:
            # Recalculate
            salary_calc_result = SalaryCalculator.calculate_salaries(
                base_salary=base_salary,
                salary_type=salary_type,
                ndfl_rate=ndfl_rate
            )
            update_data['base_salary_gross'] = salary_calc_result['base_salary_gross']
            update_data['base_salary_net'] = salary_calc_result['base_salary_net']
            update_data['ndfl_amount'] = salary_calc_result['ndfl_amount']
        else:
            # For fired employees or zero salary, set all to zero
            update_data['base_salary_gross'] = 0
            update_data['base_salary_net'] = 0
            update_data['ndfl_amount'] = 0

    for field, value in update_data.items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)

    # If salary changed, create salary history record
    if "base_salary" in update_data and update_data["base_salary"] != old_salary:
        salary_history = SalaryHistory(
            employee_id=employee.id,
            old_salary=old_salary,
            new_salary=update_data["base_salary"],
            effective_date=datetime.now().date(),
            reason="Salary adjustment",
            notes="Updated via employee edit"
        )
        db.add(salary_history)
        db.commit()

    return employee


@router.delete("/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an employee (ADMIN only)

    NOTE: Employees with payroll history, salary history, or KPI records cannot be deleted.
    Instead, change their status to FIRED.
    """
    # Only ADMIN can delete employees
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete employees"
        )

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check for related records
    related_issues = []

    # Check salary history
    salary_history_count = db.query(SalaryHistory).filter(
        SalaryHistory.employee_id == employee_id
    ).count()
    if salary_history_count > 0:
        related_issues.append(f"История изменений зарплаты: {salary_history_count} записей")

    # Check payroll plans
    payroll_plans_count = db.query(PayrollPlan).filter(
        PayrollPlan.employee_id == employee_id
    ).count()
    if payroll_plans_count > 0:
        related_issues.append(f"Плановые начисления: {payroll_plans_count} записей")

    # Check payroll actuals
    payroll_actuals_count = db.query(PayrollActual).filter(
        PayrollActual.employee_id == employee_id
    ).count()
    if payroll_actuals_count > 0:
        related_issues.append(f"Фактические выплаты: {payroll_actuals_count} записей")

    # Check employee KPIs
    employee_kpis_count = db.query(EmployeeKPI).filter(
        EmployeeKPI.employee_id == employee_id
    ).count()
    if employee_kpis_count > 0:
        related_issues.append(f"Записи KPI: {employee_kpis_count} записей")

    # If there are related records, prevent deletion
    if related_issues:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Невозможно удалить сотрудника с историей начислений и выплат",
                "reason": "У сотрудника есть связанные записи",
                "related_records": related_issues,
                "suggestion": f"Вместо удаления измените статус сотрудника на 'Уволен' (FIRED). ФИО: {employee.full_name}"
            }
        )

    # If no related records, safe to delete
    db.delete(employee)
    db.commit()
    return None


@router.get("/{employee_id}/salary-history", response_model=List[SalaryHistoryInDB])
async def get_salary_history(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get salary history for an employee
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    salary_history = db.query(SalaryHistory).filter(
        SalaryHistory.employee_id == employee_id
    ).order_by(SalaryHistory.effective_date.asc()).all()

    return salary_history


@router.post("/{employee_id}/salary-history", response_model=SalaryHistoryInDB, status_code=status.HTTP_201_CREATED)
async def add_salary_history(
    employee_id: int,
    salary_data: SalaryHistoryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a salary history record

    - **USER**: Can add salary history only for employees in their own department
    - **MANAGER/ADMIN**: Can add salary history for any employee
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    # Return 404 instead of 403 to prevent information disclosure
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Create salary history record
    new_history = SalaryHistory(**salary_data.model_dump())
    db.add(new_history)

    # Update employee base salary if this is the most recent change
    if salary_data.effective_date >= datetime.now().date():
        employee.base_salary = salary_data.new_salary

    db.commit()
    db.refresh(new_history)

    return new_history


@router.get("/{employee_id}/tax-calculation")
async def get_employee_tax_calculation(
    employee_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get tax calculation for employee's current salary

    Returns НДФЛ, ПФР, ФОМС, ФСС breakdown based on current tax rates.
    
    НДФЛ рассчитывается от годовой зарплаты по прогрессивной шкале.
    Страховые взносы рассчитываются от месячного оклада (gross) из справочников.
    """
    from sqlalchemy import and_, or_
    from datetime import date
    from decimal import Decimal

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # Check department access
    if not check_department_access(current_user, employee.department_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    today = date.today()
    current_year = today.year
    
    # Определяем месячный оклад в зависимости от salary_type
    base_salary_input = Decimal(str(employee.base_salary))
    monthly_gross_salary = base_salary_input
    
    if employee.salary_type == SalaryTypeEnum.NET:
        # Если оклад введен как NET, пересчитываем в GROSS для месячного оклада
        # Используем простую формулу для месячного оклада
        ndfl_rate = employee.ndfl_rate or Decimal("0.13")
        monthly_gross_salary = base_salary_input / (Decimal("1") - ndfl_rate)
    
    # Рассчитываем годовую зарплату (gross)
    monthly_bonus = Decimal(str(employee.monthly_bonus_base or 0))
    quarterly_bonus = Decimal(str(employee.quarterly_bonus_base or 0))
    annual_bonus = Decimal(str(employee.annual_bonus_base or 0))
    
    # Годовая зарплата = (месячный оклад + месячная премия) * 12 + квартальная премия * 4 + годовая премия
    annual_gross_salary = (monthly_gross_salary + monthly_bonus) * Decimal("12") + quarterly_bonus * Decimal("4") + annual_bonus
    
    # Рассчитываем НДФЛ от годовой зарплаты по прогрессивной шкале
    ndfl_calculation = calculate_progressive_ndfl(annual_gross_salary, current_year)
    annual_ndfl = Decimal(str(ndfl_calculation['total_tax']))
    ndfl_effective_rate = Decimal(str(ndfl_calculation['effective_rate'])) / Decimal("100")  # Конвертируем из процентов
    
    # Месячный НДФЛ (для отображения) = годовой НДФЛ / 12
    monthly_ndfl = annual_ndfl / Decimal("12")
    
    # Для расчета страховых взносов используем месячный gross оклад
    gross_amount = monthly_gross_salary

    # Get active tax rates for current date (department-specific + global)
    tax_rates = db.query(TaxRate).filter(
        TaxRate.is_active == True,
        TaxRate.effective_from <= today,
        or_(
            TaxRate.effective_to.is_(None),
            TaxRate.effective_to >= today
        )
    ).filter(
        or_(
            TaxRate.department_id == employee.department_id,
            TaxRate.department_id.is_(None)
        )
    ).all()

    selected_rates = merge_tax_rates_with_defaults(tax_rates)

    # Initialize result
    income_tax = Decimal(0)
    income_tax_rate = Decimal(0)
    pension_fund = Decimal(0)
    pension_fund_rate = Decimal(0)
    medical_insurance = Decimal(0)
    medical_insurance_rate = Decimal(0)
    social_insurance = Decimal(0)
    social_insurance_rate = Decimal(0)

    breakdown = {}

    # Calculate taxes
    # НДФЛ уже рассчитан от годовой зарплаты, используем его
    income_tax = monthly_ndfl
    income_tax_rate = ndfl_effective_rate
    
    breakdown["income_tax"] = {
        "rate": float(income_tax_rate),
        "rate_percent": float(ndfl_calculation['effective_rate']),
        "amount": float(income_tax),
        "description": f"НДФЛ (прогрессивная шкала, годовой доход: {annual_gross_salary:,.0f} ₽)"
    }
    
    # Calculate other taxes (страховые взносы от месячного оклада)
    for tax_rate in selected_rates.values():
        if tax_rate.tax_type == TaxTypeEnum.INCOME_TAX:
            # НДФЛ уже рассчитан, пропускаем
            continue

        elif tax_rate.tax_type == TaxTypeEnum.PENSION_FUND:
            # ПФР
            if tax_rate.threshold_amount and gross_amount > tax_rate.threshold_amount:
                amount_below = tax_rate.threshold_amount
                amount_above = gross_amount - tax_rate.threshold_amount
                pension_fund = (amount_below * tax_rate.rate) + (amount_above * (tax_rate.rate_above_threshold or Decimal(0)))
                pension_fund_rate = tax_rate.rate
            else:
                pension_fund = gross_amount * tax_rate.rate
                pension_fund_rate = tax_rate.rate

            breakdown["pension_fund"] = {
                "rate": float(pension_fund_rate),
                "rate_percent": float(pension_fund_rate * 100),
                "amount": float(pension_fund),
                "description": tax_rate.name
            }

        elif tax_rate.tax_type == TaxTypeEnum.MEDICAL_INSURANCE:
            # ФОМС
            medical_insurance = gross_amount * tax_rate.rate
            medical_insurance_rate = tax_rate.rate

            breakdown["medical_insurance"] = {
                "rate": float(medical_insurance_rate),
                "rate_percent": float(medical_insurance_rate * 100),
                "amount": float(medical_insurance),
                "description": tax_rate.name
            }

        elif tax_rate.tax_type == TaxTypeEnum.SOCIAL_INSURANCE:
            # ФСС
            social_insurance = gross_amount * tax_rate.rate
            social_insurance_rate = tax_rate.rate

            breakdown["social_insurance"] = {
                "rate": float(social_insurance_rate),
                "rate_percent": float(social_insurance_rate * 100),
                "amount": float(social_insurance),
                "description": tax_rate.name
            }

    # Calculate totals
    total_social_contributions = pension_fund + medical_insurance + social_insurance
    net_amount = gross_amount - income_tax
    employer_cost = gross_amount + total_social_contributions
    
    # Годовая стоимость для компании
    annual_employer_cost = (gross_amount + total_social_contributions) * Decimal("12") + quarterly_bonus * Decimal("4") + annual_bonus

    return {
        "employee_id": employee_id,
        "employee_name": employee.full_name,
        "salary_type": employee.salary_type.value,  # Добавляем тип зарплаты
        "gross_salary": float(gross_amount),  # Месячный gross оклад
        "annual_gross_salary": float(annual_gross_salary),  # Годовая зарплата (gross)
        "income_tax": float(income_tax),  # Месячный НДФЛ
        "annual_income_tax": float(annual_ndfl),  # Годовой НДФЛ
        "income_tax_rate_percent": float(ndfl_calculation['effective_rate']),  # Эффективная ставка НДФЛ
        "social_contributions": {
            "pension_fund": float(pension_fund),
            "pension_fund_rate_percent": float(pension_fund_rate * 100),
            "medical_insurance": float(medical_insurance),
            "medical_insurance_rate_percent": float(medical_insurance_rate * 100),
            "social_insurance": float(social_insurance),
            "social_insurance_rate_percent": float(social_insurance_rate * 100),
            "total": float(total_social_contributions)
        },
        "net_salary": float(net_amount),  # Месячный net оклад
        "employer_total_cost": float(employer_cost),  # Месячная стоимость для компании
        "annual_employer_total_cost": float(annual_employer_cost),  # Годовая стоимость для компании
        "breakdown": breakdown
    }
