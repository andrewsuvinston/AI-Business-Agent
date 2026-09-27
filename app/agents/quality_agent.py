"""Quality agent — technical checks + stock-ready JPEG export.

Checks: dimensions, megapixels, sharpness (edge variance), noise (residual).
Output: JPEG @ quality 90 with standard sRGB ICC profile embedded.
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageCms, ImageFilter, ImageStat

# Adobe Stock minimums
MIN_SIDE = 2000
MIN_MP = 4.0
MAX_MP = 100.0

# Output
JPEG_QUALITY = 90

# Heuristic thresholds — tuned for SD1.5 upscaled output.
# Adjust if you see too many false warnings.
SHARPNESS_MIN = 15.0
NOISE_MAX = 30.0


def _sharpness_score(img: Image.Image) -> float:
    """Higher = sharper. Edge-detect then measure variance."""
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    return ImageStat.Stat(edges).stddev[0]


def _noise_score(img: Image.Image) -> float:
    """Higher = noisier. Difference from a blurred version."""
    gray = img.convert("L")
    blurred = gray.filter(ImageFilter.GaussianBlur(radius=1.5))
    residual = ImageChops.difference(gray, blurred)
    return ImageStat.Stat(residual).stddev[0]


def analyze(path: Path) -> dict:
    """Return numeric stats about an image."""
    img = Image.open(path)
    w, h = img.size
    return {
        "width": w,
        "height": h,
        "megapixels": round((w * h) / 1_000_000, 2),
        "sharpness": round(_sharpness_score(img), 2),
        "noise": round(_noise_score(img), 2),
        "mode": img.mode,
    }


def make_stock_jpg(src: Path, dest_dir: Path, slug: str) -> Path:
    """Convert src to sRGB JPEG @ quality 90. Returns the destination path."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{slug}.jpg"

    img = Image.open(src).convert("RGB")

    # Strip any existing ICC profile, embed standard sRGB
    srgb_profile = ImageCms.createProfile("sRGB")
    icc_bytes = ImageCms.ImageCmsProfile(srgb_profile).tobytes()

    img.save(dest, "JPEG", quality=JPEG_QUALITY, icc_profile=icc_bytes,
             optimize=True, progressive=True)
    return dest


def check_image(src: Path, dest_dir: Path, slug: str) -> tuple[bool, list[str], dict, Path]:
    """Run all checks and write the stock JPEG.

    Returns (passed, issues, stats, jpg_path).
    `passed` means all *hard* checks passed. Warnings are informative.
    """
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Image not found: {src}")

    stats = analyze(src)
    issues: list[str] = []

    # Hard checks — these MUST pass
    if stats["width"] < MIN_SIDE or stats["height"] < MIN_SIDE:
        issues.append(
            f"too small: {stats['width']}x{stats['height']} (min {MIN_SIDE}x{MIN_SIDE})"
        )
    if stats["megapixels"] < MIN_MP:
        issues.append(f"below {MIN_MP} MP: {stats['megapixels']}")
    if stats["megapixels"] > MAX_MP:
        issues.append(f"above {MAX_MP} MP: {stats['megapixels']}")

    # Soft checks — warnings only, human decides
    if stats["sharpness"] < SHARPNESS_MIN:
        issues.append(f"low sharpness: {stats['sharpness']} (min {SHARPNESS_MIN})")
    if stats["noise"] > NOISE_MAX:
        issues.append(f"high noise: {stats['noise']} (max {NOISE_MAX})")

    jpg_path = make_stock_jpg(src, dest_dir, slug)

    return (len(issues) == 0), issues, stats, jpg_path