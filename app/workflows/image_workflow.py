"""Image workflow — one idea -> one image.

Usage from CLI:
    python -m app.main image data/processed/ideas_2026-09-26_192806.json --index 1
"""

from pathlib import Path

from app.agents.image_agent import generate
from app.utils.storage import load_json, save_json


def build_prompt(idea: dict) -> str:
    """Turn one idea dict into an SD1.5 prompt string."""
    parts = [idea.get("title", "")]
    kws = idea.get("keywords") or []
    parts.extend(kws)
    # A little style seasoning — SD1.5 responds well to these tags
    parts.append("poster art, high detail, soft lighting, clean composition")
    return ", ".join(p for p in parts if p)


def run(ideas_path: str, index: int = 1) -> Path:
    """Generate an image for one idea and record its path."""
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
    prompt = build_prompt(idea)
    print(f"[image] idea #{index}: {idea.get('title', '(untitled)')}")
    print(f"[image] prompt: {prompt}")

    png_path = generate(prompt)

    # record it back into the ideas file
    idea["image_path"] = str(png_path)
    save_json(data, path)
    print(f"[image] recorded image_path in {path.name}")

    return png_path
