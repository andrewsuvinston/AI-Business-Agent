"""Quality workflow — one idea -> one stock-ready JPEG.

Usage:
    python -m app.main quality <ideas_file> --index N
"""

from pathlib import Path

from app.agents.quality_agent import check_image
from app.utils.storage import load_json, save_json
from config.settings import READY_DIR

STOCK_DIR = READY_DIR / "stock"


def _slug(text: str, max_len: int = 50) -> str:
    cleaned = "".join(c if c.isalnum() else "-" for c in text.lower())
    cleaned = "-".join(p for p in cleaned.split("-") if p)
    return cleaned[:max_len] or "item"


def run(ideas_path: str, index: int = 1) -> Path:
    """Produce a stock-ready JPEG for one idea and record its path."""
    path = Path(ideas_path)
    if not path.exists():
        raise FileNotFoundError(f"Ideas file not found: {path}")

    data = load_json(path)
    ideas = data.get("ideas", [])
    if not ideas:
        raise ValueError(f"No ideas in {path}")

    if index < 1 or index > len(ideas):
        raise IndexError(f"--index {index} out of range (1..{len(ideas)})")

    idea = ideas[index - 1]
    src_str = idea.get("image_upscaled_path") or idea.get("image_path")
    if not src_str:
        raise ValueError(
            f"idea #{index} has no image. Run 'image' and 'enhance' first."
        )

    slug = _slug(idea.get("title", f"idea-{index}"))
    print(f"[quality] idea #{index}: {idea.get('title', '(untitled)')}")

    passed, issues, stats, jpg_path = check_image(Path(src_str), STOCK_DIR, slug)

    print(f"[quality] dimensions : {stats['width']}x{stats['height']}  "
          f"({stats['megapixels']} MP)")
    print(f"[quality] sharpness  : {stats['sharpness']}  "
          f"(min {15.0})")
    print(f"[quality] noise      : {stats['noise']}  "
          f"(max {30.0})")

    if passed:
        print("[quality] [PASS] no issues")
    else:
        print(f"[quality] [WARN] {'; '.join(issues)}")

    print(f"[quality] wrote -> {jpg_path}")

    idea["image_stock_path"] = str(jpg_path)
    save_json(data, path)
    print(f"[quality] recorded image_stock_path in {path.name}")

    return jpg_path