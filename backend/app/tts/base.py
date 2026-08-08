"""TTS backend interface + emotion-to-tone mapping (section 3.6)."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ToneParams:
    """Backend-agnostic knobs; each backend maps these onto its own controls."""

    rate_wpm: int = 175  # words per minute
    pitch_semitones: float = 0.0  # relative pitch shift
    volume: float = 1.0  # 0..1


# Emotion state -> tone adjustment. Deliberately simple; the point is that
# the detected state (app/stt/emotion.py) actually changes how Oreo sounds.
EMOTION_TONE_MAP: dict[str, ToneParams] = {
    "neutral": ToneParams(rate_wpm=175, pitch_semitones=0.0, volume=1.0),
    "urgent": ToneParams(rate_wpm=195, pitch_semitones=0.5, volume=1.0),
    "frustrated": ToneParams(rate_wpm=160, pitch_semitones=-1.0, volume=0.9),
    "happy": ToneParams(rate_wpm=180, pitch_semitones=1.5, volume=1.0),
    "sad": ToneParams(rate_wpm=150, pitch_semitones=-1.5, volume=0.85),
}


def tone_for_emotion(emotion_state: str) -> ToneParams:
    return EMOTION_TONE_MAP.get(emotion_state, EMOTION_TONE_MAP["neutral"])


class TTSBackend(ABC):
    @abstractmethod
    def synthesize(self, text: str, emotion_state: str = "neutral") -> bytes:
        """Return WAV audio bytes for `text`, tone-adjusted for `emotion_state`."""
        raise NotImplementedError
