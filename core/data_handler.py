import os
import numpy as np
import pandas as pd


def get_dataframe(csv_file):
    if not os.path.exists(csv_file):
        raise FileNotFoundError(f"Файл '{csv_file}' не знайдено. Перевірте правильність шляху.")

    if not os.path.isfile(csv_file):
        raise IsADirectoryError(f"Вказаний шлях '{csv_file}' є директорією, а не файлом.")

    print(f"[Дані] Читання файлу: {csv_file}")
    try:
        df = pd.read_csv(csv_file)
    except pd.errors.EmptyDataError:
        raise ValueError(f"Файл '{csv_file}' абсолютно порожній.")
    except pd.errors.ParserError as e:
        raise ValueError(f"Помилка структури CSV у файлі '{csv_file}': {e}")
    except UnicodeDecodeError:
        raise ValueError(f"Непідтримуване кодування файлу '{csv_file}'. Збережіть його у UTF-8.")
    except PermissionError:
        raise PermissionError(f"Немає прав доступу для читання файлу '{csv_file}'.")

    if df.empty:
        raise ValueError(f"Файл '{csv_file}' містить лише заголовки, але не має жодного рядка даних.")

    print(f"[Дані] Знайдено рядків: {len(df)}")
    print(f"[Дані] Доступні стовпці: {list(df.columns)}")
    return df


def validate_columns(df, cols):
    """Перевіряє існування стовпців, їхній числовий тип та відсутність NaN/Inf."""
    # Зберігаємо порядок, прибираючи дублікати
    unique_cols = list(dict.fromkeys(cols))

    missing_cols = [col for col in unique_cols if col not in df.columns]
    if missing_cols:
        raise KeyError(f"Стовпці {missing_cols} не знайдені у файлі. Доступні: {list(df.columns)}")

    for col in unique_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise TypeError(
                f"Стовпець '{col}' містить нечислові значення (текст або спецсимволи). "
                f"Для соніфікації потрібні лише числові дані."
            )
        if df[col].isna().any():
            raise ValueError(f"Стовпець '{col}' містить порожні значення (NaN). Очистіть або заповніть їх.")
        if np.isinf(df[col]).any():
            raise ValueError(f"Стовпець '{col}' містить нескінченні значення (Inf).")