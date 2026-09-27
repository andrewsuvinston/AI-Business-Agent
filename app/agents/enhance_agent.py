"""Enhance agent — resize an image up to Adobe Stock specs.

Currently uses Pillow (LANCZOS). Later: swap in Real-ESRGAN for sharpness.

Adobe Stock minimum: 4 megapixels, 300 DPI.
We target 2000x2000 (4.0 MP) by default.
"""

from pathlib import Path

from PIL import Image


DEFAULT_SIZE = 2000
DEFAULT_DPI = 300


def upscale(src: Path, size: int = DEFAULT_SIZE, dpi: int = DEFAULT_DPI) -> Path:
    """Resize `src` to size x size, save as `*_upscaled.png` next to it."""
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    img = Image.open(src).convert("RGB")
    img = img.resize((size, size), Image.LANCZOS)

    dest = src.with_name(src.stem + f"_upscaled_{size}.png")
    img.save(dest, "PNG", dpi=(dpi, dpi))
    print(f"[enhance] {src.name} ({img.width}x{img.height}) -> {dest.name} @ {dpi} DPI")
    return dest