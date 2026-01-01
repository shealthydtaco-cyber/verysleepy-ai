import subprocess
import tempfile
import os


def _generate_wav(text: str, voice_model: str) -> str:
    """Generate TTS via piper into a temp WAV and return the path."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
        out = f.name

    try:
        subprocess.run(
            [
                "piper",
                "--model", f"voices/{voice_model}",
                "--output_file", out
            ],
            input=text.encode("utf-8"),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except Exception as e:
        # If piper isn't available or fails, ensure we clean up and raise
        try:
            os.remove(out)
        except Exception:
            pass
        raise

    return out


def play_audio(wav_path: str):
    """Fallback synchronous player using sounddevice/soundfile (lazy import)."""
    try:
        import soundfile as sf
        import sounddevice as sd
    except Exception as e:
        print("DEBUG | play_audio unavailable (missing deps):", e)
        return

    data, samplerate = sf.read(wav_path, dtype="float32")
    sd.play(data, samplerate)
    sd.wait()


def speak(text: str, voice_model: str):
    """Generate TTS wav then play it inside the app if possible, otherwise fallback.

    Uses `audio_player.play_wav_in_app` when available (non-blocking). If that's not
    available, falls back to a synchronous `play_audio` implementation.
    The WAV file is removed after playback (or immediately on failure).
    """
    try:
        wav = _generate_wav(text, voice_model)
    except Exception as e:
        print("DEBUG | TTS generation failed:", e)
        return

    # Try to use the in-app async player if present
    try:
        from audio_player import play_wav_in_app

        try:
            controller = play_wav_in_app(
                wav,
                on_done=lambda: os.remove(wav) if os.path.exists(wav) else None,
                volume=1.0,
            )
            # Return controller so callers can stop playback if needed
            return controller
        except Exception as e:
            print("DEBUG | play_wav_in_app failed, falling back:", e)
            try:
                play_audio(wav)
            except Exception as e2:
                print("DEBUG | fallback play_audio failed:", e2)
            finally:
                try:
                    os.remove(wav)
                except Exception:
                    pass
    except Exception:
        # audio_player is not available — do a synchronous play as a fallback
        try:
            play_audio(wav)
        except Exception as e:
            print("DEBUG | play_audio failed:", e)
        finally:
            try:
                os.remove(wav)
            except Exception:
                pass

    return None
