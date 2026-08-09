"""Faster-Whisper based transcription (section 3.2).

The model is lazy-loaded on first use so importing this module (e.g. during
test collection) never triggers a multi-GB download. Model size is
configurable via WHISPER_MODEL_SIZE; the shipped default ("small") is
practical to run on a laptop CPU. Swap in "large-v3-turbo" via env var for
production-quality transcription once you have the hardware for it.
"""
from dataclasses import dataclass
from typing import Protocol

from app.config import get_settings
from app.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class TranscriptionResult:
    text: str
    language: str
    duration_seconds: float
    segments: list[dict]


class SupportsTranscribe(Protocol):
    def transcribe(self, audio_path: str) -> TranscriptionResult: ...


class WhisperTranscriber:
    """Thin wrapper around faster_whisper.WhisperModel with lazy init."""

    def __init__(self, model_size: str | None = None, device: str | None = None, compute_type: str | None = None):
        settings = get_settings()
        self.model_size = model_size or settings.whisper_model_size
        self.device = device or settings.whisper_device
        self.compute_type = compute_type or settings.whisper_compute_type
        self._model = None

    def _get_model(self):
        if self._model is None:
            # Imported here (not at module top) so the heavy dependency only
            # loads when transcription actually happens.
            from faster_whisper import WhisperModel

            logger.info("whisper_model_loading", size=self.model_size, device=self.device)
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
            logger.info("whisper_model_loaded", size=self.model_size)
        return self._model

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        model = self._get_model()
        segments_iter, info = model.transcribe(audio_path, beam_size=5)
        segments = [
            {"start": s.start, "end": s.end, "text": s.text}
            for s in segments_iter
        ]
        text = " ".join(s["text"].strip() for s in segments).strip()
        return TranscriptionResult(
            text=text,
            language=info.language,
            duration_seconds=info.duration,
            segments=segments,
        )


_default_transcriber: WhisperTranscriber | None = None


def get_transcriber() -> WhisperTranscriber:
    global _default_transcriber
    if _default_transcriber is None:
        _default_transcriber = WhisperTranscriber()
    return _default_transcriber
