"""Enhance agent — upscale to stock dimensions.

Strategy:
  - If source is already >= 2000px on the short side, just resize (fast).
  - Else, run Real-ESRGAN via ComfyUI, then resize.
"""

from pathlib import Path

from PIL import Image

from app.agents.image_agent import upscale_via_comfy

DEFAULT_SIZE = 2000
DEFAULT_DPI = 300


def _simple_resize(src: Path, size: int, dpi: int) -> Path:
    dest = src.with_name(src.stem + f"_upscaled_{size}.png")
    img = Image.open(src).convert("RGB").resize((size, size), Image.LANCZOS)
    img.save(dest, "PNG", dpi=(dpi, dpi))
    print(f"[enhance] simple resize -> {dest.name}")
    return dest


def upscale(src: Path, size: int = DEFAULT_SIZE, dpi: int = DEFAULT_DPI) -> Path:
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    # If source is already big enough, skip AI upscale
    img = Image.open(src)
    if min(img.size) >= size:
        return _simple_resize(src, size, dpi)

    try:
        dest = upscale_via_comfy(src, target_size=size)
        return dest
    except Exception as e:
        print(f"[enhance] ComfyUI upscale failed: {e}")
        print("[enhance] Falling back to Pillow (blurry).")
        return _simple_resize(src, size, dpi)