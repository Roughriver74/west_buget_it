#!/usr/bin/env python3
"""
Подготовка данных склада для импорта
"""
import pandas as pd
from pathlib import Path
import json
from datetime import datetime

def prepare_expenses_budget(file_path: str, output_path: str):
    """
    Подготовка бюджета по расходам склада
    Файл: Бюджет_склад_расходы_2025_готово.xlsx
    """
    print(f"\n{'='*80}")
    print(f"Подготовка бюджета по расходам")
    print(f"{'='*80}\n")

    df = pd.read_excel(file_path, sheet_name='Sheet1')

    print(f"Загружено {len(df)} категорий\n")
    print("Превью данных:")
    print(df.head().to_string())

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
    print(f"\n✅ Подготовлено {len(records)} записей")
    print(f"📁 Сохранено в: {output_path}")

    # Показываем статистику
    print(f"\n📊 Статистика:")
    print(f"  - Категорий: {len(df)}")
    print(f"  - Месяцев: 12")
    print(f"  - Общая сумма: {result_df['Плановая сумма'].sum():,.0f} руб.")
    print(f"  - OPEX: {result_df[result_df['Тип расходов'] == 'OPEX']['Плановая сумма'].sum():,.0f} руб.")
    print(f"  - CAPEX: {result_df[result_df['Тип расходов'] == 'CAPEX']['Плановая сумма'].sum():,.0f} руб.")

def prepare_payroll_budget(file_path: str, output_path: str, sheet_name: str = 'мой'):
    """
    Подготовка бюджета по зарплате склада
    Файл: Бюджет ЗП склад 2025_3.xlsx
    """
    print(f"\n{'='*80}")
    print(f"Подготовка бюджета по зарплате (лист: {sheet_name})")
    print(f"{'='*80}\n")

    # Читаем файл с пропуском первых строк
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    print(f"Размер данных: {df.shape}")
    print("\nПервые 10 строк:")
    print(df.head(10).to_string())

    # Ищем строку с заголовками
    header_row = None
    for idx, row in df.iterrows():
        if 'ФИО' in str(row.values):
            header_row = idx
            print(f"\n✅ Найдена строка заголовков: {idx}")
            break

    if header_row is None:
        print("❌ Не найдена строка заголовков с 'ФИО'")
        return

    # Получаем заголовки
    headers = df.iloc[header_row].tolist()
    print(f"\nЗаголовки: {headers[:10]}...")

    # Получаем данные (строки после заголовков)
    data_df = df.iloc[header_row + 1:].reset_index(drop=True)
    data_df.columns = headers

    # Фильтруем пустые строки
    data_df = data_df.dropna(subset=['ФИО'])

    print(f"\n✅ Загружено {len(data_df)} сотрудников\n")

    # Месяцы в файле
    month_columns = {
        'Янв': 1, 'февр': 2, 'март': 3, 'апрель': 4, 'май': 5, 'июнь': 6,
        'июль': 7, 'авг': 8, 'сент': 9, 'сент/негат.': 9,
        'окт': 10, 'окт/негат.': 10,
        'нояб': 11, 'нояб/негат.': 11,
        'дек +10%': 12, 'дек/негат. +10%': 12
    }

    # Подготовка данных для payroll_plans
    records = []
    for idx, row in data_df.iterrows():
        full_name = row['ФИО']
        position = row.get('Должность', '')

        # Пропускаем строки без ФИО
        if pd.isna(full_name) or full_name == '':
            continue

        print(f"  - {full_name} ({position})")

        # Извлекаем помесячные суммы
        for month_col, month_num in month_columns.items():
            if month_col in row.index:
                amount = row[month_col]

                # Конвертируем в число
                if pd.notna(amount):
                    try:
                        amount = float(str(amount).replace(' ', '').replace(',', '.'))
                    except:
                        amount = 0
                else:
                    amount = 0

                if amount > 0:
                    record = {
                        'ФИО': full_name,
                        'Должность': position,
                        'Год': 2025,
                        'Месяц': month_num,
                        'Оклад': amount,
                        'Премия': 0,  # Премии нужно извлекать отдельно
                        'Тип премии': 'FIXED',
                        'Статус': 'DRAFT'
                    }
                    records.append(record)

    # Создаем DataFrame
    if len(records) == 0:
        print("\n❌ Не найдено данных для импорта")
        return

    result_df = pd.DataFrame(records)

    # Группируем по месяцам (если есть дубли)
    result_df = result_df.groupby(['ФИО', 'Должность', 'Год', 'Месяц'], as_index=False).agg({
        'Оклад': 'sum',
        'Премия': 'first',
        'Тип премии': 'first',
        'Статус': 'first'
    })

    # Сохраняем в Excel
    result_df.to_excel(output_path, index=False, engine='openpyxl')
    print(f"\n✅ Подготовлено {len(result_df)} записей")
    print(f"📁 Сохранено в: {output_path}")

    # Показываем статистику
    print(f"\n📊 Статистика:")
    print(f"  - Сотрудников: {result_df['ФИО'].nunique()}")
    print(f"  - Записей: {len(result_df)}")
    print(f"  - Общий фонд оплаты труда: {result_df['Оклад'].sum():,.0f} руб.")
    print(f"  - Средняя зарплата: {result_df['Оклад'].mean():,.0f} руб.")

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent / "xls"
    output_path = base_path / "prepared"
    output_path.mkdir(exist_ok=True)

    print("\n" + "="*80)
    print("ПОДГОТОВКА ДАННЫХ СКЛАДА ДЛЯ ИМПОРТА")
    print("="*80)

    # 1. Подготовка бюджета по расходам
    prepare_expenses_budget(
        file_path=base_path / "Бюджет_склад_расходы_2025_готово.xlsx",
        output_path=output_path / "warehouse_expenses_2025_prepared.xlsx"
    )

    # 2. Подготовка бюджета по зарплате
    prepare_payroll_budget(
        file_path=base_path / "Бюджет ЗП склад 2025_3.xlsx",
        output_path=output_path / "warehouse_payroll_2025_prepared.xlsx",
        sheet_name='мой'  # Используем лист 'мой' или '2025г.'
    )

    print("\n" + "="*80)
    print("✅ ПОДГОТОВКА ЗАВЕРШЕНА")
    print("="*80)
    print(f"\n📁 Подготовленные файлы находятся в: {output_path}")
    print("\nСледующие шаги:")
    print("1. Скопируйте файлы на сервер")
    print("2. Используйте Unified Import API для загрузки данных")
    print("3. Или используйте legacy скрипты импорта")
