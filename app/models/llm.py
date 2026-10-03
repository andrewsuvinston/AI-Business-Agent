"""Local LLM via Ollama. Single provider, no cloud dependency."""
import json
import urllib.request

from config import settings

OLLAMA_URL = f"{settings.OLLAMA_HOST}/api/generate"
OLLAMA_MODEL = settings.OLLAMA_MODEL


def _call(prompt: str, system: str | None, model: str | None,
          json_mode: bool) -> str:
    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system
    if json_mode:
        payload["format"] = "json"

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return resp["response"]


def ask(prompt: str, model: str | None = None, system: str | None = None) -> str:
    return _call(prompt, system, model, json_mode=False)


def ask_json(prompt: str, model: str | None = None,
             system: str | None = None) -> dict:
    raw = _call(prompt, system, model, json_mode=True)
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].lstrip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"LLM returned non-JSON: {raw[:500]!r}") from e