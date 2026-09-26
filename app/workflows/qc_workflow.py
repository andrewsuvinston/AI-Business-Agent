"""Workflow: validate every idea in every ideas_*.json file.

Passes go to data/ready_to_upload/, failures to data/rejected/.
Each idea becomes its own file so it can be approved individually.
"""
import json
from datetime import datetime
from pathlib import Path

from app.agents.qc_agent import check
from app.utils.storage import load_json, save_json
from config.settings import PROCESSED_DIR, READY_DIR, REJECTED_DIR

PATTERN = "ideas_*.json"


def _slug(text: str, max_len: int = 40) -> str:
    cleaned = "".join(c if c.isalnum() else "-" for c in text.lower())
    cleaned = "-".join(p for p in cleaned.split("-") if p)
    return cleaned[:max_len] or "item"


def run() -> None:
    files = sorted(PROCESSED_DIR.glob(PATTERN))
    if not files:
        print("\nNo ideas files to check.")
        print(f"Looked in: {PROCESSED_DIR}")
        return

    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    seen_titles: set[str] = set()

    total = 0
    passed = 0
    rejected = 0
    duplicate = 0

    print()
    print("=" * 68)
    print("  AI Business Agent — Quality Control")
    print("=" * 68)

    for path in files:
        data = load_json(path)
        if not isinstance(data, dict) or "ideas" not in data:
            print(f"\n  [skip] {path.name} (not an ideas file)")
            continue

        direction = data.get("direction", "unknown")
        ideas = data["ideas"]
        print(f"\n  {path.name}  ({len(ideas)} ideas, direction: {direction!r})")
        print("  " + "-" * 64)

        for i, idea in enumerate(ideas, start=1):
            total += 1
            title = idea.get("title", f"idea-{i}")

            # Duplicate check
            title_key = title.strip().lower()
            if title_key in seen_titles:
                duplicate += 1
                out = REJECTED_DIR / f"idea_{stamp}_{_slug(title)}.json"
                save_json({"reason": "duplicate title", "direction": direction, "idea": idea}, out)
                print(f"    [dup]  {title}")
                continue
            seen_titles.add(title_key)

            ok, reasons = check(idea)
            if ok:
                passed += 1
                out = READY_DIR / f"idea_{stamp}_{_slug(title)}.json"
                save_json({"direction": direction, "source_file": path.name, "idea": idea}, out)
                print(f"    [ok]   {title}")
            else:
                rejected += 1
                out = REJECTED_DIR / f"idea_{stamp}_{_slug(title)}.json"
                save_json({"reasons": reasons, "direction": direction, "source_file": path.name, "idea": idea}, out)
                print(f"    [fail] {title}  --  {', '.join(reasons)}")

    print()
    print("=" * 68)
    print(f"  Total:      {total}")
    print(f"  Passed:     {passed}   ->  {READY_DIR}")
    print(f"  Rejected:   {rejected}   ->  {REJECTED_DIR}")
    print(f"  Duplicates: {duplicate}   (also rejected)")
    print("=" * 68)
    print()
