import argparse
import os
import sys
import time
import mido
from core.data_handler import get_dataframe, validate_columns
from core.midi_builder import generate_midi
from ui.visualizer import create_plot

try:
    os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

class CustomArgumentParser(argparse.ArgumentParser):
    """Перехоплює помилки CLI (зайві параметри, невідомі прапорці) для чистого виводу."""
    def error(self, message):
        print(f"\n[Помилка параметрів запуску] {message}")
        print("Підказка: виконайте 'python main.py -h' для перегляду дозволених прапорців.")
        sys.exit(2)

def validate_cli_args(args):
    """Перевіряє коректність значень та відсутність зайвих переданих параметрів."""
    num_tracks = len(args.pitch)

    if num_tracks > 15:
        raise ValueError(f"Передано {num_tracks} стовпців у --pitch. Максимум у MIDI — 15 мелодійних каналів.")

    # Захист від передачі зайвих аргументів у списках
    if len(args.velocity) > num_tracks:
        raise ValueError(
            f"Зайві параметри у --velocity: передано {len(args.velocity)}, "
            f"але вказано лише {num_tracks} стовпець(ці) у --pitch."
        )
    if args.duration and len(args.duration) > num_tracks:
        raise ValueError(
            f"Зайві параметри у --duration: передано {len(args.duration)}, "
            f"але вказано лише {num_tracks} стовпець(ці) у --pitch."
        )
    if len(args.instrument) > num_tracks:
        raise ValueError(
            f"Зайві параметри у --instrument: передано {len(args.instrument)}, "
            f"але вказано лише {num_tracks} трек(ів) у --pitch."
        )

    # Перевірка діапазону BPM
    if not (30 <= args.bpm <= 300):
        raise ValueError(f"Некоректний темп ({args.bpm} BPM). Допустимий діапазон: 30..300.")

    # Перевірка кожного інструмента в діапазоні 1..128
    for inst in args.instrument:
        if not (1 <= inst <= 128):
            raise ValueError(f"Некоректний номер інструмента ({inst}). Допустимий діапазон General MIDI: 1..128.")

    # Автокорекція розширень вихідних файлів, якщо користувач їх не дописав
    if not args.out_midi.lower().endswith(".mid"):
        args.out_midi += ".mid"
    if not args.out_plot.lower().endswith((".png", ".jpg", ".jpeg")):
        args.out_plot += ".png"

def play_midi(file_path):
    """Відтворює MIDI-файл із прогрес-баром та перехопленням помилок аудіодрайвера."""
    if not PYGAME_AVAILABLE:
        print("\n[Помилка] Бібліотека pygame не встановлена. Виконайте: pip install pygame")
        return

    try:
        mid = mido.MidiFile(file_path)
        total_length = mid.length
    except Exception as e:
        print(f"\n[Помилка читання MIDI] Не вдалося визначити тривалість файлу: {e}")
        return

    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
    except pygame.error as e:
        print(f"\n[Помилка аудіосистеми] Не вдалося ініціалізувати відтворення звуку: {e}")
        print("Перевірте наявність аудіопристрою або програмного синтезатора (наприклад, timidity / fluidsynth).")
        return

    print(f"\n[Відтворення] Запуск '{file_path}'... (Натисніть Ctrl+C для зупинки)")
    bar_len = 30
    try:
        while pygame.mixer.music.get_busy():
            current_pos = pygame.mixer.music.get_pos() / 1000.0
            if total_length > 0:
                progress = min(max(current_pos / total_length, 0.0), 1.0)
                filled_len = int(bar_len * progress)
                bar = '█' * filled_len + '-' * (bar_len - filled_len)
                sys.stdout.write(f"\r\tПрогрес: [{bar}] {int(progress * 100)}% ({current_pos:.1f}с / {total_length:.1f}с)")
                sys.stdout.flush()
            time.sleep(0.1)

        if total_length > 0:
            bar = '█' * bar_len
            sys.stdout.write(f"\r\tПрогрес: [{bar}] 100% ({total_length:.1f}с / {total_length:.1f}с)\n")
        print("\n[Відтворення] Завершено.")

    except KeyboardInterrupt:
        pygame.mixer.music.stop()
        print("\n\n[Відтворення] Зупинено користувачем.")
    finally:
        if pygame.mixer.get_init():
            pygame.mixer.quit()

def main():
    print("=== Запуск програми багатоканальної соніфікації даних ===\n")

    parser = CustomArgumentParser(description="Перетворення числових даних CSV у поліфонічний MIDI")
    parser.add_argument("input_file", help="Шлях до вхідного CSV-файлу")
    parser.add_argument("--pitch", nargs='+', required=True, help="Стовпці для висоти ноти (1..15 значень)")
    parser.add_argument("--velocity", nargs='+', required=True, help="Стовпці для гучності (не більше ніж --pitch)")
    parser.add_argument("--duration", nargs='+', help="Стовпці для тривалості (опціонально, не більше ніж --pitch)")
    parser.add_argument("--instrument", nargs='+', type=int, default=[1], help="Інструменти 1..128 (не більше ніж --pitch)")
    parser.add_argument("--bpm", type=int, default=120, help="Темп у BPM (30..300)")
    parser.add_argument("--play", action="store_true", help="Автоматично відтворити після генерації")
    parser.add_argument("--out-midi", type=str, default="output.mid", help="Ім'я вихідного MIDI-файлу")
    parser.add_argument("--out-plot", type=str, default="sonification_plot.png", help="Ім'я вихідного файлу графіка")

    args = parser.parse_args()

    try:
        # 1. Валідація параметрів CLI
        validate_cli_args(args)

        # 2. Читання та перевірка даних
        data = get_dataframe(args.input_file)
        required_cols = args.pitch + args.velocity + (args.duration if args.duration else [])
        validate_columns(data, required_cols)

        # 3. Побудова графіка лише за вибраними числовими стовпцями
        print("\n--- Етап візуалізації ---")
        create_plot(data, required_cols, args.out_plot)

        # 4. Генерація MIDI
        print("\n--- Етап соніфікації ---")
        generate_midi(
            df=data,
            pitch_cols=args.pitch,
            velocity_cols=args.velocity,
            duration_cols=args.duration,
            instruments=args.instrument,
            bpm=args.bpm,
            output_midi=args.out_midi
        )

    except (FileNotFoundError, IsADirectoryError, KeyError, TypeError, ValueError, PermissionError, OSError, RuntimeError) as e:
        print(f"\n[Помилка виконання] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n[Перервано] Роботу програми зупинено користувачем.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[Критична непередбачувана помилка] {e}")
        sys.exit(1)

    print("\n=== Роботу завершено успішно ===")
    print(f"Результат: збережено '{args.out_midi}' та '{args.out_plot}'.")

    should_play = args.play
    if not should_play:
        try:
            user_choice = input(f"\nБажаєте відтворити згенерований файл '{args.out_midi}' зараз? (y/n): ").strip().lower()
            if user_choice in ['y', 'yes', 'т', 'так']:
                should_play = True
        except (KeyboardInterrupt, EOFError):
            print("\n[Скасовано]")

    if should_play:
        play_midi(args.out_midi)

if __name__ == "__main__":
    main()