#!/usr/bin/env python3
"""
Скрипт для конвертации бюджетных файлов склада в формат для импорта
Преобразует файлы вида "Бюджет по расходам склада 2025г..xls"
в формат совместимый с API импорта (Категория, Тип, Январь...Декабрь, Обоснование)
"""

import sys
import os
from pathlib import Path
import argparse
import pandas as pd
from decimal import Decimal

# Добавляем родительскую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

MONTH_NAMES = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']


def convert_warehouse_expenses(input_file: str, output_file: str, expense_type: str = 'OPEX'):
    """
    Конвертирует файл бюджета расходов склада в стандартный формат

    Входной формат:
    - Строка 0-2: заголовки
    - Строка 3: даты месяцев (datetime)
    - Строки 4+: [номер, категория, пусто, янв, фев, ..., дек, итого, примечание]

    Выходной формат:
    - Категория, Тип, Январь, Февраль, ..., Декабрь, Обоснование
    """
    print(f"\n{'='*80}")
    print(f"КОНВЕРТАЦИЯ: {os.path.basename(input_file)}")
    print(f"{'='*80}\n")

    # Читаем Excel без заголовков
    df = pd.read_excel(input_file, header=None)

    # Находим строку с данными (первая строка с числовым индексом в колонке 0)
    start_row = None
    for i in range(len(df)):
        if pd.notna(df.iloc[i, 0]) and isinstance(df.iloc[i, 0], (int, float)):
            start_row = i
            break

    if start_row is None:
        raise ValueError("Не найдена строка с данными (первая колонка должна содержать номера)")

    print(f"✓ Данные начинаются со строки {start_row}")

    # Создаем новый DataFrame для результата
    result_data = []

    # Обрабатываем каждую строку с данными
    for i in range(start_row, len(df)):
        row = df.iloc[i]

        # Проверяем, есть ли название категории
        if pd.isna(row[1]) or not isinstance(row[1], str):
            continue

        category_name = str(row[1]).strip()

        # Пропускаем строки-итоги
        if any(word in category_name.lower() for word in ['итого', 'всего', 'общие затраты']):
            continue

        # Собираем данные по месяцам (колонки 3-14)
        month_data = {}
        for month_idx in range(12):
            col_idx = 3 + month_idx
            if col_idx < len(row):
                value = row[col_idx]
                if pd.notna(value):
                    try:
                        month_data[MONTH_NAMES[month_idx]] = float(value)
                    except:
                        month_data[MONTH_NAMES[month_idx]] = 0
                else:
                    month_data[MONTH_NAMES[month_idx]] = 0
            else:
                month_data[MONTH_NAMES[month_idx]] = 0

        # Обоснование (если есть в последней колонке)
        justification = ''
        if len(row) > 15 and pd.notna(row[15]):
            justification = str(row[15]).strip()

        # Добавляем в результат
        result_row = {
            'Категория': category_name,
            'Тип': expense_type,
            **month_data,
            'Обоснование': justification
        }
        result_data.append(result_row)

    # Создаем результирующий DataFrame
    result_df = pd.DataFrame(result_data)

    # Сохраняем в Excel
    result_df.to_excel(output_file, index=False)

    print(f"\n✓ Обработано категорий: {len(result_data)}")
    print(f"✓ Сохранено в: {output_file}")
    print(f"\nПример данных:")
    print(result_df.head(3).to_string())
    print()

    return result_df


def convert_warehouse_payroll(input_file: str, output_file: str):
    """
    Конвертирует файл бюджета зарплат склада в стандартный формат

    Это сложный файл с премиями, нужно адаптировать под конкретную структуру
    """
    print(f"\n{'='*80}")
    print(f"КОНВЕРТАЦИЯ ЗП: {os.path.basename(input_file)}")
    print(f"{'='*80}\n")

    # Читаем Excel без заголовков
    df = pd.read_excel(input_file, header=None)

    print(f"⚠️  Файл зарплат имеет сложную структуру")
    print(f"Размер: {df.shape[0]} строк x {df.shape[1]} колонок")
    print(f"\nПервые 10 строк:")
    for i in range(min(10, len(df))):
        row_preview = [str(x)[:30] for x in df.iloc[i].tolist()[:5]]
        print(f"  {i}: {row_preview}")

    print(f"\n⚠️  Требуется ручная адаптация структуры файла!")
    print(f"Рекомендация: подготовьте файл в формате:")
    print(f"  Категория | Тип | Январь | ... | Декабрь | Обоснование")

    return None


def main():
    parser = argparse.ArgumentParser(
        description='Конвертация бюджетных файлов склада в стандартный формат для импорта'
    )
    parser.add_argument('input', help='Путь к исходному Excel файлу')
    parser.add_argument('output', help='Путь для сохранения конвертированного файла')
    parser.add_argument('--type', choices=['OPEX', 'CAPEX'], default='OPEX',
                       help='Тип расходов (по умолчанию: OPEX)')
    parser.add_argument('--payroll', action='store_true',
                       help='Файл содержит зарплаты (требует специальной обработки)')

    args = parser.parse_args()

    # Проверяем существование файла
    if not os.path.exists(args.input):
        print(f"❌ Файл не найден: {args.input}")
        sys.exit(1)

    try:
        if args.payroll:
            result = convert_warehouse_payroll(args.input, args.output)
        else:
            result = convert_warehouse_expenses(args.input, args.output, args.type)

        if result is not None:
            print(f"\n✅ Конвертация завершена успешно!")
            print(f"\nСледующие шаги:")
            print(f"1. Проверьте файл: {args.output}")
            print(f"2. Убедитесь, что категории существуют в системе")
            print(f"3. Импортируйте через UI или API")
        else:
            print(f"\n⚠️  Конвертация требует доработки")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
