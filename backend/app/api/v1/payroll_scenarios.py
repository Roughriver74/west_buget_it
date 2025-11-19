"""
API endpoints for Payroll Scenarios and Insurance Rates

Управление ставками страховых взносов и сценарное планирование ФОТ
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.session import get_db
from app.db.models import (
    InsuranceRate,
    PayrollScenario,
    PayrollScenarioDetail,
    PayrollYearlyComparison,
    User,
    UserRoleEnum,
)
from app.schemas.payroll_scenario import (
    # Insurance Rates
    InsuranceRateCreate,
    InsuranceRateUpdate,
    InsuranceRateInDB,
    # Payroll Scenarios
    PayrollScenarioCreate,
    PayrollScenarioUpdate,
    PayrollScenarioInDB,
    PayrollScenarioWithDetails,
    # Payroll Scenario Details
    PayrollScenarioDetailCreate,
    PayrollScenarioDetailUpdate,
    PayrollScenarioDetailInDB,
    # Comparisons
    PayrollYearlyComparisonInDB,
    YearComparisonRequest,
    ScenarioCalculationRequest,
    ScenarioCalculationResponse,
    InsuranceImpactAnalysis,
)
from app.utils.auth import get_current_active_user
from app.services.payroll_scenario_calculator import (
    PayrollScenarioCalculator,
    InsuranceImpactAnalyzer,
    PayrollComparisonGenerator,
)

router = APIRouter()


# ==================== Insurance Rates Endpoints ====================

@router.get("/insurance-rates", response_model=List[InsuranceRateInDB])
def get_insurance_rates(
    year: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить ставки страховых взносов

    - **year**: фильтр по году (опционально)
    - **department_id**: фильтр по отделу (опционально, только для MANAGER/ADMIN)
    """
    query = db.query(InsuranceRate)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(InsuranceRate.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(InsuranceRate.department_id == department_id)

    # Year filter
    if year:
        query = query.filter(InsuranceRate.year == year)

    # Active only
    query = query.filter(InsuranceRate.is_active == True)

    return query.order_by(InsuranceRate.year, InsuranceRate.rate_type).all()


@router.post("/insurance-rates", response_model=InsuranceRateInDB, status_code=status.HTTP_201_CREATED)
def create_insurance_rate(
    rate: InsuranceRateCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Создать ставку страхового взноса

    Требуется роль: MANAGER, ADMIN
    """
    # Check permissions
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER/ADMIN can create insurance rates"
        )

    # Auto-assign department for USER
    department_id = rate.department_id
    if current_user.role == UserRoleEnum.USER:
        department_id = current_user.department_id
    elif not department_id:
        department_id = current_user.department_id

    # Check for duplicates
    existing = db.query(InsuranceRate).filter(
        and_(
            InsuranceRate.year == rate.year,
            InsuranceRate.rate_type == rate.rate_type,
            InsuranceRate.department_id == department_id,
            InsuranceRate.is_active == True
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Rate for {rate.rate_type} in {rate.year} already exists"
        )

    db_rate = InsuranceRate(
        **rate.model_dump(exclude={'department_id'}),
        department_id=department_id,
        created_by=current_user.id
    )

    db.add(db_rate)
    db.commit()
    db.refresh(db_rate)

    return db_rate


@router.put("/insurance-rates/{rate_id}", response_model=InsuranceRateInDB)
def update_insurance_rate(
    rate_id: int,
    rate_update: InsuranceRateUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновить ставку страхового взноса

    Требуется роль: MANAGER, ADMIN
    """
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER/ADMIN can update insurance rates"
        )

    db_rate = db.query(InsuranceRate).filter(InsuranceRate.id == rate_id).first()

    if not db_rate:
        raise HTTPException(status_code=404, detail="Insurance rate not found")

    # Update fields
    for field, value in rate_update.model_dump(exclude_unset=True).items():
        setattr(db_rate, field, value)

    db.commit()
    db.refresh(db_rate)

    return db_rate


@router.delete("/insurance-rates/{rate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insurance_rate(
    rate_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Удалить (деактивировать) ставку

    Требуется роль: ADMIN
    """
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete insurance rates"
        )

    db_rate = db.query(InsuranceRate).filter(InsuranceRate.id == rate_id).first()

    if not db_rate:
        raise HTTPException(status_code=404, detail="Insurance rate not found")

    db_rate.is_active = False
    db.commit()


# ==================== Payroll Scenarios Endpoints ====================

@router.get("/scenarios", response_model=List[PayrollScenarioInDB])
def get_scenarios(
    target_year: Optional[int] = None,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить список сценариев ФОТ

    - **target_year**: фильтр по целевому году
    - **department_id**: фильтр по отделу
    """
    query = db.query(PayrollScenario)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(PayrollScenario.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(PayrollScenario.department_id == department_id)

    if target_year:
        query = query.filter(PayrollScenario.target_year == target_year)

    query = query.filter(PayrollScenario.is_active == True)

    return query.order_by(PayrollScenario.created_at.desc()).all()


@router.get("/scenarios/{scenario_id}", response_model=PayrollScenarioWithDetails)
def get_scenario_with_details(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить сценарий с детальной разбивкой по сотрудникам
    """
    scenario = db.query(PayrollScenario).filter(
        PayrollScenario.id == scenario_id
    ).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Check access
    if current_user.role == UserRoleEnum.USER:
        if scenario.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    return scenario


@router.post("/scenarios", response_model=PayrollScenarioInDB, status_code=status.HTTP_201_CREATED)
def create_scenario(
    scenario: PayrollScenarioCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Создать сценарий планирования ФОТ

    Требуется роль: MANAGER, ADMIN
    """
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER/ADMIN can create scenarios"
        )

    # Auto-assign department
    department_id = scenario.department_id or current_user.department_id

    db_scenario = PayrollScenario(
        **scenario.model_dump(exclude={'department_id'}),
        department_id=department_id,
        created_by=current_user.id
    )

    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)

    return db_scenario


@router.put("/scenarios/{scenario_id}", response_model=PayrollScenarioInDB)
def update_scenario(
    scenario_id: int,
    scenario_update: PayrollScenarioUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Обновить сценарий

    Требуется роль: MANAGER, ADMIN
    """
    if current_user.role not in [UserRoleEnum.MANAGER, UserRoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only MANAGER/ADMIN can update scenarios"
        )

    db_scenario = db.query(PayrollScenario).filter(
        PayrollScenario.id == scenario_id
    ).first()

    if not db_scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Update fields
    for field, value in scenario_update.model_dump(exclude_unset=True).items():
        setattr(db_scenario, field, value)

    db.commit()
    db.refresh(db_scenario)

    return db_scenario


@router.post("/scenarios/{scenario_id}/calculate", response_model=ScenarioCalculationResponse)
def calculate_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Рассчитать сценарий ФОТ

    Автоматически:
    - Создает детали по сотрудникам (если не существуют)
    - Рассчитывает страховые взносы по новым ставкам
    - Сравнивает с базовым годом
    - Возвращает итоги и разбивку по сотрудникам
    """
    scenario = db.query(PayrollScenario).filter(
        PayrollScenario.id == scenario_id
    ).first()

    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    # Check access
    if current_user.role == UserRoleEnum.USER:
        if scenario.department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    # Calculate
    calculator = PayrollScenarioCalculator(db, scenario.department_id)
    result = calculator.calculate_scenario(scenario_id)

    # Get details
    details = db.query(PayrollScenarioDetail).filter(
        PayrollScenarioDetail.scenario_id == scenario_id
    ).all()

    return ScenarioCalculationResponse(
        scenario_id=scenario_id,
        total_headcount=result['total_headcount'],
        total_base_salary=result['total_base_salary'],
        total_insurance_cost=result['total_insurance_cost'],
        total_payroll_cost=result['total_payroll_cost'],
        cost_difference=result['cost_difference'],
        cost_difference_percent=result['cost_difference_percent'],
        breakdown_by_employee=details
    )


@router.delete("/scenarios/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Удалить (деактивировать) сценарий

    Требуется роль: ADMIN
    """
    if current_user.role != UserRoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only ADMIN can delete scenarios"
        )

    db_scenario = db.query(PayrollScenario).filter(
        PayrollScenario.id == scenario_id
    ).first()

    if not db_scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    db_scenario.is_active = False
    db.commit()


# ==================== Analysis Endpoints ====================

@router.post("/compare-years", response_model=PayrollYearlyComparisonInDB)
def compare_years(
    request: YearComparisonRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Сравнить ФОТ между годами (например, 2025 vs 2026)

    Автоматически рассчитывает:
    - Изменения ставок страховых взносов
    - Влияние на общий ФОТ
    - Рекомендации по оптимизации
    """
    department_id = request.department_id or current_user.department_id

    # Check access
    if current_user.role == UserRoleEnum.USER:
        if department_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    generator = PayrollComparisonGenerator(db, department_id)
    comparison = generator.generate_comparison(
        base_year=request.base_year,
        target_year=request.target_year
    )

    return comparison


@router.get("/impact-analysis", response_model=InsuranceImpactAnalysis)
def get_impact_analysis(
    base_year: int,
    target_year: int,
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Анализ влияния изменений страховых взносов

    Возвращает:
    - Изменения ставок между годами
    - Общее влияние на ФОТ (в рублях и %)
    - Разбивку по типам взносов (ПФР, ФОМС, ФСС)
    - Рекомендации по оптимизации
    """
    dept_id = department_id or current_user.department_id

    # Check access
    if current_user.role == UserRoleEnum.USER:
        if dept_id != current_user.department_id:
            raise HTTPException(status_code=403, detail="Access denied")

    analyzer = InsuranceImpactAnalyzer(db, dept_id)
    analysis = analyzer.analyze_impact(base_year, target_year)

    return InsuranceImpactAnalysis(
        base_year=analysis['base_year'],
        target_year=analysis['target_year'],
        rate_changes=analysis['rate_changes'],
        total_impact=analysis['total_impact'],
        impact_percent=analysis['impact_percent'],
        recommendations=analysis['recommendations']
    )


@router.get("/yearly-comparisons", response_model=List[PayrollYearlyComparisonInDB])
def get_yearly_comparisons(
    department_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Получить все сохраненные сравнения между годами
    """
    query = db.query(PayrollYearlyComparison)

    # Role-based filtering
    if current_user.role == UserRoleEnum.USER:
        query = query.filter(PayrollYearlyComparison.department_id == current_user.department_id)
    elif department_id:
        query = query.filter(PayrollYearlyComparison.department_id == department_id)

    return query.order_by(PayrollYearlyComparison.calculated_at.desc()).all()
