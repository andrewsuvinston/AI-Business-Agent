"""Workflow: summarize all saved ideas files as a daily report."""
from collections import defaultdict
from pathlib import Path

from app.utils.storage import load_json
from config.settings import PROCESSED_DIR

PATTERN = "ideas_*.json"


def _parse_timestamp(stem: str) -> tuple[str, str]:
    """Turn 'ideas_2026-09-26_191858' into ('2026-09-26', '19:18')."""
    # strip the 'ideas_' prefix
    rest = stem[len("ideas_"):] if stem.startswith("ideas_") else stem
    if len(rest) < 15 or rest[10] != "_":
        return ("unknown", "unknown")
    date = rest[:10]
    time = rest[11:13] + ":" + rest[13:15]
    return date, time


def _collect() -> list[dict]:
    entries: list[dict] = []
    for path in sorted(PROCESSED_DIR.glob(PATTERN)):
        data = load_json(path)
        if not isinstance(data, dict) or "ideas" not in data:
            print(f"  [skip] {path.name} (not a valid ideas file)")
            continue
        date, time = _parse_timestamp(path.stem)
        entries.append({
            "date": date,
            "time": time,
            "filename": path.name,
            "direction": data.get("direction", "(unknown)"),
            "count": len(data["ideas"]),
        })
    return entries


def run() -> None:
    entries = _collect()
    if not entries:
        print("\nNo ideas files yet.")
        print(f"Looked in: {PROCESSED_DIR}")
        print('Run: python -m app.main ideas "<direction>"')
        return

    by_date: dict[str, list[dict]] = defaultdict(list)
    for e in entries:
        by_date[e["date"]].append(e)

    total_files = len(entries)
    total_ideas = sum(e["count"] for e in entries)
    dates = sorted(by_date.keys())

    line = "=" * 68
    print()
    print(line)
    print("  AI Business Agent — Ideas Report")
    print(line)
    print(f"  Files:  {total_files}")
    print(f"  Ideas:  {total_ideas}")
    print(f"  Dates:  {dates[0]}  ->  {dates[-1]}")
    print(line)

    for date in reversed(dates):  # newest first
        items = sorted(by_date[date], key=lambda x: x["time"], reverse=True)
        day_count = sum(i["count"] for i in items)
        print()
        print(f"  {date}   ({len(items)} files, {day_count} ideas)")
        print("  " + "-" * 64)
        for item in items:
            print(f"    {item['time']}   {item['count']:>2} ideas   {item['direction']}")
            print(f"            {item['filename']}")
    print()
