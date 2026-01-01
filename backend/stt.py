# stt.py
import sounddevice as sd
from scipy.io.wavfile import write
from faster_whisper import WhisperModel
import tempfile
import os

model = WhisperModel(
    "small",
    device="cuda",
    compute_type="int8_float16"
)

def record_and_transcribe(seconds=5):
    fs = 16000
    print("🎤 Listening...")
    audio = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
    sd.wait()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        write(f.name, fs, audio)
        wav_path = f.name

    try:
        text = transcribe_file(wav_path)
    finally:
        try:
            os.unlink(wav_path)
        except Exception:
            pass

    return text


def transcribe_file(path: str) -> str:
    """Transcribe an existing audio file and return a text string.

    This is useful when audio is uploaded from a client (web) or saved to disk.
    """
    segments, _ = model.transcribe(path)
    return " ".join(seg.text for seg in segments).strip()
