#!/usr/bin/env python3
"""
Анализ структуры Excel файлов для импорта данных склада
"""
import pandas as pd
from pathlib import Path

def analyze_excel_file(file_path: str):
    """Анализирует структуру Excel файла"""
    print(f"\n{'='*80}")
    print(f"Анализ файла: {Path(file_path).name}")
    print(f"{'='*80}\n")

    try:
        # Читаем все листы
        excel_file = pd.ExcelFile(file_path)
        print(f"Количество листов: {len(excel_file.sheet_names)}")
        print(f"Названия листов: {excel_file.sheet_names}\n")

        # Анализируем каждый лист
        for sheet_name in excel_file.sheet_names:
            print(f"\n--- Лист: {sheet_name} ---")
            df = pd.read_excel(file_path, sheet_name=sheet_name, nrows=10)

            print(f"Размер данных: {df.shape[0]} строк x {df.shape[1]} столбцов")
            print(f"\nСтолбцы:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col}")

            print(f"\nПервые 3 строки данных:")
            print(df.head(3).to_string())

            # Проверяем типы данных
            print(f"\nТипы данных:")
            print(df.dtypes.to_string())

            # Проверяем пустые значения
            null_counts = df.isnull().sum()
            if null_counts.any():
                print(f"\nПустые значения:")
                print(null_counts[null_counts > 0].to_string())

            print("\n" + "-"*80)

    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    base_path = Path(__file__).parent.parent.parent / "xls"

    # Анализируем файл с зарплатой
    analyze_excel_file(base_path / "Бюджет ЗП склад 2025_3.xlsx")

    # Анализируем файл с расходами
    analyze_excel_file(base_path / "Бюджет_склад_расходы_2025_готово.xlsx")
