#!/usr/bin/env python3
"""
Подготовка только бюджета по расходам склада для импорта
"""
import pandas as pd
from pathlib import Path

def prepare_expenses_budget(file_path: str, output_path: str):
    """
    Подготовка бюджета по расходам склада
    Файл: Бюджет_склад_расходы_2025_готово.xlsx
    """
    print(f"\n{'='*80}")
    print(f"Подготовка бюджета по расходам склада")
    print(f"{'='*80}\n")

    df = pd.read_excel(file_path, sheet_name='Sheet1')

    print(f"Загружено {len(df)} категорий\n")
    print("Превью данных:")
    print(df.head(10).to_string())
    print("\n")

    # Месяцы для обработки
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

    # Подготовка данных для budget_plan_details
    records = []
    for idx, row in df.iterrows():
        category_name = row['Категория']
        expense_type = row['Тип']

        for month_idx, month_name in enumerate(months, 1):
            amount = row[month_name]

            record = {
                'Категория': category_name,
                'Тип расходов': expense_type,
                'Год': 2025,
                'Месяц': month_idx,
                'Плановая сумма': amount,
                'Обоснование': row.get('Обоснование', ''),
            }
            records.append(record)

    # Создаем DataFrame
    result_df = pd.DataFrame(records)

    # Сохраняем в Excel
    result_df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"✅ Подготовлено {len(records)} записей")
    print(f"📁 Сохранено в: {output_path}")

    # Показываем статистику
    print(f"\n📊 Статистика:")
    print(f"  - Категорий: {len(df)}")
    print(f"  - Месяцев: 12")
    print(f"  - Всего записей: {len(result_df)}")
    print(f"  - Общая сумма: {result_df['Плановая сумма'].sum():,.0f} руб.")

    opex_sum = result_df[result_df['Тип расходов'] == 'OPEX']['Плановая сумма'].sum()
    capex_sum = result_df[result_df['Тип расходов'] == 'CAPEX']['Плановая сумма'].sum()

    print(f"  - OPEX: {opex_sum:,.0f} руб.")
    print(f"  - CAPEX: {capex_sum:,.0f} руб.")

    # Показываем примеры записей
    print(f"\n📋 Примеры записей:")
    print(result_df.head(5).to_string())

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent / "xls"
    output_path = base_path / "prepared"
    output_path.mkdir(exist_ok=True)

    print("\n" + "="*80)
    print("ПОДГОТОВКА БЮДЖЕТА ПО РАСХОДАМ СКЛАДА")
    print("="*80)

    prepare_expenses_budget(
        file_path=base_path / "Бюджет_склад_расходы_2025_готово.xlsx",
        output_path=output_path / "warehouse_expenses_2025_prepared.xlsx"
    )

    print("\n" + "="*80)
    print("✅ ПОДГОТОВКА ЗАВЕРШЕНА")
    print("="*80)
    print(f"\n📁 Подготовленный файл: {output_path / 'warehouse_expenses_2025_prepared.xlsx'}")
    print("\nСледующие шаги:")
    print("1. Скопируйте файл на сервер в /root/import/")
    print("2. Используйте команду для импорта:")
    print("   python scripts/import_budget_plan_details.py --file /root/import/warehouse_expenses_2025_prepared.xlsx")
    print("3. Или используйте Unified Import API через веб-интерфейс")
