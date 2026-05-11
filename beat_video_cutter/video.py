"""Video discovery and clip pool construction."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from .config import SUPPORTED_VIDEO_EXTS


@dataclass
class ClipRef:
    """Reference to a continuous fragment of a source video file."""

    source_path: str
    start: float
    end: float
    width: int
    height: int
    fps: float

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def find_videos(directory: str) -> List[Path]:
    """Return all video files in ``directory`` (non-recursive) sorted by name."""
    p = Path(directory)
    if not p.is_dir():
        return []
    files = [
        f for f in p.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_VIDEO_EXTS
    ]
    return sorted(files)


def build_clip_pool(
    directory: str,
    clip_duration: float = 2.0,
    min_clip_remains: float = 0.5,
    log: Optional[Callable[[str], None]] = None,
) -> Tuple[List[ClipRef], List[Tuple[int, int, float]]]:
    """Scan a directory of videos and produce a pool of short clip references.

    Returns (pool, source_specs) where source_specs is a list of
    (width, height, fps) for each successfully opened source — handy for
    deciding on the output resolution / fps.
    """
    from moviepy.editor import VideoFileClip

    if log is None:
        log = lambda _msg: None

    files = find_videos(directory)
    if not files:
        return [], []

    pool: List[ClipRef] = []
    specs: List[Tuple[int, int, float]] = []

    for f in files:
        try:
            with VideoFileClip(str(f)) as vc:
                dur = float(vc.duration or 0.0)
                w, h = int(vc.w), int(vc.h)
                fps = float(vc.fps or 30.0)
            if dur <= 0 or w <= 0 or h <= 0:
                log(f"[skip] {f.name}: invalid metadata")
                continue
            specs.append((w, h, fps))

            t = 0.0
            while t + clip_duration <= dur + 1e-6:
                pool.append(ClipRef(
                    source_path=str(f),
                    start=t,
                    end=t + clip_duration,
                    width=w,
                    height=h,
                    fps=fps,
                ))
                t += clip_duration

            remainder = dur - t
            if remainder >= max(0.0, min_clip_remains):
                pool.append(ClipRef(
                    source_path=str(f),
                    start=t,
                    end=dur,
                    width=w,
                    height=h,
                    fps=fps,
                ))
            log(f"[ok] {f.name}: {dur:.2f}s -> {sum(1 for c in pool if c.source_path == str(f))} clips")
        except Exception as e:
            log(f"[skip] {f.name}: {e}")
            continue

    return pool, specs
