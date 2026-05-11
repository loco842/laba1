"""Beat-synced editing and final video export."""

from __future__ import annotations

import math
import os
import random
import tempfile
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from .audio import BeatAnalysis, build_intervals, detect_beats
from .config import Config
from .video import ClipRef, build_clip_pool


ProgressCb = Callable[[float, str], None]


@dataclass
class EditResult:
    output_path: str
    duration: float
    n_segments: int
    tempo: float
    used_fallback_beats: bool


def _safe_log(progress: Optional[ProgressCb], pct: float, msg: str) -> None:
    if progress is not None:
        try:
            progress(pct, msg)
        except Exception:
            pass


def _decide_target_resolution(
    cfg: Config, specs: List[Tuple[int, int, float]]
) -> Tuple[int, int]:
    if cfg.output_width and cfg.output_height:
        return int(cfg.output_width), int(cfg.output_height)
    if not specs:
        return 1280, 720
    max_area = max(specs, key=lambda s: s[0] * s[1])
    w, h = int(max_area[0]), int(max_area[1])
    w -= w % 2
    h -= h % 2
    return w, h


def _fit_clip_to_duration(clip, target_duration: float, mode: str):
    """Adapt clip's duration to ``target_duration`` using the selected mode."""
    from moviepy.editor import concatenate_videoclips
    from moviepy.video.fx.all import speedx

    src_dur = float(clip.duration or 0.0)
    if src_dur <= 0 or target_duration <= 0:
        return clip

    if abs(src_dur - target_duration) < 1e-3:
        return clip

    if src_dur > target_duration:
        return clip.subclip(0, target_duration)

    if mode == "speed":
        factor = src_dur / target_duration
        factor = max(0.1, factor)
        try:
            new_clip = speedx(clip, factor=factor)
            if new_clip.duration > target_duration:
                new_clip = new_clip.subclip(0, target_duration)
            return new_clip
        except Exception:
            mode = "loop"

    if mode == "trim":
        return clip

    repeats = int(math.ceil(target_duration / src_dur))
    pieces = []
    remaining = target_duration
    for _ in range(repeats):
        if remaining <= 0:
            break
        if remaining >= src_dur:
            pieces.append(clip.copy())
            remaining -= src_dur
        else:
            pieces.append(clip.subclip(0, remaining))
            remaining = 0
    if not pieces:
        return clip
    if len(pieces) == 1:
        return pieces[0]
    return concatenate_videoclips(pieces, method="compose")


def _prepare_segment(clip, target_w: int, target_h: int, target_fps: int):
    """Resize+pad and set fps for uniform composition."""
    from moviepy.editor import CompositeVideoClip, ColorClip

    src_w, src_h = clip.w, clip.h
    if src_w == target_w and src_h == target_h:
        return clip.set_fps(target_fps)

    scale = min(target_w / src_w, target_h / src_h)
    new_w = max(2, int(round(src_w * scale)))
    new_h = max(2, int(round(src_h * scale)))
    new_w -= new_w % 2
    new_h -= new_h % 2

    resized = clip.resize(newsize=(new_w, new_h))
    if new_w == target_w and new_h == target_h:
        return resized.set_fps(target_fps)

    bg = ColorClip(size=(target_w, target_h), color=(0, 0, 0), duration=resized.duration)
    centered = resized.set_position(("center", "center"))
    composed = CompositeVideoClip([bg, centered], size=(target_w, target_h))
    composed = composed.set_duration(resized.duration).set_fps(target_fps)
    return composed


