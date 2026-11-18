import os
import numpy as np
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo


def get_note_name(pitch):
    """Перетворює MIDI-номер (0..127) у музичну назву ноти."""
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (pitch // 12) - 1
    return f"{notes[pitch % 12]}{octave}"


def normalize(array, target_min, target_max, name="Unknown"):
    """Масштабує числовий масив у заданий MIDI-діапазон."""
    min_val, max_val = float(np.min(array)), float(np.max(array))
    print(f"  -> Нормалізація '{name}': [{min_val:.2f} ... {max_val:.2f}] -> [{target_min} ... {target_max}]")

    if max_val == min_val:
        return np.full(array.shape, target_min, dtype=int)

    normalized = (array - min_val) / (max_val - min_val)
    return np.round(normalized * (target_max - target_min) + target_min).astype(int)


def align_list(lst, target_len, default_val=None):
    """Розширює список до target_len дублюванням останнього елемента, якщо передано менше значень."""
    if not lst:
        return [default_val] * target_len
    return lst + [lst[-1]] * (target_len - len(lst))


def generate_midi(df, pitch_cols, velocity_cols, duration_cols=None, instruments=None, bpm=120,
                  output_midi="output.mid"):
    """Генерує багатоканальний MIDI-файл із захистом від помилок запису."""
    if instruments is None:
        instruments = [1]

    num_tracks = len(pitch_cols)
    velocity_cols = align_list(velocity_cols, num_tracks)
    duration_cols = align_list(duration_cols, num_tracks) if duration_cols else [None] * num_tracks
    instruments = align_list(instruments, num_tracks, 1)

    print(f"\n  [Багатоканальна генерація]: Треків = {num_tracks}, Темп = {bpm} BPM")
    mid = MidiFile()

    try:
        for i in range(num_tracks):
            print(f"\n  --- Трек {i + 1} (Інструмент #{instruments[i]}) ---")
            track = MidiTrack()
            mid.tracks.append(track)

            if i == 0:
                track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))

            # Канал 9 (10-й у General MIDI) зарезервований під ударні
            channel = i if i < 9 else i + 1
            track.append(Message('program_change', program=instruments[i] - 1, time=0, channel=channel))

            pitch_values = normalize(df[pitch_cols[i]].values, 36, 84, name=f"Pitch: {pitch_cols[i]}")
            velocity_values = normalize(df[velocity_cols[i]].values, 40, 110, name=f"Velocity: {velocity_cols[i]}")

            if duration_cols[i]:
                duration_values = normalize(df[duration_cols[i]].values, 120, 960, name=f"Duration: {duration_cols[i]}")
            else:
                duration_values = np.full(len(df), 240, dtype=int)

            # Вивід журналу перетворення перших 3-х нот треку
            print(f"  [Приклад мапінгу (перші 3 ноти треку {i + 1})]:")
            for idx in range(min(3, len(pitch_values))):
                p = int(pitch_values[idx])
                v = int(velocity_values[idx])
                d = int(duration_values[idx])
                print(f"     Крок {idx + 1}: Pitch={p} ({get_note_name(p)}), Velocity={v}, Duration={d} ticks")

            for pitch, velocity, duration in zip(pitch_values, velocity_values, duration_values):
                track.append(Message('note_on', note=int(pitch), velocity=int(velocity), time=0, channel=channel))
                track.append(
                    Message('note_off', note=int(pitch), velocity=int(velocity), time=int(duration), channel=channel))

        out_dir = os.path.dirname(output_midi)
        if out_dir and not os.path.exists(out_dir):
            raise FileNotFoundError(f"Директорія '{out_dir}' для збереження MIDI не існує.")

        mid.save(output_midi)
        print(f"\n  [MIDI] Файл '{output_midi}' успішно збережено.")

    except PermissionError:
        raise PermissionError(f"Не вдалося перезаписати '{output_midi}'. Можливо, файл відкрито в іншому плеєрі.")
    except OSError as e:
        raise OSError(f"Системна помилка при записі MIDI-файлу '{output_midi}': {e}")