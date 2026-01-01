# voice.py
# Lightweight STT helper with graceful fallback to text input

def record_and_transcribe(timeout_seconds=6):
    """Attempt to record from the default microphone and transcribe.
    Falls back to typed input on failure.
    """
    try:
        import speech_recognition as sr
    except Exception as e:
        print("DEBUG | speech_recognition not available, falling back to typed input:", e)
        return input("You (type): ")

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("(listening...)")
            audio = r.listen(source, timeout=timeout_seconds)
        text = r.recognize_google(audio)
        return text
    except Exception as e:
        print("DEBUG | voice capture/transcription failed:", e)
        return input("You (type): ")