"""The only file in the project that knows how to talk to the LLM.

If we ever swap Ollama for a cloud API, we change this file only.
"""
import json
from typing import Optional

from ollama import Client

from config.settings import OLLAMA_HOST, OLLAMA_MODEL

_client = Client(host=OLLAMA_HOST)


def _build_messages(prompt: str, system: Optional[str]) -> list:
    """Small helper: turn our two args into the message list Ollama expects."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def ask(prompt: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
    """Send a prompt to the local model and return its reply as plain text."""
    response = _client.chat(
        model=model or OLLAMA_MODEL,
        messages=_build_messages(prompt, system),
    )
    return response.message.content


def ask_json(prompt: str, model: Optional[str] = None, system: Optional[str] = None) -> dict:
    """Like ask(), but the model is forced to reply with JSON.

    Returns a Python dict (parsed from the model's JSON text).
    Raises json.JSONDecodeError if the model somehow returns invalid JSON.
    """
    response = _client.chat(
        model=model or OLLAMA_MODEL,
        messages=_build_messages(prompt, system),
        format="json",  # <-- the key difference: Ollama constrains output to valid JSON
    )
    return json.loads(response.message.content)