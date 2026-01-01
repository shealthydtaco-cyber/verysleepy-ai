import sounddevice as sd
import soundfile as sf
import threading

# Single global controller to manage/interrupt current playback
_current_controller = None
_current_lock = threading.Lock()

class PlaybackController:
    """Controller handle returned by `play_wav_in_app`.

    Call `.stop()` to interrupt playback immediately (calls `sd.stop()`).
    """

    def __init__(self):
        self._stopped = False

    def stop(self):
        try:
            sd.stop()
        finally:
            self._stopped = True

    @property
    def stopped(self):
        return self._stopped


def play_wav_in_app(wav_path, on_done=None, volume: float = 1.0):
    """
    Plays WAV audio directly in-app (no external player).
    Non-blocking. Returns a `PlaybackController` that can be used to interrupt playback.

    Parameters:
    - wav_path: path to wav file
    - on_done: optional callable invoked when playback finishes or is stopped
    - volume: float 0.0-1.0 to scale playback amplitude
    """

    def _play(controller: PlaybackController):
        try:
            data, samplerate = sf.read(wav_path, dtype="float32")

            # Apply volume scaling if needed (try numpy for performance, fallback otherwise)
            if volume != 1.0:
                try:
                    import numpy as _np
                    data = data * float(volume)
                    data = _np.clip(data, -1.0, 1.0)
                except Exception:
                    # Fallback: elementwise scaling (slower)
                    try:
                        data = (data * float(volume)).tolist()
                    except Exception:
                        pass

            if controller.stopped:
                return

            sd.play(data, samplerate)
            sd.wait()
        finally:
            try:
                if on_done:
                    on_done()
            except Exception:
                pass
            # Clear global controller when finished
            with _current_lock:
                global _current_controller
                if _current_controller is controller:
                    _current_controller = None

    controller = PlaybackController()

    # Stop any existing playback and replace with this controller
    with _current_lock:
        global _current_controller
        if _current_controller:
            try:
                _current_controller.stop()
            except Exception:
                pass
        _current_controller = controller

    threading.Thread(target=_play, args=(controller,), daemon=True).start()
    return controller


def stop_all():
    """Stop any active playback immediately."""
    with _current_lock:
        global _current_controller
        if _current_controller:
            try:
                _current_controller.stop()
            except Exception:
                pass
            _current_controller = None
