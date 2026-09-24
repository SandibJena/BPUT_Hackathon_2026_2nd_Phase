"""
stt/whisper_stt.py — Server-side speech-to-text using faster-whisper.

DESIGN:
- Model loaded lazily on first call, cached as a module-level singleton.
- Supports tiny/base/small models on CPU (int8 quantization) — no GPU needed.
- Falls back gracefully if faster-whisper is unavailable.
- Audio files are processed in-memory where possible; temp files deleted immediately.

SAFETY:
- Audio is processed locally — never sent to any external service.
- Transcription output goes through the same PII masking as text input.
- Transcript is advisory; health worker must verify before submission.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Supported audio MIME types
SUPPORTED_AUDIO_TYPES = {
    "audio/wav", "audio/wave", "audio/x-wav",
    "audio/mp3", "audio/mpeg",
    "audio/webm", "audio/ogg", "audio/mp4",
    "audio/m4a", "audio/flac",
}

# Singleton model cache
_model = None
_model_name: str = ""


def _get_model(model_name: str = "base"):
    """Load and cache the Whisper model (lazy init)."""
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model

    try:
        from faster_whisper import WhisperModel
        log.info(f"Loading faster-whisper model '{model_name}' on CPU (int8)...")
        _model = WhisperModel(model_name, device="cpu", compute_type="int8")
        _model_name = model_name
        log.info(f"faster-whisper model '{model_name}' loaded.")
        return _model
    except ImportError:
        log.error("faster_whisper not installed. Run: pip install faster-whisper")
        raise
    except Exception as e:
        log.error(f"Failed to load Whisper model '{model_name}': {e}")
        raise


def transcribe_audio_bytes(
    audio_bytes: bytes,
    filename: str,
    language: str = "en",
    model_name: str = "base",
) -> dict:
    """
    Transcribe audio bytes using faster-whisper.

    Args:
        audio_bytes: Raw audio file content
        filename:    Original filename (for extension detection)
        language:    ISO language code hint ('en', 'hi', 'or')
        model_name:  Whisper model size ('tiny', 'base', 'small')

    Returns:
        dict with keys:
          - transcript: str (full transcript)
          - language_detected: str
          - duration_seconds: float
          - segments: list of {start, end, text}
          - model_used: str
          - warning: str | None
    """
    if not audio_bytes:
        return _empty_result("Empty audio file received.")

    # Map language codes to Whisper language codes
    lang_map = {"en": "en", "hi": "hi", "or": None, "en-IN": "en", "hi-IN": "hi"}
    whisper_lang = lang_map.get(language, language)

    # Write to a temp file (faster-whisper needs a file path)
    suffix = _get_suffix(filename)
    tmp_path: Optional[Path] = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = Path(tmp.name)

        model = _get_model(model_name)

        # Transcribe — word_timestamps=False for speed
        segments, info = model.transcribe(
            str(tmp_path),
            language=whisper_lang,
            beam_size=3,
            vad_filter=True,        # Remove silence
            vad_parameters={"min_silence_duration_ms": 300},
        )

        seg_list = [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments
        ]
        transcript = " ".join(s["text"] for s in seg_list).strip()

        return {
            "transcript": transcript,
            "language_detected": info.language,
            "language_probability": round(info.language_probability, 3),
            "duration_seconds": round(info.duration, 2),
            "segments": seg_list,
            "model_used": model_name,
            "warning": (
                "Transcription is approximate. Health worker must verify the content."
                if transcript else
                "No speech detected in audio. Please re-record."
            ),
        }

    except ImportError:
        return _empty_result(
            "faster-whisper not available. Use text input or browser voice mode instead."
        )
    except Exception as e:
        log.error(f"Transcription failed: {e}", exc_info=True)
        return _empty_result(f"Transcription error: {type(e).__name__}. Please use text input.")
    finally:
        # Always clean up temp file
        if tmp_path and tmp_path.exists():
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def _get_suffix(filename: str) -> str:
    """Get file extension for temp file."""
    ext = Path(filename).suffix.lower()
    return ext if ext in {".wav", ".mp3", ".webm", ".ogg", ".m4a", ".flac", ".mp4"} else ".wav"


def _empty_result(warning: str) -> dict:
    return {
        "transcript": "",
        "language_detected": "unknown",
        "language_probability": 0.0,
        "duration_seconds": 0.0,
        "segments": [],
        "model_used": "none",
        "warning": warning,
    }


def whisper_available() -> bool:
    """Check if faster-whisper is importable."""
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False
