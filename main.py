import core.recognizer, core.service, keyboard
from TTS.api import TTS
import sounddevice as sd
import os

def main():
    tts = TTS(model_name="tts_models/en/vctk/vits")
    speaker_id = "p347"

    wav = tts.tts("Hello world, can you hear me?", speaker=speaker_id)
    sd.play(wav, samplerate=tts.synthesizer.output_sample_rate)
    sd.wait()
    whisper_model = core.recognizer.initiate_recognizer()
    

    keyboard.add_hotkey('ctrl+alt+k', lambda: core.service.toggle_recording(whisper_model))
    print("Press Ctrl+Alt+K to start/stop recording.")
    print("Press Ctrl+C in terminal to quit.")

    keyboard.wait()

if __name__ == '__main__':
    main() 