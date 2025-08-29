import ffmpeg
import threading
import time
import os
from core.utils import output_filename, ffmpeg_exe, mic_name
from core.recognizer import handle_transcription

# ------------------- Global variables -------------------
is_recording = False
recording_thread = None
process = None


def record_audio():
    """
    Record audio with FFmpeg in a separate thread.
    """
    global process, is_recording

    try:
        print("\nStarting FFmpeg recording...")

        # Build FFmpeg command with simple audio input
        stream = (
            ffmpeg
            .input(f'audio={mic_name}', f='dshow')
            .output(output_filename, acodec='flac', ar='16000', ac='1')
            .overwrite_output()
        )

        # Print command for debugging
        args = stream.get_args()
        print("FFmpeg command:", ' '.join(args))

        # Start FFmpeg process
        process = stream.run_async(
            cmd=ffmpeg_exe,
            pipe_stdin=True,
            pipe_stdout=True,
            pipe_stderr=True
        )

        # Verify process started
        if not process or process.poll() is not None:
            raise Exception("Failed to start FFmpeg process")

        print("FFmpeg process started with PID:", process.pid)

        # Timer loop with proper state checking
        seconds = 0
        while is_recording:
            if process.poll() is not None:  # Process terminated unexpectedly
                error = process.stderr.read().decode() if process.stderr else "Unknown error"
                raise Exception(f"FFmpeg process terminated unexpectedly: {error}")

            print(f"Recording audio... {seconds}s", end='\r', flush=True)
            seconds += 1
            time.sleep(1)

    except Exception as e:
        print(f"\nError during recording: {str(e)}")
        is_recording = False
        if process and process.stderr:
            error = process.stderr.read().decode()
            print(f"FFmpeg error: {error}")


def toggle_recording(whisper_model):
    """
    Toggle recording state and handle file processing.
    """
    global is_recording, recording_thread, process

    if is_recording:
        print("\nStopping recording...")
        is_recording = False

        if process:
            process.terminate()
            process.wait(timeout=2.0)
            process = None

        if recording_thread:
            recording_thread.join(timeout=2.0)
            recording_thread = None

        time.sleep(1.0)  # Allow time for file writing

        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 0:
            print(f"Recording saved ({os.path.getsize(output_filename)} bytes)")

            try:
                transcription = handle_transcription(whisper_model)
                print(f"Transcription: {transcription['text']}")
            except Exception as e:
                print(f"Error during transcription: {str(e)}")
        else:
            print("No recording file created")

    else:
        print("\nStarting new recording...")
        is_recording = True
        recording_thread = threading.Thread(target=record_audio, daemon=True)
        recording_thread.start()
