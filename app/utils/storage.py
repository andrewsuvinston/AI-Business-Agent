"""Small helpers for saving and loading JSON files.

Every agent that needs to persist data uses these functions.
"""
import json
from pathlib import Path
from typing import Any, Optional, Union


def save_json(data: Any, path: Union[str, Path], indent: int = 2) -> Path:
    """Write `data` to `path` as JSON. Creates parent folders if needed.

    Returns the resolved Path object where the data was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    return path


def load_json(path: Union[str, Path]) -> Optional[Any]:
    """Read JSON from `path`. Returns None if the file doesn't exist."""
    path = Path(path)
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)
    