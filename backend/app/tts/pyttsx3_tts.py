"""pyttsx3 backend — works fully offline out of the box (uses the OS TTS
engine / espeak on Linux). This is the practical default for local dev
since it needs no model download, unlike Piper/XTTS.
"""
import io
import tempfile
from pathlib import Path

from app.tts.base import TTSBackend, tone_for_emotion


class Pyttsx3TTS(TTSBackend):
    def synthesize(self, text: str, emotion_state: str = "neutral") -> bytes:
        import pyttsx3

        tone = tone_for_emotion(emotion_state)
        engine = pyttsx3.init()
        engine.setProperty("rate", tone.rate_wpm)
        engine.setProperty("volume", tone.volume)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "oreo_tts.wav"
            engine.save_to_file(text, str(out_path))
            engine.runAndWait()
            return out_path.read_bytes() if out_path.exists() else b""
