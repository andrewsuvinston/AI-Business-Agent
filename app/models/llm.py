"""The only file in the project that knows how to talk to the LLM.

If we ever swap Ollama for a cloud API, we change this file only.
"""
from typing import Optional

from ollama import Client

from config.settings import OLLAMA_HOST, OLLAMA_MODEL

_client = Client(host=OLLAMA_HOST)


def ask(prompt: str, model: Optional[str] = None, system: Optional[str] = None) -> str:
    """Send a prompt to the local model and return its text reply."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = _client.chat(model=model or OLLAMA_MODEL, messages=messages)
    return response.message.content