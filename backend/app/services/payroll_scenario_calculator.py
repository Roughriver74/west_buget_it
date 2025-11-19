"""
Payroll Scenario Calculator Service

Сервис для расчета влияния изменений в страховых взносах на ФОТ
и сценарного планирования
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    InsuranceRate,
    PayrollScenario,
    PayrollScenarioDetail,
    PayrollYearlyComparison,
    Employee,
    PayrollActual,
    PayrollPlan,
    TaxTypeEnum,
    PayrollScenarioTypeEnum,
    PayrollDataSourceEnum,
    TaxRate,
)
from app.services.tax_rate_utils import merge_tax_rates_with_defaults

logger = logging.getLogger(__name__)


class PayrollScenarioCalculator:
    """
    Калькулятор сценариев ФОТ с учетом изменений страховых взносов
    """

    def __init__(self, db: Session, department_id: int):
        self.db = db
        self.department_id = department_id

    def calculate_scenario(self, scenario_id: int) -> Dict:
        """
        Рассчитать сценарий ФОТ

        Args:
            scenario_id: ID сценария

        Returns:
            Dict с результатами расчета
        """
        scenario = self.db.query(PayrollScenario).filter(
            PayrollScenario.id == scenario_id,
            PayrollScenario.department_id == self.department_id
        ).first()

        if not scenario:
            raise ValueError(f"Scenario {scenario_id} not found")

        # Получить ставки страховых взносов для целевого года
        insurance_rates = self._get_insurance_rates(scenario.target_year)

        # Получить детали сценария
        scenario_details = self.db.query(PayrollScenarioDetail).filter(
            PayrollScenarioDetail.scenario_id == scenario_id
        ).all()

        # ВСЕГДА пересоздаем детали при расчете от БАЗОВОГО ГОДА,
        # чтобы правильно применить новые проценты изменения
        # Удаляем старые детали
        logger.info(f"Recreating scenario details from BASE YEAR for scenario {scenario_id}")
        self.db.query(PayrollScenarioDetail).filter(
            PayrollScenarioDetail.scenario_id == scenario_id
        ).delete()
        self.db.commit()

        # Создаем новые детали в зависимости от источника данных
        if scenario.data_source == PayrollDataSourceEnum.PLAN:
            # Если источник данных - план, используем данные из PayrollPlan
            scenario_details = self._create_scenario_details_from_plan(
                scenario, insurance_rates
            )
        else:
            # Для EMPLOYEES и ACTUAL используем данные из PayrollActual
            scenario_details = self._create_scenario_details_from_base_year(
                scenario, insurance_rates
            )

        # Рассчитать каждого сотрудника
        total_headcount = 0
        total_base_salary = Decimal('0.00')
        total_insurance = Decimal('0.00')
        total_income_tax = Decimal('0.00')
        total_payroll_cost = Decimal('0.00')

        for detail in scenario_details:
            # Если источник данных - план, детали уже рассчитаны с суммами из плана
            # Просто суммируем уже рассчитанные значения
            if scenario.data_source == PayrollDataSourceEnum.PLAN:
                # Для планов все уже рассчитано в _create_scenario_details_from_plan
                if not detail.is_terminated:
                    total_headcount += 1
                
                # Аккумулировать итоги из уже рассчитанных значений
                # Для планов годовая зарплата = total_employee_cost - total_insurance
                # (это уже рассчитано в _create_scenario_details_from_plan)
                if detail.total_employee_cost and detail.total_insurance:
                    # Годовая зарплата из плана с учетом процента изменения
                    annual_salary = detail.total_employee_cost - detail.total_insurance
                else:
                    # Fallback: используем месячный оклад * 12
                    annual_salary = detail.base_salary * 12
                
                total_base_salary += annual_salary
                total_insurance += detail.total_insurance or Decimal('0.00')
                total_income_tax += detail.income_tax or Decimal('0.00')
                total_payroll_cost += detail.total_employee_cost or Decimal('0.00')
            else:
                # Для EMPLOYEES и ACTUAL пересчитываем как раньше
                # Учитываем уволенных сотрудников - они не считаются в численности
                # но их зарплата может считаться частично (если указан termination_month)
                if detail.is_terminated:
                    # Если указан месяц увольнения, считаем зарплату только до этого месяца
                    if detail.termination_month:
                        months_worked = detail.termination_month
                    else:
                        months_worked = 0  # Уволен сразу, не считаем
                else:
                    total_headcount += 1
                    months_worked = 12

                # ВАЖНО: detail.base_salary хранит МЕСЯЧНЫЙ оклад
                # Для годового расчета умножаем на количество отработанных месяцев
                annual_salary = (detail.base_salary + detail.monthly_bonus) * months_worked

                # Рассчитать страховые взносы на ГОДОВУЮ зарплату (пропорционально месяцам)
                insurance_calc = self._calculate_insurance_for_employee(
                    annual_salary,
                    insurance_rates
                )

                # Рассчитать НДФЛ на ГОДОВУЮ зарплату (13% дефолт или ставка из справочника)
                income_tax_rate = insurance_rates.get('INCOME_TAX', Decimal('0.13'))
                income_tax = annual_salary * income_tax_rate

                # Обновить детали (сохраняем годовые значения)
                detail.pension_contribution = insurance_calc['pension']
                detail.medical_contribution = insurance_calc['medical']
                detail.social_contribution = insurance_calc['social']
                detail.injury_contribution = insurance_calc['injury']
                detail.total_insurance = insurance_calc['total']
                detail.income_tax = income_tax
                detail.total_employee_cost = (
                    annual_salary +
                    insurance_calc['total']
                )

                # Аккумулировать итоги (годовые суммы)
                total_base_salary += annual_salary
                total_insurance += insurance_calc['total']
                total_income_tax += income_tax
                total_payroll_cost += detail.total_employee_cost

        # Обновить сценарий
        scenario.total_headcount = total_headcount
        scenario.total_base_salary = total_base_salary
        scenario.total_insurance_cost = total_insurance
        scenario.total_payroll_cost = total_payroll_cost

        # Рассчитать сравнение с базовым годом (используем тех же сотрудников)
        # Если источник данных - план, используем планы для базового года
        base_year_cost = self._get_base_year_cost_for_employees(
            scenario.base_year, 
            scenario_details,
            data_source=scenario.data_source
        )
        scenario.base_year_total_cost = base_year_cost
        scenario.cost_difference = total_payroll_cost - base_year_cost
        scenario.cost_difference_percent = (
            (scenario.cost_difference / base_year_cost * 100)
            if base_year_cost > 0 else Decimal('0.00')
        )

        self.db.commit()
        self.db.refresh(scenario)

        return {
            'scenario_id': scenario.id,
            'total_headcount': scenario.total_headcount,
            'total_base_salary': float(scenario.total_base_salary),
            'total_insurance_cost': float(scenario.total_insurance_cost),
            'total_payroll_cost': float(scenario.total_payroll_cost),
            'cost_difference': float(scenario.cost_difference),
            'cost_difference_percent': float(scenario.cost_difference_percent),
        }

    def _get_insurance_rates(self, year: int) -> Dict[str, Decimal]:
        """Получить ставки страховых взносов/НДФЛ для года из справочника TaxRate

        Использует TaxRate (справочник налоговых ставок) вместо InsuranceRate.
        Логика поиска:
        1. Конвертируем год в дату (1 января указанного года)
        2. Ищем активные ставки для этой даты (effective_from <= calc_date и effective_to >= calc_date или NULL)
        3. Если есть ставки с effective_from в будущем (но <= конца года), учитываем их как будущие изменения
        4. Сначала ищем ставки для конкретного отдела, затем глобальные
        5. Если не найдены, используем дефолтные значения
        """
        from datetime import date
        from sqlalchemy import or_, and_
        
        # Конвертируем год в дату (1 января указанного года и 31 декабря для поиска будущих ставок)
        calc_date = date(year, 1, 1)
        year_end_date = date(year, 12, 31)
        
        rates = {}
        
        # Получаем ставки для указанной даты
        # Сначала ищем для конкретного департамента
        tax_rates_query_dept = self.db.query(TaxRate).filter(
            TaxRate.is_active == True,
            TaxRate.department_id == self.department_id,
            # Ставка должна быть актуальна на calc_date или начаться в течение года
            or_(
                # Актуальная ставка на calc_date
                and_(
                    TaxRate.effective_from <= calc_date,
                    or_(
                        TaxRate.effective_to.is_(None),
                        TaxRate.effective_to >= calc_date
                    )
                ),
                # Будущая ставка, которая начнет действовать в этом году
                and_(
                    TaxRate.effective_from > calc_date,
                    TaxRate.effective_from <= year_end_date
                )
            )
        ).order_by(TaxRate.effective_from.desc())
        
        tax_rates = tax_rates_query_dept.all()
        
        # Если не найдены ставки для департамента, ищем глобальные ставки (department_id IS NULL)
        if not tax_rates:
            tax_rates_query_global = self.db.query(TaxRate).filter(
                TaxRate.is_active == True,
                TaxRate.department_id.is_(None),  # Только глобальные ставки
                # Ставка должна быть актуальна на calc_date или начаться в течение года
                or_(
                    # Актуальная ставка на calc_date
                    and_(
                        TaxRate.effective_from <= calc_date,
                        or_(
                            TaxRate.effective_to.is_(None),
                            TaxRate.effective_to >= calc_date
                        )
                    ),
                    # Будущая ставка, которая начнет действовать в этом году
                    and_(
                        TaxRate.effective_from > calc_date,
                        TaxRate.effective_from <= year_end_date
                    )
                )
            ).order_by(TaxRate.effective_from.desc())
            tax_rates = tax_rates_query_global.all()
            logger.info(f"Found {len(tax_rates)} global tax rates for year {year}")
        
        # Объединяем с дефолтами
        selected_rates = merge_tax_rates_with_defaults(tax_rates)
        
        # Извлекаем нужные ставки страховых взносов + НДФЛ (если есть)
        # Приоритет: ставка актуальная на calc_date, если есть будущая - берем её
        for rate_type in [
            TaxTypeEnum.PENSION_FUND,
            TaxTypeEnum.MEDICAL_INSURANCE,
            TaxTypeEnum.SOCIAL_INSURANCE,
            TaxTypeEnum.INJURY_INSURANCE,
            TaxTypeEnum.INCOME_TAX,
        ]:
            # Ищем ставку для этого типа
            rate_obj = selected_rates.get(rate_type)
            
            # Если есть несколько ставок, ПРИОРИТЕТ будущим ставкам, которые начнут действовать в целевом году
            matching_rates = [r for r in tax_rates if r.tax_type == rate_type]
            if matching_rates:
                # Разделяем на актуальные и будущие
                current_rates = [r for r in matching_rates if r.effective_from <= calc_date]
                future_rates = [r for r in matching_rates if r.effective_from > calc_date and r.effective_from <= year_end_date]
                
                # ВАЖНО: Будущие ставки имеют приоритет над текущими
                # Если есть ставка, которая начнет действовать в целевом году, используем её
                if future_rates:
                    # Берем самую раннюю будущую ставку (которая начнет действовать первой в целевом году)
                    rate_obj = min(future_rates, key=lambda r: r.effective_from)
                    logger.info(f"Using future rate for {rate_type.value} in {year}: {rate_obj.rate * 100}% (effective_from: {rate_obj.effective_from})")
                elif current_rates:
                    # Если нет будущих, берем самую позднюю актуальную ставку
                    rate_obj = max(current_rates, key=lambda r: r.effective_from)
                else:
                    rate_obj = None
            
            if rate_obj and hasattr(rate_obj, 'rate'):
                rates[rate_type.value] = Decimal(str(rate_obj.rate))
                # Check if rate_obj has effective_from (TaxRate) or not (TaxRateDefault)
                if hasattr(rate_obj, 'effective_from'):
                    logger.info(f"Found tax rate for {rate_type.value} in {year}: {rates[rate_type.value] * 100}% (effective_from: {rate_obj.effective_from})")
                else:
                    logger.info(f"Using default tax rate for {rate_type.value} in {year}: {rates[rate_type.value] * 100}%")
            else:
                # Дефолтные ставки на случай отсутствия данных
                defaults = {
                    TaxTypeEnum.PENSION_FUND.value: Decimal('0.22'),
                    TaxTypeEnum.MEDICAL_INSURANCE.value: Decimal('0.051'),
                    TaxTypeEnum.SOCIAL_INSURANCE.value: Decimal('0.029'),
                    TaxTypeEnum.INJURY_INSURANCE.value: Decimal('0.002'),
                    TaxTypeEnum.INCOME_TAX.value: Decimal('0.13'),
                }
                rates[rate_type.value] = defaults.get(rate_type.value, Decimal('0.00'))
                logger.warning(f"No tax rate found for {rate_type.value} in {year}, using default: {rates[rate_type.value]}")

        return rates

    def _calculate_insurance_for_employee(
        self, gross_salary: Decimal, insurance_rates: Dict[str, Decimal]
    ) -> Dict[str, Decimal]:
        """Рассчитать страховые взносы для сотрудника"""
        return {
            'pension': gross_salary * insurance_rates.get('PENSION_FUND', Decimal('0.22')),
            'medical': gross_salary * insurance_rates.get('MEDICAL_INSURANCE', Decimal('0.051')),
            'social': gross_salary * insurance_rates.get('SOCIAL_INSURANCE', Decimal('0.029')),
            'injury': gross_salary * insurance_rates.get('INJURY_INSURANCE', Decimal('0.002')),
            'total': gross_salary * (
                insurance_rates.get('PENSION_FUND', Decimal('0.22')) +
                insurance_rates.get('MEDICAL_INSURANCE', Decimal('0.051')) +
                insurance_rates.get('SOCIAL_INSURANCE', Decimal('0.029')) +
                insurance_rates.get('INJURY_INSURANCE', Decimal('0.002'))
            )
        }

    def _create_scenario_details_from_employees(
        self, scenario: PayrollScenario, insurance_rates: Dict[str, Decimal]
    ) -> List[PayrollScenarioDetail]:
        """Создать детали сценария из текущих сотрудников"""
        employees = self.db.query(Employee).filter(
            Employee.department_id == self.department_id,
            Employee.status == 'ACTIVE'
        ).all()

        details = []
        for emp in employees:
            # Применить изменения зарплаты по сценарию
            salary_multiplier = Decimal('1.00') + (scenario.salary_change_percent / 100)
            adjusted_salary = emp.base_salary * salary_multiplier

            # Получить базовый год для сравнения
            base_year_salary, base_year_insurance = self._get_employee_base_year_data(
                emp.id, scenario.base_year
            )

            detail = PayrollScenarioDetail(
                scenario_id=scenario.id,
                employee_id=emp.id,
                employee_name=emp.full_name,
                position=emp.position,
                base_salary=adjusted_salary,
                monthly_bonus=emp.monthly_bonus_base * salary_multiplier,
                base_year_salary=base_year_salary,
                base_year_insurance=base_year_insurance,
                department_id=self.department_id,
            )

            self.db.add(detail)
            details.append(detail)

        # Если есть изменение headcount, добавить/удалить сотрудников
        if scenario.headcount_change_percent != 0:
            headcount_change = int(len(employees) * scenario.headcount_change_percent / 100)

            if headcount_change > 0:
                # Добавить новых сотрудников (средняя зарплата)
                avg_salary = sum(e.base_salary for e in employees) / len(employees) if employees else Decimal('50000')

                for i in range(headcount_change):
                    detail = PayrollScenarioDetail(
                        scenario_id=scenario.id,
                        employee_id=None,
                        employee_name=f"Новый сотрудник {i+1}",
                        position="Планируемая позиция",
                        base_salary=avg_salary,
                        monthly_bonus=Decimal('0.00'),
                        is_new_hire=True,
                        department_id=self.department_id,
                    )
                    self.db.add(detail)
                    details.append(detail)

            elif headcount_change < 0:
                # Отметить сотрудников на увольнение
                for i in range(abs(headcount_change)):
                    if i < len(details):
                        details[i].is_terminated = True

        self.db.commit()
        return details

    def _create_scenario_details_from_base_year(
        self, scenario: PayrollScenario, insurance_rates: Dict[str, Decimal]
    ) -> List[PayrollScenarioDetail]:
        """
        Создать детали сценария от БАЗОВОГО ГОДА с применением процентов изменения

        ВАЖНО: Этот метод создает scenario_details от базового года (PayrollActual),
        а не от текущего Employee table. Это гарантирует правильное применение
        процентов изменения относительно базового года.

        Args:
            scenario: Сценарий с параметрами (headcount_change_percent, salary_change_percent)
            insurance_rates: Ставки страховых взносов для целевого года

        Returns:
            List[PayrollScenarioDetail]: Детали сценария
        """
        logger.info(f"Creating scenario details from BASE YEAR {scenario.base_year}")

        # 1. Получить уникальных сотрудников из базового года (JOIN с Employee для имени/должности)
        base_year_employees = self.db.query(
            PayrollActual.employee_id,
            Employee.full_name.label('employee_name'),
            Employee.position.label('position'),
            func.sum(PayrollActual.total_paid).label('annual_salary'),
            func.sum(PayrollActual.social_tax_amount).label('annual_insurance')
        ).join(
            Employee, PayrollActual.employee_id == Employee.id
        ).filter(
            PayrollActual.department_id == self.department_id,
            PayrollActual.year == scenario.base_year
        ).group_by(
            PayrollActual.employee_id,
            Employee.full_name,
            Employee.position
        ).all()

        base_year_count = len(base_year_employees)
        logger.info(f"Found {base_year_count} employees in base year {scenario.base_year}")

        if base_year_count == 0:
            logger.warning(f"No employees found in base year {scenario.base_year}, cannot create scenario")
            return []

        # 2. Применить изменения зарплаты
        salary_multiplier = Decimal('1.00') + (scenario.salary_change_percent / 100)
        logger.info(f"Salary multiplier: {salary_multiplier} ({scenario.salary_change_percent}%)")

        # 3. Создать детали для существующих сотрудников базового года
        details = []
        total_base_year_salary = Decimal('0.00')

        for emp in base_year_employees:
            # Годовая зарплата из базового года
            annual_base_salary = emp.annual_salary or Decimal('0.00')
            total_base_year_salary += annual_base_salary

            # Применить процент изменения зарплаты
            # ВАЖНО: annual_salary уже годовая, нужно получить месячную для base_salary
            monthly_base_salary = (annual_base_salary / 12) * salary_multiplier

            detail = PayrollScenarioDetail(
                scenario_id=scenario.id,
                employee_id=emp.employee_id,
                employee_name=emp.employee_name,
                position=emp.position,
                base_salary=monthly_base_salary,  # Месячный оклад
                monthly_bonus=Decimal('0.00'),  # Бонусы пока не учитываем
                base_year_salary=annual_base_salary,  # Годовая зарплата базового года
                base_year_insurance=emp.annual_insurance or Decimal('0.00'),
                department_id=self.department_id,
                is_new_hire=False,
                is_terminated=False,
            )

            self.db.add(detail)
            details.append(detail)

        # 4. Применить изменение headcount
        if scenario.headcount_change_percent != 0:
            headcount_change = int(base_year_count * scenario.headcount_change_percent / 100)
            logger.info(f"Headcount change: {headcount_change} people ({scenario.headcount_change_percent}%)")

            if headcount_change > 0:
                # Добавить новых сотрудников
                # Средняя месячная зарплата = (total_base_year_salary / base_year_count / 12) * salary_multiplier
                avg_monthly_salary = (total_base_year_salary / base_year_count / 12) * salary_multiplier
                logger.info(f"Adding {headcount_change} new employees with avg monthly salary {avg_monthly_salary}")

                for i in range(headcount_change):
                    detail = PayrollScenarioDetail(
                        scenario_id=scenario.id,
                        employee_id=None,
                        employee_name=f"Новый сотрудник {i+1}",
                        position="Планируемая позиция",
                        base_salary=avg_monthly_salary,
                        monthly_bonus=Decimal('0.00'),
                        base_year_salary=Decimal('0.00'),  # Не было в базовом году
                        base_year_insurance=Decimal('0.00'),
                        department_id=self.department_id,
                        is_new_hire=True,
                        is_terminated=False,
                    )
                    self.db.add(detail)
                    details.append(detail)

            elif headcount_change < 0:
                # Отметить сотрудников на увольнение (первые по списку)
                terminate_count = min(abs(headcount_change), len(details))
                logger.info(f"Marking {terminate_count} employees as terminated")

                for i in range(terminate_count):
                    details[i].is_terminated = True
                    # Устанавливаем месяц увольнения (например, середина года)
                    details[i].termination_month = 6

        self.db.commit()
        logger.info(f"Created {len(details)} scenario details from base year")

        return details

    def _get_employee_base_year_data(
        self, employee_id: int, base_year: int
    ) -> Tuple[Decimal, Decimal]:
        """
        Получить данные сотрудника за базовый год

        Returns:
            Tuple[Decimal, Decimal]: (годовая зарплата, годовые страховые взносы)
        """
        # Получить ВСЕ записи за год (12 месяцев)
        payroll_records = self.db.query(PayrollActual).filter(
            PayrollActual.employee_id == employee_id,
            PayrollActual.year == base_year
        ).all()

        if payroll_records:
            # Суммировать ВСЕ месяцы за год
            total_salary = sum(p.total_paid for p in payroll_records)
            total_insurance = sum(p.social_tax_amount for p in payroll_records)
            return total_salary, total_insurance
        else:
            # Если нет данных за базовый год, использовать текущий оклад * 12 месяцев
            employee = self.db.query(Employee).get(employee_id)
            if employee:
                annual_salary = employee.base_salary * 12
                # Рассчитать страховые взносы за год
                base_insurance_rates = self._get_insurance_rates(base_year)
                insurance_calc = self._calculate_insurance_for_employee(
                    annual_salary, base_insurance_rates
                )
                return annual_salary, insurance_calc['total']

        return Decimal('0.00'), Decimal('0.00')

    def _get_base_year_cost(self, base_year: int) -> Decimal:
        """
        Получить общий ФОТ за базовый год (ВСЕ сотрудники)

        ВНИМАНИЕ: Этот метод не используется для сравнения в сценариях!
        Используйте _get_base_year_cost_for_employees() для корректного сравнения.
        """
        result = self.db.query(
            func.sum(PayrollActual.total_paid + PayrollActual.social_tax_amount)
        ).filter(
            PayrollActual.department_id == self.department_id,
            PayrollActual.year == base_year
        ).scalar()

        return result or Decimal('0.00')

    def _get_base_year_cost_for_employees(
        self, base_year: int, scenario_details: List[PayrollScenarioDetail],
        data_source: PayrollDataSourceEnum = PayrollDataSourceEnum.ACTUAL
    ) -> Decimal:
        """
        Получить общий ФОТ за базовый год для тех же сотрудников, что в сценарии

        Это обеспечивает корректное сравнение "яблоки с яблоками":
        - Базовый год: те же сотрудники, что в целевом году
        - Целевой год: сотрудники из scenario_details

        Args:
            base_year: Базовый год
            scenario_details: Детали сценария с сотрудниками

        Returns:
            Decimal: Общий ФОТ за базовый год для указанных сотрудников
        """
        total_base_year_cost = Decimal('0.00')
        base_insurance_rates = self._get_insurance_rates(base_year)

        for detail in scenario_details:
            # Пропускаем новых сотрудников (их не было в базовом году)
            if detail.is_new_hire or not detail.employee_id:
                continue

            # Пропускаем уволенных (не учитываем их в базовом году для сравнения)
            if detail.is_terminated:
                continue

            # Получить данные сотрудника за базовый год
            if data_source == PayrollDataSourceEnum.PLAN:
                # Если источник данных - план, используем планы
                payroll_plans = self.db.query(PayrollPlan).filter(
                    PayrollPlan.employee_id == detail.employee_id,
                    PayrollPlan.year == base_year,
                    PayrollPlan.department_id == self.department_id
                ).all()
                
                if payroll_plans:
                    # Суммируем все плановые суммы за год (total_planned)
                    year_salary = sum(p.total_planned for p in payroll_plans)
                    # Рассчитать страховые взносы от годовой суммы из плана
                    insurance_calc = self._calculate_insurance_for_employee(
                        year_salary, base_insurance_rates
                    )
                    year_insurance = insurance_calc['total']
                    employee_total_cost = year_salary + year_insurance
                else:
                    employee_total_cost = Decimal('0.00')
            else:
                # Для ACTUAL и EMPLOYEES используем фактические выплаты
                payroll_actuals = self.db.query(PayrollActual).filter(
                    PayrollActual.employee_id == detail.employee_id,
                    PayrollActual.year == base_year,
                    PayrollActual.department_id == self.department_id
                ).all()

                if payroll_actuals:
                    # Суммируем все выплаты за год (12 месяцев)
                    year_salary = sum(p.total_paid for p in payroll_actuals)
                    year_insurance = sum(p.social_tax_amount for p in payroll_actuals)
                    employee_total_cost = year_salary + year_insurance
                else:
                    employee_total_cost = Decimal('0.00')
            
            if employee_total_cost == 0:
            else:
                # Если нет данных за базовый год, используем current employee base_salary * 12
                employee = self.db.query(Employee).get(detail.employee_id)
                if employee:
                    annual_salary = employee.base_salary * 12
                    # Рассчитываем страховые взносы по ставкам базового года
                    insurance_calc = self._calculate_insurance_for_employee(
                        annual_salary, base_insurance_rates
                    )
                    employee_total_cost = annual_salary + insurance_calc['total']
                else:
                    # Последний fallback - используем плановый оклад из сценария
                    annual_salary = detail.base_salary * 12
                    insurance_calc = self._calculate_insurance_for_employee(
                        annual_salary, base_insurance_rates
                    )
                    employee_total_cost = annual_salary + insurance_calc['total']

            total_base_year_cost += employee_total_cost

        return total_base_year_cost

    def _create_scenario_details_from_plan(
        self, scenario: PayrollScenario, insurance_rates: Dict[str, Decimal]
    ) -> List[PayrollScenarioDetail]:
        """
        Создать детали сценария из ПЛАНА (PayrollPlan) для базового года
        
        Когда источник данных - план, используем суммы из PayrollPlan.total_planned
        вместо пересчета по сотрудникам.
        
        Args:
            scenario: Сценарий с параметрами
            insurance_rates: Ставки страховых взносов для целевого года
            
        Returns:
            List[PayrollScenarioDetail]: Детали сценария из планов
        """
        logger.info(f"Creating scenario details from PLAN for base year {scenario.base_year}")
        
        # Получить уникальных сотрудников из планов базового года
        # Группируем по сотрудникам и суммируем total_planned за весь год
        plan_data = self.db.query(
            PayrollPlan.employee_id,
            Employee.full_name.label('employee_name'),
            Employee.position.label('position'),
            func.sum(PayrollPlan.total_planned).label('annual_planned'),  # Годовая сумма из плана
            func.sum(PayrollPlan.base_salary).label('total_base_salary'),  # Для расчета среднего оклада
        ).join(
            Employee, PayrollPlan.employee_id == Employee.id
        ).filter(
            PayrollPlan.department_id == self.department_id,
            PayrollPlan.year == scenario.base_year
        ).group_by(
            PayrollPlan.employee_id,
            Employee.full_name,
            Employee.position
        ).all()
        
        plan_count = len(plan_data)
        logger.info(f"Found {plan_count} employees with plans in base year {scenario.base_year}")
        
        if plan_count == 0:
            logger.warning(f"No plans found in base year {scenario.base_year}, cannot create scenario")
            return []
        
        # Применить изменения зарплаты
        salary_multiplier = Decimal('1.00') + (scenario.salary_change_percent / 100)
        logger.info(f"Salary multiplier: {salary_multiplier} ({scenario.salary_change_percent}%)")
        
        # Создать детали для сотрудников из плана
        details = []
        
        for plan in plan_data:
            # Годовая сумма из плана (total_planned за весь год)
            annual_planned = plan.annual_planned or Decimal('0.00')
            
            # Применить процент изменения к общей сумме из плана
            adjusted_annual = annual_planned * salary_multiplier
            
            # Получить средний месячный оклад для расчета (используем для расчета страховых взносов)
            # Средний месячный оклад = total_base_salary / 12
            avg_monthly_base = (plan.total_base_salary / 12) if plan.total_base_salary else Decimal('0.00')
            adjusted_monthly_base = avg_monthly_base * salary_multiplier
            
            # Рассчитать страховые взносы от скорректированной годовой суммы
            insurance_calc = self._calculate_insurance_for_employee(
                adjusted_annual,
                insurance_rates
            )
            
            # Рассчитать НДФЛ от годовой суммы из плана
            income_tax_rate = insurance_rates.get('INCOME_TAX', Decimal('0.13'))
            income_tax = adjusted_annual * income_tax_rate
            
            # Получить базовый год для сравнения (используем те же планы)
            base_year_salary = annual_planned
            # Рассчитать страховые взносы базового года (для сравнения)
            base_insurance_rates = self._get_insurance_rates(scenario.base_year)
            base_insurance_calc = self._calculate_insurance_for_employee(
                annual_planned,
                base_insurance_rates
            )
            base_year_insurance = base_insurance_calc['total']
            
            detail = PayrollScenarioDetail(
                scenario_id=scenario.id,
                employee_id=plan.employee_id,
                employee_name=plan.employee_name,
                position=plan.position,
                base_salary=adjusted_monthly_base,  # Месячный оклад (для отображения)
                monthly_bonus=Decimal('0.00'),  # Премии уже включены в total_planned
                # Сохраняем годовые суммы для расчета
                pension_contribution=insurance_calc['pension'],
                medical_contribution=insurance_calc['medical'],
                social_contribution=insurance_calc['social'],
                injury_contribution=insurance_calc['injury'],
                total_insurance=insurance_calc['total'],
                income_tax=income_tax,
                total_employee_cost=adjusted_annual + insurance_calc['total'],
                base_year_salary=base_year_salary,
                base_year_insurance=base_year_insurance,
                department_id=self.department_id,
                is_new_hire=False,
                is_terminated=False,
            )
            
            self.db.add(detail)
            details.append(detail)
        
        # Применить изменение headcount
        if scenario.headcount_change_percent != 0:
            headcount_change = int(plan_count * scenario.headcount_change_percent / 100)
            logger.info(f"Headcount change: {headcount_change} people ({scenario.headcount_change_percent}%)")
            
            if headcount_change > 0:
                # Добавить новых сотрудников (средняя зарплата из планов)
                avg_annual = sum(p.annual_planned for p in plan_data) / plan_count if plan_data else Decimal('50000') * 12
                avg_monthly = avg_annual / 12
                
                for i in range(headcount_change):
                    adjusted_avg = avg_monthly * salary_multiplier
                    adjusted_annual = avg_annual * salary_multiplier
                    
                    insurance_calc = self._calculate_insurance_for_employee(
                        adjusted_annual,
                        insurance_rates
                    )
                    
                    detail = PayrollScenarioDetail(
                        scenario_id=scenario.id,
                        employee_id=None,
                        employee_name=f"Новый сотрудник {i+1}",
                        position="Планируемая позиция",
                        base_salary=adjusted_avg,
                        monthly_bonus=Decimal('0.00'),
                        pension_contribution=insurance_calc['pension'],
                        medical_contribution=insurance_calc['medical'],
                        social_contribution=insurance_calc['social'],
                        injury_contribution=insurance_calc['injury'],
                        total_insurance=insurance_calc['total'],
                        income_tax=adjusted_annual * insurance_rates.get('INCOME_TAX', Decimal('0.13')),
                        total_employee_cost=adjusted_annual + insurance_calc['total'],
                        is_new_hire=True,
                        department_id=self.department_id,
                    )
                    self.db.add(detail)
                    details.append(detail)
            
            elif headcount_change < 0:
                # Отметить сотрудников на увольнение
                for i in range(abs(headcount_change)):
                    if i < len(details):
                        details[i].is_terminated = True
        
        self.db.commit()
        logger.info(f"Created {len(details)} scenario details from PLAN")
        
        return details


class InsuranceImpactAnalyzer:
    """
    Анализатор влияния изменений страховых взносов на ФОТ
    """

    def __init__(self, db: Session, department_id: int):
        self.db = db
        self.department_id = department_id

    def analyze_impact(self, base_year: int, target_year: int) -> Dict:
        """
        Проанализировать влияние изменений ставок между годами

        Args:
            base_year: Базовый год
            target_year: Целевой год

        Returns:
            Dict с анализом
        """
        # Получить ставки для обоих годов
        base_rates = self._get_all_rates(base_year)
        target_rates = self._get_all_rates(target_year)
        
        logger.info(f"Base year {base_year} rates: {base_rates}")
        logger.info(f"Target year {target_year} rates: {target_rates}")

        # Маппинг английских названий на русские
        rate_type_labels = {
            'PENSION_FUND': 'ПФР',
            'MEDICAL_INSURANCE': 'ФОМС',
            'SOCIAL_INSURANCE': 'ФСС',
            'INJURY_INSURANCE': 'Травматизм',
        }
        
        # Рассчитать изменения
        rate_changes = {}
        for rate_type in base_rates:
            base_rate = base_rates[rate_type]
            target_rate = target_rates.get(rate_type, base_rate)
            
            # Используем русское название как ключ
            russian_name = rate_type_labels.get(rate_type, rate_type)

            rate_changes[russian_name] = {
                'from': float(base_rate * 100),
                'to': float(target_rate * 100),
                'change': float((target_rate - base_rate) * 100),
            }
            logger.info(f"Rate change for {russian_name} ({rate_type}): {base_rate * 100}% -> {target_rate * 100}% (change: {(target_rate - base_rate) * 100}%)")

        # Получить данные ФОТ за базовый год
        base_year_payroll = self._get_year_payroll_data(base_year)

        # Рассчитать влияние на каждый тип взносов
        total_impact = Decimal('0.00')
        pension_impact = Decimal('0.00')
        medical_impact = Decimal('0.00')
        social_impact = Decimal('0.00')

        if base_year_payroll['total_salary'] > 0:
            pension_change = (
                target_rates.get('PENSION_FUND', Decimal('0.22')) -
                base_rates.get('PENSION_FUND', Decimal('0.22'))
            )
            pension_impact = base_year_payroll['total_salary'] * pension_change * 12

            medical_change = (
                target_rates.get('MEDICAL_INSURANCE', Decimal('0.051')) -
                base_rates.get('MEDICAL_INSURANCE', Decimal('0.051'))
            )
            medical_impact = base_year_payroll['total_salary'] * medical_change * 12

            social_change = (
                target_rates.get('SOCIAL_INSURANCE', Decimal('0.029')) -
                base_rates.get('SOCIAL_INSURANCE', Decimal('0.029'))
            )
            social_impact = base_year_payroll['total_salary'] * social_change * 12

            total_impact = pension_impact + medical_impact + social_impact

        # Генерировать рекомендации
        recommendations = self._generate_recommendations(
            total_impact,
            base_year_payroll['total_cost'],
            base_year_payroll['headcount']
        )

        return {
            'base_year': base_year,
            'target_year': target_year,
            'rate_changes': rate_changes,
            'total_impact': float(total_impact),
            'impact_percent': float(
                (total_impact / base_year_payroll['total_cost'] * 100)
                if base_year_payroll['total_cost'] > 0 else 0
            ),
            'pension_impact': float(pension_impact),
            'medical_impact': float(medical_impact),
            'social_impact': float(social_impact),
            'recommendations': recommendations,
        }

    def _get_all_rates(self, year: int) -> Dict[str, Decimal]:
        """Получить все ставки для года из справочника TaxRate
        
        Использует TaxRate (справочник налоговых ставок) вместо InsuranceRate.
        Учитывает будущие ставки, которые начнут действовать в целевом году.
        """
        from datetime import date
        from sqlalchemy import or_, and_
        
        # Конвертируем год в дату (1 января указанного года и 31 декабря для поиска будущих ставок)
        calc_date = date(year, 1, 1)
        year_end_date = date(year, 12, 31)
        
        # Получаем ставки для указанной даты
        # Сначала ищем для конкретного департамента
        tax_rates_query_dept = self.db.query(TaxRate).filter(
            TaxRate.is_active == True,
            TaxRate.department_id == self.department_id,
            # Ставка должна быть актуальна на calc_date или начаться в течение года
            or_(
                # Актуальная ставка на calc_date
                and_(
                    TaxRate.effective_from <= calc_date,
                    or_(
                        TaxRate.effective_to.is_(None),
                        TaxRate.effective_to >= calc_date
                    )
                ),
                # Будущая ставка, которая начнет действовать в этом году
                and_(
                    TaxRate.effective_from > calc_date,
                    TaxRate.effective_from <= year_end_date
                )
            )
        ).order_by(TaxRate.effective_from.desc())
        
        tax_rates = tax_rates_query_dept.all()
        
        # Если не найдены ставки для департамента, ищем глобальные ставки (department_id IS NULL)
        if not tax_rates:
            tax_rates_query_global = self.db.query(TaxRate).filter(
                TaxRate.is_active == True,
                TaxRate.department_id.is_(None),  # Глобальные ставки имеют department_id = NULL
                # Ставка должна быть актуальна на calc_date или начаться в течение года
                or_(
                    # Актуальная ставка на calc_date
                    and_(
                        TaxRate.effective_from <= calc_date,
                        or_(
                            TaxRate.effective_to.is_(None),
                            TaxRate.effective_to >= calc_date
                        )
                    ),
                    # Будущая ставка, которая начнет действовать в этом году
                    and_(
                        TaxRate.effective_from > calc_date,
                        TaxRate.effective_from <= year_end_date
                    )
                )
            ).order_by(TaxRate.effective_from.desc())
            tax_rates = tax_rates_query_global.all()
            logger.info(f"Found {len(tax_rates)} global tax rates (department_id IS NULL) for year {year} in _get_all_rates")
        
        # Объединяем с дефолтами
        selected_rates = merge_tax_rates_with_defaults(tax_rates)
        
        # Извлекаем нужные ставки страховых взносов
        # ПРИОРИТЕТ: будущие ставки > текущие ставки
        rates = {}
        logger.info(f"Total tax_rates found: {len(tax_rates)}")
        logger.info(f"Selected rates from merge: {list(selected_rates.keys())}")
        
        for rate_type in [TaxTypeEnum.PENSION_FUND, TaxTypeEnum.MEDICAL_INSURANCE,
                          TaxTypeEnum.SOCIAL_INSURANCE, TaxTypeEnum.INJURY_INSURANCE]:
            # Ищем ставку для этого типа
            rate_obj = None
            
            # Если есть несколько ставок, берем будущую, если она есть, иначе текущую
            matching_rates = [r for r in tax_rates if r.tax_type == rate_type]
            logger.info(f"Found {len(matching_rates)} matching rates for {rate_type.value} in year {year}")
            
            if matching_rates:
                # Разделяем на актуальные и будущие
                current_rates = [r for r in matching_rates if r.effective_from <= calc_date]
                future_rates = [r for r in matching_rates if r.effective_from > calc_date and r.effective_from <= year_end_date]
                
                logger.info(f"Current rates: {len(current_rates)}, Future rates: {len(future_rates)}")
                
                # ВАЖНО: Будущие ставки имеют приоритет
                if future_rates:
                    # Берем самую раннюю будущую ставку (которая начнет действовать первой в целевом году)
                    rate_obj = min(future_rates, key=lambda r: r.effective_from)
                    logger.info(f"Using future rate for {rate_type.value} in {year}: {rate_obj.rate * 100}% (effective_from: {rate_obj.effective_from})")
                elif current_rates:
                    # Если нет будущих, берем самую позднюю актуальную ставку
                    rate_obj = max(current_rates, key=lambda r: r.effective_from)
                    logger.info(f"Using current rate for {rate_type.value} in {year}: {rate_obj.rate * 100}% (effective_from: {rate_obj.effective_from})")
            
            # Если не нашли в tax_rates, используем selected_rates (может быть TaxRateDefault)
            if not rate_obj:
                rate_obj = selected_rates.get(rate_type)
                if rate_obj:
                    logger.info(f"Using rate from selected_rates for {rate_type.value}: {rate_obj.rate * 100}%")
            
            if rate_obj:
                # Может быть TaxRate или TaxRateDefault - оба имеют rate
                if hasattr(rate_obj, 'rate'):
                    rates[rate_type.value] = Decimal(str(rate_obj.rate))
                    logger.info(f"Final rate for {rate_type.value} in {year}: {rates[rate_type.value] * 100}%")
                else:
                    logger.warning(f"Rate object for {rate_type.value} has no 'rate' attribute")
            else:
                # Дефолтные ставки (если ничего не найдено)
                defaults = {
                    'PENSION_FUND': Decimal('0.22'),
                    'MEDICAL_INSURANCE': Decimal('0.051'),
                    'SOCIAL_INSURANCE': Decimal('0.029'),
                    'INJURY_INSURANCE': Decimal('0.002'),
                }
                rates[rate_type.value] = defaults.get(rate_type.value, Decimal('0.00'))
                logger.warning(f"No tax rate found for {rate_type.value} in {year}, using hardcoded default: {rates[rate_type.value] * 100}%")

        return rates

    def _get_year_payroll_data(self, year: int) -> Dict:
        """Получить данные ФОТ за год"""
        result = self.db.query(
            func.count(func.distinct(PayrollActual.employee_id)).label('headcount'),
            func.sum(PayrollActual.total_paid).label('total_salary'),
            func.sum(PayrollActual.social_tax_amount).label('total_insurance'),
            func.sum(PayrollActual.total_paid + PayrollActual.social_tax_amount).label('total_cost')
        ).filter(
            PayrollActual.department_id == self.department_id,
            PayrollActual.year == year
        ).first()

        if result:
            return {
                'headcount': result.headcount or 0,
                'total_salary': result.total_salary or Decimal('0.00'),
                'total_insurance': result.total_insurance or Decimal('0.00'),
                'total_cost': result.total_cost or Decimal('0.00'),
            }

        return {
            'headcount': 0,
            'total_salary': Decimal('0.00'),
            'total_insurance': Decimal('0.00'),
            'total_cost': Decimal('0.00'),
        }

    def _generate_recommendations(
        self, impact: Decimal, current_cost: Decimal, headcount: int
    ) -> List[Dict]:
        """Генерировать рекомендации по оптимизации"""
        recommendations = []

        if impact > 0:
            # Рекомендация 1: Сокращение штата
            if headcount > 0:
                avg_cost_per_employee = current_cost / headcount
                headcount_reduction = int(impact / avg_cost_per_employee)

                if headcount_reduction > 0:
                    recommendations.append({
                        'type': 'headcount_reduction',
                        'description': f'Сократить {headcount_reduction} сотрудников для компенсации роста взносов',
                        'impact': -float(headcount_reduction * avg_cost_per_employee),
                        'details': {
                            'headcount_reduction': headcount_reduction,
                            'avg_cost_per_employee': float(avg_cost_per_employee),
                        }
                    })

            # Рекомендация 2: Снижение зарплат
            if current_cost > 0:
                salary_reduction_percent = (impact / current_cost) * 100

                recommendations.append({
                    'type': 'salary_reduction',
                    'description': f'Снизить фонд зарплат на {salary_reduction_percent:.1f}% для компенсации',
                    'impact': -float(impact),
                    'details': {
                        'reduction_percent': float(salary_reduction_percent),
                    }
                })

            # Рекомендация 3: Оптимизация структуры
            recommendations.append({
                'type': 'structure_optimization',
                'description': 'Пересмотреть структуру премий и бонусов',
                'impact': -float(impact * Decimal('0.3')),  # Примерная экономия 30%
                'details': {
                    'potential_savings_percent': 30,
                }
            })

        return recommendations


class PayrollComparisonGenerator:
    """
    Генератор сравнений ФОТ между годами
    """

    def __init__(self, db: Session, department_id: int):
        self.db = db
        self.department_id = department_id

    def generate_comparison(self, base_year: int, target_year: int) -> PayrollYearlyComparison:
        """
        Сгенерировать сравнение между годами

        Args:
            base_year: Базовый год
            target_year: Целевой год

        Returns:
            PayrollYearlyComparison record
        """
        # Использовать анализатор для расчетов
        analyzer = InsuranceImpactAnalyzer(self.db, self.department_id)
        impact_analysis = analyzer.analyze_impact(base_year, target_year)

        # Получить данные по годам
        base_data = analyzer._get_year_payroll_data(base_year)
        target_data = analyzer._get_year_payroll_data(target_year)

        # Создать или обновить запись
        comparison = self.db.query(PayrollYearlyComparison).filter(
            PayrollYearlyComparison.base_year == base_year,
            PayrollYearlyComparison.target_year == target_year,
            PayrollYearlyComparison.department_id == self.department_id
        ).first()

        if not comparison:
            comparison = PayrollYearlyComparison(
                base_year=base_year,
                target_year=target_year,
                department_id=self.department_id
            )
            self.db.add(comparison)

        # Обновить данные
        comparison.base_year_headcount = base_data['headcount']
        comparison.base_year_total_salary = base_data['total_salary']
        comparison.base_year_total_insurance = base_data['total_insurance']
        comparison.base_year_total_cost = base_data['total_cost']

        comparison.target_year_headcount = target_data['headcount']
        comparison.target_year_total_salary = base_data['total_salary']  # Без изменений в штате
        comparison.target_year_total_insurance = (
            base_data['total_insurance'] + Decimal(str(impact_analysis['total_impact']))
        )
        comparison.target_year_total_cost = (
            comparison.target_year_total_salary + comparison.target_year_total_insurance
        )

        comparison.insurance_rate_change = impact_analysis['rate_changes']
        comparison.total_cost_increase = Decimal(str(impact_analysis['total_impact']))
        comparison.total_cost_increase_percent = Decimal(str(impact_analysis['impact_percent']))

        comparison.pension_increase = Decimal(str(impact_analysis['pension_impact']))
        comparison.medical_increase = Decimal(str(impact_analysis['medical_impact']))
        comparison.social_increase = Decimal(str(impact_analysis['social_impact']))

        comparison.recommendations = impact_analysis['recommendations']
        comparison.calculated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(comparison)

        return comparison
