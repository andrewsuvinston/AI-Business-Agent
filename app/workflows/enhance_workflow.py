"""Enhance workflow — upscale the image for one idea.

Usage from CLI:
    python -m app.main enhance <ideas_file> --index N
"""

from pathlib import Path

from app.agents.enhance_agent import upscale
from app.utils.storage import load_json, save_json


def run(ideas_path: str, index: int = 1) -> Path:
    """Upscale the image for one idea, record the path in the ideas file."""
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
    image_path = idea.get("image_path")
    if not image_path:
        raise ValueError(
            f"idea #{index} has no image_path. Run the 'image' step first."
        )

    upscaled = upscale(Path(image_path))

    idea["image_upscaled_path"] = str(upscaled)
    save_json(data, path)
    print(f"[enhance] recorded image_upscaled_path in {path.name}")

    return upscaled