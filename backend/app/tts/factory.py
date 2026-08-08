from app.config import get_settings
from app.tts.base import TTSBackend

_default_backend: TTSBackend | None = None


def get_tts_backend() -> TTSBackend:
    global _default_backend
    if _default_backend is None:
        settings = get_settings()
        if settings.tts_backend == "piper":
            from app.tts.piper_tts import PiperTTS

            _default_backend = PiperTTS()
        else:
            from app.tts.pyttsx3_tts import Pyttsx3TTS

            _default_backend = Pyttsx3TTS()
    return _default_backend
