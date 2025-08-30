# Unit tests for recognizer
import os
from TTS.api import TTS
import sounddevice as sd

# Make sure eSpeak-NG folder is in PATH

# Load the TTS model
tts = TTS(model_name="tts_models/en/vctk/vits")

# List all available speakers for this model
print("Available speakers:")
for i, speaker in enumerate(tts.speakers):
    print(f"{i}: {speaker}")

# Let user pick a speaker
while True:
    choice = int(input("Enter the number of the speaker to test: "))
    speaker_id = tts.speakers[choice]

    # Generate sample speech
    text = "Hello! This is a test of your chosen TTS voice."
    wav = tts.tts(text, speaker=speaker_id)

    # Play the audio
    print(f"Playing voice: {speaker_id}")
    sd.play(wav, samplerate=tts.synthesizer.output_sample_rate)
    sd.wait()