#!/usr/bin/env python3
"""Скрипт для анализа файла с FTP"""

import pandas as pd
import sys

def analyze_ftp_file(file_path):
    """Анализ файла с FTP"""
    try:
        # Читаем Excel файл
        df = pd.read_excel(file_path, engine='openpyxl')

        print(f"="*80)
        print(f"АНАЛИЗ ФАЙЛА С FTP")
        print(f"="*80)

        print(f"\nРазмер: {df.shape[0]} строк × {df.shape[1]} столбцов")
        print(f"\nСтолбцы:")
        for i, col in enumerate(df.columns, 1):
            print(f"  {i}. {col}")

        print(f"\nПервые 3 строки:")
        print(df.head(3).to_string())

        # Ищем поле "Подразделение"
        subdivision_cols = [col for col in df.columns if 'подразделен' in col.lower()]

        if subdivision_cols:
            print(f"\n{'='*80}")
            print(f"НАЙДЕНО ПОЛЕ ПОДРАЗДЕЛЕНИЕ: {subdivision_cols}")
            print(f"{'='*80}")

            for col in subdivision_cols:
                print(f"\nУникальные значения в поле '{col}':")
                unique_values = df[col].dropna().unique()
                for val in unique_values:
                    count = df[col].value_counts().get(val, 0)
                    print(f"  - '{val}' ({count} записей)")
        else:
            print(f"\n⚠️  ПОЛЕ 'ПОДРАЗДЕЛЕНИЕ' НЕ НАЙДЕНО!")
            print(f"Доступные столбцы: {list(df.columns)}")

    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    file_path = "/Users/evgenijsikunov/projects/west/west_buget_it/xls/Zayavki na raszkhod(spisok) XLSX.xlsx"
    analyze_ftp_file(file_path)
