"""
Payroll-KPI Synchronization Service
Синхронизация PayrollActual ← EmployeeKPI для автоматического создания записей факта зарплаты
"""
from decimal import Decimal
from typing import Optional, Dict, Any, List
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import EmployeeKPI, PayrollActual, PayrollPlan, Employee
import logging

logger = logging.getLogger(__name__)


class PayrollKPISyncService:
    """
    Сервис для синхронизации PayrollActual с EmployeeKPI.

    Создаёт или обновляет записи PayrollActual на основе рассчитанных бонусов из EmployeeKPI.
    """

    def __init__(self, db: Session):
        self.db = db

    def sync_employee_kpi_to_payroll(
        self,
        employee_kpi_id: int,
        base_salary: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Синхронизирует одну запись EmployeeKPI с PayrollActual.

        Args:
            employee_kpi_id: ID записи EmployeeKPI
            base_salary: Базовый оклад (если None, берётся из Employee.base_salary)

        Returns:
            Dict с результатами синхронизации
        """
        # Получаем запись EmployeeKPI
        employee_kpi = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.id == employee_kpi_id
        ).first()

        if not employee_kpi:
            raise ValueError(f"EmployeeKPI с ID {employee_kpi_id} не найден")

        # Получаем сотрудника
        employee = self.db.query(Employee).filter(
            Employee.id == employee_kpi.employee_id
        ).first()

        if not employee:
            raise ValueError(f"Сотрудник с ID {employee_kpi.employee_id} не найден")

        # Определяем базовый оклад
        if base_salary is None:
            base_salary = employee.base_salary or Decimal(0)

        # Проверяем существование записи PayrollActual
        payroll_actual = self.db.query(PayrollActual).filter(
            and_(
                PayrollActual.employee_id == employee_kpi.employee_id,
                PayrollActual.year == employee_kpi.year,
                PayrollActual.month == employee_kpi.month,
                PayrollActual.department_id == employee_kpi.department_id
            )
        ).first()

        # Подготавливаем данные
        monthly_bonus = employee_kpi.monthly_bonus_calculated or Decimal(0)
        quarterly_bonus = employee_kpi.quarterly_bonus_calculated or Decimal(0)
        annual_bonus = employee_kpi.annual_bonus_calculated or Decimal(0)

        total_paid = base_salary + monthly_bonus + quarterly_bonus + annual_bonus

        # Расчёт НДФЛ (13%)
        income_tax_rate = Decimal('0.13')
        income_tax_amount = total_paid * income_tax_rate

        if payroll_actual:
            # Обновляем существующую запись
            payroll_actual.base_salary_paid = base_salary
            payroll_actual.monthly_bonus_paid = monthly_bonus
            payroll_actual.quarterly_bonus_paid = quarterly_bonus
            payroll_actual.annual_bonus_paid = annual_bonus
            payroll_actual.total_paid = total_paid
            payroll_actual.income_tax_amount = income_tax_amount

            action = "updated"
            logger.info(
                f"PayrollActual обновлён для сотрудника#{employee_kpi.employee_id} "
                f"за {employee_kpi.year}-{employee_kpi.month:02d}"
            )
        else:
            # Создаём новую запись
            payroll_actual = PayrollActual(
                year=employee_kpi.year,
                month=employee_kpi.month,
                employee_id=employee_kpi.employee_id,
                department_id=employee_kpi.department_id,
                base_salary_paid=base_salary,
                monthly_bonus_paid=monthly_bonus,
                quarterly_bonus_paid=quarterly_bonus,
                annual_bonus_paid=annual_bonus,
                other_payments_paid=Decimal(0),
                total_paid=total_paid,
                income_tax_rate=income_tax_rate,
                income_tax_amount=income_tax_amount,
                social_tax_amount=Decimal(0),
                notes=f"Синхронизировано из EmployeeKPI#{employee_kpi_id}"
            )
            self.db.add(payroll_actual)

            action = "created"
            logger.info(
                f"PayrollActual создан для сотрудника#{employee_kpi.employee_id} "
                f"за {employee_kpi.year}-{employee_kpi.month:02d}"
            )

        self.db.commit()
        self.db.refresh(payroll_actual)

        return {
            "action": action,
            "payroll_actual_id": payroll_actual.id,
            "employee_kpi_id": employee_kpi_id,
            "employee_id": employee_kpi.employee_id,
            "year": employee_kpi.year,
            "month": employee_kpi.month,
            "base_salary_paid": float(base_salary),
            "monthly_bonus_paid": float(monthly_bonus),
            "quarterly_bonus_paid": float(quarterly_bonus),
            "annual_bonus_paid": float(annual_bonus),
            "total_paid": float(total_paid),
            "income_tax_amount": float(income_tax_amount),
            "net_amount": float(total_paid - income_tax_amount)
        }

    def sync_department_kpi_to_payroll(
        self,
        department_id: int,
        year: int,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Массовая синхронизация всех EmployeeKPI отдела с PayrollActual.

        Args:
            department_id: ID отдела
            year: Год
            month: Месяц (если None, синхронизируются все месяцы года)

        Returns:
            Dict со статистикой синхронизации
        """
        query = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.department_id == department_id,
            EmployeeKPI.year == year
        )

        if month:
            query = query.filter(EmployeeKPI.month == month)

        employee_kpis = query.all()

        success_count = 0
        error_count = 0
        errors = []

        for emp_kpi in employee_kpis:
            try:
                self.sync_employee_kpi_to_payroll(emp_kpi.id)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    "employee_kpi_id": emp_kpi.id,
                    "employee_id": emp_kpi.employee_id,
                    "period": f"{emp_kpi.year}-{emp_kpi.month:02d}",
                    "error": str(e)
                })
                logger.error(
                    f"Ошибка при синхронизации EmployeeKPI#{emp_kpi.id}: {e}"
                )

        return {
            "total": len(employee_kpis),
            "success": success_count,
            "errors": error_count,
            "error_details": errors
        }

    def get_sync_preview(
        self,
        employee_kpi_id: int,
        base_salary: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Предпросмотр синхронизации без сохранения в БД.

        Показывает, какие данные будут синхронизированы.
        """
        employee_kpi = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.id == employee_kpi_id
        ).first()

        if not employee_kpi:
            raise ValueError(f"EmployeeKPI с ID {employee_kpi_id} не найден")

        employee = self.db.query(Employee).filter(
            Employee.id == employee_kpi.employee_id
        ).first()

        if not employee:
            raise ValueError(f"Сотрудник с ID {employee_kpi.employee_id} не найден")

        if base_salary is None:
            base_salary = employee.base_salary or Decimal(0)

        monthly_bonus = employee_kpi.monthly_bonus_calculated or Decimal(0)
        quarterly_bonus = employee_kpi.quarterly_bonus_calculated or Decimal(0)
        annual_bonus = employee_kpi.annual_bonus_calculated or Decimal(0)

        total_paid = base_salary + monthly_bonus + quarterly_bonus + annual_bonus
        income_tax_amount = total_paid * Decimal('0.13')

        # Проверяем существование записи
        existing = self.db.query(PayrollActual).filter(
            and_(
                PayrollActual.employee_id == employee_kpi.employee_id,
                PayrollActual.year == employee_kpi.year,
                PayrollActual.month == employee_kpi.month,
                PayrollActual.department_id == employee_kpi.department_id
            )
        ).first()

        return {
            "will_create": existing is None,
            "existing_payroll_actual_id": existing.id if existing else None,
            "employee_id": employee_kpi.employee_id,
            "employee_name": employee.full_name,
            "year": employee_kpi.year,
            "month": employee_kpi.month,
            "preview": {
                "base_salary_paid": float(base_salary),
                "monthly_bonus_paid": float(monthly_bonus),
                "quarterly_bonus_paid": float(quarterly_bonus),
                "annual_bonus_paid": float(annual_bonus),
                "total_paid": float(total_paid),
                "income_tax_amount": float(income_tax_amount),
                "net_amount": float(total_paid - income_tax_amount)
            }
        }

    def sync_employee_kpi_to_payroll_plan(
        self,
        employee_kpi_id: int
    ) -> Dict[str, Any]:
        """
        Синхронизирует рассчитанные бонусы из EmployeeKPI в PayrollPlan.

        Вызывается автоматически при approve EmployeeKPI.
        Обновляет плановые бонусы (monthly_bonus, quarterly_bonus, annual_bonus).

        Args:
            employee_kpi_id: ID записи EmployeeKPI

        Returns:
            Dict с результатами синхронизации
        """
        # Получаем запись EmployeeKPI
        employee_kpi = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.id == employee_kpi_id
        ).first()

        if not employee_kpi:
            raise ValueError(f"EmployeeKPI с ID {employee_kpi_id} не найден")

        # Получаем сотрудника для базового оклада
        employee = self.db.query(Employee).filter(
            Employee.id == employee_kpi.employee_id
        ).first()

        if not employee:
            raise ValueError(f"Сотрудник с ID {employee_kpi.employee_id} не найден")

        # Ищем существующую запись PayrollPlan
        payroll_plan = self.db.query(PayrollPlan).filter(
            and_(
                PayrollPlan.employee_id == employee_kpi.employee_id,
                PayrollPlan.year == employee_kpi.year,
                PayrollPlan.month == employee_kpi.month,
                PayrollPlan.department_id == employee_kpi.department_id
            )
        ).first()

        # Подготавливаем данные бонусов
        monthly_bonus = employee_kpi.monthly_bonus_calculated or Decimal(0)
        quarterly_bonus = employee_kpi.quarterly_bonus_calculated or Decimal(0)
        annual_bonus = employee_kpi.annual_bonus_calculated or Decimal(0)

        base_salary = employee.base_salary or Decimal(0)
        total_planned = base_salary + monthly_bonus + quarterly_bonus + annual_bonus

        if payroll_plan:
            # Обновляем существующую запись
            payroll_plan.monthly_bonus = monthly_bonus
            payroll_plan.quarterly_bonus = quarterly_bonus
            payroll_plan.annual_bonus = annual_bonus
            payroll_plan.total_planned = total_planned

            action = "updated"
            logger.info(
                f"PayrollPlan обновлён для сотрудника#{employee_kpi.employee_id} "
                f"за {employee_kpi.year}-{employee_kpi.month:02d}"
            )
        else:
            # Создаём новую запись
            payroll_plan = PayrollPlan(
                year=employee_kpi.year,
                month=employee_kpi.month,
                employee_id=employee_kpi.employee_id,
                department_id=employee_kpi.department_id,
                base_salary=base_salary,
                monthly_bonus=monthly_bonus,
                quarterly_bonus=quarterly_bonus,
                annual_bonus=annual_bonus,
                other_payments=Decimal(0),
                total_planned=total_planned,
                notes=f"Синхронизировано из EmployeeKPI#{employee_kpi_id} (APPROVED)"
            )
            self.db.add(payroll_plan)

            action = "created"
            logger.info(
                f"PayrollPlan создан для сотрудника#{employee_kpi.employee_id} "
                f"за {employee_kpi.year}-{employee_kpi.month:02d}"
            )

        self.db.commit()
        self.db.refresh(payroll_plan)

        return {
            "action": action,
            "payroll_plan_id": payroll_plan.id,
            "employee_kpi_id": employee_kpi_id,
            "employee_id": employee_kpi.employee_id,
            "employee_name": employee.full_name,
            "year": employee_kpi.year,
            "month": employee_kpi.month,
            "base_salary": float(base_salary),
            "monthly_bonus": float(monthly_bonus),
            "quarterly_bonus": float(quarterly_bonus),
            "annual_bonus": float(annual_bonus),
            "total_planned": float(total_planned)
        }
