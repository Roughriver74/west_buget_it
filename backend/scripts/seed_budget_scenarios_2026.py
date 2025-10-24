"""
Seed budget scenarios for 2026 based on IT_BUDGET_CONCEPT_2026.md
Создает 3 сценария планирования бюджета на 2026 год
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from decimal import Decimal
from app.db.database import SessionLocal
from app.db.models import BudgetScenario, BudgetScenarioItem, BudgetCategoryTypeEnum, BudgetPriorityEnum


def create_scenario_1_optimistic(db, base_budget: Decimal = Decimal('37500000')):
    """
    Сценарий 1: ОПТИМИСТИЧНЫЙ (Стабильное развитие)
    Сокращение бюджета на 5-10% (возьмем -7.5%)
    Базовый бюджет 2025: ~40М (предположительно)
    Бюджет 2026: ~37.5М
    """
    total_budget = base_budget  # 37,500,000 RUB

    scenario = BudgetScenario(
        name="Оптимистичный",
        description="Стабильное развитие. Сокращение бюджета на 5-10%. Фокус на критических системах и безопасности.",
        year=2026,
        total_budget=total_budget,
        budget_change_percent=Decimal('-7.5'),
        is_active=True,
        notes="Рекомендуемый сценарий. Сохранение ключевого персонала, усиление кибербезопасности."
    )
    db.add(scenario)
    db.flush()

    items = [
        # OPEX
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="ФОТ (Фонд оплаты труда)",
            percentage=Decimal('55.0'),
            amount=total_budget * Decimal('0.55'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('-3.0'),
            notes="Оптимизация штата, заморозка индексации"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Программное обеспечение",
            percentage=Decimal('18.0'),
            amount=total_budget * Decimal('0.18'),
            priority=BudgetPriorityEnum.HIGH,
            change_from_previous=Decimal('-5.0'),
            notes="Пересмотр лицензий, отказ от неиспользуемых"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Облачные сервисы",
            percentage=Decimal('10.0'),
            amount=total_budget * Decimal('0.10'),
            priority=BudgetPriorityEnum.HIGH,
            change_from_previous=Decimal('2.0'),
            notes="Миграция с on-premise для снижения CAPEX"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Кибербезопасность",
            percentage=Decimal('8.0'),
            amount=total_budget * Decimal('0.08'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('3.0'),
            notes="Обязательное усиление защиты"
        ),
        # CAPEX
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.CAPEX,
            category_name="Оборудование",
            percentage=Decimal('6.0'),
            amount=total_budget * Decimal('0.06'),
            priority=BudgetPriorityEnum.MEDIUM,
            change_from_previous=Decimal('-10.0'),
            notes="Отложить обновление на Q3-Q4"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.CAPEX,
            category_name="Инфраструктурные проекты",
            percentage=Decimal('3.0'),
            amount=total_budget * Decimal('0.03'),
            priority=BudgetPriorityEnum.LOW,
            change_from_previous=Decimal('-15.0'),
            notes="Только критические проекты"
        ),
    ]

    for item in items:
        db.add(item)

    return scenario


def create_scenario_2_baseline(db, base_budget: Decimal = Decimal('33000000')):
    """
    Сценарий 2: БАЗОВЫЙ (Оптимизация и стабилизация)
    Сокращение бюджета на 15-20% (возьмем -17.5%)
    Бюджет 2026: ~33М
    """
    total_budget = base_budget  # 33,000,000 RUB

    scenario = BudgetScenario(
        name="Базовый",
        description="Оптимизация и стабилизация. Сокращение бюджета на 15-20%. Жесткая оптимизация всех расходов.",
        year=2026,
        total_budget=total_budget,
        budget_change_percent=Decimal('-17.5'),
        is_active=True,
        notes="Переход на open-source, максимальная автоматизация, сокращение штата на 10-15%"
    )
    db.add(scenario)
    db.flush()

    items = [
        # OPEX
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="ФОТ (Фонд оплаты труда)",
            percentage=Decimal('58.0'),
            amount=total_budget * Decimal('0.58'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('-12.0'),
            notes="Сокращение штата на 10-15%, оптимизация премий"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Программное обеспечение",
            percentage=Decimal('15.0'),
            amount=total_budget * Decimal('0.15'),
            priority=BudgetPriorityEnum.HIGH,
            change_from_previous=Decimal('-15.0'),
            notes="Переход на open-source решения где возможно"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Облачные сервисы",
            percentage=Decimal('12.0'),
            amount=total_budget * Decimal('0.12'),
            priority=BudgetPriorityEnum.HIGH,
            change_from_previous=Decimal('5.0'),
            notes="Миграция всех возможных сервисов в облако"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Кибербезопасность",
            percentage=Decimal('7.0'),
            amount=total_budget * Decimal('0.07'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('0.0'),
            notes="Сохранить минимум для базовой защиты"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Аутсорсинг",
            percentage=Decimal('3.0'),
            amount=total_budget * Decimal('0.03'),
            priority=BudgetPriorityEnum.MEDIUM,
            change_from_previous=None,
            notes="L1 поддержка, частичный аутсорсинг функций"
        ),
        # CAPEX
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.CAPEX,
            category_name="Оборудование",
            percentage=Decimal('5.0'),
            amount=total_budget * Decimal('0.05'),
            priority=BudgetPriorityEnum.LOW,
            change_from_previous=Decimal('-25.0'),
            notes="Только критическое оборудование"
        ),
    ]

    for item in items:
        db.add(item)

    return scenario


def create_scenario_3_pessimistic(db, base_budget: Decimal = Decimal('30000000')):
    """
    Сценарий 3: ПЕССИМИСТИЧНЫЙ (Режим выживания)
    Сокращение бюджета на 25-30% (возьмем -25%)
    Бюджет 2026: ~30М
    """
    total_budget = base_budget  # 30,000,000 RUB

    scenario = BudgetScenario(
        name="Пессимистичный",
        description="Режим выживания. Сокращение бюджета на 25-30%. Поддержание только критической инфраструктуры.",
        year=2026,
        total_budget=total_budget,
        budget_change_percent=Decimal('-25.0'),
        is_active=False,  # НЕ РЕКОМЕНДУЕТСЯ
        notes="⚠️ НЕ РЕКОМЕНДУЕТСЯ! Критические риски для бизнеса. Рассматривать только в крайнем случае."
    )
    db.add(scenario)
    db.flush()

    items = [
        # OPEX
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="ФОТ (Фонд оплаты труда)",
            percentage=Decimal('50.0'),
            amount=total_budget * Decimal('0.50'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('-30.0'),
            notes="Сокращение до 5-7 ключевых специалистов"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Программное обеспечение",
            percentage=Decimal('10.0'),
            amount=total_budget * Decimal('0.10'),
            priority=BudgetPriorityEnum.MEDIUM,
            change_from_previous=Decimal('-30.0'),
            notes="Только критическое ПО"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Облачные сервисы",
            percentage=Decimal('18.0'),
            amount=total_budget * Decimal('0.18'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('20.0'),
            notes="Максимальная миграция, отказ от собственных серверов"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Кибербезопасность",
            percentage=Decimal('10.0'),
            amount=total_budget * Decimal('0.10'),
            priority=BudgetPriorityEnum.CRITICAL,
            change_from_previous=Decimal('5.0'),
            notes="Базовая защита обязательна"
        ),
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.OPEX,
            category_name="Аутсорсинг",
            percentage=Decimal('10.0'),
            amount=total_budget * Decimal('0.10'),
            priority=BudgetPriorityEnum.HIGH,
            change_from_previous=None,
            notes="Полный аутсорсинг L1/L2 поддержки и инфраструктуры"
        ),
        # CAPEX
        BudgetScenarioItem(
            scenario_id=scenario.id,
            category_type=BudgetCategoryTypeEnum.CAPEX,
            category_name="Оборудование",
            percentage=Decimal('2.0'),
            amount=total_budget * Decimal('0.02'),
            priority=BudgetPriorityEnum.LOW,
            change_from_previous=Decimal('-50.0'),
            notes="Только аварийные замены"
        ),
    ]

    for item in items:
        db.add(item)

    return scenario


def main():
    """Create all three budget scenarios for 2026"""
    db = SessionLocal()

    try:
        print("🚀 Создание бюджетных сценариев на 2026 год...")

        # Create scenarios
        scenario1 = create_scenario_1_optimistic(db)
        print(f"✅ Сценарий 1: {scenario1.name} - {scenario1.total_budget:,.0f} ₽")

        scenario2 = create_scenario_2_baseline(db)
        print(f"✅ Сценарий 2: {scenario2.name} - {scenario2.total_budget:,.0f} ₽")

        scenario3 = create_scenario_3_pessimistic(db)
        print(f"✅ Сценарий 3: {scenario3.name} - {scenario3.total_budget:,.0f} ₽")

        db.commit()

        print("\n📊 Статистика:")
        print(f"  Всего сценариев: 3")
        print(f"  Всего категорий: {db.query(BudgetScenarioItem).count()}")
        print(f"\n💡 Рекомендуемый сценарий: {scenario1.name}")
        print(f"⚠️  НЕ рекомендуется: {scenario3.name}")

        print("\n✅ Готово! Сценарии успешно созданы.")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
