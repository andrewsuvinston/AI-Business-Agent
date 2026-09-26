"""Workflow: run the Idea Agent, print a table, save the JSON."""
from datetime import datetime
from pathlib import Path

from app.agents.idea_agent import generate
from app.utils.storage import save_json
from config.settings import PROCESSED_DIR


def _format_table(result: dict) -> str:
    """Return a human-readable multi-line string for the console."""
    lines = []
    for i, idea in enumerate(result["ideas"], start=1):
        lines.append(f"--- {i}. {idea['title']} ---")
        lines.append(f"  Buyer:      {idea['buyer']}")
        lines.append(f"  Format:     {idea['format']}")
        lines.append(f"  Why:        {idea['why_it_might_sell']}")
        lines.append(f"  Difficulty: {idea['difficulty']}")
        lines.append(f"  Price:      {idea['price_range_inr']}")
        lines.append(f"  Keywords:   {', '.join(idea['keywords'])}")
        lines.append("")
    return "\n".join(lines)


def _save(result: dict) -> Path:
    """Save result to data/processed/ideas_<timestamp>.json. Returns the path."""
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = PROCESSED_DIR / f"ideas_{stamp}.json"
    save_json(result, path)
    return path


def run(direction: str, count: int = 5) -> Path:
    print(f"\n>>> Direction: {direction}")
    print(f">>> Count:     {count}")
    print(">>> Generating ideas (first run can take 30-60s)...\n")

    result = generate(direction=direction, count=count)
    print(_format_table(result))

    path = _save(result)
    print(f"Saved to: {path}")
    return path
