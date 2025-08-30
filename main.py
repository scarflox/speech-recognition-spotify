
import core.recognizer, core.service, keyboard
import os
from core.utils import global_tts
import core.audio_feedback as af


ESPEAK_PATH = r"F:\eSpeak\command-line"
os.environ["PATH"] += ";" + ESPEAK_PATH

def main():
    
    af.initiate_tts(global_tts, text="Hello! I'm Q, your virtual assistant!")
    
    whisper_model = core.recognizer.initiate_recognizer()

    keyboard.add_hotkey('ctrl+alt+k', lambda: core.service.toggle_recording(whisper_model))
    print("Press Ctrl+Alt+K to start/stop recording.")
    print("Press Ctrl+C in terminal to quit.")

    keyboard.wait()

if __name__ == '__main__':
    main()
