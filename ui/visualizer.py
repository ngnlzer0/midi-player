import os
import matplotlib.pyplot as plt


def create_plot(df, columns_to_plot, output_img="sonification_plot.png"):
    """Будує графік вибраних числових показників із захистом від помилок запису."""
    print("[Візуалізація] Побудова графіка...")

    # Залишаємо унікальні стовпці, які реально використовувалися для звуку
    unique_cols = list(dict.fromkeys(columns_to_plot))
    colors = ['#1f77b4', '#d62728', '#2ca02c', '#ff7f0e', '#9467bd', '#8c564b']

    try:
        plt.figure(figsize=(10, 5))

        for idx, col in enumerate(unique_cols):
            color = colors[idx % len(colors)]
            plt.plot(df[col].values, label=col, color=color, linewidth=2, alpha=0.85)

        plt.title("Візуалізація показників для соніфікації")
        plt.xlabel("Часові кроки (рядки таблиці)")
        plt.ylabel("Вхідні значення")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)

        out_dir = os.path.dirname(output_img)
        if out_dir and not os.path.exists(out_dir):
            raise FileNotFoundError(f"Директорія '{out_dir}' для збереження графіка не існує.")

        plt.savefig(output_img, dpi=150, bbox_inches='tight')
        print(f"[Візуалізація] Графік збережено як: {output_img}")
    except PermissionError:
        raise PermissionError(f"Немає прав на запис графіка '{output_img}'. Закрийте файл, якщо він відкритий.")
    except Exception as e:
        raise RuntimeError(f"Помилка при створенні графіка: {e}")
    finally:
        plt.close()