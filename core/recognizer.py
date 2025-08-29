import os
import whisper
from core.utils import output_filename, ffmpeg_exe
import unicodedata
import string
"""
1. The initiate_recognizer() function will be called once when the program starts.
2. The handle_transcription() function will be called at the end of every recording.
"""


def remove_punctuation(text):

    # Create a translation table where each punctuation character is mapped to None
    translator = str.maketrans('', '', string.punctuation)
    # Apply the translation to the string
    return text.translate(translator)

def get_text_direction(text):

    rtl_count = 0
    ltr_count = 0

    for char in text:
        if char.isalpha():
            bidirectional = unicodedata.bidirectional(char)
            if bidirectional in ('R', 'AL'):  # Right-to-left characters
                rtl_count += 1
            elif bidirectional in ('L',):    # Left-to-right characters
                ltr_count += 1

    if rtl_count > ltr_count:
        return 'RTL'
    else:
        return 'LTR'

latest_transcription = None

def handle_transcription(whisper_model):
    # Ensure FFmpeg is in PATH
    os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep
    print(f"Using FFmpeg from: {ffmpeg_exe}")
    print(f"Transcribing file: {output_filename}")
    
    # Transcribe the audio file
    transcription = whisper_model.transcribe(output_filename)

    if isinstance(transcription, dict):
        latest_transcription = transcription.get("text", "")
    elif isinstance(transcription, str):
        latest_transcription = transcription
    else:
        raise ValueError(f"Unexpected transcription type: {type(transcription)}")
    
    
    text_direction = get_text_direction(latest_transcription)
    cleaned_text  = remove_punctuation(latest_transcription)
    if "by" in cleaned_text:
        cleaned_text.replace("by", "-")
    if text_direction == 'RTL':
        cleaned_text = cleaned_text[::-1]

    print(f"Transcription (cleaned): {cleaned_text}")
    return cleaned_text
    
    



def initiate_recognizer():
    # Add FFmpeg to PATH
    os.environ["PATH"] = os.path.dirname(ffmpeg_exe) + os.pathsep + os.environ["PATH"]
    
    # Load and return the Whisper model
    whisper_model = whisper.load_model("small.en")
    return whisper_model
