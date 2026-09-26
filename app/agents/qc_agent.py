"""Quality-Control Agent — structural validation of one idea.

No LLM. Pure deterministic checks.
"""
from typing import Any

REQUIRED_FIELDS = (
    "title",
    "buyer",
    "format",
    "why_it_might_sell",
    "difficulty",
    "keywords",
    "price_range_inr",
)

ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}

MIN_TITLE_LEN = 3


def check(idea: Any) -> tuple[bool, list[str]]:
    """Return (pass, reasons). If pass is False, reasons explains why."""
    reasons: list[str] = []

    if not isinstance(idea, dict):
        return False, [f"not a dict: {type(idea).__name__}"]

    for field in REQUIRED_FIELDS:
        if field not in idea:
            reasons.append(f"missing field: {field}")

    if reasons:
        return False, reasons

    title = idea.get("title", "")
    if not isinstance(title, str) or len(title.strip()) < MIN_TITLE_LEN:
        reasons.append(f"title too short: {title!r}")

    difficulty = idea.get("difficulty", "")
    if difficulty not in ALLOWED_DIFFICULTY:
        reasons.append(f"difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}, got {difficulty!r}")

    keywords = idea.get("keywords", [])
    if not isinstance(keywords, list) or not keywords:
        reasons.append("keywords must be a non-empty list")

    return (len(reasons) == 0), reasons
