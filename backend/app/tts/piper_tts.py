"""Piper (Coqui XTTS alternative, lighter weight) backend.

Requires a downloaded .onnx voice model — see PIPER_MODEL_PATH in
.env.example and https://github.com/rhasspy/piper for voice downloads.
Not exercised in CI/tests since it needs that model file on disk.
"""
import tempfile
from pathlib import Path

from app.config import get_settings
from app.tts.base import TTSBackend, tone_for_emotion


class PiperTTS(TTSBackend):
    def __init__(self, model_path: str | None = None):
        settings = get_settings()
        self.model_path = model_path or settings.piper_model_path

    def synthesize(self, text: str, emotion_state: str = "neutral") -> bytes:
        from piper.voice import PiperVoice

        if not Path(self.model_path).exists():
            raise FileNotFoundError(
                f"Piper voice model not found at {self.model_path}. "
                "Download one from https://github.com/rhasspy/piper/releases and set PIPER_MODEL_PATH."
            )

        tone = tone_for_emotion(emotion_state)
        # Piper's length_scale is inversely proportional to speaking rate.
        length_scale = 175 / max(tone.rate_wpm, 1)

        voice = PiperVoice.load(self.model_path)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_path = Path(tmp_dir) / "oreo_tts.wav"
            with open(out_path, "wb") as f:
                voice.synthesize(text, f, length_scale=length_scale)
            return out_path.read_bytes()
