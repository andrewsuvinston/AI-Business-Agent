"""Workflow: read one idea from a saved ideas file, produce metadata."""
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.agents.metadata_agent import generate
from app.utils.storage import load_json, save_json
from config.settings import PROCESSED_DIR


def _slug(text: str, max_len: int = 40) -> str:
    cleaned = "".join(c if c.isalnum() else "-" for c in text.lower())
    cleaned = "-".join(p for p in cleaned.split("-") if p)
    return cleaned[:max_len] or "item"


def _format(metadata: dict) -> str:
    lines = []
    lines.append(f"Source title: {metadata['source_title']}")
    lines.append("")
    lines.append("Title variants:")
    for v in metadata["title_variants"]:
        lines.append(f"  - {v}")
    lines.append("")
    lines.append("Description:")
    lines.append(f"  {metadata['description']}")
    lines.append("")
    lines.append("Tags:")
    lines.append("  " + ", ".join(metadata["tags"]))
    lines.append("")
    lines.append(f"Pinterest title:       {metadata['pinterest_title']}")
    lines.append(f"Pinterest description: {metadata['pinterest_description']}")
    lines.append("")
    lines.append("Listing bullets:")
    for b in metadata["listing_bullets"]:
        lines.append(f"  - {b}")
    return "\n".join(lines)


def run(ideas_file: str, index: int = 1, model: Optional[str] = None) -> Path:
    path = Path(ideas_file)
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        print(f"Error: file not found: {path}")
        raise SystemExit(1)

    data = load_json(path)
    if not isinstance(data, dict) or "ideas" not in data:
        print(f"Error: {path.name} is not a valid ideas file.")
        raise SystemExit(1)

    ideas = data["ideas"]
    if index < 1 or index > len(ideas):
        print(f"Error: --index {index} is out of range (1..{len(ideas)}).")
        raise SystemExit(1)

    idea = ideas[index - 1]
    direction = data.get("direction", "(unknown)")
    print(f"\n>>> Source file: {path.name}")
    print(f">>> Direction:   {direction}")
    print(f">>> Idea #{index}:  {idea.get('title', '(no title)')}")
    print(f">>> Model:       {model or '(from .env)'}")
    print(">>> Generating metadata...\n")

    metadata = generate(idea=idea, model=model)
    print(_format(metadata))

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = PROCESSED_DIR / f"metadata_{stamp}_{_slug(idea.get('title', 'item'))}.json"
    save_json(metadata, out)
    print(f"\nSaved to: {out}")
    return out
