from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

# Import backend logic lazily to avoid importing optional audio / desktop deps at module-import time
# We'll import when the first request arrives so the server can start for simple text-only usage.
handle_query = None
process_input = None

app = FastAPI(title="VerySleepy AI API")

# Allow all origins for Replit environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryPayload(BaseModel):
    input: str
    mode: Optional[str] = None
    source: Optional[str] = "text"  # allowed values: 'text' or 'voice'


# --- STT upload endpoint --------------------------------------------------
from fastapi import File, UploadFile


@app.post("/stt")
async def stt_upload(file: UploadFile = File(...)):
    """Accept an audio upload (webm/ogg/wav/etc) and return a transcript."""
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    try:
        import tempfile
        import shutil

        suffix = os.path.splitext(file.filename)[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            temp_path = f.name
            # Write uploaded bytes
            shutil.copyfileobj(file.file, f)

        # Lazy import stt and use its transcribe_file helper
        try:
            from stt import transcribe_file
        except Exception:
            raise HTTPException(status_code=500, detail="STT not available on server")

        text = transcribe_file(temp_path)
        try:
            os.unlink(temp_path)
        except Exception:
            pass

        # Check if the transcript contains an explicit memory command (for UI confirmation)
        triggers = [
            "remember this",
            "remember that",
            "save this",
            "from now on remember",
            "always remember",
        ]
        t = text.lower() if text else ""
        contains_memory_command = any(k in t for k in triggers)

        # Check if content is disallowed for long-term memory
        try:
            from memory import is_disallowed_memory_content
            disallowed = is_disallowed_memory_content(text)
        except Exception:
            disallowed = None

        return {"transcript": text, "contains_memory_command": contains_memory_command, "disallowed_memory_reason": disallowed}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- TTS playback control -------------------------------------------------
from uuid import uuid4

_playback_registry = {}


class SpeakPayload(BaseModel):
    text: str
    voice: Optional[str] = "en_US-lessac"
    volume: Optional[float] = 1.0


@app.post("/speak")
async def speak_endpoint(payload: SpeakPayload):
    """Trigger server-side TTS playback and return an id for controlling it."""
    if not payload.text or not payload.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")

    # Lazy import tts.speak
    try:
        from tts import speak as _speak
    except Exception:
        raise HTTPException(status_code=500, detail="TTS not available on server")

    try:
        controller = _speak(payload.text, payload.voice)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS generation/playback error: {e}")

    play_id = None
    if controller is not None:
        play_id = str(uuid4())
        _playback_registry[play_id] = controller

    return {"id": play_id, "status": "playing"}


@app.post("/speak/{play_id}/stop")
async def stop_speak(play_id: str):
    controller = _playback_registry.get(play_id)
    if not controller:
        return {"status": "not_found"}
    try:
        controller.stop()
    except Exception:
        pass
    try:
        del _playback_registry[play_id]
    except Exception:
        pass
    return {"status": "stopped"}


@app.get("/speak/{play_id}")
async def get_playback(play_id: str):
    controller = _playback_registry.get(play_id)
    if not controller:
        return {"status": "not_found"}
    return {"status": "playing"}

# --- Memory & Prefs endpoints -------------------------------------------
class PrefPayload(BaseModel):
    key: str
    value: str


@app.post("/prefs")
async def set_pref_endpoint(payload: PrefPayload):
    try:
        from memory import set_pref
    except Exception:
        raise HTTPException(status_code=500, detail="Memory service unavailable")

    try:
        set_pref(payload.key, payload.value)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RememberPayload(BaseModel):
    content: str
    source: Optional[str] = "explicit"


@app.post("/memory/remember")
async def remember(payload: RememberPayload):
    if not payload.content or not payload.content.strip():
        raise HTTPException(status_code=400, detail="Content required")

    try:
        from memory import is_disallowed_memory_content, add_long_term
        disallowed = is_disallowed_memory_content(payload.content)
        if disallowed:
            raise HTTPException(status_code=400, detail=f"Content not allowed for long-term memory: {disallowed}")
        add_long_term(payload.content, source=payload.source)
        return {"status": "remembered"}
    except HTTPException:
        raise
    except Exception as e:
        # If memory.add_long_term raises ValueError for disallowed content, map to 400
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/clear")
async def clear_memory():
    try:
        from memory import clear_all_memory
        clear_all_memory()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory")
async def get_memory():
    try:
        from memory import get_long_term, get_context
        long_term = get_long_term()
        short_term = get_context()
        return {"long_term": long_term, "short_term": short_term}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/snapshot")
async def get_memory_snapshot_endpoint():
    try:
        from memory import get_memory_snapshot
        return get_memory_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/prefs")
async def get_prefs():
    try:
        from memory import get_prefs
    except Exception:
        raise HTTPException(status_code=500, detail="Memory service unavailable")
    try:
        return get_prefs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/{entry_id}")
async def delete_memory(entry_id: int):
    try:
        from memory import delete_long_term
    except Exception:
        raise HTTPException(status_code=500, detail="Memory service unavailable")
    try:
        delete_long_term(entry_id)
        return {"status": "deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
def query(payload: QueryPayload):
    if not payload.input or not payload.input.strip():
        raise HTTPException(status_code=400, detail="Input is required")
    try:
        # Lazy import the core logic to avoid pulling in optional audio / OS-specific
        # packages during module import (which can crash the server on systems
        # without audio libs when only text-based API is desired).
        global handle_query, process_input
        if handle_query is None or process_input is None:
            # Import using package-relative name so imports work whether the server is
            # run from the project root or as the `backend` package under uvicorn.
            try:
                from .main import handle_query as _handle_query, process_input as _process_input
            except Exception:
                from backend.main import handle_query as _handle_query, process_input as _process_input
            handle_query = _handle_query
            process_input = _process_input

        # Respect the source (voice vs text) to avoid auto-saving voice memory
        src = payload.source or "text"
        if payload.mode:
            # process_input handles mode; pass source along by setting global or via wrapper
            resp = process_input(payload.input, payload.mode, source=src)
        else:
            resp = handle_query(payload.input, source=src)
        return {"response": resp}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.api:app", host="0.0.0.0", port=8000, reload=True)
