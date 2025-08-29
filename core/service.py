# core/service.py
import ffmpeg
import threading
import time
import os
from core.utils import output_filename, ffmpeg_exe, mic_name
from core.recognizer import handle_transcription
import subprocess

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
        # Choose how to send the device to ffmpeg:
        # - If mic_name starts with @device use it directly (no quotes)
        # - Otherwise quote it to handle spaces and parentheses
        if str(mic_name).startswith('@device'):
            input_device = f'audio={mic_name}'
        else:
            # IMPORTANT: include quotes around the friendly name for dshow
            input_device = f'audio="{mic_name}"'

        # Build FFmpeg command
        stream = (
            ffmpeg
            .input(input_device, f='dshow')
            .output(output_filename, acodec='flac', ar='16000', ac=1)
            .overwrite_output()
            .global_args('-loglevel', 'debug')  # set to 'info' if too verbose
        )

        # Print command for debugging (exact args passed to ffmpeg)
        args = stream.get_args()
        # ffmpeg-python may produce args like ['-f', 'dshow', '-i', 'audio="Mic Name"', ...]
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
                # read stderr non-blocking: read whatever is available
                try:
                    err = process.stderr.read().decode() if process.stderr else "Unknown error"
                except Exception:
                    err = "Could not read stderr"
                raise Exception(f"FFmpeg process terminated unexpectedly: {err}")

            print(f"Recording audio... {seconds}s", end='\r', flush=True)
            seconds += 1
            time.sleep(1)

    except Exception as e:
        print(f"\nError during recording: {str(e)}")
        is_recording = False
        if process and process.stderr:
            try:
                error = process.stderr.read().decode()
                print(f"FFmpeg error: {error}")
            except Exception:
                pass


def toggle_recording(whisper_model):
    """
    Toggle recording state and handle file processing.
    Stops FFmpeg gracefully by sending 'q' to stdin, then falls back to terminate().
    """
    global is_recording, recording_thread, process

    if is_recording:
        print("\nStopping recording...")
        is_recording = False

        if process:
            try:
                # 1) Try graceful stop: send 'q' to ffmpeg stdin and wait
                if process.stdin:
                    try:
                        process.stdin.write(b'q')
                        process.stdin.flush()
                    except Exception:
                        # some Popen objects close stdin automatically; ignore
                        pass

                # Wait a short while for ffmpeg to finish normally
                try:
                    stdout, stderr = process.communicate(timeout=4)
                except Exception:
                    # If it doesn't exit in time, fall back to terminate
                    print("FFmpeg didn't exit after 'q' — terminating.")
                    try:
                        process.terminate()
                    except Exception:
                        pass
                    try:
                        stdout, stderr = process.communicate(timeout=3)
                    except Exception:
                        stdout, stderr = (b'', b'Could not collect output after terminate.')

                # Ensure process is cleaned up
                if process.poll() is None:
                    try:
                        process.kill()
                    except Exception:
                        pass

            except Exception as e:
                print(f"Error while stopping FFmpeg: {e}")
            finally:
                # Read/print stderr (helpful diagnostics)
                try:
                    if stderr:
                        print("FFmpeg stderr (on stop):")
                        print(stderr.decode(errors='ignore'))
                    else:
                        # try reading from process.stderr if still present
                        if process and process.stderr:
                            try:
                                tail = process.stderr.read().decode(errors='ignore')
                                if tail:
                                    print("FFmpeg stderr (tail):")
                                    print(tail)
                            except Exception:
                                pass
                except Exception:
                    pass

                process = None

        if recording_thread:
            recording_thread.join(timeout=2.0)
            recording_thread = None

        # small wait to let file system flush
        time.sleep(0.5)

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
