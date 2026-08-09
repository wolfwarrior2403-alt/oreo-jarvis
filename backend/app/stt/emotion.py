"""Emotion / state classification (section 3.3).

Rule-based on purpose: combines prosody (pitch, pace, energy, jitter) with a
small lexicon of urgency/frustration cue words in the transcript. This is a
deliberately simple baseline — swapping in a trained classifier (e.g. a
fine-tuned wav2vec2 or a text+audio fusion model) is a documented future
step; the call signature here (`classify_state`) is the seam to swap it
behind.
"""
from dataclasses import dataclass

from app.stt.prosody import ProsodyFeatures

STATE_NEUTRAL = "neutral"
STATE_URGENT = "urgent"
STATE_FRUSTRATED = "frustrated"
STATE_HAPPY = "happy"
STATE_SAD = "sad"

_FRUSTRATION_WORDS = {
    "ugh", "annoying", "frustrated", "frustrating", "stupid", "broken",
    "why won't", "hate", "seriously", "come on",
}
_URGENCY_WORDS = {
    "now", "immediately", "asap", "urgent", "emergency", "hurry", "quick", "quickly",
}
_POSITIVE_WORDS = {
    "great", "awesome", "thanks", "thank you", "nice", "love", "perfect", "cool",
}
_SAD_WORDS = {
    "sad", "tired", "exhausted", "sorry", "down", "upset",
}


@dataclass
class EmotionResult:
    state: str
    confidence: float
    signals: dict


def _lexicon_hits(transcript: str, words: set[str]) -> int:
    lowered = transcript.lower()
    return sum(1 for w in words if w in lowered)


def classify_state(transcript: str, prosody: ProsodyFeatures) -> EmotionResult:
    frustration_hits = _lexicon_hits(transcript, _FRUSTRATION_WORDS)
    urgency_hits = _lexicon_hits(transcript, _URGENCY_WORDS)
    positive_hits = _lexicon_hits(transcript, _POSITIVE_WORDS)
    sad_hits = _lexicon_hits(transcript, _SAD_WORDS)

    # Fast/loud/pitchy speech nudges toward urgent or frustrated.
    is_fast = bool(prosody.pace_wpm and prosody.pace_wpm > 170)
    is_loud = prosody.energy_rms > 0.08
    is_erratic = prosody.jitter > 0.05

    scores = {
        STATE_FRUSTRATED: frustration_hits * 2 + (1 if is_erratic else 0) + (1 if is_loud else 0),
        STATE_URGENT: urgency_hits * 2 + (1 if is_fast else 0),
        STATE_HAPPY: positive_hits * 2,
        STATE_SAD: sad_hits * 2 + (1 if prosody.energy_rms < 0.02 and prosody.pitch_std_hz < 5 else 0),
    }

    best_state = max(scores, key=scores.get)
    best_score = scores[best_state]

    if best_score <= 0:
        return EmotionResult(
            state=STATE_NEUTRAL,
            confidence=0.5,
            signals={"scores": scores, "prosody": prosody.__dict__},
        )

    confidence = min(0.5 + 0.1 * best_score, 0.95)
    return EmotionResult(state=best_state, confidence=confidence, signals={"scores": scores, "prosody": prosody.__dict__})
