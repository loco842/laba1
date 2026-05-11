"""BeatVideoCutter — automatic video editing synchronized to music beats."""


def _patch_pillow_compat() -> None:
    """moviepy 1.0.3 references PIL.Image.ANTIALIAS which was removed in Pillow 10.

    Re-create it as an alias for Resampling.LANCZOS so resizing still works
    with modern Pillow installs.
    """
    try:
        from PIL import Image  # type: ignore
        if not hasattr(Image, "ANTIALIAS"):
            try:
                Image.ANTIALIAS = Image.Resampling.LANCZOS  # type: ignore[attr-defined]
            except AttributeError:
                Image.ANTIALIAS = Image.LANCZOS  # type: ignore[attr-defined]
    except Exception:
        pass


_patch_pillow_compat()


from .config import Config  # noqa: E402

__all__ = ["Config"]
__version__ = "0.1.0"
