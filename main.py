import argparse
import sys
import time
import mido
from core.data_handler import get_dataframe
from core.midi_builder import generate_midi
from ui.visualizer import create_plot

# Намагаємося імпортувати pygame для відтворення
try:
    import os

    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


def play_midi(file_path):
    """Відтворює MIDI-файл із відображенням прогрес-бару у терміналі."""
    if not PYGAME_AVAILABLE:
        print("\n[Помилка] Для автоматичного відтворення потрібно встановити pygame (pip install pygame).")
        return

    # Отримуємо загальну тривалість файлу в секундах через mido
    try:
        mid = mido.MidiFile(file_path)
        total_length = mid.length
    except Exception:
        total_length = 0

    print(f"\n[Відтворення] Запуск '{file_path}'... (Натисніть Ctrl+C для зупинки)")
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    try:
        bar_len = 30  # Довжина прогрес-бару в символах
        while pygame.mixer.music.get_busy():
            current_pos = pygame.mixer.music.get_pos() / 1000.0  # переводимо мілісекунди в секунди

            if total_length > 0:
                # Розрахунок відсотків (уникаємо виходу за 100%)
                progress = min(current_pos / total_length, 1.0)
                filled_len = int(bar_len * progress)
                bar = '█' * filled_len + '-' * (bar_len - filled_len)

                sys.stdout.write(
                    f"\r\tПрогрес: [{bar}] {int(progress * 100)}% ({current_pos:.1f}с / {total_length:.1f}с)")
                sys.stdout.flush()

            time.sleep(0.1)  # Оновлюємо кожні 100 мс для плавності

        # Коли музика закінчилась природним шляхом, заповнюємо бар до кінця
        if total_length > 0:
            bar = '█' * bar_len
            sys.stdout.write(f"\r\tПрогрес: [{bar}] 100% ({total_length:.1f}с / {total_length:.1f}с)\n")
        print("\n[Відтворення] Завершено.")

    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        print("\n\n[Відтворення] Зупинено користувачем.")


def main():
    print("=== Запуск програми багатоканальної соніфікації даних ===\n")

    parser = argparse.ArgumentParser(description="Перетворення CSV у поліфонічний MIDI")
    parser.add_argument("input_file", help="Шлях до вашого CSV файлу")
    parser.add_argument("--pitch", nargs='+', required=True, help="Стовпці для висоти ноти (через пробіл)")
    parser.add_argument("--velocity", nargs='+', required=True, help="Стовпці для гучності (через пробіл)")
    parser.add_argument("--duration", nargs='+', help="Стовпці для тривалості (опціонально)")

    parser.add_argument("--instrument", nargs='+', type=int, default=[1],
                        help="Номери інструментів 1-128 (через пробіл)")
    parser.add_argument("--bpm", type=int, default=120, help="Темп композиції в BPM (30-300)")
    parser.add_argument("--play", action="store_true", help="Автоматично відтворити після генерації")

    # Нові аргументи для імен вихідних файлів
    parser.add_argument("--out-midi", type=str, default="output.mid",
                        help="Ім'я вихідного MIDI файлу (за замовчуванням: output.mid)")
    parser.add_argument("--out-plot", type=str, default="sonification_plot.png",
                        help="Ім'я вихідного файлу графіка (за замовчуванням: sonification_plot.png)")

    args = parser.parse_args()

    try:
        data = get_dataframe(args.input_file)
    except Exception as e:
        print(f"\n[Помилка] {e}")
        sys.exit(1)

    required_cols = args.pitch + args.velocity
    if args.duration:
        required_cols += args.duration

    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        print(f"\n[Помилка] Стовпці {list(set(missing_cols))} не знайдені у файлі.")
        sys.exit(1)

    print("\n--- Етап візуалізації ---")
    # Передаємо ім'я файлу графіка, яке задав користувач
    create_plot(data, args.out_plot)

    print("\n--- Етап соніфікації ---")
    # Передаємо ім'я MIDI файлу, яке задав користувач
    generate_midi(
        df=data,
        pitch_cols=args.pitch,
        velocity_cols=args.velocity,
        duration_cols=args.duration,
        instruments=args.instrument,
        bpm=args.bpm,
        output_midi=args.out_midi
    )

    print("\n=== Роботу завершено успішно ===")
    print(f"Результат: збережено '{args.out_midi}' та '{args.out_plot}'.")

    # Інтерактивна логіка відтворення
    should_play = args.play

    if not should_play:
        try:
            user_choice = input(
                f"\nБажаєте відтворити згенерований файл '{args.out_midi}' зараз? (y/n): ").strip().lower()
            if user_choice in ['y', 'yes', 'т', 'так']:
                should_play = True
        except KeyboardInterrupt:
            print("\n[Скасовано]")

    if should_play:
        play_midi(args.out_midi)


if __name__ == "__main__":
    main()