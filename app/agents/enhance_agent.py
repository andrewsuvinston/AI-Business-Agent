"""Enhance agent — AI upscaling using the Real-ESRGAN portable executable.

Calls realesrgan-ncnn-vulkan.exe via subprocess. Falls back to Pillow
LANCZOS if the executable is not found.
"""

import subprocess
from pathlib import Path

from PIL import Image

DEFAULT_SIZE = 2000
DEFAULT_DPI = 300

EXE_PATH = Path(__file__).resolve().parents[2] / "tools" / "realesrgan" / "realesrgan-ncnn-vulkan.exe"


def _upscale_with_pillow(src: Path, size: int) -> Image.Image:
    img = Image.open(src).convert("RGB")
    return img.resize((size, size), Image.LANCZOS)


def upscale(src: Path, size: int = DEFAULT_SIZE, dpi: int = DEFAULT_DPI) -> Path:
    """Upscale `src` using Real-ESRGAN exe. Save as `*_upscaled_{size}.png`."""
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    dest = src.with_name(src.stem + f"_upscaled_{size}.png")
    temp_4x = src.with_name(src.stem + "_temp_4x.png")

    if not EXE_PATH.exists():
        print(f"[enhance] Executable not found at {EXE_PATH}. Using Pillow fallback (blurry).")
        img = _upscale_with_pillow(src, size)
    else:
        # Run Real-ESRGAN exe (4x upscale)
        cmd = [
            str(EXE_PATH),
            "-i", str(src),
            "-o", str(temp_4x),
            "-n", "realesrgan-x4plus",
            "-s", "4",
        ]
        print(f"[enhance] Running Real-ESRGAN (4x)... this may take a minute.")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"[enhance] Real-ESRGAN failed: {result.stderr}")
            print("[enhance] Falling back to Pillow.")
            img = _upscale_with_pillow(src, size)
        else:
            # Load the 4x result and resize to final target size
            img_4x = Image.open(temp_4x).convert("RGB")
            img = img_4x.resize((size, size), Image.LANCZOS)
            temp_4x.unlink(missing_ok=True)  # clean up temp file

    img.save(dest, "PNG", dpi=(dpi, dpi))
    print(f"[enhance] {src.name} -> {dest.name} @ {dpi} DPI")
    return dest