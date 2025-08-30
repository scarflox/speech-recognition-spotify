# core/utils.py
import os
import sounddevice as sd
import subprocess
from TTS.api import TTS
import re

# ------------------- Paths -------------------

output_folder = os.path.join(os.path.expanduser("~"), "Documents", "recordings")
os.makedirs(output_folder, exist_ok=True)

output_filename = os.path.join(output_folder, "user_audio.flac")

# ------------------- FFmpeg executable -------------------

ffmpeg_exe = r"C:\ffmpeg\bin\ffmpeg.exe"

global_tts = TTS(model_name="tts_models/en/vctk/vits", progress_bar=True)

def get_alternative_mic_name(friendly_name):
    """
    Use ffmpeg -list_devices to find the alternative DirectShow name for a friendly device name.
    Returns the alternative name string beginning with '@device' (no surrounding quotes),
    or None if not found.
    """
    try:
        # ffmpeg prints devices to stderr
        result = subprocess.run(
            [ffmpeg_exe, "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            capture_output=True,
            text=True,
            check=False
        )
        out_lines = result.stderr.splitlines()
        # look for the line containing the friendly name, then find a nearby line containing '@device'
        for i, line in enumerate(out_lines):
            if friendly_name in line:
                # scan forward a few lines for '@device'
                for j in range(i+1, min(i+6, len(out_lines))):
                    if '@device' in out_lines[j]:
                        match = re.search(r'@device[^"]+', out_lines[j])
                        if match:
                            return match.group(0).strip()
        return None
    except Exception as e:
        print(f"get_alternative_mic_name error: {e}")
        return None

# ------------------- Mic info -------------------

default_device_index = sd.default.device[0]  # default input device index
friendly_mic_name = sd.query_devices(default_device_index, kind='input')['name']  # type: ignore

# try to resolve an alternative DirectShow name (recommended)
alt_name = get_alternative_mic_name(friendly_mic_name)
if alt_name:
    mic_name = alt_name
else:
    mic_name = friendly_mic_name

print(f"Using microphone (friendly): {friendly_mic_name}")
print(f"Using microphone (for ffmpeg): {mic_name}")

# ------------------- State variables -------------------

is_recording = False
process = None

