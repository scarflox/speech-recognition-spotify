# Unit tests for recognizer
from TTS.api import TTS
import sounddevice as sd
import soundfile as sf
import librosa

# Initialize the TTS model (only needs to happen once)
tts = TTS(model_name="tts_models/en/ljspeech/fast_pitch", progress_bar=True)

# The text you want to synthesize
text = "Hello world! This is a test of the Tacotron 2 DDC TTS model."

# File path to save output
file_path = "greeting.wav"

# Optional parameters to adjust voice
length_scale = 0.85   # slow down speech (0.85x speed)
noise_scale = 0.6     # reduce robotic artifacts
noise_scale_w = 0.6   # affects prosody

# Generate speech to file
tts.tts_to_file(
    text=text,
    file_path=file_path,
    length_scale=length_scale,
    noise_scale=noise_scale,
    noise_scale_w=noise_scale_w
)

# Load WAV file and resample to 44100Hz for playback
wav, sr = sf.read(file_path)
wav_44100 = librosa.resample(wav, orig_sr=sr, target_sr=44100)

# Play the audio
sd.play(wav_44100, samplerate=44100)
sd.wait()

print(f"TTS finished! File saved to {file_path}")

