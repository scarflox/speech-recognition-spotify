import core.recognizer, core.service, keyboard


def main():
    whisper_model = core.recognizer.initiate_recognizer()
    

    keyboard.add_hotkey('ctrl+alt+k', lambda: core.service.toggle_recording(whisper_model))
    print("Press Ctrl+Alt+K to start/stop recording.")
    print("Press Ctrl+C in terminal to quit.")

    keyboard.wait()



if __name__ == '__main__':
    main()