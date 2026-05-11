"""Audio analysis: beat detection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class BeatAnalysis:
    """Result of beat detection."""

    tempo: float
    beats: List[float]
    duration: float
    used_fallback: bool


def detect_beats(
    audio_path: str,
    beat_divider: int = 1,
    fallback_interval: float = 0.5,
    sr: Optional[int] = None,
) -> BeatAnalysis:
    """Detect beats in an audio file.

    Returns the tempo (BPM), beat timestamps in seconds (already filtered
    by beat_divider), and the total audio duration.

    If the algorithm fails to detect a tempo, falls back to evenly spaced
    intervals of length ``fallback_interval`` seconds.
    """
    import librosa

    if beat_divider < 1:
        raise ValueError("beat_divider must be >= 1")

    y, sr = librosa.load(audio_path, sr=sr, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))

    used_fallback = False
    tempo: float = 0.0
    beat_times: List[float] = []

    try:
        tempo_arr, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
        tempo_val = float(np.atleast_1d(tempo_arr)[0])
        if beat_frames is not None and len(beat_frames) >= 2 and tempo_val > 0:
            times = librosa.frames_to_time(beat_frames, sr=sr)
            beat_times = [float(t) for t in times if 0.0 < float(t) < duration]
            tempo = tempo_val
    except Exception:
        beat_times = []

    if len(beat_times) < 2:
        used_fallback = True
        step = max(0.05, float(fallback_interval))
        n = max(1, int(duration / step))
        beat_times = [i * step for i in range(1, n) if i * step < duration]
        tempo = 60.0 / step if step > 0 else 0.0

    if beat_divider > 1:
        beat_times = beat_times[::beat_divider]

    beat_times = sorted(set(beat_times))

    return BeatAnalysis(
        tempo=tempo,
        beats=beat_times,
        duration=duration,
        used_fallback=used_fallback,
    )


def build_intervals(beats: List[float], duration: float) -> List[tuple]:
    """Build (start, end) intervals from 0 -> beats -> duration.

    Filters out zero/negative-length intervals.
    """
    points = [0.0] + [b for b in beats if 0.0 < b < duration] + [float(duration)]
    points = sorted(set(points))
    intervals: List[tuple] = []
    for i in range(len(points) - 1):
        a, b = points[i], points[i + 1]
        if b - a > 1e-3:
            intervals.append((a, b))
    return intervals
