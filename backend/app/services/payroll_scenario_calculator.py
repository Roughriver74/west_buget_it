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
    TaxTypeEnum,
    PayrollScenarioTypeEnum,
)

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

        if not scenario_details:
            # Если детали не созданы, создать их из текущих сотрудников
            scenario_details = self._create_scenario_details_from_employees(
                scenario, insurance_rates
            )

        # Рассчитать каждого сотрудника
        total_headcount = 0
        total_base_salary = Decimal('0.00')
        total_insurance = Decimal('0.00')
        total_income_tax = Decimal('0.00')
        total_payroll_cost = Decimal('0.00')

        for detail in scenario_details:
            if not detail.is_terminated:
                total_headcount += 1

            # Рассчитать страховые взносы
            insurance_calc = self._calculate_insurance_for_employee(
                detail.base_salary + detail.monthly_bonus,
                insurance_rates
            )

            # Рассчитать НДФЛ (13%)
            income_tax = (detail.base_salary + detail.monthly_bonus) * Decimal('0.13')

            # Обновить детали
            detail.pension_contribution = insurance_calc['pension']
            detail.medical_contribution = insurance_calc['medical']
            detail.social_contribution = insurance_calc['social']
            detail.injury_contribution = insurance_calc['injury']
            detail.total_insurance = insurance_calc['total']
            detail.income_tax = income_tax
            detail.total_employee_cost = (
                detail.base_salary +
                detail.monthly_bonus +
                insurance_calc['total']
            )

            # Аккумулировать итоги
            total_base_salary += detail.base_salary + detail.monthly_bonus
            total_insurance += insurance_calc['total']
            total_income_tax += income_tax
            total_payroll_cost += detail.total_employee_cost

        # Обновить сценарий
        scenario.total_headcount = total_headcount
        scenario.total_base_salary = total_base_salary
        scenario.total_insurance_cost = total_insurance
        scenario.total_payroll_cost = total_payroll_cost

        # Рассчитать сравнение с базовым годом
        base_year_cost = self._get_base_year_cost(scenario.base_year)
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
        """Получить ставки страховых взносов для года"""
        rates = {}

        for rate_type in [TaxTypeEnum.PENSION_FUND, TaxTypeEnum.MEDICAL_INSURANCE,
                          TaxTypeEnum.SOCIAL_INSURANCE, TaxTypeEnum.INJURY_INSURANCE]:
            rate_record = self.db.query(InsuranceRate).filter(
                InsuranceRate.year == year,
                InsuranceRate.rate_type == rate_type,
                InsuranceRate.department_id == self.department_id,
                InsuranceRate.is_active == True
            ).first()

            if rate_record:
                rates[rate_type.value] = rate_record.rate_percentage / 100
            else:
                # Дефолтные ставки на случай отсутствия данных
                defaults = {
                    TaxTypeEnum.PENSION_FUND.value: Decimal('0.22'),
                    TaxTypeEnum.MEDICAL_INSURANCE.value: Decimal('0.051'),
                    TaxTypeEnum.SOCIAL_INSURANCE.value: Decimal('0.029'),
                    TaxTypeEnum.INJURY_INSURANCE.value: Decimal('0.002'),
                }
                rates[rate_type.value] = defaults.get(rate_type.value, Decimal('0.00'))

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

    def _get_employee_base_year_data(
        self, employee_id: int, base_year: int
    ) -> Tuple[Decimal, Decimal]:
        """Получить данные сотрудника за базовый год"""
        payroll = self.db.query(PayrollActual).filter(
            PayrollActual.employee_id == employee_id,
            PayrollActual.year == base_year
        ).first()

        if payroll:
            return payroll.total_paid, payroll.social_tax_amount
        else:
            # Если нет данных, вернуть текущий оклад
            employee = self.db.query(Employee).get(employee_id)
            if employee:
                return employee.base_salary * 12, Decimal('0.00')

        return Decimal('0.00'), Decimal('0.00')

    def _get_base_year_cost(self, base_year: int) -> Decimal:
        """Получить общий ФОТ за базовый год"""
        result = self.db.query(
            func.sum(PayrollActual.total_paid + PayrollActual.social_tax_amount)
        ).filter(
            PayrollActual.department_id == self.department_id,
            PayrollActual.year == base_year
        ).scalar()

        return result or Decimal('0.00')


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

        # Рассчитать изменения
        rate_changes = {}
        for rate_type in base_rates:
            base_rate = base_rates[rate_type]
            target_rate = target_rates.get(rate_type, base_rate)

            rate_changes[rate_type] = {
                'from': float(base_rate * 100),
                'to': float(target_rate * 100),
                'change': float((target_rate - base_rate) * 100),
            }

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
        """Получить все ставки для года"""
        rates = {}

        for rate_type in [TaxTypeEnum.PENSION_FUND, TaxTypeEnum.MEDICAL_INSURANCE,
                          TaxTypeEnum.SOCIAL_INSURANCE, TaxTypeEnum.INJURY_INSURANCE]:
            rate_record = self.db.query(InsuranceRate).filter(
                InsuranceRate.year == year,
                InsuranceRate.rate_type == rate_type,
                InsuranceRate.department_id == self.department_id,
                InsuranceRate.is_active == True
            ).first()

            if rate_record:
                rates[rate_type.value] = rate_record.rate_percentage / 100
            else:
                # Дефолтные ставки
                defaults = {
                    'PENSION_FUND': Decimal('0.22'),
                    'MEDICAL_INSURANCE': Decimal('0.051'),
                    'SOCIAL_INSURANCE': Decimal('0.029'),
                    'INJURY_INSURANCE': Decimal('0.002'),
                }
                rates[rate_type.value] = defaults.get(rate_type.value, Decimal('0.00'))

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
