"""Prosody feature extraction (pitch, pace, jitter) feeding the emotion classifier.

This is intentionally simple signal processing, not a trained model — good
enough to distinguish "flat/calm" from "loud/fast/erratic" speech. Swapping
in a proper prosody model (e.g. openSMILE, a wav2vec2-based extractor) is a
documented future step; see app/stt/emotion.py.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class ProsodyFeatures:
    pitch_mean_hz: float
    pitch_std_hz: float
    jitter: float  # relative cycle-to-cycle pitch perturbation, 0=perfectly stable
    pace_wpm: float | None  # words per minute, filled in by the caller once text is known
    energy_rms: float


def extract_prosody(audio_path: str, transcript_word_count: int | None = None) -> ProsodyFeatures:
    """Extract prosody features from an audio file on disk.

    Imports librosa lazily so importing this module stays cheap.
    """
    import librosa

    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration_s = max(len(y) / sr, 1e-6)

    f0, voiced_flag, _ = librosa.pyin(
        y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"), sr=sr
    )
    voiced_f0 = f0[voiced_flag] if voiced_flag is not None else np.array([])
    voiced_f0 = voiced_f0[~np.isnan(voiced_f0)] if voiced_f0.size else voiced_f0

    if voiced_f0.size >= 2:
        pitch_mean = float(np.mean(voiced_f0))
        pitch_std = float(np.std(voiced_f0))
        cycle_diffs = np.abs(np.diff(voiced_f0))
        jitter = float(np.mean(cycle_diffs) / pitch_mean) if pitch_mean > 0 else 0.0
    elif voiced_f0.size == 1:
        pitch_mean, pitch_std, jitter = float(voiced_f0[0]), 0.0, 0.0
    else:
        pitch_mean, pitch_std, jitter = 0.0, 0.0, 0.0

    energy_rms = float(np.sqrt(np.mean(y**2))) if y.size else 0.0

    pace_wpm = None
    if transcript_word_count is not None and duration_s > 0:
        pace_wpm = transcript_word_count / (duration_s / 60.0)

    return ProsodyFeatures(
        pitch_mean_hz=pitch_mean,
        pitch_std_hz=pitch_std,
        jitter=jitter,
        pace_wpm=pace_wpm,
        energy_rms=energy_rms,
    )
