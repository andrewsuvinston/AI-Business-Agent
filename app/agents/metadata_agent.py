"""Metadata Agent — turns one product idea into shippable product metadata."""
import json
from typing import Any, Optional

from app.models.llm import ask_json

SYSTEM_PROMPT = """You are a copywriter and SEO specialist for a solo
digital-product business. You will be given ONE product idea (as JSON).
Your job: produce customer-facing metadata for that idea.

Reply with a JSON object with EXACTLY this shape:

{
  "source_title": "<copy the idea's title verbatim>",
  "title_variants": ["<variant 1>", "<variant 2>", "<variant 3>"],
  "description": "<2-4 sentence product description for the buyer>",
  "tags": ["<tag 1>", "<tag 2>", "<... up to 13 separate tags>"],
  "pinterest_title": "<short, clickable Pinterest pin title>",
  "pinterest_description": "<one-sentence Pinterest pin description>",
  "listing_bullets": ["<bullet 1>", "<bullet 2>", "<bullet 3>"]
}

Rules:
- Output ONLY the JSON object. No prose, no markdown fences.
- "title_variants", "tags", and "listing_bullets" must be JSON ARRAYS
  of SEPARATE strings. Do not put commas inside one string.
- Tone: human and specific. No hype words like "revolutionary".
- Do NOT invent claims the product does not support.
"""

REQUIRED_FIELDS = (
    "source_title",
    "title_variants",
    "description",
    "tags",
    "pinterest_title",
    "pinterest_description",
    "listing_bullets",
)

LIST_FIELDS = ("title_variants", "tags", "listing_bullets")


def _validate(result: Any) -> None:
    if not isinstance(result, dict):
        raise ValueError(f"Expected a dict, got {type(result).__name__}: {result!r}")
    for field in REQUIRED_FIELDS:
        if field not in result:
            raise ValueError(f"Missing field: {field}. Got keys: {list(result.keys())}")
    for field in LIST_FIELDS:
        v = result[field]
        if not isinstance(v, list) or not v:
            raise ValueError(f"'{field}' must be a non-empty list, got: {v!r}")


def _normalize(metadata: dict) -> None:
    """Split any comma-joined strings inside the list fields."""
    for field in LIST_FIELDS:
        cleaned: list[str] = []
        for item in metadata[field]:
            if not isinstance(item, str):
                continue
            parts = [p.strip() for p in item.split(",") if p.strip()]
            cleaned.extend(parts)
        seen = set()
        unique = []
        for x in cleaned:
            if x not in seen:
                seen.add(x)
                unique.append(x)
        metadata[field] = unique


def generate(idea: dict, model: Optional[str] = None) -> dict:
    """Return metadata for a single idea dict."""
    user = "Product idea (JSON):\n" + json.dumps(idea, ensure_ascii=False, indent=2)
    user += "\n\nProduce the metadata JSON now."
    result = ask_json(prompt=user, system=SYSTEM_PROMPT, model=model)
    _validate(result)
    _normalize(result)
    return result
