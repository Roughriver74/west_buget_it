#!/usr/bin/env python3
"""Скрипт для анализа структуры файла Планфакт2025.xlsx"""

import pandas as pd
import sys

def analyze_excel_file(file_path):
    """Анализ структуры Excel файла"""
    try:
        # Получаем список листов
        excel_file = pd.ExcelFile(file_path)
        print(f"Найдено листов: {len(excel_file.sheet_names)}")
        print(f"Названия листов: {excel_file.sheet_names}\n")

        # Анализируем первые 3 листа
        for i, sheet_name in enumerate(excel_file.sheet_names[:3]):
            print(f"\n{'='*80}")
            print(f"ЛИСТ {i+1}: {sheet_name}")
            print(f"{'='*80}")

            # Читаем лист
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            print(f"\nРазмер: {df.shape[0]} строк × {df.shape[1]} столбцов")
            print(f"\nСтолбцы: {list(df.columns)}")
            print(f"\nПервые 5 строк:")
            print(df.head())
            print(f"\nТипы данных:")
            print(df.dtypes)
            print(f"\nПропущенные значения:")
            print(df.isnull().sum())

    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        sys.exit(1)

if __name__ == "__main__":
    file_path = "/Users/evgenijsikunov/projects/west/west_buget_it/xls/Планфакт2025.xlsx"
    analyze_excel_file(file_path)
