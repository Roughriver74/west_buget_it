"""
Add 'Покупатель' budget category for customer revenue
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department, ExpenseTypeEnum

def add_customer_category():
    db: Session = SessionLocal()

    try:
        # Найти отдел FIN
        fin_dept = db.query(Department).filter_by(code="FIN").first()
        if not fin_dept:
            print("❌ Отдел FIN не найден!")
            return

        print(f"✅ Отдел: {fin_dept.name} (id={fin_dept.id})")

        # Проверить, существует ли категория
        existing = db.query(BudgetCategory).filter(
            BudgetCategory.department_id == fin_dept.id,
            BudgetCategory.name == 'Покупатель'
        ).first()

        if existing:
            print(f"⏭️  Категория 'Покупатель' уже существует (id={existing.id})")
            return

        # Создать категорию
        new_cat = BudgetCategory(
            name='Покупатель',
            type=ExpenseTypeEnum.OPEX,  # Используем OPEX, хотя это доход (нет отдельного Revenue type)
            description='Доходы от покупателей: оплата счетов по заказам, поступления от клиентов',
            department_id=fin_dept.id,
            is_active=True
        )
        db.add(new_cat)
        db.commit()
        db.refresh(new_cat)

        print(f"✅ Добавлена категория 'Покупатель' (id={new_cat.id})")
        print(f"\n{'=' * 80}")
        print("ГОТОВО!")
        print("Категория 'Покупатель' создана для классификации доходов от клиентов.")
        print("Транзакции с 'оплата счету по заказу' будут автоматически относиться к этой категории.")
        print(f"{'=' * 80}")

    finally:
        db.close()

if __name__ == '__main__':
    add_customer_category()
