import matplotlib.pyplot as plt


def create_plot(df, output_img="sonification_plot.png"):
    """Створює графік вхідних даних."""
    print("[Візуалізація] Побудова графіка...")
    plt.figure(figsize=(10, 5))

    # Будуємо лінії для перших двох стовпців
    plt.plot(df.iloc[:, 0], label=df.columns[0], color='blue', linewidth=2)
    plt.plot(df.iloc[:, 1], label=df.columns[1], color='red', alpha=0.7)

    plt.title("Візуалізація даних для соніфікації")
    plt.xlabel("Часові кроки")
    plt.ylabel("Значення показників")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)

    plt.savefig(output_img)
    print(f"[Візуалізація] Графік збережено як: {output_img}")
    plt.close()