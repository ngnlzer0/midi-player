import os
import pandas as pd


def get_dataframe(csv_file):
    """Читає дані з переданого CSV файлу."""
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Файл '{csv_file}' не знайдено! Перевірте правильність шляху.")

    print(f"[Дані] Читання файлу: {csv_file}")
    df = pd.read_csv(csv_file)

    print(f"[Дані] Знайдено рядків: {len(df)}")
    print(f"[Дані] Знайдено показники: {list(df.columns)}")

    return df