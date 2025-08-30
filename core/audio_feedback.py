import os
import sounddevice as sd
import soundfile as sf
import threading

ESPEAK_PATH = r"F:\eSpeak\command-line"
os.environ["PATH"] = ESPEAK_PATH + os.pathsep + os.environ.get("PATH", "")

def initiate_tts(tts, text="Sorry! Haven't quite caught that.", speaker_id = "p347", file_path = "assets/sounds/temp.wav"):

    try:
        # parameters for smoother speech
        length_scale = 1.5  # slightly slower speech
        noise_scale = 0.6     # reduces robotic artifacts
        noise_scale_w = 0.6   # affects prosody

        tts.tts_to_file(
            text=text,
            speaker=speaker_id,
            file_path=file_path,
            length_scale=length_scale,
            noise_scale=noise_scale,
            noise_scale_w=noise_scale_w
        )

        wav, sr = sf.read(file_path)
        sd.play(wav, samplerate=sr)
        sd.wait()

    except Exception as e:
        print(f"TTS error: {e}")

    
    