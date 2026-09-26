"""Idea Agent — turns a business direction into structured product ideas.

Public API:
    generate(direction, count=5, model=None) -> dict
"""
from typing import Any, Optional

from app.models.llm import ask_json

# --- The agent's role and output contract ---
# Edit this string to change the agent's behavior. Nothing else needs to change.
SYSTEM_PROMPT = """You are a market researcher for a solo digital-product business.

The business sells AI-assisted digital products (image packs, printables,
templates) to niche audiences. The owner is a student with limited time.

You will be given a business direction (a niche or theme).
Your job: propose distinct, specific product ideas within that direction.

Reply with a JSON object with EXACTLY this shape:

{
  "direction": "<the direction you were given, copied verbatim>",
  "ideas": [
    {
      "title": "<short product name, 3-6 words>",
      "buyer": "<who specifically buys this, one phrase>",
      "format": "<what the buyer receives, e.g. 'PNG pack, 5 sizes, 300 DPI'>",
      "why_it_might_sell": "<one sentence — the market reason>",
      "difficulty": "easy",
      "keywords": ["<3-6 search keywords>"],
      "price_range_inr": "<e.g. 'Rs.99-299'>"
    }
  ]
}

Rules:
- Output ONLY the JSON object. No prose, no explanations, no markdown fences.
- Do NOT invent a "count" field.
- Every idea must be a distinct product, not a variation of the same one.
- "difficulty" must be one of: easy, medium, hard.
"""

REQUIRED_IDEA_FIELDS = (
    "title",
    "buyer",
    "format",
    "why_it_might_sell",
    "difficulty",
    "keywords",
    "price_range_inr",
)

ALLOWED_DIFFICULTY = {"easy", "medium", "hard"}


def _validate(result: Any) -> None:
    """Raise ValueError with a clear message if the model's reply is malformed."""
    if not isinstance(result, dict):
        raise ValueError(f"Expected a dict, got {type(result).__name__}: {result!r}")

    if "ideas" not in result:
        raise ValueError(f"Missing 'ideas' key. Got keys: {list(result.keys())}")

    ideas = result["ideas"]
    if not isinstance(ideas, list) or not ideas:
        raise ValueError(f"'ideas' must be a non-empty list, got: {ideas!r}")

    for i, idea in enumerate(ideas):
        if not isinstance(idea, dict):
            raise ValueError(f"ideas[{i}] is not a dict: {idea!r}")
        missing = [f for f in REQUIRED_IDEA_FIELDS if f not in idea]
        if missing:
            raise ValueError(
                f"ideas[{i}] missing fields: {missing}. Got keys: {list(idea.keys())}"
            )
        if idea["difficulty"] not in ALLOWED_DIFFICULTY:
            raise ValueError(
                f"ideas[{i}].difficulty must be one of {sorted(ALLOWED_DIFFICULTY)}, "
                f"got {idea['difficulty']!r}"
            )


def generate(direction: str, count: int = 5, model: Optional[str] = None) -> dict:
    """Generate `count` product ideas for a business `direction`.

    Returns a dict: { "direction": str, "ideas": [ {...}, ... ] }
    Raises ValueError if the model's reply doesn't match the expected schema.
    """
    user_prompt = (
        f"Business direction: {direction}\n"
        f"Generate exactly {count} product ideas."
    )
    result = ask_json(prompt=user_prompt, system=SYSTEM_PROMPT, model=model)
    _validate(result)
    return result
