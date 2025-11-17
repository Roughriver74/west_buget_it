"""
Add enhanced budget categories based on Excel analysis
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import BudgetCategory, Department, ExpenseTypeEnum

def add_categories():
    db: Session = SessionLocal()

    try:
        # Найти отдел FIN
        fin_dept = db.query(Department).filter_by(code="FIN").first()
        if not fin_dept:
            print("❌ Отдел FIN не найден!")
            return

        print(f"✅ Отдел: {fin_dept.name} (id={fin_dept.id})")

        # Категории для добавления (если не существуют)
        categories_to_add = [
            # OPEX
            {
                'name': 'Командировочные расходы',
                'type': ExpenseTypeEnum.OPEX,
                'description': 'Расходы на командировки: проезд, проживание, суточные'
            },
            {
                'name': 'Хозяйственные расходы',
                'type': ExpenseTypeEnum.OPEX,
                'description': 'Хозяйственные товары и расходные материалы'
            },
            # Налоги и взносы
            {
                'name': 'НДФЛ',
                'type': ExpenseTypeEnum.OPEX,
                'description': 'Налог на доходы физических лиц'
            },
            {
                'name': 'Страховые взносы',
                'type': ExpenseTypeEnum.OPEX,
                'description': 'Страховые взносы (ПФР, ФСС, ФФОМС)'
            },
            # Зарплата
            {
                'name': 'Зарплата',
                'type': ExpenseTypeEnum.OPEX,
                'description': 'Заработная плата сотрудников'
            },
        ]

        added = 0
        skipped = 0

        for cat_data in categories_to_add:
            # Проверить, существует ли категория
            existing = db.query(BudgetCategory).filter(
                BudgetCategory.department_id == fin_dept.id,
                BudgetCategory.name == cat_data['name']
            ).first()

            if existing:
                print(f"⏭️  Категория '{cat_data['name']}' уже существует (id={existing.id})")
                skipped += 1
            else:
                # Создать категорию
                new_cat = BudgetCategory(
                    name=cat_data['name'],
                    type=cat_data['type'],
                    description=cat_data['description'],
                    department_id=fin_dept.id,
                    is_active=True
                )
                db.add(new_cat)
                db.flush()  # Получить ID
                print(f"✅ Добавлена категория '{cat_data['name']}' (id={new_cat.id})")
                added += 1

        db.commit()

        print(f"\n{'=' * 80}")
        print(f"ИТОГО:")
        print(f"  Добавлено: {added}")
        print(f"  Пропущено (уже существуют): {skipped}")
        print(f"{'=' * 80}")

    finally:
        db.close()

if __name__ == '__main__':
    add_categories()
