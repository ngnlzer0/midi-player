import numpy as np
from mido import Message, MidiFile, MidiTrack, MetaMessage, bpm2tempo


def get_note_name(pitch):
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = (pitch // 12) - 1
    return f"{notes[pitch % 12]}{octave}"


def normalize(array, target_min, target_max, name="Unknown"):
    min_val, max_val = np.min(array), np.max(array)
    print(f"  -> Нормалізація '{name}': [{min_val:.2f} ... {max_val:.2f}] -> [{target_min} ... {target_max}]")

    if max_val == min_val:
        return np.full(array.shape, target_min)

    normalized = (array - min_val) / (max_val - min_val)
    return (normalized * (target_max - target_min) + target_min).astype(int)


def align_list(lst, target_len, default_val=None):
    """Масштабує список аргументів. Якщо передали 2 Pitch, але 1 Velocity, Velocity дублюється."""
    if not lst:
        return [default_val] * target_len
    if len(lst) >= target_len:
        return lst[:target_len]
    return lst + [lst[-1]] * (target_len - len(lst))


def generate_midi(df, pitch_cols, velocity_cols, duration_cols=None, instruments=[1], bpm=120,
                  output_midi="output.mid"):
    num_tracks = len(pitch_cols)

    # Вирівнюємо масиви налаштувань, щоб їх кількість збігалася з кількістю треків
    velocity_cols = align_list(velocity_cols, num_tracks)
    if duration_cols:
        duration_cols = align_list(duration_cols, num_tracks)
    instruments = align_list(instruments, num_tracks, 1)

    print(f"\n  [Багатоканальна генерація]: Створення {num_tracks} треків. Темп={bpm} BPM")

    mid = MidiFile()

    for i in range(num_tracks):
        print(f"\n  --- Трек {i + 1} (Інструмент {instruments[i]}) ---")
        track = MidiTrack()
        mid.tracks.append(track)

        # Записуємо темп (тільки для першого треку)
        if i == 0:
            track.append(MetaMessage('set_tempo', tempo=bpm2tempo(bpm), time=0))

        # Встановлюємо інструмент на окремому каналі MIDI (від 0 до 15)
        # Канал 9 у MIDI зарезервований під ударні, тому його краще уникати для мелодій
        channel = i if i < 9 else i + 1
        track.append(Message('program_change', program=instruments[i] - 1, time=0, channel=channel))

        # Нормалізація
        pitch_values = normalize(df[pitch_cols[i]].values, 36, 84, name=f"Pitch: {pitch_cols[i]}")
        velocity_values = normalize(df[velocity_cols[i]].values, 40, 110, name=f"Velocity: {velocity_cols[i]}")

        if duration_cols and duration_cols[i]:
            duration_values = normalize(df[duration_cols[i]].values, 120, 960, name=f"Duration: {duration_cols[i]}")
        else:
            duration_values = np.full(len(df), 240)

        # Запис подій
        for pitch, velocity, duration in zip(pitch_values, velocity_values, duration_values):
            track.append(Message('note_on', note=pitch, velocity=velocity, time=0, channel=channel))
            track.append(Message('note_off', note=pitch, velocity=velocity, time=int(duration), channel=channel))

    mid.save(output_midi)
    print(f"\n  [MIDI] Файл {output_midi} успішно згенеровано.")