"""Workflow: validate every idea in every ideas_*.json file.

Passes go to data/ready_to_upload/, failures to data/rejected/.
Each idea becomes its own file so it can be approved individually.
"""
import json
import shutil
from datetime import datetime
from pathlib import Path

from config.settings import PROCESSED_DIR, READY_DIR, REJECTED_DIR

from app.agents.qc_agent import check
from app.utils.storage import load_json, save_json
from config.settings import PROCESSED_DIR, READY_DIR, REJECTED_DIR

PATTERN = "ideas_*.json"


def _slug(text: str, max_len: int = 40) -> str:
    cleaned = "".join(c if c.isalnum() else "-" for c in text.lower())
    cleaned = "-".join(p for p in cleaned.split("-") if p)
    return cleaned[:max_len] or "item"
def _clean_dir(folder: Path) -> None:
    """Remove everything in folder except .gitkeep and stock/. Recreate the folder."""
    folder.mkdir(parents=True, exist_ok=True)
    for item in folder.iterdir():
        if item.name in (".gitkeep", "stock"):
            continue
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)


def run() -> None:
    files = sorted(PROCESSED_DIR.glob(PATTERN))
    if not files:
        print("\nNo ideas files to check.")
        print(f"Looked in: {PROCESSED_DIR}")
        return
     # Fresh start — remove last run's output
    _clean_dir(READY_DIR)
    _clean_dir(REJECTED_DIR)

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
                slug = _slug(title)
                out = READY_DIR / f"idea_{stamp}_{slug}.json"

                # Copy the image (upscaled preferred) if one exists
                img_src = idea.get("image_upscaled_path") or idea.get("image_path")
                img_note = ""
                if img_src:
                    src = Path(img_src)
                    if src.exists():
                        dest = READY_DIR / f"image_{stamp}_{slug}{src.suffix}"
                        shutil.copy2(src, dest)
                        img_note = f"  +image"
                    else:
                        img_note = "  (image missing)"

                save_json({"direction": direction, "source_file": path.name, "idea": idea}, out)
                print(f"    [ok]   {title}{img_note}")

    print()
    print("=" * 68)
    print(f"  Total:      {total}")
    print(f"  Passed:     {passed}   ->  {READY_DIR}")
    print(f"  Rejected:   {rejected}   ->  {REJECTED_DIR}")
    print(f"  Duplicates: {duplicate}   (also rejected)")
    print("=" * 68)
    print()
