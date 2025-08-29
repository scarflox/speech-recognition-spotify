import os
import whisper
from core.utils import output_filename, ffmpeg_exe

"""
1. The initiate_recognizer() function will be called once when the program starts.
2. The handle_transcription() function will be called at the end of every recording.
"""

def handle_transcription(whisper_model):
    # Ensure FFmpeg is in PATH
    os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep
    print(f"Using FFmpeg from: {ffmpeg_exe}")
    print(f"Transcribing file: {output_filename}")
    
    # Transcribe the audio file
    transcription = whisper_model.transcribe(output_filename)
    print(transcription["text"])


def initiate_recognizer():
    # Add FFmpeg to PATH
    os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep + os.environ["PATH"]
    
    # Load and return the Whisper model
    whisper_model = whisper.load_model("base")
    return whisper_model