def run_edit(
    cfg: Config,
    progress: Optional[ProgressCb] = None,
    cancel_check: Optional[Callable[[], bool]] = None,
) -> EditResult:
    """End-to-end pipeline: analyze audio, build clip pool, edit, export."""

    cfg.validate()

    if cfg.random_seed is not None:
        random.seed(cfg.random_seed)

    from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoFileClip, concatenate_videoclips

    def _check_cancel():
        if cancel_check is not None and cancel_check():
            raise RuntimeError("Operation cancelled by user")

    _safe_log(progress, 0.01, "Analyzing audio…")
    _check_cancel()
    analysis: BeatAnalysis = detect_beats(
        cfg.audio_file,
        beat_divider=cfg.beat_divider,
        fallback_interval=cfg.fallback_interval,
    )
    _safe_log(
        progress, 0.1,
        f"Tempo {analysis.tempo:.1f} BPM, {len(analysis.beats)} beats"
        + (" (fallback)" if analysis.used_fallback else ""),
    )

    intervals = build_intervals(analysis.beats, analysis.duration)
    if not intervals:
        intervals = [(0.0, analysis.duration)]
    _safe_log(progress, 0.12, f"{len(intervals)} intervals to fill")

    _safe_log(progress, 0.15, "Scanning videos and building clip pool…")
    _check_cancel()
    pool: List[ClipRef]
    specs: List[Tuple[int, int, float]]
    pool, specs = build_clip_pool(
        directory=cfg.video_input_dir,
        clip_duration=cfg.clip_duration,
        min_clip_remains=cfg.min_clip_remains,
        log=lambda m: _safe_log(progress, 0.17, m),
    )
    if not pool:
        raise RuntimeError(
            "Clip pool is empty: no readable video files in the input directory."
        )
    _safe_log(progress, 0.25, f"Clip pool size: {len(pool)} fragments")

    target_w, target_h = _decide_target_resolution(cfg, specs)
    target_fps = int(cfg.output_fps)
    _safe_log(progress, 0.27, f"Output: {target_w}x{target_h} @ {target_fps}fps")

    opened: dict = {}

    def _get_source(path: str):
        if path not in opened:
            opened[path] = VideoFileClip(path)
        return opened[path]

    segments = []
    total = len(intervals)
    try:
        for idx, (a, b) in enumerate(intervals):
            _check_cancel()
            interval_dur = max(0.0, b - a)
            if interval_dur <= 1e-3:
                continue
            ref: ClipRef = random.choice(pool)
            source = _get_source(ref.source_path)
            end = min(float(source.duration or ref.end), ref.end)
            start = max(0.0, min(ref.start, end - 1e-3))
            base = source.subclip(start, end).without_audio()
            fitted = _fit_clip_to_duration(base, interval_dur, cfg.length_fit_mode)
            prepared = _prepare_segment(fitted, target_w, target_h, target_fps)
            prepared = prepared.set_duration(interval_dur)
            segments.append(prepared)

            if idx % 5 == 0 or idx == total - 1:
                pct = 0.27 + 0.33 * ((idx + 1) / max(1, total))
                _safe_log(progress, pct, f"Built segment {idx + 1}/{total}")

        _safe_log(progress, 0.62, "Concatenating segments…")
        final = concatenate_videoclips(segments, method="compose")
        final = final.set_duration(analysis.duration).set_fps(target_fps)

        _safe_log(progress, 0.7, "Composing audio…")
        music = AudioFileClip(cfg.audio_file)
        music = music.subclip(0, min(float(music.duration or analysis.duration), analysis.duration))

        if cfg.keep_original_audio and final.audio is not None:
            mix_ratio = max(0.0, min(1.0, cfg.audio_mix_ratio))
            try:
                from moviepy.audio.fx.all import volumex
                orig = volumex(final.audio, 1.0 - mix_ratio)
                bg = volumex(music, mix_ratio if mix_ratio > 0 else 1.0)
                final = final.set_audio(CompositeAudioClip([orig, bg]))
            except Exception:
                final = final.set_audio(music)
        else:
            final = final.set_audio(music)

        out_path = cfg.output_file
        out_dir = os.path.dirname(os.path.abspath(out_path))
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        tmp_audio = tempfile.mktemp(suffix=".m4a", prefix="bvc_audio_")
        _safe_log(progress, 0.75, "Encoding final video…")

        ffmpeg_params = []
        if cfg.bitrate:
            pass

        try:
            final.write_videofile(
                out_path,
                fps=target_fps,
                codec=cfg.codec_video,
                audio_codec=cfg.codec_audio,
                preset=cfg.preset,
                bitrate=cfg.bitrate,
                temp_audiofile=tmp_audio,
                remove_temp=True,
                threads=os.cpu_count() or 2,
                logger=None,
                verbose=False,
            )
        finally:
            for p in (tmp_audio,):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except OSError:
                    pass

        _safe_log(progress, 1.0, "Done")

        return EditResult(
            output_path=out_path,
            duration=float(final.duration or analysis.duration),
            n_segments=len(segments),
            tempo=analysis.tempo,
            used_fallback_beats=analysis.used_fallback,
        )
    finally:
        for seg in segments:
            try:
                seg.close()
            except Exception:
                pass
        for src in opened.values():
            try:
                src.close()
            except Exception:
                pass
