import os
import sounddevice as sd

# ------------------- Paths -------------------
output_folder = os.path.join(os.path.expanduser("~"), "Documents", "recordings")
os.makedirs(output_folder, exist_ok=True)

output_filename = os.path.join(output_folder, "user_audio.flac")

# ------------------- FFmpeg executable -------------------
ffmpeg_exe = r"C:\ffmpeg\bin\ffmpeg.exe"

# ------------------- Mic info -------------------

default_device_index = sd.default.device[0]  # default input device
mic_name = sd.query_devices(default_device_index, kind='input')['name'] # type: ignore

# ------------------- State variables -------------------
is_recording = False
process = None
