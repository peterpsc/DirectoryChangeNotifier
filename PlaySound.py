import os

import sounddevice
import soundfile


def play_sound(audio_file_path):
    data, fs = soundfile.read(audio_file_path, dtype='float32')
    sounddevice.play(data, fs)
    status = sounddevice.wait()


if __name__ == "__main__":
    base_dir = "Resources"
    name = 'Close the group status report'
    file_name = f"{name}.mp3"
    audio_file_path = os.path.join(base_dir, file_name)

    play_sound(audio_file_path)
