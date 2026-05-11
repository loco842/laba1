"""Configuration dataclass for BeatVideoCutter."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Tuple


SUPPORTED_VIDEO_EXTS: Tuple[str, ...] = (
    ".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v", ".flv", ".wmv",
)
SUPPORTED_AUDIO_EXTS: Tuple[str, ...] = (
    ".wav", ".mp3", ".aac", ".flac", ".ogg", ".m4a",
)


@dataclass
class Config:
    """All user-configurable parameters of the editor."""

    video_input_dir: str = ""
    audio_file: str = ""
    output_file: str = "output.mp4"

    clip_duration: float = 2.0
    beat_divider: int = 1
    min_clip_remains: float = 0.5

    output_width: Optional[int] = None
    output_height: Optional[int] = None
    output_fps: int = 30

    keep_original_audio: bool = False
    audio_mix_ratio: float = 0.2

    codec_video: str = "libx264"
    codec_audio: str = "aac"
    preset: str = "medium"
    bitrate: Optional[str] = None

    length_fit_mode: str = "loop"

    fallback_interval: float = 0.5

    random_seed: Optional[int] = None

    extra: dict = field(default_factory=dict)

    def validate(self) -> None:
        if not self.video_input_dir:
            raise ValueError("video_input_dir is required")
        if not Path(self.video_input_dir).is_dir():
            raise ValueError(f"video_input_dir does not exist or is not a directory: {self.video_input_dir}")
        if not self.audio_file:
            raise ValueError("audio_file is required")
        if not Path(self.audio_file).is_file():
            raise ValueError(f"audio_file does not exist: {self.audio_file}")
        if not self.output_file:
            raise ValueError("output_file is required")
        if self.clip_duration <= 0:
            raise ValueError("clip_duration must be > 0")
        if self.beat_divider < 1:
            raise ValueError("beat_divider must be >= 1")
        if self.min_clip_remains < 0:
            raise ValueError("min_clip_remains must be >= 0")
        if self.output_fps <= 0:
            raise ValueError("output_fps must be > 0")
        if self.length_fit_mode not in ("loop", "speed", "trim"):
            raise ValueError("length_fit_mode must be one of: loop, speed, trim")
        if self.output_width is not None and self.output_width <= 0:
            raise ValueError("output_width must be > 0")
        if self.output_height is not None and self.output_height <= 0:
            raise ValueError("output_height must be > 0")
