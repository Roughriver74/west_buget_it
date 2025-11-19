"""
KPI Calculation Service - Автоматический расчет KPI% на основе взвешенных целей
"""
from decimal import Decimal
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.db.models import EmployeeKPI, EmployeeKPIGoal, KPIGoalStatusEnum
import logging

logger = logging.getLogger(__name__)


class KPICalculationService:
    """
    Сервис для расчета KPI% сотрудника на основе взвешенных достижений по целям.

    Формула:
    kpi_percentage = sum(achievement_percentage * weight) / sum(weight)

    Пример:
    - Цель 1: achievement=85%, weight=50 → 85 * 50 = 4250
    - Цель 2: achievement=100%, weight=30 → 100 * 30 = 3000
    - Цель 3: achievement=75%, weight=20 → 75 * 20 = 1500
    - Итого: (4250 + 3000 + 1500) / (50 + 30 + 20) = 8750 / 100 = 87.5%
    """

    def __init__(self, db: Session):
        self.db = db

    def calculate_employee_kpi_percentage(
        self,
        employee_kpi_id: int,
        auto_save: bool = True
    ) -> Dict[str, Any]:
        """
        Рассчитывает KPI% для конкретной записи EmployeeKPI на основе связанных целей.

        Args:
            employee_kpi_id: ID записи EmployeeKPI
            auto_save: Автоматически сохранять результат в БД

        Returns:
            Dict с результатами расчета:
            {
                "employee_kpi_id": int,
                "kpi_percentage": Decimal,
                "total_weight": Decimal,
                "goals_count": int,
                "goals": [
                    {
                        "goal_id": int,
                        "goal_name": str,
                        "achievement_percentage": Decimal,
                        "weight": Decimal,
                        "weighted_achievement": Decimal
                    }
                ]
            }
        """
        # Получаем запись EmployeeKPI
        employee_kpi = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.id == employee_kpi_id
        ).first()

        if not employee_kpi:
            raise ValueError(f"EmployeeKPI с ID {employee_kpi_id} не найден")

        # Получаем все активные цели для этого периода
        goals = self.db.query(EmployeeKPIGoal).filter(
            and_(
                EmployeeKPIGoal.employee_kpi_id == employee_kpi_id,
                EmployeeKPIGoal.status == KPIGoalStatusEnum.ACTIVE
            )
        ).all()

        if not goals:
            logger.warning(
                f"Нет активных целей для EmployeeKPI#{employee_kpi_id}. "
                f"KPI% установлен в NULL."
            )
            if auto_save:
                employee_kpi.kpi_percentage = None
                self.db.commit()

            return {
                "employee_kpi_id": employee_kpi_id,
                "kpi_percentage": None,
                "total_weight": Decimal(0),
                "goals_count": 0,
                "goals": []
            }

        # Расчет взвешенного KPI%
        total_weighted_achievement = Decimal(0)
        total_weight = Decimal(0)
        goals_details = []

        for goal in goals:
            # Пропускаем цели без веса или достижения
            if goal.weight is None or goal.weight == 0:
                logger.warning(
                    f"EmployeeKPIGoal#{goal.id} имеет weight=0 или NULL. Пропускаем."
                )
                continue

            if goal.achievement_percentage is None:
                logger.warning(
                    f"EmployeeKPIGoal#{goal.id} не имеет achievement_percentage. "
                    f"Используем 0%."
                )
                achievement = Decimal(0)
            else:
                achievement = Decimal(str(goal.achievement_percentage))

            weight = Decimal(str(goal.weight))
            weighted_achievement = achievement * weight

            total_weighted_achievement += weighted_achievement
            total_weight += weight

            goals_details.append({
                "goal_id": goal.goal_id,
                "goal_name": goal.goal.name if goal.goal else "Unknown",
                "achievement_percentage": float(achievement),
                "weight": float(weight),
                "weighted_achievement": float(weighted_achievement)
            })

        # Финальный расчет KPI%
        if total_weight == 0:
            logger.warning(
                f"Сумма весов для EmployeeKPI#{employee_kpi_id} равна 0. "
                f"KPI% установлен в NULL."
            )
            kpi_percentage = None
        else:
            kpi_percentage = total_weighted_achievement / total_weight
            # Округляем до 2 знаков после запятой
            kpi_percentage = kpi_percentage.quantize(Decimal('0.01'))

        # Сохраняем результат
        if auto_save:
            employee_kpi.kpi_percentage = kpi_percentage
            self.db.commit()
            self.db.refresh(employee_kpi)
            logger.info(
                f"KPI% для EmployeeKPI#{employee_kpi_id} рассчитан: "
                f"{kpi_percentage}% (на основе {len(goals)} целей)"
            )

        return {
            "employee_kpi_id": employee_kpi_id,
            "kpi_percentage": float(kpi_percentage) if kpi_percentage else None,
            "total_weight": float(total_weight),
            "goals_count": len(goals_details),
            "goals": goals_details
        }

    def calculate_for_employee_period(
        self,
        employee_id: int,
        year: int,
        month: int,
        auto_save: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Рассчитывает KPI% для сотрудника за конкретный период.

        Args:
            employee_id: ID сотрудника
            year: Год
            month: Месяц (1-12)
            auto_save: Автоматически сохранять результат

        Returns:
            Dict с результатами или None если запись не найдена
        """
        employee_kpi = self.db.query(EmployeeKPI).filter(
            and_(
                EmployeeKPI.employee_id == employee_id,
                EmployeeKPI.year == year,
                EmployeeKPI.month == month
            )
        ).first()

        if not employee_kpi:
            logger.warning(
                f"EmployeeKPI для сотрудника#{employee_id} за {year}-{month:02d} не найден"
            )
            return None

        return self.calculate_employee_kpi_percentage(
            employee_kpi_id=employee_kpi.id,
            auto_save=auto_save
        )

    def recalculate_all_for_department(
        self,
        department_id: int,
        year: Optional[int] = None,
        month: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Пересчитывает KPI% для всех сотрудников отдела за указанный период.

        Args:
            department_id: ID отдела
            year: Год (если None, пересчет для всех годов)
            month: Месяц (если None, пересчет для всех месяцев)

        Returns:
            Dict со статистикой пересчета
        """
        query = self.db.query(EmployeeKPI).filter(
            EmployeeKPI.department_id == department_id
        )

        if year:
            query = query.filter(EmployeeKPI.year == year)
        if month:
            query = query.filter(EmployeeKPI.month == month)

        employee_kpis = query.all()

        success_count = 0
        error_count = 0
        errors = []

        for emp_kpi in employee_kpis:
            try:
                self.calculate_employee_kpi_percentage(
                    employee_kpi_id=emp_kpi.id,
                    auto_save=True
                )
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
                    f"Ошибка при расчете KPI для EmployeeKPI#{emp_kpi.id}: {e}"
                )

        return {
            "total": len(employee_kpis),
            "success": success_count,
            "errors": error_count,
            "error_details": errors
        }
